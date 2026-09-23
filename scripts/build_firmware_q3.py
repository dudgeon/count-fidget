"""Build/verify the separate Q3 OLED candidate without touching Q1/Q2 images."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile

from build_firmware import file_record, hex_image, tree_record
from run_host_tests_q3 import run_tests

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "firmware/q3-oled"
STEM = "click-counter-Q3-oled"
SOURCES = ("main_msp430.c", "counter.c", "oled.c", "input.c")
HEADERS = ("counter.h", "oled.h", "input.h")
INPUTS = tuple("firmware/q3-oled/" + name for name in SOURCES + HEADERS + (
    "test_counter.c", "test_oled.c", "test_input.c", "README.md", "source-records.json")) + (
    "scripts/build_firmware_q3.py", "scripts/run_host_tests_q3.py", "scripts/build_firmware.py",
)
FLAGS = ("-mmcu=msp430fr4133", "-std=c11", "-Os", "-Wall", "-Wextra", "-Werror",
         "-ffunction-sections", "-fdata-sections", "-fstack-usage")
SUFFIXES = (".elf", ".hex", ".map", ".lst")
FACTORY = "factory-blank-info-Q3.hex"

def factory_image():
    # Factory only: initialize the existing32-byte journal and new2-byte gapmarker.
    records = []
    for address, length in ((0x1800,16),(0x1810,16),(0x1820,2)):
        payload = bytes([length,address>>8,address&255,0])+bytes([255])*length
        records.append(":"+(payload+bytes([-sum(payload)&255])).hex().upper())
    return "\n".join(records)+"\n:00000001FF\n"



def elf_image(path):
    data = path.read_bytes()
    if data[:6] != b"\x7fELF\x01\x01" or struct.unpack_from("<H", data, 18)[0] != 105:
        raise ValueError("Expected little-endian ELF32 MSP430")
    phoff = struct.unpack_from("<I", data, 28)[0]
    phsize, phcount = struct.unpack_from("<HH", data, 42)
    shoff = struct.unpack_from("<I", data, 32)[0]
    shsize, shcount = struct.unpack_from("<HH", data, 46)
    if phsize != 32 or shsize != 40:
        raise ValueError("Unexpected ELF headers")
    segments = [struct.unpack_from("<8I", data, phoff + i * phsize) for i in range(phcount)]
    sections = [struct.unpack_from("<10I", data, shoff + i * shsize) for i in range(shcount)]
    image, symbols, ram_bytes = {}, {}, 0
    for section in sections:
        _, kind, flags, address, offset, size, link, _, _, entrysize = section
        if flags & 2 and 0x2000 <= address < 0x2800:
            if address + size > 0x2800:
                raise ValueError("RAM allocation outside device")
            ram_bytes += size
        if kind == 1 and flags & 2 and size:
            owners = [s for s in segments if s[0] == 1 and s[1] <= offset
                      and offset + size <= s[1] + s[4]
                      and address == s[2] + offset - s[1]]
            if len(owners) != 1 or offset + size > len(data):
                raise ValueError("ELF initialized section has no unique load mapping")
            load = owners[0][3] + offset - owners[0][1]
            for target, byte in enumerate(data[offset:offset + size], load):
                if target in image:
                    raise ValueError("Overlapping ELF load bytes")
                image[target] = byte
        if kind == 2:
            strings = sections[link]
            names = data[strings[4]:strings[4] + strings[5]]
            for position in range(offset, offset + size, entrysize):
                name, value, _, _, _, _ = struct.unpack_from("<IIIBBH", data, position)
                symbols[names[name:].split(b"\0", 1)[0].decode()] = value
    return image, symbols, ram_bytes


def validate(directory):
    image = hex_image(directory / (STEM + ".hex"))
    loaded, symbols, ram_bytes = elf_image(directory / (STEM + ".elf"))
    if image != loaded:
        raise ValueError("ELF and HEX load images differ")
    if any(not 0xc400 <= a <= 0xffff or 0xff80 <= a < 0xff88 for a in image):
        raise ValueError("Application writes outside program FRAM/vectors or initializes security signatures")
    if set(image) & set(range(0x1800, 0x1a00)):
        raise ValueError("Application initializes information FRAM")
    vectors = {"port1_isr": 0xffe6, "i2c_isr": 0xffea, "timer0_isr": 0xfff8,
               "_start": 0xfffe}
    for name, address in vectors.items():
        actual = image.get(address, 0) | image.get(address + 1, 0) << 8
        if name not in symbols or actual != symbols[name] or actual not in image:
            raise ValueError("Incorrect compiled interrupt/reset vector: " + name)
    if ram_bytes > 1024:
        raise ValueError("Q3 static RAM exceeds half the available 2 KiB")
    payload = b"".join(struct.pack("<IB", a, b) for a, b in sorted(image.items()))
    return {"elf_hex_load_bytes_equal": True, "load_bytes": len(image),
            "addressed_load_sha256": hashlib.sha256(payload).hexdigest(),
            "addressed_load_hash_encoding": "sorted little-endian uint32 address + uint8 byte",
            "information_fram_0x1800_0x19ff_excluded": True,
            "security_signatures_0xff80_0xff87_excluded": True,
            "factory_only_information_initializer": FACTORY,
            "vectors": {name: {"vector": hex(a), "target": hex(symbols[name])}
                        for name, a in vectors.items()},
            "static_ram_bytes": ram_bytes,
            "hardware_tested": False, "manufacturing_released": False}


def verify_manifest(directory=None):
    directory = directory or SOURCE / "build"
    manifest = json.loads((directory / "build-manifest.json").read_text())
    if manifest["schema"] != 1 or set(manifest["inputs"]) != set(INPUTS):
        raise ValueError("Unexpected Q3 manifest inputs/schema")
    for name, record in manifest["inputs"].items():
        if file_record(ROOT / name) != record:
            raise ValueError("Q3 source changed since compilation: " + name)
    expected = {STEM + suffix for suffix in SUFFIXES} | {"host-tests.txt", "stack-usage.txt", FACTORY}
    if set(manifest["outputs"]) != expected:
        raise ValueError("Unexpected Q3 output set")
    for name, record in manifest["outputs"].items():
        if file_record(directory / name) != record:
            raise ValueError("Q3 output changed since compilation: " + name)
    if (directory / FACTORY).read_text() != factory_image():
        raise ValueError("Unexpected Q3 factory information initializer")
    if validate(directory) != manifest["validation"]:
        raise ValueError("Q3 load validation differs")
    for name, record in manifest["preserved_baselines"].items():
        if file_record(ROOT / name) != record:
            raise ValueError("Frozen Q1/Q2 artifact changed: " + name)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toolchain", type=Path)
    parser.add_argument("--support", type=Path)
    parser.add_argument("--output", type=Path, default=SOURCE / "build")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    # Repository output is deliberately confined to this revision's subtree.
    if ROOT in output.parents and SOURCE not in output.parents:
        parser.error("Repository outputs must be inside firmware/q3-oled/")
    if args.verify_only:
        verify_manifest(output);print("PASS: Q3 input/output hashes and target load validation");return
    if not args.toolchain or not args.support:
        parser.error("--toolchain and --support are required to compile")
    tc, support = args.toolchain.resolve(), args.support.resolve()
    version = (tc / "version.properties").read_text().strip()
    support_revision = (support / "Revisions_Header.txt").read_text().splitlines()[0]
    if "version=9.3.1.11" not in version or support_revision != "Build 1.212 (GCC)":
        parser.error("Q3 recipe requires TI GCC 9.3.1.11 and support 1.212")
    for name in ("counter.c", "counter.h", "test_counter.c"):
        if (SOURCE / name).read_bytes() != (ROOT / "firmware" / name).read_bytes():
            raise ValueError("Counter/journal baseline copy differs: " + name)
    inputs = {name: file_record(ROOT / name) for name in INPUTS}
    baseline_paths = [ROOT / "firmware" / ("click-counter-Q1" + s) for s in (".elf", ".hex", ".map")]
    baseline_paths += sorted((ROOT / "firmware/q2-lcd-check").glob("*"))
    baselines = {p.relative_to(ROOT).as_posix(): file_record(p) for p in baseline_paths if p.is_file()}
    tools = {name: tc / "bin" / ("msp430-elf-" + name)
             for name in ("gcc", "objcopy", "objdump", "size")}
    provenance = {"compiler_package": version, "support_revision": support_revision,
                  "toolchain_tree": tree_record(tc), "support_tree": tree_record(support),
                  "tools": {name: {**file_record(path), "version": subprocess.check_output(
                      [str(path), "--version"], text=True).splitlines()[0]}
                            for name, path in tools.items()}}
    commands = []
    with tempfile.TemporaryDirectory(prefix="count-fidget-q3-") as temporary:
        stage = Path(temporary)
        for name in SOURCES + HEADERS:
            shutil.copyfile(SOURCE / name, stage / name)

        def portable(text):
            return text.replace(str(tc), "<TOOLCHAIN>").replace(str(support), "<SUPPORT>").replace(str(stage), "<BUILD>")

        def run(command):
            commands.append([portable(str(arg)) for arg in command])
            return subprocess.check_output([str(arg) for arg in command], cwd=stage, text=True)

        for name in SOURCES:
            run([tools["gcc"], *FLAGS, "-I" + str(support / "include"), "-MD", "-MF", name + ".d",
                 "-c", name, "-o", name + ".o"])
        run([tools["gcc"], *FLAGS, "-L" + str(support / "include"), *(name + ".o" for name in SOURCES),
             "-Wl,--gc-sections,-Map," + STEM + ".map", "-o", STEM + ".elf"])
        run([tools["objcopy"], "-O", "ihex", STEM + ".elf", STEM + ".hex"])
        (stage / (STEM + ".lst")).write_text(portable(run([tools["objdump"], "-d", STEM + ".elf"])))
        map_file = stage / (STEM + ".map")
        map_file.write_text(portable(map_file.read_text()))
        size = run([tools["size"], STEM + ".elf"]).strip()
        (stage / "stack-usage.txt").write_text("".join(p.read_text() for p in sorted(stage.glob("*.su"))))
        (stage / "host-tests.txt").write_text(run_tests())
        (stage / FACTORY).write_text(factory_image())
        if hex_image(stage / FACTORY) != {a:255 for a in range(0x1800,0x1822)}:
            raise ValueError("Factory initializer range differs")
        dependencies = {}
        for name in SOURCES:
            content = (stage / (name + ".d")).read_text().replace("\\\n", " ")
            for item in re.findall(r"(?:\\.|[^\s])+", content.split(":", 1)[1]):
                path = Path(item.replace("\\ ", " "))
                path = path if path.is_absolute() else stage / path
                dependencies[portable(str(path))] = file_record(path)
        validation = validate(stage)
        if any(file_record(ROOT / name) != record for name, record in inputs.items()):
            raise RuntimeError("Source changed during compilation; output not published")
        outputs = {STEM + s: file_record(stage / (STEM + s)) for s in SUFFIXES}
        outputs.update({name: file_record(stage / name) for name in ("host-tests.txt", "stack-usage.txt", FACTORY)})
        manifest = {"schema": 1, "status": "Q3 OLED candidate; hardware and manufacture hold",
                    "target": "MSP430FR4133IG48R", "display": "X087-2832TSWIG02-H14 / SSD1312",
                    "inputs": inputs, "outputs": outputs, "provenance": provenance,
                    "dependencies": dependencies, "commands": commands, "size": size,
                    "validation": validation, "preserved_baselines": baselines}
        (stage / "build-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        output.mkdir(parents=True, exist_ok=True)
        for name in (*outputs, "build-manifest.json"):
            shutil.copyfile(stage / name, output / name)
    verify_manifest(output)
    print(size)
    print("PASS: Q3 compiled/host checks, vectors, ELF/HEX equivalence and information-FRAM exclusion")
    print("Q1/Q2 firmware preserved. Q3 hardware qualification is outstanding.")


if __name__ == "__main__":
    main()
