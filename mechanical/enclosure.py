"""Parametric fit-study CAD, millimetres. Not released for final electronics.
Run from this directory with Python + CadQuery + matplotlib.
All non-printed components below are dimensional envelopes, not vendor CAD.
"""
from pathlib import Path
import json
import cadquery as cq
from cadquery import exporters
from PIL import Image, ImageDraw, ImageFont

OUT=Path(__file__).resolve().parent
W,D,WALL,FLOOR=46.,44.,1.2,1.2
PCB_Z,PCB_T=9.5,1.0
SEAM,TOP=14.5,16.0
SCREWS=[(-19.,-18.5),(19.,-18.5),(-19.,18.5),(19.,18.5)]
KEYS=[(-9.525,8.),(9.525,8.)]

def block(w,d,h,z=0,x=0,y=0):
    return cq.Workplane('XY').box(w,d,h,centered=(True,True,False)).translate((x,y,z))
def rounded(w,d,h,z,r=3):
    return block(w,d,h,z).edges('|Z').fillet(r)
def cyl(r,h,z,x=0,y=0):
    return cq.Workplane('XY').circle(r).extrude(h).translate((x,y,z))

base=rounded(W,D,SEAM,0).cut(rounded(W-2*WALL,D-2*WALL,SEAM,FLOOR,1.8))
# Battery tray, sized for a supplier-prepared LIR2032 lead assembly.
tray=cyl(11.1,1.4,FLOOR,0,7).cut(cyl(10.45,1.6,FLOOR,0,7))
tray=tray.cut(block(5,6,3,FLOOR,x=0,y=-4))  # lead egress
base=base.union(tray)
for x,y in SCREWS:
    base=base.union(cyl(2.7,PCB_Z-FLOOR,FLOOR,x,y))
    base=base.cut(cyl(.85,PCB_Z-2,2,x,y))
# Side USB-C opening; connector envelope must be replaced with vendor drawing.
base=base.cut(block(8,10.0,4.2,9.9,x=W/2,y=-4.6))

lid=rounded(W,D,TOP-SEAM,SEAM)
for x,y in KEYS: lid=lid.cut(block(14.2,14.2,4,SEAM-1,x,y))
lid=lid.union(block(38,15.6,2,TOP,0,-12.5))
lid=lid.cut(block(35.5,13.6,3.0,SEAM-.1,0,-12.5))
lid=lid.cut(block(32.5,6.8,5,SEAM,0,-12.5))
for x,y in SCREWS:
    lid=lid.union(cyl(2.15,SEAM-(PCB_Z+PCB_T),PCB_Z+PCB_T,x,y))
    lid=lid.cut(cyl(1.2,12,PCB_Z+PCB_T-1,x,y))
    lid=lid.cut(cyl(2.05,4.8,TOP-.7,x,y))

pcb=rounded(42,40,PCB_T,PCB_Z,2)
for x,y in SCREWS: pcb=pcb.cut(cyl(1.2,3,PCB_Z-1,x,y))
for x,y in KEYS:
    pcb=pcb.cut(cyl(2,3,PCB_Z-1,x,y))
    for dx,dy,r in [(-3.81,-2.54,.8),(2.54,-5.08,.8),(-5.08,0,.9),(5.08,0,.9)]:
        pcb=pcb.cut(cyl(r,3,PCB_Z-1,x+dx,y+dy))

battery=cyl(10.,3.4,1.5,0,7)
lcd=block(34.9,13,2.2,14.5,0,-12.5)
usb=block(8,8.94,3.2,10.5,19.5,-4.6)
mcu=block(12,12,1.4,8.1,0,-12.5)
switches=[block(15.6,15.6,11.6,PCB_Z+PCB_T,x,y) for x,y in KEYS]
caps=[]
for x,y in KEYS:
    outer=rounded(18.2,18.2,7,21.8,1.4).translate((x,y,0))
    inner=block(15.8,15.8,6,21.7,x,y)
    caps.append(outer.cut(inner))

parts=[('base',base,'#80b9c0'),('lid',lid,'#d4eef0'),('PCB-envelope',pcb,'#296e58'),
       ('battery-envelope',battery,'#c5c7cc'),('LCD-envelope',lcd,'#b6c49f'),
       ('USB-envelope',usb,'#b6bcc6'),('MCU-envelope',mcu,'#293444')]
parts += [(f'switch-{i+1}-envelope',s,'#313d4b') for i,s in enumerate(switches)]
parts += [(f'keycap-{i+1}-envelope',s,'#64a7d1' if i==0 else '#edb96e') for i,s in enumerate(caps)]
assembly=cq.Assembly(name='Click-counter-fit-study')
for name,shape,color in parts:
    assert shape.val().isValid(),name
    assembly.add(shape,name=name,color=cq.Color(color))
assembly.export(str(OUT/'fit-study.step'))
exporters.export(base,str(OUT/'base-fit-study.stl'))
# Raised bezel on the bed: underside spacers face up. Supports required under
# the remaining top face, which is 2 mm above the bed.
lid_print=lid.rotate((0,0,0),(1,0,0),180).translate((0,0,TOP+2))
exporters.export(lid_print,str(OUT/'lid-fit-study.stl'))

# Compute actual model volumes; weights for bought components remain estimates.
mass={n:round(s.val().Volume()*1.24/1000,3) for n,s,c in parts if n in ['base','lid']}
checks={
 'status':'FIT STUDY ONLY — LCD speed, approved standoff and USB/switch fit pending',
 'body_mm':[W,D,TOP+2],'overall_keycap_envelope_mm':[W,D,28.8],
 'pcb_envelope_mm':[42,40,PCB_T],
 'solid_PLA_shell_mass_g':mass,
 'base_solids':len(base.solids().vals()),'lid_solids':len(lid.solids().vals()),
 'base_lid_intersection_mm3':round(base.intersect(lid).val().Volume(),8),
 'battery_pcb_gap_mm':PCB_Z-(1.5+3.4),
 'caveats':['LCD pin matrix obtained; current part suffix, response time and mechanical support not finalized.',
 'Switch plate stack height and clip clearance need physical fit test.',
 'No LCD leads, battery leads, NTC, solder fillets, passive parts, screws or cable overmold are modeled.',
 'Component envelope intersections do not constitute assembly clearance verification.']}
(OUT/'geometry-check.json').write_text(json.dumps(checks,indent=2))
assert checks['base_solids']==1 and checks['lid_solids']==1
assert checks['base_lid_intersection_mm3']<0.001, checks

def render(path,exploded=False):
    import numpy as np
    width,height=1400,1100
    canvas=np.empty((height,width,3),dtype=np.uint8);canvas[:]=[244,246,248]
    depth=np.full((height,width),np.inf,dtype=np.float32)
    target=np.array([0,0,32 if exploded else 13],dtype=float)
    camera=target+np.array([50,-85,140],dtype=float)
    forward=(target-camera);forward/=np.linalg.norm(forward)
    right=np.cross(forward,[0,0,1]);right/=np.linalg.norm(right)
    up=np.cross(right,forward)
    scale=10.0 if exploded else 13.6
    light=np.array([-0.35,-0.6,0.72]);light/=np.linalg.norm(light)
    render_parts=[]
    for name,shape,color in parts:
        dz=0
        if exploded:
            if name=='lid':dz=30
            elif 'keycap' in name:dz=40
            elif 'switch' in name:dz=18
            elif name=='LCD-envelope':dz=24
            elif name not in ['base','battery-envelope']:dz=12
        render_parts.append((shape,color,dz))
    if not exploded:
        for label,size,x,y,z in [('00000421',4,0,-12.5,16.71),('+1',4,-9.525,8,28.81),('RESET',2.5,9.525,8,28.81)]:
            shape=cq.Workplane('XY').text(label,size,.04,font='DejaVu Sans Mono',kind='bold').translate((x,y,z))
            render_parts.append((shape,'#203447',0))
    for shape,color,dz in render_parts:
        vertices,triangles=shape.val().tessellate(.07,.15)
        pts=np.array([(p.x,p.y,p.z+dz) for p in vertices])
        rel=pts-target
        projected=np.column_stack((width/2+(rel@right)*scale,height*.56-(rel@up)*scale,(pts-camera)@forward))
        rgb=np.array([int(color[i:i+2],16) for i in (1,3,5)],dtype=float)
        for tri in triangles:
            q=projected[list(tri)];xyz=pts[list(tri)]
            xmin=max(0,int(np.floor(q[:,0].min())));xmax=min(width-1,int(np.ceil(q[:,0].max())))
            ymin=max(0,int(np.floor(q[:,1].min())));ymax=min(height-1,int(np.ceil(q[:,1].max())))
            if xmin>xmax or ymin>ymax:continue
            den=(q[1,1]-q[2,1])*(q[0,0]-q[2,0])+(q[2,0]-q[1,0])*(q[0,1]-q[2,1])
            if abs(den)<1e-9:continue
            xx,yy=np.meshgrid(np.arange(xmin,xmax+1)+.5,np.arange(ymin,ymax+1)+.5)
            aa=((q[1,1]-q[2,1])*(xx-q[2,0])+(q[2,0]-q[1,0])*(yy-q[2,1]))/den
            bb=((q[2,1]-q[0,1])*(xx-q[2,0])+(q[0,0]-q[2,0])*(yy-q[2,1]))/den
            cc=1-aa-bb;zz=aa*q[0,2]+bb*q[1,2]+cc*q[2,2]
            block_depth=depth[ymin:ymax+1,xmin:xmax+1]
            mask=(aa>=-1e-8)&(bb>=-1e-8)&(cc>=-1e-8)&(zz<block_depth)
            normal=np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]);n=np.linalg.norm(normal)
            shade=.45+.55*abs(np.dot(normal/n,light)) if n>1e-12 else .8
            block_depth[mask]=zz[mask]
            canvas[ymin:ymax+1,xmin:xmax+1][mask]=np.clip(rgb*shade,0,255).astype(np.uint8)
    im=Image.fromarray(canvas);d=ImageDraw.Draw(im)
    bold=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',38)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',23)
    d.text((55,35),'CLICK COUNTER',font=bold,fill='#193144')
    d.text((55,90),'Exploded CAD fit study' if exploded else 'CAD fit study · 46 × 44 mm body',font=font,fill='#46616f')
    d.text((55,1050),'Component envelopes only · Unrouted PCB · Final fit not verified',font=font,fill='#526573')
    im.save(path)
render(OUT/'assembled-cad.png')
render(OUT/'exploded-cad.png',True)
print(json.dumps(checks,indent=2))
