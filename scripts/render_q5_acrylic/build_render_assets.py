#!/usr/bin/env python3
"""Build the render-only 3D assets for the Q5A (acrylic lid) visualisation.

Enclosure parts come straight from scripts/build_q5_acrylic_enclosure.py, so the
renders show the checked design. Parts that have no KiCad 3D model are modelled
here from their drawings: the CPG151101D13 switch (clear PC top housing, black
PA base, cyan stem, white click jacket, spring), the HS96L01W4S03 OLED module
(blue PCB, glass, COG driver, FPC, seven-pin header), the CR2032-BS-6-1 holder
with an LIR2032 cell, the purple CPG151101S11 hot-swap sockets, the TS-1088 tact
switch, M2 x 14 cross pan-head screws and brass spacers. They are appearance
models, not vendor CAD, and are never used for fit claims.

Output: one GLB in millimetres, CAD frame (X = PCB_X - 21, Y = 27 - PCB_Y,
Z above the tray underside). Node names are '<material>|<part>'.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_q5_enclosure as q5  # noqa: E402
import build_q5_acrylic_enclosure as acr  # noqa: E402

block, cyl = q5.block, q5.cyl


def rr(w, d, h, z, r, x=0, y=0):
    return block(w, d, h, z, x, y).edges('|Z').fillet(r)


def place(shape, x, y, z=0, rot=0):
    if rot:
        shape = shape.rotate((0, 0, 0), (0, 0, 1), rot)
    return shape.translate((x, y, z))


# ---------------------------------------------------------------- switch
def mx_switch():
    """Local frame: centre on the PCB top (z = 0), sloped (south) side toward +X."""
    p = {}
    base = rr(13.95, 13.95, 3.6, 0, 0.6)
    base = base.union(rr(12.2, 12.2, 2.9, 3.6, 0.8))              # upper bottom-housing, seen through the clear top
    base = base.cut(block(6.2, 5.6, 4.0, 3.0))                      # stem well
    p['plastic_black'] = base.union(cyl(1.925, 2.85, -2.85)).union(cyl(1.6, 0.4, -3.25))
    # Clear PC top housing: skirt with clips, rim, sloped upper shell, stem window.
    skirt = rr(13.95, 13.95, 1.4, 3.6, 0.6).cut(rr(12.3, 12.3, 1.6, 3.5, 0.5))
    for sx in (-1, 1):
        clip = (cq.Workplane('YZ').polyline([(0, 0), (0.38, 0.9), (0, 1.3)]).close().extrude(4.0, both=True)
                .rotate((0, 0, 0), (0, 0, 1), 90 if sx > 0 else -90).translate((sx * 6.975, 0, 3.4)))
        skirt = skirt.union(clip)
    rim = rr(15.6, 13.96, 1.0, 5.0, 0.8)
    prof = [(-5.8, 0), (7.35, 0), (3.4, 5.0), (-5.0, 5.0), (-5.8, 4.2)]
    upper = cq.Workplane('XZ').polyline(prof).close().extrude(6.17, both=True).translate((0, 0, 6.0))
    try:
        upper = upper.edges('|X').fillet(0.6)
    except Exception:
        pass
    shell = rim.union(upper)
    inner = cq.Workplane('XZ').polyline([(-4.95, -1.2), (6.35, -1.2), (2.85, 4.1), (-4.95, 4.1)]).close().extrude(5.3, both=True).translate((0, 0, 6.0))
    shell = shell.cut(inner).cut(rr(6.4, 5.9, 3, 9.5, 0.6))
    shell = shell.cut(rr(3.2, 2.2, 2, 9.8, 0.3, 4.6 - 1.2, 0))     # LED window on the sloped side
    p['pc_clear'] = shell.union(skirt)
    # Stem: cross on a slider, cyan POM.
    stem = block(4.0, 1.3, 3.6, 11.4).union(block(1.1, 4.0, 3.6, 11.4))
    stem = stem.union(rr(5.4, 5.0, 4.4, 7.0, 0.5))
    stem = stem.union(block(1.6, 7.2, 1.2, 7.0)).union(block(7.6, 1.4, 1.0, 7.4))
    p['pom_cyan'] = stem
    jacket = rr(7.0, 6.2, 1.6, 6.3, 0.8).cut(rr(5.6, 5.2, 2, 6.2, 0.5))
    p['pom_white'] = jacket
    helix = cq.Wire.makeHelix(pitch=1.05, height=6.6, radius=2.05).translate(cq.Vector(0, 0, 0.7))
    wire_prof = cq.Workplane('XZ').center(2.05, 0.7).circle(0.18)
    try:
        spring = wire_prof.sweep(cq.Workplane('XY').add(helix), isFrenet=True)
        p['steel_spring'] = spring
    except Exception:
        p['steel_spring'] = cyl(2.25, 6.6, 0.7).cut(cyl(1.85, 7, 0.6))
    pins = None
    for px, py in ((-5.08, -2.54), (-2.54, 3.81)):
        pin = block(0.4, 1.5, 3.3, -3.3, px, py).union(block(0.4, 1.0, 0.6, -3.9, px, py))
        pins = pin if pins is None else pins.union(pin)
    leaf = block(0.25, 3.2, 3.2, 3.2, -4.9, 1.2).union(block(0.25, 2.4, 2.6, 3.4, -4.4, -1.6))
    p['gold'] = pins.union(leaf)
    return p


# ---------------------------------------------------------------- OLED module
def oled_module():
    """Local frame: module PCB centre, z = 0 at the module PCB underside.
    +Y is toward the keys (Y-down builder frame); the header row is at y = -12.4."""
    p = {}
    board = rr(27.3, 27.8, 1.2, 0, 0.5)
    for hx in (-11.65, 11.65):
        for hy in (-11.9, 11.9):
            board = board.cut(cyl(1.25, 2, -0.5, hx, hy))
    pads = []
    for i in range(7):
        x = -7.62 + i * 2.54
        board = board.cut(cyl(0.5, 2, -0.5, x, -12.4))
        pads.append((x, -12.4))
    p['pcb_blue'] = board
    rings = None
    for hx in (-11.65, 11.65):
        for hy in (-11.9, 11.9):
            r = cyl(2.0, 0.04, 1.2, hx, hy).cut(cyl(1.25, 1, 1.0, hx, hy)).union(cyl(2.0, 0.04, -0.04, hx, hy).cut(cyl(1.25, 1, -0.5, hx, hy)))
            rings = r if rings is None else rings.union(r)
    p['tin_pads'] = rings
    # Glass stack: 24.74 x 16.9 x 1.4 (drawing), centre 0.58 toward the header.
    gy = -0.58
    p['glass_edge'] = rr(24.74, 16.9, 0.75, 1.2 + 0.1, 0.15, 0, gy)           # bottom (TFT/OLED) glass incl. ledge
    p['glass_top'] = rr(24.74, 14.3, 0.5, 1.2 + 0.85, 0.15, 0, gy - 1.3)       # encapsulation glass
    p['polariser'] = rr(23.74, 12.86, 0.12, 1.2 + 1.35, 0.1, 0, -2.1)         # viewing area over the pixels
    p['oled_active'] = block(21.74, 10.86, 0.004, 1.2 + 1.35 + 0.12, 0, -2.1)  # emissive pixels on the polariser (texture)
    p['cog_die'] = block(13.5, 1.0, 0.3, 1.2 + 0.85, 0, gy + 7.1)             # SSD1315 chip-on-glass on the ledge
    # FPC: flat on the ledge, around the lower PCB edge, back under the module.
    fpc_w, t = 12.0, 0.12
    ledge_y = gy + 16.9 / 2
    flat = block(fpc_w, 16.9 / 2 - 6.9 + 0.2, t, 1.2 + 0.85, 0, (gy + 6.9 + ledge_y) / 2 + 0.1)
    run = block(fpc_w, ledge_y - (gy + 6.9) + (13.9 - ledge_y), t, 1.2 + 0.85, 0, 0).translate((0, 0, 0))
    arc = (cq.Workplane('YZ').center(13.9, 0.6).circle(0.95 + t).circle(0.95).extrude(fpc_w / 2, both=True)
           .intersect(block(fpc_w + 1, 2.2, 3, -0.8, 0, 13.9 + 1.1)))
    down = block(fpc_w, 13.9 - ledge_y, t, 1.2 + 0.85, 0, (13.9 + ledge_y) / 2)
    under = block(fpc_w, 6.0, t, -0.47, 0, 13.9 - 3.0)
    p['fpc_kapton'] = flat.union(down).union(arc).union(under)
    smd = None
    for i, (sx, sy) in enumerate([(-8, 4), (-6, 4), (-4, 4), (6, 5), (8, 5), (-9, -2), (9, -3), (4, -6)]):
        c = block(1.6, 0.8, 0.5, -0.5, sx, sy)
        smd = c if smd is None else smd.union(c)
    p['smd_body'] = smd
    return p, pads


def header_and_joints(oled_origin, module_z, pcb_z, pcb_top, pads_local):
    ox, oy = oled_origin
    p = {}
    p['plastic_black'] = rr(17.78, 2.5, 2.5, pcb_top, 0.2, ox, oy - 12.4)
    pins = solder = None
    for lx, ly in pads_local:
        x, y = ox + lx, oy + ly
        pin = block(0.64, 0.64, (module_z + 1.2 + 1.0) - (pcb_z - 1.3), pcb_z - 1.3, x, y)
        pins = pin if pins is None else pins.union(pin)
        top = cq.Solid.makeCone(0.85, 0.32, 0.55, cq.Vector(x, y, module_z + 1.2))
        bot = cq.Solid.makeCone(0.85, 0.32, 0.9, cq.Vector(x, y, pcb_z), cq.Vector(0, 0, -1))
        s = cq.Workplane('XY').add(top).union(cq.Workplane('XY').add(bot))
        solder = s if solder is None else solder.union(s)
    p['tin_pins'] = pins
    p['solder'] = solder
    return p


# ---------------------------------------------------------------- holder + cell
def holder_and_cell():
    """Local: holder centre, z = 0 at the PCB underside, parts hang to z = -5.5."""
    p = {}
    base = rr(22.26, 16.16, 0.8, -0.8, 0.6).cut(cyl(10.25, 1, -0.9).intersect(block(30, 12.4, 2, -1)))
    ends = None
    for sx in (-1, 1):
        wall = rr(1.7, 10.5, 5.5, -5.5, 0.4, sx * (11.13 - 0.85), 0)
        lip = block(1.4, 7.0, 0.7, -5.5, sx * (11.13 - 1.9), 0)
        e = wall.union(lip)
        ends = e if ends is None else ends.union(e)
    cradle = base.union(ends)
    for sy in (-1, 1):
        cradle = cradle.union(rr(14.0, 1.1, 1.4, -2.2, 0.3, 0, sy * (8.08 - 0.55)))
    cradle = cradle.cut(cyl(10.2, 4.0, -4.75))
    p['nylon_ivory'] = cradle
    plus = block(5.4, 3.8, 0.2, -0.2, 14.39, 0).union(block(0.3, 3.8, 4.9, -5.1, 11.4, 0)).union(block(3.0, 3.8, 0.3, -5.1, 10.0, 0))
    minus = block(5.4, 3.8, 0.2, -0.2, -14.39, 0).union(block(4.0, 3.0, 0.25, -1.05, -9.8, 0))
    p['tin_contacts'] = plus.union(minus)
    cell = cyl(10.0, 3.2, -4.8).edges().fillet(0.35)
    p['steel_cell'] = cell
    p['cell_label'] = cyl(9.6, 0.004, -4.806)                       # disc under the + face for the marking texture
    return p


# ---------------------------------------------------------------- hot-swap socket
FAB = [(-5.45, 5.49), (-6.6, 5.49), (-6.6, -0.41), (-0.35, -0.41), (-0.35, 3.08), (4, 3.08), (4, 7.08), (-1.65, 7.08), (-1.65, 5.49)]


def hotswap(ref_pads, sign):
    """Body from the footprint fab outline mapped into the board with the placement map
    found from the pad data: SW1 (x, y) -> (-y, -x), SW2 (x, y) -> (y, x)."""
    m = (lambda x, y: (-y, -x)) if sign > 0 else (lambda x, y: (y, x))
    pts = [m(x, y) for x, y in FAB]
    body = cq.Workplane('XY').polyline(pts).close().extrude(1.85).translate((0, 0, -1.85))
    try:
        body = body.edges('|Z').fillet(0.4)
    except Exception:
        pass
    for hx, hy in ((-3.81, 2.54), (2.54, 5.08)):
        x, y = m(hx, hy)
        body = body.union(cyl(2.0, 1.85, -1.85, x, y)).cut(cyl(0.8, 0.5, -0.3, x, y))
    tabs = None
    for (px, py), inward in (((5.842, 5.08), -1), ((-7.085, 2.54), 1)):
        x, y = m(px, py)
        t = block(2.3, 2.3, 0.22, -0.22, x, y)
        tabs = t if tabs is None else tabs.union(t)
    return {'pa_purple': body, 'tin_contacts': tabs}


def tact_switch():
    body = rr(3.9, 3.0, 1.1, -1.1, 0.2)
    top = block(3.5, 2.8, 0.25, -1.35)
    act = cyl(0.75, 0.65, -2.0)
    legs = block(1.0, 1.6, 0.25, -0.25, -2.225, 0).union(block(1.0, 1.6, 0.25, -0.25, 2.225, 0))
    return {'plastic_black': body.union(act), 'steel_satin': top, 'tin_contacts': legs}


# ---------------------------------------------------------------- fasteners
def pan_screw(length):
    """M2 cross pan head, head on z = 0 up; shank down to -length with a helical thread."""
    head = cq.Workplane('XY').circle(1.9).extrude(1.6)
    try:
        head = head.faces('>Z').edges().fillet(0.7)
    except Exception:
        pass
    for ang in (0, 90):
        slot = (cq.Workplane('XY').polyline([(-1.05, -0.28), (1.05, -0.28), (0.55, 0.28), (-0.55, 0.28)]).close()
                .extrude(1.0).rotate((0, 0, 0), (1, 0, 0), 90).translate((0, 0.5, 0.75)))
        slot = cq.Workplane('XY').box(2.1, 0.55, 1.2, centered=(True, True, False)).translate((0, 0, 0.75))
        head = head.cut(slot.rotate((0, 0, 0), (0, 0, 1), ang))
    head = head.cut(cq.Workplane('XY').add(cq.Solid.makeCone(0.0, 0.75, 0.95, cq.Vector(0, 0, 0.7))))
    core = cyl(0.78, length - 0.3, -length + 0.3).union(cq.Workplane('XY').add(cq.Solid.makeCone(0.2, 0.78, 0.3, cq.Vector(0, 0, -length))))
    thread = None
    pitch = 0.4
    n = int((length - 0.6) / pitch)
    for i in range(n):
        z = -length + 0.45 + i * pitch
        ring = cq.Workplane('XY').add(cq.Solid.makeCone(0.78, 1.0, pitch / 2, cq.Vector(0, 0, z))).union(
            cq.Workplane('XY').add(cq.Solid.makeCone(1.0, 0.78, pitch / 2, cq.Vector(0, 0, z + pitch / 2))))
        thread = ring if thread is None else thread.union(ring)
    return head.union(core).union(thread)


def spacer():
    s = cyl(2.0, 6.0, 0).cut(cyl(1.1, 7, -0.5))
    try:
        s = s.faces('>Z or <Z').edges().chamfer(0.2)
    except Exception:
        pass
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--kicad-python', required=True)
    ap.add_argument('--out', type=Path, default=ROOT / 'build/render-q5-acrylic/assets/q5a-parts.glb')
    args = ap.parse_args()
    data, refs = q5.read_board(args.kicad_python)
    g = acr.build(refs)
    parts = []   # (material, name, shape) in the builder (Y-down) frame

    def add(mat, name, shape):
        parts.append((mat, name, shape))
    add('tray', 'tray', g['tray'])
    add('acrylic', 'lid', g['lid'])
    add('keycap_count', 'keycap-1', g['keycaps'][0])
    add('keycap_reset', 'keycap-2', g['keycaps'][1])
    for i, (x, y) in enumerate(g['mounts'], 1):
        add('brass', f'spacer-{i}', spacer().translate((x, y, acr.PCB_TOP)))
        add('steel_screw', f'screw-{i}', pan_screw(acr.SCREW_LEN).translate((x, y, acr.LID_TOP)))
    sw = mx_switch()
    for i, ((x, y), rot) in enumerate(zip(acr.KEYS, acr.KEY_ROT), 1):
        r = 0 if rot % 360 == 90 else 180
        for mat, s in sw.items():
            add(mat, f'switch-{i}-{mat}', place(s, x, y, acr.PCB_TOP, r))
    om, pads = oled_module()
    ox, oy = refs['DS1']['x'] - 21, refs['DS1']['y'] - 27
    mz = acr.PCB_TOP + 2.5
    for mat, s in om.items():
        add(mat, f'oled-{mat}', s.translate((ox, oy, mz)))
    for mat, s in header_and_joints((ox, oy), mz, acr.PCB_Z, acr.PCB_TOP, pads).items():
        add(mat, f'oled-header-{mat}', s)
    bx, by = refs['BT1']['x'] - 21, refs['BT1']['y'] - 27
    for mat, s in holder_and_cell().items():
        add(mat, f'bt1-{mat}', s.translate((bx, by, acr.PCB_Z)))
    for ref, sign in (('SW1', 1), ('SW2', -1)):
        c = [q for q in refs[ref]['pads'] if abs(q['drill'][0] - 4.0) < 1e-3][0]
        for mat, s in hotswap(refs[ref]['pads'], sign).items():
            add(mat, f'{ref.lower()}-socket-{mat}', s.translate((c['x'] - 21, c['y'] - 27, acr.PCB_Z)))
    sx, sy = refs['SW3']['x'] - 21, refs['SW3']['y'] - 27
    for mat, s in tact_switch().items():
        add(mat, f'sw3-{mat}', s.translate((sx, sy, acr.PCB_Z)))
    assy = cq.Assembly(name='q5a-render-parts')
    for mat, name, shape in parts:
        assy.add(shape.mirror('XZ'), name=f'{mat}|{name}')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    assy.export(str(args.out), 'GLTF', tolerance=0.01, angularTolerance=0.08)
    meta = dict(frame='mm; CAD frame X = PCB_X - 21, Y = 27 - PCB_Y, Z above tray underside',
                pcb_z=acr.PCB_Z, pcb_top=acr.PCB_TOP, lid_z=acr.LID_Z, lid_top=acr.LID_TOP, keycap_top=acr.KEYCAP_TOP,
                stem_top=acr.STEM_TOP, travel=acr.TRAVEL, mounts=[[x, -y] for x, y in g['mounts']],
                keys=[[x, -y] for x, y in acr.KEYS], oled_active_center=[ox, -(oy - 2.1)], oled_active_size=[21.74, 10.86],
                oled_active_z=mz + 1.2 + 1.35 + 0.124, oled_module_center=[ox, -oy], bt1_center=[bx, -by],
                board_sha256=data['board_sha256'], parts=[f'{m}|{n}' for m, n, _ in parts])
    args.out.with_suffix('.json').write_text(json.dumps(meta, indent=1) + '\n')
    print('parts', len(parts), '->', args.out)


if __name__ == '__main__':
    main()
