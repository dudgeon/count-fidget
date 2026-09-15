"""Bundle the reviewed Q2 quotation candidate without changing submitted Q1."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile
from package_rfq import markdown, page

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    subprocess.run([sys.executable, str(ROOT/'scripts/verify_project.py')], check=True, cwd=ROOT)
    subprocess.run([sys.executable, str(ROOT/'scripts/verify_q2.py')], check=True, cwd=ROOT)
    export = json.loads((ROOT/'procurement/q2/export-manifest-Q2.json').read_text())
    board = ROOT/'electronics/q2/click-counter-Q2.kicad_pcb'
    assert sha(board) == export['source_board_sha256'], 'Exports refer to an older board'
    for name, expected in export['inputs_sha256'].items():
        assert sha(ROOT/name) == expected, 'Stale export input: '+name
    for name, expected in export['files'].items():
        assert sha(ROOT/name) == expected['sha256'], name
    mechanical = json.loads((ROOT/'mechanical/q2/build-manifest.json').read_text())
    assert mechanical['board'] == sha(board), 'Mechanical board hash is stale'
    assert mechanical['model'] == sha(ROOT/'electronics/q2/netlist-Q2.json'), 'Mechanical model hash is stale'
    assert mechanical['generator'] == sha(ROOT/'scripts/build_q2_enclosure.py'), 'Mechanical generator hash is stale'
    for name, expected in mechanical['outputs'].items():
        assert sha(ROOT/'mechanical/q2'/name) == expected, 'Stale mechanical output: '+name
    fit = json.loads((ROOT/'mechanical/q2/fit-report.json').read_text())
    assert fit['reported_intersections'] == [], 'Mechanical intersections remain'
    assert all(v == 0 for v in fit['shell_intersections_mm3'].values()), 'Shell intersections remain'
    assert set(fit['valid_solids']) == {'base','lid','battery-keeper'}
    assert all(v['valid'] and v['count'] == 1 for v in fit['valid_solids'].values()), 'Invalid mechanical print solids'
    rfq = ROOT/'procurement/q2/RFQ-Q2.md'
    (rfq.with_suffix('.html')).write_text(page('Count Fidget Q2 — quotation only', markdown(rfq.read_text())))
    members = set()
    for folder in ('electronics/q2','procurement/q2','mechanical/q2','firmware/q2-lcd-check'):
        for p in (ROOT/folder).rglob('*'):
            if p.is_file() and p.suffix not in ('.dsn','.ses','.pyc','.kicad_prl') and '__pycache__' not in p.parts:
                members.add(p.relative_to(ROOT).as_posix())
    members.update('firmware/'+n for n in ('main_msp430.c','counter.c','counter.h','lcd_de188.c','lcd_de188.h','factory-display-info.hex'))
    members.update('verification/'+n for n in ('q2-native-drc.json','q2-native-erc.json','q2-validation.json','q2-native-netlist.xml'))
    members.update('scripts/'+n for n in ('build_firmware.py','run_host_tests.py','verify_project.py','verify_q2.py','build_q2_model.py','build_q2_schematic.py','build_q2_board.py','finish_q2_board.py','preroute_q2.py','sync_q2_board.py','kicad_sexpr.py','build_q2_enclosure.py','export_q2.py','package_q2.py','package_rfq.py'))
    members.add('electronics/netlist.json')
    members.update('docs/'+n for n in ('q2-power-design.md','q2-power-independent-review.md','q2-display-selection.md','q2-solder-mask-review.md','q2-candidate-independent-review.md','open-issues.md','adversarial-review-Q2.md','review-lcd-firmware-Q2.md','review-charger-Q2.md','review-protection-Q2.md','review-mechanical-Q2.md'))
    dist = ROOT/'dist/q2'
    dist.mkdir(exist_ok=True, parents=True)
    archive = dist/'click-counter-Q2-RFQ.zip'
    entries = {}
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as zipped:
        for name in sorted(members):
            path = ROOT/name
            data = path.read_bytes()
            info = zipfile.ZipInfo(name, date_time=(2026,9,15,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zipped.writestr(info,data)
            entries[name] = {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    manifest = {'revision':'Q2 engineering quotation candidate','purpose':'Vendor review and quotation only; no paid procurement or manufacturing release',
                'hardware_tested':False,'manufacturing_released':False,'source_board_sha256':sha(board),
                'file':archive.name,'bytes':archive.stat().st_size,'sha256':sha(archive),'members':entries}
    (dist/'manifest-Q2.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Packaged {len(entries)} Q2 review files: {archive.relative_to(ROOT)} ({archive.stat().st_size} bytes)')
    print('SHA256',manifest['sha256'])


if __name__ == '__main__':
    main()
