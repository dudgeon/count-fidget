"""Export separately identified Q2 quotation files from a validated native PCB.

Requires a successful, current scripts/verify_q2.py result. This is an export,
not release approval; no Q1 artifact is regenerated or changed.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'procurement/q2'
BOARD = ROOT / 'electronics/q2/click-counter-Q2.kicad_pcb'


def write_csv(path, header, rows):
    with path.open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export(args, OUT):
    subprocess.run([sys.executable, str(ROOT / 'scripts/verify_q2.py')], check=True, cwd=ROOT)
    inputs = [BOARD, ROOT/'electronics/q2/netlist-Q2.json', ROOT/'verification/q2-validation.json',
              ROOT/'procurement/BOM-JLCPCB-Q1.csv', ROOT/'procurement/OFFBOARD-items-Q1.csv', Path(__file__).resolve()]
    initial = {str(path.relative_to(ROOT)): digest(path) for path in inputs}
    commands = []
    cli_path = Path(args.kicad_cli).resolve()
    tool = {'version':subprocess.check_output([str(cli_path),'version'],text=True).strip(), 'sha256':digest(cli_path)}
    OUT.mkdir(exist_ok=True, parents=True)
    model = json.loads((ROOT / 'electronics/q2/netlist-Q2.json').read_text())
    parts = [p for p in model['parts'] if not p['ref'].startswith(('TP', 'H'))]
    assert len(parts) == 50
    header = ['Comment','Designator','Footprint','Quantity','Manufacturer','Manufacturer Part Number','Assembly','Notes']
    rows = [[p['value'],p['ref'],p['footprint'],1,p['manufacturer'],p['mpn'],p['side'],p['notes']] for p in parts]
    write_csv(OUT / 'BOM-PCBA-Q2.csv', header, rows)
    # Carry only previously verified identity matches for unchanged exact MPNs.
    # A catalog identifier is not stock allocation or qualification approval.
    known = {}
    with (ROOT / 'procurement/BOM-JLCPCB-Q1.csv').open(newline='') as stream:
        for row in csv.DictReader(stream):
            known[(row['Manufacturer'],row['Manufacturer Part Number'])] = row['LCSC Part #']
    known[('Texas Instruments','TPS7A0230PDBVR')] = 'C3747031'
    known[('Texas Instruments','TLV7032DGKR')] = 'C2863894'
    adapter = []
    for p, row in zip(parts, rows):
        adapter.append([p['mpn']] + row[1:] + [p['value'],known.get((p['manufacturer'],p['mpn']),'')])
    write_csv(OUT / 'BOM-JLCPCB-Q2.csv', header + ['Source Label','LCSC Part #'], adapter)
    shutil.copyfile(ROOT / 'procurement/OFFBOARD-items-Q1.csv', OUT / 'OFFBOARD-items-Q2.csv')
    with (OUT / 'OFFBOARD-items-Q2.csv').open(newline='') as stream:
        offboard = list(csv.reader(stream))[1:]
    write_csv(OUT / 'BOM-Q2.csv', header, rows + offboard)
    def cli(*arguments):
        command = [str(cli_path), 'pcb', 'export', *map(str,arguments), str(BOARD)]
        subprocess.run(command, check=True, cwd=ROOT)
        commands.append(['<kicad-cli>']+[v.replace(str(OUT),'<output>').replace(str(ROOT)+'/', '') for v in command[1:]])
    fabrication = OUT / 'gerbers'
    fabrication.mkdir(exist_ok=True)
    cli('gerbers','--output',fabrication,'--layers','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,F.Paste,B.Paste,Edge.Cuts','--subtract-soldermask')
    cli('drill','--output',fabrication,'--excellon-separate-th','--excellon-units','mm','--excellon-oval-format','route','--generate-report','--report-path',OUT / 'drill-report-Q2.txt')
    cli('pos','--output',OUT / 'placements-KiCad-Q2.csv','--format','csv','--units','mm','--side','both','--exclude-dnp')
    with (OUT / 'placements-KiCad-Q2.csv').open(newline='') as stream:
        positions = list(csv.DictReader(stream))
    assert len(positions) == len({r['Ref'] for r in positions}) == 50
    assert {r['Ref'] for r in positions} == {p['ref'] for p in parts}
    by_ref = {p['ref']: p for p in parts}
    for row in positions:
        part = by_ref[row['Ref']]
        assert abs(float(row['PosX']) - part['x']) < 1e-6
        assert abs(float(row['PosY']) + part['y']) < 1e-6
        assert abs((float(row['Rot']) - part['rotation'] + 180) % 360 - 180) < 1e-6
        assert row['Side'] == part['side']
    write_csv(OUT / 'CPL-JLCPCB-Q2.csv',['Designator','Mid X','Mid Y','Layer','Rotation'],
              [[r['Ref'],r['PosX']+'mm',r['PosY']+'mm',r['Side'].title(),r['Rot']] for r in positions])
    for side, layer in [('top','F'),('bottom','B')]:
        options = ['svg','--output',OUT / f'assembly-{side}-Q2.svg','--mode-single','--layers',f'{layer}.Cu,{layer}.Fab,{layer}.SilkS,Edge.Cuts','--fit-page-to-board','--exclude-drawing-sheet','--sketch-pads-on-fab-layers']
        if side == 'bottom':
            options.append('--mirror')
        cli(*options)
    archive = OUT / 'click-counter-Q2-Gerbers.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as zipped:
        for path in sorted(fabrication.iterdir()):
            assert path.is_file() and path.name.startswith('click-counter-Q2-')
            zipped.write(path,path.name)
    assert initial == {str(path.relative_to(ROOT)): digest(path) for path in inputs}, 'Design changed during export'
    subprocess.run([sys.executable, str(ROOT/'scripts/verify_q2.py')],check=True,cwd=ROOT)
    products = [p for p in sorted(OUT.rglob('*')) if p.is_file()]
    manifest = {'revision':'Q2 engineering quotation candidate','manufacturing_released':False,
                'source_board_sha256':initial[str(BOARD.relative_to(ROOT))], 'inputs_sha256':initial,
                'kicad_cli':tool,'commands':commands,
                'files':{str((DEST/p.relative_to(OUT)).relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':digest(p)} for p in products}}
    DEST.mkdir(exist_ok=True,parents=True)
    # Only this generator's exact Q2 fabrication folder is replaced. Staging
    # starts empty, so an obsolete drill or layer cannot enter the new ZIP.
    if (DEST/'gerbers').exists():
        shutil.rmtree(DEST/'gerbers')
    for source in products:
        target = DEST/source.relative_to(OUT)
        target.parent.mkdir(exist_ok=True,parents=True)
        shutil.copyfile(source,target)
    (DEST/'export-manifest-Q2.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Exported Q2 fabrication, 50-ref BOM/CPL and native assembly views. Quote only; hardware unqualified.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kicad-cli', required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='count-fidget-q2-export-') as folder:
        export(args, Path(folder))


if __name__ == '__main__':
    main()
