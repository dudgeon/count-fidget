"""Plan an unambiguous silkscreen pin-1 dot for every polarised Q5 part.

Why: the canonical footprints were inherited without silkscreen bodies, so an
assembler's engineer had nothing on the board to confirm orientation against
(JLC queried exactly the unmarked parts on the first order). Each polarised
part now gets a filled 0.5 mm silk dot beside pin 1. The dot is placed where it

* clears every copper pad and via drill by >= 0.2 mm where possible, never less
  than JLC's 0.15 mm silkscreen-to-pad minimum (vias are tented) and other silkscreen by >= 0.15 mm,
* stays outside the part's own body and every other part's body (so it stays
  visible after assembly) and, where possible, outside other parts' courtyards,
* stays >= 0.5 mm inside the board edge, and
* is unambiguous: its distance to pin 1 is at most 0.75 x its distance to any
  other pad of the same part (so it sits beside pin 1, never between pins) and
  closer to pin 1 than to any pad of another part.

The plan is recorded in electronics/q5/pin1-markers.json and applied by
finish_q5_board.py as board-level silkscreen (footprints stay identical to
the library); verify_q5.py re-checks every rule on the saved board.
Run after placement/routing: python3 scripts/plan_q5_pin1_marks.py
"""
import json
import math
from pathlib import Path
import pcbnew as p
from shapely.geometry import Point, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'electronics/q5'
POLARISED = ['U1', 'U2', 'U3', 'U4', 'U5', 'U6', 'U7', 'U8', 'Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'D1', 'D2', 'D3', 'D4']
DOT_R = 0.25
PAD_CLEAR, MIN_PAD_CLEAR, SILK_CLEAR, EDGE_CLEAR, AMBIGUITY, NEIGHBOUR = 0.2, 0.15, 0.15, 0.5, 0.75, 1.0


def mm(q):
    return (p.ToMM(q.x), p.ToMM(q.y))


def bbox_poly(bb, grow=0.0):
    return box(p.ToMM(bb.GetLeft()) - grow, p.ToMM(bb.GetTop()) - grow, p.ToMM(bb.GetRight()) + grow, p.ToMM(bb.GetBottom()) + grow)


def layer_items(fp, layers):
    return [g for g in fp.GraphicalItems() if g.GetLayer() in layers]


def is_marker(g):
    return (isinstance(g, p.PCB_SHAPE) and g.GetShape() == p.SHAPE_T_CIRCLE and g.IsSolidFill()
            and g.GetLayer() in (p.F_SilkS, p.B_SilkS) and abs(p.ToMM(g.GetRadius()) - DOT_R) < 1e-4)


def pad_xy(pad):
    return mm(pad.GetPosition())


def existing_marker(f):
    """True when the footprint's own silkscreen already marks pin 1: a pin-1 polygon
    (KiCad triangle) or, for a two-terminal diode, the cathode bar at pad 1."""
    pads = {q.GetNumber(): q for q in f.Pads() if q.GetNumber()}
    silk = [g for g in f.GraphicalItems() if g.GetLayer() in (p.F_SilkS, p.B_SilkS) and not is_marker(g)]
    def nearest(g):
        c = mm(g.GetBoundingBox().GetCenter())
        return min(pads, key=lambda n: math.dist(c, pad_xy(pads[n])))
    if any(g.GetShape() == p.SHAPE_T_POLY and nearest(g) == '1' for g in silk):
        return 'pin-1 triangle'
    if len(pads) == 2 and len(silk) >= 2 and all(nearest(g) == '1' for g in silk):
        return 'cathode bar at pad 1'
    return None


def plan(board):
    w = max(p.ToMM(d.GetEnd().x) for d in board.GetDrawings() if d.GetLayer() == p.Edge_Cuts)
    h = max(p.ToMM(d.GetEnd().y) for d in board.GetDrawings() if d.GetLayer() == p.Edge_Cuts)
    inner = box(EDGE_CLEAR, EDGE_CLEAR, w - EDGE_CLEAR, h - EDGE_CLEAR)
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    copper = {s: [] for s in ('top', 'bottom')}
    for f in board.GetFootprints():
        for pad in f.Pads():
            poly = bbox_poly(pad.GetBoundingBox())
            if pad.GetAttribute() in (p.PAD_ATTRIB_PTH, p.PAD_ATTRIB_NPTH):
                copper['top'].append(poly); copper['bottom'].append(poly)
            else:
                copper['bottom' if f.IsFlipped() else 'top'].append(poly)
    for t in board.GetTracks():
        if isinstance(t, p.PCB_VIA):
            # Vias are tented on both sides (board setup), so silk may cross them;
            # only the drilled hole is kept clear (drill radius; PAD_CLEAR adds margin).
            c = Point(*mm(t.GetPosition())).buffer(p.ToMM(t.GetDrillValue()) / 2)
            copper['top'].append(c); copper['bottom'].append(c)
    copper = {s: unary_union(v) for s, v in copper.items()}
    plans, placed = [], []
    for ref in POLARISED:
        f = fps[ref]
        if existing_marker(f):
            continue
        side = 'bottom' if f.IsFlipped() else 'top'
        silk_layer, fab_layer, crt_layer = ((p.B_SilkS, p.B_Fab, p.B_CrtYd) if side == 'bottom' else (p.F_SilkS, p.F_Fab, p.F_CrtYd))
        others_silk = unary_union([bbox_poly(g.GetBoundingBox()) for o in board.GetFootprints()
                                   for g in layer_items(o, [silk_layer]) if not is_marker(g)] or [Point(-99, -99)])
        body = unary_union([bbox_poly(g.GetBoundingBox()) for g in layer_items(f, [fab_layer])]).envelope
        foreign_crt = unary_union([bbox_poly(g.GetBoundingBox()) for o in board.GetFootprints() if o.GetReference() != ref
                                   and o.IsFlipped() == f.IsFlipped() for g in layer_items(o, [crt_layer])])
        foreign_body = unary_union([unary_union([bbox_poly(g.GetBoundingBox()) for g in layer_items(o, [fab_layer])
                                                 if isinstance(g, p.PCB_SHAPE)]).envelope
                                    for o in board.GetFootprints() if o.GetReference() != ref and o.IsFlipped() == f.IsFlipped()
                                    and layer_items(o, [fab_layer])])
        pads = {pad.GetNumber(): pad for pad in f.Pads() if pad.GetNumber()}
        p1 = pads['1']
        c1 = mm(p1.GetPosition())
        others = [mm(q.GetPosition()) for n, q in pads.items() if n != '1']
        # Pads of every other part on the same side: the dot must belong visibly to this part.
        neighbours = [mm(q.GetPosition()) for o in board.GetFootprints() if o.GetReference() != ref
                      and o.IsFlipped() == f.IsFlipped() for q in o.Pads()]
        cands = sorted(((round(c1[0] + 0.05 * i, 3), round(c1[1] + 0.05 * j, 3)) for i in range(-50, 51) for j in range(-50, 51)),
                       key=lambda q: math.dist(q, c1))
        best = None
        for strict, pad_clear in ((True, PAD_CLEAR), (False, PAD_CLEAR), (True, MIN_PAD_CLEAR), (False, MIN_PAD_CLEAR)):
            for x, y in cands:
                dot = Point(x, y).buffer(DOT_R)
                d1 = math.dist((x, y), c1)
                dmin = min(math.dist((x, y), o) for o in others)
                if d1 > AMBIGUITY * dmin or not inner.contains(dot):
                    continue
                if d1 >= NEIGHBOUR * min(math.dist((x, y), o) for o in neighbours):
                    continue
                if dot.buffer(pad_clear).intersects(copper[side]) or dot.intersects(body) or dot.intersects(foreign_body):
                    continue
                if dot.buffer(SILK_CLEAR).intersects(others_silk):
                    continue
                if any(dot.buffer(SILK_CLEAR).intersects(q) for q in placed):
                    continue
                if strict and dot.intersects(foreign_crt):
                    continue
                best = (x, y, round(d1, 3), round(dmin, 3), strict, pad_clear)
                break
            if best:
                break
        assert best, f'{ref}: no legal pin-1 marker position'
        placed.append(Point(best[0], best[1]).buffer(DOT_R))
        plans.append(dict(ref=ref, side=side, pad1_xy=[round(c1[0], 4), round(c1[1], 4)], marker_xy=[best[0], best[1]],
                          radius_mm=DOT_R, distance_to_pin1_mm=best[2], distance_to_nearest_other_pad_mm=best[3],
                          outside_other_courtyards=best[4], pad_clearance_mm=best[5]))
    return plans


def main():
    board = p.LoadBoard(str(OUT / 'click-counter-Q5.kicad_pcb'))
    plans = plan(board)
    (OUT / 'pin1-markers.json').write_text(json.dumps(dict(
        schema=1, purpose='Silkscreen pin-1 dot per polarised part; applied by finish_q5_board.py, re-checked by verify_q5.py',
        rules=dict(dot_radius_mm=DOT_R, pad_and_via_clearance_mm=PAD_CLEAR, minimum_pad_clearance_mm=MIN_PAD_CLEAR, silk_clearance_mm=SILK_CLEAR,
                   edge_clearance_mm=EDGE_CLEAR, max_ratio_pin1_to_other_pad_distance=AMBIGUITY,
                   max_ratio_pin1_to_other_part_pad_distance=NEIGHBOUR),
        markers=plans), indent=1) + '\n')
    for f in board.GetFootprints():
        if f.GetReference() in POLARISED and existing_marker(f):
            print(f.GetReference(), 'already marked:', existing_marker(f))
    for m in plans:
        print(m['ref'], m['marker_xy'], 'd1', m['distance_to_pin1_mm'], 'dother', m['distance_to_nearest_other_pad_mm'], 'clear', m['pad_clearance_mm'],
              '' if m['outside_other_courtyards'] else '(inside another courtyard)')


if __name__ == '__main__':
    main()
