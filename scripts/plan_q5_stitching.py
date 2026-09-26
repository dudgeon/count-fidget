"""Plan local GND stitching vias beside Q5 bypass/ground pads on the routed board.

The headless router connects GND with traces; both outer layers are later
filled with GND. This planner adds one via (plus a short B.Cu stub) beside
each listed ground pad so every decoupling return reaches both pours locally.
It only proposes positions clear of all other-net copper, holes and the board
edge with margin, writes electronics/q5/gnd-stitch.json, and changes nothing
else. finish_q5_board.py applies the recorded list; fresh native DRC decides.
"""
import json
import math
from pathlib import Path
import pcbnew as p
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

OUT = Path(__file__).resolve().parents[1] / 'electronics/q5'
TARGETS = [('C1', '2'), ('C2', '2'), ('C3', '2'), ('C5', '2'), ('C6', '2'), ('C9', '2'), ('C20', '2'),
           ('C30', '2'), ('C31', '2'), ('C32', '2'), ('C33', '2'), ('C34', '2'), ('C35', '2'), ('C36', '2'),
           ('C37', '2'), ('C38', '2'), ('C39', '2'), ('C7', '2'), ('C10', '2'), ('C11', '2'), ('C12', '2'),
           ('U1', '8'), ('U1', '23'), ('U1', '35'), ('U1', '47'), ('U2', '5'), ('U3', '3'), ('U6', '2'), ('U7', '2'),
           ('U8', '4'), ('D1', '2'), ('D2', '2'), ('R9', '2'), ('R31', '2'), ('R37', '2')]
VIA_R, CLEAR, MARGIN = 0.3, 0.127, 0.06


def pad_poly(pad, layer):
    ps = pad.GetEffectivePolygon(layer)
    shapes = []
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        pts = [(p.ToMM(o.CPoint(j).x), p.ToMM(o.CPoint(j).y)) for j in range(o.PointCount())]
        if len(pts) >= 3:
            shapes.append(Polygon(pts))
    return unary_union(shapes)


def main():
    b = p.LoadBoard(str(OUT / 'click-counter-Q5.kicad_pcb'))
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    other = {p.F_Cu: [], p.B_Cu: []}
    holes = []
    for f in b.GetFootprints():
        for a in f.Pads():
            for layer in (p.F_Cu, p.B_Cu):
                if a.IsOnLayer(layer) and a.GetNetname() != 'GND':
                    other[layer].append(pad_poly(a, layer))
            if a.GetDrillSize().x > 0:
                q = a.GetPosition(); holes.append(Point(p.ToMM(q.x), p.ToMM(q.y)).buffer(p.ToMM(a.GetDrillSize().x) / 2))
    for t in b.GetTracks():
        if t.GetNetname() == 'GND':
            if isinstance(t, p.PCB_VIA):
                q = t.GetPosition(); holes.append(Point(p.ToMM(q.x), p.ToMM(q.y)).buffer(.15))
            continue
        if isinstance(t, p.PCB_VIA):
            q = t.GetPosition(); c = Point(p.ToMM(q.x), p.ToMM(q.y))
            for layer in (p.F_Cu, p.B_Cu): other[layer].append(c.buffer(p.ToMM(t.GetWidth(p.F_Cu)) / 2))
            holes.append(c.buffer(.15))
        else:
            a, c = t.GetStart(), t.GetEnd()
            other[t.GetLayer()].append(LineString([(p.ToMM(a.x), p.ToMM(a.y)), (p.ToMM(c.x), p.ToMM(c.y))]).buffer(p.ToMM(t.GetWidth()) / 2))
    blocked = {layer: unary_union(g) for layer, g in other.items()}
    gnd_pads = [a for f in b.GetFootprints() for a in f.Pads() if a.GetNetname() == 'GND' and a.GetAttribute() == p.PAD_ATTRIB_SMD]
    def box_gap(a, x, y):
        bb = a.GetBoundingBox()
        dx = max(p.ToMM(bb.GetX()) - x, 0, x - p.ToMM(bb.GetRight())); dy = max(p.ToMM(bb.GetY()) - y, 0, y - p.ToMM(bb.GetBottom()))
        return math.hypot(dx, dy) - VIA_R
    gnd_lands = unary_union([pad_poly(a, p.B_Cu) for f in b.GetFootprints() for a in f.Pads()
                             if a.GetNetname() == 'GND' and a.IsOnLayer(p.B_Cu) and a.GetAttribute() == p.PAD_ATTRIB_SMD])
    hole_union = unary_union(holes)
    inner = box(0.3 + VIA_R + MARGIN, 0.3 + VIA_R + MARGIN, 42 - 0.3 - VIA_R - MARGIN, 54 - 0.3 - VIA_R - MARGIN)
    placed, records = [], []
    for ref, number in TARGETS:
        pad = next(a for a in fps[ref].Pads() if a.GetNumber() == number)
        assert pad.GetNetname() == 'GND', (ref, number)
        q = pad.GetPosition(); cx, cy = p.ToMM(q.x), p.ToMM(q.y)
        own = pad_poly(pad, p.B_Cu)
        best = None
        for dist in (0.9, 1.05, 1.2, 1.4, 1.6, 1.8, 2.0):
            for k in range(16):
                ang = 2 * math.pi * k / 16
                vx, vy = round(cx + dist * math.cos(ang), 3), round(cy + dist * math.sin(ang), 3)
                via = Point(vx, vy).buffer(VIA_R)
                if not inner.contains(Point(vx, vy)): continue
                # No via-in-pad: keep >=0.15 mm of solder mask web to every GND land.
                if gnd_lands.distance(Point(vx, vy)) < VIA_R + 0.15: continue
                if min(box_gap(a, vx, vy) for a in gnd_pads) < 0.12: continue
                keep = VIA_R + CLEAR + MARGIN
                if any(g.distance(Point(vx, vy)) < keep for g in (blocked[p.F_Cu], blocked[p.B_Cu])): continue
                if hole_union.distance(Point(vx, vy)) < 0.15 + 0.25 + MARGIN: continue
                if any(Point(vx, vy).distance(Point(px, py)) < 2 * VIA_R + CLEAR + MARGIN for px, py in placed): continue
                stub = LineString([(cx, cy), (vx, vy)]).buffer(0.1)
                if stub.difference(own).distance(blocked[p.B_Cu]) < CLEAR + MARGIN and not stub.difference(own).is_empty: continue
                best = (vx, vy); break
            if best: break
        if best:
            placed.append(best)
            records.append(dict(ref=ref, pad=number, pad_xy=[round(cx, 4), round(cy, 4)], via=list(best), stub_width_mm=0.2))
        else:
            records.append(dict(ref=ref, pad=number, pad_xy=[round(cx, 4), round(cy, 4)], via=None, reason='no clear position'))
    (OUT / 'gnd-stitch.json').write_text(json.dumps(dict(revision='Q5', method=__doc__.split('\n')[0], vias=records), indent=2) + '\n')
    print(f"{sum(r['via'] is not None for r in records)}/{len(records)} ground pads received a local stitching via")


if __name__ == '__main__':
    main()
