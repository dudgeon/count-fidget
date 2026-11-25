#!/usr/bin/env python3
"""Render-only 3D assets for the Q5B visualisation (bezel tray, acrylic window, acrylic switch plate).

Enclosure parts, laser parts, spacers and keycap envelopes come from scripts/build_q5b_enclosure.py, so the
renders show the checked design. Board-side appearance models (OLED module, header, BT1 with cell, hot-swap
sockets, tact switch) are reused from the Q5A render assets. The Kailh Box Jade switch, the M2 machine screws
and hex nuts are appearance models from MX/Box standard dimensions, not vendor CAD, and are never used for fit.

Output: one GLB in millimetres, CAD frame (X = PCB_X - 21, Y = 27 - PCB_Y, Z above the tray underside).
Node names are '<material>|<part>'.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'scripts/render_q5_acrylic'))
import build_q5_enclosure as q5          # noqa: E402
import build_q5b_enclosure as b          # noqa: E402
import build_render_assets as ra         # noqa: E402  (Q5A appearance models, read-only)

block, cyl, rr = q5.block, q5.cyl, ra.rr


def box_jade():
    """Kailh Box Jade appearance, local frame centred on the PCB top (z = 0)."""
    p = {}
    pt = b.PLATE_TOP - b.PCB_TOP                 # 5.0
    base = rr(13.95, 13.95, pt, 0, 0.5)
    base = base.cut(block(15, 15, b.PLATE_T + 0.02, pt - b.PLATE_T - 0.01).cut(rr(13.4, 13.4, 2, pt - 2, 0.5)))  # plate groove
    p['plastic_black'] = base.union(cyl(1.925, 2.85, -2.85))
    top_h = b.HOUSING_TOP - b.PLATE_TOP          # 6.6
    shell = (cq.Workplane('XY').workplane(offset=pt).rect(15.6, 15.6).workplane(offset=top_h).rect(13.0, 13.0).loft())
    shell = shell.cut(cq.Workplane('XY').workplane(offset=pt - 0.01).rect(14.2, 14.2).workplane(offset=top_h - 0.8).rect(11.6, 11.6).loft())
    shell = shell.cut(rr(7.0, 7.0, 2, pt + top_h - 1.2, 0.6))                    # box opening
    p['pc_clear'] = shell
    # Box stem: square box around the MX cross, jade POM, and the click bar seen through the clear top.
    stem = rr(6.2, 6.2, 4.4, pt + top_h - 2.2, 0.5).cut(rr(5.0, 5.0, 5, pt + top_h - 2.0, 0.4))
    cross = block(4.0, 1.3, 3.6, b.STEM_TOP - b.PCB_TOP - 3.6).union(block(1.1, 4.0, 3.6, b.STEM_TOP - b.PCB_TOP - 3.6))
    p['pom_jade'] = stem.union(cross).union(block(5.2, 5.2, 0.8, pt + top_h - 2.2))
    p['steel_spring'] = block(11.0, 0.5, 0.5, pt + 3.6).union(block(0.5, 0.5, 3.0, pt + 0.8, 5.25, 0))   # click bar
    pins = None
    for px, py in ((-3.81, 2.54), (2.54, 5.08)):
        pin = block(0.4, 1.5, 3.3, -3.3, px, py)
        pins = pin if pins is None else pins.union(pin)
    p['gold'] = pins
    return p


def machine_screw(length):
    """M2 pan head (ISO 7045, head 4.0 x 1.6, cross recess), head on z = 0 up; plain-threaded shank down."""
    head = cq.Workplane('XY').circle(b.HEAD_D / 2).extrude(b.HEAD_H)
    try:
        head = head.faces('>Z').edges().fillet(0.7)
    except Exception:
        pass
    for ang in (0, 90):
        slot = cq.Workplane('XY').box(2.1, 0.55, 1.2, centered=(True, True, False)).translate((0, 0, 0.75))
        head = head.cut(slot.rotate((0, 0, 0), (0, 0, 1), ang))
    core = cyl(0.8, length, -length)
    thread = None
    pitch = 0.4
    for i in range(int((length - 0.4) / pitch)):
        z = -length + 0.2 + i * pitch
        ring = cq.Workplane('XY').add(cq.Solid.makeCone(0.8, 1.0, pitch / 2, cq.Vector(0, 0, z))).union(
            cq.Workplane('XY').add(cq.Solid.makeCone(1.0, 0.8, pitch / 2, cq.Vector(0, 0, z + pitch / 2))))
        thread = ring if thread is None else thread.union(ring)
    return head.union(core).union(thread)


def hex_nut():
    n = b.hexagon(b.NUT_AF, b.NUT_H, 0, 0, 0).cut(cyl(0.85, 3, -1))
    try:
        n = n.faces('>Z or <Z').edges('not %CIRCLE').chamfer(0.15)
    except Exception:
        pass
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--kicad-python', required=True)
    ap.add_argument('--out', type=Path, default=ROOT / 'build/render-q5b/assets/q5b-parts.glb')
    args = ap.parse_args()
    data, refs = q5.read_board(args.kicad_python)
    g = b.build(refs)
    parts = []

    def add(mat, name, shape):
        parts.append((mat, name, shape))
    add('tray', 'tray', g['tray'])
    add('acrylic', 'window', g['window'])
    add('plastic_black', 'plate', g['plate'])
    for i, c in enumerate(g['keycaps'], 1):
        add('keycap', f'keycap-{i}', c)
    for i, (x, y) in enumerate(g['mounts'], 1):
        s = g['spec'][(x, y)]
        add('spacer', f'spacer-{i}', g['spacers'][i - 1])
        add('steel_screw', f'screw-{i}', machine_screw(s['len']).translate((x, y, s['head_z'])))
        add('steel_screw', f'nut-{i}', hex_nut().translate((x, y, s['nut_top'] - b.NUT_H)))
    sw = box_jade()
    for i, (x, y) in enumerate(b.KEYS, 1):
        for mat, s in sw.items():
            add(mat, f'switch-{i}-{mat}', s.translate((x, y, b.PCB_TOP)))
    om, pads = ra.oled_module()
    ox, oy = refs['DS1']['x'] - 21, refs['DS1']['y'] - 27
    mz = b.PCB_TOP + 2.5
    for mat, s in om.items():
        add(mat, f'oled-{mat}', s.translate((ox, oy, mz)))
    for mat, s in ra.header_and_joints((ox, oy), mz, b.PCB_Z, b.PCB_TOP, pads).items():
        add(mat, f'oled-header-{mat}', s)
    bx, by = refs['BT1']['x'] - 21, refs['BT1']['y'] - 27
    for mat, s in ra.holder_and_cell().items():
        add(mat, f'bt1-{mat}', s.translate((bx, by, b.PCB_Z)))
    for ref, sign in (('SW1', 1), ('SW2', -1)):
        c = [q for q in refs[ref]['pads'] if abs(q['drill'][0] - 4.0) < 1e-3][0]
        for mat, s in ra.hotswap(refs[ref]['pads'], sign).items():
            add(mat, f'{ref.lower()}-socket-{mat}', s.translate((c['x'] - 21, c['y'] - 27, b.PCB_Z)))
    sx, sy = refs['SW3']['x'] - 21, refs['SW3']['y'] - 27
    for mat, s in ra.tact_switch().items():
        add(mat, f'sw3-{mat}', s.translate((sx, sy, b.PCB_Z)))
    assy = cq.Assembly(name='q5b-render-parts')
    for mat, name, shape in parts:
        assy.add(shape.mirror('XZ'), name=f'{mat}|{name}')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    assy.export(str(args.out), 'GLTF', tolerance=0.01, angularTolerance=0.08)
    meta = dict(frame='mm; CAD frame X = PCB_X - 21, Y = 27 - PCB_Y, Z above tray underside',
                pcb_z=b.PCB_Z, pcb_top=b.PCB_TOP, plate_z=b.PLATE_Z, plate_top=b.PLATE_TOP, win_z=b.WIN_Z, win_top=b.WIN_TOP,
                keycap_top=b.CAP_B + b.CAP_H, stem_top=b.STEM_TOP, travel=b.TRAVEL,
                mounts=[[x, -y] for x, y in g['mounts']], screw_head_z=[g['spec'][m]['head_z'] for m in g['mounts']],
                upper=[i + 1 for i, m in enumerate(g['mounts']) if m[1] < 0], lower=[i + 1 for i, m in enumerate(g['mounts']) if m[1] > 0],
                keys=[[x, -y] for x, y in b.KEYS], oled_active_center=[ox, -(oy - 2.1)], oled_active_size=[21.74, 10.86],
                oled_active_z=mz + 1.2 + 1.35 + 0.124, oled_module_center=[ox, -oy], bt1_center=[bx, -by],
                board_sha256=data['board_sha256'], parts=[f'{m}|{n}' for m, n, _ in parts])
    args.out.with_suffix('.json').write_text(json.dumps(meta, indent=1) + '\n')
    print('parts', len(parts), '->', args.out)


if __name__ == '__main__':
    main()
