#!/usr/bin/env python3
"""Render OLED frames with the reviewed Q5 firmware renderer (firmware/q5-stm32/oled.c).

Each frame is the exact 128 x 64 bitmap the firmware would send for an OledView,
written as an 8-bit PNG (255 = lit). Used as the emissive texture of the display.
"""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
FW = ROOT / 'firmware/q5-stm32'
LABELS = {'none': 'OLED_LABEL_NONE', 'chg': 'OLED_LABEL_CHG', 'rst': 'OLED_LABEL_RST', 'lo': 'OLED_LABEL_LO'}

HARNESS = r'''
#include <stdio.h>
#include <stdlib.h>
#include "oled.h"
int main(int argc, char **argv) {
    OledView v = {(uint32_t)strtoul(argv[1], 0, 10), (uint8_t)atoi(argv[2]), (uint8_t)atoi(argv[3]), false};
    for (int p = 0; p < 8; p++) for (int c = 0; c < 128; c++) putchar(oled_frame_byte(&v, p, c));
    return 0;
}
'''


def build(tmp):
    src = tmp / 'frames.c'
    exe = tmp / 'frames'
    src.write_text(HARNESS)
    subprocess.run(['cc', '-std=c11', '-O2', '-I', str(FW), str(src), str(FW / 'oled.c'), '-o', str(exe)], check=True)
    return exe


def label_value(name):
    order = ['OLED_LABEL_NONE', 'OLED_LABEL_ERR', 'OLED_LABEL_MAX', 'OLED_LABEL_RST', 'OLED_LABEL_LO', 'OLED_LABEL_CHG', 'OLED_LABEL_BAT', 'OLED_LABEL_OPT']
    return order.index(LABELS[name])


def frame(exe, count, label='none', bars=3):
    raw = subprocess.check_output([str(exe), str(count), str(label_value(label)), str(bars)])
    assert len(raw) == 1024
    im = Image.new('L', (128, 64), 0)
    px = im.load()
    for page in range(8):
        for col in range(128):
            b = raw[page * 128 + col]
            for bit in range(8):
                if b & (1 << bit):
                    px[col, page * 8 + bit] = 255
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, default=ROOT / 'build/render-q5-acrylic/oled')
    ap.add_argument('--views', default='0,1,2,3,108,109,2718,12345678')
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='q5a-oled-') as t:
        exe = build(Path(t))
        made = []
        for spec in args.views.split(','):
            count, _, label = spec.partition(':')
            label = label or 'none'
            im = frame(exe, int(count), label)
            name = f'oled_{count}_{label}.png'
            im.save(args.out / name)
            made.append(name)
    (args.out / 'frames.json').write_text(json.dumps(dict(renderer='firmware/q5-stm32/oled.c', frames=made), indent=1) + '\n')
    print(made)


if __name__ == '__main__':
    main()
