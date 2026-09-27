#!/usr/bin/env python3
"""Cut the rendered Q5A frames into two films with ffmpeg:

- q5a-assembly-film.mp4       polished cut: fades, an opening title and an end card
- q5a-assembly-explainer.mp4  the same footage with captions, callouts that track the
                              parts (anchors exported by animate.py) and a few holds

python3 scripts/render_q5_acrylic/compose_videos.py [--frames DIR] [--out DIR] [--crf N] [--preview]
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
TITLES = [  # polished film: (first, last, title, subtitle, style)
    (26, 104, 'Count Fidget', 'Q5A  ·  clear acrylic lid', 'light'),
]
END_CARD = (84, 'Count Fidget', 'Q5A')   # film: extra frames on the last shot while it softens and the name comes up

CAPTIONS = [  # explainer: (first, last, title, body, callouts)
    (8, 118, 'The ordered Q5 board', 'JLC assembles every part on this side, which faces down in the tray.',
     [('mcu', 'STM32L072 MCU'), ('cell', 'LIR2032 in BT1')]),
    (124, 226, 'Display side', 'The HS96L01 OLED module stands 2.5 mm off the board on its header.', [('oled', '128 × 64 OLED', 204, 226)]),
    (232, 334, 'Printed tray', 'PETG, 1.2 mm walls, 0.5 mm around the board. Four bosses and two load posts carry it.', [('tray', 'Tray')]),
    (340, 418, 'Switches, no soldering', 'The clicky CPG151101D13 switches press into the hot-swap sockets.', [('switch', 'Clicky MX switch')]),
    (424, 538, 'One flat lid', '2 mm clear cast acrylic, laser cut. No display cutout: the OLED sits at least 0.3 mm below it.', [('lid', '2.0 mm cast acrylic')]),
    (544, 670, 'Four screws hold everything', 'M2 × 14 self-tapping screws pass through 6 mm spacers and the board into the tray.',
     [('screw', 'M2 × 14 screw', 544, 618), ('spacer', '6 mm spacer', 552, 618)]),
    (676, 742, 'Printed keycaps', '17 mm tiles: 1.4 mm clear of the screw heads and 0.7 mm above the lid at full travel.', [('keycap', 'Keycap')]),
    (748, 874, 'Firmware-accurate display', "Frames from the Q5 firmware's own renderer: wake, then COUNT three times.", []),
    (880, 984, 'Q5A', 'Body 45.4 × 57.4 × 16.8 mm  ·  26.2 mm to the key tops  ·  1.8 mm smaller each way than Q5', []),
]

HOLDS = {  # explainer: frame -> (extra frames, note lines)
    118: (30, None),
    214: (36, None),      # the OLED faces the camera only after the roll-over at 206
    516: (48, ['The lid rests on the switch rims', '15.2 × 12.9 mm holes over 15.6 × 13.96 mm rims', 'so it holds the switches down']),
    872: (24, None),
}


def draw_title(im, f, a, b, t1, t2, style='dark'):
    op = fade(f, a, b, 14)
    if op <= 0:
        return im
    w, h = im.size
    over = Image.new('RGBA', im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    y1, y2 = h * 0.86, h * 0.86 + 46
    if style == 'light':
        # soft bottom gradient and a blurred shadow keep white type legible over the board
        grad = Image.new('L', (1, h), 0)
        for y in range(h):
            grad.putpixel((0, y), int(max(0, (y - 0.55 * h) / (0.45 * h)) ** 1.6 * 150 * op))
        shade = Image.new('RGBA', im.size, (8, 10, 12, 0))
        shade.putalpha(grad.resize(im.size))
        im = Image.alpha_composite(im, shade)
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh)
        sd.text((w / 2, y1 + 2), t1, font=font(300, 58), fill=(0, 0, 0, int(160 * op)), anchor='ms')
        sd.text((w / 2, y2 + 2), t2, font=font(400, 25), fill=(0, 0, 0, int(160 * op)), anchor='ms')
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(6)))
        d.text((w / 2, y1), t1, font=font(300, 58), fill=(255, 255, 255, int(250 * op)), anchor='ms')
        d.text((w / 2, y2), t2, font=font(400, 25), fill=(235, 238, 240, int(230 * op)), anchor='ms')
    else:
        d.text((w / 2, y1), t1, font=font(300, 58), fill=(*INK, int(235 * op)), anchor='ms')
        d.text((w / 2, y2), t2, font=font(400, 25), fill=(*SOFT, int(220 * op)), anchor='ms')
    return Image.alpha_composite(im, over)


SIDE = {'lid': -1}   # preferred label side per anchor (default: right of the part unless near the right edge)


def draw_end_card(im, k, t1, t2):
    """The settled last frame softens towards the backdrop colour and the name comes up, centred."""
    w, h = im.size
    g = ease(k / 18)
    if g > 0:
        backdrop = im.crop((0, 0, w // 20, h // 20)).convert('RGB').resize((1, 1), Image.BOX).getpixel((0, 0))
        im = Image.blend(im.filter(ImageFilter.GaussianBlur(14 * g)), Image.new('RGBA', im.size, (*backdrop, 255)), 0.78 * g)
    op = ease((k - 8) / 14)
    if op > 0:
        over = Image.new('RGBA', im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(over)
        d.text((w / 2, h * 0.5), t1, font=font(300, 72), fill=(*INK, int(240 * op)), anchor='ms')
        d.text((w / 2, h * 0.5 + 54), t2, font=font(400, 28), fill=(*SOFT, int(225 * op)), anchor='ms')
        im = Image.alpha_composite(im, over)
    return im


def label(d, xy, text, op, side, size):
    """Leader line from the part to a light pill with dark text, legible on the backdrop and on the board."""
    x, y = xy
    w, h = size
    f = font(600, 28)
    pw, ph = d.textlength(text, font=f) + 32, 44
    if side > 0 and x + 110 + pw > w - 40:
        side = -1
    elif side < 0 and x - 110 - pw < 40:
        side = 1
    ln = 110 * side
    ex, ey = x + ln, max(48 + ph / 2, y - 70)
    pts = [(x, y), (x + ln * 0.35, ey), (ex, ey)]
    d.line(pts, fill=(255, 255, 255, int(150 * op)), width=6, joint='curve')
    d.line(pts, fill=(*INK, int(225 * op)), width=2, joint='curve')
    d.ellipse([x - 8, y - 8, x + 8, y + 8], fill=(255, 255, 255, int(235 * op)))
    d.ellipse([x - 4.5, y - 4.5, x + 4.5, y + 4.5], fill=(*INK, int(255 * op)))
    x0 = ex if side > 0 else ex - pw
    d.rounded_rectangle([x0, ey - ph / 2, x0 + pw, ey + ph / 2], radius=ph / 2,
                        fill=(252, 252, 250, int(228 * op)), outline=(0, 0, 0, int(24 * op)), width=1)
    d.text((x0 + 16, ey + 1), text, font=f, fill=(*INK, int(255 * op)), anchor='lm')


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
        edge = min(1.0, (u - 0.04) / 0.08, (0.9 - u) / 0.08, (v - 0.03) / 0.04, (0.78 - v) / 0.06)
        if depth <= 0 or edge <= 0:
            continue
        cop = op * fade(f, ca, cb, 10) * ease(edge)
        if cop > 0.01:
            label(d, (u * w, v * h), text, cop, SIDE.get(name, 1 if u < 0.62 else -1), (w, h))
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


def write_film(frames, out, mode, crf=20, preview=False):
    anchors = json.loads((BUILD / 'anchors.json').read_text()) if mode == 'explainer' else {}
    src = frames_list(frames, 984)
    seq = []
    for i, p in enumerate(src, 1):
        seq.append((i, p, None))
        if mode == 'explainer' and i in HOLDS:
            extra, note = HOLDS[i]
            for k in range(extra):
                seq.append((i, p, ('hold', k, extra, note)))
    if mode == 'film':
        for k in range(END_CARD[0]):
            seq.append((len(src), src[-1], ('end', k, END_CARD[0], None)))
    n = len(seq)
    with tempfile.TemporaryDirectory(prefix='q5a-cut-') as tmp:
        tmp = Path(tmp)
        for j, (f, p, hold) in enumerate(seq, 1):
            im = Image.open(p).convert('RGBA')
            if preview:
                im = im.resize((960, 540), Image.LANCZOS)
            if mode == 'film':
                for a, b, t1, t2, style in TITLES:
                    im = draw_title(im, f, a, b, t1, t2, style)
                if hold:
                    im = draw_end_card(im, hold[1], *END_CARD[1:])
            else:
                for cap in CAPTIONS:
                    im = draw_caption(im, f, cap, anchors)
                if hold and hold[3]:
                    _, k, extra, note = hold
                    im = draw_hold_note(im, note, fade(k, 0, extra, 8))
            im = global_fade(im, j, n)
            im.convert('RGB').save(tmp / f'o_{j:05d}.png', compress_level=1)
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', str(tmp / 'o_%05d.png'),
                        '-c:v', 'libx264', '-preset', 'slow', '-crf', str(crf if not preview else 26), '-pix_fmt', 'yuv420p',
                        '-movflags', '+faststart', str(out)], check=True)
    print('wrote', out, f'{n / FPS:.1f}s')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--frames', type=Path, default=BUILD / 'frames')
    ap.add_argument('--out', type=Path, default=ROOT / 'mechanical/q5-acrylic/video')
    ap.add_argument('--crf', type=int, default=20)
    ap.add_argument('--preview', action='store_true')
    ap.add_argument('--only', choices=['film', 'explainer'])
    args = ap.parse_args()
    for mode in ('film', 'explainer'):
        if args.only and mode != args.only:
            continue
        name = 'q5a-assembly-film.mp4' if mode == 'film' else 'q5a-assembly-explainer.mp4'
        write_film(args.frames, args.out / name, mode, args.crf, args.preview)


if __name__ == '__main__':
    main()
