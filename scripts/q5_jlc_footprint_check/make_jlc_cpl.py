"""Write JLC-corrected CPL files from corrections.json (run corrections.py first).

Rotation and centroid corrections are the ones predicted by fitting JLC's own EasyEDA/LCSC
footprints onto our pads (see REPORT.md). The bottom-side convention (rotation = 180 - KiCad
rotation, X mirrored) is community-documented (KiKit, Bouni kicad-jlcpcb-tools, KiBot), not
JLC-documented: always confirm BT1 +, D4 cathode and U3 pin 1 in JLC's preview.
"""
import csv, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
Q5 = os.path.join(HERE, '../../procurement/q5')
corr = {c['ref']: c for c in json.load(open(os.path.join(HERE, 'corrections.json')))}
for src, dst in (('CPL-JLCPCB-Q5.csv', 'CPL-JLCPCB-Q5-JLC-CORRECTED.csv'),
                 ('CPL-JLCPCB-Q5-FULL-ASSEMBLY.csv', 'CPL-JLCPCB-Q5-FULL-ASSEMBLY-JLC-CORRECTED.csv')):
    rows = list(csv.DictReader(open(os.path.join(Q5, src), newline='', encoding='utf-8-sig')))
    changed = []
    for r in rows:
        c = corr[r['Designator']]
        assert abs(float(r['Mid X'][:-2]) - c['cpl_mid'][0]) < 1e-6 and abs(float(r['Mid Y'][:-2]) - c['cpl_mid'][1]) < 1e-6, \
            f"{r['Designator']}: corrections.json is stale; re-run analyze.py and corrections.py"
        new = dict(r)
        if c['offset_change']:
            new['Mid X'], new['Mid Y'] = f"{c['new_mid'][0]:.6f}mm", f"{c['new_mid'][1]:.6f}mm"
        new['Rotation'] = f"{float(c['correct_rot']):.6f}"
        if new != r:
            changed.append(r['Designator'])
        r.update(new)
    with open(os.path.join(Q5, dst), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    print(dst, len(rows), 'rows;', len(changed), 'corrected:', ' '.join(changed))
