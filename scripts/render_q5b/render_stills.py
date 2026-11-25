"""Stills for the Q5B variant (bezel tray, acrylic window, acrylic switch plate).

python scripts/render_q5b/render_stills.py -- --shots hero,top --preview
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
    G, H, md, P = ctx['G'], ctx['home'], S.meta(), ctx['parts']
    G['pcb'].location.z = H['pcb'].z + 0.018 * amount
    for i in (1, 2):
        G[f'sw{i}'].location.z = 0.036 * amount
        G[f'key{i}'].location.z = 0.084 * amount
    G['plate'].location.z = 0.036 * amount
    G['window'].location.z = 0.054 * amount
    for i in range(1, 5):
        up = i in md['upper']
        P[f'screw-{i}'].location.z = md['screw_head_z'][i - 1] * MM + (0.012 if up else 0.010) * amount
        P[f'spacer-{i}'].location.z = md['pcb_top'] * MM - (0.006 if up else 0.003) * amount
        P[f'nut-{i}'].location.z = -0.010 * amount


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
    'hero': ((-0.125, -0.180, 0.245), (0.0, 0.0015, 0.0135), 85, 11, (0.0, -0.002, 0.019), None),
    'top': ((0.0, -0.0005, 0.44), (0.0, 0.0, 0.0), 135, None, None, None),
    'exploded': ((-0.255, -0.330, 0.270), (0.0, 0.0, 0.045), 70, None, None, 'explode'),
    'keys': ((0.034, -0.140, 0.074), (0.0, -0.0120, 0.0190), 100, 14, (0.0, -0.0200, 0.0240), None),
    'side': ((0.0, -0.33, 0.014), (0.0, 0.0, 0.014), 135, None, None, None),
    'lowangle': ((0.150, -0.150, 0.045), (0.0, 0.0, 0.012), 85, 11, (0.010, -0.012, 0.016), None),
    'usb': ((0.095, -0.075, 0.032), (0.0235, -0.0006, 0.0060), 100, 8, (0.0235, -0.0006, 0.0060), None),
    'under': ((-0.110, -0.150, -0.140), (0.0, 0.0, 0.004), 85, None, None, 'under'),
}


def under(ctx):
    """Underside: hide the backdrop so the nut pockets show."""
    for o in bpy.data.objects:
        if o.name.lower().startswith(('cyclo', 'backdrop', 'floor')):
            o.hide_render = True


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
        elif setup == 'under':
            under(ctx)
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
