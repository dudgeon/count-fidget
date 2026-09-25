"""Export Q4 engineering review files from current, saved native validation.

No uploads, quotation changes, purchases or manufacturing release are performed.
The factory list contains 67 SMT placements; DS1/SW1/SW2 and their separate
header are home-completion scope. Offboard pack/caps remain unqualified.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'procurement/q4'
BOARD = ROOT / 'electronics/q4/click-counter-Q4.kicad_pcb'
MODEL = ROOT / 'electronics/q4/netlist-Q4.json'
VALIDATION = ROOT / 'verification/q4-validation.json'
STOCK = DEST / 'stock.json'
HARDWARE = DEST / 'hardware-bom.json'
MANIFEST = DEST / 'export-manifest-Q4.json'
GERBER_SUFFIXES = {
    'F_Cu.gtl', 'B_Cu.gbl', 'F_Mask.gts', 'B_Mask.gbs',
    'F_Silkscreen.gto', 'B_Silkscreen.gbo', 'F_Paste.gtp', 'B_Paste.gbp',
    'Edge_Cuts.gm1', 'PTH.drl', 'NPTH.drl', 'job.gbrjob',
}
EXPORT_NAMES = {
    'BOM-PCBA-Q4.csv', 'BOM-JLCPCB-Q4.csv', 'BOM-Q4.csv',
    'OFFBOARD-items-Q4.csv', 'HOME-COMPLETION-Q4.csv', 'SEPARATE-HARDWARE-Q4.csv',
    'CPL-JLCPCB-Q4.csv', 'placements-KiCad-Q4.csv',
    'assembly-top-Q4.svg', 'assembly-bottom-Q4.svg',
    'click-counter-Q4-Gerbers.zip', 'drill-report-Q4.txt', 'REVIEW-EXPORTS-Q4.md',
} | {'gerbers/click-counter-Q4-' + suffix for suffix in GERBER_SUFFIXES}
BOM_HEADER = [
    'Comment', 'Designator', 'Footprint', 'Quantity', 'Manufacturer',
    'Manufacturer Part Number', 'LCSC Part #', 'Assembly Role', 'Side',
    'Qualification', 'Notes',
]
JLC_HEADER = ['Comment', 'Designator', 'Footprint', 'LCSC Part #']
CPL_HEADER = ['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation']
HOME_HEADER = BOM_HEADER + [
    'Retail Source', 'Observed UTC', 'Retail Stock', 'Minimum Order',
    'Order Multiple', 'Quantity for 10 (this reference)', 'Retail Order Group',
    'Retail Group Screening Quantity for 10 (shown once per MPN)',
    'Solder Joints', 'Assembly Sequence',
]


def require(condition, message):
    # Export guards must remain active even if Python is invoked with -O.
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref_key(ref):
    match = re.fullmatch(r'([A-Z]+)(\d+)', ref)
    return (match[1], int(match[2])) if match else (ref, 0)


def write_csv(path, header, rows):
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream, lineterminator='\n')
        writer.writerow(header)
        writer.writerows(rows)


def read_csv(directory, name):
    with (directory / name).open(newline='', encoding='utf-8') as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames, list(reader)


def check_csv(directory, name, header, expected):
    fields, actual = read_csv(directory, name)
    require(fields == header, f'{name}: unexpected column mapping')
    wanted = [dict(zip(header, map(str, row))) for row in expected]
    require(actual == wanted, f'{name}: exact rows, identities, quantities or ordering differ')


def groups(parts):
    result = defaultdict(list)
    for part in parts:
        result[(part['mpn'], part['lcsc'])].append(part)
    return result


def selected_parts(model):
    parts = model['parts']
    require(len(parts) == len({p['ref'] for p in parts}) == 86, 'Expected 86 unique native references')
    require(model['layers'] == 2 and model['board_mm'] == [42, 54, 1], 'Wrong Q4 board stack or outline')
    require(model.get('hardware_tested') is False and model.get('manufacturing_released') is False,
            'Model must preserve unqualified engineering status')
    require(Counter(p.get('assembly') for p in parts) ==
            {'jlc_smt': 67, 'home_through_hole': 3, 'pcb_feature': 16}, 'Assembly-role counts differ')
    fitted = sorted((p for p in parts if p['assembly'] != 'pcb_feature'), key=lambda p: ref_key(p['ref']))
    smt = [p for p in fitted if p['assembly'] == 'jlc_smt']
    home = [p for p in fitted if p['assembly'] == 'home_through_hole']
    require({p['ref'] for p in home} == {'DS1', 'SW1', 'SW2'}, 'Home completion reference set differs')
    require(all(p['side'] == 'bottom' for p in smt) and all(p['side'] == 'top' for p in home),
            'Assembly side contract changed')
    require(len(groups(fitted)) == len({p['mpn'] for p in fitted}) == 38,
            'Expected 38 exact fitted identities with one catalog code each')
    require(len({p['lcsc'] for p in fitted}) == 38, 'Catalog code aliases distinct selected MPNs')
    require(all(p['mpn'] and p['manufacturer'] and re.fullmatch(r'C\d+', p['lcsc'])
                and p['footprint'].startswith('CountFidgetQ4:') for p in fitted), 'Missing exact identity or Q4 footprint')
    return fitted, smt, home


def check_retail(entry, refs, mpn, code, quantity):
    require(entry['references'] == sorted(refs), 'Retail references differ')
    require((entry['mpn'], entry['lcsc_part'], entry['quantity_per_board']) == (mpn, code, quantity),
            'Retail exact identity or quantity differs')
    require(entry['source'] == f'https://www.lcsc.com/product-detail/{code}.html' and entry['observed_at'],
            'Retail observation source missing')
    need = quantity * 10
    spares = max(2, math.ceil(need / 10))
    minimum, multiple = entry['minimum_order'], entry['order_multiple']
    require(isinstance(minimum, int) and isinstance(multiple, int) and minimum > 0 and multiple > 0,
            'Retail minimum/order multiple missing')
    rounded = math.ceil(max(need + spares, minimum) / multiple) * multiple
    require(entry['quantity_for_10'] == need and entry['screening_spares'] == spares and
            entry['rounded_screening_quantity'] == rounded, 'Retail screening quantity differs')
    require(entry['passes_retail_stock_screen'] is True and entry['in_stock'] >= rounded,
            'Insufficient observed loose-parts retail stock')


def fitted_identity_digest(model):
    fields = ('ref', 'mpn', 'lcsc', 'manufacturer', 'assembly')
    identities = [{field: p[field] for field in fields} for p in selected_parts(model)[0]]
    return hashlib.sha256(json.dumps(identities, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def validate_sources(model, stock, hardware, model_hash):
    fitted, smt, home = selected_parts(model)
    plan = stock['screening_plan']
    require(plan['boards'] == 10 and plan['final_bom_screen_complete'] is True,
            'Complete ten-board stock screen required')
    require(plan['final_model_sha256'] == model_hash and plan.get('native_layout_binding_pending') is False,
            'Stock screen model binding is stale or layout binding pending')
    require(plan['fitted_identity_sha256'] == fitted_identity_digest(model), 'Stock identity digest differs')
    require(plan['fitted_positions'] == 70 and plan['exact_fitted_types'] == 38 and
            plan['assembly_role_positions'] == {'jlc_smt': 67, 'home_through_hole': 3, 'pcb_feature': 16},
            'Stock screen counts differ from current model')
    screen = stock['fitted_bom_screen']
    by_key = {(s['mpn'], s['jlc_part']): s for s in screen}
    require(len(by_key) == len(screen) == 38 and set(by_key) == set(groups(fitted)),
            'Stock screen exact MPN/catalog identity set differs')
    selected_observations = []
    for key, matching in groups(fitted).items():
        row = by_key[key]
        quantity = len(matching)
        need = quantity * 10
        spares = max(2, math.ceil(need / 10))
        require(row['references'] == sorted(p['ref'] for p in matching) and row['fitted_per_board'] == quantity
                and row['assembly_roles'] == dict(Counter(p['assembly'] for p in matching)),
                f'Stock references, quantity or assembly role differs: {key[0]}')
        require((row['quantity_for_10'], row['screening_attrition'], row['screening_required_quantity']) ==
                (need, spares, need + spares), f'Stock screening quantity differs: {key[0]}')
        require(row['minimum_order'] >= 1 and row['available_order_quantity'] >=
                max(need + spares, row['minimum_order']) and row['passes_stock_screen'] is True,
                f'Insufficient observed orderable stock: {key[0]}')
        observations = [o for o in stock['observations'] if (o['mpn'], o['jlc_part'], o['observed_at']) ==
                        (*key, row['observed_at']) and o['available_order_quantity'] == row['available_order_quantity']
                        and o['minimum_order'] == row['minimum_order']]
        require(len(observations) == 1, f'Stock screen lacks exact catalog observation: {key[0]}')
        observation = observations[0]
        require(observation['source'] == f'https://jlcpcb.com/partdetail/{key[1]}', 'Unexpected stock source')
        selected_observations.append(observation)
    items = hardware['items']
    require(len(items) == 1, 'Expected one separately accounted OLED header')
    header = items[0]
    require((header['hardware_id'], header['mpn'], header['jlc_part'], header['quantity_per_board'],
             header['manufacturer'], header['solder_joints_per_assembly']) ==
            ('DS1-INTERPOSER', 'PZ254V-11-07P', 'C492406', 1, 'XFCN', 14), 'Separate header contract differs')
    require(header['quantity_for_10'] == 10 and header['screening_spares'] == 2 and
            header['screening_required'] == 12 and header['available_order_quantity'] >=
            max(12, header['minimum_order']), 'Separate header stock quantity differs')
    require(header['catalog_source'] == 'https://jlcpcb.com/partdetail/C492406', 'Header catalog source differs')
    separate = stock['separate_hardware_screen']
    require(len(separate) == 1 and separate[0]['mpn'] == header['mpn'] and
            separate[0]['jlc_part'] == header['jlc_part'] and separate[0]['quantity_for_10'] == 10 and
            separate[0]['screening_required_quantity'] == 12 and separate[0]['passes_stock_screen'] is True and
            separate[0]['available_order_quantity'] == header['available_order_quantity'], 'Separate header screen differs')
    retail = {(r['mpn'], r['lcsc_part']): r for r in stock['retail_home_parts']}
    expected_retail = set(groups(home)) | {(header['mpn'], header['jlc_part'])}
    require(len(retail) == len(stock['retail_home_parts']) == 3 and set(retail) == expected_retail,
            'Retail screen must cover exact home components and separate header')
    for key, matching in groups(home).items():
        check_retail(retail[key], [p['ref'] for p in matching], *key, len(matching))
    check_retail(retail[(header['mpn'], header['jlc_part'])], ['DS1-INTERPOSER'],
                 header['mpn'], header['jlc_part'], 1)
    require(header['retail_stock'] == retail[(header['mpn'], header['jlc_part'])], 'Header retail records differ')
    return {'model_references': 86, 'fitted_references': 70, 'distinct_exact_mpns': 38,
            'jlc_smt_references': 67, 'jlc_smt_exact_mpns': len(groups(smt)),
            'home_through_hole_references': ['DS1', 'SW1', 'SW2'],
            'separate_header_quantity_per_board': 1, 'screened_boards': 10,
            'catalog_observation_range_utc': [min(o['observed_at'] for o in selected_observations),
                                            max(o['observed_at'] for o in selected_observations)],
            'stock_is_unreserved_observation_not_qualification': True}


def bom_row(part):
    return [part['value'], part['ref'], part['footprint'], 1, part['manufacturer'], part['mpn'],
            part['lcsc'], part['assembly'], part['side'], 'Engineering candidate; physically unqualified', part['notes']]


def table_rows(model, stock, hardware):
    fitted, smt, home = selected_parts(model)
    pcb = [bom_row(part) for part in fitted]
    jlc = [[p['mpn'], p['ref'], p['footprint'], p['lcsc']] for p in smt]
    header = hardware['items'][0]
    separate = [[header['description'], header['hardware_id'], 'SEPARATE_HARDWARE', header['quantity_per_board'],
                 header['manufacturer'], header['mpn'], header['jlc_part'], 'home_header_interposer', '',
                 'Catalog screened; stack/solder fit unqualified',
                 'One header at DS1; no separate placement. Fourteen joints: seven module and seven host. '
                 'Loose header inclusion with module is unconfirmed; account once. ' + header['assembly_status']]]
    offboard = [
        ['Rechargeable battery with keyed NTC harness', 'BAT1', 'OFFBOARD', 1, 'UNQUALIFIED', 'NOT_SELECTED', '',
         'qualified_pack_supplier_then_home_connection', '', 'Unqualified; sourcing and pack process unresolved',
         'One prepared rechargeable coin-cell pack including attached NTC, insulated leads, keyed housing and contacts. '
         'No JLC battery stock claim. Exact cell, harness pinout, sensor contact, pack safety and shipping require qualification. '
         'No direct iron soldering to a bare cell.'],
        ['MX-compatible keycaps', 'K1,K2', 'OFFBOARD', 2, 'UNQUALIFIED', 'NOT_SELECTED', '', 'home_press_fit', '',
         'Unqualified; exact source and physical fit unresolved',
         'Two individual caps per device. Verify stem, skirt, clearance and key travel; no current exact stock claim.'],
    ]
    retail = {(r['mpn'], r['lcsc_part']): r for r in stock['retail_home_parts']}
    home_rows = []
    shown_retail_groups = set()
    for part in home:
        r = retail[(part['mpn'], part['lcsc'])]
        sequence = ('Solder separate seven-pin header to module and host with front cover removed; '
                    '14 joints total counted once with DS1, trim to mechanical envelope.' if part['ref'] == 'DS1' else
                    'Seat switch in rear key plate BEFORE soldering its two electrical leads to host PCB.')
        key = (part['mpn'], part['lcsc'])
        grouped_quantity = r['rounded_screening_quantity'] if key not in shown_retail_groups else ''
        shown_retail_groups.add(key)
        home_rows.append(bom_row(part) + [r['source'], r['observed_at'], r['in_stock'], r['minimum_order'],
                         r['order_multiple'], 10, ','.join(r['references']), grouped_quantity,
                         14 if part['ref'] == 'DS1' else 2, sequence])
    return {
        'BOM-PCBA-Q4.csv': (BOM_HEADER, pcb),
        'BOM-JLCPCB-Q4.csv': (JLC_HEADER, jlc),
        'HOME-COMPLETION-Q4.csv': (HOME_HEADER, home_rows),
        'SEPARATE-HARDWARE-Q4.csv': (BOM_HEADER, separate),
        'OFFBOARD-items-Q4.csv': (BOM_HEADER, offboard),
        'BOM-Q4.csv': (BOM_HEADER, pcb + separate + offboard),
    }


def write_tables(directory, model, stock, hardware):
    for name, (header, rows) in table_rows(model, stock, hardware).items():
        write_csv(directory / name, header, rows)


def native_positions(directory, model):
    fitted, _, _ = selected_parts(model)
    parts = {p['ref']: p for p in fitted}
    fields, data = read_csv(directory, 'placements-KiCad-Q4.csv')
    require(fields == ['Ref', 'Val', 'Package', 'PosX', 'PosY', 'Rot', 'Side'], 'Unexpected native placement columns')
    require(len(data) == len({r['Ref'] for r in data}) == 70 and {r['Ref'] for r in data} == set(parts),
            'Native placements must contain all 70 fitted references exactly once')
    for row in data:
        part = parts[row['Ref']]
        require(abs(float(row['PosX']) - part['x']) < 1e-6 and abs(float(row['PosY']) + part['y']) < 1e-6,
                f'Native placement coordinate differs: {part["ref"]}')
        require(abs((float(row['Rot']) - part['rotation'] + 180) % 360 - 180) < 1e-6 and row['Side'] == part['side'],
                f'Native placement side or rotation differs: {part["ref"]}')
        require(row['Package'] == part['footprint'].split(':', 1)[1], f'Native placement footprint differs: {part["ref"]}')
    return data


def cpl_rows(positions, model):
    smt_refs = {p['ref'] for p in selected_parts(model)[1]}
    return [[r['Ref'], r['PosX'] + 'mm', r['PosY'] + 'mm', r['Side'].title(), r['Rot']]
            for r in sorted(positions, key=lambda r: ref_key(r['Ref'])) if r['Ref'] in smt_refs]


def deterministic_zip(directory):
    with zipfile.ZipFile(directory / 'click-counter-Q4-Gerbers.zip', 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted((directory / 'gerbers').iterdir()):
            require(path.is_file() and not path.is_symlink(), 'Unexpected fabrication entry')
            info = zipfile.ZipInfo(path.name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compresslevel=9)


def validate_exports(directory, model, stock, hardware):
    for name, (header, rows) in table_rows(model, stock, hardware).items():
        check_csv(directory, name, header, rows)
    positions = native_positions(directory, model)
    cpl = cpl_rows(positions, model)
    require(len(cpl) == 67, 'Factory CPL count differs')
    check_csv(directory, 'CPL-JLCPCB-Q4.csv', CPL_HEADER, cpl)
    fabrication = directory / 'gerbers'
    expected = {'click-counter-Q4-' + suffix for suffix in GERBER_SUFFIXES}
    require({p.name for p in fabrication.iterdir()} == expected, 'Missing/unexpected fabrication file or inner copper layer')
    job = json.loads((fabrication / 'click-counter-Q4-job.gbrjob').read_text())
    require(job['GeneralSpecs']['LayerNumber'] == 2 and job['GeneralSpecs']['BoardThickness'] == 1.0 and
            job['GeneralSpecs']['ProjectId']['Name'] == 'click-counter-Q4', 'Wrong Gerber project/stack')
    require({x['Name'] for x in job['MaterialStackup'] if x['Type'] == 'Copper'} == {'F.Cu', 'B.Cu'},
            'Gerber job copper stack differs')
    attributes = job['FilesAttributes']
    require(len(attributes) == 9 and {x['Path'] for x in attributes} == expected -
            {'click-counter-Q4-' + s for s in ('PTH.drl', 'NPTH.drl', 'job.gbrjob')}, 'Gerber job file set differs')
    require({x['FileFunction'] for x in attributes if x['FileFunction'].startswith('Copper,')} ==
            {'Copper,L1,Top', 'Copper,L2,Bot'}, 'Gerber copper functions differ')
    geometry = r'(?:D01|D03|G36|G37)\*'
    require(not re.search(geometry, (fabrication / 'click-counter-Q4-F_Paste.gtp').read_text()),
            'Top paste must be empty for the home-fitted display and switches')
    require(re.search(geometry, (fabrication / 'click-counter-Q4-B_Paste.gbp').read_text()),
            'Bottom SMT paste geometry missing')
    for layer in ('F_Cu.gtl', 'B_Cu.gbl', 'Edge_Cuts.gm1'):
        require(re.search(geometry, (fabrication / ('click-counter-Q4-' + layer)).read_text()), 'Empty native geometry: ' + layer)
    with zipfile.ZipFile(directory / 'click-counter-Q4-Gerbers.zip') as archive:
        require(len(archive.namelist()) == len(expected) and set(archive.namelist()) == expected and
                archive.testzip() is None, 'Gerber ZIP members/corruption differ')
        require(all(archive.read(name) == (fabrication / name).read_bytes() for name in expected),
                'Gerber ZIP bytes differ from native exports')
    for side in ('top', 'bottom'):
        svg = ET.parse(directory / f'assembly-{side}-Q4.svg').getroot()
        require(svg.tag == '{http://www.w3.org/2000/svg}svg' and
                any(node.tag.rsplit('}', 1)[-1] in {'path', 'polyline', 'polygon', 'circle', 'rect'}
                    for node in svg.iter()), 'Empty or malformed assembly SVG')
    actual_files = {p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file()}
    require(actual_files == EXPORT_NAMES, 'Unexpected export product set')
    for path in directory.rglob('*'):
        if path.is_file() and path.suffix != '.zip':
            data = path.read_text(encoding='utf-8')
            require(not re.search(r'/Users/|/private/|file://|(?:[A-Z]:\\Users\\)', data),
                    f'Private local path in public export: {path.name}')
    return {'engineering_pcb_bom_rows': 70, 'engineering_complete_bom_rows': 73,
            'jlc_smt_bom_and_cpl_rows': 67, 'native_placement_rows': 70, 'home_completion_rows': 3,
            'separate_header_rows': 1, 'home_solder_joints_per_board': 18,
            'offboard_rows': 2, 'offboard_pack_and_caps_unqualified': True,
            'copper_layers': 2, 'gerber_and_drill_files': len(expected), 'top_paste_geometry': False,
            'bottom_paste_geometry': True, 'archive_members_equal_native_exports': True,
            'full_board_simulation_or_hardware_qualification': False}


def saved_validation():
    # No --kicad-cli: the verifier checks the saved, source-bound native evidence;
    # this exporter never creates a new native-validation claim for an unrouted board.
    subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/verify_q4.py')], check=True, cwd=ROOT)
    result = json.loads(VALIDATION.read_text())
    require(result['status'] == 'PASS_NATIVE_DESIGN_CHECKS_ONLY' and result['hardware_tested'] is False and
            result['manufacturing_released'] is False, 'Current saved native validation is required')
    return result


def input_hashes(validation):
    paths = {BOARD, MODEL, VALIDATION, STOCK, HARDWARE, Path(__file__).resolve()}
    for mapping in ('inputs_sha256', 'reports_sha256'):
        for name, expected in validation[mapping].items():
            path = (ROOT / name).resolve()
            require(path.is_relative_to(ROOT) and not Path(name).is_absolute(), 'Non-public validation source path')
            require(digest(path) == expected, 'Changed native source or report: ' + name)
            paths.add(path)
    return {path.relative_to(ROOT).as_posix(): digest(path) for path in sorted(paths)}


def review_readme():
    return '''# Q4 engineering review exports

These files are for engineering review only. Hardware has not been physically
qualified. No upload, quotation, purchase or manufacturing release is authorized.

- `BOM-JLCPCB-Q4.csv` has four unambiguous import columns and exactly 67 SMT
  references. `CPL-JLCPCB-Q4.csv` contains those same 67 references, on the bottom.
- `BOM-PCBA-Q4.csv` and `placements-KiCad-Q4.csv` describe all 70 fitted board
  parts. The native placements include DS1/SW1/SW2 for engineering review.
- `HOME-COMPLETION-Q4.csv` lists DS1 and the two key switches, separately sourced
  as loose retail parts. Retail screening quantities are shown once per exact
  MPN group, so SW1/SW2 share one rounded switch order. These are not purchases.
  Fit the rear key plate BEFORE soldering switch leads.
  Complete the seven-pin display header with the front cover removed: 14 joints
  across module and host, plus four key-switch joints. Physical fit remains open.
- `SEPARATE-HARDWARE-Q4.csv` accounts for one PZ254V-11-07P interposer header.
  It shares DS1's holes and has no additional CPL row. Header inclusion with the
  module is unknown; count it once, and avoid a duplicate if supplied together.
- `OFFBOARD-items-Q4.csv` retains one prepared rechargeable pack including NTC
  harness and two keycaps as explicitly unqualified sourcing/fit requirements.
  `BOM-Q4.csv` combines the 70 board rows, one header row and two offboard rows.
  The board's 16 test/mounting features are neither purchased parts nor DNP parts.
- The native two-layer Gerbers/drills, their exact ZIP, and top/bottom assembly
  SVGs are review outputs. No top stencil paste is present; SMT is on the bottom.

CPL X/Y, rotations and sides come from KiCad's native placement export. KiCad
uses a negative Y coordinate here. These values are checked against the source
model; actual importer coordinate/orientation handling needs later authorized
assembly review. No manufacturer-specific rotation correction is assumed.

Stock counts are timestamped, unreserved catalog observations in `stock.json`;
loose home-part supply is separately checked through LCSC retail. Quantities for
ten boards include research spares rounded to retail packs, not confirmed
assembler attrition or a purchase. Neither inventory nor file agreement proves
battery safety, power/USB operation, display function, solder process or fit.
See `export-manifest-Q4.json` for exact source/output hashes and checks.
'''


def export(args, output):
    # Remove a previous success marker before attempting a replacement. Failed
    # exports leave no current success marker; all new products are staged first.
    MANIFEST.unlink(missing_ok=True)
    validation = saved_validation()
    initial = input_hashes(validation)
    model, stock, hardware = (json.loads(path.read_text()) for path in (MODEL, STOCK, HARDWARE))
    source_checks = validate_sources(model, stock, hardware, digest(MODEL))
    cli_path = Path(args.kicad_cli).resolve()
    require(cli_path.is_file(), 'KiCad CLI does not exist')
    require(digest(cli_path) == validation['tool_sha256'], 'Export/native-validation KiCad executables differ')
    tool = {'version': subprocess.check_output([str(cli_path), 'version'], text=True).strip(), 'sha256': digest(cli_path)}
    require(tool['version'].startswith('10.'), 'KiCad 10 required')
    output.mkdir(exist_ok=True, parents=True)
    write_tables(output, model, stock, hardware)
    commands = []

    def cli(*arguments):
        command = [str(cli_path), 'pcb', 'export', *map(str, arguments), str(BOARD)]
        subprocess.run(command, check=True, cwd=ROOT)
        commands.append(['<kicad-cli>'] + [v.replace(str(output), '<output>').replace(str(ROOT) + '/', '') for v in command[1:]])

    fabrication = output / 'gerbers'
    fabrication.mkdir()
    cli('gerbers', '--output', fabrication, '--layers',
        'F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,F.Paste,B.Paste,Edge.Cuts', '--subtract-soldermask')
    cli('drill', '--output', fabrication, '--excellon-separate-th', '--excellon-units', 'mm',
        '--excellon-oval-format', 'route', '--generate-report', '--report-path', output / 'drill-report-Q4.txt')
    cli('pos', '--output', output / 'placements-KiCad-Q4.csv', '--format', 'csv', '--units', 'mm', '--side', 'both', '--exclude-dnp')
    positions = native_positions(output, model)
    write_csv(output / 'CPL-JLCPCB-Q4.csv', CPL_HEADER, cpl_rows(positions, model))
    for side, layer in [('top', 'F'), ('bottom', 'B')]:
        options = ['svg', '--output', output / f'assembly-{side}-Q4.svg', '--mode-single', '--layers',
                   f'{layer}.Cu,{layer}.Fab,{layer}.SilkS,Edge.Cuts', '--fit-page-to-board',
                   '--exclude-drawing-sheet', '--sketch-pads-on-fab-layers']
        if side == 'bottom':
            options.append('--mirror')
        cli(*options)
    deterministic_zip(output)
    (output / 'REVIEW-EXPORTS-Q4.md').write_text(review_readme(), encoding='utf-8')
    checks = validate_exports(output, model, stock, hardware)
    require(input_hashes(validation) == initial, 'Design, stock or validation changed during export')
    require(saved_validation() == validation, 'Saved validation changed during export')
    products = [p for p in sorted(output.rglob('*')) if p.is_file()]
    manifest = {
        'schema_version': 1, 'revision': 'Q4 engineering review candidate', 'status': 'PASS_REVIEW_EXPORT_CHECKS_ONLY',
        'hardware_tested': False, 'manufacturing_released': False, 'vendor_upload_authorized': False,
        'quote_pause': True, 'source_board_sha256': initial[BOARD.relative_to(ROOT).as_posix()],
        'inputs_sha256': initial, 'kicad_cli': tool, 'commands': commands,
        'source_checks': source_checks, 'export_checks': checks,
        'files': {str((DEST / p.relative_to(output)).relative_to(ROOT)):
                  {'bytes': p.stat().st_size, 'sha256': digest(p)} for p in products},
    }
    DEST.mkdir(exist_ok=True, parents=True)
    if (DEST / 'gerbers').exists():
        shutil.rmtree(DEST / 'gerbers')
    for source in products:
        target = DEST / source.relative_to(output)
        target.parent.mkdir(exist_ok=True, parents=True)
        shutil.copyfile(source, target)
    for name, entry in manifest['files'].items():
        require(digest(ROOT / name) == entry['sha256'] and (ROOT / name).stat().st_size == entry['bytes'],
                'Published output copy differs: ' + name)
    require(input_hashes(validation) == initial, 'Sources changed while publishing staged exports')
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print('Q4 review exports checked: 70 board parts, 67 SMT BOM/CPL, 3 home THT parts and separate header. Hardware unqualified; quote pause remains.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kicad-cli', required=True)
    args = parser.parse_args()
    try:
        with tempfile.TemporaryDirectory(prefix='count-fidget-q4-export-') as folder:
            export(args, Path(folder))
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError, zipfile.BadZipFile, ET.ParseError) as error:
        print('FAIL: ' + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
