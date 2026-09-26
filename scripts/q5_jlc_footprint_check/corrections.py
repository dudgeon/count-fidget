"""Predict JLC preview corrections. Model (community-documented, see report): bottom P = C + My*R(beta)*E ; top P = C + R(beta)*E."""
import json, math, csv
exec(open('analyze.py').read().split("if __name__")[0].replace("HERE = os.path.dirname(os.path.abspath(__file__))", "HERE = '.'"))
res = json.load(open('results.json'))
NONPOLAR = lambda r: r[0] in 'RC' or r == 'TH1' or r == 'SW3'

def geo_fit(E, K, tf):
    # match every E item to nearest K item of same kind (pad<->copper pad, hole<->NPTH), ignoring numbers
    off = sub(centroid([(k['x'], k['y']) for k in K if not k['npth']]), centroid([tf(e) for e in E if e['kind'] == 'pad']))
    for _ in range(6):
        d = []
        for e in E:
            p = tf(e); ks = [k for k in K if bool(k['npth']) == (e['kind'] == 'hole')]
            k = min(ks, key=lambda k: dist(add(p, off), (k['x'], k['y'])))
            d.append(sub((k['x'], k['y']), p))
        off = (sum(a for a, _ in d) / len(d), sum(b for _, b in d) / len(d))
    r = max(dist(add(tf(e), off), min(((k['x'], k['y']) for k in K if bool(k['npth']) == (e['kind'] == 'hole')), key=lambda q: dist(add(tf(e), off), q))) for e in E)
    return off, r

rows = []
for ref, e in res.items():
    r = cpl[ref]; C = (float(r['Mid X'][:-2]), float(r['Mid Y'][:-2])); theta = float(r['Rotation']); bottom = r['Layer'] == 'Bottom'
    E = easy(e['lcsc'])['pads']; K = kpads_board(ref)
    th = int(round(theta)) % 360
    cands = {}
    for b in (0, 90, 180, 270):
        tf = lambda q, b=b: jlc_place(q, C, b, bottom)
        if ref in ('SW1', 'SW2'):
            off, rr = geo_fit(E, K, tf)
        else:
            f = fit(E, K, tf); off, rr = f['off'], f['num_max']
        cands[b] = (rr, off)
    best = min(cands, key=lambda b: cands[b][0])
    rr, off = cands[best]
    ok = {b for b in cands if cands[b][0] < rr + 0.02}
    need_rot = th not in ok
    need_off = math.hypot(*off) > 0.2
    newC = add(C, off) if need_off else C
    # legacy model
    E2best = e['legacy_best']['beta']
    rows.append(dict(ref=ref, lcsc=e['lcsc'], layer=r['Layer'], cpl_rot=theta, predicted_ok_rot=sorted(ok), correct_rot=best if need_rot else th,
                     rot_change=need_rot, resid=round(rr, 3), offset=(round(off[0], 3), round(off[1], 3)), offset_change=need_off,
                     new_mid=(round(newC[0], 3), round(newC[1], 3)), legacy_model_rot=E2best, cpl_mid=C))
json.dump(rows, open('corrections.json', 'w'), indent=1)
with open('corrections.csv', 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['Designator', 'LCSC', 'Layer', 'CPL rot', 'Rotations that align JLC footprint (predicted)', 'Change rotation?', 'Suggested rot', 'Residual mm', 'JLC offset needed dx,dy mm', 'Change position?', 'Suggested Mid X', 'Suggested Mid Y', 'Legacy-model rot'])
    for x in rows:
        w.writerow([x['ref'], x['lcsc'], x['layer'], x['cpl_rot'], ' '.join(map(str, x['predicted_ok_rot'])), 'YES' if x['rot_change'] else '', x['correct_rot'], x['resid'], f"{x['offset'][0]},{x['offset'][1]}", 'YES' if x['offset_change'] else '', x['new_mid'][0], x['new_mid'][1], x['legacy_model_rot']])
for x in rows:
    if x['rot_change'] or x['offset_change'] or x['resid'] > 0.1:
        print(x['ref'], x['cpl_rot'], '->', x['correct_rot'], 'ok', x['predicted_ok_rot'], 'res', x['resid'], 'off', x['offset'], 'new', x['new_mid'] if x['offset_change'] else '', 'legacy', x['legacy_model_rot'])
