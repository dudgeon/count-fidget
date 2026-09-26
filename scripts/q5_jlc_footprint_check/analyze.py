"""Compare KiCad Q5 footprints with the EasyEDA/LCSC footprints JLC uses, and predict
the JLC placement preview for the Q5 CPL. Read-only on the repo."""
import csv, json, math, os, sys
from itertools import product

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = '/home/user/count-fidget'
MIL10 = 0.254

kb = json.load(open(f'{HERE}/kicad.json'))
klib = json.load(open(f'{HERE}/kicad_lib.json'))

def read_csv(p):
    with open(p, newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

bom = read_csv(f'{REPO}/procurement/q5/BOM-JLCPCB-Q5-FULL-ASSEMBLY.csv')
cpl = {r['Designator']: r for r in read_csv(f'{REPO}/procurement/q5/CPL-JLCPCB-Q5-FULL-ASSEMBLY.csv')}
ref_lcsc = {}
ref_fp = {}
for r in bom:
    for d in r['Designator'].split(','):
        ref_lcsc[d.strip()] = r['LCSC Part #']
        ref_fp[d.strip()] = r['Footprint'].split(':')[-1]
netlist = {p['ref']: p for p in json.load(open(f'{REPO}/electronics/q5/netlist-Q5.json'))['parts']}

# ---------- EasyEDA parsing ----------
def easy(lcsc):
    d = json.load(open(f'{HERE}/easyeda/{lcsc}.json'))['result']
    pk = d['packageDetail']['dataStr']
    hx, hy = float(pk['head']['x']), float(pk['head']['y'])
    pads = []
    texts = []
    for s in pk['shape']:
        f = s.split('~')
        if f[0] == 'PAD':
            x, y, w, h = map(float, f[2:6])
            layer = f[6]; num = f[8]; holer = float(f[9] or 0)
            rot = float(f[11] or 0)
            pads.append(dict(num=num, x=(x - hx) * MIL10, y=-(y - hy) * MIL10, w=w * MIL10, h=h * MIL10,
                             layer=layer, hole=2 * holer * MIL10, rot=rot, kind='pad'))
        elif f[0] == 'HOLE':
            x, y, r = map(float, f[1:4])
            pads.append(dict(num='', x=(x - hx) * MIL10, y=-(y - hy) * MIL10, w=2 * r * MIL10, h=2 * r * MIL10,
                             layer='hole', hole=2 * r * MIL10, rot=0, kind='hole'))
        elif f[0] == 'TEXT':
            texts.append(f[1:12])
    c = d['dataStr']['head']['c_para']
    return dict(pads=pads, package=pk['head']['c_para'].get('package'), mfr=c.get('Manufacturer'),
                mpn=c.get('Manufacturer Part'), cls=c.get('JLCPCB Part Class'), texts=texts,
                origin=(hx, hy))

def kpads_local(fpname):
    out = []
    for p in klib[fpname]:
        if not p['copper'] and not p['npth']:
            continue  # paste-only apertures
        out.append(dict(num=p['num'], x=p['x'], y=-p['y'], w=p['w'], h=p['h'], npth=p['npth'], drill=p['drill']))
    return out

def kpads_board(ref):
    out = []
    for p in kb['DS1' if ref == 'DS1H' else ref]['pads']:
        if not p['copper'] and not p['npth']:
            continue
        out.append(dict(num=p['num'], x=p['x'], y=-p['y'], npth=p['npth'], drill=p['drill']))
    return out

# ---------- geometry ----------
def rot(pt, deg):
    a = math.radians(deg); c, s = round(math.cos(a), 12), round(math.sin(a), 12)
    return (pt[0] * c - pt[1] * s, pt[0] * s + pt[1] * c)

def T(pt, deg, mirror):
    x, y = pt
    if mirror:
        x = -x
    return rot((x, y), deg)

def names(n):
    return set(n.split('-')) if n else set()

def match_by_number(E, K, tf, off):
    """pairs (e,k) where k.num is in e's name set; for duplicates pick nearest."""
    pairs = []
    for k in K:
        if not k['num']:
            continue
        cands = [e for e in E if e['kind'] == 'pad' and k['num'] in names(e['num'])]
        if not cands:
            pairs.append((None, k)); continue
        best = min(cands, key=lambda e: dist(add(tf(e), off), (k['x'], k['y'])))
        pairs.append((best, k))
    return pairs

def add(a, b): return (a[0] + b[0], a[1] + b[1])
def sub(a, b): return (a[0] - b[0], a[1] - b[1])
def dist(a, b): return math.hypot(a[0] - b[0], a[1] - b[1])

def fit(E, K, tf, fixed_offset=None):
    """Return (offset, max residual numbered, max residual geometric (all copper+holes), details)."""
    Epts = [(e, tf(e)) for e in E]
    # initial offset: mean over number matches with unique names
    if fixed_offset is None:
        off = (0.0, 0.0)
        for _ in range(4):
            pairs = [(e, k) for e, k in match_by_number(E, K, tf, off) if e is not None]
            if not pairs:
                ce = centroid([p for _, p in Epts]); ck = centroid([(k['x'], k['y']) for k in K])
                off = sub(ck, ce); break
            diffs = [sub((k['x'], k['y']), tf(e)) for e, k in pairs]
            off = (sum(d[0] for d in diffs) / len(diffs), sum(d[1] for d in diffs) / len(diffs))
    else:
        off = fixed_offset
    pairs = match_by_number(E, K, tf, off)
    num_res = [dist(add(tf(e), off), (k['x'], k['y'])) for e, k in pairs if e is not None]
    missing = [k['num'] for e, k in pairs if e is None]
    # geometric: every KiCad copper pad / hole to nearest EasyEDA pad/hole of same kind (any number)
    geo = []
    for k in K:
        kind_holes = k.get('npth')
        cands = [p for e, p in Epts if (e['kind'] == 'hole') == bool(kind_holes)] or [p for _, p in Epts]
        geo.append((k, min(dist(add(p, off), (k['x'], k['y'])) for p in cands)))
    # reverse: every EasyEDA pad has a KiCad pad nearby
    rev = []
    for e, p in Epts:
        rev.append((e, min(dist(add(p, off), (k['x'], k['y'])) for k in K)))
    return dict(off=off, num_max=max(num_res) if num_res else None, n_num=len(num_res), missing=missing,
                geo_max=max(g for _, g in geo), rev_max=max(r for _, r in rev),
                geo_detail=geo, rev_detail=rev, pairs=pairs)

def centroid(pts):
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))

def local_align(E, K):
    res = []
    for deg, m in product((0, 90, 180, 270), (False, True)):
        tf = lambda e, deg=deg, m=m: T((e['x'], e['y']), deg, m)
        r = fit(E, K, tf)
        r.update(deg=deg, mirror=m)
        res.append(r)
    key = lambda r: (r['num_max'] if r['num_max'] is not None else 1e9, r['geo_max'])
    by_num = min(res, key=key)
    by_geo = min(res, key=lambda r: (max(r['geo_max'], r['rev_max']), r['mirror']))
    return by_num, by_geo, res

# ---------- JLC preview model ----------
# bottom: P = C + My . R(beta) . E    (Bouni kicad-jlcpcb-tools / KiKit 'MirrorBottom': beta = 180 - theta)
# top:    P = C + R(beta) . E
def jlc_place(e, C, beta, bottom, model='current'):
    x, y = e['x'], e['y']
    if not bottom:
        p = rot((x, y), beta)
    elif model == 'current':
        p = rot((x, y), beta); p = (-p[0], p[1])
    else:  # 'kicadlike': mirror local y then rotate (KiCad board convention)
        p = rot((x, -y), beta)
    return add(C, p)

def board_eval(ref, E, model='current'):
    r = cpl[ref]
    C = (float(r['Mid X'].rstrip('mm')), float(r['Mid Y'].rstrip('mm')))
    bottom = r['Layer'].lower().startswith('b')
    K = kpads_board(ref)
    out = {}
    for beta in (0, 90, 180, 270):
        tf = lambda e, beta=beta: jlc_place(e, C, beta, bottom, model)
        f0 = fit(E, K, tf, fixed_offset=(0.0, 0.0))  # as JLC would show, no offset
        fb = fit(E, K, tf)  # with best offset
        out[beta] = (f0, fb)
    return C, float(r['Rotation']), bottom, K, out

def fmt(v):
    return '-' if v is None else f'{v:.3f}'

def main():
    rows = []
    refs = sorted(cpl, key=lambda s: (''.join(c for c in s if c.isalpha()), int(''.join(c for c in s if c.isdigit()) or 0)))
    cache = {}
    report = {}
    for ref in refs:
        lcsc = ref_lcsc[ref]
        if lcsc not in cache:
            cache[lcsc] = easy(lcsc)
        ez = cache[lcsc]
        fpname = ref_fp[ref] if ref != 'DS1H' else None
        E = ez['pads']
        entry = dict(ref=ref, lcsc=lcsc, package=ez['package'], mpn=ez['mpn'], fp=fpname)
        if fpname:
            K = kpads_local(fpname)
            bn, bg, allr = local_align(E, K)
            entry['local'] = dict(deg=bn['deg'], mirror=bn['mirror'], off=bn['off'], num_max=bn['num_max'],
                                  geo_max=bn['geo_max'], rev_max=bn['rev_max'], missing=bn['missing'],
                                  n_E=len(E), n_K=len(K),
                                  geo_deg=bg['deg'], geo_mirror=bg['mirror'], geo_off=bg['off'],
                                  geo_geo_max=max(bg['geo_max'], bg['rev_max']), geo_num_max=bg['num_max'])
            # centroid of KiCad copper pads (local) vs origin
            cu = [(k['x'], k['y']) for k in K if not k['npth']]
            entry['k_centroid'] = centroid(cu)
            xs = [p[0] for p in cu]; ys = [p[1] for p in cu]
            entry['k_bbox_c'] = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
            # KiCad board placement vs library (sanity: board pads equal library pads transformed)
        C, theta, bottom, Kb, ev = board_eval(ref, E, 'current')
        entry['cpl'] = dict(C=C, rot=theta, bottom=bottom)
        th = int(round(theta)) % 360
        entry['as_is'] = ev[th][0]['num_max'], ev[th][0]['geo_max'], ev[th][0]['rev_max']
        # best beta by numbered then geometric
        best = min(ev, key=lambda b: (ev[b][1]['num_max'] if ev[b][1]['num_max'] is not None else 1e9))
        bestg = min(ev, key=lambda b: max(ev[b][1]['geo_max'], ev[b][1]['rev_max']))
        entry['best_num'] = dict(beta=best, off=ev[best][1]['off'], num_max=ev[best][1]['num_max'],
                                 geo=max(ev[best][1]['geo_max'], ev[best][1]['rev_max']),
                                 zero_off_num=ev[best][0]['num_max'])
        entry['best_geo'] = dict(beta=bestg, off=ev[bestg][1]['off'], geo=max(ev[bestg][1]['geo_max'], ev[bestg][1]['rev_max']),
                                 num_max=ev[bestg][1]['num_max'])
        # alternative (legacy KiCad-like) model
        _, _, _, _, ev2 = board_eval(ref, E, 'kicadlike')
        best2 = min(ev2, key=lambda b: (ev2[b][1]['num_max'] if ev2[b][1]['num_max'] is not None else 1e9))
        entry['legacy_best'] = dict(beta=best2, num_max=ev2[best2][1]['num_max'], off=ev2[best2][1]['off'])
        entry['legacy_as_is'] = ev2[th][0]['num_max']
        entry['all_beta'] = {b: dict(num0=ev[b][0]['num_max'], numb=ev[b][1]['num_max'],
                                     geob=max(ev[b][1]['geo_max'], ev[b][1]['rev_max']), off=ev[b][1]['off'])
                             for b in ev}
        report[ref] = entry
    json.dump(report, open(f'{HERE}/results.json', 'w'), indent=1, default=str)
    # table
    fh = open(f'{HERE}/results.csv', 'w', newline=''); w = csv.writer(fh)
    w.writerow(['ref', 'lcsc', 'easyeda_package', 'kicad_fp', 'layer', 'cpl_rot',
                'local_rot', 'local_mirror', 'local_off_x', 'local_off_y', 'local_num_resid', 'local_geo_resid', 'missing_nums',
                'jlc_as_is_num_resid', 'jlc_best_rot', 'jlc_best_num_resid', 'jlc_best_off_x', 'jlc_best_off_y',
                'jlc_geo_best_rot', 'jlc_geo_best_resid', 'legacy_model_best_rot', 'kicad_origin_minus_pad_centroid_x', '_y'])
    for ref, e in report.items():
        L = e.get('local', {})
        kc = e.get('k_centroid', (0, 0))
        w.writerow([ref, e['lcsc'], e['package'], e['fp'], 'B' if e['cpl']['bottom'] else 'T', e['cpl']['rot'],
                    L.get('deg'), L.get('mirror'), fmt(L.get('off', (None,))[0]) if L else '', fmt(L['off'][1]) if L else '',
                    fmt(L.get('num_max')), fmt(L.get('geo_max')), ' '.join(L.get('missing', [])),
                    fmt(e['as_is'][0]), e['best_num']['beta'], fmt(e['best_num']['num_max']),
                    fmt(e['best_num']['off'][0]), fmt(e['best_num']['off'][1]),
                    e['best_geo']['beta'], fmt(e['best_geo']['geo']), e['legacy_best']['beta'],
                    fmt(-kc[0]), fmt(-kc[1])])
    fh.close()

if __name__ == '__main__':
    main()
