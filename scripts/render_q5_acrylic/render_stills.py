"""Stills for the Q5A acrylic-lid variant.

blender -b --python scripts/render_q5_acrylic/render_stills.py -- --shots hero,top --preview
"""
import argparse
import math
import sys
import time
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scene as S  # noqa: E402

MM = S.MM


def explode(ctx, amount=1.0):
    G, H = ctx['G'], ctx['home']
    G['pcb'].location.z = H['pcb'].z + 0.020 * amount
    for i in (1, 2):
        G[f'sw{i}'].location.z = 0.034 * amount
        G[f'key{i}'].location.z = 0.070 * amount
    G['lid'].location.z = 0.050 * amount
    for i in range(1, 5):
        ctx['parts'][f'screw-{i}'].location.z = S.meta()['lid_top'] * MM + 0.010 * amount
        ctx['parts'][f'spacer-{i}'].location.z = S.meta()['pcb_top'] * MM - 0.004 * amount


def flip_pcb(ctx):
    """PCB alone, component side up, floating above the backdrop."""
    G = ctx['G']
    for k, g in G.items():
        if k != 'pcb':
            for c in [g] + list(g.children_recursive):
                c.hide_render = True
    G['pcb'].rotation_euler = (0, math.pi, math.radians(0))
    G['pcb'].location = (0, 0, ctx['home']['pcb'].z + 0.0105)


SHOTS = {
    # name: (camera location, target, lens, fstop or None, focus point or None, setup)
    'hero': ((-0.120, -0.175, 0.235), (0.0, 0.0015, 0.0115), 85, 11, (0.0, -0.002, 0.017), None),
    'top': ((0.0, -0.0005, 0.42), (0.0, 0.0, 0.0), 135, None, None, None),
    'exploded': ((-0.255, -0.330, 0.270), (0.0, 0.0, 0.043), 70, None, None, 'explode'),
    'display': ((0.010, -0.047, 0.088), (0.0, 0.0112, 0.0145), 100, 16, (0.0, 0.0124, 0.0140), None),
    'edge': ((-0.098, -0.090, 0.052), (-0.0150, -0.0205, 0.0140), 100, 11, (-0.0185, -0.0250, 0.0168), None),
    'keys': ((0.030, -0.132, 0.066), (0.0, -0.0105, 0.0170), 100, 16, (0.0, -0.0200, 0.0230), None),
    'side': ((0.0, -0.33, 0.012), (0.0, 0.0, 0.012), 135, None, None, None),
    'usb': ((0.090, -0.075, 0.030), (0.0227, -0.0006, 0.0060), 100, 8, (0.0227, -0.0006, 0.0060), None),
    'pcb': ((-0.105, -0.150, 0.150), (0.0, 0.0, 0.0185), 85, 13, (0.0, -0.004, 0.0215), 'flip'),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--shots', default='hero')
    ap.add_argument('--preview', action='store_true')
    ap.add_argument('--samples', type=int, default=384)
    ap.add_argument('--res', default='1920x1080')
    ap.add_argument('--out', type=Path, default=S.BUILD / 'stills')
    ap.add_argument('--tray', default='#3a3b3e')
    ap.add_argument('--frame', default='oled_108_none.png')
    ap.add_argument('--exposure', type=float, default=0.0)
    ap.add_argument('--scale', type=int, default=2, help='preview divisor')
    ap.add_argument('--suffix', default='')
    args = ap.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    args.out.mkdir(parents=True, exist_ok=True)
    w, h = (int(v) for v in args.res.split('x'))
    if args.preview:
        w, h = w // args.scale, h // args.scale
    for shot in args.shots.split(','):
        ctx = S.build(tray_colour=S.srgb(args.tray), oled_frame=S.OLED / args.frame)
        S.studio_lights()
        bpy.context.scene.view_settings.exposure = args.exposure
        S.configure_render(samples=48 if args.preview else args.samples, res=(w, h), threshold=0.03 if args.preview else 0.02)
        S.lean_paths()
        loc, tgt, lens, fstop, focus, setup = SHOTS[shot]
        if setup == 'explode':
            explode(ctx)
        elif setup == 'flip':
            flip_pcb(ctx)
        cam = S.camera(lens=lens)
        S.aim(cam, loc, tgt)
        if fstop:
            S.dof(cam, (Vector(focus) - Vector(loc)).length, fstop)
        bpy.context.scene.render.filepath = str(args.out / f'{shot}{args.suffix}{"-preview" if args.preview else ""}.png')
        t = time.time()
        bpy.ops.render.render(write_still=True)
        print(f'SHOT {shot} {time.time() - t:.1f}s -> {bpy.context.scene.render.filepath}', flush=True)


if __name__ == '__main__':
    main()
