#!/usr/bin/env python3
"""Generate the separate Q5 fit candidate; never writes historical or PCB files.

Q5 changes from Q4: the cell is in the vendor-soldered BT1 holder under the PCB
(no pack bay, keeper or harness corridor), side clearance is 1.0 mm, the USB-C
opening passes a USB-IF maximum overmold to the receptacle face (issue #4), and
two MX-stem keycaps are printed parts. Design lock (independent review): 1.6 mm
PCB with MX hot-swap sockets (switches clip into the rear key plate and press
in), LCSC-stocked M2x6 self-tapping screws seated low in the lid bosses,
keycap datum from the switch drawing, USB rib clear of J1's joints, a reset
pinhole guide tube and a debossed cell warning.

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
PCB_T = 1.6                      # hot-swap sockets need the MX pin length of a 1.6 mm board
PCB_TOP = PCB_Z + PCB_T
SEAM, TOP = PCB_TOP + 3.5, PCB_TOP + 5.0          # MX plate: top 5.0 mm above the PCB, 1.5 mm thick
FRONT_SEAM, FRONT_TOP, FRONT_STEP_Y = PCB_TOP + 6.0, PCB_TOP + 7.5, 3.8
BEZEL_TOP = FRONT_TOP
WALL_RELIEF = 0.2                # base wall tops sit below the lids: the bosses set the stack
# CPG151101D13 drawing: housing top 11.0 +/-0.15 above the PCB, stem top 4.0 above that,
# cross 3.6 mm tall (4.00 x 1.30 horizontal arm, 4.00 x 1.10 vertical arm), travel 4.0 +/-0.4.
STEM_TOP = PCB_TOP + 15.0
HOUSING_TOP = PCB_TOP + 11.15
TRAVEL = 4.4
SOCKET_DEPTH = 3.5               # < 3.6 mm cross: the cap rests on the cross top, not the shoulder
KEYCAP_Z = PCB_TOP + 10.0        # unpressed skirt bottom
KEYCAP_ROOF = STEM_TOP + 1.2     # cavity roof: 0.65 mm above the housing at worst-case travel
KEYCAP_H = KEYCAP_ROOF + 1.2 - KEYCAP_Z
PRESSED_Z = KEYCAP_Z - TRAVEL
LCD_X, LCD_Y = 0., -10.3
KEYS = [(-9.525, 13.8), (9.525, 13.8)]
KEY_ROT = [90, 270]              # hot-swap sockets turned outward; switch/cross rotate with them
MOUNTS = [(-18.5, 25.), (18.5, 25.)]
LOAD_SUPPORTS = [(15.5 - 21, 44.0 - 27), (26.5 - 21, 44.0 - 27)]   # board (15.5,44.0) and (26.5,44.0)
# LCSC C357360 PA2X6nie: M2 x 6 cross pan-head self-tapping screw (in stock); head ~3.8 x 1.6 mm.
SCREW_LEN, SCREW_HEAD_R, SCREW_HEAD_H = 6.0, 1.9, 1.6
BOSS_FLOOR = 1.0                 # lid boss floor clamped on the PCB top; head seats on it
BORE_R, LID_BOSS_R, PILOT_R, PILOT_DEPTH, BASE_BOSS_R = 2.3, 3.2, 0.85, 4.2, 2.2


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
    assert abs(data['thickness'] - PCB_T) < 1e-6
    assert all(abs(a-b)<1e-5 for a,b in zip(data['edges'],[0,0,42,54])), data['edges']
    assert all(by_ref[n]['side']=='top' for n in ('H1','H2','H3','H4'))
    assert by_ref['DS1']['x'] == 21 and by_ref['DS1']['side']=='top'
    assert len(by_ref['DS1']['pads']) == 7
    for ref, (x, y), rot in zip(['SW1', 'SW2'], KEYS, KEY_ROT):
        central = [p for p in by_ref[ref]['pads'] if abs(p['drill'][0] - 4.0) < .001]
        assert len(central) == 1 and abs(central[0]['x'] - 21 - x) < 1e-6 and abs(central[0]['y'] - 27 - y) < 1e-6
        assert by_ref[ref]['side'] == 'bottom' and abs(by_ref[ref]['angle'] % 360 - rot) < 1e-6, ref
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


def keycap(x, y, symbol, rot=0):
    """Printable MX keycap from the switch drawing: 18.2 mm square, 16.3 mm cavity,
    5.5 mm boss, 3.5 mm cross socket sized per arm (1.32 / 1.12 mm) and rotated
    with the switch, engraved legend."""
    top = KEYCAP_Z + KEYCAP_H
    cap = rounded(18.2, 18.2, KEYCAP_H, KEYCAP_Z, 1.4, x, y).cut(block(16.3, 16.3, KEYCAP_ROOF - KEYCAP_Z + .1, KEYCAP_Z - .1, x, y))
    boss_z = STEM_TOP - SOCKET_DEPTH
    boss = cyl(2.75, KEYCAP_ROOF - boss_z + .05, boss_z, x, y)
    wide, narrow = (4.05, 1.32), (1.12, 4.05)          # switch frame: horizontal arm 1.30, vertical arm 1.10
    if rot % 180:
        wide, narrow = (1.32, 4.05), (4.05, 1.12)
    cross = block(*wide, SOCKET_DEPTH + .1, boss_z - .1, x, y).union(block(*narrow, SOCKET_DEPTH + .1, boss_z - .1, x, y))
    cap = cap.union(boss).cut(cross)
    if symbol == '+':
        legend = block(8, 1.6, .5, top - .5, x, y).union(block(1.6, 8, .5, top - .5, x, y))
    else:
        legend = cyl(4.2, .5, top - .5, x, y).cut(cyl(2.8, .6, top - .55, x, y))
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
    base = rounded(W,D,FRONT_SEAM-WALL_RELIEF,r=3).cut(rounded(W-2*WALL,D-2*WALL,FRONT_SEAM,FLOOR,r=1.4))
    base = base.cut(block(70,80,20,SEAM-WALL_RELIEF,0,FRONT_STEP_Y+40))
    for x,y in MOUNTS:
        # Boss top carries the PCB; a 1.7 mm pilot takes the M2x6 self-tapping thread.
        base = base.union(cyl(BASE_BOSS_R,PCB_Z-FLOOR,FLOOR,x,y)).cut(cyl(PILOT_R,PILOT_DEPTH+.01,PCB_Z-PILOT_DEPTH,x,y))
    for x,y in LOAD_SUPPORTS:
        base = base.union(cyl(1.3,PCB_Z-FLOOR,FLOOR,x,y))
    # Issue #4: pass a USB-IF maximum 12.35 x 6.5 mm overmold to the receptacle face.
    usb_cut = block(12,13.4,7.2,usb_axis-3.6,W/2,usb_y)
    base = base.cut(usb_cut)
    full_lid = rounded(W,D,TOP-SEAM,SEAM,r=3)
    lid = full_lid.cut(block(70,80,20,SEAM-1,0,FRONT_STEP_Y-40))
    front_lid = rounded(W,D,FRONT_TOP-FRONT_SEAM,FRONT_SEAM,r=3)
    front_lid = front_lid.intersect(block(70,80,20,FRONT_SEAM-1,0,FRONT_STEP_Y-40))
    bridge = block(W-2*WALL-.2,.8,FRONT_TOP-(PCB_TOP+4.3),PCB_TOP+4.3,0,FRONT_STEP_Y-.5)
    lid = lid.union(front_lid).union(bridge)
    for x,y in KEYS:
        lid = lid.cut(block(14.05,14.05,8,SEAM-1,x,y))
    # Viewing opening is centered on active pixels, not the asymmetric glass outline;
    # 0.4 mm wider than Q4 for the module's +/-0.4 mm lateral tolerance.
    lid = lid.cut(block(23.6,12.8,12,PCB_TOP,LCD_X,LCD_Y-2.1))
    for x,y in MOUNTS:
        mount_seam,mount_top=(FRONT_SEAM,FRONT_TOP) if y<0 else (SEAM,TOP)
        # Boss clamps the PCB top; the screw head seats on its 1.0 mm floor, reached through a 4.6 mm bore.
        # Clip the boss to the base cavity (0.15 mm clear of the inner wall) so the lid still drops in.
        boss = cyl(LID_BOSS_R,mount_top-PCB_TOP,PCB_TOP,x,y).intersect(block(W-2*WALL-.3,D-2*WALL-.3,mount_top-PCB_TOP,PCB_TOP))
        lid = lid.union(boss)
        lid = lid.cut(cyl(1.2,BOSS_FLOOR+.2,PCB_TOP-.1,x,y))
        lid = lid.cut(cyl(BORE_R,mount_top-(PCB_TOP+BOSS_FLOOR)+1,PCB_TOP+BOSS_FLOOR,x,y))
    lid = lid.cut(usb_cut)
    # The switches clip into the rear plate; plate and switches then press into the hot-swap sockets.
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
                # MX switch pins (3.30 mm) and centre post (3.00 mm) below the housing, through the 1.6 mm board.
                if dx > 3.5: tails.append((ref+'-post-'+str(len(tails)),cyl(1.925,1.4,PCB_Z-1.4,x,y),'#c4ad73'))
                else: tails.append((ref+'-pin-'+str(len(tails)),cyl(.75,1.7,PCB_Z-1.7,x,y),'#c4ad73'))
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
    # Guide tube from the floor to 0.8 mm below the tact switch body centres a 0.8-1.0 mm pin.
    tube_top=PCB_Z-2.2-.8
    base=base.union(cyl(1.65,tube_top-FLOOR,FLOOR,reset_x,reset_y)).cut(cyl(.65,tube_top+.1,-.05,reset_x,reset_y))
    base=base.union(block(3,5,PCB_Z-3.31-.15-FLOOR,FLOOR,17,usb_y))
    # Axial USB backstop bears on the receptacle shell only: top 1.0 mm below the PCB, clear of J1's rear joints.
    base=base.union(block(.8,5,PCB_Z-1.0-FLOOR,FLOOR,13.675,usb_y))
    # Cell warning debossed 0.4 mm into the outside of the base floor (mirrored so it reads from below).
    try:
        warn=(cq.Workplane('XY').text('LIR2032 ONLY - rechargeable - never CR2032',2.2,.45,kind='bold',halign='center',valign='center')
              .mirror('YZ').translate((0,-D/2+9,-.05)))
        base=base.cut(warn)
    except Exception as exc:  # text needs a system font; geometry checks do not depend on it
        print('warning text skipped:',exc)
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
    sockets = {}
    for ref,p in refs.items():
        if p['side'] != 'bottom' or ref.startswith('TP') or ref in ('U1','J1','BT1'): continue
        bx0,by0,bw,bd = p['bbox']
        fp=model_parts[ref]['footprint']
        if ref in ('SW1','SW2'):
            # Hot-swap socket body 14.5 x 5.9 x 1.85 mm (maker drawing), offset from the key centre.
            pads=[q for q in p['pads'] if q['number'] in ('1','2')]
            cx=sum(q['x'] for q in pads)/2-21; cy=sum(q['y'] for q in pads)/2-27
            ang=math.degrees(math.atan2(pads[1]['y']-pads[0]['y'],pads[1]['x']-pads[0]['x']))
            s = block(15.5,5.9,1.85,PCB_Z-1.85,0,0).rotate((0,0,0),(0,0,1),ang).translate((cx,cy,0))
            sockets[ref]=s
            bottom.append((ref,s)); parts.append((ref+'-socket-envelope',s,'#6a5acd'))
            continue
        h = 2.2 if ref=='SW3' else 2.0 if ref=='U8' else 1.1 if ('0603' in fp or '0805' in fp or 'SOD-323' in fp) else 1.6
        s = block(bw,bd,h,PCB_Z-h,bx0+bw/2-21,by0+bd/2-27)
        bottom.append((ref,s)); parts.append((ref+'-envelope',s,'#414854'))
        component_checks.append((ref,s))
    caps=[]
    for i,((x,y),rot) in enumerate(zip(KEYS,KEY_ROT),1):
        # Bottom housing 13.95 below the plate top; top housing 15.6 up to 11.15 mm (drawing max).
        switch = block(13.95,13.95,5,PCB_TOP,x,y).union(block(15.6,15.6,HOUSING_TOP-(PCB_TOP+5),PCB_TOP+5,x,y))
        cap = keycap(x,y,'+' if i==1 else 'o',rot)
        caps.append(cap)
        parts += [(f'switch-{i}',switch,'#35404d'),(f'keycap-{i}',cap,'#62accb' if i==1 else '#e4b568')]
        component_checks += [(f'switch-{i}',switch),(f'keycap-{i}-pressed-envelope',rounded(18.2+1.2,18.2+1.2,KEYCAP_H,PRESSED_Z,1.4,x,y))]
    for i,x in enumerate((LCD_X-11.65,LCD_X+11.65)):
        support=cyl(1.9,2.5,PCB_TOP,x,LCD_Y+11.9).cut(cyl(1.25,2.7,PCB_TOP-.1,x,LCD_Y+11.9))
        parts.append((f'OLED-support-{i+1}',support,'#ead7bc'))
        component_checks.append((f'OLED-support-{i+1}',support))
    # Reservation volume: USB-IF maximum overmold envelope seated at the receptacle face.
    plug_access = block(10,12.55,6.7,usb_axis-3.35,mouth_x+5.0,usb_y)
    reservations = [('USB-plug-access',plug_access)]
    screws=[]
    for i,(x,y) in enumerate(MOUNTS):
        seat=PCB_TOP+BOSS_FLOOR
        screws.append((f'board-screw-{i+1}',cyl(1,SCREW_LEN,seat-SCREW_LEN,x,y).union(cyl(SCREW_HEAD_R,SCREW_HEAD_H,seat,x,y))))
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
        # Self-tapping screws cut into the boss wall by design; the tip must stay inside the pilot depth.
        tip=shape.val().BoundingBox().zmin
        if tip<PCB_Z-PILOT_DEPTH-1e-6: results.append(dict(a=name,b='pilot-bottom',intersection_mm3=round(PCB_Z-PILOT_DEPTH-tip,6)))
        engagement=PCB_Z-tip
        if engagement<3.0: results.append(dict(a=name,b='thread-engagement<3mm',intersection_mm3=round(3.0-engagement,6)))
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
            if name.startswith((other+'-pin',other+'-post')): continue   # pins enter the socket; the post passes its centre cut-out
            vv=overlap(shape,obj)
            if vv>1e-5:results.append(dict(a=name,b=other,intersection_mm3=round(vv,6)))
    # Straight assembly paths with covers/fasteners removed: the assembled PCB,
    # key plate with switches, module and inserted cell enter as one assembly.
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
        'socket_to_floor': min(s.val().distance(floor_top.val()) for s in sockets.values()),
        'pressed_keycap_to_plate_top': PRESSED_Z-TOP,
        'pressed_keycap_roof_to_housing': KEYCAP_ROOF-TRAVEL-HOUSING_TOP,
        'keycap_to_front_step_plan': min(abs((y-9.1)-FRONT_STEP_Y) for x,y in KEYS),
        'screw_thread_engagement': min(PCB_Z-s.val().BoundingBox().zmin for _,s in screws),
        'max_oled_to_mcu': max_glass.val().distance(mcu.val()),
        'max_oled_to_usb': max_glass.val().distance(usb.val()),
        'pressed_keycap_to_rear_screw': min(s.val().distance(q.val()) for n,s in component_checks if 'pressed-envelope' in n for name,q in screws if name.startswith('board')),
        'usb_mouth_to_outer_wall': W/2-mouth_x,
    }
    assert sha(BOARD)==data['board_sha256'] and sha(MODEL)==data['model_sha256'], 'Source changed during build; regenerate'
    printed=[('base',base),('lid-front',lid_front),('lid-rear',lid_rear),('keycap-count',caps[0]),('keycap-reset',caps[1])]
    report=dict(status='Q5 engineering fit candidate; physical qualification pending',body_mm=[W,D,BEZEL_TOP],keycap_envelope_height_mm=round(KEYCAP_Z+KEYCAP_H,3),pcb_bottom_z_mm=PCB_Z,
        pcb_mm=[42,54,PCB_T],key_rotation_deg=KEY_ROT,keycap_datum=dict(stem_top_above_pcb_mm=15.0,socket_depth_mm=SOCKET_DEPTH,cavity_mm=16.3,boss_diameter_mm=5.5,cross_slots_mm=[[4.05,1.32],[1.12,4.05]],travel_checked_mm=TRAVEL),mounts_board_xy_mm=[[refs[r]["x"],refs[r]["y"]] for r in ("H1","H2","H3","H4")],key_centers_board_xy_mm=[[11.475,40.8],[30.525,40.8]],
        load_supports_board_xy_mm=[[x+21,y+27] for x,y in LOAD_SUPPORTS],board_side_clearance_mm=round(SIDE_GAP,3),
        cell='User-supplied LIR2032 in the vendor-soldered BT1 holder; no pack, keeper or harness',holder_envelope_mm=[31.4,20.3,HOLDER_H],
        oled_support_mm=2.5,oled_nominal_module_pcb_mm=[27.3,27.8,1.2],oled_nominal_glass_mm=[24.74,16.9,1.4],oled_checked_max_mm=[27.7,28.2,3.4],oled_aperture_mm=[23.6,12.8],oled_roof_z_mm=FRONT_TOP,oled_max_top_gap_mm=round(FRONT_SEAM-(module_z+3.2),3),key_plate_top_above_pcb_mm=5,key_plate_thickness_mm=1.5,key_plate_hole_mm=14.05,
        usb_opening_y_mm=refs["J1"]["y"],usb_opening_mm=[13.4,7.2],usb_axis_z_mm=round(usb_axis,3),usb_plug_reservation_mm=[12.55,6.7],
        fasteners='Four M2 x 6 cross pan-head self-tapping screws (LCSC C357360 PA2X6nie) through the lid-boss floor and PCB into 1.7 mm base pilots (4.2 mm deep)',
        valid_solids={n:dict(valid=s.val().isValid(),count=len(s.solids().vals()),volume_mm3=round(volume(s),3)) for n,s in printed},
        shell_intersections_mm3={'lid_front_rear':round(overlap(lid_front,lid_rear),8),'base_lid':round(overlap(base,lid),8)},
        reported_intersections=results,assembly_path_checks=dict(poses=motion_count,sampled_intersection_tests=motion_tests,step_mm=.5,max_lift_mm=40,collisions=motion_hits,limitations='Sampled straight vertical assembly/removal; excludes soldering, screw insertion, cell insertion and print distortion.'),minimum_modeled_distances_mm={k:round(v,5) for k,v in distances.items()},source_board_sha256=data['board_sha256'],source_model_sha256=data['model_sha256'],generator_sha256=generator_hash,rendered_count=12345678,firmware_renderer_sha256=firmware_hashes,cadquery_version=cq.__version__,python_version=sys.version.split()[0],
        limitations=['Component bodies, pins and screws are simplified envelopes; no exact assembled vendor CAD claim.',
        'Native footprint bounding boxes conservatively bound bottom components; heights are stated family allowances.',
        'BT1 envelope uses the supplier 3D model extents plus the full 20 mm cell cylinder at holder height; cell retention and insertion force are untested.',
        'Printed MX keycaps: cross-socket fit, travel and legend durability require a print sample.',
        'Module drawing controls27.30x27.80mm geometry; summary26x26mm conflicts. Header centering is nominal; verify exact sample, clamp-free support lands, trimmedpins and+/-0.4mm lateral fit.',
        'Switches clip into the rear key plate and press into vendor-placed hot-swap sockets (no switch soldering); plate-hole and socket alignment and switch retention need a print sample.',
        'USB opening is checked against a USB-IF maximum overmold envelope only; real cable fit in both orientations is a first-article check.',
        'Self-tapping thread strength over repeated cell changes, print tolerances, 1.0 mm side clearance, USB strain and drop behavior remain untested; print the tolerance coupon first.'])
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
    flipped_cap=lambda c,x,y: c.translate((-x,-y,0)).rotate((0,0,0),(1,0,0),180).translate((0,0,KEYCAP_Z+KEYCAP_H))
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
