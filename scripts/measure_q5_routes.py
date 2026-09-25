"""Measure Q5 routed centerlines and conservative via-to-land clearances.

This is a geometric review aid, not a substitute for native DRC or measured
USB/analog qualification. No plane propagation or package lead delay is modeled.
"""
import pcbnew as p, math,json,hashlib,heapq,collections
from pathlib import Path
OUT=Path(__file__).resolve().parents[1]/'electronics/q5'
path=OUT/'click-counter-Q5.kicad_pcb';b=p.LoadBoard(str(path)); fps={f.GetReference():f for f in b.GetFootprints()}
def xy(q):return (round(p.ToMM(q.x),6),round(p.ToMM(q.y),6))
def dist(a,c):return math.hypot(a[0]-c[0],a[1]-c[1])
def pad(ref,pin):return next(a for a in fps[ref].Pads() if a.GetNumber()==str(pin))
tracks=list(b.GetTracks()); layers=(p.F_Cu,p.B_Cu)
netgraph={}
def graph(net):
 if net in netgraph:return netgraph[net]
 nodes=set();segments=[];edges=[];pads=[]
 for t in tracks:
  if t.GetNetname()!=net:continue
  if isinstance(t,p.PCB_VIA):
   q=xy(t.GetPosition()); a=(*q,p.F_Cu);c=(*q,p.B_Cu);nodes.update([a,c]);edges.append((a,c,0,1))
  else:
   a=(*xy(t.GetStart()),t.GetLayer());c=(*xy(t.GetEnd()),t.GetLayer());nodes.update([a,c]);segments.append((a,c))
 for f in fps.values():
  for a in f.Pads():
   if a.GetNetname()!=net:continue
   for l in layers:
    if a.IsOnLayer(l):nodes.add((*xy(a.GetPosition()),l));pads.append((a,l))
 g=collections.defaultdict(list)
 def edge(a,c,length,via=0):g[a].append((c,length,via));g[c].append((a,length,via))
 for a,c in segments:
  length=dist(a,c);near=[]
  for q in nodes:
   if q[2]!=a[2]:continue
   if abs(dist(a,q)+dist(q,c)-length)<.000005:near.append(q)
  near.sort(key=lambda q:dist(a,q))
  for x,y in zip(near,near[1:]):edge(x,y,dist(x,y))
 for a,c,length,vias in edges:edge(a,c,length,vias)
 # Native pad geometry is used to join copper endpoints inside a common land.
 for a,l in pads:
  ctr=(*xy(a.GetPosition()),l)
  for q in nodes:
   if q[2]==l and a.HitTest(p.VECTOR2I(p.FromMM(q[0]),p.FromMM(q[1]))):edge(ctr,q,dist(ctr,q))
 netgraph[net]=g;return g

def shortest(ref,pin,ref2=None,pin2=None,nearest_via=False):
 a=pad(ref,pin);net=a.GetNetname();g=graph(net);start=(*xy(a.GetPosition()),p.B_Cu if a.IsOnLayer(p.B_Cu) else p.F_Cu)
 targets=set()
 if nearest_via:
  for t in tracks:
   if isinstance(t,p.PCB_VIA) and t.GetNetname()==net:
    targets.update([(*xy(t.GetPosition()),l) for l in layers])
 else:
  z=pad(ref2,pin2);assert z.GetNetname()==net
  targets={(*xy(z.GetPosition()),l) for l in layers if z.IsOnLayer(l)}
 queue=[(0,0,start)];seen={};previous={}
 while queue:
  length,vs,n=heapq.heappop(queue)
  if n in seen:continue
  seen[n]=(length,vs)
  if n in targets:return {'net':net,'from':f'{ref}.{pin}','to':f'{ref2}.{pin2}' if not nearest_via else 'nearest same-net via','planar_mm':round(length,6),'via_count':vs,'target_xy':n[:2]}
  for q,w,k in g[n]:
   if q not in seen:heapq.heappush(queue,(length+w,vs+k,q))
 return {'net':net,'from':f'{ref}.{pin}','to':f'{ref2}.{pin2}','error':'No exact endpoint/pad graph path; inspect manually. Planes are intentionally excluded.'}
pairs=[('U1',32,'J1','A7'),('U1',32,'J1','B7'),('U1',33,'J1','A6'),('U1',33,'J1','B6'),('U3',6,'C5',1),('U3',1,'C6',1),('U3',2,'R30',2),('U3',2,'R31',1),('U2',10,'C1',1),('U2',1,'C2',1),('U2',2,'C3',1),('U2',2,'BT1',1),('U5',8,'C9',1),('U6',1,'C20',1),('U6',4,'C28',2),('U7',4,'C29',2),('U7',3,'D3',3),('U7',3,'R38',2),('R38',1,'D4',1),('U7',3,'C40',1),('U7',3,'R35',1),('U8',8,'C36',1),('U8',8,'C30',1),('U1',1,'C31',1),('U1',9,'C35',1),('U1',24,'C34',1),('U1',36,'C33',1),('U1',48,'C32',1),('U1',14,'R36',2),('U1',14,'C37',1),('U1',20,'D3',2),('U4',4,'C4',2),('U4',5,'C4',1),('D1',5,'C38',1),('D2',5,'C39',1),('BT1',2,'Q1',2),('Q3',1,'R14',1),('Q4',1,'R15',1)]
paths=[shortest(*v) for v in pairs]
grounds=[shortest(ref,pin,nearest_via=True) for ref,pin in [('C5',2),('C6',2),('C1',2),('C2',2),('C3',2),('C9',2),('C20',2),('C30',2),('C36',2),('C31',2),('C32',2),('C33',2),('C34',2),('C35',2),('C37',2)]]
gaps=[]
for t in tracks:
 if not isinstance(t,p.PCB_VIA):continue
 q=t.GetPosition();rad=t.GetWidth(p.F_Cu)/2
 for f in fps.values():
  for a in f.Pads():
   if a.GetAttribute()!=p.PAD_ATTRIB_SMD or not a.GetNetname() or a.GetNetname()!=t.GetNetname():continue
   box=a.GetBoundingBox();dx=max(box.GetX()-q.x,0,q.x-box.GetRight());dy=max(box.GetY()-q.y,0,q.y-box.GetBottom());gap=p.ToMM(math.hypot(dx,dy)-rad)
   if a.GetShape()==p.PAD_SHAPE_CIRCLE:gap=p.ToMM(math.hypot(q.x-a.GetPosition().x,q.y-a.GetPosition().y)-a.GetSize().x/2-rad)
   if gap<.1:gaps.append({'ref':f.GetReference(),'pad':a.GetNumber(),'net':a.GetNetname(),'via':xy(q),'conservative_bounding_box_gap_mm':round(gap,6)})
r={'board_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'measurement_method':'Shortest centerline graph with endpoints joined by exact native pad hit testing. Planar length includes pad-center joins; via count excludes component lead/package propagation. Ground pours/plane propagation excluded. USB characteristic impedance is not inferred.','paths':paths,'ground_to_nearest_via':grounds,'same_net_via_to_smt_land_gaps_below_0_1mm':gaps,'track_count':len(tracks),'via_count':sum(isinstance(x,p.PCB_VIA) for x in tracks)}
(OUT/'routing-audit.json').write_text(json.dumps(r,indent=2)+'\n')
print('Q5 route measurements saved; inspect actual paths and retained qualification limits.')
