"""Vendor polarity reference for the Q5 board: one picture per assembled side plus a table.

Assemblers' engineers check part orientation against a 2D view of the bottom side
seen from below (mirrored), which is exactly how JLC's placement photos are drawn.
This sheet shows that view with every polarised part's pin 1 ringed and labelled with
its function, so an engineering query can be answered by pointing at it. The table
lists pin-1 function, board and bottom-view coordinates, the silkscreen marker type
and the JLC-corrected CPL rotation for each polarised part.

Writes procurement/q5/POLARITY-REFERENCE-Q5-BOTTOM.png, -TOP.png, .pdf and .csv.
Run: python3 scripts/polarity_reference_q5.py   (KiCad Python bindings, Pillow)
"""
import csv
import json
import math
import re
from pathlib import Path
import pcbnew as p
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
Q5 = ROOT / 'electronics/q5'
OUT = ROOT / 'procurement/q5'
POLARISED = ['U1', 'U2', 'U3', 'U4', 'U5', 'U6', 'U7', 'U8', 'Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'D1', 'D2', 'D3', 'D4', 'BT1', 'DS1']
S, M = 40, 380            # px per mm, side margin px (room for labels)
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def mm(q):
    return p.ToMM(q.x), p.ToMM(q.y)


def main():
    board = p.LoadBoard(str(Q5 / 'click-counter-Q5.kicad_pcb'))
    model = {q['ref']: q for q in json.loads((Q5 / 'netlist-Q5.json').read_text())['parts']}
    marks = {m['ref']: m for m in json.loads((Q5 / 'pin1-markers.json').read_text())['markers']}
    cpl = {}
    for name in ('CPL-JLCPCB-Q5-FULL-ASSEMBLY-JLC-CORRECTED.csv',):
        for r in csv.DictReader(open(OUT / name, newline='', encoding='utf-8-sig')):
            cpl[r['Designator']] = r
    w, h, _ = json.loads((Q5 / 'netlist-Q5.json').read_text())['board_mm']
    font = ImageFont.truetype(FONT, 30); small = ImageFont.truetype(FONT, 22); title = ImageFont.truetype(FONT, 40)
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    rows, images = [], []
    for side in ('bottom', 'top'):
        mirror = side == 'bottom'
        def px(x, y):
            return (M + ((w - x) if mirror else x) * S, 140 + y * S)
        img = Image.new('RGB', (int(w * S + 2 * M), int(h * S + 400)), (18, 70, 32))
        d = ImageDraw.Draw(img)
        d.rectangle([px(0, 0)[0] if not mirror else px(w, 0)[0], px(0, 0)[1], px(w, 0)[0] if not mirror else px(0, 0)[0], px(0, h)[1]],
                    outline=(230, 230, 230), width=4, fill=(34, 110, 50))
        d.text((30, 12), f'Count Fidget Q5 - {side.upper()} side', fill=(255, 255, 255), font=title)
        d.text((30, 62), 'seen from BELOW (mirrored), as in JLC placement photos' if mirror else 'seen from above', fill=(255, 255, 255), font=small)
        boxes = []
        layer_cu = p.B_Cu if mirror else p.F_Cu
        for f in board.GetFootprints():
            on_side = f.IsFlipped() == mirror
            for pad in f.Pads():
                if not (pad.IsOnLayer(layer_cu)):
                    continue
                bb = pad.GetBoundingBox()
                a, b = px(p.ToMM(bb.GetLeft()), p.ToMM(bb.GetTop())), px(p.ToMM(bb.GetRight()), p.ToMM(bb.GetBottom()))
                d.rectangle([min(a[0], b[0]), a[1], max(a[0], b[0]), b[1]], fill=(200, 200, 200) if on_side else (120, 150, 120))
            if on_side and f.GetReference() in model and not f.GetReference().startswith(('TP', 'H')):
                c = px(*mm(f.GetPosition()))
                d.text((c[0] - 18, c[1] - 12), f.GetReference(), fill=(255, 255, 120), font=small)
        for g in board.GetDrawings():
            if isinstance(g, p.PCB_SHAPE) and g.GetShape() == p.SHAPE_T_CIRCLE and g.GetLayer() == (p.B_SilkS if mirror else p.F_SilkS):
                c = px(*mm(g.GetCenter())); r = p.ToMM(g.GetRadius()) * S
                d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=(255, 255, 255))
        for ref in POLARISED:
            f = fps[ref]
            if (f.IsFlipped() != mirror) and ref != 'DS1':
                continue
            if ref == 'DS1' and mirror:
                continue
            pad1 = next(q for q in f.Pads() if q.GetNumber() == '1')
            part = model[ref]
            fn = re.sub(r'_\d+$', '', pad1.GetPinFunction() or '') or part['pins'].get('1', '')
            net = part['pins'].get('1', '')
            x, y = mm(pad1.GetPosition()); c = px(x, y)
            d.ellipse([c[0] - 26, c[1] - 26, c[0] + 26, c[1] + 26], outline=(255, 0, 255), width=7)
            label = f'{ref} pin 1 = {fn}' + (f' ({net})' if net and net != fn else '')
            if ref == 'BT1':
                label = 'BT1 pad 1 = + (CELL_P)'
            if ref == 'D4':
                label = 'D4 pad 1 = cathode (VBUS_WAKE)'
            tw = d.textlength(label, font=font)
            options = [(c[0] + dx, c[1] + dy) if dx > 0 else (c[0] + dx - tw, c[1] + dy)
                       for dy in (-44, 8, -90, 50, -136, 96, -182, 142) for dx in (32, -32, 140, -140)]
            def free(o):
                bx = (o[0], o[1], o[0] + tw, o[1] + 34)
                return (bx[0] >= 5 and bx[2] <= img.width - 5 and bx[1] >= 95 and bx[3] <= img.height - 80
                        and all(bx[2] < q[0] or bx[0] > q[2] or bx[3] < q[1] or bx[1] > q[3] for q in boxes))
            tx, ty = next((o for o in options if free(o)), options[0])
            boxes.append((tx, ty, tx + tw, ty + 34))
            d.line([c, (tx if tx > c[0] else tx + tw, ty + 17)], fill=(255, 120, 255), width=3)
            d.text((tx, ty), label, fill=(255, 120, 255), font=font, stroke_width=3, stroke_fill=(0, 0, 0))
            marker = ('board silk dot' if ref in marks else 'footprint pin-1 triangle' if ref in ('U1', 'U3', 'U5', 'U8')
                      else 'cathode bar' if ref == 'D4' else '+/- silk marks' if ref == 'BT1' else 'square pad 1 (THT header)')
            vx, vy = ((w - x) if mirror else x), y
            rows.append(dict(ref=ref, side=side, mpn=part['mpn'], lcsc=part.get('lcsc', ''), pin1_function=fn, pin1_net=net,
                             pin1_board_x_mm=round(x, 3), pin1_board_y_mm=round(y, 3),
                             pin1_view_x_mm=round(vx, 3), pin1_view_y_mm=round(vy, 3), silk_marker=marker,
                             jlc_cpl_rotation=cpl.get(ref, {}).get('Rotation', '')))
        d.text((30, img.height - 70), 'Magenta ring = pin 1 (or +/cathode) of every polarised part.  White dots = silkscreen pin-1 dots.  '
               'Coordinates in POLARITY-REFERENCE-Q5.csv.', fill=(255, 255, 255), font=small)
        path = OUT / f'POLARITY-REFERENCE-Q5-{side.upper()}.png'
        img.save(path, optimize=True)
        images.append(img)
    images[0].save(OUT / 'POLARITY-REFERENCE-Q5.pdf', save_all=True, append_images=images[1:], resolution=150)
    with open(OUT / 'POLARITY-REFERENCE-Q5.csv', 'w', newline='') as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0])); wr.writeheader(); wr.writerows(rows)
    print('polarity reference:', len(rows), 'parts;', ', '.join(r['ref'] for r in rows))


if __name__ == '__main__':
    main()
