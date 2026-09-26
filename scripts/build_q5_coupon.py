"""Print-tolerance coupon for the Q5 key plate and keycap cross sockets (first-article test G0).

One flat strip carries three 1.5 mm plate sections with square switch holes of
13.95 / 14.05 / 14.15 mm (nominal 14.05 in build_q5_enclosure.py) and three 5.5 mm
bosses with 3.5 mm deep MX cross sockets whose arms are -0.05 / nominal / +0.05 mm
(nominal 1.32 x 4.05 and 1.12 x 4.05). Print in the enclosure material and orientation,
clip a CPG151101D13 switch into each hole and press a stem into each socket; choose the
firm/snug pair and change the nominal in build_q5_enclosure.py.
Writes mechanical/q5/tolerance-coupon-Q5.stl.
"""
from pathlib import Path
import cadquery as cq

OUT = Path(__file__).resolve().parents[1] / 'mechanical/q5/tolerance-coupon-Q5.stl'
PLATE_T, SOCKET_DEPTH = 1.5, 3.5
HOLES = (13.95, 14.05, 14.15)
ARM_DELTA = (-0.05, 0.0, 0.05)


def block(w, d, h, z, x=0, y=0):
    return cq.Workplane('XY').box(w, d, h, centered=(True, True, False)).translate((x, y, z))


def label(text, x, y, z):
    return cq.Workplane('XY').text(text, 3.0, 0.4, halign='center', valign='center').translate((x, y, z))


def main():
    pitch = 20.0
    body = block(3 * pitch, 21.0, PLATE_T, 0, pitch, 0)
    body = body.union(block(3 * pitch, 12.0, SOCKET_DEPTH + 1.0, 0, pitch, -16.5))
    for i, (hole, delta) in enumerate(zip(HOLES, ARM_DELTA)):
        x = i * pitch
        body = body.cut(block(hole, hole, PLATE_T + .2, -.1, x, 0))
        z = 1.0
        cross = block(1.32 + delta, 4.05 + delta, SOCKET_DEPTH + .1, z, x, -16.5).union(
            block(4.05 + delta, 1.12 + delta, SOCKET_DEPTH + .1, z, x, -16.5))
        body = body.cut(cross)
        body = body.union(label(('-', '0', '+')[i], x + 6.5, -16.5, SOCKET_DEPTH + 1.0))
    cq.exporters.export(body, str(OUT), tolerance=0.01, angularTolerance=0.1)
    assert body.val().isValid()
    print('wrote', OUT.relative_to(OUT.parents[2]), 'holes', HOLES, 'cross arm deltas', ARM_DELTA)


if __name__ == '__main__':
    main()
