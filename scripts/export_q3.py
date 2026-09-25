"""Export separately identified Q3 quotation files from a validated native PCB.

Requires a successful, current scripts/verify_q3.py result. This is an export,
not release approval; no Q1 artifact is regenerated or changed.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'procurement/q3'
BOARD = ROOT / 'electronics/q3/click-counter-Q3.kicad_pcb'
GERBER_SUFFIXES = {'F_Cu.gtl','B_Cu.gbl','F_Mask.gts','B_Mask.gbs','F_Silkscreen.gto','B_Silkscreen.gbo',
                  'F_Paste.gtp','B_Paste.gbp','Edge_Cuts.gm1','PTH.drl','NPTH.drl','job.gbrjob'}
EXPORT_NAMES = {'BOM-PCBA-Q3.csv','BOM-JLCPCB-Q3.csv','BOM-Q3.csv','OFFBOARD-items-Q3.csv',
                'CPL-JLCPCB-Q3.csv','placements-KiCad-Q3.csv','assembly-top-Q3.svg','assembly-bottom-Q3.svg',
                'click-counter-Q3-Gerbers.zip','drill-report-Q3.txt'} | {'gerbers/click-counter-Q3-'+s for s in GERBER_SUFFIXES}


def write_csv(path, header, rows):
    with path.open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_exports(directory, model):
    """Check the actual generated files; historical layers/parts cannot slip in."""
    parts={p['ref']:p for p in model['parts'] if not p['ref'].startswith(('TP','H'))}
    assert len(parts)==70 and model['layers']==2 and len({p['mpn'] for p in parts.values()})==43
    def rows(name):
        with (directory/name).open(newline='') as stream:return list(csv.DictReader(stream))
    for name,jlc in [('BOM-PCBA-Q3.csv',False),('BOM-JLCPCB-Q3.csv',True)]:
        data=rows(name)
        assert len(data)==70 and {r['Designator'] for r in data}==set(parts), 'BOM reference set differs'
        for row in data:
            part=parts[row['Designator']]
            assert row['Quantity']=='1' and row['Manufacturer Part Number']==part['mpn'] and row['Manufacturer']==part['manufacturer']
            assert row['Assembly']==part['side'] and row['Footprint']==part['footprint']
            assert row['Comment']==(part['mpn'] if jlc else part['value'])
            if jlc:assert row['Source Label']==part['value'] and row['LCSC Part #']==part['lcsc']
    offboard=rows('OFFBOARD-items-Q3.csv')
    assert len(offboard)==2 and {r['Designator'] for r in offboard}=={'BAT1','K1,K2'}, 'Offboard battery or loose keycaps omitted'
    assert {r['Designator']:r['Quantity'] for r in offboard}=={'BAT1':'1','K1,K2':'2'}
    assert all(r['Footprint']=='OFFBOARD' for r in offboard)
    assert rows('BOM-Q3.csv')==rows('BOM-PCBA-Q3.csv')+offboard, 'Complete BOM differs from PCBA plus offboard scope'
    native=rows('placements-KiCad-Q3.csv');cpl=rows('CPL-JLCPCB-Q3.csv')
    assert len(native)==len(cpl)==70 and {r['Ref'] for r in native}=={r['Designator'] for r in cpl}==set(parts)
    for row in native:
        p=parts[row['Ref']]
        assert abs(float(row['PosX'])-p['x'])<1e-6 and abs(float(row['PosY'])+p['y'])<1e-6
        assert abs((float(row['Rot'])-p['rotation']+180)%360-180)<1e-6 and row['Side']==p['side']
    assert cpl==[dict(zip(['Designator','Mid X','Mid Y','Layer','Rotation'],
                        [r['Ref'],r['PosX']+'mm',r['PosY']+'mm',r['Side'].title(),r['Rot']])) for r in native]
    fabrication=directory/'gerbers'
    expected={'click-counter-Q3-'+s for s in GERBER_SUFFIXES}
    assert {p.name for p in fabrication.iterdir()}==expected, 'Unexpected/missing fabrication file or obsolete inner copper layer'
    job=json.loads((fabrication/'click-counter-Q3-job.gbrjob').read_text())
    assert job['GeneralSpecs']['LayerNumber']==2 and job['GeneralSpecs']['BoardThickness']==1.0
    assert job['GeneralSpecs']['ProjectId']['Name']=='click-counter-Q3'
    assert {x['Name'] for x in job['MaterialStackup'] if x['Type']=='Copper'}=={'F.Cu','B.Cu'}
    attributes=job['FilesAttributes']
    assert len(attributes)==9 and {x['Path'] for x in attributes}==expected-{'click-counter-Q3-'+s for s in ('PTH.drl','NPTH.drl','job.gbrjob')}
    assert {x['FileFunction'] for x in attributes if x['FileFunction'].startswith('Copper,')}=={'Copper,L1,Top','Copper,L2,Bot'}
    # No top component receives stencil paste: OLED is separately soldered and
    # switches are through-hole. Validate the actual Gerber, not only its name.
    paste=(fabrication/'click-counter-Q3-F_Paste.gtp').read_text()
    assert not re.search(r'(?:D01|D03|G36|G37)\*',paste), 'Unexpected top stencil geometry; OLED must have no paste'
    with zipfile.ZipFile(directory/'click-counter-Q3-Gerbers.zip') as zipped:
        assert len(zipped.namelist())==len(expected) and set(zipped.namelist())==expected and zipped.testzip() is None
        assert all(zipped.read(name)==(fabrication/name).read_bytes() for name in expected), 'Gerber ZIP differs from native exports'
    return {'fitted_references':70,'distinct_exact_mpns':43,'offboard_physical_items':3,'cpl_references':70,
            'copper_layers':2,'gerber_and_drill_files':len(expected),'top_paste_geometry':False,'archive_members_equal_exports':True}


def export(args, OUT):
    subprocess.run([sys.executable, str(ROOT / 'scripts/verify_q3.py')], check=True, cwd=ROOT)
    inputs = [BOARD, ROOT/'electronics/q3/netlist-Q3.json', ROOT/'verification/q3-validation.json',
              ROOT/'procurement/q3/live-stock-2026-09-15.json', ROOT/'procurement/OFFBOARD-items-Q1.csv', Path(__file__).resolve()]
    initial = {str(path.relative_to(ROOT)): digest(path) for path in inputs}
    commands = []
    cli_path = Path(args.kicad_cli).resolve()
    tool = {'version':subprocess.check_output([str(cli_path),'version'],text=True).strip(), 'sha256':digest(cli_path)}
    OUT.mkdir(exist_ok=True, parents=True)
    model = json.loads((ROOT / 'electronics/q3/netlist-Q3.json').read_text())
    parts = [p for p in model['parts'] if not p['ref'].startswith(('TP', 'H'))]
    assert len(parts) == 70
    header = ['Comment','Designator','Footprint','Quantity','Manufacturer','Manufacturer Part Number','Assembly','Notes']
    rows = [[p['value'],p['ref'],p['footprint'],1,p['manufacturer'],p['mpn'],p['side'],p['notes']] for p in parts]
    write_csv(OUT / 'BOM-PCBA-Q3.csv', header, rows)
    # Exact live-catalog identity codes are part of the controlled Q3 model.
    # They are not allocation, sourcing approval or qualification evidence.
    adapter = []
    for p, row in zip(parts, rows):
        adapter.append([p['mpn']] + row[1:] + [p['value'],p['lcsc']])
    write_csv(OUT / 'BOM-JLCPCB-Q3.csv', header + ['Source Label','LCSC Part #'], adapter)
    shutil.copyfile(ROOT / 'procurement/OFFBOARD-items-Q1.csv', OUT / 'OFFBOARD-items-Q3.csv')
    # Battery/harness and keycaps remain offboard; never invent placements or DNP them.
    with (OUT / 'OFFBOARD-items-Q3.csv').open(newline='') as stream:
        offboard = list(csv.reader(stream))[1:]
    write_csv(OUT / 'BOM-Q3.csv', header, rows + offboard)
    def cli(*arguments):
        command = [str(cli_path), 'pcb', 'export', *map(str,arguments), str(BOARD)]
        subprocess.run(command, check=True, cwd=ROOT)
        commands.append(['<kicad-cli>']+[v.replace(str(OUT),'<output>').replace(str(ROOT)+'/', '') for v in command[1:]])
    fabrication = OUT / 'gerbers'
    fabrication.mkdir(exist_ok=True)
    cli('gerbers','--output',fabrication,'--layers','F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,F.Paste,B.Paste,Edge.Cuts','--subtract-soldermask')
    cli('drill','--output',fabrication,'--excellon-separate-th','--excellon-units','mm','--excellon-oval-format','route','--generate-report','--report-path',OUT / 'drill-report-Q3.txt')
    cli('pos','--output',OUT / 'placements-KiCad-Q3.csv','--format','csv','--units','mm','--side','both','--exclude-dnp')
    with (OUT / 'placements-KiCad-Q3.csv').open(newline='') as stream:
        positions = list(csv.DictReader(stream))
    assert len(positions) == len({r['Ref'] for r in positions}) == 70
    assert {r['Ref'] for r in positions} == {p['ref'] for p in parts}
    by_ref = {p['ref']: p for p in parts}
    for row in positions:
        part = by_ref[row['Ref']]
        assert abs(float(row['PosX']) - part['x']) < 1e-6
        assert abs(float(row['PosY']) + part['y']) < 1e-6
        assert abs((float(row['Rot']) - part['rotation'] + 180) % 360 - 180) < 1e-6
        assert row['Side'] == part['side']
    write_csv(OUT / 'CPL-JLCPCB-Q3.csv',['Designator','Mid X','Mid Y','Layer','Rotation'],
              [[r['Ref'],r['PosX']+'mm',r['PosY']+'mm',r['Side'].title(),r['Rot']] for r in positions])
    for side, layer in [('top','F'),('bottom','B')]:
        options = ['svg','--output',OUT / f'assembly-{side}-Q3.svg','--mode-single','--layers',f'{layer}.Cu,{layer}.Fab,{layer}.SilkS,Edge.Cuts','--fit-page-to-board','--exclude-drawing-sheet','--sketch-pads-on-fab-layers']
        if side == 'bottom':
            options.append('--mirror')
        cli(*options)
    archive = OUT / 'click-counter-Q3-Gerbers.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as zipped:
        for path in sorted(fabrication.iterdir()):
            assert path.is_file() and path.name.startswith('click-counter-Q3-')
            zipped.write(path,path.name)
    checks=validate_exports(OUT,model)
    assert initial == {str(path.relative_to(ROOT)): digest(path) for path in inputs}, 'Design changed during export'
    subprocess.run([sys.executable, str(ROOT/'scripts/verify_q3.py')],check=True,cwd=ROOT)
    products = [p for p in sorted(OUT.rglob('*')) if p.is_file()]
    assert {p.relative_to(OUT).as_posix() for p in products}==EXPORT_NAMES, 'Unexpected export products'
    manifest = {'revision':'Q3 engineering quotation candidate','manufacturing_released':False,
                'source_board_sha256':initial[str(BOARD.relative_to(ROOT))], 'inputs_sha256':initial,
                'kicad_cli':tool,'commands':commands,'export_checks':checks,
                'files':{str((DEST/p.relative_to(OUT)).relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':digest(p)} for p in products}}
    DEST.mkdir(exist_ok=True,parents=True)
    # Only this generator's exact Q3 fabrication folder is replaced. Staging
    # starts empty, so an obsolete drill or layer cannot enter the new ZIP.
    if (DEST/'gerbers').exists():
        shutil.rmtree(DEST/'gerbers')
    for source in products:
        target = DEST/source.relative_to(OUT)
        target.parent.mkdir(exist_ok=True,parents=True)
        shutil.copyfile(source,target)
    (DEST/'export-manifest-Q3.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Exported Q3 fabrication, 70-ref BOM/CPL and native assembly views. Quote only; hardware unqualified.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kicad-cli', required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='count-fidget-q3-export-') as folder:
        export(args, Path(folder))


if __name__ == '__main__':
    main()
