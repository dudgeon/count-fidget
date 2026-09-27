"""Render the saved film.blend (from animate.py) to a PNG sequence.

blender -b build/render-q5-acrylic/film.blend --python scripts/render_q5_acrylic/render_film.py -- \
    --start 1 --end 984 [--step 1] [--preview] [--out build/render-q5-acrylic/frames]
Existing frames are skipped, so an interrupted render resumes where it stopped.
"""
import argparse
import sys
import time
from pathlib import Path

import bpy

ap = argparse.ArgumentParser()
ap.add_argument('--start', type=int, default=1)
ap.add_argument('--end', type=int, default=984)
ap.add_argument('--step', type=int, default=1)
ap.add_argument('--preview', action='store_true')
ap.add_argument('--samples', type=int, default=16)
ap.add_argument('--out', type=Path, default=Path('build/render-q5-acrylic/frames'))
args = ap.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
sc = bpy.context.scene
if args.preview:
    sc.render.resolution_x, sc.render.resolution_y = 480, 270
    sc.cycles.samples = 4
    sc.cycles.use_denoising = True
else:
    sc.cycles.samples = args.samples
args.out.mkdir(parents=True, exist_ok=True)
markers = sorted(((m.frame, m.camera) for m in sc.timeline_markers), key=lambda t: t[0])
for f in range(args.start, args.end + 1, args.step):
    path = args.out / f'f_{f:04d}.png'
    if path.exists():
        continue
    sc.frame_set(f)
    sc.camera = [c for start, c in markers if start <= f][-1]
    sc.render.filepath = str(path)
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print(f'FRAME {f} {time.time() - t:.1f}s', flush=True)
