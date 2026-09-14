"""Package existing Q1 inputs; never reroute, flash, or claim fresh hardware checks."""
from pathlib import Path
import base64
import hashlib
import html
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MEMBERS = [
    "procurement/" + name for name in (
        "RFQ-Q1.md", "RFQ-Q1.html", "BOM-Q1.csv", "BOM-PCBA-Q1.csv",
        "OFFBOARD-items-Q1.csv", "WEBSITE-IMPORT-NOTES-Q1.md",
        "placements-KiCad-Q1.csv", "CPL-JLCPCB-Q1.csv",
        "assembly-top.svg", "assembly-bottom.svg", "click-counter-Q1-Gerbers.zip",
    )
] + [
    "firmware/" + name for name in (
        "click-counter-Q1.hex", "factory-display-info.hex", "SHA256.json",
        "main_msp430.c", "counter.h", "counter.c", "lcd_de188.c", "lcd_de188.h",
    )
] + [
    "electronics/click-counter-Q1.kicad_pcb", "electronics/netlist.json",
    "verification/routed-drc.json", "verification/Q1-status.json",
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def inline(text):
    text = html.escape(text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", text)


def markdown(text):
    """Render the trusted project Markdown subset, escaping all raw HTML."""
    lines = text.splitlines()
    output = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if line.startswith("#"):
            level = min(len(line) - len(line.lstrip("#")) + 1, 6)
            output.append(f"<h{level}>" + inline(line.lstrip("#").strip()) + f"</h{level}>")
            index += 1
        elif line.startswith("|"):
            rows = []
            while index < len(lines) and lines[index].startswith("|"):
                cells = [v.strip() for v in lines[index].strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", v.replace(" ", "")) for v in cells):
                    rows.append(cells)
                index += 1
            output.append('<div class="scroll"><table>')
            for number, row in enumerate(rows):
                tag = "th" if number == 0 else "td"
                output.append("<tr>" + "".join(f"<{tag}>{inline(c)}</{tag}>" for c in row) + "</tr>")
            output.append("</table></div>")
        elif re.match(r"^(?:- |\d+\. )", line):
            tag = "ul" if line.startswith("- ") else "ol"
            pattern = r"^- " if tag == "ul" else r"^\d+\. "
            output.append(f"<{tag}>")
            while index < len(lines) and re.match(pattern, lines[index]):
                output.append("<li>" + inline(re.sub(pattern, "", lines[index])) + "</li>")
                index += 1
            output.append(f"</{tag}>")
        else:
            paragraph = []
            while index < len(lines) and lines[index].strip() and not lines[index].startswith(("#", "|", "- ")):
                paragraph.append(lines[index])
                index += 1
            output.append("<p>" + inline(" ".join(paragraph)) + "</p>")
    return "\n".join(output)


STYLE = """body{font:16px/1.55 system-ui,sans-serif;color:#18333d;max-width:1080px;margin:36px auto;padding:0 22px}h1,h2,h3{line-height:1.2}h2{margin-top:36px}table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;vertical-align:top;padding:9px;border-bottom:1px solid #d3e0e5}th{background:#eef4f6}.scroll{overflow-x:auto}code{font-size:.85em;overflow-wrap:anywhere}a{color:#076f95}.notice{background:#fff1d8;border-left:4px solid #ae761c;padding:18px}.drawings{display:grid;grid-template-columns:1fr 1fr;gap:20px}.drawings img{width:100%}figure{margin:12px 0}figcaption{font-size:13px}details{border-top:1px solid #d3e0e5;padding:18px 0}summary{font-weight:700;cursor:pointer}@media(max-width:700px){.drawings{grid-template-columns:1fr}body{padding:0 14px}}@media print{body{margin:0}tr{break-inside:avoid}details{display:block}}"""


def page(title, body):
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>{html.escape(title)}</title><style>{STYLE}</style></head><body>{body}</body></html>")


def drawings():
    parts = []
    for side in ("top", "bottom"):
        content = base64.b64encode((ROOT / f"procurement/assembly-{side}.svg").read_bytes()).decode()
        parts.append(f'<figure><img alt="Q1 {side} assembly" src="data:image/svg+xml;base64,{content}">'
                     f"<figcaption>Q1 {side} assembly; bottom is viewed from below.</figcaption></figure>")
    return '<div class="drawings">' + "".join(parts) + "</div>"


def main():
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    rfq = markdown((ROOT / "procurement/RFQ-Q1.md").read_text())
    (ROOT / "procurement/RFQ-Q1.html").write_text(page("Count Fidget Q1 RFQ", '<h1>Count Fidget · Q1 prototype RFQ</h1>' + drawings() + rfq))
    archive = dist / "click-counter-Q1-RFQ.zip"
    entries = {}
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipped:
        for name in sorted(MEMBERS):
            data = (ROOT / name).read_bytes()
            info = zipfile.ZipInfo(name, date_time=(2026, 9, 14, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zipped.writestr(info, data)
            entries[name] = {"bytes": len(data), "sha256": digest(data)}
    manifest = {"revision": "Q1-public-handoff", "file": archive.name,
                "bytes": archive.stat().st_size, "sha256": digest(archive.read_bytes()),
                "purpose": "Prototype quotation only; no technical release. Repackaged with public contact text and corrected importer BOM.",
                "members": entries}
    (dist / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    body = '<h1>Count Fidget · Q1 design review</h1><div class="notice"><strong>Quotation prototype.</strong> No complete quotes or confirmed website uploads. Hardware is unqualified and the enclosure is an obsolete fit study. No purchase or manufacturing release.</div>' + drawings()
    for title, name in (("Product specification", "docs/product-spec.md"), ("Decisions", "docs/decisions.md"),
                        ("Engineering issues", "docs/open-issues.md"), ("Vendor status", "procurement/vendor-status.md"),
                        ("Exact RFQ", "procurement/RFQ-Q1.md"), ("Electrical connectivity", "electronics/design.md")):
        body += '<details open><summary>' + html.escape(title) + "</summary>" + markdown((ROOT / name).read_text()) + "</details>"
    (ROOT / "docs/design-review.html").write_text(page("Count Fidget Q1 design review", body))
    print(f"Packaged {len(entries)} files: {archive.relative_to(ROOT)} ({manifest['bytes']} bytes)")
    print("SHA256", manifest["sha256"])
    print("No design regeneration, new DRC, target compile or hardware test was performed.")


if __name__ == "__main__":
    main()
