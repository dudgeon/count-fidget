#!/usr/bin/env python3
"""Generate a separate Q2 fit candidate; never writes historical Rev0 or PCB files.

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
from pathlib import Path

import cadquery as cq
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'mechanical/q2'
BOARD = ROOT / 'electronics/q2/click-counter-Q2.kicad_pcb'
MODEL = ROOT / 'electronics/q2/netlist-Q2.json'
W, D, WALL, FLOOR = 50., 45., 1.6, 1.6
PCB_Z, PCB_T, SEAM, TOP, BEZEL_TOP = 10.5, 1., 15.5, 17.1, 19.8
LCD_X, LCD_Y = 0., -11.25
KEYS = [(-9.525, 8.), (9.525, 8.)]
MOUNTS = [(-18.5, 17.5), (18.5, 17.5)]
LOAD_SUPPORTS = [(-15., 10.5), (15., 10.5)]
BAT_X, BAT_Y, BAT_Z = 0., 7., 1.9
KEEPER_Z = 6.4
KEEPER_SCREWS = [(-9.5, 16.5), (9.5, 16.5)]


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
    return volume(a.intersect(b))


def mesh_check(path):
    data=path.read_bytes(); count=struct.unpack_from('<I',data,80)[0]
    assert len(data)==84+50*count, 'Unexpected binary STL length'
    edges=Counter()
    for i in range(count):
        points=struct.unpack_from('<12f',data,84+50*i)[3:]
        vertices=[tuple(round(v,5) for v in points[j:j+3]) for j in [0,3,6]]
        for a,b in [(0,1),(1,2),(2,0)]: edges[tuple(sorted([vertices[a],vertices[b]]))]+=1
    bad=sum(v!=2 for v in edges.values())
    assert not bad, f'{path.name}: nonmanifold STL edges'
    return dict(triangles=count,nonmanifold_edges=bad,vertex_quantization_mm=.00001)


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
    assert all(abs(a-b)<1e-5 for a,b in zip(data['edges'],[0,0,42,40])), data['edges']
    assert [(by_ref[n]['x'], by_ref[n]['y']) for n in ['H1', 'H2']] == [(2.5, 37.5), (39.5, 37.5)]
    assert (by_ref['DS1']['x'], by_ref['DS1']['y']) == (21, 8.75)
    rows = sorted(set(round(p['y'], 6) for p in by_ref['DS1']['pads']))
    assert rows == [2.25, 15.25], rows
    for ref, (x, y) in zip(['SW1', 'SW2'], KEYS):
        central = [p for p in by_ref[ref]['pads'] if abs(p['drill'][0] - 4) < .001]
        assert len(central) == 1 and abs(central[0]['x'] - 21 - x) < 1e-6 and abs(central[0]['y'] - 20 - y) < 1e-6
    assert (by_ref['J1']['x'], by_ref['J1']['y'], by_ref['J1']['angle']) == (38.9, 13.3, 90)
    assert sha(BOARD)==board_hash and sha(MODEL)==model_hash, 'Source changed while reading; rebuild from stable files'
    data['board_sha256'] = board_hash
    data['model_sha256'] = model_hash
    return data, by_ref


def render(path, parts, exploded=False, cutaway=False, label=None):
    width, height = 1300, 1050
    canvas = np.full((height, width, 3), [242, 246, 249], dtype=np.uint8)
    depth = np.full((height, width), np.inf, dtype=np.float32)
    target = np.array([0, 0, 24 if exploded else 13], dtype=float)
    camera = target + [65, -95, 130]
    forward = target - camera; forward /= np.linalg.norm(forward)
    right = np.cross(forward, [0, 0, 1]); right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    scale = 9.7 if exploded else 14.0
    light = np.array([-.35, -.6, .72]); light /= np.linalg.norm(light)
    for name, source, color in parts:
        if cutaway and name in ['lid', 'keycap-1', 'keycap-2']:
            continue
        shape = source
        if cutaway and name == 'base':
            shape = shape.cut(block(80, 80, 25, 8))
        dz = 0
        if exploded:
            dz = 28 if name == 'lid' else 38 if name.startswith('keycap') else 16 if name.startswith('switch') else 22 if name == 'LCD-glass' else 11 if name not in ['base', 'pack-envelope', 'battery-keeper'] else 0
        rgb = np.array([int(color[i:i+2], 16) for i in (1, 3, 5)])
        for solid in shape.solids().vals():
            verts, triangles = solid.tessellate(.12, .2)
            pts = np.array([(v.x, v.y, v.z + dz) for v in verts])
            rel = pts - target
            proj = np.column_stack((width/2 + rel@right*scale, height*.54-rel@up*scale, (pts-camera)@forward))
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
    draw.text((40, 30), 'COUNT FIDGET  /  Q2', font=font, fill='#183e50')
    draw.text((40, 75), f'{view} · 50 × 45 mm body', font=small, fill='#456473')
    draw.text((40, 1004), 'Engineering fit candidate · component envelopes · physical qualification pending', font=small, fill='#456473')
    im.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--kicad-python', required=True)
    ap.add_argument('--skip-render', action='store_true')
    args = ap.parse_args()
    generator_hash = sha(Path(__file__))
    OUT.mkdir(parents=True, exist_ok=True)
    data, refs = read_board(args.kicad_python)
    (OUT/'board-geometry.json').write_text(json.dumps(data, indent=2)+'\n')
    base = rounded(W,D,SEAM,r=3).cut(rounded(W-2*WALL,D-2*WALL,SEAM,FLOOR,r=1.4))
    for x,y in MOUNTS:
        base = base.union(cyl(2.6,PCB_Z-FLOOR,FLOOR,x,y)).cut(cyl(.85,PCB_Z-2.4,2.4,x,y))
    for x,y in LOAD_SUPPORTS:
        base = base.union(cyl(1.3,PCB_Z-FLOOR,FLOOR,x,y))
    tray = cyl(12.1,1.4,FLOOR,BAT_X,BAT_Y).cut(cyl(10.9,1.5,FLOOR,BAT_X,BAT_Y))
    tray = tray.cut(block(9,7,3,FLOOR,-11,3))
    base = base.union(tray)
    for x,y in KEEPER_SCREWS:
        base = base.union(cyl(2.4,KEEPER_Z-FLOOR,FLOOR,x,y)).cut(cyl(.85,KEEPER_Z-2.2,2.2,x,y))
    # Front engagement hooks retain the lid while the two rear screws close it.
    for x in [-12,12]:
        base = base.union(block(6,1.5,1,14.1,x,-20.35))
    usb_cut = block(12,13.2,5.0,11.1,W/2,-6.7)
    base = base.cut(usb_cut)
    lid = rounded(W,D,TOP-SEAM,SEAM,r=3)
    for x,y in KEYS:
        lid = lid.cut(block(16.4,16.4,8,SEAM-1,x,y))
    lid = lid.union(rounded(38.6,16.6,BEZEL_TOP-TOP,TOP,.8,LCD_X,LCD_Y))
    lid = lid.cut(block(36.2,14.8,18.8-SEAM+.2,SEAM-.1,LCD_X,LCD_Y))
    lid = lid.cut(block(32.7,7.2,8,SEAM-.1,LCD_X,LCD_Y))
    for x,y in MOUNTS:
        lid = lid.union(cyl(1.8,SEAM-(PCB_Z+PCB_T)+.1,PCB_Z+PCB_T,x,y))
        lid = lid.cut(cyl(1.2,8,PCB_Z+PCB_T-.1,x,y))
        lid = lid.cut(cyl(2.1,3,TOP-.6,x,y))
    for x in [-12,12]:
        lid = lid.union(block(6,.8,3.2,12.4,x,-18.9))
        lid = lid.union(block(6,1.6,.7,13.1,x,-19.5))
    lid = lid.cut(usb_cut)
    keeper = rounded(29,3.4,1.2,KEEPER_Z,.6,0,13)
    for x,y in KEEPER_SCREWS:
        keeper = keeper.union(block(4.8,3.5,1.2,KEEPER_Z,x,14.75)).union(cyl(2.4,1.2,KEEPER_Z,x,y))
        keeper = keeper.cut(cyl(1.2,2,KEEPER_Z-.1,x,y))
    for x,y in LOAD_SUPPORTS:
        keeper = keeper.cut(cyl(1.65,2,KEEPER_Z-.1,x,y))
    pcb = rounded(42,40,PCB_T,PCB_Z,2)
    tails = []
    for ref,p in refs.items():
        for pad in p['pads']:
            dx,dy = pad['drill']; x,y = pad['x']-21,pad['y']-20
            if min(dx,dy) <= 0: continue
            if abs(dx-dy) < 1e-6:
                hole = cyl(dx/2,3,PCB_Z-1,x,y)
            else:
                angle = (0 if dx>=dy else 90)-pad['angle']
                hole = cq.Workplane('XY').slot2D(max(dx,dy),min(dx,dy),angle).extrude(3).translate((x,y,PCB_Z-1))
            pcb = pcb.cut(hole)
            if ref.startswith('SW'):
                tails.append((ref+'-post-'+str(len(tails)),cyl(max(dx/2-.1,.25),2.3,PCB_Z-2.3,x,y),'#c4ad73'))
            elif ref == 'DS1':
                tails.append(('LCD-lead-'+pad['number'],block(1.1,.3,6.,PCB_Z-1,x,y),'#b7bcc0'))
    pack = cyl(10.5,4.2,BAT_Z,BAT_X,BAT_Y)
    glass = block(34.9,13,2.2,PCB_Z+PCB_T+4,LCD_X,LCD_Y)
    max_glass = block(35.1,13.2,2.85,PCB_Z+PCB_T+4,LCD_X,LCD_Y)
    usb = block(7.35,8.94,3.31,PCB_Z+PCB_T,17.9,-6.7)
    mcu = block(12.5,8.3,1.2,PCB_Z+PCB_T,0,-11.25)
    jst = block(4.95,6,2.96,PCB_Z+PCB_T,-16,-3.2)
    parts = [('base',base,'#82bac6'),('lid',lid,'#d0e7ec'),('battery-keeper',keeper,'#5893a4'),('PCB',pcb,'#2b755e'),('pack-envelope',pack,'#c8cbd0'),('LCD-glass',glass,'#b4c9a2'),('USB',usb,'#b7c0c8'),('MCU',mcu,'#333e4a'),('JST',jst,'#eee7cf')]
    parts += tails
    component_checks = [('PCB',pcb),('pack',pack),('LCD-max',max_glass),('USB',usb),('MCU',mcu),('JST',jst)] + [(n,s) for n,s,_ in tails]
    bottom = []
    for ref,p in refs.items():
        if p['side'] != 'bottom' or ref.startswith('TP'): continue
        bx,by,bw,bd = p['bbox']
        h = 1.1 if ref.startswith('R') or ('0603' in next((a['footprint'] for a in json.loads(MODEL.read_text())['parts'] if a['ref']==ref),'')) else 1.6
        s = block(bw,bd,h,PCB_Z-h,bx+bw/2-21,by+bd/2-20)
        bottom.append((ref,s)); parts.append((ref+'-envelope',s,'#414854'))
        component_checks.append((ref,s))
    for i,(x,y) in enumerate(KEYS,1):
        switch = block(14,14,5,PCB_Z+PCB_T,x,y).union(block(15.6,15.6,6.6,PCB_Z+PCB_T+5,x,y))
        cap = rounded(18.2,18.2,7,22.8,1.4,x,y).cut(block(15.8,15.8,6,22.7,x,y))
        parts += [(f'switch-{i}',switch,'#35404d'),(f'keycap-{i}',cap,'#62accb' if i==1 else '#e4b568')]
        component_checks += [(f'switch-{i}',switch),(f'keycap-{i}-pressed-envelope',block(18.2,18.2,7,18.8,x,y))]
    # Nonconductive 4 mm support pads; separate parts, never hard-clamp glass.
    pads = [block(3,4,4,PCB_Z+PCB_T,-15.5,-11.5),block(3,3,4,PCB_Z+PCB_T,15.5,-15)]
    for i,s in enumerate(pads): parts.append((f'LCD-compliant-pad-{i+1}',s,'#ead7bc'))
    # Reservation volumes: not a manufactured harness or a selected USB cable.
    wire_side = block(2.0,10,7.5,4.0,-22.2,-.5)
    wire_exit = block(8,6,2.4,3.2,-11,3)
    wire_under = block(10,4,2.4,4,-17,1)
    plug_access = block(10,12,4.6,11.5,26.5,-6.7)
    reservations = [('wire-side-corridor',wire_side),('wire-tab-NTC-exit',wire_exit),('wire-under-PCB',wire_under),('USB-plug-access',plug_access)]
    # Fastener envelopes: rear M2x12 (seat16.5->tip4.5), keeper M2x5 (tip2.6).
    screws=[]
    for i,(x,y) in enumerate(MOUNTS): screws.append((f'rear-screw-{i+1}',cyl(1,12,TOP-.6-12,x,y).union(cyl(2,1.7,TOP-.6,x,y))))
    for i,(x,y) in enumerate(KEEPER_SCREWS): screws.append((f'keeper-screw-{i+1}',cyl(1,5,KEEPER_Z+1.2-5,x,y).union(cyl(2,1.7,KEEPER_Z+1.2,x,y))))
    parts += [(n,s,'#929da6') for n,s in screws]
    results=[]
    for shell_name,shell in [('base',base),('lid',lid),('battery-keeper',keeper)]:
        for name,shape in component_checks+reservations:
            v=overlap(shell,shape)
            if v>1e-5: results.append(dict(a=shell_name,b=name,intersection_mm3=round(v,6)))
    for name,shape in bottom+[(n,s) for n,s,_ in tails]:
        for other,obj in [('pack',pack),('battery-keeper',keeper)]+screws:
            v=overlap(shape,obj)
            if v>1e-5: results.append(dict(a=name,b=other,intersection_mm3=round(v,6)))
    for name,shape in screws:
        for other,obj in [('pack',pack),('PCB',pcb)]+[(n,s) for n,s in component_checks if 'pressed-envelope' in n]:
            v=overlap(shape,obj)
            if v>1e-5: results.append(dict(a=name,b=other,intersection_mm3=round(v,6)))
    distances = {
        'pack_to_bottom_components': min(s.val().distance(pack.val()) for _,s in bottom),
        'pack_to_switch_tails': min(s.val().distance(pack.val()) for n,s,_ in tails if n.startswith('SW')),
        'keeper_to_bottom_components': min(s.val().distance(keeper.val()) for _,s in bottom),
        'keeper_screw_to_bottom_components': min(s.val().distance(q.val()) for _,s in bottom for n,q in screws if n.startswith('keeper')),
        'max_lcd_to_mcu': max_glass.val().distance(mcu.val()),
        'max_lcd_to_usb': max_glass.val().distance(usb.val()),
        'max_lcd_to_jst': max_glass.val().distance(jst.val()),
        'pack_to_fasteners': min(s.val().distance(pack.val()) for _,s in screws),
        'pressed_keycap_to_rear_screw': min(s.val().distance(q.val()) for n,s in component_checks if 'pressed-envelope' in n for name,q in screws if name.startswith('rear')),
    }
    assert sha(BOARD)==data['board_sha256'] and sha(MODEL)==data['model_sha256'], 'Source changed during build; regenerate'
    report=dict(status='Q2 engineering fit candidate; physical qualification pending',body_mm=[W,D,BEZEL_TOP],keycap_envelope_height_mm=29.8,pcb_bottom_z_mm=PCB_Z,
        pcb_mm=[42,40,1],mounts_board_xy_mm=[[2.5,37.5],[39.5,37.5]],key_centers_board_xy_mm=[[11.475,28],[30.525,28]],
        battery_max_envelope_mm=[21,21,4.2],battery_bore_mm=21.8,battery_to_board_mm=PCB_Z-(BAT_Z+4.2),battery_to_keeper_mm=KEEPER_Z-(BAT_Z+4.2),
        lcd_standoff_mm=4,lcd_nominal_glass_mm=[34.9,13,2.2],lcd_checked_max_mm=[35.1,13.2,2.85],lcd_pocket_mm=[36.2,14.8],lcd_max_top_gap_mm=18.8-(PCB_Z+PCB_T+4+2.85),
        usb_opening_y_mm=13.3,usb_opening_mm=[13.2,5],board_side_clearance_mm=[(W-2*WALL-42)/2,(D-2*WALL-40)/2],
        valid_solids={n:dict(valid=s.val().isValid(),count=len(s.solids().vals()),volume_mm3=round(volume(s),3)) for n,s in [('base',base),('lid',lid),('battery-keeper',keeper)]},
        shell_intersections_mm3={'base_lid':round(overlap(base,lid),8),'base_keeper':round(overlap(base,keeper),8),'lid_keeper':round(overlap(lid,keeper),8)},
        reported_intersections=results,minimum_modeled_distances_mm={k:round(v,5) for k,v in distances.items()},source_board_sha256=data['board_sha256'],source_model_sha256=data['model_sha256'],generator_sha256=generator_hash,cadquery_version=cq.__version__,python_version=sys.version.split()[0],
        limitations=['Component bodies, pins and screws are simplified envelopes; no exact assembled vendor CAD claim.',
        'Native footprint bounding boxes conservatively bound bottom components; heights are stated family allowances.',
        'Four-wire corridor and tab/NTC reservations do not prove the finished 40±5mm harness bends or connector insertion.',
        'Keycaps are provisional envelopes, not approved Adafruit CAD; full travel and fit require a sample.',
        'LCD compliant pads need material/contact approval; no glass clamping or preload qualified.',
        'Screw thread strength, print tolerances, battery retention, USB strain and drop behavior remain untested.'])
    (OUT/'fit-report.json').write_text(json.dumps(report,indent=2)+'\n')
    assembly=cq.Assembly(name='Count-Fidget-Q2-enclosure-candidate')
    for name,shape,color in parts: assembly.add(shape,name=name,color=cq.Color(color))
    assembly.export(str(OUT/'enclosure-Q2.step'))
    for name,shape in [('base',base),('battery-keeper',keeper.translate((0,0,-KEEPER_Z))),('lid',lid.rotate((0,0,0),(1,0,0),180).translate((0,0,BEZEL_TOP)))]:
        cq.exporters.export(shape,str(OUT/f'{name}-Q2.stl'),tolerance=.04,angularTolerance=.1)
    report['stl_mesh_checks']={p.name:mesh_check(p) for p in OUT.glob('*.stl')}
    (OUT/'fit-report.json').write_text(json.dumps(report,indent=2)+'\n')
    if not args.skip_render:
        render(OUT/'assembled-Q2.png',parts)
        render(OUT/'exploded-Q2.png',parts,exploded=True)
        render(OUT/'interior-Q2.png',parts,cutaway=True)
        bay = [p for p in parts if p[0] in ['base','pack-envelope','battery-keeper'] or p[0].startswith('keeper-screw')]
        render(OUT/'battery-bay-Q2.png',bay,cutaway=True,label='Battery bay / board removed')
    outputs={p.name:sha(p) for p in OUT.iterdir() if p.suffix in ['.stl','.step','.png','.json'] and p.name!='build-manifest.json'}
    assert sha(Path(__file__))==generator_hash, 'Generator changed during build; regenerate'
    assert sha(BOARD)==data['board_sha256'] and sha(MODEL)==data['model_sha256'], 'Source changed during export; regenerate'
    (OUT/'build-manifest.json').write_text(json.dumps(dict(generator=report['generator_sha256'],board=report['source_board_sha256'],model=report['source_model_sha256'],outputs=outputs),indent=2)+'\n')
    print(json.dumps(report,indent=2))
    assert all(v['valid'] and v['count']==1 for v in report['valid_solids'].values())
    assert max(report['shell_intersections_mm3'].values())<1e-5
    assert not results, 'Review intersections listed in fit-report.json before considering the candidate ready'


if __name__=='__main__': main()
