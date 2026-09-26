import json, sys
sys.argv=['x']
exec(open('analyze.py').read().split("if __name__")[0])
res=json.load(open('results.json'))
def rect(x,y,w,h,r):
    if int(round(r))%180==90: w,h=h,w
    return (x-w/2,y-h/2,x+w/2,y+h/2)
def iou(a,b):
    ix=max(0,min(a[2],b[2])-max(a[0],b[0])); iy=max(0,min(a[3],b[3])-max(a[1],b[1]))
    inter=ix*iy; A=(a[2]-a[0])*(a[3]-a[1]); B=(b[2]-b[0])*(b[3]-b[1])
    return inter/(A+B-inter), inter/A
seen=set()
for ref in sys.stdin.read().split():
    e=res[ref]; lc=e['lcsc']
    ez=easy(lc); L=e['local']; deg=L['deg']; m=L['mirror']; off=L['off']
    print(f"== {ref} {lc} {ez['package']} vs {e['fp']}  align rot {deg} mirror {m} off {off[0]:.3f},{off[1]:.3f}")
    K={}
    for p in klib[e['fp']]:
        if p['copper'] or p['npth']: K.setdefault(p['num'],[]).append(p)
    for q in ez['pads']:
        x,y=T((q['x'],q['y']),deg,m); x+=off[0]; y+=off[1]
        r=q['rot']+deg
        er=rect(x,y,q['w'],q['h'],r)
        cands=[k for n in (names(q['num']) or {''}) for k in K.get(n,[])]
        if not cands: print(f"   E {q['num']:>7} ({x:7.3f},{y:7.3f}) {q['w']:.2f}x{q['h']:.2f} kind={q['kind']} hole={q['hole']:.2f}  NO KiCad pad with this number"); continue
        k=min(cands,key=lambda k:(k['x']-x)**2+(-k['y']-y)**2)
        kr=rect(k['x'],-k['y'],k['w'],k['h'],k['rot'])
        io,cov=iou(er,kr)
        print(f"   E {q['num']:>7} ({x:7.3f},{y:7.3f}) {q['w']:.2f}x{q['h']:.2f}{' hole %.2f'%q['hole'] if q['hole'] else ''} -> K {k['num']:>4} ({k['x']:7.3f},{-k['y']:7.3f}) {k['w']:.2f}x{k['h']:.2f}{' drill %.2f'%k['drill'] if k['drill'] else ''} d={((k['x']-x)**2+(-k['y']-y)**2)**.5:.3f} IoU={io:.2f} Ecov={cov:.2f}  E[{er[0]:.2f},{er[1]:.2f},{er[2]:.2f},{er[3]:.2f}] K[{kr[0]:.2f},{kr[1]:.2f},{kr[2]:.2f},{kr[3]:.2f}]")
