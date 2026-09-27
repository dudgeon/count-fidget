#!/usr/bin/env python3
"""Q5A: printed tray + one flat laser-cut cast-acrylic lid for the locked Q5 board.

A separate enclosure variant for the ordered Q5 board. It never writes the
board, the Q5 printed-lid candidate (mechanical/q5) or any historical file.
Board positions, the switch/connector assertions and the component envelopes
come from the Q5 builder (imported read-only), so both variants are checked
against the same native board.

Stack (Z above the tray underside, mm):
  floor 1.2 | 0.5 gap | BT1 holder 5.52 | PCB 1.6 (top 8.82)
  brass spacer 6.0: lid underside 14.82 = PCB top + 6.0
    - the checked OLED maximum is PCB top + 5.7 (0.3 mm air gap; no display cutout)
    - the CPG151101D13 rim top is PCB top + 6.00 (drawing): the lid rests on both rims
  cast acrylic 2.0 (1.8-2.3 accepted) | lid top 16.82
Keycaps are 17 mm tiles datumed on the stem (top at PCB top + 17.4, as Q5).

All geometry is built in the Q5 builder's frame (X = PCB_X - 21, Y = PCB_Y - 27,
Y down) and exported mirrored to right-handed CAD coordinates (Y = 27 - PCB_Y).
Component solids are envelopes, not vendor CAD. Requires CadQuery 2.8 and a
KiCad 10 Python (for pcbnew) passed with --kicad-python.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_q5_enclosure as q5  # noqa: E402  (read-only reuse: board reader, helpers, envelopes)

OUT = ROOT / 'mechanical/q5-acrylic'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
block, rounded, cyl, overlap, volume, sha = q5.block, q5.rounded, q5.cyl, q5.overlap, q5.volume, q5.sha

# ---- stack --------------------------------------------------------------
FLOOR = 1.2                  # 6 x 0.2 mm layers; braced by bosses, load supports and the pinhole tube
HOLDER_H = q5.HOLDER_H       # 5.52, CR2032-BS-6-1 supplier model
HOLDER_GAP = 0.5             # printed-floor flatness allowance under the holder
PCB_T = q5.PCB_T
PCB_Z = FLOOR + HOLDER_GAP + HOLDER_H
PCB_TOP = PCB_Z + PCB_T
SPACER_L, SPACER_OD, SPACER_ID = 6.0, 4.0, 2.2
LID_Z = PCB_TOP + SPACER_L
LID_T, LID_T_RANGE = 2.0, (1.8, 2.3)   # cast sheet thickness tolerance is wide; the lid datum is its underside
LID_TOP = LID_Z + LID_T
REVEAL = 0.25                # tray rim sits below the lid: spacers, not the print, set the lid height
WALL_TOP = LID_Z - REVEAL
GAP, WALL = 0.5, 1.2         # PCB-to-wall clearance and wall (3 x 0.4 mm perimeters)
W, D = 42 + 2 * (GAP + WALL), 54 + 2 * (GAP + WALL)
R_IN = 1.4                   # inner corner: clears the square PCB corner (max 1.47 at 0.5 gap)
R_OUT = R_IN + WALL
LID_INSET = 0.25             # lid is inset from the tray outline so print/cut tolerance reads as a deliberate step
TOP_CHAMFER, BOTTOM_FILLET = 0.4, 0.6

# ---- keys ---------------------------------------------------------------
KEYS, KEY_ROT = q5.KEYS, q5.KEY_ROT              # (+-9.525, 13.8); sockets and switches at 90 / 270 deg
STEM_TOP = PCB_TOP + 15.0                        # CPG151101D13: housing 11.0 +-0.15, stem 4.0 above it
HOUSING_TOP = PCB_TOP + 11.15
TRAVEL = 4.4                                     # 4.0 +-0.4
SOCKET_DEPTH = 3.5
RIM = (15.6, 13.96)                              # drawing: 15.60 along the pin axis (board X here), 13.96 across
RIM_Z = (PCB_TOP + 5.0, PCB_TOP + 6.0)           # plate datum 5.00, rim top 6.00
UPPER_PIN_SIDE, UPPER_SLOPE_SIDE, UPPER_HALF_Y = 5.8, 7.35, 6.17   # upper housing just above the rim (drawing)
KEY_HOLE = (15.2, 12.9, 0.6)                     # lid key hole (X, Y, corner r): clears the upper housing, captures the rim
KEYCAP, KEYCAP_R = 17.0, 2.0
KEYCAP_B = PCB_TOP + 13.1                        # skirt underside at rest; pressed 8.7 above the PCB
KEYCAP_ROOF = STEM_TOP + 1.2                     # 0.65 mm above the housing at 4.4 mm travel
KEYCAP_TOP = KEYCAP_ROOF + 1.2
KEYCAP_CAVITY = 14.0

# ---- fasteners (standard parts) ------------------------------------------
SCREW_LEN, SCREW_D, SCREW_HEAD_D, SCREW_HEAD_H = 14.0, 2.0, 3.8, 1.6   # M2 x 14 cross pan-head self-tapping
LID_HOLE = 2.4
PILOT_R, PILOT_DEPTH, BOSS_R = 0.85, 4.8, 2.2
USB_RELIEF = (0.4, 10.0)     # depth into the wall, width along the wall
GUSSET_TOP = FLOOR + 3.3     # below every bottom-side part except the centred BT1


def rrect(w, d, r, h, z, x=0, y=0):
    return block(w, d, h, z, x, y).edges('|Z').fillet(r)


def switch_envelope(x, y, rot):
    """CPG151101D13 from the HanElectricity RevA drawing (p6): bottom housing 13.95,
    rim 15.60 x 13.96 at 5.00-6.00, upper housing 13.15 along the pin axis (pin side
    5.8, sloped side 7.35 from centre) and 12.35 across, top 11.0 +0.15."""
    s = 1 if rot % 360 == 90 else -1               # sloped (south) side points at the board centre line
    bottom = block(13.95, 13.95, 5.0, PCB_TOP, x, y)
    rim = block(RIM[0], RIM[1], RIM_Z[1] - RIM_Z[0], RIM_Z[0], x, y)
    prof = [(-UPPER_PIN_SIDE, 0), (UPPER_SLOPE_SIDE, 0), (3.4, HOUSING_TOP - RIM_Z[1]), (-UPPER_PIN_SIDE, HOUSING_TOP - RIM_Z[1])]
    upper = (cq.Workplane('XZ').polyline([(s * u, z) for u, z in prof]).close()
             .extrude(UPPER_HALF_Y, both=True).translate((x, y, RIM_Z[1])))
    # MX stem opening: a standard 5.5 mm keycap boss enters the housing at full travel.
    upper = upper.cut(cyl(2.85, HOUSING_TOP - RIM_Z[1] + 1, RIM_Z[1] - 0.5, x, y))
    stem = block(4.0, 1.3, STEM_TOP - HOUSING_TOP, HOUSING_TOP, x, y).union(block(1.1, 4.0, STEM_TOP - HOUSING_TOP, HOUSING_TOP, x, y))
    return bottom, rim, upper, stem


def make_lid(mounts, thickness=LID_T):
    lid = rrect(W - 2 * LID_INSET, D - 2 * LID_INSET, R_OUT - LID_INSET, thickness, LID_Z)
    for x, y in mounts:
        lid = lid.cut(cyl(LID_HOLE / 2, thickness + 1, LID_Z - 0.5, x, y))
    for x, y in KEYS:
        lid = lid.cut(rrect(KEY_HOLE[0], KEY_HOLE[1], KEY_HOLE[2], thickness + 1, LID_Z - 0.5, x, y))
    return lid


def keycap(x, y, symbol, rot):
    h = KEYCAP_TOP - KEYCAP_B
    cap = rrect(KEYCAP, KEYCAP, KEYCAP_R, h, KEYCAP_B, x, y)
    try:
        cap = cap.faces('>Z').edges().fillet(0.8)
    except Exception:
        pass
    cap = cap.cut(block(KEYCAP_CAVITY, KEYCAP_CAVITY, KEYCAP_ROOF - KEYCAP_B + 0.1, KEYCAP_B - 0.1, x, y).edges('|Z').fillet(1.0))
    boss_z = STEM_TOP - SOCKET_DEPTH
    cap = cap.union(cyl(2.75, KEYCAP_ROOF - boss_z + 0.05, boss_z, x, y))
    wide, narrow = (4.05, 1.32), (1.12, 4.05)     # switch frame: horizontal arm 1.30, vertical arm 1.10
    if rot % 180:
        wide, narrow = (1.32, 4.05), (4.05, 1.12)
    cap = cap.cut(block(*wide, SOCKET_DEPTH + 0.1, boss_z - 0.1, x, y)).cut(block(*narrow, SOCKET_DEPTH + 0.1, boss_z - 0.1, x, y))
    top = KEYCAP_TOP
    if symbol == '+':
        legend = block(7.0, 1.3, 0.4, top - 0.4, x, y).union(block(1.3, 7.0, 0.4, top - 0.4, x, y))
    else:
        legend = cyl(3.6, 0.4, top - 0.4, x, y).cut(cyl(2.45, 0.5, top - 0.45, x, y))
    return cap.cut(legend)


def build(refs):
    """Every enclosure part and envelope in the internal (Y-down) frame."""
    mounts = [(refs[r]['x'] - 21, refs[r]['y'] - 27) for r in ('H1', 'H2', 'H3', 'H4')]
    lcd_x, lcd_y = refs['DS1']['x'] - 21, refs['DS1']['y'] - 27
    usb_y = refs['J1']['y'] - 27
    usb_axis = PCB_Z - 3.31 / 2
    mouth_x = 21.575
    g = {}
    # ---- tray ----
    tray = rounded(W, D, WALL_TOP, r=R_OUT)
    tray = tray.faces('>Z').edges().chamfer(TOP_CHAMFER)
    tray = tray.faces('<Z').edges().fillet(BOTTOM_FILLET)
    tray = tray.cut(rounded(W - 2 * WALL, D - 2 * WALL, WALL_TOP, FLOOR, r=R_IN))
    iw, idp = W / 2 - WALL, D / 2 - WALL
    boxes = [(-W / 2, -D / 2, 0, W / 2, D / 2, FLOOR),                       # floor
             (-W / 2, -D / 2, 0, -iw + R_IN, D / 2, WALL_TOP), (iw - R_IN, -D / 2, 0, W / 2, D / 2, WALL_TOP),
             (-W / 2, -D / 2, 0, W / 2, -idp + R_IN, WALL_TOP), (-W / 2, idp - R_IN, 0, W / 2, D / 2, WALL_TOP)]
    for x, y in mounts:
        tray = tray.union(cyl(BOSS_R, PCB_Z - FLOOR, FLOOR, x, y))
        boxes.append((min(x, math.copysign(21 + GAP, x)) - 1, min(y, math.copysign(27 + GAP, y)) - 1, 0,
                      max(x, math.copysign(21 + GAP, x)) + 1, max(y, math.copysign(27 + GAP, y)) + 1, PCB_Z))
        cx, cy = math.copysign(21 + GAP, x), math.copysign(27 + GAP, y)
        ang = math.degrees(math.atan2(cy - y, cx - x))
        length = math.hypot(cx - x, cy - y) + 0.6
        gusset = (block(length, 1.2, GUSSET_TOP - FLOOR, FLOOR).translate((length / 2, 0, 0))
                  .rotate((0, 0, 0), (0, 0, 1), ang).translate((x, y, 0)))
        tray = tray.union(gusset.intersect(rounded(W - 0.2, D - 0.2, WALL_TOP, 0, r=R_OUT - 0.1)))
    for x, y in mounts:
        tray = tray.cut(cyl(PILOT_R, PILOT_DEPTH + 0.01, PCB_Z - PILOT_DEPTH, x, y))
    for x, y in q5.LOAD_SUPPORTS:
        tray = tray.union(cyl(1.3, PCB_Z - FLOOR, FLOOR, x, y))
        boxes.append((x - 1.3, y - 1.3, 0, x + 1.3, y + 1.3, PCB_Z))
    usb_cut = (cq.Workplane('YZ').rect(13.4, 7.2).extrude(8).edges('|X').fillet(1.0)   # r <= 1.13 keeps the max overmold corners inside
               .translate((W / 2 - WALL - 3, usb_y, usb_axis)))
    tray = tray.cut(usb_cut)
    # J1's mouth is 0.575 mm proud of the PCB edge but the side gap is 0.5 mm: a hidden 0.4 mm relief
    # above the opening lets the receptacle drop straight in (wall stays 0.8 mm over a 10 mm strip).
    tray = tray.cut(block(USB_RELIEF[0] + 1, USB_RELIEF[1], WALL_TOP, usb_axis, W / 2 - WALL - 1 + USB_RELIEF[0] / 2 + 0.5, usb_y))
    tray = tray.union(block(3, 5, PCB_Z - 3.31 - 0.15 - FLOOR, FLOOR, 17, usb_y))          # receptacle pedestal
    tray = tray.union(block(0.8, 5, PCB_Z - 1.0 - FLOOR, FLOOR, 13.675, usb_y))            # axial plug backstop
    boxes.append((13.275, usb_y - 2.5, 0, 18.5, usb_y + 2.5, PCB_Z))
    rx, ry = refs['SW3']['x'] - 21, refs['SW3']['y'] - 27
    tube_top = PCB_Z - 2.2 - 0.8
    tray = tray.union(cyl(1.65, tube_top - FLOOR, FLOOR, rx, ry)).cut(cyl(0.65, tube_top + 0.1, -0.05, rx, ry))
    boxes.append((rx - 1.65, ry - 1.65, 0, rx + 1.65, ry + 1.65, tube_top))
    g['tray_boxes'] = boxes
    warn = (cq.Workplane('XY').text('LIR2032 ONLY - rechargeable - never CR2032', 2.2, 0.45, fontPath=FONT,
                                    halign='center', valign='center').mirror('YZ').translate((0, -D / 2 + 9, -0.05)))
    tray = tray.cut(warn)
    g['tray'] = tray
    # ---- lid ----
    g['lid'] = make_lid(mounts)
    g['keycaps'] = [keycap(x, y, '+' if i == 0 else 'o', rot) for i, ((x, y), rot) in enumerate(zip(KEYS, KEY_ROT))]
    g['spacers'] = [cyl(SPACER_OD / 2, SPACER_L, PCB_TOP, x, y).cut(cyl(SPACER_ID / 2, SPACER_L + 1, PCB_TOP - 0.5, x, y)) for x, y in mounts]
    g['screws'] = [cyl(SCREW_D / 2, SCREW_LEN, LID_TOP - SCREW_LEN, x, y).union(cyl(SCREW_HEAD_D / 2, SCREW_HEAD_H, LID_TOP, x, y)) for x, y in mounts]
    g['switches'] = [switch_envelope(x, y, rot) for (x, y), rot in zip(KEYS, KEY_ROT)]
    # ---- board and component envelopes (as Q5, re-based on this stack) ----
    pcb = block(42, 54, PCB_T, PCB_Z)
    for ref, p in refs.items():
        for pad in p['pads']:
            dx, dy = pad['drill']
            if min(dx, dy) <= 0:
                continue
            x, y = pad['x'] - 21, pad['y'] - 27
            if abs(dx - dy) < 1e-6:
                hole = cyl(dx / 2, 3, PCB_Z - 1, x, y)
            else:
                hole = cq.Workplane('XY').slot2D(max(dx, dy), min(dx, dy), (0 if dx >= dy else 90) - pad['angle']).extrude(3).translate((x, y, PCB_Z - 1))
            pcb = pcb.cut(hole)
    g['pcb'] = pcb
    bx, by = refs['BT1']['x'] - 21, refs['BT1']['y'] - 27
    g['holder'] = (block(22.3, 16.2, HOLDER_H, PCB_Z - HOLDER_H, bx, by).union(block(31.4, 7.0, 2.2, PCB_Z - 2.2, bx, by))
                   .union(cyl(10.15, HOLDER_H, PCB_Z - HOLDER_H, bx, by)))
    module_z = PCB_TOP + 2.5
    g['oled_max'] = block(27.7, 28.2, 1.8, module_z - 0.2, lcd_x, lcd_y).union(block(24.94, 17.1, 2.2, module_z + 1.0, lcd_x, lcd_y - 0.58))
    g['oled_header'] = block(17.78, 2.5, 2.5, PCB_TOP, lcd_x, lcd_y - 12.4)
    g['usb'] = block(7.35, 8.94, 3.31, PCB_Z - 3.31, 17.9, usb_y)
    g['mcu'] = block(9.4, 9.4, 1.6, PCB_Z - 1.6, refs['U1']['x'] - 21, refs['U1']['y'] - 27)
    g['usb_plug'] = block(10, 12.55, 6.7, usb_axis - 3.35, mouth_x + 5.0, usb_y)
    bottom = []
    model_parts = {a['ref']: a for a in json.loads(q5.MODEL.read_text())['parts']}
    for ref, p in refs.items():
        if p['side'] != 'bottom' or ref.startswith('TP') or ref in ('U1', 'J1', 'BT1'):
            continue
        if ref in ('SW1', 'SW2'):
            pads = [q for q in p['pads'] if q['number'] in ('1', '2')]
            cx = sum(q['x'] for q in pads) / 2 - 21
            cy = sum(q['y'] for q in pads) / 2 - 27
            ang = math.degrees(math.atan2(pads[1]['y'] - pads[0]['y'], pads[1]['x'] - pads[0]['x']))
            bottom.append((ref + '-socket', block(15.5, 5.9, 1.85, PCB_Z - 1.85, 0, 0).rotate((0, 0, 0), (0, 0, 1), ang).translate((cx, cy, 0))))
            continue
        bx0, by0, bw, bd = p['bbox']
        fp = model_parts[ref]['footprint']
        h = 2.2 if ref == 'SW3' else 2.0 if ref == 'U8' else 1.1 if ('0603' in fp or '0805' in fp or 'SOD-323' in fp) else 1.6
        bottom.append((ref, block(bw, bd, h, PCB_Z - h, bx0 + bw / 2 - 21, by0 + bd / 2 - 27)))
    g['bottom'] = bottom
    tails = []
    for ref in ('SW1', 'SW2'):
        for pad in refs[ref]['pads']:
            if pad['drill'][0] <= 0:
                continue
            x, y = pad['x'] - 21, pad['y'] - 27
            if pad['drill'][0] > 3.5:
                tails.append((ref + '-post', cyl(1.925, 1.4, PCB_Z - 1.4, x, y)))
            else:
                tails.append((ref + '-pin', cyl(0.75, 1.7, PCB_Z - 1.7, x, y)))
    for i, pad in enumerate(refs['DS1']['pads']):
        tails.append((f'DS1-joint-{i}', cyl(0.9, 1.0, PCB_Z - 1, pad['x'] - 21, pad['y'] - 27)))
    g['tails'] = tails
    g['mounts'], g['usb_y'], g['usb_axis'], g['mouth_x'], g['module_z'] = mounts, usb_y, usb_axis, mouth_x, module_z
    return g


def rim_capture(lid, x, y):
    """Area of each rim top face covered by the lid underside, and the per-side overlap."""
    rim_top = block(RIM[0], RIM[1], 0.02, RIM_Z[1] - 0.01, x, y)
    lid_skin = lid.intersect(block(80, 80, 0.02, LID_Z, 0, 0))
    area = volume(rim_top.intersect(lid_skin.translate((0, 0, RIM_Z[1] - 0.01 - LID_Z)))) / 0.02
    return dict(area_mm2=round(area, 2), overlap_x_mm=round((RIM[0] - KEY_HOLE[0]) / 2, 3), overlap_y_mm=round((RIM[1] - KEY_HOLE[1]) / 2, 3))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--kicad-python', required=True)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    global OUT
    if args.output:
        OUT = args.output.resolve()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'build-manifest.json').unlink(missing_ok=True)
    generator_hash, q5_hash = sha(Path(__file__)), sha(ROOT / 'scripts/build_q5_enclosure.py')
    data, refs = q5.read_board(args.kicad_python)
    g = build(refs)
    tray, lid, caps = g['tray'], g['lid'], g['keycaps']
    switches = g['switches']
    comps = ([('PCB', g['pcb']), ('holder', g['holder']), ('OLED-max', g['oled_max']), ('OLED-header', g['oled_header']),
              ('USB', g['usb']), ('MCU', g['mcu'])] + g['bottom'] + g['tails'])
    for i, (bot, rim, upper, stem) in enumerate(switches, 1):
        comps += [(f'switch-{i}-bottom', bot), (f'switch-{i}-rim', rim), (f'switch-{i}-upper', upper)]
    hits = []

    def check(a, sa, b, sb, tol=1e-5):
        v = overlap(sa, sb)
        if v > tol:
            hits.append(dict(a=a, b=b, intersection_mm3=round(v, 6)))
    # Tray against every component, the plug reservation, spacers and screw heads.
    for n, s in comps + [('USB-plug-access', g['usb_plug'])] + [(f'spacer-{i+1}', s) for i, s in enumerate(g['spacers'])]:
        if n == 'PCB':
            continue      # the PCB rests on the bosses (face contact)
        check('tray', tray, n, s)
    # Screws: shank cuts its own thread in the pilot; everything else must be clear.
    for i, s in enumerate(g['screws'], 1):
        for n, c in comps:
            if n == 'PCB':
                continue
            check(f'screw-{i}', s, n, c)
        tip = s.val().BoundingBox().zmin
        if tip < PCB_Z - PILOT_DEPTH - 1e-6:
            hits.append(dict(a=f'screw-{i}', b='pilot-bottom', intersection_mm3=round(PCB_Z - PILOT_DEPTH - tip, 4)))
    # Lid: clear of the OLED maximum, the upper housings, the stems, spacers' bores; resting on rims.
    for n, s in comps:
        if n.endswith('-rim'):
            continue
        check('lid', lid, n, s)
    for i, s in enumerate(g['screws'], 1):
        check('lid', lid, f'screw-{i}', s)
    # Pressed keycaps (4.4 mm, with 0.6 mm wobble margin) against the thickest accepted sheet and screw heads.
    thick_lid = make_lid(g['mounts'], LID_T_RANGE[1])
    pressed = [c.translate((0, 0, -TRAVEL)) for c in caps]
    heads = [cyl(SCREW_HEAD_D / 2, SCREW_HEAD_H, LID_Z + LID_T_RANGE[1], x, y) for x, y in g['mounts']]
    for i, c in enumerate(pressed, 1):
        check(f'keycap-{i}-pressed', c, 'lid-2.3mm', thick_lid)
        for j, h in enumerate(heads, 1):
            check(f'keycap-{i}-pressed', c, f'screw-head-{j}-on-2.3mm', h)
        check(f'keycap-{i}-pressed', c, 'tray', tray)
        bot, rim, upper, stem = switches[i - 1]
        check(f'keycap-{i}-pressed', c, f'switch-{i}-upper', upper)
    # Straight-line assembly: board assembly into the tray; lid+spacers+screws over the switches; caps.
    motion = []
    board_assy = [n_s for n_s in comps if not n_s[0].startswith('switch')]
    stages = [('board-into-tray', board_assy, [('tray', tray)]),
              ('switches-into-sockets', [(n, s) for n, s in comps if n.startswith('switch')], [('tray', tray), ('OLED-max', g['oled_max'])]),
              ('lid-assembly-down', [('lid', lid)] + [(f'spacer-{i+1}', s) for i, s in enumerate(g['spacers'])],
               [(n, s) for n, s in comps if not n.endswith('-rim') and n != 'PCB'] + [('tray', tray)]),
              ('keycaps-down', [(f'keycap-{i+1}', c) for i, c in enumerate(caps)], [('lid', lid)] + [(f'screw-{i+1}', s) for i, s in enumerate(g['screws'])])]
    poses = tests = 0
    tray_motion = tray.cut(block(W, D, 0.5, -0.1))      # the underside text cannot meet anything moving above the floor

    def touches_tray(bb):
        return any(bb.xmin < b[3] and bb.xmax > b[0] and bb.ymin < b[4] and bb.ymax > b[1] and bb.zmin < b[5] and bb.zmax > b[2]
                   for b in g['tray_boxes'])
    for stage, moving, obstacles in stages:
        for step in range(61):
            dz = step * 0.5
            poses += 1
            for n, s in moving:
                lifted = s.translate((0, 0, dz))
                bb = lifted.val().BoundingBox()
                for m, o in obstacles:
                    tests += 1
                    if m == 'tray':
                        if not touches_tray(bb):
                            continue          # exact: the tray is the union of the boxed features
                        o = tray_motion
                    v = overlap(lifted, o)
                    if v > 1e-5:
                        motion.append(dict(stage=stage, dz_mm=dz, a=n, b=m, intersection_mm3=round(v, 6)))
    floor_top = block(W - 2 * WALL, D - 2 * WALL, 0.01, FLOOR - 0.01)
    screw_heads_nominal = [cyl(SCREW_HEAD_D / 2, SCREW_HEAD_H, LID_TOP, x, y) for x, y in g['mounts']]
    dist = {
        'oled_max_to_lid_underside': LID_Z - (g['module_z'] + 3.2),
        'holder_to_floor': g['holder'].val().distance(floor_top.val()),
        'pressed_keycap_to_lid_top_nominal': KEYCAP_B - TRAVEL - LID_TOP,
        'pressed_keycap_to_lid_top_2.3mm_sheet': KEYCAP_B - TRAVEL - (LID_Z + LID_T_RANGE[1]),
        'keycap_to_screw_head_plan': min(c.val().distance(h.translate((0, 0, KEYCAP_B - LID_TOP)).val()) for c in caps for h in screw_heads_nominal),
        'pressed_keycap_roof_to_housing': KEYCAP_ROOF - TRAVEL - HOUSING_TOP,
        'lid_key_hole_to_upper_housing_x': KEY_HOLE[0] / 2 - UPPER_SLOPE_SIDE,
        'lid_key_hole_to_upper_housing_y': KEY_HOLE[1] / 2 - UPPER_HALF_Y,
        'screw_thread_engagement': PCB_Z - (LID_TOP - SCREW_LEN),
        'usb_mouth_to_outer_wall': W / 2 - g['mouth_x'],
        'usb_mouth_to_relief_wall': (W / 2 - WALL + USB_RELIEF[0]) - g['mouth_x'],
        'pcb_side_clearance': GAP,
        'lid_hole_edge_to_lid_edge_min': min(min((W / 2 - LID_INSET) - abs(x), (D / 2 - LID_INSET) - abs(y)) - LID_HOLE / 2 for x, y in g['mounts']),
        'lid_web_between_key_holes': (KEYS[1][0] - KEYS[0][0]) - KEY_HOLE[0],
    }
    capture = {f'switch-{i+1}': rim_capture(lid, x, y) for i, (x, y) in enumerate(KEYS)}
    assert sha(q5.BOARD) == data['board_sha256'] and sha(q5.MODEL) == data['model_sha256'], 'Source changed during build'
    printed = [('tray', tray), ('keycap-count', caps[0]), ('keycap-reset', caps[1])]
    solids = {n: dict(valid=s.val().isValid(), count=len(s.solids().vals()), volume_mm3=round(volume(s), 3)) for n, s in printed + [('lid-acrylic', lid)]}
    report = dict(
        status='Q5A acrylic-lid engineering fit candidate for the ordered Q5 board; physical qualification pending',
        body_mm=[round(W, 3), round(D, 3), round(LID_TOP, 3)], lid_mm=[round(W - 2 * LID_INSET, 3), round(D - 2 * LID_INSET, 3), LID_T],
        lid_thickness_accepted_mm=list(LID_T_RANGE), keycap_top_mm=round(KEYCAP_TOP, 3),
        stack_mm=dict(floor=FLOOR, holder_gap=HOLDER_GAP, holder=HOLDER_H, pcb_bottom=round(PCB_Z, 3), pcb_top=round(PCB_TOP, 3),
                      spacer=SPACER_L, lid_underside=round(LID_Z, 3), lid_top=round(LID_TOP, 3), tray_rim=round(WALL_TOP, 3), reveal=REVEAL),
        walls_mm=dict(wall=WALL, pcb_gap=GAP, r_inner=R_IN, r_outer=R_OUT, lid_inset=LID_INSET, top_chamfer=TOP_CHAMFER, bottom_fillet=BOTTOM_FILLET,
                      usb_relief=dict(depth=USB_RELIEF[0], width=USB_RELIEF[1], reason='J1 mouth is 0.575 mm proud of the PCB edge; the side gap is 0.5 mm')),
        lid=dict(material='clear cast acrylic (PMMA), laser cut, both sides identical', holes=dict(screw=LID_HOLE, key=list(KEY_HOLE)),
                 display_cutout=False, reason='OLED maximum is 0.3 mm below the lid underside; the switch rims already set the lid there, so a cutout saves no height'),
        keycaps=dict(size=KEYCAP, corner_r=KEYCAP_R, underside_above_pcb=round(KEYCAP_B - PCB_TOP, 3), top_above_pcb=round(KEYCAP_TOP - PCB_TOP, 3),
                     cavity=KEYCAP_CAVITY, socket_depth=SOCKET_DEPTH),
        fasteners=dict(screws='4 x M2 x 14 cross pan-head self-tapping (head 3.8 x 1.6) through the lid, spacer and PCB into 1.7 mm tray pilots',
                       spacers='4 x round spacer OD 4.0 / ID 2.2 / L 6.0 (brass or nylon; clear PC also works)', pilot_depth=PILOT_DEPTH),
        rim_capture=capture,
        tolerance_stack_mm=dict(rim_top='6.00 +-0.15 (drawing X.xx general tolerance)', spacer='6.0 +-0.1',
                                result='lid underside to rim: -0.25 (light preload) to +0.25 (switch may lift 0.25 before the lid stops it)',
                                preload_limit='CPG151101D13 push strength 5 kgf, 15 s, no damage'),
        valid_solids=solids, reported_intersections=hits,
        assembly_path_checks=dict(poses=poses, sampled_intersection_tests=tests, step_mm=0.5, max_lift_mm=30, collisions=motion,
                                  limitations='Straight vertical sampled paths; excludes screw driving, cell insertion and print distortion.'),
        minimum_modeled_distances_mm={k: round(v, 4) for k, v in dist.items()},
        source_board_sha256=data['board_sha256'], source_model_sha256=data['model_sha256'],
        generator_sha256=generator_hash, q5_builder_sha256=q5_hash, cadquery_version=cq.__version__, python_version=sys.version.split()[0],
        cad_coordinate_transform='X = PCB_X - 21; Y = 27 - PCB_Y; Z above the tray underside',
        limitations=['Component bodies are envelopes; the switch profile is read from the maker drawing (upper-housing widths +-0.2 mm).',
                     'Rim capture depends on the real upper-housing width; cut the laser coupon first (key holes 15.0/15.2/15.4 x 12.7/12.9/13.1).',
                     'Cast acrylic thickness varies 1.8-2.3 mm; keycap clearance is checked at 2.3 mm.',
                     'Self-tapping thread life in printed pilots, drop behaviour, acrylic stress crazing and USB cable fit are untested.'])
    print(json.dumps({'intersections': hits, 'motion': motion[:8], 'solids': solids, 'distances': report['minimum_modeled_distances_mm'], 'rim_capture': capture}, indent=1), flush=True)
    assert all(v['valid'] and v['count'] == 1 for v in solids.values()), 'Invalid solid'
    assert not hits, f'Resolve modelled intersections: {hits}'
    assert not motion, f'Resolve assembly-path collisions: {motion[:8]}'
    assert dist['oled_max_to_lid_underside'] >= 0.25 and dist['pressed_keycap_to_lid_top_2.3mm_sheet'] >= 0.35
    assert dist['keycap_to_screw_head_plan'] >= 1.0, 'Keycap too close to a lid screw head'
    assert all(c['area_mm2'] > 5 for c in capture.values()), 'Lid does not capture the switch rims'
    export(g, report)


def export(g, report):
    mirror = lambda s: s.mirror('XZ')
    # Printed parts, already in print orientation.
    stl = {'tray-Q5A.stl': g['tray']}
    flip = lambda c, x, y: c.translate((-x, -y, 0)).rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, KEYCAP_TOP))
    stl['keycap-count-Q5A.stl'] = flip(g['keycaps'][0], *KEYS[0])
    stl['keycap-reset-Q5A.stl'] = flip(g['keycaps'][1], *KEYS[1])
    stl['spacer-printable-Q5A.stl'] = g['spacers'][0].translate((-g['mounts'][0][0], -g['mounts'][0][1], -PCB_TOP))
    for name, shape in stl.items():
        cq.exporters.export(mirror(shape), str(OUT / name), tolerance=0.02, angularTolerance=0.1)
    report['stl_mesh_checks'] = {name: q5.mesh_check(OUT / name) for name in stl}
    # Laser file: the lid underside profile in CAD coordinates (seen from above), 1:1 mm.
    lid_face = mirror(g['lid']).faces('<Z').val().translate((0, 0, -LID_Z))
    cq.exporters.export(cq.Workplane('XY').add(lid_face), str(OUT / 'lid-acrylic-Q5A.dxf'))
    write_lid_svg(OUT / 'lid-acrylic-Q5A.svg', g)
    write_coupon(OUT)
    # Assembly STEP for review (envelopes).
    assy = cq.Assembly(name='Count-Fidget-Q5A-acrylic-lid')
    colours = {'tray': '#e9e7e2', 'lid': '#d8f0f4', 'pcb': '#1f6b3a', 'holder': '#ece6d6', 'oled_max': '#1d3f73', 'usb': '#b7bcc0'}
    for key, col in colours.items():
        assy.add(mirror(g[key]), name=key, color=cq.Color(col))
    for i, c in enumerate(g['keycaps'], 1):
        assy.add(mirror(c), name=f'keycap-{i}', color=cq.Color('#f4f3ef'))
    for i, (bot, rim, upper, stem) in enumerate(g['switches'], 1):
        assy.add(mirror(bot.union(rim)), name=f'switch-{i}-base', color=cq.Color('#202326'))
        assy.add(mirror(upper), name=f'switch-{i}-top', color=cq.Color('#dfe8ea'))
        assy.add(mirror(stem), name=f'switch-{i}-stem', color=cq.Color('#35b7e8'))
    for i, (s, sc) in enumerate(zip(g['spacers'], g['screws']), 1):
        assy.add(mirror(s), name=f'spacer-{i}', color=cq.Color('#c9a449'))
        assy.add(mirror(sc), name=f'screw-{i}', color=cq.Color('#9aa3aa'))
    for n, s in g['bottom']:
        assy.add(mirror(s), name=f'env-{n}', color=cq.Color('#3a3f46'))
    assy.export(str(OUT / 'enclosure-Q5A.step'))
    (OUT / 'fit-report.json').write_text(json.dumps(report, indent=2) + '\n')
    names = list(stl) + ['lid-acrylic-Q5A.dxf', 'lid-acrylic-Q5A.svg', 'laser-coupon-Q5A.svg', 'enclosure-Q5A.step', 'fit-report.json']
    manifest = dict(generator=report['generator_sha256'], q5_builder=report['q5_builder_sha256'], board=report['source_board_sha256'],
                    model=report['source_model_sha256'], outputs={n: sha(OUT / n) for n in names})
    (OUT / 'build-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(report['minimum_modeled_distances_mm'], indent=1))


def _rr_path(cx, cy, w, h, r):
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    r = round(r, 4)
    return (f'M{x0 + r:.4f},{y0:.4f} H{x1 - r:.4f} A{r:g},{r:g} 0 0 1 {x1:.4f},{y0 + r:.4f} V{y1 - r:.4f} '
            f'A{r:g},{r:g} 0 0 1 {x1 - r:.4f},{y1:.4f} H{x0 + r:.4f} A{r:g},{r:g} 0 0 1 {x0:.4f},{y1 - r:.4f} V{y0 + r:.4f} '
            f'A{r:g},{r:g} 0 0 1 {x0 + r:.4f},{y0:.4f} Z')


def write_lid_svg(path, g):
    """Laser file in the common service convention: 1 user unit = 1 mm, red hairline = cut.
    Drawn in the top-view frame (display at the top of the sheet); both lid faces are identical."""
    lw, ld = W - 2 * LID_INSET, D - 2 * LID_INSET
    m = 2.0
    cx, cy = lw / 2 + m, ld / 2 + m
    items = [_rr_path(cx, cy, lw, ld, R_OUT - LID_INSET)]
    for x, y in g['mounts']:
        items.append(f'M{cx + x - LID_HOLE / 2:.4f},{cy + y:.4f} a{LID_HOLE / 2:g},{LID_HOLE / 2:g} 0 1 0 {LID_HOLE:g},0 a{LID_HOLE / 2:g},{LID_HOLE / 2:g} 0 1 0 {-LID_HOLE:g},0 Z')
    for x, y in KEYS:
        items.append(_rr_path(cx + x, cy + y, KEY_HOLE[0], KEY_HOLE[1], KEY_HOLE[2]))
    body = '\n'.join(f'  <path d="{d}" fill="none" stroke="#ff0000" stroke-width="0.01"/>' for d in items)
    sw, sh = lw + 2 * m, ld + 2 * m
    path.write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="{sw:.3f}mm" height="{sh:.3f}mm" viewBox="0 0 {sw:.3f} {sh:.3f}">\n'
                    f'  <!-- Count Fidget Q5A lid: clear cast acrylic 2.0 mm, 1 part. Red = cut. Finished sizes; kerf compensation by the cutter. -->\n{body}\n</svg>\n')


def write_coupon(out):
    """Laser test strip: three key-hole sizes around the nominal and three screw holes."""
    holes = [(15.0, 12.7), (15.2, 12.9), (15.4, 13.1)]
    m, pitch, frame = 3.0, 19.0, 1.0
    w, h = 2 * m + 2 * pitch + 15.4, 25.0
    items = [_rr_path(frame + w / 2, frame + h / 2, w, h, 1.5)]
    for i, (a, b) in enumerate(holes):
        items.append(_rr_path(frame + m + 7.7 + i * pitch, frame + 9.5, a, b, KEY_HOLE[2]))
    for i, d in enumerate((2.3, 2.4, 2.5)):
        x = frame + m + 7.7 + i * pitch
        items.append(f'M{x - d / 2:.4f},{frame + 20.5:.4f} a{d / 2:g},{d / 2:g} 0 1 0 {d:g},0 a{d / 2:g},{d / 2:g} 0 1 0 {-d:g},0 Z')
    body = '\n'.join(f'  <path d="{d}" fill="none" stroke="#ff0000" stroke-width="0.01"/>' for d in items)
    sw, sh = w + 2 * frame, h + 2 * frame
    (out / 'laser-coupon-Q5A.svg').write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="{sw:.3f}mm" height="{sh:.3f}mm" viewBox="0 0 {sw:.3f} {sh:.3f}">\n'
                                              f'  <!-- Key holes 15.0x12.7 / 15.2x12.9 (nominal) / 15.4x13.1; screw holes 2.3 / 2.4 (nominal) / 2.5. Cut from the lid sheet. -->\n{body}\n</svg>\n')


if __name__ == '__main__':
    main()
