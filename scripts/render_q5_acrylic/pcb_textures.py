#!/usr/bin/env python3
"""Rasterise the locked Q5 board into render textures (never writes the board).

Run with a Python that can import KiCad 10's pcbnew, with kicad-cli on PATH and
rsvg-convert installed. Writes 8-bit greyscale masks (white = feature) in the
top-view frame of the board: pixel (0, 0) is board (0, 0), +x right, +y down,
PX_PER_MM pixels per millimetre. Bottom-side layers are NOT mirrored; the
Blender material mirrors them when it maps the underside.
"""
import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
BOARD = ROOT / 'electronics/q5/click-counter-Q5.kicad_pcb'
BOARD_W, BOARD_H = 42.0, 54.0
LAYERS = ['F.Cu', 'B.Cu', 'F.Mask', 'B.Mask', 'F.SilkS', 'B.SilkS', 'F.Paste', 'B.Paste']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def export_layer(layer, folder, px_per_mm):
    svg = folder / f'{layer}.svg'
    cmd = ['kicad-cli', 'pcb', 'export', 'svg', '--mode-single', '--layers', layer,
           '--black-and-white', '--exclude-drawing-sheet', '--page-size-mode', '2',
           '--drill-shape-opt', '0', '-o', str(svg), str(BOARD)]
    if 'SilkS' in layer:
        cmd.insert(-3, '--subtract-soldermask')
    subprocess.run(cmd, check=True, capture_output=True)
    text = svg.read_text()
    # kicad-cli rounds the page to 1/1000 inch and clips the board edge; the
    # drawing itself is in board millimetres, so pin the page to the outline.
    text, n = re.subn(r'width="[^"]*mm" height="[^"]*mm" viewBox="[^"]*"',
                      f'width="{BOARD_W}mm" height="{BOARD_H}mm" viewBox="0 0 {BOARD_W} {BOARD_H}"', text, count=1)
    assert n == 1, f'{layer}: unexpected SVG header'
    svg.write_text(text)
    png = folder / f'{layer}.png'
    dpi = px_per_mm * 25.4
    subprocess.run(['rsvg-convert', '-b', 'white', '-d', str(dpi), '-p', str(dpi), '-o', str(png), str(svg)], check=True)
    im = np.asarray(Image.open(png).convert('L'), dtype=np.uint8)
    expect = (round(BOARD_H * px_per_mm), round(BOARD_W * px_per_mm))
    assert abs(im.shape[0] - expect[0]) <= 1 and abs(im.shape[1] - expect[1]) <= 1, (layer, im.shape, expect)
    return 255 - im  # features white


def drill_maps(px_per_mm, supersample=4):
    import pcbnew
    board = pcbnew.LoadBoard(str(BOARD))
    s = px_per_mm * supersample
    size = (round(BOARD_W * s), round(BOARD_H * s))
    maps = {k: Image.new('L', size, 0) for k in ('pth', 'npth', 'via')}
    draws = {k: ImageDraw.Draw(v) for k, v in maps.items()}
    holes = []

    def slot(kind, x, y, dx, dy, angle):
        draw = draws[kind]
        if abs(dx - dy) < 1e-6:
            r = dx / 2
            draw.ellipse([(x - r) * s, (y - r) * s, (x + r) * s, (y + r) * s], fill=255)
            return
        # Oblong hole: capsule along its long axis, rotated by the pad angle.
        import math
        long_, short = max(dx, dy), min(dx, dy)
        a = math.radians(-angle + (0 if dx >= dy else 90))
        ux, uy = math.cos(a), math.sin(a)
        half = (long_ - short) / 2
        r = short / 2
        for t in np.linspace(-half, half, 24):
            cx, cy = x + ux * t, y + uy * t
            draw.ellipse([(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s], fill=255)

    for fp in board.GetFootprints():
        for pad in fp.Pads():
            d = pad.GetDrillSize()
            dx, dy = pcbnew.ToMM(d.x), pcbnew.ToMM(d.y)
            if dx <= 0 or dy <= 0:
                continue
            p = pad.GetPosition()
            x, y = pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)
            kind = 'npth' if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH else 'pth'
            slot(kind, x, y, dx, dy, pad.GetOrientationDegrees())
            holes.append(dict(ref=fp.GetReference(), pad=pad.GetNumber(), kind=kind, x=x, y=y, dx=dx, dy=dy))
    tented = {'front': 0, 'back': 0}
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            p = t.GetPosition()
            x, y = pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)
            dr = pcbnew.ToMM(t.GetDrillValue())
            slot('via', x, y, dr, dr, 0)
            holes.append(dict(ref='via', kind='via', x=x, y=y, dx=dr, dy=dr))
    out = {k: np.asarray(v.resize((round(BOARD_W * px_per_mm), round(BOARD_H * px_per_mm)), Image.LANCZOS)) for k, v in maps.items()}
    return out, holes


def blur(im, sigma_px):
    from PIL import ImageFilter
    return np.asarray(Image.fromarray(im).filter(ImageFilter.GaussianBlur(sigma_px)))


def export_glb(out, model_dir):
    """Board body (with every drill, via holes included) and the KiCad component models only;
    copper, mask and silk come from the textures instead."""
    env = dict(__import__('os').environ, KICAD10_3DMODEL_DIR=str(model_dir))
    subprocess.run(['kicad-cli', 'pcb', 'export', 'glb', '-f', '-o', str(out), '--cut-vias-in-body',
                    '--no-extra-pad-thickness', '-D', f'KICAD10_3DMODEL_DIR={model_dir}', str(BOARD)],
                   check=True, capture_output=True, env=env)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, default=ROOT / 'build/render-q5-acrylic/textures')
    ap.add_argument('--px-per-mm', type=float, default=80.0)
    ap.add_argument('--models', type=Path, default=Path('/opt/kicad3d'),
                    help='folder holding the KiCad 10 packages3D STEP files the board references')
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    board_hash = sha(BOARD)
    layers = {}
    with tempfile.TemporaryDirectory(prefix='q5a-svg-') as tmp:
        tmp = Path(tmp)
        for layer in LAYERS:
            im = export_layer(layer, tmp, args.px_per_mm)
            layers[layer] = im
            print(layer, im.shape, 'coverage %.3f' % (im.mean() / 255))
    drills, holes = drill_maps(args.px_per_mm)
    rgba = lambda a, b, c, d: Image.fromarray(np.dstack([a, b, c, d]).astype(np.uint8), 'RGBA')
    s = args.px_per_mm * 0.03          # ~30 um: soldermask flowing over copper and silk edges
    rgba(layers['F.Cu'], layers['F.Mask'], layers['F.SilkS'], layers['F.Paste']).save(args.out / 'top_rgba.png')
    rgba(layers['B.Cu'], layers['B.Mask'], layers['B.SilkS'], layers['B.Paste']).save(args.out / 'bot_rgba.png')
    rgba(blur(layers['F.Cu'], s), blur(layers['B.Cu'], s), blur(layers['F.SilkS'], s / 2), blur(layers['B.SilkS'], s / 2)).save(args.out / 'height_rgba.png')
    full = np.full_like(drills['pth'], 255)
    rgba(drills['pth'], drills['npth'], drills['via'], full).save(args.out / 'drill_rgba.png')
    export_glb(args.out / 'board.glb', args.models)
    assert sha(BOARD) == board_hash, 'Board changed during texture export'
    meta = dict(board=str(BOARD.relative_to(ROOT)), board_sha256=board_hash, px_per_mm=args.px_per_mm,
                size_px=[round(BOARD_W * args.px_per_mm), round(BOARD_H * args.px_per_mm)],
                frame='top view, board mm; pixel (0,0) = board (0,0); +y down; bottom layers not mirrored',
                layers=LAYERS, holes=holes)
    (args.out / 'textures.json').write_text(json.dumps(meta, indent=1) + '\n')
    print('holes', len(holes))


if __name__ == '__main__':
    main()
