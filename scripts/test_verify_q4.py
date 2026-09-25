"""Adversarial Q4 verifier checks on temporary copies of a valid native baseline.

Default requires verify_q4.saved() to pass BEFORE any corruption. --semantic-only
requires a clean semantic baseline and omits native-evidence tests; it never
claims a valid routed/native baseline. --list needs no completed board. Every
negative must fail for its expected reason. No real design or report is edited,
no synthetic successful native report is created, and no KiCad run is performed.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

import verify_q4 as v


SEMANTIC_CASES = (
    'PCB supply-pad net changed', 'PCB pad position changed',
    'PCB physical drill changed', 'PCB pad size changed', 'PCB pad layer changed',
    'PCB component moved', 'PCB component flipped', 'PCB MPN changed',
    'PCB duplicate UUID', 'PCB route removed', 'PCB ground fill removed',
    'PCB outline vertex changed', 'PCB extra outline primitive',
    'PCB thickness changed', 'PCB inner layer added',
    'Schematic MPN changed', 'Schematic MPN duplicated',
    'Schematic MCU supply connection omitted', 'Schematic MCU pin duplicated',
    'Coherent MCU supply miswired despite independent contract',
    'Coherent regulator MPN changed despite independent contract',
)
BOUND_CASES = (
    'Bound source modified', 'Bound local footprint modified',
    'Bound circuit contract modified', 'Bound ERC bytes modified',
    'Bound DRC bytes modified', 'Bound native XML bytes modified',
    'Bound input digest changed', 'Bound report digest changed',
    'Bound status changed', 'Bound manufacture flag changed',
    'Bound native command drops parity', 'Bound semantic summary changed',
    'Bound native summary changed', 'DRC wrong source field',
    'ERC wrong source field', 'DRC missing warning severity',
    'DRC ignored clearance', 'DRC nonzero unconnected',
    'DRC nonzero parity', 'DRC nonzero physical violation',
    'ERC nonzero violation',
)


def write_tree(node):
    # Only the project's read-only parser consumes these test copies. Quoting
    # atoms avoids accidentally inventing a second S-expression root.
    return '(' + ' '.join(write_tree(n) for n in node) + ')' if isinstance(node, list) else json.dumps(node)


def by_ref(board, ref):
    return next(f for f in v.children(board, 'footprint') if v.property_value(f, 'Reference') == ref)


def pad(board, ref, pin):
    return next(p for p in v.children(by_ref(board, ref), 'pad') if p[1] == pin)


def flip_layer(node, key):
    item=v.child(node,key)
    item[1]='B.Cu' if item[1]=='F.Cu' else 'F.Cu'


def bump(node, key, index=1, amount=.1):
    item = v.child(node, key)
    item[index] = str(float(item[index]) + amount)


class Fixture:
    def __init__(self, root):
        self.root = root
        self.board = root / 'electronics/q4/click-counter-Q4.kicad_pcb'
        self.xml = root / 'electronics/q4/schematic-netlist-Q4.xml'
        self.report = root / 'verification/q4-validation.json'
        self.touched = {}

    def edit(self, path, content):
        path = self.root / path if not path.is_absolute() else path
        if path not in self.touched:
            self.touched[path] = path.read_bytes()
        path.write_bytes(content.encode() if isinstance(content, str) else content)

    def json(self, path, mutate):
        path = Path(path)
        absolute = self.root / path
        data = json.loads(absolute.read_text())
        mutate(data)
        self.edit(path, json.dumps(data, indent=2) + '\n')

    def pcb(self, mutate):
        tree = v.parse(self.board.read_text())
        mutate(tree)
        self.edit(self.board, write_tree(tree))

    def schematic_xml(self, mutate):
        tree = ET.parse(self.xml)
        mutate(tree.getroot())
        self.edit(self.xml, ET.tostring(tree.getroot(), encoding='utf-8', xml_declaration=True))

    def restore(self):
        for path, contents in self.touched.items():
            path.write_bytes(contents)
        self.touched.clear()

    def run(self, mode):
        if mode in ('semantic', 'bound'):
            command = [sys.executable, '-B', 'scripts/verify_q4.py']
            if mode == 'semantic':
                command.append('--semantic-only')
        else:
            # These target report content validation separately from byte-hash
            # rejection. The baseline was real and valid before mutation.
            kind = mode.removeprefix('report-')
            command = [sys.executable, '-B', '-c',
                "import sys;sys.path.insert(0,'scripts');import verify_q4 as v;"
                f"v.report_checks(v.{kind.upper()},'{kind}')"]
        return subprocess.run(command, cwd=self.root, text=True, capture_output=True, timeout=60)


def coherent_mutation(fixture, *, wrong_pin=False):
    """Change all semantically compared copies except the independent contract.

    This deliberately bypasses ordinary model/XML/PCB agreement, exercising the
    reviewed contract itself. It does not fabricate or rebind native reports.
    """
    source = Path('scripts/build_q4_model.py')
    text = (fixture.root / source).read_text()
    marker = '    return model'
    if text.count(marker) != 1:
        raise AssertionError('Cannot locate unique model-return mutation site')
    change = ("next(p for p in model['parts'] if p['ref']=='U1')['pins']['1']='GND'"
              if wrong_pin else
              "next(p for p in model['parts'] if p['ref']=='U3')['mpn']='TEST_INVALID_REGULATOR'")
    fixture.edit(source, text.replace(marker, '    ' + change + '\n' + marker))
    model_path = Path('electronics/q4/netlist-Q4.json')
    fixture.edit(model_path, (fixture.root / model_path).read_bytes())
    generated = subprocess.run([sys.executable, '-B', str(source)], cwd=fixture.root,
                               text=True, capture_output=True, timeout=30)
    if generated.returncode:
        raise AssertionError('Coherent fixture model failed: ' + generated.stderr)
    if wrong_pin:
        fixture.json('electronics/q4/schematic-paths-Q4.json',
                     lambda m: m['parts']['U1']['pins']['1'].update(net='GND'))
        def move_supply(root):
            parent = next(n for n in root.findall('nets/net') if n.find("node[@ref='U1'][@pin='1']") is not None)
            node = parent.find("node[@ref='U1'][@pin='1']")
            parent.remove(node)
            root.find("nets/net[@name='GND']").append(node)
        fixture.schematic_xml(move_supply)
        def net_change(board):
            target = pad(board, 'U1', '1')
            target.remove(v.child(target, 'net'))
            target.append(copy.deepcopy(v.child(pad(board, 'U1', '8'), 'net')))
        fixture.pcb(net_change)
    else:
        fixture.schematic_xml(lambda x: setattr(x.find("components/comp[@ref='U3']/fields/field[@name='MPN']"),
                                                'text', 'TEST_INVALID_REGULATOR'))
        fixture.pcb(lambda b: next(p for p in v.children(by_ref(b, 'U3'), 'property') if p[1] == 'MPN').__setitem__(2, 'TEST_INVALID_REGULATOR'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--semantic-only', action='store_true')
    parser.add_argument('--list', action='store_true', help='List cases without requiring completed native files')
    parser.add_argument('--output', type=Path, help='Optional test report destination; never a native validation report')
    args = parser.parse_args()
    if args.list:
        print(json.dumps({'semantic': SEMANTIC_CASES, 'native_bound': BOUND_CASES}, indent=2))
        return 0

    # Pre-existing routing/parity/contract errors cannot count as successful
    # corruption detection. Any baseline failure ends the suite immediately.
    baseline = v.verify_semantics() if args.semantic_only else v.saved()
    hashes = v.input_hashes()
    originals = set(hashes)
    if not args.semantic_only:
        originals.update(baseline['reports_sha256'])
        originals.add('verification/q4-validation.json')
    passed = []
    with tempfile.TemporaryDirectory(prefix='count-fidget-q4-negative-') as directory:
        folder = Path(directory)
        for name in sorted(originals):
            target = folder / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(v.ROOT / name, target)
        if v.input_hashes() != hashes:
            raise AssertionError('Live design changed while copying baseline; rerun after freeze')
        f = Fixture(folder)
        mode = 'semantic' if args.semantic_only else 'bound'
        initial = f.run(mode)
        if initial.returncode:
            raise AssertionError('Copied baseline failed; no negative result is valid:\n' + initial.stderr)

        def rejects(name, mutate, expected, mode='semantic'):
            try:
                mutate()
                result = f.run(mode)
                if result.returncode == 0:
                    raise AssertionError(name + ': corruption incorrectly accepted')
                detail = result.stdout + result.stderr
                if expected.lower() not in detail.lower():
                    raise AssertionError(name + ': failed for wrong reason, expected ' + repr(expected) + '\n' + detail)
                passed.append({'case': name, 'mode': mode, 'expected_rejection': expected})
            finally:
                f.restore()

        def board_case(name, mutate, expected):
            rejects(name, lambda: f.pcb(mutate), expected)

        board_case('PCB supply-pad net changed', lambda b: v.child(pad(b, 'U1', '1'), 'net').__setitem__(-1, 'GND'), 'PCB pad net differs: U1.1')
        board_case('PCB pad position changed', lambda b: bump(pad(b, 'U1', '1'), 'at'), 'Local/embedded pad')
        board_case('PCB physical drill changed', lambda b: bump(next(p for p in v.children(by_ref(b, 'SW1'), 'pad') if v.children(p, 'drill')), 'drill'), 'Local/embedded pad')
        board_case('PCB pad size changed', lambda b: bump(pad(b, 'U3', '1'), 'size'), 'Local/embedded pad')
        board_case('PCB pad layer changed', lambda b: flip_layer(pad(b, 'U1', '1'), 'layers'), 'Local/embedded pad')
        board_case('PCB component moved', lambda b: bump(by_ref(b, 'R30'), 'at'), 'R30 x')
        board_case('PCB component flipped', lambda b: flip_layer(by_ref(b, 'R30'), 'layer'), 'PCB side differs: R30')
        board_case('PCB MPN changed', lambda b: next(p for p in v.children(by_ref(b, 'U3'), 'property') if p[1] == 'MPN').__setitem__(2, 'INVALID'), 'PCB property differs: U3.MPN')
        board_case('PCB duplicate UUID', lambda b: v.child(by_ref(b, 'R30'), 'uuid').__setitem__(1, v.child(by_ref(b, 'R31'), 'uuid')[1]), 'Duplicate PCB UUID')
        board_case('PCB route removed', lambda b: b.__setitem__(slice(None), [n for n in b if not isinstance(n, list) or n[0] != 'segment']), 'No routes')
        board_case('PCB ground fill removed', lambda b: b.__setitem__(slice(None), [n for n in b if not isinstance(n, list) or n[0] != 'zone']), 'ground fills')
        board_case('PCB outline vertex changed', lambda b: bump(next(g for g in v.children(b, 'gr_line') if v.child(g, 'layer')[1] == 'Edge.Cuts'), 'start'), 'outline')
        board_case('PCB extra outline primitive', lambda b: b.append(['gr_circle', ['center', '5', '5'], ['end', '6', '5'], ['stroke', ['width', '.05'], ['type', 'default']], ['fill', 'none'], ['layer', 'Edge.Cuts'], ['uuid', 'q4-negative-test-extra-outline']]), 'outline')
        board_case('PCB thickness changed', lambda b: bump(v.child(b, 'general'), 'thickness'), 'Board thickness')
        board_case('PCB inner layer added', lambda b: v.child(b, 'layers').append(['2', 'In1.Cu', 'power']), 'two copper layers')
        rejects('Schematic MPN changed', lambda: f.schematic_xml(lambda x: setattr(x.find("components/comp[@ref='U3']/fields/field[@name='MPN']"), 'text', 'INVALID')), 'Schematic identity differs: U3.mpn')
        rejects('Schematic MPN duplicated', lambda: f.schematic_xml(lambda x: x.find("components/comp[@ref='U3']/fields").append(copy.deepcopy(x.find("components/comp[@ref='U3']/fields/field[@name='MPN']")))), 'duplicated schematic identity')
        def remove_supply(x):
            parent = next(n for n in x.findall('nets/net') if n.find("node[@ref='U1'][@pin='1']") is not None)
            parent.remove(parent.find("node[@ref='U1'][@pin='1']"))
        rejects('Schematic MCU supply connection omitted', lambda: f.schematic_xml(remove_supply), 'Physical pin absent in native export')
        rejects('Schematic MCU pin duplicated', lambda: f.schematic_xml(lambda x: x.find("nets/net[@name='GND']").append(copy.deepcopy(x.find("nets/net/node[@ref='U1'][@pin='1']")))), 'Physical schematic pin assigned twice')
        rejects('Coherent MCU supply miswired despite independent contract', lambda: coherent_mutation(f, wrong_pin=True), 'Critical circuit contract differs: U1.pins')
        rejects('Coherent regulator MPN changed despite independent contract', lambda: coherent_mutation(f), 'Critical circuit contract differs: U3.mpn')

        if not args.semantic_only:
            def append(name):
                path = Path(name)
                f.edit(path, (folder / path).read_bytes() + b'\n')
            for label, name, expected in [
                ('Bound source modified', 'scripts/build_q4_board.py', 'Stale native evidence'),
                ('Bound local footprint modified', next(n for n in hashes if n.endswith('.kicad_mod')), 'Stale native evidence'),
                ('Bound circuit contract modified', 'electronics/q4/circuit-contract.json', 'Stale native evidence'),
                ('Bound ERC bytes modified', 'verification/q4-native-erc.json', 'Native reports changed'),
                ('Bound DRC bytes modified', 'verification/q4-native-drc.json', 'Native reports changed'),
                ('Bound native XML bytes modified', 'verification/q4-native-netlist.xml', 'Native reports changed')]:
                rejects(label, lambda n=name: append(n), expected, 'bound')
            def bound(name, mutate, expected):
                rejects(name, lambda: f.json('verification/q4-validation.json', mutate), expected, 'bound')
            bound('Bound input digest changed', lambda r: r['inputs_sha256'].__setitem__('scripts/build_q4_model.py', '0'*64), 'Stale native evidence')
            bound('Bound report digest changed', lambda r: r['reports_sha256'].__setitem__('verification/q4-native-drc.json', '0'*64), 'Native reports changed')
            bound('Bound status changed', lambda r: r.update(status='FAIL'), 'status')
            bound('Bound manufacture flag changed', lambda r: r.update(manufacturing_released=True), 'status')
            bound('Bound native command drops parity', lambda r: r['commands'][2].remove('--schematic-parity'), 'Recorded native invocation differs')
            bound('Bound semantic summary changed', lambda r: r['semantic_checks'].update(connected_physical_pins=-1), 'Saved semantic summary differs')
            bound('Bound native summary changed', lambda r: r['native_checks']['drc'].update(kicad_version='TEST'), 'Saved native summary differs')
            def native(name, kind, mutate, expected):
                rejects(name, lambda: f.json('verification/q4-native-'+kind+'.json', mutate), expected, 'report-'+kind)
            native('DRC wrong source field', 'drc', lambda r: r.update(source='other.kicad_pcb'), 'Wrong native board source')
            native('ERC wrong source field', 'erc', lambda r: r.update(source='other.kicad_sch'), 'Wrong native schematic source')
            native('DRC missing warning severity', 'drc', lambda r: r.update(included_severities=['error','exclusion']), 'All native severities required')
            native('DRC ignored clearance', 'drc', lambda r: r.setdefault('ignored_checks',[]).append({'key':'clearance'}), 'Additional native checks suppressed')
            native('DRC nonzero unconnected', 'drc', lambda r: r['unconnected_items'].append({'test':'not a genuine diagnostic'}), 'Native DRC unconnected_items is not zero')
            native('DRC nonzero parity', 'drc', lambda r: r['schematic_parity'].append({'test':'not a genuine diagnostic'}), 'Native DRC schematic_parity is not zero')
            native('DRC nonzero physical violation', 'drc', lambda r: r['violations'].append({'test':'not a genuine diagnostic'}), 'Native DRC violations is not zero')
            native('ERC nonzero violation', 'erc', lambda r: r['sheets'][0]['violations'].append({'test':'not a genuine diagnostic'}), 'ERC violations remain')
        final = f.run(mode)
        if final.returncode:
            raise AssertionError('Restored baseline failed:\n' + final.stderr)
    if v.input_hashes() != hashes:
        raise AssertionError('Live design changed during negative checks; rerun after freeze')
    expected = len(SEMANTIC_CASES) + (0 if args.semantic_only else len(BOUND_CASES))
    if len(passed) != expected:
        raise AssertionError(f'Case inventory differs: {len(passed)} != {expected}')
    report = {
        'status': 'PASS_NEGATIVE_VERIFIER_CHECKS_ONLY',
        'native_baseline_required_and_verified': not args.semantic_only,
        'fresh_native_checks_run_by_this_test': False,
        'negative_corruptions_rejected': len(passed),
        'test_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'baseline_inputs_sha256': hashes,
        'baseline_report_sha256': hashlib.sha256(v.REPORT.read_bytes()).hexdigest() if not args.semantic_only else None,
        'checks': passed,
        'limitations': ['Only the named mutations are covered; this is not exhaustive verification.',
                        'No electrical or physical qualification, source-authenticity signature or manufacturing release.',
                        'Coherent model/XML/PCB changes test the separate reviewed contract, not fresh KiCad regeneration.'],
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (AssertionError, ValueError, OSError, KeyError, subprocess.TimeoutExpired) as error:
        print('FAIL: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
