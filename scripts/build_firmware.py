"""Build the unreleased Q2 LCD candidate; never overwrite submitted Q1 artifacts."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
STEM = "click-counter-Q2-lcd-check"
SOURCES = ("main_msp430.c", "counter.c", "lcd_de188.c")
HEADERS = ("counter.h", "lcd_de188.h")
INPUTS = tuple("firmware/" + name for name in SOURCES + HEADERS) + (
    "scripts/build_firmware.py", "scripts/verify_project.py", "scripts/run_host_tests.py",
)
DIVERGENCES = {"firmware/main_msp430.c"}
Q1_HEX = "firmware/click-counter-Q1.hex"
Q1_HEX_SHA256 = "98e775d027c6de064d5f0e2c25695ad2b998d30e9aae37ea2704a56c85b46b18"
# This recipe supports exactly the reviewed divider-only candidate, not general Q2 firmware.
EXPECTED_LOAD_CHANGES = {0xC53D: (0x18, 0x38)}
FLAGS = ("-mmcu=msp430fr4133", "-std=c11", "-Os", "-Wall", "-Wextra",
         "-Werror", "-ffunction-sections", "-fdata-sections")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_record(path):
    data = path.read_bytes()
    return {"sha256": digest(data), "bytes": len(data)}


def tree_record(path):
    """Hash relative names and every file's contents, independent of install path."""
    entries = [(p.relative_to(path).as_posix(), digest(p.read_bytes()))
               for p in sorted(path.rglob("*")) if p.is_file()]
    payload = "".join(name + "\0" + sha + "\n" for name, sha in entries).encode()
    return {"sha256": digest(payload), "files": len(entries),
            "algorithm": "SHA256 of sorted relative-path + NUL + file-SHA256 + LF"}


def hex_image(path):
    image, base, ended = {}, 0, False
    for line in path.read_text().splitlines():
        if ended or not line.startswith(":"):
            raise ValueError("Invalid HEX record/EOF")
        raw = bytes.fromhex(line[1:])
        if len(raw) < 5 or len(raw) != raw[0] + 5 or sum(raw) % 256:
            raise ValueError("HEX length/checksum mismatch")
        offset, kind, data = int.from_bytes(raw[1:3], "big"), raw[3], raw[4:-1]
        if kind == 0:
            for index, byte in enumerate(data, base + offset):
                if index in image:
                    raise ValueError("Overlapping HEX data")
                image[index] = byte
        elif kind == 1 and not data:
            ended = True
        elif kind in (2, 4) and len(data) == 2:
            base = int.from_bytes(data, "big") << (4 if kind == 2 else 16)
        elif kind not in (3, 5):
            raise ValueError("Unsupported HEX record")
    if not ended or not image:
        raise ValueError("Incomplete HEX image")
    return image


def elf_image_and_lcd(path):
    """Read ELF32 MSP430 load bytes and the actual lcd_start symbol's code."""
    data = path.read_bytes()
    if data[:6] != b"\x7fELF\x01\x01" or struct.unpack_from("<H", data, 18)[0] != 105:
        raise ValueError("Expected little-endian ELF32 MSP430")
    phoff = struct.unpack_from("<I", data, 28)[0]
    phsize, phcount = struct.unpack_from("<HH", data, 42)
    if phsize != 32:
        raise ValueError("Unsupported ELF32 program-header size")
    segments = [struct.unpack_from("<8I", data, phoff + index * phsize)
                for index in range(phcount)]
    shoff = struct.unpack_from("<I", data, 32)[0]
    shsize, count = struct.unpack_from("<HH", data, 46)
    if shsize != 40:
        raise ValueError("Unsupported ELF32 section-header size")
    sections = [struct.unpack_from("<10I", data, shoff + index * shsize)
                for index in range(count)]
    image, lcd = {}, None
    for section in sections:
        _, kind, flags, address, offset, size, link, _, _, entrysize = section
        if kind == 1 and flags & 2 and size:  # Allocated initialized bytes only.
            # HEX uses load addresses (LMA), not a .data section's RAM runtime address.
            # Select its PT_LOAD by both file extent and virtual-address mapping.
            owners = [segment for segment in segments if segment[0] == 1
                      and segment[1] <= offset
                      and offset + size <= segment[1] + segment[4]
                      and address == segment[2] + offset - segment[1]]
            if len(owners) != 1 or offset + size > len(data):
                raise ValueError("ELF section has no unique complete load mapping")
            segment = owners[0]
            load_address = segment[3] + offset - segment[1]
            for index, byte in enumerate(data[offset:offset + size], load_address):
                if index in image:
                    raise ValueError("Overlapping ELF sections")
                image[index] = byte
        if kind == 2:
            strings = sections[link]
            names = data[strings[4]:strings[4] + strings[5]]
            for position in range(offset, offset + size, entrysize):
                name, value, length, _, _, which = struct.unpack_from("<IIIBBH", data, position)
                if names[name:].split(b"\0", 1)[0] == b"lcd_start":
                    owner = sections[which]
                    start = owner[4] + value - owner[3]
                    lcd = (value, data[start:start + length])
    if lcd is None or not image:
        raise ValueError("Missing lcd_start or load image")
    return image, lcd


def validate_candidate(directory, root=ROOT):
    frozen = root / Q1_HEX
    if file_record(frozen)["sha256"] != Q1_HEX_SHA256:
        raise ValueError("Frozen Q1 application HEX differs from the reviewed baseline")
    baseline = hex_image(frozen)
    image = hex_image(directory / (STEM + ".hex"))
    loaded, (address, lcd) = elf_image_and_lcd(directory / (STEM + ".elf"))
    if image != loaded:
        raise ValueError("ELF and HEX load bytes differ")
    # Exclude the whole device information FRAM, not just the current journal.
    if set(image) & set(range(0x1800, 0x1A00)):
        raise ValueError("Application initializes information FRAM")
    if image.keys() != baseline.keys():
        raise ValueError("Exact Q2 LCD candidate must retain all Q1 load addresses")
    changes = {address: (baseline[address], byte) for address, byte in image.items()
               if baseline[address] != byte}
    if changes != EXPECTED_LOAD_CHANGES:
        raise ValueError("Exact Q2 LCD candidate requires only 0xc53d: 0x18 -> 0x38")
    # Verify compiled immediate writes to real registers, not a source substring.
    required = {"LCDCTL0": bytes.fromhex("b2 40 5d 38 00 06"),
                "LCDVCTL": bytes.fromhex("b2 40 a0 f0 08 06")}
    for name, instruction in required.items():
        if lcd.count(instruction) != 1:
            raise ValueError("Unexpected compiled " + name + " configuration")
    return {"elf_hex_load_bytes_equal": True, "load_bytes": len(image),
            "scope": "Exact reviewed Q2 LCD divider-only candidate",
            "frozen_q1_hex": {"file": Q1_HEX, "sha256": Q1_HEX_SHA256},
            "loaded_byte_changes": [{"address": hex(address), "q1": hex(old),
                                     "q2": hex(new)}
                                    for address, (old, new) in sorted(changes.items())],
            "information_fram_0x1800_0x19ff_excluded": True,
            "lcd_start_address": hex(address), "LCDCTL0": "0x385d",
            "LCDVCTL": "0xf0a0", "nominal_frame_hz": 32,
            "hardware_tested": False, "manufacturing_released": False}


def verify_manifest(root=ROOT, directory=None):
    directory = directory or root / "firmware/q2-lcd-check"
    manifest = json.loads((directory / "build-manifest.json").read_text())
    if manifest["schema"] != 1 or set(manifest["inputs"]) != set(INPUTS):
        raise ValueError("Unexpected Q2 build inputs/schema")
    for name, record in manifest["inputs"].items():
        if file_record(root / name) != record:
            raise ValueError("Q2 input changed since compilation: " + name)
    expected_outputs = {STEM + suffix for suffix in (".elf", ".hex", ".map", ".lst")}
    if set(manifest["outputs"]) != expected_outputs:
        raise ValueError("Unexpected Q2 output list")
    for name, record in manifest["outputs"].items():
        if file_record(directory / name) != record:
            raise ValueError("Q2 compiled output changed: " + name)
    if validate_candidate(directory, root) != manifest["validation"]:
        raise ValueError("Q2 target validation differs")
    frozen = json.loads((root / "dist/manifest.json").read_text())
    changes = manifest["frozen_q1_divergences"]
    if set(changes) != DIVERGENCES:
        raise ValueError("Only explicitly named Q2 source divergence is allowed")
    for name, hashes in changes.items():
        if hashes != {"q1_sha256": frozen["members"][name]["sha256"],
                      "q2_sha256": manifest["inputs"][name]["sha256"]}:
            raise ValueError("Invalid Q1/Q2 source provenance: " + name)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toolchain", required=True, type=Path,
                        help="TI MSP430 GCC installation root (contains bin/)")
    parser.add_argument("--support", required=True, type=Path,
                        help="TI support package root (contains include/)")
    parser.add_argument("--output", type=Path, default=ROOT / "firmware/q2-lcd-check")
    args = parser.parse_args()
    tc, support, output = args.toolchain.resolve(), args.support.resolve(), args.output.resolve()
    if output == ROOT / "firmware" or output == ROOT / "dist":
        parser.error("Output must be a separate Q2 candidate directory")
    include = support / "include"
    version = (tc / "version.properties").read_text().strip()
    support_revision = (support / "Revisions_Header.txt").read_text().splitlines()[0]
    if "version=9.3.1.11" not in version or support_revision != "Build 1.212 (GCC)":
        parser.error("This verified recipe requires TI GCC 9.3.1.11 and support 1.212")
    inputs = {name: file_record(ROOT / name) for name in INPUTS}
    provenance = {"compiler_package": version, "support_revision": support_revision,
                  "toolchain_tree": tree_record(tc), "support_tree": tree_record(support)}
    tools = {name: tc / "bin" / ("msp430-elf-" + name)
             for name in ("gcc", "objcopy", "objdump", "size")}
    provenance["tools"] = {name: {**file_record(path), "version": subprocess.check_output(
        [str(path), "--version"], text=True).splitlines()[0]} for name, path in tools.items()}
    commands = []
    with tempfile.TemporaryDirectory(prefix="count-fidget-q2-") as temporary:
        stage = Path(temporary)
        for name in SOURCES + HEADERS:
            shutil.copyfile(ROOT / "firmware" / name, stage / name)

        def portable(text):
            return text.replace(str(tc), "<TOOLCHAIN>").replace(str(support), "<SUPPORT>").replace(
                str(stage), "<BUILD>")

        def run(command):
            commands.append([portable(str(arg)) for arg in command])
            return subprocess.check_output([str(arg) for arg in command], cwd=stage, text=True)

        # Separate compilation gives stable object names and dependency records.
        for name in SOURCES:
            run([tools["gcc"], *FLAGS, "-I" + str(include), "-MD", "-MF", name + ".d",
                 "-c", name, "-o", name + ".o"])
        run([tools["gcc"], *FLAGS, "-L" + str(include), *(name + ".o" for name in SOURCES),
             "-Wl,--gc-sections,-Map," + STEM + ".map", "-o", STEM + ".elf"])
        run([tools["objcopy"], "-O", "ihex", STEM + ".elf", STEM + ".hex"])
        listing = run([tools["objdump"], "-d", STEM + ".elf"])
        (stage / (STEM + ".lst")).write_text(portable(listing))
        size = run([tools["size"], STEM + ".elf"]).strip()
        map_path = stage / (STEM + ".map")
        map_path.write_text(portable(map_path.read_text()))
        dependencies = {}
        for name in SOURCES:
            dep = (stage / (name + ".d")).read_text().replace("\\\n", " ")
            # Dependency paths from this package contain no spaces; GCC escapes spaces if present.
            for item in re.findall(r"(?:\\.|[^\s])+", dep.split(":", 1)[1]):
                path = Path(item.replace("\\ ", " "))
                path = path if path.is_absolute() else stage / path
                dependencies[portable(str(path))] = file_record(path)
        validation = validate_candidate(stage)
        if any(file_record(ROOT / name) != record for name, record in inputs.items()):
            raise RuntimeError("Inputs changed during compilation; candidate not published")
        frozen = json.loads((ROOT / "dist/manifest.json").read_text())
        with zipfile.ZipFile(ROOT / "dist" / frozen["file"]) as archive:
            divergences = {name: {"q1_sha256": digest(archive.read(name)),
                                 "q2_sha256": inputs[name]["sha256"]} for name in DIVERGENCES}
        manifest = {"schema": 1, "status": "Q2 LCD verification candidate; hardware hold",
                    "target": "MSP430FR4133IG48R", "inputs": inputs, "provenance": provenance,
                    "dependencies": dependencies, "command_working_directory": "<BUILD>",
                    "commands": commands, "size": size, "validation": validation,
                    "frozen_q1_divergences": divergences,
                    "outputs": {STEM + suffix: file_record(stage / (STEM + suffix))
                                for suffix in (".elf", ".hex", ".map", ".lst")}}
        (stage / "build-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        output.mkdir(parents=True, exist_ok=True)
        for name in (*manifest["outputs"], "build-manifest.json"):
            shutil.copyfile(stage / name, output / name)
    verify_manifest(ROOT, output)
    print(size)
    print("PASS: compiled LCDCTL0=0x385d, LCDVCTL=0xf0a0; ELF/HEX match; information FRAM excluded")
    print("Q2 candidate written; Q1 artifacts preserved. Hardware qualification is still required.")


if __name__ == "__main__":
    main()
