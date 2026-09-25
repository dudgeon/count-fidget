"""Lock short Q4 USB, supply bypass and feedback routes before autorouting.

Run only after prepare_q4_route.py --reset-route. Routes are actual copper,
not routing hints; finish_q4_board preserves them when importing incremental SES.
"""
import json
from pathlib import Path
import pcbnew as p
from sync_q4_board import sync
OUT=Path(__file__).resolve().parents[1]/'electronics/q4'
b=p.LoadBoard(str(OUT/'click-counter-Q4.kicad_pcb'))
assert b.GetCopperLayerCount()==2 and not list(b.GetTracks())
sync(b)
fps={f.GetReference():f for f in b.GetFootprints()}
def pt(ref,pin):
 a=next(a for a in fps[ref].Pads() if a.GetNumber()==str(pin))
 return (p.ToMM(a.GetPosition().x),p.ToMM(a.GetPosition().y))
def v(q):return p.VECTOR2I(p.FromMM(q[0]),p.FromMM(q[1]))
records=[]
def route(net,points,width=.2,layer=p.B_Cu):
 for a,c in zip(points,points[1:]):
  if a==c:continue
  t=p.PCB_TRACK(b);t.SetStart(v(a));t.SetEnd(v(c));t.SetWidth(p.FromMM(width));t.SetLayer(layer);t.SetNet(b.FindNet(net));t.SetLocked(True);b.Add(t)
 records.append({'net':net,'layer':p.LayerName(layer),'width_mm':width,'points':points})
def link(net,ref,pin,ref2,pin2,mid=(),width=.2,layer=p.B_Cu):route(net,[pt(ref,pin),*mid,pt(ref2,pin2)],width,layer)
def via(net,q):
 t=p.PCB_VIA(b);t.SetPosition(v(q));t.SetWidth(p.FromMM(.6));t.SetDrill(p.FromMM(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(b.FindNet(net));t.SetLocked(True);b.Add(t)
 records.append({'net':net,'via':q,'diameter_mm':.6,'drill_mm':.3})
def ground(ref,pin,q,mid=()):
 route('GND',[pt(ref,pin),*mid,q],.2);via('GND',q)
# USB full-speed paths. The short single-layer MCU-to-clamp routes are kept
# clear of unrelated copper; the duplicated USB-C data contacts remain connected
# by the general route and must be checked after import.
link('USB_DM','U1',32,'D2',6,[(28.8,27.75),(29.25,27.3),(29.25,26.5),(29.7,26.05)])
link('USB_DP','U1',33,'D2',4,[(29.4,28.25),(29.7,27.95)])
link('USB_DM','D2',1,'J1','B7',[(34.0,26.05),(34.2,26.25)])
link('USB_DP','D2',3,'J1','B6',[(34.0,27.95),(34.2,27.75)])
ground('D2',2,(31.8,27.0))
# Regulator input/output and a genuinely local feedback divider.
link('SYS_LOAD','U3',6,'C5',1,[(30.65,7.95)])
link('SYS_LOAD','U3',4,'U3',6,[(30.32,6.65),(30.32,7.95)],width=.15)
link('VLOGIC','U3',1,'C6',1,[(28.1125,8.8),(27.1625,9.75)],width=.25)
link('VLOGIC','R30',1,'C6',1,[(25.275,8.3)],width=.2)
link('VLOGIC_FB','U3',2,'R30',2,width=.15)
link('VLOGIC_FB','R30',2,'R31',1,width=.15)
link('GND','U3',3,'U3',7,[(28.6,6.65)],width=.2)
link('GND','U3',5,'U3',7,width=.2)
ground('U3',7,(29.0,9.1));ground('U3',7,(29.0,5.8))
route('GND',[pt('C5',2),(30.5,5.8),(29.0,5.8)],.25)
ground('C6',2,(23.35,10.9));ground('R31',2,(24.2,5.65))
# Charger bypasses, with short traces escaping its fine-pitch leads.
link('VBUS','U2',10,'C1',1,[(29.85,12.8),(30.25,13.2)],width=.18)
link('SYS','U2',1,'C2',1,[(26.6,12.8),(26.6,13.2),(25.65,13.2)],width=.18)
route('CELL_P',[pt('U2',2),(26.0,12.4)],.15);via('CELL_P',(26.0,12.4))
route('CELL_P',[(26.0,12.4),(26.0,15.0)],.25,p.F_Cu);via('CELL_P',(26.0,15.0))
route('CELL_P',[(26.0,15.0),pt('C3',1)],.25)
ground('U2',11,(28.0,13.6));ground('U2',11,(28.0,10.4))
link('GND','U2',5,'U2',11,[(27.6,11.2)],width=.15)
ground('C1',2,(33.75,13.2));ground('C2',2,(23.5,14.55));ground('C3',2,(30.1,15.0))
# Protected return sense resistor and back-to-back FET midpoint remain distinct.
link('FET_DRAIN','Q1',3,'Q2',3,width=.4)
link('TEMP_COLD_OK','Q3',1,'R14',1,[(13.175,19.8375)],width=.2)
link('TEMP_HOT_OK','Q4',1,'R15',1,[(17.175,19.8375)],width=.2)
link('VBUS','U5',8,'C9',1,width=.2)
ground('C9',2,(21.35,11.075))
link('VLOGIC','U6',1,'C20',1,width=.25)
ground('C20',2,(15.325,16.25))
# Slew capacitors return to each switch input, not ground.
link('OLED_CT','U6',4,'C28',2,[(21.8,13.05),(22.125,12.725)],width=.2)
link('OLED_SUPPLY','U6',5,'U6',6,width=.25)
link('SYS_CT','U7',4,'C29',2,width=.2)
link('SYS','U7',1,'U7',3,[(24.85,18.95),(24.85,17.05)],width=.2)
# Local STM32 bypasses, one on every supply pin group.
link('VLOGIC','U1',1,'C31',1,[(18.125,29.75)],width=.2)
link('VLOGIC','U1',9,'C35',1,[(18.2,25.75),(18.2,24.375)],width=.2)
link('VLOGIC','U1',24,'C34',1,[(26.25,21.075)],width=.2)
link('VLOGIC','U1',36,'C33',1,[(29.525,29.75)],width=.2)
link('VLOGIC','U1',48,'C32',1,[(20.75,32.425)],width=.2)
link('NRST','U1',7,'C10',1,[(18.4,26.75),(17.975,27.175)],width=.2)
for r,q in [('C31',(16.1,29.025)),('C35',(16.1,22.825)),('C34',(29.45,20.6)),('C33',(28.4,31.375)),('C32',(23.275,34.65)),('C10',(16.1,25.925))]:ground(r,2,q)
for pin,q in [(8,(20.7,26.25)),(23,(25.75,24.2)),(35,(26.3,29.25)),(47,(21.25,29.8))]:ground('U1',pin,q)
# FRAM bypass at the VDD end of its package. All connections are downstream
# of R32; no copper path bypasses the deliberately current-limited supply.
link('VFRAM','U8',8,'C36',1,[(25.53,47.905)],width=.25)
link('VFRAM','U8',7,'U8',8,width=.25)
link('VFRAM','C36',1,'C30',1,width=.25)
ground('C36',2,(26.95,46.525));ground('C30',2,(27.0,51.45));ground('U8',4,(17.15,44.095))
p.SaveBoard(str(OUT/'click-counter-Q4.kicad_pcb'),b)
assert p.ExportSpecctraDSN(b,str(OUT/'click-counter-Q4.dsn'))
(OUT/'locked-route-seed.json').write_text(json.dumps({'revision':'Q4','tracks_and_vias':records,'qualification':'Geometric seed only; fresh native DRC and completed-path review required.'},indent=2)+'\n')
print(f'Q4 locked seed saved: {len(list(b.GetTracks()))} copper items. Run native DRC before autorouting.')
