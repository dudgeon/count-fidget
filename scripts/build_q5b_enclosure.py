#!/usr/bin/env python3
"""Q5B: printed bezel tray + one-piece clear acrylic faceplate on four screws + hidden MX switch plate, for the locked Q5 board.

Successor to Q5A (mechanical/q5-acrylic), after the owner's review on 24 Nov 2026:
  * keys are Kailh Box Jade (3-pin, plate mount) with standard MX keycaps, not the HanElectricity
    switch with printed tiles, so the lid can no longer rely on a raised switch rim;
  * the tray forms a thin bezel around the laser-cut parts, walls are thicker, bottom edge chamfered;
  * fasteners are ordinary M2 machine screws into hex nuts captive in pockets under the tray;
  * spacers are printable.

Two laser-cut parts replace the Q5A lid:
  plate  - hidden 1.5 mm plate at the standard MX plate height (top = PCB top + 5.0) with 14.0 mm cut-outs.
           Every MX/Box switch clips into it, so switch retention no longer depends on a rim overlap.
           It rests on two tray posts below the keys and is clamped there by the lower faceplate screws;
           printed pegs in the board's lower holes locate it and hold the board down.
  window - one-piece 4.5 mm clear faceplate (3/16 in accepted) over the whole top, underside PCB top + 6.7
           (1.0 mm over the OLED maximum), one well round both keycaps. Four M2 x 18 screws go through it:
           two in the board's upper holes on 6.7 mm spacers, two on the tray posts below the keys on 1.7 mm
           spacers (the board's lower holes leave only 0.3 mm of acrylic to the key well).

Stack (Z above the tray underside, mm):
  floor 1.2 | PCB 7.22-8.82 | plate 12.32-13.82 | faceplate 15.52-20.02 | tray top 20.02
  Body 47.0 x 64.0 mm.

Geometry is built in the Q5 builder frame (X = PCB_X - 21, Y = PCB_Y - 27, Y down) and exported mirrored to
right-handed CAD coordinates (Y = 27 - PCB_Y). Board envelopes are reused read-only from the Q5A generator.
Requires CadQuery 2.8 and a KiCad 10 Python (pcbnew) passed with --kicad-python.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_q5_enclosure as q5            # noqa: E402  board reader, helpers, mesh check (read-only)
import build_q5_acrylic_enclosure as q5a   # noqa: E402  board/component envelopes on the same stack (read-only)

OUT = ROOT / 'mechanical/q5b'
FONT = q5a.FONT
block, rounded, cyl, overlap, volume, sha = q5.block, q5.rounded, q5.cyl, q5.overlap, q5.volume, q5.sha

# ---- stack (board datum identical to Q5A) ---------------------------------------
FLOOR, PCB_Z, PCB_TOP, PCB_T = q5a.FLOOR, q5a.PCB_Z, q5a.PCB_TOP, q5a.PCB_T
PLATE_T = 1.5                       # standard MX plate thickness; Box clips are made for 1.5
PLATE_TOP = PCB_TOP + 5.0           # MX standard: PCB top to plate top 5.0
PLATE_Z = PLATE_TOP - PLATE_T       # = PCB top + 3.5 (lower spacer length)
LOW_SPACER = PLATE_Z - PCB_TOP
WIN_Z = PCB_TOP + 6.7               # faceplate underside: 1.0 mm over the OLED maximum (PCB top + 5.7), 0.1 mm over the lower screw heads
HIGH_SPACER = WIN_Z - PCB_TOP
WIN_T, WIN_T_RANGE = 4.5, (4.3, 5.0)   # cast sheet; datum is the underside. 3/16 in (4.76) is inside the range
WIN_TOP = WIN_Z + WIN_T
TOP = WIN_TOP                       # bezel top flush with the nominal window top

# ---- tray -------------------------------------------------------------------------
GAP, WALL = 0.5, 2.0                # board clearance; wall = 5 x 0.4 mm perimeters
BEZEL = 1.2                         # wall left beside the laser parts (3 perimeters)
CLEAR = 0.25                        # laser part to bezel, each side
PART_HOLE = 2.4
W = 42 + 2 * (GAP + WALL)            # 47.0
Y_TOP = -(27 + GAP + WALL)           # -29.5: display end, as Q5A/Q5B v1
# Four screws through the one faceplate. The lower pair cannot use the board's lower holes (+-18.5, 25): a hole there
# leaves 0.3 mm of acrylic to the key well. They sit just below the keys instead, outside the board edge, on tray posts.
FACE_LOW_Y = 27 + GAP + 2.2          # 29.7: post (R2.2) clears the board edge by the board gap
FACE_LOW = [(-18.5, FACE_LOW_Y), (18.5, FACE_LOW_Y)]
PART_BOT_Y = FACE_LOW_Y + PART_HOLE / 2 + 2.15          # 33.05: faceplate/plate bottom edge
Y_BOT = PART_BOT_Y + 0.25 + 1.2      # 34.5 (CLEAR + BEZEL)
D = Y_BOT - Y_TOP                    # 64.0
YC = (Y_TOP + Y_BOT) / 2             # 2.5: tray centre offset (board frame)
R_IN = 1.4
R_OUT = R_IN + WALL
R_POCKET = R_OUT - BEZEL
TOP_CHAMFER, BOTTOM_CHAMFER = 0.4, 1.0
SPLIT_Y = 4.2                       # board-frame Y where the window pocket (above) meets the key well (below)
LEDGE_DROP = 0.1                    # printed ledges sit just under the laser parts: spacers, not the print, set heights
USB_RELIEF = (0.4, 10.0)
GUSSET_TOP = FLOOR + 3.3

# ---- laser parts ------------------------------------------------------------------
PART_HALF_W = W / 2 - BEZEL - CLEAR                     # 22.05
PART_TOP_Y = Y_TOP + BEZEL + CLEAR                      # -28.05
WELL = (2 * (abs(q5.KEYS[0][0]) + 9.1 + 0.6), 18.2 + 2 * 0.6, 1.0)   # key well in the faceplate: 1u caps + 0.6 mm all round
PLATE_EDGE_Y = 4.45                 # plate top edge: 0.5 mm clear of the OLED module footprint
SWITCH_CUT, SWITCH_CUT_R = 14.0, 0.3

# ---- keys: Kailh Box Jade + standard 1u MX keycap (envelopes, not vendor CAD) ------
KEYS, KEY_ROT = q5.KEYS, q5.KEY_ROT                     # (+-9.525, 13.8): 19.05 mm pitch
HOUSING_BOTTOM = 13.95
TOP_HOUSING_BASE, TOP_HOUSING_TIP = 15.6, 13.0
HOUSING_TOP = PCB_TOP + 11.6
STEM_TOP = PCB_TOP + 15.2
TRAVEL = 4.0                         # Box Jade 3.6 +-0.4 total travel
CAP_BASE, CAP_TIP, CAP_R = 18.2, 13.0, 1.0
CAP_B = PCB_TOP + 11.0               # skirt underside at rest, OEM R3-like (user's caps not measured)
CAP_H = 9.4
CAP_WOBBLE = 0.3

# ---- fasteners (hardware-store parts) ----------------------------------------------
HEAD_D, HEAD_H = 4.0, 1.6            # M2 pan head, ISO 7045 / DIN 7985 (largest common)
NUT_AF, NUT_H = 4.0, 1.6             # M2 hex nut, ISO 4032
NUT_POCKET_AF = 4.15                 # snug for PETG; nut pressed in from below
HOLE_R = 1.2                         # 2.4 clearance through the bosses
BOSS_R, BOSS_BASE_R = 2.2, 3.7
UPPER = dict(len=18.0, head_z=WIN_TOP, nut_top=3.7)     # through faceplate, 6.7 spacer, PCB, tray boss
LOWER = dict(len=18.0, head_z=WIN_TOP, nut_top=3.7)     # through faceplate, 1.7 spacer, plate, tray post (outside the board)
PEG_PIN_R = 0.95                     # locating pegs in the board's lower holes: 1.9 pins into the 2.2 / 2.4 holes


def rrect(w, d, r, h, z, x=0, y=0):
    return block(w, d, h, z, x, y).edges('|Z').fillet(r)


def span(y0, y1, h, z, x0=-22.05, x1=22.05, r_top=0.0, r_bot=0.0):
    """Laser-part outline from y0 (top, board frame) to y1, with separate corner radii."""
    pts = cq.Workplane('XY').rect(x1 - x0, y1 - y0).extrude(h).translate(((x0 + x1) / 2, (y0 + y1) / 2, z))
    if r_top:
        pts = pts.edges('|Z and <Y').fillet(r_top)
    if r_bot:
        pts = pts.edges('|Z and >Y').fillet(r_bot)
    return pts


def hexagon(af, h, z, x, y):
    return cq.Workplane('XY').polygon(6, af / math.cos(math.radians(30))).extrude(h).translate((x, y, z))


def switch_envelope(x, y):
    bottom = rrect(HOUSING_BOTTOM, HOUSING_BOTTOM, 0.5, PLATE_TOP - PCB_TOP, PCB_TOP, x, y)   # MX housings have relieved corners
    upper = (cq.Workplane('XY').workplane(offset=PLATE_TOP).rect(TOP_HOUSING_BASE, TOP_HOUSING_BASE)
             .workplane(offset=HOUSING_TOP - PLATE_TOP).rect(TOP_HOUSING_TIP, TOP_HOUSING_TIP).loft().translate((x, y, 0)))
    stem = block(4.0, 1.3, STEM_TOP - HOUSING_TOP, HOUSING_TOP, x, y).union(block(1.1, 4.0, STEM_TOP - HOUSING_TOP, HOUSING_TOP, x, y))
    return bottom, upper, stem


def _rounded_wire(w, r, z):
    face = cq.Sketch().rect(w, w).vertices().fillet(r)._faces.Faces()[0]
    return face.outerWire().translate(cq.Vector(0, 0, z))


def keycap(x, y, base=CAP_BASE):
    """Standard 1u keycap envelope: tapered shell, open underneath, cross boss to the stem."""
    outer = cq.Workplane('XY').add(cq.Solid.makeLoft([_rounded_wire(base, CAP_R, CAP_B), _rounded_wire(CAP_TIP, 2.0, CAP_B + CAP_H)], True))
    inner = cq.Workplane('XY').add(cq.Solid.makeLoft([_rounded_wire(base - 2.4, 0.6, CAP_B - 0.01),
                                                      _rounded_wire(CAP_TIP - 1.6, 1.2, STEM_TOP + 0.4)], True))
    cap = outer.cut(inner)
    boss_z = STEM_TOP - 3.8
    cap = cap.union(cyl(2.75, STEM_TOP + 0.5 - boss_z, boss_z))
    return cap.translate((x, y, 0))


def make_window(mounts, t=WIN_T):
    """One-piece clear faceplate over the whole top: covers the display, one well round both keycaps,
    four screw holes (two upper board holes, two posts below the keys)."""
    win = rrect(2 * PART_HALF_W, PART_BOT_Y - PART_TOP_Y, R_POCKET - CLEAR, t, WIN_Z, 0, (PART_TOP_Y + PART_BOT_Y) / 2)
    for x, y in mounts:
        win = win.cut(cyl(PART_HOLE / 2, t + 1, WIN_Z - 0.5, x, y))
    win = win.cut(rrect(WELL[0], WELL[1], WELL[2], t + 1, WIN_Z - 0.5, 0, KEYS[0][1]))
    return win


def make_plate(points):
    """Hidden switch plate: clamped between the lower tray posts and the faceplate's 1.7 mm spacers by the two lower
    faceplate screws; the pegs in the board's lower holes locate it and hold the board down."""
    plate = span(PLATE_EDGE_Y, PART_BOT_Y, PLATE_T, PLATE_Z, -PART_HALF_W, PART_HALF_W, r_top=0.5, r_bot=R_POCKET - CLEAR)
    for x, y in points:
        plate = plate.cut(cyl(PART_HOLE / 2, PLATE_T + 1, PLATE_Z - 0.5, x, y))
    for x, y in KEYS:
        plate = plate.cut(rrect(SWITCH_CUT, SWITCH_CUT, SWITCH_CUT_R, PLATE_T + 1, PLATE_Z - 0.5, x, y))
    return plate


def fastener(x, y, spec):
    screw = cyl(1.0, spec['len'], spec['head_z'] - spec['len'], x, y).union(cyl(HEAD_D / 2, HEAD_H, spec['head_z'], x, y))
    nut = hexagon(NUT_AF, NUT_H, spec['nut_top'] - NUT_H, x, y).cut(cyl(1.0, NUT_H + 1, spec['nut_top'] - NUT_H - 0.5, x, y))
    return screw, nut


def build(refs):
    env = q5a.build(refs)            # board, components, envelopes on the identical stack
    board_mounts = env['mounts']
    upper = [m for m in board_mounts if m[1] < 0]
    pegs_at = [m for m in board_mounts if m[1] > 0]
    mounts = upper + FACE_LOW        # the four faceplate screws
    usb_y, usb_axis = env['usb_y'], env['usb_axis']
    g = {k: env[k] for k in ('pcb', 'holder', 'oled_max', 'oled_header', 'usb', 'mcu', 'usb_plug', 'bottom', 'tails', 'module_z', 'mouth_x')}
    g['mounts'], g['board_mounts'], g['peg_points'], g['usb_y'] = mounts, board_mounts, pegs_at, usb_y
    spec = {m: (UPPER if m[1] < 0 else LOWER) for m in mounts}
    clip = rounded(W - 0.2, D - 0.2, TOP, 0, r=R_OUT - 0.1, y=YC)
    # ---- tray ----
    tray = rounded(W, D, TOP, r=R_OUT, y=YC)
    tray = tray.faces('>Z').edges().chamfer(TOP_CHAMFER)
    tray = tray.faces('<Z').edges().chamfer(BOTTOM_CHAMFER)
    tray = tray.cut(rounded(W - 2 * WALL, D - 2 * WALL, TOP, FLOOR, r=R_IN, y=YC))
    pocket = rounded(W - 2 * BEZEL, D - 2 * BEZEL, TOP, 0, r=R_POCKET, y=YC)
    win_ledge, plate_ledge = WIN_Z - LEDGE_DROP, PLATE_Z - LEDGE_DROP
    tray = tray.cut(pocket.intersect(block(W, SPLIT_Y - Y_TOP, TOP, win_ledge, 0, (SPLIT_Y + Y_TOP) / 2)))
    tray = tray.cut(pocket.intersect(block(W, Y_BOT - SPLIT_Y, TOP, plate_ledge, 0, (SPLIT_Y + Y_BOT) / 2)))
    iw = W / 2 - WALL
    boxes = [(-W / 2, Y_TOP, 0, W / 2, Y_BOT, FLOOR),
             (-W / 2, Y_TOP, 0, -iw + R_IN, Y_BOT, TOP), (iw - R_IN, Y_TOP, 0, W / 2, Y_BOT, TOP),
             (-W / 2, Y_TOP, 0, W / 2, Y_TOP + WALL + R_IN, TOP), (-W / 2, Y_BOT - WALL - R_IN, 0, W / 2, Y_BOT, TOP)]

    def gusset(x, y):
        cx, cy = math.copysign(21 + GAP, x), math.copysign(27 + GAP, y)
        ang = math.degrees(math.atan2(cy - y, cx - x))
        length = math.hypot(cx - x, cy - y) + 0.6
        return (block(length, 1.2, GUSSET_TOP - FLOOR, FLOOR).translate((length / 2, 0, 0))
                .rotate((0, 0, 0), (0, 0, 1), ang).translate((x, y, 0))).intersect(clip)
    for x, y in board_mounts:        # bosses under all four board holes (upper: screw + nut; lower: peg support)
        tray = tray.union(cyl(BOSS_R, PCB_Z - FLOOR, FLOOR, x, y))
        if y < 0:
            tray = tray.union(cyl(BOSS_BASE_R, spec[(x, y)]['nut_top'] + 1.2 - FLOOR, FLOOR, x, y).intersect(clip))
        r = BOSS_BASE_R if y < 0 else BOSS_R
        boxes.append((min(x, math.copysign(21 + GAP, x)) - r, min(y, math.copysign(27 + GAP, y)) - r, 0,
                      max(x, math.copysign(21 + GAP, x)) + r, max(y, math.copysign(27 + GAP, y)) + r, PCB_Z))
        tray = tray.union(gusset(x, y))
    for x, y in FACE_LOW:            # posts outside the board edge, up to the plate underside, tied into the end wall
        tray = tray.union(cyl(BOSS_R, PLATE_Z - FLOOR, FLOOR, x, y))
        tray = tray.union(block(2 * BOSS_R, Y_BOT - WALL + 0.5 - y, PLATE_Z - FLOOR, FLOOR, x, (y + Y_BOT - WALL + 0.5) / 2).intersect(clip))
        tray = tray.union(cyl(BOSS_BASE_R, spec[(x, y)]['nut_top'] + 1.2 - FLOOR, FLOOR, x, y).intersect(clip))
        boxes.append((x - BOSS_BASE_R, y - BOSS_BASE_R, 0, x + BOSS_BASE_R, Y_BOT, PLATE_Z))
    for x, y in mounts:
        s = spec[(x, y)]
        tray = tray.cut(cyl(HOLE_R, PLATE_Z + 0.1, -0.05, x, y))
        tray = tray.cut(hexagon(NUT_POCKET_AF, s['nut_top'] + 0.05, -0.05, x, y))
    for x, y in q5.LOAD_SUPPORTS:
        tray = tray.union(cyl(1.3, PCB_Z - FLOOR, FLOOR, x, y))
        boxes.append((x - 1.3, y - 1.3, 0, x + 1.3, y + 1.3, PCB_Z))
    usb_cut = (cq.Workplane('YZ').rect(13.4, 7.2).extrude(10).edges('|X').fillet(1.0)
               .translate((W / 2 - WALL - 3, usb_y, usb_axis)))
    tray = tray.cut(usb_cut)
    tray = tray.cut(block(USB_RELIEF[0] + 1, USB_RELIEF[1], TOP, usb_axis, W / 2 - WALL - 1 + USB_RELIEF[0] / 2 + 0.5, usb_y))
    tray = tray.union(block(3, 5, PCB_Z - 3.31 - 0.15 - FLOOR, FLOOR, 17, usb_y))
    tray = tray.union(block(0.8, 5, PCB_Z - 1.0 - FLOOR, FLOOR, 13.675, usb_y))
    boxes.append((13.275, usb_y - 2.5, 0, 18.5, usb_y + 2.5, PCB_Z))
    rx, ry = refs['SW3']['x'] - 21, refs['SW3']['y'] - 27
    tube_top = PCB_Z - 2.2 - 0.8
    tray = tray.union(cyl(1.65, tube_top - FLOOR, FLOOR, rx, ry)).cut(cyl(0.65, tube_top + 0.1, -0.05, rx, ry))
    boxes.append((rx - 1.65, ry - 1.65, 0, rx + 1.65, ry + 1.65, tube_top))
    warn = None
    for line, size, dy in (('LIR2032 ONLY', 2.6, 11.5), ('rechargeable - never CR2032', 1.7, 8.0)):
        t = (cq.Workplane('XY').text(line, size, 0.45, fontPath=FONT, halign='center', valign='center')
             .translate((0, Y_TOP + dy, -0.05)))   # reads correctly from below after the CAD-frame mirror
        warn = t if warn is None else warn.union(t)
    bb = warn.val().BoundingBox()
    assert bb.xlen < W - 2 * (BOTTOM_CHAMFER + 3), f'Underside text too wide: {bb.xlen:.1f} mm'
    tray = tray.cut(warn)
    g['tray'], g['tray_boxes'] = tray, boxes
    # ---- laser parts, keys, fasteners ----
    g['window'] = make_window(mounts)
    g['plate'] = make_plate(FACE_LOW + pegs_at)
    g['switches'] = [switch_envelope(x, y) for x, y in KEYS]
    g['keycaps'] = [keycap(x, y) for x, y in KEYS]
    g['spacers'] = []
    g['screws'], g['nuts'] = [], []
    for x, y in mounts:
        bot = PCB_TOP if y < 0 else PLATE_TOP
        g['spacers'].append(cyl(2.0, WIN_Z - bot, bot, x, y).cut(cyl(1.15, WIN_Z - bot + 1, bot - 0.5, x, y)))
        sc, nut = fastener(x, y, spec[(x, y)])
        g['screws'].append(sc)
        g['nuts'].append(nut)
    g['pegs'] = [cyl(2.0, PLATE_Z - PCB_TOP, PCB_TOP, x, y).union(cyl(PEG_PIN_R, 1.4, PCB_TOP - 1.4, x, y))
                 .union(cyl(PEG_PIN_R, PLATE_T - 0.2, PLATE_Z, x, y)) for x, y in pegs_at]
    g['spec'] = spec
    return g


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
    data, refs = q5.read_board(args.kicad_python)
    g = build(refs)
    tray, win, plate, caps = g['tray'], g['window'], g['plate'], g['keycaps']
    comps = ([('PCB', g['pcb']), ('holder', g['holder']), ('OLED-max', g['oled_max']), ('OLED-header', g['oled_header']),
              ('USB', g['usb']), ('MCU', g['mcu'])] + g['bottom'] + g['tails'])
    sw = []
    for i, (bot, upper, stem) in enumerate(g['switches'], 1):
        sw += [(f'switch-{i}-bottom', bot), (f'switch-{i}-upper', upper), (f'switch-{i}-stem', stem)]
    spacers = [(f'spacer-{i+1}', s) for i, s in enumerate(g['spacers'])]
    screws = [(f'screw-{i+1}', s) for i, s in enumerate(g['screws'])]
    nuts = [(f'nut-{i+1}', s) for i, s in enumerate(g['nuts'])]
    pegs = [(f'peg-{i+1}', s) for i, s in enumerate(g['pegs'])]
    hits = []

    def check(a, sa, b, sb, tol=1e-5):
        v = overlap(sa, sb)
        if v > tol:
            hits.append(dict(a=a, b=b, intersection_mm3=round(v, 6)))
    # Tray: clear of every component, switch, laser part, spacer, screw and nut (screws pass clearance holes).
    for n, s in comps + sw + [('USB-plug-access', g['usb_plug']), ('window', win), ('plate', plate)] + spacers + screws + nuts + pegs:
        if n != 'PCB':
            check('tray', tray, n, s)
    for n, s in comps + pegs + [('USB-plug-access', g['usb_plug'])]:
        for (m, sc), pt in zip(screws, g['mounts']):
            if n != 'PCB' or pt[1] > 0:          # the lower screws pass outside the board, so check them against it too
                check(m, sc, n, s)
    for part, shape in (('window', win), ('plate', plate)):
        for n, s in comps + sw + screws + pegs:
            if n == 'PCB' or (part == 'plate' and n.startswith('peg')):
                continue
            check(part, shape, n, s)
    check('window', win, 'plate', plate)
    for n, s in spacers + pegs:
        for m, o in sw + comps:
            if m != 'PCB' or n.startswith('spacer'):
                check(n, s, m, o)
    # Keycaps at rest and pressed (full travel, plus wobble as a 0.3 mm larger skirt) against our parts.
    thick_win = make_window(g['mounts'], WIN_T_RANGE[1])
    for i, (x, y) in enumerate(KEYS, 1):
        for state, dz, base in (('rest', 0, CAP_BASE), ('pressed', -TRAVEL, CAP_BASE + 2 * CAP_WOBBLE)):
            c = keycap(x, y, base).translate((0, 0, dz))
            for n, s in [('tray', tray), ('window-thickest', thick_win), ('plate', plate)] + screws:
                check(f'keycap-{i}-{state}', c, n, s)
    # Straight vertical assembly paths (lift 0-30 mm in 0.5 mm steps).
    motion, poses, tests = [], 0, 0
    tray_motion = tray.cut(block(W, D, 0.6, -0.1))

    def touches_tray(bb):
        return any(bb.xmin < b[3] and bb.xmax > b[0] and bb.ymin < b[4] and bb.ymax > b[1] and bb.zmin < b[5] and bb.zmax > b[2]
                   for b in g['tray_boxes'])
    others = [n_s for n_s in comps if n_s[0] != 'PCB']
    stages = [('board-into-tray', comps, [('tray', tray)]),
              ('pegs', pegs, others + [('tray', tray)]),
              ('plate-with-switches', [('plate', plate)] + sw, others + pegs + [('tray', tray)]),
              ('faceplate-with-spacers', [('window', win)] + spacers, others + sw + pegs + [('plate', plate), ('tray', tray)]),
              ('screws', screws, [('window', win), ('plate', plate), ('tray', tray)] + pegs),
              ('keycaps', [(f'keycap-{i+1}', c) for i, c in enumerate(caps)], [('window', win), ('plate', plate), ('tray', tray)] + screws)]
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
                            continue
                        o = tray_motion
                    v = overlap(lifted, o)
                    if v > 1e-5:
                        motion.append(dict(stage=stage, dz_mm=dz, a=n, b=m, intersection_mm3=round(v, 6)))
    # Distances that matter for the review.
    heads = [cyl(HEAD_D / 2, HEAD_H, g['spec'][m]['head_z'], *m) for m in g['mounts']]
    cap_skirts = [rrect(CAP_BASE, CAP_BASE, CAP_R, 0.01, 0, x, y) for x, y in KEYS]
    head_rings = [cyl(HEAD_D / 2, 0.01, 0, *m) for m in g['mounts']]
    floor_top = block(W - 2 * WALL, D - 2 * WALL, 0.01, FLOOR - 0.01)
    engage = {}
    for m in g['mounts']:
        s = g['spec'][m]
        tip = s['head_z'] - s['len']
        for t in WIN_T_RANGE + (4.7625,):
            shift = t - WIN_T
            nut_bottom = s['nut_top'] - NUT_H
            engage[f"{'upper' if m[1] < 0 else 'lower'}@{t}"] = dict(
                thread_in_nut=round(min(NUT_H, s['nut_top'] - (tip + shift)), 3),
                tip_below_nut=round(nut_bottom - (tip + shift), 3), tip_above_underside=round(tip + shift, 3))
    dist = {
        'oled_max_to_window_underside': WIN_Z - (g['module_z'] + 3.2),
        'holder_to_floor': g['holder'].val().distance(floor_top.val()),
        'keycap_skirt_rest_above_window_top': CAP_B - WIN_TOP,
        'keycap_skirt_pressed_above_plate_top': CAP_B - TRAVEL - PLATE_TOP,
        'keycap_to_screw_head_plan': min(c.val().distance(h.val()) for c in cap_skirts for h in head_rings),
        'keycap_to_faceplate_well_plan': (WELL[1] - CAP_BASE) / 2,
        'faceplate_lower_hole_to_well': FACE_LOW_Y - PART_HOLE / 2 - (KEYS[0][1] + WELL[1] / 2),
        'faceplate_strip_below_well': PART_BOT_Y - (KEYS[0][1] + WELL[1] / 2),
        'lower_post_to_board_edge': FACE_LOW_Y - BOSS_R - 27,
        'faceplate_side_rail': PART_HALF_W - WELL[0] / 2,
        'plate_edge_to_oled_footprint': PLATE_EDGE_Y - 3.95,
        'keycap_top_above_bezel': CAP_B + CAP_H - TOP,
        'part_hole_edge_to_part_edge_min': min(min(PART_HALF_W - abs(x), (y - PART_TOP_Y) if y < 0 else (PART_BOT_Y - y)) - PART_HOLE / 2
                                               for x, y in g['mounts']),
        'plate_switch_cutout_web': (KEYS[1][0] - KEYS[0][0]) - SWITCH_CUT,
        'plate_top_edge_to_cutout': (KEYS[0][1] - SWITCH_CUT / 2) - PLATE_EDGE_Y,
        'usb_mouth_to_outer_wall': W / 2 - g['mouth_x'],
        'pcb_side_clearance': GAP,
    }
    assert sha(q5.BOARD) == data['board_sha256'] and sha(q5.MODEL) == data['model_sha256'], 'Source changed during build'
    solids = {n: dict(valid=s.val().isValid(), count=len(s.solids().vals()), volume_mm3=round(volume(s), 3))
              for n, s in (('tray', tray), ('window', win), ('plate', plate), ('spacer-6.7', g['spacers'][0]),
                           ('spacer-1.7', g['spacers'][-1]), ('peg', g['pegs'][0]))}
    report = dict(
        status='Q5B engineering fit candidate for the ordered Q5 board (Kailh Box Jade, standard MX keycaps); physical qualification pending',
        body_mm=[round(W, 3), round(D, 3), round(TOP, 3)],
        keycap_top_mm=round(CAP_B + CAP_H, 3),
        stack_mm=dict(floor=FLOOR, pcb_bottom=round(PCB_Z, 3), pcb_top=round(PCB_TOP, 3), plate=[round(PLATE_Z, 3), round(PLATE_TOP, 3)],
                      window=[round(WIN_Z, 3), round(WIN_TOP, 3)], tray_top=round(TOP, 3)),
        walls_mm=dict(wall=WALL, pcb_gap=GAP, bezel=BEZEL, part_clearance=CLEAR, r_outer=R_OUT, top_chamfer=TOP_CHAMFER,
                      bottom_chamfer=BOTTOM_CHAMFER, ledge_drop=LEDGE_DROP),
        window=dict(material='clear cast acrylic', thickness=WIN_T, accepted=list(WIN_T_RANGE),
                    outline=[round(2 * PART_HALF_W, 3), round(-2 * PART_TOP_Y, 3)], key_well=list(WELL), holes=PART_HOLE),
        plate=dict(material='hidden: black cast acrylic (laser) or printed PETG (plate-printable-Q5B.stl)', thickness=PLATE_T,
                   outline=[round(2 * PART_HALF_W, 3), round(PART_BOT_Y - PLATE_EDGE_Y, 3)], switch_cutout=SWITCH_CUT, holes=PART_HOLE),
        fasteners=dict(upper='2 x M2 x 18 pan-head machine screw (ISO 7045/DIN 7985) through faceplate, 6.7 mm spacer, PCB upper holes, tray boss',
                       lower='2 x M2 x 18 pan-head machine screw through faceplate, 1.7 mm spacer, plate, tray post below the keys (outside the board)',
                       nuts=f'4 x M2 hex nut (4.0 AF x 1.6) in hex pockets {NUT_POCKET_AF} AF open to the underside',
                       spacers='2 x 6.7 mm + 2 x 1.7 mm, OD 4.0 / ID 2.3, printed (spacer-6.7-Q5B.stl, spacer-1.7-Q5B.stl)',
                       pegs='2 x printed 3.5 mm locating pegs (OD 4.0, 1.9 mm pins) in the board lower holes: hold the board down under the plate (peg-3.5-Q5B.stl)',
                       thread_engagement_mm=engage),
        valid_solids=solids, reported_intersections=hits,
        assembly_path_checks=dict(poses=poses, sampled_intersection_tests=tests, step_mm=0.5, max_lift_mm=30, collisions=motion,
                                  limitations='Straight vertical sampled paths; excludes screw driving, nut insertion and print distortion.'),
        minimum_modeled_distances_mm={k: round(v, 4) for k, v in dist.items()},
        source_board_sha256=data['board_sha256'], source_model_sha256=data['model_sha256'],
        generator_sha256=sha(Path(__file__)), q5a_generator_sha256=sha(ROOT / 'scripts/build_q5_acrylic_enclosure.py'),
        cadquery_version=cq.__version__, python_version=sys.version.split()[0],
        cad_coordinate_transform='X = PCB_X - 21; Y = 27 - PCB_Y; Z above the tray underside',
        limitations=['Box Jade and keycap bodies are envelopes from MX/Box standard dimensions, not vendor drawings; '
                     'the keycap skirt height (PCB top + 11.0 at rest) is an OEM-R3-like estimate. Measure the real caps.',
                     'Plate cut-out fit (14.0 mm) depends on the laser kerf: cut the coupon first.',
                     'Nut-pocket fit, drop behaviour, acrylic crazing at the screw holes and USB cable fit are untested.'])
    print(json.dumps({'intersections': hits, 'motion': motion[:10], 'solids': solids, 'distances': report['minimum_modeled_distances_mm'],
                      'engagement': engage}, indent=1), flush=True)
    assert all(v['valid'] and v['count'] == 1 for v in solids.values()), 'Invalid solid'
    assert not hits, f'Resolve modelled intersections: {hits}'
    assert not motion, f'Resolve assembly-path collisions: {motion[:8]}'
    assert dist['oled_max_to_window_underside'] >= 0.25
    assert all(v['thread_in_nut'] >= 1.0 and v['tip_above_underside'] >= 0.0 for v in engage.values()), engage
    export(g, report)


def _rr_path(cx, cy, w, h, r):
    return q5a._rr_path(cx, cy, w, h, r)


def _circle(x, y, d):
    return f'M{x - d / 2:.4f},{y:.4f} a{d / 2:g},{d / 2:g} 0 1 0 {d:g},0 a{d / 2:g},{d / 2:g} 0 1 0 {-d:g},0 Z'


def _outline(x0, y0, x1, y1, rt, rb):
    """Rectangle (SVG frame, y down) with top corners rt and bottom corners rb."""
    return (f'M{x0 + rt:.4f},{y0:.4f} H{x1 - rt:.4f} A{rt:g},{rt:g} 0 0 1 {x1:.4f},{y0 + rt:.4f} V{y1 - rb:.4f} '
            f'A{rb:g},{rb:g} 0 0 1 {x1 - rb:.4f},{y1:.4f} H{x0 + rb:.4f} A{rb:g},{rb:g} 0 0 1 {x0:.4f},{y1 - rb:.4f} V{y0 + rt:.4f} '
            f'A{rt:g},{rt:g} 0 0 1 {x0 + rt:.4f},{y0:.4f} Z')


def write_svg(path, title, y0, y1, rt, rb, holes, cutouts, wells=()):
    m = 2.0
    ox, oy = PART_HALF_W + m, -y0 + m
    items = [_outline(ox - PART_HALF_W, oy + y0, ox + PART_HALF_W, oy + y1, rt, rb)]
    items += [_circle(ox + x, oy + y, PART_HOLE) for x, y in holes]
    items += [_rr_path(ox + x, oy + y, SWITCH_CUT, SWITCH_CUT, SWITCH_CUT_R) for x, y in cutouts]
    items += [_rr_path(ox + x, oy + y, WELL[0], WELL[1], WELL[2]) for x, y in wells]
    body = '\n'.join(f'  <path d="{d}" fill="none" stroke="#ff0000" stroke-width="0.01"/>' for d in items)
    sw, sh = 2 * PART_HALF_W + 2 * m, y1 - y0 + 2 * m
    path.write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="{sw:.3f}mm" height="{sh:.3f}mm" '
                    f'viewBox="0 0 {sw:.3f} {sh:.3f}">\n  <!-- {title} Red = cut. Finished sizes; kerf compensation by the cutter. -->\n{body}\n</svg>\n')


def write_coupon(out):
    sizes, pitch, m = (13.9, 14.0, 14.1), 18.0, 3.0
    w, h = 2 * m + 2 * pitch + 14.1, 24.0
    items = [_rr_path(1 + w / 2, 1 + h / 2, w, h, 1.5)]
    for i, s in enumerate(sizes):
        items.append(_rr_path(1 + m + 7.05 + i * pitch, 1 + 9.5, s, s, SWITCH_CUT_R))
    for i, d in enumerate((2.3, 2.4, 2.5)):
        items.append(_circle(1 + m + 7.05 + i * pitch, 1 + 20.0, d))
    body = '\n'.join(f'  <path d="{d}" fill="none" stroke="#ff0000" stroke-width="0.01"/>' for d in items)
    (out / 'laser-coupon-Q5B.svg').write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="{w + 2:.3f}mm" height="{h + 2:.3f}mm" viewBox="0 0 {w + 2:.3f} {h + 2:.3f}">\n'
        f'  <!-- Cut from the 1.5 mm plate sheet. Switch cut-outs 13.9 / 14.0 (nominal) / 14.1; holes 2.3 / 2.4 (nominal) / 2.5. '
        f'A Box Jade should click in and not rock in the nominal hole. -->\n{body}\n</svg>\n')


def export(g, report):
    mirror = lambda s: s.mirror('XZ')
    stl = {'tray-Q5B.stl': g['tray'], 'plate-printable-Q5B.stl': g['plate'].translate((0, 0, -PLATE_Z))}
    for i, m in enumerate(g['mounts']):
        name = f'spacer-{HIGH_SPACER:.1f}-Q5B.stl' if m[1] < 0 else f'spacer-{WIN_Z - PLATE_TOP:.1f}-Q5B.stl'
        stl[name] = g['spacers'][i].translate((-m[0], -m[1], -(PCB_TOP if m[1] < 0 else PLATE_TOP)))
    pm = g['peg_points'][0]
    stl[f'peg-{LOW_SPACER:.1f}-Q5B.stl'] = g['pegs'][0].translate((-pm[0], -pm[1], -(PCB_TOP - 1.4)))
    for name, shape in stl.items():
        cq.exporters.export(mirror(shape), str(OUT / name), tolerance=0.02, angularTolerance=0.1)
    report['stl_mesh_checks'] = {name: q5.mesh_check(OUT / name) for name in stl}
    for part, z in (('window', WIN_Z), ('plate', PLATE_Z)):
        face = mirror(g[part]).faces('<Z').val().translate((0, 0, -z))
        cq.exporters.export(cq.Workplane('XY').add(face), str(OUT / f"{'faceplate' if part == 'window' else part}-acrylic-Q5B.dxf"))
    write_svg(OUT / 'faceplate-acrylic-Q5B.svg', f'Count Fidget Q5B faceplate: clear cast acrylic {WIN_T} mm (3/16 in OK), 1 part.',
              PART_TOP_Y, PART_BOT_Y, R_POCKET - CLEAR, R_POCKET - CLEAR, g['mounts'], [], wells=[(0, KEYS[0][1])])
    write_svg(OUT / 'plate-acrylic-Q5B.svg', f'Count Fidget Q5B switch plate: cast acrylic {PLATE_T} mm, 1 part.',
              PLATE_EDGE_Y, PART_BOT_Y, 0.5, R_POCKET - CLEAR, FACE_LOW + g['peg_points'], KEYS)
    write_coupon(OUT)
    assy = cq.Assembly(name='Count-Fidget-Q5B')
    for key, col in {'tray': '#5f6166', 'window': '#d8f0f4', 'plate': '#16171a', 'pcb': '#1f6b3a', 'holder': '#ece6d6',
                     'oled_max': '#1d3f73', 'usb': '#b7bcc0'}.items():
        assy.add(mirror(g[key]), name=key, color=cq.Color(col))
    for i, c in enumerate(g['keycaps'], 1):
        assy.add(mirror(c), name=f'keycap-{i}', color=cq.Color('#f4f3ef'))
    for i, (bot, upper, stem) in enumerate(g['switches'], 1):
        assy.add(mirror(bot), name=f'switch-{i}-base', color=cq.Color('#202326'))
        assy.add(mirror(upper), name=f'switch-{i}-top', color=cq.Color('#dfe8ea'))
        assy.add(mirror(stem), name=f'switch-{i}-stem', color=cq.Color('#2bb673'))
    for i, (s, sc, n) in enumerate(zip(g['spacers'], g['screws'], g['nuts']), 1):
        assy.add(mirror(s), name=f'spacer-{i}', color=cq.Color('#3a3f46'))
        assy.add(mirror(sc), name=f'screw-{i}', color=cq.Color('#9aa3aa'))
        assy.add(mirror(n), name=f'nut-{i}', color=cq.Color('#9aa3aa'))
    for i, pg in enumerate(g['pegs'], 1):
        assy.add(mirror(pg), name=f'peg-{i}', color=cq.Color('#3a3f46'))
    for n, s in g['bottom']:
        assy.add(mirror(s), name=f'env-{n}', color=cq.Color('#3a3f46'))
    assy.export(str(OUT / 'enclosure-Q5B.step'))
    (OUT / 'fit-report.json').write_text(json.dumps(report, indent=2) + '\n')
    names = list(stl) + ['faceplate-acrylic-Q5B.dxf', 'faceplate-acrylic-Q5B.svg', 'plate-acrylic-Q5B.dxf', 'plate-acrylic-Q5B.svg',
                         'laser-coupon-Q5B.svg', 'enclosure-Q5B.step', 'fit-report.json']
    manifest = dict(generator=report['generator_sha256'], board=report['source_board_sha256'], model=report['source_model_sha256'],
                    outputs={n: sha(OUT / n) for n in names})
    (OUT / 'build-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(report['minimum_modeled_distances_mm'], indent=1))


if __name__ == '__main__':
    main()
