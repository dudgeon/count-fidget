"""Prepare the Q5 board for autorouting: lock the SYS trunk and export the DSN.

Run only after prepare_q5_route.py --reset-route. One locked seed carries SYS
from the charger (U2 pin 1) to the soft-power switch (U7 pin 1) on F.Cu down
the right edge, between the USB-C shell pins, where the headless router could
not find a corridor. Every other net, including GND, is routed by the router
as traces; finish_q5_board then adds recorded GND stitching, fills both GND
pours (which complete a few GND links) and preserves exactly this seed.
"""
import json
from pathlib import Path
import pcbnew as p
from sync_q5_board import sync
OUT=Path(__file__).resolve().parents[1]/'electronics/q5'
b=p.LoadBoard(str(OUT/'click-counter-Q5.kicad_pcb'))
assert b.GetCopperLayerCount()==2 and not list(b.GetTracks())
sync(b)
fps={f.GetReference():f for f in b.GetFootprints()}
def pt(ref,pin):
 a=next(a for a in fps[ref].Pads() if a.GetNumber()==str(pin))
 return (round(p.ToMM(a.GetPosition().x),4),round(p.ToMM(a.GetPosition().y),4))
def v(q):return p.VECTOR2I(p.FromMM(q[0]),p.FromMM(q[1]))
records=[]
def route(net,points,width=.3,layer=p.B_Cu):
 for a,c in zip(points,points[1:]):
  if a==c:continue
  t=p.PCB_TRACK(b);t.SetStart(v(a));t.SetEnd(v(c));t.SetWidth(p.FromMM(width));t.SetLayer(layer);t.SetNet(b.FindNet(net));t.SetLocked(True);b.Add(t)
 records.append({'net':net,'layer':p.LayerName(layer),'width_mm':width,'points':[list(q) for q in points]})
def via(net,q):
 t=p.PCB_VIA(b);t.SetPosition(v(q));t.SetWidth(p.FromMM(.6));t.SetDrill(p.FromMM(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(b.FindNet(net));t.SetLocked(True);b.Add(t)
 records.append({'net':net,'via':list(q),'diameter_mm':.6,'drill_mm':.3})
import sys
start=pt('U2',1);end=pt('U7',1)
if '--no-seed' not in sys.argv:
 route('SYS',[start,(33.4,10.3),(33.4,11.3)],.2)
 via('SYS',(33.4,11.3))
 route('SYS',[(33.4,11.3),(36.9,14.8),(36.9,21.0),(37.9,22.0),(37.9,32.0),(37.4,32.5)],.3,p.F_Cu)
 via('SYS',(37.4,32.5))
 route('SYS',[(37.4,32.5),(35.3,32.9),(35.3,35.55),end],.3)
p.SaveBoard(str(OUT/'click-counter-Q5.kicad_pcb'),b)
assert p.ExportSpecctraDSN(b,str(OUT/'click-counter-Q5.dsn'))
(OUT/'locked-route-seed.json').write_text(json.dumps({'revision':'Q5','tracks_and_vias':records,'qualification':'Geometric seed only; fresh native DRC and completed-path review required.'},indent=2)+'\n')
print(f'Q5 locked SYS seed saved: {len(list(b.GetTracks()))} copper items. Route with Freerouting, then run finish_q5_board.py --import-route.')
