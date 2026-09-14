"""Import the matching SES, normalize 5 mil necks, add ground copper and export.
Run once after build_pcb.py and offline Freerouting. No production release.
"""
from pathlib import Path
import pcbnew as p
import json
ROOT=Path(__file__).resolve().parent
path=ROOT/'click-counter-Q1.kicad_pcb'
b=p.LoadBoard(str(path))
if not len(b.GetTracks()):
    assert p.ImportSpecctraSES(b,str(ROOT/'click-counter-Q1.ses'))
for tr in b.GetTracks():
    if isinstance(tr,p.PCB_TRACK) and not isinstance(tr,p.PCB_VIA) and tr.GetWidth()<p.FromMM(.127):tr.SetWidth(p.FromMM(.127))
for f in b.GetFootprints():
    if f.GetReference().startswith(('TP','H')):f.SetAttributes(f.GetAttributes()|p.FP_EXCLUDE_FROM_BOM|p.FP_EXCLUDE_FROM_POS_FILES)
    if f.GetReference()=='DS1':
        f.SetFPID(p.LIB_ID('ClickCounter','DE188_20P_34.9x13mm'))
        lib=ROOT/'ClickCounter.pretty';lib.mkdir(exist_ok=True)
        cp=p.FOOTPRINT(f);cp.SetPosition(p.VECTOR2I(0,0))
        p.PCB_IO_MGR.FindPlugin(p.PCB_IO_MGR.KICAD_SEXP).FootprintSave(str(lib),cp)
if not len(b.Zones()):
    for layer in [p.In1_Cu,p.In2_Cu]:
        z=p.ZONE(b);z.SetLayer(layer);z.SetNet(b.FindNet('GND'))
        z.SetLocalClearance(p.FromMM(.15));z.SetThermalReliefGap(p.FromMM(.2));z.SetThermalReliefSpokeWidth(p.FromMM(.2))
        z.SetMinThickness(p.FromMM(.15));outline=z.Outline();outline.NewOutline()
        for x,y in [(1.3,1.3),(40.7,1.3),(40.7,38.7),(1.3,38.7)]:outline.Append(p.FromMM(x),p.FromMM(y))
        b.Add(z)
p.ZONE_FILLER(b).Fill(b.Zones())
p.SaveBoard(str(path),b)
pro=ROOT/'click-counter-Q1.kicad_pro';d=json.loads(pro.read_text())
for n in d['net_settings']['classes']:n['clearance']=.127
pro.write_text(json.dumps(d,indent=2))
(ROOT/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "ClickCounter")(type "KiCad")(uri "${KIPRJMOD}/ClickCounter.pretty")(options "")(descr "DE188 Rev4 custom footprint")))\n')
print('Routed board: 5 mil minimum tracks, 5 mil clearance; two internal GND fills.')
