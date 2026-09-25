#!/usr/bin/env python3
"""Generate a separate Q4 fit candidate; never writes historical Rev0 or PCB files.

Requires CadQuery 2.8, NumPy, Pillow and an explicit KiCad Python interpreter.
All coordinates in mm: centered board top-view X/Y, Z positive above base floor.
Component solids are conservative/nominal envelopes, not production vendor CAD.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
import subprocess
import struct
import sys
import tempfile
from pathlib import Path

import cadquery as cq
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'mechanical/q4'
BOARD = ROOT / 'electronics/q4/click-counter-Q4.kicad_pcb'
MODEL = ROOT / 'electronics/q4/netlist-Q4.json'
W, D, WALL, FLOOR = 50., 60., 1.6, 1.6
PCB_Z, PCB_T, SEAM, TOP, BEZEL_TOP = 11.1, 1., 15.6, 17.1, 19.6
FRONT_SEAM, FRONT_TOP, FRONT_STEP_Y = 18.1, 19.6, 4.5
LCD_X, LCD_Y = 0., -10.3
KEYS = [(-9.525, 13.8), (9.525, 13.8)]
MOUNTS = [(-18.5, 25.), (18.5, 25.)]
LOAD_SUPPORTS = [(-15., 16.3), (15., 16.3)]
BAT_X, BAT_Y, BAT_Z = 0., 7., 1.9
KEEPER_Z = 6.4
KEEPER_SCREWS = [(-8.5, 18.8), (8.5, 18.8)]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def block(w, d, h, z=0, x=0, y=0):
    return cq.Workplane('XY').box(w, d, h, centered=(True, True, False)).translate((x, y, z))


def rounded(w, d, h, z=0, r=2, x=0, y=0):
    return block(w, d, h, z, x, y).edges('|Z').fillet(r)


def cyl(r, h, z, x=0, y=0):
    return cq.Workplane('XY').circle(r).extrude(h).translate((x, y, z))


def volume(shape):
    return sum(s.Volume() for s in shape.solids().vals())


def overlap(a, b):
    aa,bb=a.val().BoundingBox(),b.val().BoundingBox()
    if any(getattr(aa,axis+'max')<=getattr(bb,axis+'min')+1e-8 or getattr(bb,axis+'max')<=getattr(aa,axis+'min')+1e-8 for axis in ('x','y','z')):
        return 0.
    return volume(a.intersect(b))


def mesh_check(path):
    data=path.read_bytes(); count=struct.unpack_from('<I',data,80)[0]
    assert len(data)==84+50*count, 'Unexpected binary STL length'
    edges=Counter(); z_values=[]
    for i in range(count):
        points=struct.unpack_from('<12f',data,84+50*i)[3:]
        vertices=[tuple(round(v,5) for v in points[j:j+3]) for j in [0,3,6]]
        z_values.extend(v[2] for v in vertices)
        for a,b in [(0,1),(1,2),(2,0)]: edges[tuple(sorted([vertices[a],vertices[b]]))]+=1
    bad=sum(v!=2 for v in edges.values())
    assert not bad, f'{path.name}: nonmanifold STL edges'
    assert abs(min(z_values))<=.00001, f'{path.name}: print part is not on bed'
    return dict(triangles=count,nonmanifold_edges=bad,vertex_quantization_mm=.00001,z_min_mm=min(z_values),z_max_mm=max(z_values))


def read_board(kicad_python):
    board_hash, model_hash = sha(BOARD), sha(MODEL)
    code = '''import json, sys, pcbnew
b=pcbnew.LoadBoard(sys.argv[1]); result=[]
for f in b.GetFootprints():
 p=f.GetPosition(); bb=f.GetBoundingBox(False,False); pads=[]
 for a in f.Pads():
  q=a.GetPosition(); d=a.GetDrillSize(); s=a.GetSize()
  pads.append(dict(number=a.GetNumber(),x=pcbnew.ToMM(q.x),y=pcbnew.ToMM(q.y),
   drill=[pcbnew.ToMM(d.x),pcbnew.ToMM(d.y)],size=[pcbnew.ToMM(s.x),pcbnew.ToMM(s.y)],
   angle=a.GetOrientationDegrees(),npth=a.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH))
 result.append(dict(ref=f.GetReference(),x=pcbnew.ToMM(p.x),y=pcbnew.ToMM(p.y),
  angle=f.GetOrientationDegrees(),side='bottom' if f.IsFlipped() else 'top',
  bbox=[pcbnew.ToMM(v) for v in [bb.GetX(),bb.GetY(),bb.GetWidth(),bb.GetHeight()]],pads=pads))
pts=[q for d in b.GetDrawings() if d.GetLayer()==pcbnew.Edge_Cuts for q in [d.GetStart(),d.GetEnd()]]
x0=min(p.x for p in pts);y0=min(p.y for p in pts);x1=max(p.x for p in pts);y1=max(p.y for p in pts)
print(json.dumps(dict(thickness=pcbnew.ToMM(b.GetDesignSettings().GetBoardThickness()),
 edges=[pcbnew.ToMM(v) for v in [x0,y0,x1-x0,y1-y0]],parts=result)))
'''
    r = subprocess.run([kicad_python, '-c', code, str(BOARD)], check=True, capture_output=True, text=True)
    data = json.loads(r.stdout)
    model = json.loads(MODEL.read_text())
    by_ref = {p['ref']: p for p in data['parts']}
    for p in model['parts']:
        actual = by_ref[p['ref']]
        assert all(abs(actual[k] - p[k]) < 1e-6 for k in ('x', 'y')), p['ref']
        assert actual['side'] == p['side'], p['ref']
    assert abs(data['thickness'] - 1) < 1e-6
    assert all(abs(a-b)<1e-5 for a,b in zip(data['edges'],[0,0,42,54])), data['edges']
    assert all(by_ref[n]['side']=='top' for n in ('H1','H2','H3','H4'))
    assert by_ref['DS1']['x'] == 21 and by_ref['DS1']['side']=='top'
    assert len(by_ref['DS1']['pads']) == 7
    for ref, (x, y) in zip(['SW1', 'SW2'], KEYS):
        central = [p for p in by_ref[ref]['pads'] if abs(p['drill'][0] - 3.95) < .001]
        assert len(central) == 1 and abs(central[0]['x'] - 21 - x) < 1e-6 and abs(central[0]['y'] - 27 - y) < 1e-6
    assert (by_ref['J1']['x'],by_ref['J1']['angle']%360,by_ref['J1']['side']) == (38.9,270,'bottom')
    assert sha(BOARD)==board_hash and sha(MODEL)==model_hash, 'Source changed while reading; rebuild from stable files'
    data['board_sha256'] = board_hash
    data['model_sha256'] = model_hash
    return data, by_ref


def render(path, parts, exploded=False, cutaway=False, label=None):
    width, height = 1300, 1050
    canvas = np.full((height, width, 3), [242, 246, 249], dtype=np.uint8)
    depth = np.full((height, width), np.inf, dtype=np.float32)
    target = np.array([0, 0, 24 if exploded else 13], dtype=float)
    camera = target + [75, -110, 190]
    forward = target - camera; forward /= np.linalg.norm(forward)
    right = np.cross(forward, [0, 0, 1]); right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    scale = 8.8 if exploded else 11.5
    light = np.array([-.35, -.6, .72]); light /= np.linalg.norm(light)
    for name, source, color in parts:
        if cutaway and (name.startswith('lid') or name in ['keycap-1', 'keycap-2']):
            continue
        shape = source
        if cutaway and name == 'base':
            shape = shape.cut(block(80, 80, 25, 8))
        dz = 0
        if exploded:
            dz = 28 if name.startswith('lid') else 38 if name.startswith('keycap') else 16 if name.startswith('switch') else 22 if name in ('OLED-glass','OLED-pixels','OLED-module','OLED-header') else 11 if name not in ['base', 'pack-envelope', 'battery-keeper'] else 0
        rgb = np.array([int(color[i:i+2], 16) for i in (1, 3, 5)])
        for solid in shape.solids().vals():
            verts, triangles = solid.tessellate(.12, .2)
            pts = np.array([(v.x, v.y, v.z + dz) for v in verts])
            rel = pts - target
            proj = np.column_stack((width/2 + rel@right*scale, height*.52-rel@up*scale, (pts-camera)@forward))
            for tri in triangles:
                q = proj[list(tri)]; xyz = pts[list(tri)]
                xmin, xmax = max(0, int(q[:, 0].min())), min(width-1, math.ceil(q[:, 0].max()))
                ymin, ymax = max(0, int(q[:, 1].min())), min(height-1, math.ceil(q[:, 1].max()))
                if xmin > xmax or ymin > ymax: continue
                den = (q[1,1]-q[2,1])*(q[0,0]-q[2,0])+(q[2,0]-q[1,0])*(q[0,1]-q[2,1])
                if abs(den) < 1e-9: continue
                xx, yy = np.meshgrid(np.arange(xmin,xmax+1)+.5, np.arange(ymin,ymax+1)+.5)
                a = ((q[1,1]-q[2,1])*(xx-q[2,0])+(q[2,0]-q[1,0])*(yy-q[2,1]))/den
                b = ((q[2,1]-q[0,1])*(xx-q[2,0])+(q[0,0]-q[2,0])*(yy-q[2,1]))/den
                c = 1-a-b; z = a*q[0,2]+b*q[1,2]+c*q[2,2]
                dep = depth[ymin:ymax+1, xmin:xmax+1]
                mask = (a >= -1e-8)&(b >= -1e-8)&(c >= -1e-8)&(z < dep)
                normal = np.cross(xyz[1]-xyz[0], xyz[2]-xyz[0]); norm = np.linalg.norm(normal)
                shade = .45 + .55*abs(normal@light/norm) if norm else .8
                dep[mask] = z[mask]
                canvas[ymin:ymax+1, xmin:xmax+1][mask] = np.clip(rgb*shade, 0, 255).astype(np.uint8)
    im = Image.fromarray(canvas); draw = ImageDraw.Draw(im)
    font_path = '/System/Library/Fonts/Supplemental/Arial.ttf'
    font = ImageFont.truetype(font_path, 29) if Path(font_path).exists() else ImageFont.load_default(size=29)
    small = ImageFont.truetype(font_path, 20) if Path(font_path).exists() else ImageFont.load_default(size=20)
    view = label or ('Exploded assembly' if exploded else 'Interior cutaway' if cutaway else 'Assembled enclosure')
    draw.text((40, 30), 'COUNT FIDGET  /  Q4', font=font, fill='#183e50')
    draw.text((40, 75), f'{view} · 50 × 60 mm body', font=small, fill='#456473')
    draw.text((40, 1004), 'Engineering fit candidate · component envelopes · physical qualification pending', font=small, fill='#456473')
    im.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--kicad-python', required=True)
    ap.add_argument('--skip-render', action='store_true')
    ap.add_argument('--input-board',type=Path)
    ap.add_argument('--input-model',type=Path)
    ap.add_argument('--output',type=Path)
    args = ap.parse_args()
    global BOARD, MODEL, OUT
    if args.input_board: BOARD=args.input_board.resolve()
    if args.input_model: MODEL=args.input_model.resolve()
    if args.output: OUT=args.output.resolve()
    generator_hash = sha(Path(__file__))
    OUT.mkdir(parents=True, exist_ok=True)
    # A failed rebuild must never leave an older success manifest in place.
    (OUT/'build-manifest.json').unlink(missing_ok=True)
    data, refs = read_board(args.kicad_python)
    global LCD_X, LCD_Y, MOUNTS
    LCD_X, LCD_Y = refs['DS1']['x']-21, refs['DS1']['y']-27
    MOUNTS = [(refs[r]['x']-21,refs[r]['y']-27) for r in ('H1','H2','H3','H4')]
    usb_y = refs['J1']['y']-27
    (OUT/'board-geometry.json').write_text(json.dumps(data, indent=2)+'\n')
    base = rounded(W,D,FRONT_SEAM,r=3).cut(rounded(W-2*WALL,D-2*WALL,FRONT_SEAM,FLOOR,r=1.4))
    base = base.cut(block(70,80,20,SEAM,0,FRONT_STEP_Y+40))
    for x,y in MOUNTS:
        base = base.union(cyl(2.6,PCB_Z-FLOOR,FLOOR,x,y)).cut(cyl(.85,PCB_Z-2.4,2.4,x,y))
    for x,y in LOAD_SUPPORTS:
        base = base.union(cyl(1.3,PCB_Z-FLOOR,FLOOR,x,y))
    tray = cyl(12.1,1.4,FLOOR,BAT_X,BAT_Y).cut(cyl(10.9,1.5,FLOOR,BAT_X,BAT_Y))
    tray = tray.cut(block(9,7,3,FLOOR,-11,3))
    base = base.union(tray)
    for x,y in KEEPER_SCREWS:
        base = base.union(cyl(2.4,KEEPER_Z-FLOOR,FLOOR,x,y)).cut(cyl(.85,KEEPER_Z-2.2,2.2,x,y))
    # Raised display roof clears the complete module; key plate remains at maker elevation.
    usb_cut = block(12,13.2,4.8,7.0,W/2,usb_y)
    base = base.cut(usb_cut)
    full_lid = rounded(W,D,TOP-SEAM,SEAM,r=3)
    lid = full_lid.cut(block(70,80,20,SEAM-1,0,FRONT_STEP_Y-40))
    front_lid = rounded(W,D,FRONT_TOP-FRONT_SEAM,FRONT_SEAM,r=3)
    front_lid = front_lid.intersect(block(70,80,20,FRONT_SEAM-1,0,FRONT_STEP_Y-40))
    bridge = block(W-2*WALL-.2,.8,FRONT_TOP-16.4,16.4,0,FRONT_STEP_Y-.5)
    lid = lid.union(front_lid).union(bridge)
    for x,y in KEYS:
        lid = lid.cut(block(14.05,14.05,8,SEAM-1,x,y))
    # Viewing opening is centered on active pixels, not the asymmetric glass outline.
    lid = lid.cut(block(23.2,12.4,12,PCB_Z+PCB_T,LCD_X,LCD_Y-2.1))
    for x,y in MOUNTS:
        mount_seam,mount_top=(FRONT_SEAM,FRONT_TOP) if y<0 else (SEAM,TOP)
        lid = lid.union(cyl(1.8,mount_seam-(PCB_Z+PCB_T)+.1,PCB_Z+PCB_T,x,y))
        lid = lid.cut(cyl(1.2,12,PCB_Z+PCB_T-.1,x,y))
        lid = lid.cut(cyl(2.1,3,mount_top-.6,x,y))
    lid = lid.cut(usb_cut)
    # Rear plate is installed on the two switches before their four pins are soldered.
    # A separate removable front cover exposes the OLED/header for simple assembly.
    # These are still four printed parts: base, front cover, rear key plate, keeper.
    lid_front = lid.intersect(block(80,80,40,0,0,FRONT_STEP_Y-.10-40))
    lid_rear = lid.intersect(block(80,80,40,0,0,FRONT_STEP_Y+.10+40))
    lid=lid_front.union(lid_rear)
    keeper = rounded(29,3.4,1.2,KEEPER_Z,.6,0,13)
    for x,y in KEEPER_SCREWS:
        keeper = keeper.union(block(4.8,6.0,1.2,KEEPER_Z,x,15.9)).union(cyl(2.4,1.2,KEEPER_Z,x,y))
        keeper = keeper.cut(cyl(1.2,2,KEEPER_Z-.1,x,y))
    for x,y in LOAD_SUPPORTS:
        keeper = keeper.cut(cyl(1.65,2,KEEPER_Z-.1,x,y))
    pcb = block(42,54,PCB_T,PCB_Z)
    tails = []
    for ref,p in refs.items():
        for pad in p['pads']:
            dx,dy = pad['drill']; x,y = pad['x']-21,pad['y']-27
            if min(dx,dy) <= 0: continue
            if abs(dx-dy) < 1e-6:
                hole = cyl(dx/2,3,PCB_Z-1,x,y)
            else:
                angle = (0 if dx>=dy else 90)-pad['angle']
                hole = cq.Workplane('XY').slot2D(max(dx,dy),min(dx,dy),angle).extrude(3).translate((x,y,PCB_Z-1))
            pcb = pcb.cut(hole)
            if ref == 'J1' and pad['number']=='SH':
                tails.append(('USB-shell-joint-'+str(len(tails)),block(pad['size'][0],pad['size'][1],.5,PCB_Z+PCB_T,x,y).rotate((x,y,0),(x,y,1),-pad['angle']),'#b7bcc0'))
            if ref.startswith('SW'):
                tails.append((ref+'-post-'+str(len(tails)),cyl(max(dx/2-.1,.25),2.3,PCB_Z-2.3,x,y),'#c4ad73'))
    pack = cyl(10.5,4.2,BAT_Z,BAT_X,BAT_Y)
    # Seven-pin header body sets2.5mm board separation. Trim protruding pins to<=1mm.
    module_z=PCB_Z+PCB_T+2.5
    module=block(27.3,27.8,1.2,module_z,LCD_X,LCD_Y)
    module_bottom=block(27.3,27.8,1.0,module_z-1,LCD_X,LCD_Y)
    for x in (LCD_X-11.65,LCD_X+11.65):
        for y in (LCD_Y-11.9,LCD_Y+11.9):
            module=module.cut(cyl(1.25,1.4,module_z-.1,x,y))
            module_bottom=module_bottom.cut(cyl(2.0,1.2,module_z-1.1,x,y))
    module_bottom=module_bottom.cut(block(18.2,3.0,1.2,module_z-1.1,LCD_X,LCD_Y-12.4))
    glass=block(24.74,16.9,1.4,module_z+1.2,LCD_X,LCD_Y-.58)
    max_glass=block(27.7,28.2,1.8,module_z-.2,LCD_X,LCD_Y).union(block(24.94,17.1,2.2,module_z+1.0,LCD_X,LCD_Y-.58))
    header=block(17.78,2.5,2.5,PCB_Z+PCB_T,LCD_X,LCD_Y-12.4)
    # Clearance envelopes cover body tolerance and nominal-header centering uncertainty.
    usb = block(7.35,8.94,3.31,PCB_Z-3.31,17.9,usb_y)
    mcu = block(9.4,9.4,1.6,PCB_Z-1.6,refs['U1']['x']-21,refs['U1']['y']-27)
    jst = block(4.95,6,2.96,PCB_Z-2.96,refs['J2']['x']-21,refs['J2']['y']-27)
    # A bottom service pinhole reaches the reset switch actuator without exposed shorting pads.
    reset_x,reset_y=refs['SW3']['x']-21,refs['SW3']['y']-27
    base=base.cut(cyl(1.2,PCB_Z,0,reset_x,reset_y))
    base=base.union(block(3,5,PCB_Z-3.31-.15-FLOOR,FLOOR,17,usb_y))
    base=base.union(block(.8,5,PCB_Z-.3-FLOOR,FLOOR,13.675,usb_y))
    parts = [('base',base,'#82bac6'),('lid-front',lid_front,'#d0e7ec'),('lid-rear',lid_rear,'#c5e1e7'),('battery-keeper',keeper,'#5893a4'),('PCB',pcb,'#2b755e'),('pack-envelope',pack,'#c8cbd0'),('OLED-module',module,'#203d59'),('OLED-glass',glass,'#101e24'),('OLED-header',header,'#303944'),('USB',usb,'#b7c0c8'),('MCU',mcu,'#333e4a'),('JST',jst,'#eee7cf')]
    # Use the reviewed production renderer for this sample count, at real pixel pitch.
    fw=ROOT/'firmware/q4-stm32'
    firmware_hashes={p.name:sha(p) for p in (fw/'oled.c',fw/'oled.h',fw/'counter.h')}
    with tempfile.TemporaryDirectory(prefix='count-fidget-q4-render-') as folder:
        src=Path(folder)/'pixels.c'; exe=Path(folder)/'pixels'
        src.write_text('#include <stdio.h>\n#include "oled.h"\nint main(void){for(int p=0;p<8;p++)for(int c=0;c<128;c++)putchar(oled_pixel_byte(12345678,p,c));}\n')
        subprocess.run(['cc','-std=c11','-O2','-I',str(fw),str(src),str(fw/'oled.c'),'-o',str(exe)],check=True)
        bitmap=subprocess.check_output([str(exe)])
    assert len(bitmap)==1024
    pixel_parts=[]
    px,py=21.74/128,10.86/64
    for page in range(8):
        for col in range(128):
            for bit in range(8):
                if bitmap[page*128+col] & (1<<bit):
                    pixel_parts.append(block(px*.9,py*.9,.015,module_z+1.2+1.4,
                        LCD_X-10.87+(col+.5)*px,LCD_Y-2.1-5.43+(page*8+bit+.5)*py).val())
    pixels=cq.Workplane('XY').newObject([cq.Compound.makeCompound(pixel_parts)])
    parts.append(('OLED-pixels',pixels,'#f5ffff'))
    parts += tails
    for i,pad in enumerate(refs['DS1']['pads']):
        x,y=pad['x']-21,pad['y']-27
        tails.append((f'OLED-host-joint-{i}',cyl(.9,1.0,PCB_Z-1,x,y),'#b7bcc0'))
        tails.append((f'OLED-module-joint-{i}',cyl(.75,1.0,module_z+1.2,x,y),'#b7bcc0'))
    parts += [v for v in tails if v[0].startswith('OLED-')]
    component_checks = [('PCB',pcb),('pack',pack),('OLED-max',max_glass),('OLED-module',module),('OLED-header',header),('OLED-underside-envelope',module_bottom),('USB',usb),('MCU',mcu),('JST',jst)] + [(n,s) for n,s,_ in tails]
    bottom = []
    for ref,p in refs.items():
        if p['side'] != 'bottom' or ref.startswith('TP') or ref in ('U1','J1','J2'): continue
        bx,by,bw,bd = p['bbox']
        h = 2.2 if ref=='SW3' else 2.0 if ref=='U8' else 1.1 if ref.startswith('R') or ('0603' in next((a['footprint'] for a in json.loads(MODEL.read_text())['parts'] if a['ref']==ref),'')) else 1.6
        s = block(bw,bd,h,PCB_Z-h,bx+bw/2-21,by+bd/2-27)
        bottom.append((ref,s)); parts.append((ref+'-envelope',s,'#414854'))
        component_checks.append((ref,s))
    for i,(x,y) in enumerate(KEYS,1):
        switch = block(13.95,13.95,5,PCB_Z+PCB_T,x,y).union(block(15.2,15.7,6.15,PCB_Z+PCB_T+5,x,y))
        cap = rounded(18.2,18.2,7,23.4,1.4,x,y).cut(block(15.8,15.8,6,23.3,x,y))
        parts += [(f'switch-{i}',switch,'#35404d'),(f'keycap-{i}',cap,'#62accb' if i==1 else '#e4b568')]
        component_checks += [(f'switch-{i}',switch),(f'keycap-{i}-pressed-envelope',block(18.2,18.2,7,19.4,x,y))]
    # Front header and compliant pads under the rear bare PCB edges support the module.
    # Physical sample must confirm component-free contact lands and adhesive compression.
    for i,x in enumerate((LCD_X-11.65,LCD_X+11.65)):
        support=cyl(1.9,2.5,PCB_Z+PCB_T,x,LCD_Y+11.9).cut(cyl(1.25,2.7,PCB_Z+PCB_T-.1,x,LCD_Y+11.9))
        parts.append((f'OLED-support-{i+1}',support,'#ead7bc'))
        component_checks.append((f'OLED-support-{i+1}',support))
    # Reservation volumes: not a manufactured harness or a selected USB cable.
    wire_side = block(2.0,10,7.5,4.0,-22.2,-.5)
    wire_exit = block(8,6,2.4,3.2,-11,3)
    wire_under = block(10,4,2.4,4,-17,1)
    plug_access = block(10,12,4.6,7.1,26.5,usb_y)
    reservations = [('wire-side-corridor',wire_side),('wire-tab-NTC-exit',wire_exit),('wire-under-PCB',wire_under),('USB-plug-access',plug_access)]
    # Fastener envelopes: four M2x12 (seat16.5->tip4.5), keeper M2x5 (tip2.6).
    screws=[]
    for i,(x,y) in enumerate(MOUNTS):
        seat=(FRONT_TOP if y<0 else TOP)-.6
        screws.append((f'board-screw-{i+1}',cyl(1,12,seat-12,x,y).union(cyl(2,1.7,seat,x,y))))
    for i,(x,y) in enumerate(KEEPER_SCREWS): screws.append((f'keeper-screw-{i+1}',cyl(1,5,KEEPER_Z+1.2-5,x,y).union(cyl(2,1.7,KEEPER_Z+1.2,x,y))))
    parts += [(n,s,'#929da6') for n,s in screws]
    results=[]
    for shell_name,shell in [('base',base),('lid',lid),('battery-keeper',keeper)]:
        for name,shape in component_checks+reservations:
            v=overlap(shell,shape)
            if v>1e-5: results.append(dict(a=shell_name,b=name,intersection_mm3=round(v,6)))
    for name,shape in bottom+[("USB",usb),("MCU",mcu),("JST",jst)]+[(n,s) for n,s,_ in tails]:
        for other,obj in [('pack',pack),('battery-keeper',keeper)]+screws:
            v=overlap(shape,obj)
            if v>1e-5: results.append(dict(a=name,b=other,intersection_mm3=round(v,6)))
    for name,shape in screws:
        for other,obj in [('pack',pack),('PCB',pcb)]+[(n,s) for n,s in component_checks if 'pressed-envelope' in n]:
            v=overlap(shape,obj)
            if v>1e-5: results.append(dict(a=name,b=other,intersection_mm3=round(v,6)))
    for name,shape in [(n,s) for n,s,_ in tails if n.startswith('USB-shell-joint')]:
        for other,obj in [(n,s) for n,s in component_checks if n.startswith('switch-')]:
            v=overlap(shape,obj)
            if v>1e-5: results.append(dict(a=name,b=other,intersection_mm3=round(v,6)))
    for name,shape in [(n,q) for n,q in component_checks if n.startswith('OLED-support')]:
        for other,obj in [('module-underside',module_bottom),('header',header)]:
            vv=overlap(shape,obj)
            if vv>1e-5:results.append(dict(a=name,b=other,intersection_mm3=round(vv,6)))
    for name,shape in [(n,q) for n,q,_ in tails if n.startswith(('OLED-host','SW'))]:
        for other,obj in bottom+[('USB',usb),('MCU',mcu),('JST',jst)]:
            vv=overlap(shape,obj)
            if vv>1e-5:results.append(dict(a=name,b=other,intersection_mm3=round(vv,6)))
    # Check the actual straight assembly paths with covers/fasteners removed.
    # PCB, pre-fitted key plate, keys and soldered module enter as one assembly.
    motion_count=0;motion_tests=0;motion_hits=[]
    stages=[('front-cover-vertical', [('lid-front',lid_front)],
             [('base',base),('rear-plate',lid_rear)]+component_checks),
            ('completed-board-vertical', [('rear-plate',lid_rear)]+component_checks,
             [('base',base),('pack',pack),('keeper',keeper)])]
    for stage,moving,obstacles in stages:
        # Pack belongs to the base and is not part of the moving board assembly.
        moving=[(n,s) for n,s in moving if n!='pack']
        for step in range(81):
            dz=step*.5;motion_count+=1
            for name,shape in moving:
                lifted=shape.translate((0,0,dz))
                for other,obj in obstacles:
                    motion_tests+=1
                    vv=overlap(lifted,obj)
                    if vv>1e-5:motion_hits.append(dict(stage=stage,dz_mm=dz,a=name,b=other,intersection_mm3=round(vv,6)))
    distances = {
        'pack_to_bottom_components': min(s.val().distance(pack.val()) for _,s in bottom+[("USB",usb),("MCU",mcu),("JST",jst)]),
        'pack_to_switch_tails': min(s.val().distance(pack.val()) for n,s,_ in tails if n.startswith('SW')),
        'keeper_to_bottom_components': min(s.val().distance(keeper.val()) for _,s in bottom+[("USB",usb),("MCU",mcu),("JST",jst)]),
        'keeper_screw_to_bottom_components': min(s.val().distance(q.val()) for _,s in bottom for n,q in screws if n.startswith('keeper')),
        'max_oled_to_mcu': max_glass.val().distance(mcu.val()),
        'max_oled_to_usb': max_glass.val().distance(usb.val()),
        'max_oled_to_jst': max_glass.val().distance(jst.val()),
        'pack_to_fasteners': min(s.val().distance(pack.val()) for _,s in screws),
        'pressed_keycap_to_rear_screw': min(s.val().distance(q.val()) for n,s in component_checks if 'pressed-envelope' in n for name,q in screws if name.startswith('board')),
    }
    assert sha(BOARD)==data['board_sha256'] and sha(MODEL)==data['model_sha256'], 'Source changed during build; regenerate'
    report=dict(status='Q4 engineering fit candidate; physical qualification pending',body_mm=[W,D,BEZEL_TOP],keycap_envelope_height_mm=30.4,pcb_bottom_z_mm=PCB_Z,
        pcb_mm=[42,54,1],mounts_board_xy_mm=[[refs[r]["x"],refs[r]["y"]] for r in ("H1","H2","H3","H4")],key_centers_board_xy_mm=[[11.475,40.8],[30.525,40.8]],
        battery_max_envelope_mm=[21,21,4.2],battery_bore_mm=21.8,battery_to_board_mm=PCB_Z-(BAT_Z+4.2),battery_to_keeper_mm=KEEPER_Z-(BAT_Z+4.2),
        oled_support_mm=2.5,oled_nominal_module_pcb_mm=[27.3,27.8,1.2],oled_nominal_glass_mm=[24.74,16.9,1.4],oled_checked_max_mm=[27.7,28.2,3.4],oled_aperture_mm=[23.2,12.4],oled_roof_z_mm=FRONT_TOP,oled_max_top_gap_mm=FRONT_SEAM-(module_z+3.2),key_plate_top_above_pcb_mm=5,key_plate_thickness_mm=1.5,key_plate_hole_mm=14.05,
        usb_opening_y_mm=refs["J1"]["y"],usb_opening_mm=[13.2,4.8],board_side_clearance_mm=[(W-2*WALL-42)/2,(D-2*WALL-54)/2],
        valid_solids={n:dict(valid=s.val().isValid(),count=len(s.solids().vals()),volume_mm3=round(volume(s),3)) for n,s in [('base',base),('lid-front',lid_front),('lid-rear',lid_rear),('battery-keeper',keeper)]},
        shell_intersections_mm3={'lid_front_rear':round(overlap(lid_front,lid_rear),8),'base_lid':round(overlap(base,lid),8),'base_keeper':round(overlap(base,keeper),8),'lid_keeper':round(overlap(lid,keeper),8)},
        reported_intersections=results,assembly_path_checks=dict(poses=motion_count,sampled_intersection_tests=motion_tests,step_mm=.5,max_lift_mm=40,collisions=motion_hits,limitations='Sampled straight vertical assembly/removal; excludes soldering, screw insertion, wire bending and print distortion.'),minimum_modeled_distances_mm={k:round(v,5) for k,v in distances.items()},source_board_sha256=data['board_sha256'],source_model_sha256=data['model_sha256'],generator_sha256=generator_hash,rendered_count=12345678,firmware_renderer_sha256=firmware_hashes,cadquery_version=cq.__version__,python_version=sys.version.split()[0],
        limitations=['Component bodies, pins and screws are simplified envelopes; no exact assembled vendor CAD claim.',
        'Native footprint bounding boxes conservatively bound bottom components; heights are stated family allowances.',
        'Four-wire corridor and tab/NTC reservations do not prove the finished 40±5mm harness bends or connector insertion.',
        'Keycaps are provisional envelopes, not approved Adafruit CAD; full travel and fit require a sample.',
        'Module drawing controls27.30x27.80mm geometry; summary26x26mm conflicts. Header centering is nominal; verify exact sample, clamp-free support lands, trimmedpins and±0.4mm lateral fit.',
        'Rear key plate must be fitted before soldering the four switch leads; the removable front cover exposes the separately soldered display header. The complete board is assembled into the base afterward. This is a home-through-hole completion design, not a drop-in cover for pre-soldered switches.',
        'Switch plate uses5mm top elevation and1.5mm thickness from the manufacturer diagram; print tolerance and snap engagement require fit testing.',
        'Screw thread strength, print tolerances, battery retention, USB strain and drop behavior remain untested.'])
    print(json.dumps({'shell_intersections':report['shell_intersections_mm3'],'collisions':results,'solids':report['valid_solids']},indent=2),flush=True)
    assert all(v['valid'] and v['count']==1 for v in report['valid_solids'].values()), 'Invalid enclosure solid'
    assert max(report['shell_intersections_mm3'].values())<1e-5, 'Enclosure parts intersect'
    assert not results, f'Resolve modeled intersections before exporting: {results}'
    assert not motion_hits, f'Resolve assembly-path intersections before exporting: {motion_hits[:8]}'
    # Internal collision math uses the PCB top-view Y-down convention. Export
    # and render in right-handed Z-up CAD coordinates so text/geometry are not mirrored.
    parts=[(name,shape.mirror('XZ'),color) for name,shape,color in parts]
    report['cad_coordinate_transform']='X = PCB_X - 21; Y = 27 - PCB_Y; Z above base floor'
    assembly=cq.Assembly(name='Count-Fidget-Q4-enclosure-candidate')
    for name,shape,color in parts: assembly.add(shape,name=name,color=cq.Color(color))
    assembly.export(str(OUT/'enclosure-Q4.step'))
    for name,shape in [('base',base),('battery-keeper',keeper.translate((0,0,-KEEPER_Z))),('lid-front',lid_front.rotate((0,0,0),(1,0,0),180).translate((0,0,BEZEL_TOP))),('lid-rear',lid_rear.rotate((0,0,0),(1,0,0),180).translate((0,0,TOP)))]:
        cq.exporters.export(shape.mirror('XZ'),str(OUT/f'{name}-Q4.stl'),tolerance=.04,angularTolerance=.1)
    stl_names=[f'{name}-Q4.stl' for name in ('base','battery-keeper','lid-front','lid-rear')]
    report['stl_mesh_checks']={name:mesh_check(OUT/name) for name in stl_names}
    (OUT/'fit-report.json').write_text(json.dumps(report,indent=2)+'\n')
    if not args.skip_render:
        render(OUT/'assembled-Q4.png',parts)
        render(OUT/'exploded-Q4.png',parts,exploded=True)
        render(OUT/'interior-Q4.png',parts,cutaway=True)
        bay = [p for p in parts if p[0] in ['base','pack-envelope','battery-keeper'] or p[0].startswith('keeper-screw')]
        render(OUT/'battery-bay-Q4.png',bay,cutaway=True,label='Battery bay / board removed')
    output_names=stl_names+['enclosure-Q4.step','board-geometry.json','fit-report.json']
    if not args.skip_render:
        output_names+=['assembled-Q4.png','exploded-Q4.png','interior-Q4.png','battery-bay-Q4.png']
    outputs={name:sha(OUT/name) for name in output_names}
    assert firmware_hashes=={p.name:sha(p) for p in (fw/'oled.c',fw/'oled.h',fw/'counter.h')}, 'Firmware renderer changed; regenerate'
    assert sha(Path(__file__))==generator_hash, 'Generator changed during build; regenerate'
    assert sha(BOARD)==data['board_sha256'] and sha(MODEL)==data['model_sha256'], 'Source changed during export; regenerate'
    (OUT/'build-manifest.json').write_text(json.dumps(dict(generator=report['generator_sha256'],board=report['source_board_sha256'],model=report['source_model_sha256'],outputs=outputs),indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
