"""Bundle the reviewed Q3 quotation candidate without changing submitted Q1."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile
from package_rfq import markdown, page
from export_q3 import EXPORT_NAMES, validate_exports

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_member(name):
    path=Path(name)
    assert name==path.as_posix() and not path.is_absolute() and '..' not in path.parts, 'Unsafe package path: '+name
    assert not any(p.startswith('.') or p.lower() in ('private','__pycache__','node_modules') for p in path.parts), 'Private/hidden package path: '+name
    assert path.suffix.lower() not in ('.dsn','.ses','.pyc','.kicad_prl','.eml','.mbox'), 'Unapproved working/private artifact: '+name
    actual=ROOT/path
    assert actual.resolve().is_relative_to(ROOT) and not actual.is_symlink(), 'External or symlinked package member: '+name
    return name


def package_members(native,export,mechanical,firmware):
    """Only declared current artifacts; never collect arbitrary folder contents."""
    members=set(native['inputs_sha256'])|set(export['inputs_sha256'])
    model=json.loads((ROOT/'electronics/q3/netlist-Q3.json').read_text())
    used_footprints={'electronics/q3/'+p['footprint'].replace(':','.pretty/')+'.kicad_mod' for p in model['parts']}
    controlled_footprints={n for n in members if n.endswith('.kicad_mod')}
    assert controlled_footprints==used_footprints, 'Native evidence must omit unused legacy footprints before packaging'
    assert set(export['files'])=={'procurement/q3/'+n for n in EXPORT_NAMES}, 'Export manifest file set differs'
    members.update(export['files'])
    mechanical_names={'base-Q3.stl','lid-front-Q3.stl','lid-rear-Q3.stl','battery-keeper-Q3.stl',
                      'enclosure-Q3.step','board-geometry.json','fit-report.json',
                      'assembled-Q3.png','exploded-Q3.png','interior-Q3.png','battery-bay-Q3.png'}
    assert set(mechanical['outputs'])==mechanical_names, 'Mechanical outputs missing current renders or contain obsolete artifacts'
    members.update('mechanical/q3/'+n for n in mechanical_names|{'build-manifest.json','README.md'})
    members.update(firmware['inputs'])
    members.update('firmware/q3-oled/build/'+n for n in set(firmware['outputs'])|{'build-manifest.json'})
    members.update('verification/'+n for n in ('q3-native-drc.json','q3-native-erc.json','q3-validation.json','q3-native-netlist.xml','q3-negative-checks.json'))
    members.update('scripts/'+n for n in ('export_q3.py','package_q3.py','package_rfq.py','build_q3_enclosure.py',
                                         'verify_project.py','test_verify_q3.py','build_firmware.py'))
    # Unchanged counter reference copies are consumed by the Q3 firmware build.
    members.update('firmware/'+n for n in ('counter.c','counter.h','test_counter.c'))
    members.update('procurement/q3/'+n for n in ('RFQ-Q3.md','RFQ-Q3.html','export-manifest-Q3.json',
                   'passive-alternatives.json','passive-alternatives.md','stock-alternatives.md'))
    members.update('docs/'+n for n in ('q3-power-design.md','q3-display-selection.md','q3-display-mechanics.md','q3-cost-decisions.md',
                   'q3-layout-routing.md','build-and-verify.md','review-firmware-Q3.md','review-hardware-Q3.md','review-mechanical-Q3.md',
                   'open-issues.md','q2-power-design.md','q2-power-independent-review.md','review-charger-Q2.md','review-protection-Q2.md'))
    for name in members:
        safe_member(name)
        assert not (name.endswith(('.hex','.elf','.map','.lst')) and not name.startswith('firmware/q3-oled/build/')), 'Obsolete program image in package'
        assert not name.startswith(('electronics/q1/','procurement/q1/','procurement/q2/','mechanical/q2/','firmware/q2-lcd-check/'))
    return members


def main():
    subprocess.run([sys.executable, str(ROOT/'scripts/verify_project.py')], check=True, cwd=ROOT)
    subprocess.run([sys.executable, str(ROOT/'scripts/verify_q3.py')], check=True, cwd=ROOT)
    subprocess.run([sys.executable, str(ROOT/'scripts/build_firmware_q3.py'), '--verify-only'], check=True, cwd=ROOT)
    native = json.loads((ROOT/'verification/q3-validation.json').read_text())
    negatives=json.loads((ROOT/'verification/q3-negative-checks.json').read_text())
    negative_inputs={'electronics/q3/click-counter-Q3.kicad_pcb','verification/q3-validation.json',
                     'verification/q3-native-drc.json','verification/q3-native-erc.json','verification/q3-native-netlist.xml',
                     'scripts/test_verify_q3.py','scripts/verify_q3.py'}
    assert negatives['schema_version']==1 and set(negatives['inputs_sha256'])==negative_inputs
    assert all(sha(ROOT/n)==h for n,h in negatives['inputs_sha256'].items()), 'Adversarial test evidence is stale'
    negative_result=negatives['result']
    assert negative_result['status']=='PASS' and negative_result['negative_corruptions_rejected']==len(negative_result['checks'])==62
    assert negative_result['full_semantic_integration'] is True and negative_result['bound_native_evidence_checked'] is True
    assert negative_result['fresh_native_checks_run_by_this_test'] is False
    export = json.loads((ROOT/'procurement/q3/export-manifest-Q3.json').read_text())
    board = ROOT/'electronics/q3/click-counter-Q3.kicad_pcb'
    assert sha(board) == export['source_board_sha256'], 'Exports refer to an older board'
    for name, expected in export['inputs_sha256'].items():
        safe_member(name)
        assert sha(ROOT/name) == expected, 'Stale export input: '+name
    for name, expected in export['files'].items():
        safe_member(name)
        assert sha(ROOT/name) == expected['sha256'], name
        assert (ROOT/name).stat().st_size == expected['bytes'], 'Export size differs: '+name
    assert export['export_checks']==validate_exports(ROOT/'procurement/q3',json.loads((ROOT/'electronics/q3/netlist-Q3.json').read_text()))
    mechanical = json.loads((ROOT/'mechanical/q3/build-manifest.json').read_text())
    assert mechanical['board'] == sha(board), 'Mechanical board hash is stale'
    assert mechanical['model'] == sha(ROOT/'electronics/q3/netlist-Q3.json'), 'Mechanical model hash is stale'
    assert mechanical['generator'] == sha(ROOT/'scripts/build_q3_enclosure.py'), 'Mechanical generator hash is stale'
    for name, expected in mechanical['outputs'].items():
        assert Path(name).name==name, 'Mechanical manifest path must be a basename'
        assert sha(ROOT/'mechanical/q3'/name) == expected, 'Stale mechanical output: '+name
    fit = json.loads((ROOT/'mechanical/q3/fit-report.json').read_text())
    assert fit['reported_intersections'] == [], 'Mechanical intersections remain'
    assert all(v == 0 for v in fit['shell_intersections_mm3'].values()), 'Shell intersections remain'
    assert set(fit['valid_solids']) == {'base','lid-front','lid-rear','battery-keeper'}
    assert all(v['valid'] and v['count'] == 1 for v in fit['valid_solids'].values()), 'Invalid mechanical print solids'
    assert set(fit['stl_mesh_checks'])=={'base-Q3.stl','lid-front-Q3.stl','lid-rear-Q3.stl','battery-keeper-Q3.stl'}
    assert all(v['nonmanifold_edges']==0 and v['triangles']>0 for v in fit['stl_mesh_checks'].values()), 'Invalid print mesh'
    assert fit['source_board_sha256']==mechanical['board'] and fit['source_model_sha256']==mechanical['model'] and fit['generator_sha256']==mechanical['generator']
    assert set(fit['firmware_renderer_sha256'])=={'oled.c','oled.h','counter.h'}
    assert all(sha(ROOT/'firmware/q3-oled'/n)==h for n,h in fit['firmware_renderer_sha256'].items()), 'Mechanical OLED rendering source is stale'
    firmware = json.loads((ROOT/'firmware/q3-oled/build/build-manifest.json').read_text())
    rfq = ROOT/'procurement/q3/RFQ-Q3.md'
    (rfq.with_suffix('.html')).write_text(page('Count Fidget Q3 — quotation only', markdown(rfq.read_text())))
    members=package_members(native,export,mechanical,firmware)
    dist = ROOT/'dist/q3'
    dist.mkdir(exist_ok=True, parents=True)
    archive = dist/'click-counter-Q3-RFQ.zip'
    entries = {}
    with tempfile.TemporaryDirectory(prefix='.q3-package-',dir=dist) as folder:
        staged=Path(folder)/archive.name
        with zipfile.ZipFile(staged,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as zipped:
            for name in sorted(members):
                data=(ROOT/name).read_bytes()
                info=zipfile.ZipInfo(name,date_time=(2026,9,15,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
                zipped.writestr(info,data)
                entries[name]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
        assert all(sha(ROOT/n)==r['sha256'] for n,r in entries.items()), 'Package input changed while archiving'
        with zipfile.ZipFile(staged) as zipped:
            assert zipped.testzip() is None and len(zipped.namelist())==len(members) and set(zipped.namelist())==members
            assert all(hashlib.sha256(zipped.read(n)).hexdigest()==r['sha256'] for n,r in entries.items())
        subprocess.run([sys.executable,str(ROOT/'scripts/verify_q3.py')],check=True,cwd=ROOT)
        subprocess.run([sys.executable,str(ROOT/'scripts/build_firmware_q3.py'),'--verify-only'],check=True,cwd=ROOT)
        assert all(sha(ROOT/n)==r['sha256'] for n,r in entries.items()), 'Package input changed before publication'
        manifest={'revision':'Q3 engineering quotation candidate','purpose':'Vendor review and quotation only; no paid procurement or manufacturing release',
                  'hardware_tested':False,'manufacturing_released':False,'source_board_sha256':sha(board),
                  'file':archive.name,'bytes':staged.stat().st_size,'sha256':sha(staged),'members':entries,
                  'scope_notes':['Q3 production artifacts only; Q2 model and review documents are explicit reference inputs.',
                                 'The unchanged OFFBOARD-items-Q1.csv is an export-source reference; quote the generated OFFBOARD-items-Q3.csv.',
                                 'Full-repository history checks require the original frozen Q1/Q2 files, which are intentionally not distributed as program images.']}
        staged_manifest=Path(folder)/'manifest-Q3.json';staged_manifest.write_text(json.dumps(manifest,indent=2)+'\n')
        staged.replace(archive);staged_manifest.replace(dist/'manifest-Q3.json')
    print(f'Packaged {len(entries)} Q3 review files: {archive.relative_to(ROOT)} ({archive.stat().st_size} bytes)')
    print('SHA256',manifest['sha256'])


if __name__ == '__main__':
    main()
