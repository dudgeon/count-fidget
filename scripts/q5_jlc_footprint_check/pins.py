import json
nl={p['ref']:p for p in json.load(open('/home/user/count-fidget/electronics/q5/netlist-Q5.json'))['parts']}
def sympins(c):
    d=json.load(open(f'easyeda/{c}.json'))['result']['dataStr']
    out={}
    for s in d['shape']:
        if s.startswith('P~'):
            seg=s.split('^^'); a=seg[0].split('~'); num=a[3]
            name=seg[3].split('~')[4] if len(seg)>3 else '?'
            out[num]=name
    return out
for ref in ['BT1','D1','D3','D4','Q1','Q3','U1','U2','U3','U4','U5','U6','U8','J1','SW1','SW3','DS1']:
    p=nl[ref]; c=p['lcsc']
    sp=p.get('symbol_pins',{})
    ours={k:(v.get('name') if isinstance(v,dict) else v) for k,v in sp.items()}
    e=sympins(c)
    keys=sorted(set(ours)|set(e),key=lambda k:(len(k),k))
    diff=[(k,ours.get(k),e.get(k)) for k in keys]
    print(ref,c); print('   ',' | '.join(f"{k}:{o}/{x}" for k,o,x in diff)[:900])
