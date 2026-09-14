"""Check transfer/package integrity; this is not hardware or fresh PCB DRC."""
from pathlib import Path
import csv
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def rows(name):
    with (ROOT / name).open(newline="") as stream:
        return list(csv.DictReader(stream))


def refs(data, key):
    result = [reference.strip() for row in data for reference in row[key].split(",")]
    assert len(result) == len(set(result)), "Duplicate reference"
    return set(result)


def hex_addresses(path):
    addresses = set()
    base = 0
    ended = False
    for line in path.read_text().splitlines():
        assert not ended, "Data after EOF"
        assert line.startswith(":"), "Invalid HEX record"
        raw = bytes.fromhex(line[1:])
        assert len(raw) == raw[0] + 5 and sum(raw) % 256 == 0, "Bad HEX checksum/length"
        offset = int.from_bytes(raw[1:3], "big")
        kind = raw[3]
        data = raw[4:-1]
        if kind == 0:
            current = set(range(base + offset, base + offset + len(data)))
            assert not addresses & current, "Overlapping HEX data"
            addresses |= current
        elif kind == 1:
            ended = True
        elif kind == 2:
            base = int.from_bytes(data, "big") << 4
        elif kind == 4:
            base = int.from_bytes(data, "big") << 16
        else:
            assert kind in (3, 5), "Unknown HEX record type"
    assert ended and addresses, "Incomplete HEX"
    return addresses


def main():
    hashes = json.loads((ROOT / "firmware/SHA256.json").read_text())
    for name, expected in hashes.items():
        assert sha((ROOT / "firmware" / name).read_bytes()) == expected, f"Firmware changed: {name}"
    journal = set(range(0x1800, 0x1820))
    assert not hex_addresses(ROOT / "firmware/click-counter-Q1.hex") & journal
    factory = hex_addresses(ROOT / "firmware/factory-display-info.hex")
    assert factory <= journal and factory, "Factory image must target info-FRAM journal only"
    print("PASS: original firmware hashes, valid HEXs and application/factory journal separation")

    full = rows("procurement/BOM-Q1.csv")
    pcb = rows("procurement/BOM-PCBA-Q1.csv")
    offboard = rows("procurement/OFFBOARD-items-Q1.csv")
    pcbrefs = refs(pcb, "Designator")
    assert len(pcbrefs) == len(pcb) == 46
    assert pcbrefs == refs(rows("procurement/CPL-JLCPCB-Q1.csv"), "Designator")
    assert pcbrefs == refs(rows("procurement/placements-KiCad-Q1.csv"), "Ref")
    assert refs(offboard, "Designator") == {"BAT1", "K1", "K2"}
    assert refs(full, "Designator") == pcbrefs | {"BAT1", "K1", "K2"}
    assert pcb == [r for r in full if r["Assembly"] in ("top", "bottom")]
    assert offboard == [r for r in full if r["Assembly"] not in ("top", "bottom")]
    print("PASS: exact 46-ref PCB BOM/CPL match and separate offboard commercial scope")

    report = json.loads((ROOT / "verification/routed-drc.json").read_text())
    assert not report["violations"] and not report["unconnected_items"]
    status = json.loads((ROOT / "verification/Q1-status.json").read_text())
    assert status["hardware_tested"] is False and status["production_released"] is False
    print("PASS: retained DRC result and explicit unqualified/unreleased status (no fresh DRC run)")

    with zipfile.ZipFile(ROOT / "procurement/click-counter-Q1-Gerbers.zip") as archive:
        assert archive.testzip() is None
        files = {p.name: p for p in (ROOT / "electronics/gerbers").iterdir() if p.is_file()}
        assert set(archive.namelist()) == set(files)
        for name, path in files.items():
            assert archive.read(name) == path.read_bytes(), f"Gerber mismatch: {name}"
    print("PASS: Gerber archive equals all loose manufacturing files")

    manifest = json.loads((ROOT / "dist/manifest.json").read_text())
    archive_path = ROOT / "dist" / manifest["file"]
    assert archive_path.stat().st_size == manifest["bytes"]
    assert sha(archive_path.read_bytes()) == manifest["sha256"]
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist()) == len(set(archive.namelist()))
        assert set(archive.namelist()) == set(manifest["members"])
        for name, item in manifest["members"].items():
            data = archive.read(name)
            assert data == (ROOT / name).read_bytes(), f"Stale RFQ member: {name}"
            assert len(data) == item["bytes"] and sha(data) == item["sha256"]
    print("PASS: RFQ archive/manifest equals repository files, including corrected import BOMs")
    print("Q1 remains a quotation prototype. Hardware tests and final enclosure remain outstanding.")


if __name__ == "__main__":
    main()
