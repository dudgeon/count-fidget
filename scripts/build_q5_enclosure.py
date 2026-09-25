#!/usr/bin/env python3
"""Generate the separate Q5 fit candidate; never writes historical or PCB files.

Q5 changes from Q4: the cell is in the vendor-soldered BT1 holder under the PCB
(no pack bay, keeper or harness corridor), the stack is 3.4 mm lower, side
clearance is 1.0 mm, the USB-C opening passes a USB-IF maximum overmold to the
receptacle face (issue #4), and two MX-stem keycaps are printed parts.

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
OUT = ROOT / 'mechanical/q5'
BOARD = ROOT / 'electronics/q5/click-counter-Q5.kicad_pcb'
MODEL = ROOT / 'electronics/q5/netlist-Q5.json'
W, D, WALL, FLOOR = 47.2, 59.2, 1.6, 1.6
SIDE_GAP = (W - 2 * WALL - 42) / 2
HOLDER_H = 5.52          # CR2032-BS-6-1 supplier model height
PCB_Z = FLOOR + HOLDER_H + 0.58  # 0.58 mm under the holder: printed floor flatness allowance
PCB_T = 1.
SEAM, TOP = PCB_Z + 4.5, PCB_Z + 6.0
FRONT_SEAM, FRONT_TOP, FRONT_STEP_Y = PCB_Z + 7.0, PCB_Z + 8.5, 4.5
BEZEL_TOP = FRONT_TOP
KEYCAP_Z = PCB_Z + 12.3          # unpressed MX keycap underside (Q4 geometry, lowered with the stack)
PRESSED_Z = PCB_Z + 8.3
LCD_X, LCD_Y = 0., -10.3
KEYS = [(-9.525, 13.8), (9.525, 13.8)]
MOUNTS = [(-18.5, 25.), (18.5, 25.)]
LOAD_SUPPORTS = [(5.5 - 21, 42.8 - 27), (34.0 - 21, 44.0 - 27)]   # board (5.5,42.8) and (34.0,44.0)


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
            dz = 28 if name.startswith('lid') else 38 if name.startswith('keycap') else 16 if name.startswith('switch') else 22 if name in ('OLED-glass','OLED-pixels','OLED-module','OLED-header') else 11 if name != 'base' else 0
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
    draw.text((40, 30), 'COUNT FIDGET  /  Q5', font=font, fill='#183e50')
    draw.text((40, 75), f'{view} · {W:g} x {D:g} x {BEZEL_TOP:g} mm body', font=small, fill='#456473')
    draw.text((40, 1004), 'Engineering fit candidate · component envelopes · physical qualification pending', font=small, fill='#456473')
    im.save(path)


def keycap(x, y, symbol):
    """Printable MX keycap: 18.2 mm square, 7 mm tall shell, cross socket, engraved legend."""
    cap = rounded(18.2, 18.2, 7, KEYCAP_Z, 1.4, x, y).cut(block(15.8, 15.8, 6, KEYCAP_Z - .1, x, y))
    boss = cyl(2.75, 4.2, KEYCAP_Z + 6 - 4.2, x, y)
    cross = block(4.15, 1.35, 3.9, KEYCAP_Z + 6 - 4.2 - .1, x, y).union(block(1.35, 4.15, 3.9, KEYCAP_Z + 6 - 4.2 - .1, x, y))
    cap = cap.union(boss).cut(cross)
    if symbol == '+':
        legend = block(8, 1.6, .5, KEYCAP_Z + 6.5, x, y).union(block(1.6, 8, .5, KEYCAP_Z + 6.5, x, y))
    else:
        legend = cyl(4.2, .5, KEYCAP_Z + 6.5, x, y).cut(cyl(2.8, .6, KEYCAP_Z + 6.45, x, y))
    return cap.cut(legend)


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
    usb_axis = PCB_Z - 3.31/2          # receptacle on the bottom side: body PCB_Z-3.31..PCB_Z
    mouth_x = 21.575                   # footprint PCB-edge line +3.675 mm from J1 origin
    (OUT/'board-geometry.json').write_text(json.dumps(data, indent=2)+'\n')
    base = rounded(W,D,FRONT_SEAM,r=3).cut(rounded(W-2*WALL,D-2*WALL,FRONT_SEAM,FLOOR,r=1.4))
    base = base.cut(block(70,80,20,SEAM,0,FRONT_STEP_Y+40))
    for x,y in MOUNTS:
        # Pilot extends into the floor (never through it) so all four screws are M2x12.
        base = base.union(cyl(2.6,PCB_Z-FLOOR,FLOOR,x,y)).cut(cyl(.85,PCB_Z-.8,.8,x,y))
    for x,y in LOAD_SUPPORTS:
        base = base.union(cyl(1.3,PCB_Z-FLOOR,FLOOR,x,y))
    # Issue #4: pass a USB-IF maximum 12.35 x 6.5 mm overmold to the receptacle face.
    usb_cut = block(12,13.4,7.2,usb_axis-3.6,W/2,usb_y)
    base = base.cut(usb_cut)
    full_lid = rounded(W,D,TOP-SEAM,SEAM,r=3)
    lid = full_lid.cut(block(70,80,20,SEAM-1,0,FRONT_STEP_Y-40))
    front_lid = rounded(W,D,FRONT_TOP-FRONT_SEAM,FRONT_SEAM,r=3)
    front_lid = front_lid.intersect(block(70,80,20,FRONT_SEAM-1,0,FRONT_STEP_Y-40))
    bridge = block(W-2*WALL-.2,.8,FRONT_TOP-(PCB_Z+5.3),PCB_Z+5.3,0,FRONT_STEP_Y-.5)
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
    lid_front = lid.intersect(block(80,80,40,0,0,FRONT_STEP_Y-.10-40))
    lid_rear = lid.intersect(block(80,80,40,0,0,FRONT_STEP_Y+.10+40))
    lid=lid_front.union(lid_rear)
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
            if ref.startswith('SW') and ref != 'SW3':
                tails.append((ref+'-post-'+str(len(tails)),cyl(max(dx/2-.1,.25),2.3,PCB_Z-2.3,x,y),'#c4ad73'))
    # BT1 holder and cell: supplier model 31.3 x 16.0 x 5.52 mm; 20 mm cell overhangs the body.
    bx,by = refs['BT1']['x']-21, refs['BT1']['y']-27
    holder = block(22.3,16.2,HOLDER_H,PCB_Z-HOLDER_H,bx,by).union(block(31.4,7.0,2.2,PCB_Z-2.2,bx,by)).union(cyl(10.15,HOLDER_H,PCB_Z-HOLDER_H,bx,by))   # 20.3 mm: LIR2032 20.0 mm nominal plus tolerance
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
    usb = block(7.35,8.94,3.31,PCB_Z-3.31,17.9,usb_y)
    mcu = block(9.4,9.4,1.6,PCB_Z-1.6,refs['U1']['x']-21,refs['U1']['y']-27)
    # A bottom service pinhole reaches the reset switch actuator without exposed shorting pads.
    reset_x,reset_y=refs['SW3']['x']-21,refs['SW3']['y']-27
    base=base.cut(cyl(1.2,PCB_Z,0,reset_x,reset_y))
    base=base.union(block(3,5,PCB_Z-3.31-.15-FLOOR,FLOOR,17,usb_y))
    base=base.union(block(.8,5,PCB_Z-.3-FLOOR,FLOOR,13.675,usb_y))
    parts = [('base',base,'#82bac6'),('lid-front',lid_front,'#d0e7ec'),('lid-rear',lid_rear,'#c5e1e7'),('PCB',pcb,'#2b755e'),('holder-envelope',holder,'#c8cbd0'),('OLED-module',module,'#203d59'),('OLED-glass',glass,'#101e24'),('OLED-header',header,'#303944'),('USB',usb,'#b7c0c8'),('MCU',mcu,'#333e4a')]
    # Use the reviewed production renderer for this sample count, at real pixel pitch.
    fw=ROOT/'firmware/q5-stm32'
    firmware_hashes={p.name:sha(p) for p in (fw/'oled.c',fw/'oled.h',fw/'counter.h')}
    with tempfile.TemporaryDirectory(prefix='count-fidget-q5-render-') as folder:
        src=Path(folder)/'pixels.c'; exe=Path(folder)/'pixels'
        src.write_text('#include <stdio.h>\n#include "oled.h"\nint main(void){OledView v={12345678,OLED_LABEL_NONE,3,false};for(int p=0;p<8;p++)for(int c=0;c<128;c++)putchar(oled_frame_byte(&v,p,c));}\n')
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
    component_checks = [('PCB',pcb),('holder',holder),('OLED-max',max_glass),('OLED-module',module),('OLED-header',header),('OLED-underside-envelope',module_bottom),('USB',usb),('MCU',mcu)] + [(n,s) for n,s,_ in tails]
    model_parts={a['ref']:a for a in json.loads(MODEL.read_text())['parts']}
    bottom = []
    for ref,p in refs.items():
        if p['side'] != 'bottom' or ref.startswith('TP') or ref in ('U1','J1','BT1'): continue
        bx0,by0,bw,bd = p['bbox']
        fp=model_parts[ref]['footprint']
        h = 2.2 if ref=='SW3' else 2.0 if ref=='U8' else 1.1 if ('0603' in fp or '0805' in fp or 'SOD-323' in fp) else 1.6
        s = block(bw,bd,h,PCB_Z-h,bx0+bw/2-21,by0+bd/2-27)
        bottom.append((ref,s)); parts.append((ref+'-envelope',s,'#414854'))
        component_checks.append((ref,s))
    caps=[]
    for i,(x,y) in enumerate(KEYS,1):
        switch = block(13.95,13.95,5,PCB_Z+PCB_T,x,y).union(block(15.2,15.7,6.15,PCB_Z+PCB_T+5,x,y))
        cap = keycap(x,y,'+' if i==1 else 'o')
        caps.append(cap)
        parts += [(f'switch-{i}',switch,'#35404d'),(f'keycap-{i}',cap,'#62accb' if i==1 else '#e4b568')]
        component_checks += [(f'switch-{i}',switch),(f'keycap-{i}-pressed-envelope',block(18.2,18.2,7,PRESSED_Z,x,y))]
    for i,x in enumerate((LCD_X-11.65,LCD_X+11.65)):
        support=cyl(1.9,2.5,PCB_Z+PCB_T,x,LCD_Y+11.9).cut(cyl(1.25,2.7,PCB_Z+PCB_T-.1,x,LCD_Y+11.9))
        parts.append((f'OLED-support-{i+1}',support,'#ead7bc'))
        component_checks.append((f'OLED-support-{i+1}',support))
    # Reservation volume: USB-IF maximum overmold envelope seated at the receptacle face.
    plug_access = block(10,12.55,6.7,usb_axis-3.35,mouth_x+5.0,usb_y)
    reservations = [('USB-plug-access',plug_access)]
    screws=[]
    for i,(x,y) in enumerate(MOUNTS):
        seat=(FRONT_TOP if y<0 else TOP)-.6
        screws.append((f'board-screw-{i+1}',cyl(1,12,seat-12,x,y).union(cyl(2,1.7,seat,x,y))))
    parts += [(n,s,'#929da6') for n,s in screws]
    results=[]
    for shell_name,shell in [('base',base),('lid',lid)]+[(f'keycap-{i+1}',c) for i,c in enumerate(caps)]:
        for name,shape in component_checks+reservations:
            if shell_name.startswith('keycap') and ('pressed-envelope' in name or name.startswith('switch')): continue
            v=overlap(shell,shape)
            if v>1e-5: results.append(dict(a=shell_name,b=name,intersection_mm3=round(v,6)))
    for name,shape in bottom+[("USB",usb),("MCU",mcu),('holder',holder)]+[(n,s) for n,s,_ in tails]:
        for other,obj in screws:
            v=overlap(shape,obj)
            if v>1e-5: results.append(dict(a=name,b=other,intersection_mm3=round(v,6)))
    for name,shape in bottom+[("USB",usb),("MCU",mcu)]:
        v=overlap(shape,holder)
        if v>1e-5: results.append(dict(a=name,b='holder',intersection_mm3=round(v,6)))
    for name,shape in screws:
        for other,obj in [('PCB',pcb)]+[(n,s) for n,s in component_checks if 'pressed-envelope' in n]:
            v=overlap(shape,obj)
            if v>1e-5: results.append(dict(a=name,b=other,intersection_mm3=round(v,6)))
        # Thread-forming screws cut into the boss wall by design; the tip must stay inside the pilot depth.
        tip=shape.val().BoundingBox().zmin
        if tip<.8-1e-6: results.append(dict(a=name,b='pilot-bottom-0.8mm',intersection_mm3=round(.8-tip,6)))
    for name,shape in [(n,s) for n,s,_ in tails if n.startswith('USB-shell-joint')]:
        for other,obj in [(n,s) for n,s in component_checks if n.startswith('switch-')]:
            v=overlap(shape,obj)
            if v>1e-5: results.append(dict(a=name,b=other,intersection_mm3=round(v,6)))
    for name,shape in [(n,q) for n,q in component_checks if n.startswith('OLED-support')]:
        for other,obj in [('module-underside',module_bottom),('header',header)]:
            vv=overlap(shape,obj)
            if vv>1e-5:results.append(dict(a=name,b=other,intersection_mm3=round(vv,6)))
    for name,shape in [(n,q) for n,q,_ in tails if n.startswith(('OLED-host','SW'))]:
        for other,obj in bottom+[('USB',usb),('MCU',mcu),('holder',holder)]:
            vv=overlap(shape,obj)
            if vv>1e-5:results.append(dict(a=name,b=other,intersection_mm3=round(vv,6)))
    # Straight assembly paths with covers/fasteners removed: the soldered PCB,
    # pre-fitted key plate, keys, module and inserted cell enter as one assembly.
    motion_count=0;motion_tests=0;motion_hits=[]
    stages=[('front-cover-vertical', [('lid-front',lid_front)],
             [('base',base),('rear-plate',lid_rear)]+component_checks),
            ('completed-board-vertical', [('rear-plate',lid_rear)]+component_checks,
             [('base',base)])]
    for stage,moving,obstacles in stages:
        moving=[(n,s) for n,s in moving if 'pressed-envelope' not in n]
        for step in range(81):
            dz=step*.5;motion_count+=1
            for name,shape in moving:
                lifted=shape.translate((0,0,dz))
                for other,obj in obstacles:
                    motion_tests+=1
                    vv=overlap(lifted,obj)
                    if vv>1e-5:motion_hits.append(dict(stage=stage,dz_mm=dz,a=name,b=other,intersection_mm3=round(vv,6)))
    floor_top=block(W-2*WALL,D-2*WALL,.01,FLOOR-.01)
    distances = {
        'holder_to_floor': holder.val().distance(floor_top.val()),
        'holder_to_bottom_components': min(s.val().distance(holder.val()) for _,s in bottom+[("USB",usb),("MCU",mcu)]),
        'holder_to_switch_tails': min(s.val().distance(holder.val()) for n,s,_ in tails if n.startswith('SW')),
        'max_oled_to_mcu': max_glass.val().distance(mcu.val()),
        'max_oled_to_usb': max_glass.val().distance(usb.val()),
        'pressed_keycap_to_rear_screw': min(s.val().distance(q.val()) for n,s in component_checks if 'pressed-envelope' in n for name,q in screws if name.startswith('board')),
        'usb_mouth_to_outer_wall': W/2-mouth_x,
    }
    assert sha(BOARD)==data['board_sha256'] and sha(MODEL)==data['model_sha256'], 'Source changed during build; regenerate'
    printed=[('base',base),('lid-front',lid_front),('lid-rear',lid_rear),('keycap-count',caps[0]),('keycap-reset',caps[1])]
    report=dict(status='Q5 engineering fit candidate; physical qualification pending',body_mm=[W,D,BEZEL_TOP],keycap_envelope_height_mm=round(KEYCAP_Z+7,3),pcb_bottom_z_mm=PCB_Z,
        pcb_mm=[42,54,1],mounts_board_xy_mm=[[refs[r]["x"],refs[r]["y"]] for r in ("H1","H2","H3","H4")],key_centers_board_xy_mm=[[11.475,40.8],[30.525,40.8]],
        load_supports_board_xy_mm=[[x+21,y+27] for x,y in LOAD_SUPPORTS],board_side_clearance_mm=round(SIDE_GAP,3),
        cell='User-supplied LIR2032 in the vendor-soldered BT1 holder; no pack, keeper or harness',holder_envelope_mm=[31.4,20.3,HOLDER_H],
        oled_support_mm=2.5,oled_nominal_module_pcb_mm=[27.3,27.8,1.2],oled_nominal_glass_mm=[24.74,16.9,1.4],oled_checked_max_mm=[27.7,28.2,3.4],oled_aperture_mm=[23.2,12.4],oled_roof_z_mm=FRONT_TOP,oled_max_top_gap_mm=round(FRONT_SEAM-(module_z+3.2),3),key_plate_top_above_pcb_mm=5,key_plate_thickness_mm=1.5,key_plate_hole_mm=14.05,
        usb_opening_y_mm=refs["J1"]["y"],usb_opening_mm=[13.4,7.2],usb_axis_z_mm=round(usb_axis,3),usb_plug_reservation_mm=[12.55,6.7],
        fasteners='Four M2 x 12 board/cover screws; pilots stop 0.8 mm above the outer floor',
        valid_solids={n:dict(valid=s.val().isValid(),count=len(s.solids().vals()),volume_mm3=round(volume(s),3)) for n,s in printed},
        shell_intersections_mm3={'lid_front_rear':round(overlap(lid_front,lid_rear),8),'base_lid':round(overlap(base,lid),8)},
        reported_intersections=results,assembly_path_checks=dict(poses=motion_count,sampled_intersection_tests=motion_tests,step_mm=.5,max_lift_mm=40,collisions=motion_hits,limitations='Sampled straight vertical assembly/removal; excludes soldering, screw insertion, cell insertion and print distortion.'),minimum_modeled_distances_mm={k:round(v,5) for k,v in distances.items()},source_board_sha256=data['board_sha256'],source_model_sha256=data['model_sha256'],generator_sha256=generator_hash,rendered_count=12345678,firmware_renderer_sha256=firmware_hashes,cadquery_version=cq.__version__,python_version=sys.version.split()[0],
        limitations=['Component bodies, pins and screws are simplified envelopes; no exact assembled vendor CAD claim.',
        'Native footprint bounding boxes conservatively bound bottom components; heights are stated family allowances.',
        'BT1 envelope uses the supplier 3D model extents plus the full 20 mm cell cylinder at holder height; cell retention and insertion force are untested.',
        'Printed MX keycaps: cross-socket fit, travel and legend durability require a print sample.',
        'Module drawing controls27.30x27.80mm geometry; summary26x26mm conflicts. Header centering is nominal; verify exact sample, clamp-free support lands, trimmedpins and+/-0.4mm lateral fit.',
        'Rear key plate must be fitted before soldering the four switch leads; the removable front cover exposes the separately soldered display header.',
        'USB opening is checked against a USB-IF maximum overmold envelope only; real cable fit in both orientations is a first-article check.',
        'Screw thread strength, print tolerances, 1.0 mm side clearance, USB strain and drop behavior remain untested.'])
    print(json.dumps({'shell_intersections':report['shell_intersections_mm3'],'collisions':results,'motion_hits':motion_hits[:6],'solids':report['valid_solids'],'distances':report['minimum_modeled_distances_mm']},indent=2),flush=True)
    assert all(v['valid'] and v['count']==1 for v in report['valid_solids'].values()), 'Invalid enclosure solid'
    assert max(report['shell_intersections_mm3'].values())<1e-5, 'Enclosure parts intersect'
    assert not results, f'Resolve modeled intersections before exporting: {results}'
    assert not motion_hits, f'Resolve assembly-path intersections before exporting: {motion_hits[:8]}'
    assert distances['holder_to_floor']>=.5, 'Holder too close to the floor'
    # Internal collision math uses the PCB top-view Y-down convention. Export
    # and render in right-handed Z-up CAD coordinates so text/geometry are not mirrored.
    parts=[(name,shape.mirror('XZ'),color) for name,shape,color in parts]
    report['cad_coordinate_transform']='X = PCB_X - 21; Y = 27 - PCB_Y; Z above base floor'
    assembly=cq.Assembly(name='Count-Fidget-Q5-enclosure-candidate')
    for name,shape,color in parts: assembly.add(shape,name=name,color=cq.Color(color))
    assembly.export(str(OUT/'enclosure-Q5.step'))
    flipped_cap=lambda c,x,y: c.translate((-x,-y,0)).rotate((0,0,0),(1,0,0),180).translate((0,0,KEYCAP_Z+7))
    exports=[('base',base),('lid-front',lid_front.rotate((0,0,0),(1,0,0),180).translate((0,0,BEZEL_TOP))),('lid-rear',lid_rear.rotate((0,0,0),(1,0,0),180).translate((0,0,TOP))),
             ('keycap-count',flipped_cap(caps[0],*KEYS[0])),('keycap-reset',flipped_cap(caps[1],*KEYS[1]))]
    for name,shape in exports:
        cq.exporters.export(shape.mirror('XZ'),str(OUT/f'{name}-Q5.stl'),tolerance=.04,angularTolerance=.1)
    stl_names=[f'{name}-Q5.stl' for name,_ in exports]
    report['stl_mesh_checks']={name:mesh_check(OUT/name) for name in stl_names}
    (OUT/'fit-report.json').write_text(json.dumps(report,indent=2)+'\n')
    if not args.skip_render:
        render(OUT/'assembled-Q5.png',parts)
        render(OUT/'exploded-Q5.png',parts,exploded=True)
        render(OUT/'interior-Q5.png',parts,cutaway=True)
    output_names=stl_names+['enclosure-Q5.step','board-geometry.json','fit-report.json']
    if not args.skip_render:
        output_names+=['assembled-Q5.png','exploded-Q5.png','interior-Q5.png']
    outputs={name:sha(OUT/name) for name in output_names}
    assert firmware_hashes=={p.name:sha(p) for p in (fw/'oled.c',fw/'oled.h',fw/'counter.h')}, 'Firmware renderer changed; regenerate'
    assert sha(Path(__file__))==generator_hash, 'Generator changed during build; regenerate'
    assert sha(BOARD)==data['board_sha256'] and sha(MODEL)==data['model_sha256'], 'Source changed during export; regenerate'
    (OUT/'build-manifest.json').write_text(json.dumps(dict(generator=report['generator_sha256'],board=report['source_board_sha256'],model=report['source_model_sha256'],outputs=outputs),indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
