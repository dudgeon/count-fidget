#!/usr/bin/env python3
"""Cut the rendered Q5A frames into two films with ffmpeg:

- q5a-assembly-film.mp4       polished cut: fades and two quiet titles
- q5a-assembly-explainer.mp4  the same footage with captions, callouts that track the
                              parts (anchors exported by animate.py) and a few holds

python3 scripts/render_q5_acrylic/compose_videos.py [--frames DIR] [--out DIR] [--preview]
"""
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / 'build/render-q5-acrylic'
FONTS = BUILD / 'assets'
FPS = 24
INK = (38, 40, 44)
SOFT = (92, 96, 102)


def font(weight, size):
    return ImageFont.truetype(str(FONTS / f'Inter-{weight}.ttf'), size)


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def fade(f, a, b, ramp=10):
    """Opacity for an overlay shown on frames a..b with ramps."""
    return min(ease((f - a) / ramp), ease((b - f) / ramp))


# --------------------------------------------------------------------------- overlays
TITLES = [  # polished film
    (26, 104, 'Count Fidget', 'Q5A  ·  clear acrylic lid'),
    (906, 984, 'Count Fidget', 'Q5A'),
]

CAPTIONS = [  # explainer: (first, last, title, body, callouts)
    (8, 118, 'The ordered Q5 board', 'JLC-assembled component side: every part below is on the underside.',
     [('mcu', 'STM32L072 MCU'), ('fram', 'FM25V02A FRAM'), ('cell', 'LIR2032 in BT1'), ('socket', 'Hot-swap socket'), ('usb', 'USB-C')]),
    (124, 226, 'Display side', 'The HS96L01 OLED module stands 2.5 mm off the board on its header.', [('oled', '128 x 64 OLED', 204, 226)]),
    (232, 334, 'Printed tray', 'PETG, 1.2 mm walls, 0.5 mm around the board. Four bosses and two load posts carry it.', [('tray', 'Tray')]),
    (340, 418, 'Switches, no soldering', 'The clicky CPG151101D13 switches press into the hot-swap sockets.', [('switch', 'Clicky MX switch')]),
    (424, 538, 'One flat lid', '2 mm clear cast acrylic, laser cut. No display cutout: the OLED sits 0.3 mm below it.', [('lid', '2.0 mm cast acrylic')]),
    (544, 670, 'Four screws hold everything', 'M2 x 14 self-tapping screws pass through 6 mm brass spacers and the board into the tray.',
     [('screw', 'M2 x 14 screw', 544, 618), ('spacer', '6 mm spacer', 552, 618)]),
    (676, 742, 'Printed keycaps', '17 mm tiles: 1.4 mm clear of the screw heads, 0.7 mm above the lid at full travel.', [('keycap', 'Keycap')]),
    (748, 874, 'Firmware-accurate display', 'Frames from the Q5 renderer: wake, then COUNT three times.', []),
    (880, 984, 'Q5A', 'Body 45.4 x 57.4 x 16.8 mm  ·  26.2 mm to the key tops  ·  1.8 mm smaller each way than Q5', []),
]

HOLDS = {  # explainer: frame -> (extra frames, note lines)
    118: (30, None),
    516: (48, ['The lid rests on the switch rims', '15.2 x 12.9 mm holes, 15.6 x 13.96 mm rims', 'so it holds the switches down']),
    872: (24, None),
}


def draw_title(im, f, a, b, t1, t2):
    op = fade(f, a, b, 14)
    if op <= 0:
        return im
    over = Image.new('RGBA', im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    w, h = im.size
    d.text((w / 2, h * 0.86), t1, font=font(300, 54), fill=(*INK, int(235 * op)), anchor='ms')
    d.text((w / 2, h * 0.86 + 44), t2, font=font(400, 24), fill=(*SOFT, int(220 * op)), anchor='ms')
    return Image.alpha_composite(im, over)


def label(d, xy, text, op, side):
    x, y = xy
    ln = 110 if side > 0 else -110
    ex, ey = x + ln, y - 70
    col = (255, 255, 255, int(255 * op))
    d.line([(x, y), (x + ln * 0.35, ey), (ex, ey)], fill=(30, 32, 36, int(170 * op)), width=6)
    d.line([(x, y), (x + ln * 0.35, ey), (ex, ey)], fill=col, width=3)
    d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=(30, 32, 36, int(150 * op)))
    d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=col)
    f = font(600, 31)
    anchor = 'ls' if side > 0 else 'rs'
    tx = ex + (10 if side > 0 else -10)
    for dx in (-2, -1, 0, 1, 2):
        for dy in (-2, -1, 0, 1, 2):
            if dx or dy:
                d.text((tx + dx, ey + 11 + dy), text, font=f, fill=(30, 32, 36, int(130 * op)), anchor=anchor)
    d.text((tx, ey + 11), text, font=f, fill=col, anchor=anchor)


def draw_caption(im, f, cap, anchors):
    a, b, title, body, callouts = cap
    op = fade(f, a, b, 12)
    if op <= 0:
        return im
    w, h = im.size
    over = Image.new('RGBA', im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    tf, bf = font(600, 38), font(400, 27)
    bw = max(d.textlength(title, font=tf), d.textlength(body, font=bf)) + 72
    x0, y0 = 64, h - 190
    panel = Image.new('RGBA', im.size, (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle([x0, y0, x0 + bw, y0 + 126], radius=22, fill=(252, 252, 250, int(214 * op)))
    im = Image.alpha_composite(im, panel.filter(ImageFilter.GaussianBlur(0.6)))
    d.text((x0 + 36, y0 + 52), title, font=tf, fill=(*INK, int(255 * op)), anchor='ls')
    d.text((x0 + 36, y0 + 96), body, font=bf, fill=(*SOFT, int(255 * op)), anchor='ls')
    pts = anchors.get(str(f), {}).get('points', {})
    for c in callouts:
        name, text = c[0], c[1]
        ca, cb = (c[2], c[3]) if len(c) > 2 else (a + 8, b - 4)
        if name not in pts:
            continue
        u, v, depth = pts[name]
        edge = min(1.0, (u - 0.04) / 0.08, (0.9 - u) / 0.08, (v - 0.10) / 0.08, (0.72 - v) / 0.08)
        if depth <= 0 or edge <= 0:
            continue
        cop = op * fade(f, ca, cb, 10) * ease(edge)
        if cop > 0.01:
            label(d, (u * w, v * h), text, cop, 1 if u < 0.62 else -1)
    return Image.alpha_composite(im, over)


def draw_hold_note(im, lines, op):
    w, h = im.size
    over = Image.new('RGBA', im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    x, y = w - 80, 110
    for i, line in enumerate(lines):
        f = font(600 if i == 0 else 400, 34 if i == 0 else 26)
        d.text((x, y + i * 44), line, font=f, fill=((*INK, int(255 * op)) if i == 0 else (*SOFT, int(255 * op))), anchor='rs')
    return Image.alpha_composite(im, over)


# --------------------------------------------------------------------------- cutting
def frames_list(frames, last):
    return [frames / f'f_{i:04d}.png' for i in range(1, last + 1)]


def global_fade(im, f, n):
    k = min(ease(f / 16), ease((n - f) / 20))
    if k >= 1:
        return im
    black = Image.new('RGBA', im.size, (0, 0, 0, 255))
    return Image.blend(black, im, k)


def write_film(frames, out, mode, preview=False):
    anchors = json.loads((BUILD / 'anchors.json').read_text()) if mode == 'explainer' else {}
    src = frames_list(frames, 984)
    seq = []
    for i, p in enumerate(src, 1):
        seq.append((i, p, None))
        if mode == 'explainer' and i in HOLDS:
            extra, note = HOLDS[i]
            for k in range(extra):
                seq.append((i, p, (k, extra, note)))
    n = len(seq)
    with tempfile.TemporaryDirectory(prefix='q5a-cut-') as tmp:
        tmp = Path(tmp)
        for j, (f, p, hold) in enumerate(seq, 1):
            im = Image.open(p).convert('RGBA')
            if preview:
                im = im.resize((960, 540), Image.LANCZOS)
            if mode == 'film':
                for a, b, t1, t2 in TITLES:
                    im = draw_title(im, f, a, b, t1, t2)
            else:
                for cap in CAPTIONS:
                    im = draw_caption(im, f, cap, anchors)
                if hold and hold[2]:
                    k, extra, note = hold
                    im = draw_hold_note(im, note, fade(k, 0, extra, 8))
            im = global_fade(im, j, n)
            im.convert('RGB').save(tmp / f'o_{j:05d}.png')
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', str(tmp / 'o_%05d.png'),
                        '-c:v', 'libx264', '-preset', 'slow', '-crf', '20' if not preview else '26', '-pix_fmt', 'yuv420p',
                        '-movflags', '+faststart', str(out)], check=True)
    print('wrote', out, f'{n / FPS:.1f}s')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--frames', type=Path, default=BUILD / 'frames')
    ap.add_argument('--out', type=Path, default=ROOT / 'mechanical/q5-acrylic/video')
    ap.add_argument('--preview', action='store_true')
    ap.add_argument('--only', choices=['film', 'explainer'])
    args = ap.parse_args()
    for mode in ('film', 'explainer'):
        if args.only and mode != args.only:
            continue
        name = 'q5a-assembly-film.mp4' if mode == 'film' else 'q5a-assembly-explainer.mp4'
        write_film(args.frames, args.out / name, mode, args.preview)


if __name__ == '__main__':
    main()
