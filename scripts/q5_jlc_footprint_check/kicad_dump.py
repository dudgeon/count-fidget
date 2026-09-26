import pcbnew, json, sys
b = pcbnew.LoadBoard('/home/user/count-fidget/electronics/q5/click-counter-Q5.kicad_pcb')
out = {}
for fp in b.GetFootprints():
    ref = fp.GetReference()
    pos = fp.GetPosition(); rot = fp.GetOrientationDegrees()
    side = 'bottom' if fp.IsFlipped() else 'top'
    pads=[]
    for p in fp.Pads():
        pp = p.GetPosition(); sz = p.GetSize(pcbnew.F_Cu) if hasattr(p,'GetSize') else None
        try: sz = p.GetSize(pcbnew.F_Cu)
        except TypeError: sz = p.GetSize()
        # local (unrotated, unflipped) position via FP_SHAPE local
        try:
            lp = p.GetFPRelativePosition()
        except Exception: lp=None
        pads.append(dict(num=p.GetNumber(), x=pcbnew.ToMM(pp.x), y=pcbnew.ToMM(pp.y),
            lx=pcbnew.ToMM(lp.x) if lp else None, ly=pcbnew.ToMM(lp.y) if lp else None,
            w=pcbnew.ToMM(sz.x), h=pcbnew.ToMM(sz.y), attr=int(p.GetAttribute()),
            drill=pcbnew.ToMM(p.GetDrillSize().x), drilly=pcbnew.ToMM(p.GetDrillSize().y),
            shape=int(p.GetShape(pcbnew.F_Cu)) if True else 0,
            padrot=p.GetOrientationDegrees(), copper=bool(p.IsOnCopperLayer()), npth=p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH))
    out[ref]=dict(fpid=str(fp.GetFPID().GetLibItemName()), x=pcbnew.ToMM(pos.x), y=pcbnew.ToMM(pos.y), rot=rot, side=side,
       value=fp.GetValue(), attrs=fp.GetAttributes(), pads=pads)

lib={}
import os
LP='/home/user/count-fidget/electronics/q5/CountFidgetQ5.pretty'
for fn in os.listdir(LP):
    n=fn[:-10]
    fp=pcbnew.FootprintLoad(LP,n)
    lib[n]=[dict(num=p.GetNumber(),x=pcbnew.ToMM(p.GetPosition().x),y=pcbnew.ToMM(p.GetPosition().y),copper=bool(p.IsOnCopperLayer()),npth=p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH,w=pcbnew.ToMM(p.GetSize(pcbnew.F_Cu).x),h=pcbnew.ToMM(p.GetSize(pcbnew.F_Cu).y),drill=pcbnew.ToMM(p.GetDrillSize().x),rot=p.GetOrientationDegrees()) for p in fp.Pads()]
json.dump(lib,open(sys.argv[1].replace('.json','_lib.json'),'w'),indent=1)
json.dump(out, open(sys.argv[1],'w'), indent=1)
print(len(out))
