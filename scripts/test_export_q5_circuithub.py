"""Corruption tests for scripts/export_q5_circuithub.py: every case must be rejected.

Copies the Q5 KiCad files, the canonical BOM, the CircuitHub cross-reference and the
generator into a temporary tree, corrupts one input at a time and checks that the
generator refuses to write a package. Run: python3 scripts/test_export_q5_circuithub.py
"""
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='q5-circuithub-test-') as folder:
        tree = Path(folder)
        for path in [*ROOT.glob('electronics/q5/*.kicad_*'), ROOT / 'procurement/q5/BOM-Q5.csv',
                     ROOT / 'procurement/q5/circuithub/crossref-q5.json', ROOT / 'scripts/export_q5_circuithub.py']:
            target = tree / path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
        cross, pcb, bom = (tree / 'procurement/q5/circuithub/crossref-q5.json', tree / 'electronics/q5/click-counter-Q5.kicad_pcb',
                           tree / 'procurement/q5/BOM-Q5.csv')
        originals = {p: p.read_text(encoding='utf-8') for p in (cross, pcb, bom)}

        def run():
            return subprocess.run([sys.executable, '-B', str(tree / 'scripts/export_q5_circuithub.py')],
                                  capture_output=True, text=True, cwd=tree)

        assert run().returncode == 0, 'baseline package must build'

        def crossref(edit):
            data = json.loads(originals[cross])
            edit(data['lines'])
            return {cross: json.dumps(data)}

        bom_lines = originals[bom].splitlines(True)
        cases = {
            'fitted part without a CircuitHub decision': crossref(lambda l: l.pop('AO3400A')),
            'cross-reference package differs from the footprint': crossref(lambda l: l['AO3400A'].update(package='0805')),
            'stale cross-reference entry': crossref(lambda l: l.update({'STALE-PART': dict(l['AO3400A'])})),
            'copper zones not filled': {pcb: originals[pcb].replace('(filled_polygon', '(unfilled_polygon')},
            'private local path in an uploaded file': {pcb: originals[pcb].replace('(generator "pcbnew")', '(generator "pcbnew") (comment "/Users/x")', 1)},
            'fitted reference listed twice': {bom: originals[bom] + next(l for l in bom_lines if l.startswith('2.2u,C1,'))},
            'fitted reference missing from the BOM': {bom: ''.join(l for l in bom_lines if not l.startswith('1n,C11,'))},
        }
        failures = 0
        for name, edits in cases.items():
            for path, text in originals.items():
                path.write_text(edits.get(path, text), encoding='utf-8')
            result = run()
            rejected = result.returncode != 0 and 'FAIL:' in result.stderr
            failures += not rejected
            print(('rejected  ' if rejected else 'ACCEPTED  ') + name)
        print(f'{len(cases) - failures}/{len(cases)} corruptions rejected')
        return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
