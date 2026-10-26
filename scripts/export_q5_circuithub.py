"""Build the CircuitHub upload package for the locked Q5 board (no upload, quote or order).

CircuitHub (South Deerfield, MA) imports native KiCad projects, not Gerbers, and buys
parts from US distributors (Digi-Key, Mouser, Arrow, TI direct, ...), not LCSC. The
canonical Q5 BOM was built from JLC/LCSC inventory, so this script writes a CircuitHub
CSV BOM that keeps every fitted reference and footprint unchanged and only replaces
LCSC-house-brand part numbers with stocked US-distributor equivalents. The table of
replacements and their evidence lives in procurement/q5/circuithub/crossref-q5.json.

Writes procurement/q5/circuithub/:
  BOM-CIRCUITHUB-Q5.csv             CircuitHub "Supplying a BOM as a CSV" format
  click-counter-Q5-circuithub.zip   the KiCad 10 files CircuitHub needs (.kicad_pro, all .kicad_sch, .kicad_pcb)
  manifest-circuithub-Q5.json       input and output SHA-256 so a stale package is detectable
Run: python3 scripts/export_q5_circuithub.py   (Python standard library only)
"""
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
Q5 = ROOT / 'electronics/q5'
DEST = ROOT / 'procurement/q5/circuithub'
BOM = ROOT / 'procurement/q5/BOM-Q5.csv'
CROSSREF = DEST / 'crossref-q5.json'
OUT_BOM = DEST / 'BOM-CIRCUITHUB-Q5.csv'
OUT_ZIP = DEST / 'click-counter-Q5-circuithub.zip'
MANIFEST = DEST / 'manifest-circuithub-Q5.json'
# Column names exactly as CircuitHub's CSV BOM importer recognises them.
COLUMNS = ['Reference Designators', 'Manufacturer', 'Manufacturer Part Number', 'Value', 'Description',
           'Supplier', 'Supplier Part Number', 'DNP']
FITTED_ROLES = {'jlc_smt', 'home_through_hole'}
ZIP_TIME = (2026, 9, 26, 0, 0, 0)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref_key(ref):
    m = re.fullmatch(r'([A-Z]+)(\d+)', ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


def schematic_parts():
    """Every placed symbol (reference -> (in_bom flag, Value)) across the hierarchical schematic."""
    parts = {}
    for path in sorted(Q5.glob('*.kicad_sch')):
        text = path.read_text(encoding='utf-8')
        for m in re.finditer(r'\(symbol \(lib_id "[^"]+"\)(.*?)\(instances', text, flags=re.S):
            body = m.group(1)
            ref = re.search(r'\(property "Reference" "([^"]+)"', body).group(1)
            if ref.startswith('#'):
                continue
            in_bom = re.search(r'\(in_bom (yes|no)\)', body).group(1) == 'yes'
            value = re.search(r'\(property "Value" "([^"]*)"', body).group(1)
            require(ref not in parts, f'Duplicate schematic reference {ref}')
            parts[ref] = (in_bom, value)
    return parts


def upload_files():
    root = Q5 / 'click-counter-Q5.kicad_sch'
    sheets = sorted(set(re.findall(r'\(property "Sheetfile" "([^"]+)"', root.read_text(encoding='utf-8'))))
    files = [Q5 / 'click-counter-Q5.kicad_pro', root] + [Q5 / s for s in sheets] + [Q5 / 'click-counter-Q5.kicad_pcb']
    on_disk = sorted(p.name for p in Q5.glob('*.kicad_sch'))
    require(sorted(p.name for p in files if p.suffix == '.kicad_sch') == on_disk,
            'Every schematic must be the root or a sub-sheet referenced by it (CircuitHub needs one root)')
    for path in files:
        require(path.is_file(), f'Missing {path.name}')
        require(not re.search(r'/Users/|/home/|/private/|file://|[A-Z]:\\\\Users\\\\', path.read_text(encoding='utf-8')),
                f'Private local path in {path.name}')
    pcb = files[-1].read_text(encoding='utf-8')
    require('(generator_version "10.0")' in pcb, 'Expected a KiCad 10 board (CircuitHub fully supports KiCad 10)')
    require(pcb.count('(filled_polygon') > 0, 'Copper zones must be filled before upload (CircuitHub does not refill)')
    return files


def main():
    cross = json.loads(CROSSREF.read_text(encoding='utf-8'))
    rows = list(csv.DictReader(BOM.open(encoding='utf-8-sig', newline='')))
    sch = schematic_parts()
    lines = {}
    seen = set()
    for row in rows:
        if row['Assembly Role'] not in FITTED_ROLES:
            continue
        ref, mpn = row['Designator'], row['Manufacturer Part Number']
        require(ref in sch and sch[ref][0], f'{ref}: fitted in BOM-Q5 but not an in-BOM schematic symbol')
        require(ref not in seen, f'{ref} listed twice in BOM-Q5')
        seen.add(ref)
        entry = cross['lines'].get(mpn)
        require(entry is not None, f'{ref} {mpn}: no CircuitHub decision in crossref-q5.json')
        require(entry['package'] in row['Footprint'], f'{ref}: crossref package {entry["package"]} != footprint {row["Footprint"]}')
        key = (entry['mpn'], entry['manufacturer'], entry['dnp'])
        line = lines.setdefault(key, dict(refs=[], entry=entry, values=[]))
        line['refs'].append(ref)
        if sch[ref][1] not in line['values']:
            line['values'].append(sch[ref][1])
    fitted_sch = {r for r, (in_bom, _) in sch.items() if in_bom}
    require(seen == fitted_sch, f'Fitted set differs from schematic: {sorted(seen ^ fitted_sch)}')
    not_fitted = sorted((r for r, (in_bom, _) in sch.items() if not in_bom), key=ref_key)
    require(all(r.startswith(('TP', 'H')) for r in not_fitted), 'Only test lands and mounting holes may be unfitted')
    unused = set(cross['lines']) - {r['Manufacturer Part Number'] for r in rows if r['Assembly Role'] in FITTED_ROLES}
    require(not unused, f'Stale crossref entries: {sorted(unused)}')

    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator='\n')
    writer.writerow(COLUMNS)
    for (mpn, manufacturer, dnp), line in sorted(lines.items(), key=lambda kv: ref_key(sorted(kv[1]['refs'], key=ref_key)[0])):
        entry = line['entry']
        refs = ','.join(sorted(line['refs'], key=ref_key))
        writer.writerow([refs, manufacturer, mpn, ' / '.join(line['values']), entry['description'],
                         entry.get('supplier', ''), entry.get('supplier_pn', ''), 'DNP' if dnp else ''])
    writer.writerow([','.join(not_fitted), '', 'NO-PART', 'PCB land / NPTH',
                     'Test lands and mounting holes: copper/drill only, nothing to place', '', '', 'DNP'])
    DEST.mkdir(parents=True, exist_ok=True)
    OUT_BOM.write_text(buffer.getvalue(), encoding='utf-8')

    files = upload_files()
    with zipfile.ZipFile(OUT_ZIP, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            info = zipfile.ZipInfo(path.name, date_time=ZIP_TIME)
            info.compress_type, info.external_attr = zipfile.ZIP_DEFLATED, 0o644 << 16
            archive.writestr(info, path.read_bytes())
    with zipfile.ZipFile(OUT_ZIP) as archive:
        require(archive.testzip() is None and all(archive.read(p.name) == p.read_bytes() for p in files),
                'Upload ZIP differs from the native KiCad files')

    placed = sum(len(l['refs']) for l in lines.values() if not l['entry']['dnp'])
    manifest = dict(
        schema=1, purpose='CircuitHub upload package for the locked Q5 board; not a quote, order or release',
        inputs_sha256={str(p.relative_to(ROOT)): digest(p) for p in [BOM, CROSSREF, *files]},
        outputs_sha256={str(p.relative_to(ROOT)): digest(p) for p in (OUT_BOM, OUT_ZIP)},
        counts=dict(fitted_references=len(seen), circuithub_placed=placed, circuithub_dnp=len(seen) - placed,
                    not_fitted_lands_and_holes=len(not_fitted), csv_lines=len(lines) + 1,
                    unique_placed_mpns=len({k for k, l in lines.items() if not l['entry']['dnp']}),
                    crossed_lines=sum(1 for e in cross['lines'].values() if e['action'] == 'cross'),
                    consign_lines=sum(1 for e in cross['lines'].values() if e['action'] == 'consign')),
        zip_members=[p.name for p in files])
    MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    print(f"CircuitHub package: {len(seen)} fitted refs -> {placed} placed by CircuitHub, {len(seen) - placed} DNP; "
          f"{manifest['counts']['crossed_lines']} crossed and {manifest['counts']['consign_lines']} consigned part lines; "
          f"{len(files)} KiCad files in the upload ZIP")


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, OSError) as error:
        print('FAIL: ' + str(error), file=sys.stderr)
        sys.exit(1)
