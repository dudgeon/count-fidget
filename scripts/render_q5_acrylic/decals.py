#!/usr/bin/env python3
"""Small printed/marked decals for the renders (appearance only):
- the LIR2032 positive face marking (user-supplied cell; generic text, no brand),
- the OLED module silkscreen pin labels (as printed on HS96L01W4S03 photos: GND VCC D0 D1 RES DC CS).
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/render-q5-acrylic/assets'
FONT = OUT / 'Inter-600.ttf'
MONO = OUT / 'JetBrainsMono-500.ttf'


def cell_label(px_per_mm=60):
    """20 mm disc; drawn as seen from below the device, i.e. mirrored for a top-view UV map."""
    s = int(20 * px_per_mm)
    im = Image.new('LA', (s, s), (0, 0))
    d = ImageDraw.Draw(im)
    big = ImageFont.truetype(str(FONT), int(2.6 * px_per_mm))
    small = ImageFont.truetype(str(FONT), int(1.3 * px_per_mm))
    plus = ImageFont.truetype(str(FONT), int(4.2 * px_per_mm))
    c = s / 2
    d.text((c, c - 3.8 * px_per_mm), '+', font=plus, fill=(255, 255), anchor='mm')
    d.text((c, c + 0.6 * px_per_mm), 'LIR2032', font=big, fill=(255, 255), anchor='mm')
    d.text((c, c + 3.4 * px_per_mm), '3.6V  Li-ion  RECHARGEABLE', font=small, fill=(255, 255), anchor='mm')
    im = im.transpose(Image.FLIP_LEFT_RIGHT)
    im.save(OUT / 'cell_label.png')


def oled_silk(px_per_mm=80):
    """Module PCB top, 27.3 x 27.8 mm, top-view frame (header row at the top edge)."""
    w, h = int(27.3 * px_per_mm), int(27.8 * px_per_mm)
    im = Image.new('LA', (w, h), (0, 0))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(str(MONO), int(0.95 * px_per_mm))
    for i, lab in enumerate(['GND', 'VCC', 'D0', 'D1', 'RES', 'DC', 'CS']):
        x = (27.3 / 2 - 7.62 + i * 2.54) * px_per_mm
        d.text((x, 3.25 * px_per_mm), lab, font=f, fill=(255, 255), anchor='mm')
    t = ImageFont.truetype(str(MONO), int(0.8 * px_per_mm))
    d.text((1.2 * px_per_mm, 26.6 * px_per_mm), 'HS96L01', font=t, fill=(255, 255), anchor='ls')
    sq = 0.08 * px_per_mm
    x0, y0 = (27.3 / 2 - 7.62 - 1.1) * px_per_mm, (1.5 - 1.1) * px_per_mm
    d.rectangle([x0, y0, x0 + 2.2 * px_per_mm, y0 + 2.2 * px_per_mm], outline=(255, 255), width=max(1, int(sq * 2)))
    im.save(OUT / 'oled_silk.png')


if __name__ == '__main__':
    cell_label()
    oled_silk()
    print('decals ->', OUT)
