#!/usr/bin/env python3
"""Q5B option C "sandwich": two clear 3/16 in acrylic sheets, two printed pieces, for the locked Q5 board.

Owner's design (25 Nov 2026): maximise the view of the board from above and below, and keep the printed part count down.

  top acrylic    one piece, one opening for both keycaps (same part as option B's faceplate)
  upper piece    printed: switch plate (2 mm rings round the switches) + the spacers up to the top acrylic
                 (two bosses at the display end on thin arms beside the display, two blocks at the key end)
  Q5 board       unchanged; its two display-end holes drilled to 7/64 in
  surround       printed: outer ring with four corner standoffs joined to its walls and a USB shelf. No floor.
  back acrylic   one piece: 4 screw holes, 4 lasered hex nut pockets, reset pinhole

Fasteners: 4 x M2.5 x 25 through everything into M2.5 nuts in the back panel's pockets; 2 x M2 x 10 self-tapping screws
through the upper piece's key-end blocks and the board's key-end holes into the surround's standoffs (the owner's change:
they replace printed locating pins). The upper piece prints board side down with no supports: the plate stands on walls
round each switch (a 0.6 mm lip under the plate leaves room for the switch clips) and the arms lie on the board.


Geometry and checks reuse the Q5B generator's constants (variant "four") and the Q5A board envelopes, read-only.
"""
import argparse
import json
import math
import os
import sys
from pathlib import Path

os.environ['Q5B_VARIANT'] = 'four'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import cadquery as cq                       # noqa: E402
import build_q5b_enclosure as b             # noqa: E402

q5, q5a = b.q5, b.q5a
block, rounded, cyl, overlap, volume, sha = b.block, b.rounded, b.cyl, b.overlap, b.volume, b.sha
OUT = ROOT / 'mechanical/q5b/sandwich'

FLOOR, PCB_Z, PCB_TOP = b.FLOOR, b.PCB_Z, b.PCB_TOP        # FLOOR = top face of the back panel
PLATE_Z, PLATE_TOP, WIN_Z, WIN_TOP, WIN_T = b.PLATE_Z, b.PLATE_TOP, b.WIN_Z, b.WIN_TOP, b.WIN_T
W, D, YC, Y_TOP, Y_BOT, WALL, BEZEL = b.W, b.D, b.YC, b.Y_TOP, b.Y_BOT, b.WALL, b.BEZEL
TOP = WIN_TOP                                # surround flush with the top acrylic
BACK_T = 4.7625
PANEL_Z = FLOOR - BACK_T                     # underside of the back panel
POCKET = 2.05                                # lasered hex nut pocket depth
KEYS, HOLE_R = b.KEYS, b.HOLE_R
MX, UP_Y, PEG_Y, LOW_Y = 18.5, -24.5, 25.0, b.FACE_LOW_Y    # mount x; display-end holes; board key-end holes; key-end screws
# upper piece
BOSS_R = 2.6
ARM_X = (17.3, 20.5)                         # arms beside the display (OLED module edge is at 13.85)
ARM_T = 2.0
RAIL_X = 20.5                                # plate half width
PLATE_Y = (b.PLATE_EDGE_Y, KEYS[0][1] + b.SWITCH_CUT / 2 + 2.0)   # 4.45 .. 22.8: 2 mm ring below the switches
BLOCK_X, BLOCK_Y = (15.8, 21.2), (23.4, 31.6)
M2_SEAT = PCB_TOP + 4.0                      # underside of the M2 screw head
M2_LEN, M2_SHANK_R, M2_HEAD_R, M2_HEAD_H = 10.0, 1.0, 1.9, 1.4
M2_CLEAR_R, M2_CBORE_R, M2_PILOT_R = 1.15, 2.0, 0.85
RING = 2.0                                   # plate ring round each switch cut-out
CLIP_OPEN = 15.2                             # opening under the plate: 0.6 mm lip all round for the switch clips
# surround
STAND_X = (16.3, 21.7)
POST_GAP = 0.15                              # key-end posts stop this far under the upper piece: the board sets the height
FOOT_R, FOOT_H = 4.0, 2.0
FEET = [(8.0, -24.5), (8.0, 28.5)]
SCREW_LEN = 25.0


def box(x0, x1, y0, y1, z0, z1):
    x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1))
    return block(x1 - x0, y1 - y0, z1 - z0, z0, (x0 + x1) / 2, (y0 + y1) / 2)


def plate_prism(z0, h, inset=0.0):
    """Plate footprint (rings round the two switch cut-outs) as a prism; inset shrinks every edge."""
    p = box(-RAIL_X + inset, RAIL_X - inset, PLATE_Y[0] + inset, PLATE_Y[1] - inset, z0, z0 + h)
    for x, y in KEYS:
        c = b.SWITCH_CUT + 2 * inset
        p = p.cut(b.rrect(c, c, b.SWITCH_CUT_R, h + 1, z0 - 0.5, x, y))
    return p


def make_upper():
    """Prints board side down with no supports: everything stands on the bed except the plate lip, a 0.6 mm overhang."""
    x1 = KEYS[1][0] + b.SWITCH_CUT / 2 + RING
    up = box(-x1, x1, PLATE_Y[0], PLATE_Y[1], PCB_TOP, PLATE_TOP)                  # switch box: walls from the board up to the plate
    for x, y in KEYS:
        up = up.cut(b.rrect(CLIP_OPEN, CLIP_OPEN, 0.4, PLATE_Z - PCB_TOP + 1, PCB_TOP - 1, x, y))   # clip room under the plate
        up = up.cut(b.rrect(b.SWITCH_CUT, b.SWITCH_CUT, b.SWITCH_CUT_R, 10, PCB_TOP - 1, x, y))
    for sx in (-1, 1):
        up = up.union(cyl(BOSS_R, WIN_Z - PCB_TOP, PCB_TOP, sx * MX, UP_Y))                              # display-end spacer boss
        up = up.union(box(sx * ARM_X[0], sx * ARM_X[1], UP_Y, PLATE_Y[0] + 1.5, PCB_TOP, PCB_TOP + ARM_T))   # arm, lying on the board
        up = up.union(box(sx * BLOCK_X[0], sx * BLOCK_X[1], PLATE_Y[1] - 0.2, BLOCK_Y[0], PCB_TOP, PLATE_TOP))   # low link, clear of the keycap
        up = up.union(box(sx * BLOCK_X[0], sx * BLOCK_X[1], BLOCK_Y[0], BLOCK_Y[1], PCB_TOP, WIN_Z))      # key-end spacer block
    for sx in (-1, 1):
        for y in (UP_Y, LOW_Y):
            up = up.cut(cyl(HOLE_R, 20, PCB_TOP - 1, sx * MX, y))
        up = up.cut(cyl(M2_CLEAR_R, 20, PCB_TOP - 1, sx * MX, PEG_Y))
        up = up.cut(cyl(M2_CBORE_R, WIN_Z - M2_SEAT + 1, M2_SEAT, sx * MX, PEG_Y))                       # open to the top: no roof to bridge
    # stay 0.15 mm inside the surround's cavity, including its rounded corners
    return up.intersect(rounded(W - 2 * WALL - 0.3, D - 2 * WALL - 0.3, 40, 0, r=b.R_IN - 0.15, y=YC))


def make_surround(env):
    usb_y, usb_axis = env['usb_y'], env['usb_axis']
    s = rounded(W, D, TOP - FLOOR, FLOOR, r=b.R_OUT, y=YC)
    s = s.faces('>Z').edges().chamfer(b.TOP_CHAMFER)
    s = s.faces('<Z').edges().chamfer(0.3)                       # elephant-foot relief on the bed edge
    s = s.cut(rounded(W - 2 * WALL, D - 2 * WALL, TOP, FLOOR - 1, r=b.R_IN, y=YC))
    s = s.cut(rounded(W - 2 * BEZEL, D - 2 * BEZEL, TOP, WIN_Z - b.LEDGE_DROP, r=b.R_POCKET, y=YC))   # bezel pocket + ledge
    clip = rounded(W - 0.2, D - 0.2, TOP, FLOOR, r=b.R_OUT - 0.1, y=YC)
    for sx in (-1, 1):
        # display end: standoff under the board hole, solid to the corner walls
        s = s.union(box(sx * STAND_X[0], sx * STAND_X[1], Y_TOP + WALL - 0.2, UP_Y + 2.3, FLOOR, PCB_Z).intersect(clip))
        # key end: standoff under the board's key-end hole (M2 pilot) and the post outside the board edge (M2.5 through)
        s = s.union(box(sx * STAND_X[0], sx * STAND_X[1], PEG_Y - 2.2, 27.5, FLOOR, PCB_Z).intersect(clip))
        s = s.union(box(sx * STAND_X[0], sx * STAND_X[1], 27.5, Y_BOT - WALL + 0.2, FLOOR, PCB_TOP - POST_GAP).intersect(clip))
    for sx in (-1, 1):
        for y in (UP_Y, LOW_Y):
            s = s.cut(cyl(HOLE_R, 30, FLOOR - 1, sx * MX, y))
        s = s.cut(cyl(M2_PILOT_R, 5.4, PCB_Z - 5.2, sx * MX, PEG_Y))
    usb_cut = (cq.Workplane('YZ').rect(13.4, 7.2).extrude(10).edges('|X').fillet(1.0).translate((W / 2 - WALL - 3, usb_y, usb_axis)))
    s = s.cut(usb_cut)
    s = s.cut(block(b.USB_RELIEF[0] + 1, b.USB_RELIEF[1], TOP, usb_axis, W / 2 - WALL - 1 + b.USB_RELIEF[0] / 2 + 0.5, usb_y))
    # USB shelf: receptacle pedestal and plug backstop on a 0.8 mm base strip tied to the side wall
    s = s.union(block(3, 5, PCB_Z - 3.31 - 0.15 - FLOOR, FLOOR, 17, usb_y))
    s = s.union(block(0.8, 5, PCB_Z - 1.0 - FLOOR, FLOOR, 13.675, usb_y))
    s = s.union(box(13.275, W / 2 - WALL + 0.2, usb_y - 2.5, usb_y + 2.5, FLOOR, FLOOR + 0.8))
    return s


def make_panel(mounts, sw3):
    p = rounded(W, D, BACK_T, PANEL_Z, r=b.R_OUT, y=YC)
    for x, y in mounts:
        p = p.cut(cyl(HOLE_R, BACK_T + 1, PANEL_Z - 0.5, x, y))
        p = p.cut(b.hexagon(b.NUT_POCKET_AF, POCKET + 0.5, PANEL_Z - 0.5, x, y))
    return p.cut(cyl(0.75, BACK_T + 1, PANEL_Z - 0.5, *sw3))


def build(refs):
    env = q5a.build(refs)
    g = {k: env[k] for k in ('pcb', 'holder', 'oled_max', 'oled_header', 'usb', 'mcu', 'usb_plug', 'bottom', 'tails', 'module_z', 'mouth_x')}
    mounts = [(sx * MX, y) for y in (UP_Y, LOW_Y) for sx in (-1, 1)]
    board_upper = sorted(m for m in env['mounts'] if m[1] < 0)
    assert all(abs(abs(x) - MX) < 1e-6 and abs(y - UP_Y) < 1e-6 for x, y in board_upper), board_upper
    assert all(abs(abs(x) - MX) < 1e-6 and abs(y - PEG_Y) < 1e-6 for x, y in env['mounts'] if y > 0)
    g['mounts'] = mounts
    g['sw3'] = (refs['SW3']['x'] - 21, refs['SW3']['y'] - 27)
    g['surround'], g['upper'] = make_surround(env), make_upper()
    g['window'] = b.make_window(mounts)
    g['panel'] = make_panel(mounts, g['sw3'])
    g['switches'] = [b.switch_envelope(x, y) for x, y in KEYS]
    g['keycaps'] = [b.keycap(x, y) for x, y in KEYS]
    g['screws'], g['nuts'], g['m2'] = [], [], []
    spec = dict(len=SCREW_LEN, head_z=WIN_TOP, nut_top=PANEL_Z + b.NUT_H)
    for x, y in mounts:
        sc, nut = b.fastener(x, y, spec)
        g['screws'].append(sc); g['nuts'].append(nut)
    for sx in (-1, 1):
        g['m2'].append(cyl(M2_SHANK_R, M2_LEN, M2_SEAT - M2_LEN, sx * MX, PEG_Y).union(cyl(M2_HEAD_R, M2_HEAD_H, M2_SEAT, sx * MX, PEG_Y)))
    g['feet'] = [cyl(FOOT_R, FOOT_H, PANEL_Z - FOOT_H, sx * x, y) for x, y in FEET for sx in (-1, 1)]
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--kicad-python', required=True)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'build-manifest.json').unlink(missing_ok=True)
    data, refs = q5.read_board(args.kicad_python)
    g = build(refs)
    sur, up, win, panel = g['surround'], g['upper'], g['window'], g['panel']
    comps = ([('PCB', g['pcb']), ('holder', g['holder']), ('OLED-max', g['oled_max']), ('OLED-header', g['oled_header']),
              ('USB', g['usb']), ('MCU', g['mcu'])] + g['bottom'] + g['tails'])
    nopcb = [c for c in comps if c[0] != 'PCB']
    sw = []
    for i, (bot, upper, stem) in enumerate(g['switches'], 1):
        sw += [(f'switch-{i}-bottom', bot), (f'switch-{i}-upper', upper), (f'switch-{i}-stem', stem)]
    screws = [(f'screw-{i+1}', s) for i, s in enumerate(g['screws'])]
    nuts = [(f'nut-{i+1}', s) for i, s in enumerate(g['nuts'])]
    m2 = [(f'm2-screw-{i+1}', s) for i, s in enumerate(g['m2'])]
    feet = [(f'foot-{i+1}', s) for i, s in enumerate(g['feet'])]
    hits = []

    def check(a, sa, bn, sb, tol=1e-5):
        v = overlap(sa, sb)
        if v > tol:
            hits.append(dict(a=a, b=bn, intersection_mm3=round(v, 6)))
    plug = [('USB-plug-access', g['usb_plug'])]
    for n, s in comps + sw + plug + [('window', win), ('upper', up), ('panel', panel)] + screws + nuts + feet:
        check('surround', sur, n, s)
    for n, s in comps + sw + plug + [('window', win), ('panel', panel)] + screws:
        check('upper', up, n, s)
    for n, s in m2:
        check('upper', up, n, s)
    for n, s in nopcb + sw + screws + m2 + [('panel', panel)]:
        check('window', win, n, s)
    for n, s in comps + sw + screws + nuts + m2 + feet:
        check('panel', panel, n, s)
    for n, s in nopcb + plug:                       # the model's display-end holes are still 2.2: the owner drills them to 7/64 in
        for m, sc in screws:
            check(m, sc, n, s)
    for (m, sc), pt in zip(screws, g['mounts']):
        if pt[1] > 0:
            check(m, sc, 'PCB', g['pcb'])
    for m, sc in m2:
        for n, s in comps + sw + plug:
            check(m, sc, n, s)
    for n, s in feet:
        for m, o in screws + nuts:
            check(n, s, m, o)
    thick_win = b.make_window(g['mounts'], b.WIN_T_RANGE[1])
    for i, (x, y) in enumerate(KEYS, 1):
        for state, dz, grow in (('rest', 0, 0.0), ('pressed', -b.TRAVEL, 2 * b.CAP_WOBBLE)):
            c = b.keycap(x, y, grow).translate((0, 0, dz))
            for n, s in [('surround', sur), ('window-thickest', thick_win), ('upper', up)] + screws + m2:
                check(f'keycap-{i}-{state}', c, n, s)
    # Straight vertical assembly paths, 0-30 mm in 0.5 mm steps, in the build order.
    motion, poses, tests = [], 0, 0
    stages = [('board-into-surround', comps, [('surround', sur)]),
              ('upper-piece-onto-board', [('upper', up)], nopcb + [('surround', sur)]),
              ('m2-screws', m2, nopcb + [('surround-above-standoffs', sur.intersect(block(80, 80, 40, PCB_TOP)))]),
              ('switches-into-plate', sw, nopcb + [('upper', up), ('surround', sur)]),
              ('top-acrylic', [('window', win)], nopcb + sw + m2 + [('upper', up), ('surround', sur)]),
              ('m2.5-screws', screws, nopcb + [('window', win), ('upper', up), ('surround', sur), ('panel', panel)]),
              ('keycaps', [(f'keycap-{i+1}', c) for i, c in enumerate(g['keycaps'])], [('window', win), ('upper', up), ('surround', sur)] + screws)]
    for stage, moving, obstacles in stages:
        for step in range(61):
            dz = step * 0.5
            poses += 1
            for n, s in moving:
                lifted = s.translate((0, 0, dz))
                for m, o in obstacles:
                    tests += 1
                    v = overlap(lifted, o)
                    if v > 1e-5:
                        motion.append(dict(stage=stage, dz_mm=dz, a=n, b=m, intersection_mm3=round(v, 6)))
    tip = WIN_TOP - SCREW_LEN
    engage = {}
    for t in b.WIN_T_RANGE + (WIN_T,):
        shift = t - WIN_T
        engage[f'top-acrylic@{t}'] = dict(thread_in_nut=round(min(b.NUT_H, PANEL_Z + b.NUT_H - (tip + shift)), 3),
                                          tip_below_panel=round(PANEL_Z - (tip + shift), 3),
                                          foot_clearance_to_table=round(FOOT_H - (PANEL_Z - (tip + shift)), 3))
    dist = {
        'oled_max_to_top_acrylic': WIN_Z - (g['module_z'] + 3.2),
        'holder_to_back_panel': (PCB_Z - q5a.HOLDER_H) - FLOOR,
        'keycap_skirt_rest_below_acrylic_top': WIN_TOP - b.CAP_B,
        'keycap_skirt_pressed_above_upper_piece_top': b.CAP_B - b.TRAVEL - WIN_Z,
        'keycap_skirt_pressed_above_plate': b.CAP_B - b.TRAVEL - PLATE_TOP,
        'keycap_top_above_acrylic': b.CAP_B + b.CAP_H - TOP,
        'm2_thread_in_standoff': M2_LEN - (M2_SEAT - PCB_TOP) - b.PCB_T,
        'm2_head_top_below_acrylic': WIN_Z - (M2_SEAT + M2_HEAD_H),
        'm2_counterbore_wall': min(MX - BLOCK_X[0], BLOCK_X[1] - MX) - M2_CBORE_R,
        'plate_ring_min': min(PLATE_Y[1] - (KEYS[0][1] + b.SWITCH_CUT / 2), (KEYS[0][1] - b.SWITCH_CUT / 2) - PLATE_Y[0]),
        'arm_to_oled_module': ARM_X[0] - 13.85,
        'key_end_post_gap_under_upper_piece': POST_GAP,
        'plate_lip_overhang': (CLIP_OPEN - b.SWITCH_CUT) / 2,
        'switch_box_wall_min': RING - (CLIP_OPEN - b.SWITCH_CUT) / 2,
        'screw_hole_wall_to_board_edge': LOW_Y - HOLE_R - 27.5,
    }
    solids = {n: dict(valid=s.val().isValid(), count=len(s.solids().vals()), volume_mm3=round(volume(s), 3))
              for n, s in [('surround', sur), ('upper', up), ('window', win), ('panel', panel)]}
    report = dict(
        variant='sandwich (option C)',
        status='Q5B option C engineering fit candidate for the ordered Q5 board; physical qualification pending',
        body_mm=[round(W, 3), round(D, 3), round(TOP - PANEL_Z, 3)], height_on_feet_mm=round(TOP - PANEL_Z + FOOT_H, 3),
        stack_mm_above_back_panel_underside={k: [round(v0 - PANEL_Z, 3), round(v1 - PANEL_Z, 3)] for k, (v0, v1) in dict(
            back_acrylic=(PANEL_Z, FLOOR), standoffs=(FLOOR, PCB_Z), pcb=(PCB_Z, PCB_TOP), plate=(PLATE_Z, PLATE_TOP),
            upper_piece=(PCB_TOP, WIN_Z), top_acrylic=(WIN_Z, WIN_TOP)).items()},
        printed_parts=['surround-Q5B.stl (1x, bed side = back-panel side)',
                       'upper-piece-Q5B.stl (1x, printed board side down, no supports)',
                       'foot-2.0-Q5B.stl (4x, optional: or stick-on bumpers, or trim the screws to 23.5 mm)'],
        laser_parts=['faceplate-acrylic-Q5B.svg/.dxf (top, 3/16 in clear)', 'back-panel-acrylic-Q5B.svg/.dxf (back, 3/16 in clear, hex pockets 2.05 mm deep)'],
        fasteners=dict(through='4 x M2.5 x 25 pan head + 4 x M2.5 hex nut (nuts in lasered pockets in the back panel)',
                       upper_piece=f'2 x M2 x {M2_LEN:g} self-tapping pan head, head <= {2 * M2_HEAD_R:g} mm dia, into {2 * M2_PILOT_R:g} mm pilot holes',
                       thread_engagement_mm=engage),
        valid_solids=solids, reported_intersections=hits,
        assembly_path_checks=dict(poses=poses, sampled_intersection_tests=tests, step_mm=0.5, max_lift_mm=30, collisions=motion,
                                  limitations='Straight vertical sampled paths; excludes screw driving, nut insertion and print distortion.'),
        minimum_modeled_distances_mm={k: round(v, 4) for k, v in dist.items()},
        source_board_sha256=data['board_sha256'], source_model_sha256=data['model_sha256'],
        generator_sha256=sha(Path(__file__)), q5b_generator_sha256=sha(ROOT / 'scripts/build_q5b_enclosure.py'),
        cadquery_version=cq.__version__, python_version=sys.version.split()[0],
        limitations=['Box Jade and keycap bodies are envelopes, not vendor drawings; the keycap skirt height is an estimate.',
                     'The board model keeps 2.2 mm display-end holes; the owner drills them to 7/64 in.',
                     'Print fit, support removal, M2 thread strength in the standoffs, laser pocket depth and acrylic crazing are untested.'])
    print(json.dumps({'intersections': hits, 'motion': motion[:6], 'n_motion': len(motion), 'distances': report['minimum_modeled_distances_mm'],
                      'engagement': engage}, indent=1), flush=True)
    assert all(v['valid'] and v['count'] == 1 for v in solids.values()), 'Invalid solid'
    assert not hits, f'Resolve modelled intersections: {hits}'
    assert not motion, f'Resolve assembly-path collisions: {motion[:8]}'
    assert all(v['thread_in_nut'] >= 1.9 and v['foot_clearance_to_table'] >= 0.4 for v in engage.values()), engage
    assert dist['m2_thread_in_standoff'] >= 4.0 and dist['m2_head_top_below_acrylic'] >= 0.5
    export(g, report)


def write_panel_svg(path, g):
    """Back panel, drawn as seen from OUTSIDE (the face to put up in the laser)."""
    m = 2.0
    x0, y0 = -W / 2, Y_TOP
    X = lambda x: (-x) - x0 + m
    Y = lambda y: y - y0 + m
    cut = [b._rr_path(X(0), Y(YC), W, D, b.R_OUT)]
    pockets = []
    for x, y in g['mounts']:
        cut.append(b._circle(X(x), Y(y), 2 * HOLE_R))
        rc = b.NUT_POCKET_AF / math.sqrt(3)
        pts = [(X(x) + rc * math.cos(math.radians(60 * k)), Y(y) + rc * math.sin(math.radians(60 * k))) for k in range(6)]
        pockets.append('M' + ' L'.join(f'{px:.3f},{py:.3f}' for px, py in pts) + ' Z')
    cut.append(b._circle(X(g['sw3'][0]), Y(g['sw3'][1]), 1.5))
    w, h = W + 2 * m, D + 2 * m
    body = '\n'.join(f'  <path d="{d}" fill="#808080" stroke="none"/>' for d in pockets)
    body += '\n' + '\n'.join(f'  <path d="{d}" fill="none" stroke="#ff0000" stroke-width="0.1"/>' for d in cut)
    path.write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="{w:.3f}mm" height="{h:.3f}mm" '
                    f'viewBox="0 0 {w:.3f} {h:.3f}">\n  <!-- Count Fidget Q5B option C back panel: clear cast acrylic 3/16 in (4.76 mm), 1 part, drawn as seen '
                    f'from OUTSIDE (put the outside face up). Red = cut through (4 screw holes 2.9 mm, reset pinhole 1.5 mm, outline). '
                    f'Grey fill = hex nut pockets ({b.NUT_POCKET_AF} mm across flats), engrave {POCKET} mm deep: test the depth on scrap first. '
                    f'Display end at the top of the drawing. Lines are 0.1 mm wide so they show on screen: set them to hairline if your laser needs it. -->\n{body}\n</svg>\n')


def export(g, report):
    mirror = lambda s: s.mirror('XZ')
    stl = {'surround-Q5B.stl': g['surround'].translate((0, 0, -FLOOR)),
           'upper-piece-Q5B.stl': g['upper'].translate((0, 0, -PCB_TOP)),
           'foot-2.0-Q5B.stl': cyl(FOOT_R, FOOT_H, 0)}
    for name, shape in stl.items():
        cq.exporters.export(mirror(shape), str(OUT / name), tolerance=0.02, angularTolerance=0.1)
    report['stl_mesh_checks'] = {name: q5.mesh_check(OUT / name) for name in stl}
    face = mirror(g['window']).faces('<Z').val().translate((0, 0, -WIN_Z))
    cq.exporters.export(cq.Workplane('XY').add(face), str(OUT / 'faceplate-acrylic-Q5B.dxf'))
    b.write_svg(OUT / 'faceplate-acrylic-Q5B.svg', f'Count Fidget Q5B option C top: clear cast acrylic {WIN_T} mm (3/16 in), 1 part.',
                b.PART_TOP_Y, b.PART_BOT_Y, b.R_POCKET - b.CLEAR, b.R_POCKET - b.CLEAR, g['mounts'], [], wells=[(0, KEYS[0][1])])
    fp = OUT / 'faceplate-acrylic-Q5B.svg'
    fp.write_text(fp.read_text().replace('stroke-width="0.01"', 'stroke-width="0.1"'))   # visible on screen
    face = mirror(g['panel']).faces('>Z').val().translate((0, 0, -FLOOR))
    cq.exporters.export(cq.Workplane('XY').add(face), str(OUT / 'back-panel-acrylic-Q5B.dxf'))
    write_panel_svg(OUT / 'back-panel-acrylic-Q5B.svg', g)
    assy = cq.Assembly(name='Count-Fidget-Q5B-sandwich')
    for key, col in {'surround': '#5f6166', 'upper': '#e59a3a', 'window': '#d8f0f4', 'panel': '#d8f0f4', 'pcb': '#1f6b3a',
                     'holder': '#ece6d6', 'oled_max': '#1d3f73', 'usb': '#b7bcc0'}.items():
        assy.add(mirror(g[key]), name=key, color=cq.Color(col))
    for i, c in enumerate(g['keycaps'], 1):
        assy.add(mirror(c), name=f'keycap-{i}', color=cq.Color('#f4f3ef'))
    for i, (bot, upper, stem) in enumerate(g['switches'], 1):
        assy.add(mirror(bot), name=f'switch-{i}-base', color=cq.Color('#202326'))
        assy.add(mirror(upper), name=f'switch-{i}-top', color=cq.Color('#dfe8ea'))
    for kind in ('screws', 'nuts', 'm2', 'feet'):
        for i, s in enumerate(g[kind], 1):
            assy.add(mirror(s), name=f'{kind}-{i}', color=cq.Color('#9aa3aa' if kind != 'feet' else '#222222'))
    assy.export(str(OUT / 'enclosure-Q5B-sandwich.step'))
    (OUT / 'fit-report.json').write_text(json.dumps(report, indent=2) + '\n')
    names = list(stl) + ['faceplate-acrylic-Q5B.dxf', 'faceplate-acrylic-Q5B.svg', 'back-panel-acrylic-Q5B.dxf', 'back-panel-acrylic-Q5B.svg',
                         'enclosure-Q5B-sandwich.step', 'fit-report.json']
    manifest = dict(generator=report['generator_sha256'], board=report['source_board_sha256'], model=report['source_model_sha256'],
                    outputs={n: sha(OUT / n) for n in names})
    (OUT / 'build-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
