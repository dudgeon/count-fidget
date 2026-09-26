"""Import incremental Q5 routing and fill two outer ground pours only."""
import argparse
import json
from pathlib import Path
import pcbnew as p
from sync_q5_board import sync

OUT=Path(__file__).resolve().parents[1]/'electronics/q5'


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--import-route',action='store_true')
    ap.add_argument('--refill-only',action='store_true')
    args=ap.parse_args()
    assert args.import_route != args.refill_only, 'Choose incremental import or refill only'
    path=OUT/'click-counter-Q5.kicad_pcb'
    board=p.LoadBoard(str(path)); assert board.GetCopperLayerCount()==2
    if args.import_route:
        # Retain exactly the recorded original seed. A replay on a completed
        # board must discard the previous post-import cleanup too, otherwise
        # those additional locked tracks/vias would be duplicated.
        def coordinate(q):return (round(p.ToMM(q.x),5),round(p.ToMM(q.y),5))
        def key(item):
            if isinstance(item,p.PCB_VIA):return ('via',item.GetNetname(),coordinate(item.GetPosition()))
            return ('track',item.GetNetname(),p.LayerName(item.GetLayer()),round(p.ToMM(item.GetWidth()),6),tuple(sorted((coordinate(item.GetStart()),coordinate(item.GetEnd())))))
        expected=set()
        for record in json.loads((OUT/'locked-route-seed.json').read_text())['tracks_and_vias']:
            if 'via' in record:expected.add(('via',record['net'],tuple(round(x,5) for x in record['via'])))
            else:
                for a,c in zip(record['points'],record['points'][1:]):
                    if a!=c:expected.add(('track',record['net'],record['layer'],record['width_mm'],tuple(sorted((tuple(round(x,5) for x in a),tuple(round(x,5) for x in c))))))
        retained=[item for item in board.GetTracks() if item.IsLocked() and key(item) in expected]
        assert len(retained)==len(expected) and {key(item) for item in retained}==expected, 'Complete original fixed seed is required'
        for item in list(board.GetTracks())+list(board.Zones()):
            if not isinstance(item,p.ZONE) and item.IsLocked() and key(item) in expected: continue
            if isinstance(item,p.ZONE) and item.GetIsRuleArea(): continue
            board.Remove(item); item.thisown=False
        assert p.ImportSpecctraSES(board,str(OUT/'click-counter-Q5.ses'))
        # Router vias closer than 0.1 mm to a same-net SMT land leave no solder-mask
        # web and invite wicking. Move each one up to 0.5 mm to the first position
        # where it and its moved track ends clear all other-net copper; replayed
        # deterministically from the same SES. Native DRC re-checks the result.
        import math
        from shapely.geometry import LineString, Point, Polygon
        from shapely.ops import unary_union
        def mm(q): return (p.ToMM(q.x),p.ToMM(q.y))
        def land(a,layer):
            ps=a.GetEffectivePolygon(layer);shapes=[]
            for i in range(ps.OutlineCount()):
                o=ps.Outline(i);pts=[(p.ToMM(o.CPoint(j).x),p.ToMM(o.CPoint(j).y)) for j in range(o.PointCount())]
                if len(pts)>=3:shapes.append(Polygon(pts))
            return unary_union(shapes)
        def box_gap(a,x,y,rad):
            box=a.GetBoundingBox();dx=max(p.ToMM(box.GetX())-x,0,x-p.ToMM(box.GetRight()));dy=max(p.ToMM(box.GetY())-y,0,y-p.ToMM(box.GetBottom()))
            return math.hypot(dx,dy)-rad
        pads=[a for fp in board.GetFootprints() for a in fp.Pads()]
        for via in sorted([t for t in board.GetTracks() if isinstance(t,p.PCB_VIA) and not t.IsLocked()],key=lambda t:mm(t.GetPosition())):
            net=via.GetNetname();q=via.GetPosition();vx,vy=mm(q);rad=p.ToMM(via.GetWidth(p.F_Cu))/2
            same=[a for a in pads if a.GetNetname()==net and a.GetAttribute()==p.PAD_ATTRIB_SMD]
            if all(box_gap(a,vx,vy,rad)>=.1 for a in same):continue
            ends=[t for t in board.GetTracks() if not isinstance(t,p.PCB_VIA) and t.GetNetname()==net and q in (t.GetStart(),t.GetEnd())]
            layer_geom={}
            for layer in (p.F_Cu,p.B_Cu):
                g=[land(a,layer) for a in pads if a.GetNetname()!=net and a.IsOnLayer(layer)]
                for t in board.GetTracks():
                    if t.GetNetname()==net:continue
                    if isinstance(t,p.PCB_VIA):g.append(Point(*mm(t.GetPosition())).buffer(p.ToMM(t.GetWidth(p.F_Cu))/2))
                    elif t.GetLayer()==layer:g.append(LineString([mm(t.GetStart()),mm(t.GetEnd())]).buffer(p.ToMM(t.GetWidth())/2))
                layer_geom[layer]=unary_union(g)
            holes=unary_union([Point(*mm(a.GetPosition())).buffer(p.ToMM(a.GetDrillSize().x)/2) for a in pads if a.GetDrillSize().x>0 and a.GetNetname()!=net])
            done=False
            for dist in (.1,.15,.2,.25,.3,.35,.4,.5):
                for k in range(8):
                    nx,ny=round(vx+dist*math.cos(k*math.pi/4),4),round(vy+dist*math.sin(k*math.pi/4),4)
                    if not all(box_gap(a,nx,ny,rad)>=.1 for a in same):continue
                    c=Point(nx,ny)
                    if any(layer_geom[l].distance(c)<rad+.147 for l in layer_geom) or holes.distance(c)<.15+.27:continue
                    ok=True
                    for t in ends:
                        other=t.GetEnd() if t.GetStart()==q else t.GetStart()
                        seg=LineString([mm(other),(nx,ny)]).buffer(p.ToMM(t.GetWidth())/2)
                        if layer_geom[t.GetLayer()].distance(seg)<.147:ok=False;break
                    if not ok:continue
                    new=p.VECTOR2I(p.FromMM(nx),p.FromMM(ny))
                    for t in ends:
                        if t.GetStart()==q:t.SetStart(new)
                        if t.GetEnd()==q:t.SetEnd(new)
                    via.SetPosition(new);done=True;break
                if done:break
            if not done and net=='GND':
                # A GND fanout via with no clear nudge is redundant with the two
                # GND pours and the recorded stitching: remove it, then prune GND
                # stubs left dangling. Native DRC must still report zero unconnected.
                board.Remove(via);via.thisown=False
                while True:
                    ends={}
                    for t in board.GetTracks():
                        if t.GetNetname()!='GND':continue
                        for q2 in ((t.GetPosition(),) if isinstance(t,p.PCB_VIA) else (t.GetStart(),t.GetEnd())):
                            ends[(q2.x,q2.y)]=ends.get((q2.x,q2.y),0)+1
                    padpts=[a for a in pads if a.GetNetname()=='GND']
                    dangling=[t for t in board.GetTracks() if t.GetNetname()=='GND' and not isinstance(t,p.PCB_VIA) and not t.IsLocked()
                              and any(ends[(q2.x,q2.y)]==1 and not any(a.HitTest(q2) for a in padpts) for q2 in (t.GetStart(),t.GetEnd()))]
                    if not dangling:break
                    for t in dangling:board.Remove(t);t.thisown=False
        # Recorded local GND stitching (plan_q5_stitching.py): a short B.Cu stub
        # and through via beside each listed ground pad, so decoupling returns
        # reach both pours locally. Native DRC re-checks every item.
        stitch=OUT/'gnd-stitch.json'
        if stitch.exists():
            def vv(q): return p.VECTOR2I(p.FromMM(q[0]),p.FromMM(q[1]))
            for r in json.loads(stitch.read_text())['vias']:
                if r['via'] is None: continue
                t=p.PCB_TRACK(board);t.SetStart(vv(r['pad_xy']));t.SetEnd(vv(r['via']));t.SetWidth(p.FromMM(r['stub_width_mm']))
                t.SetLayer(p.B_Cu);t.SetNet(board.FindNet('GND'));t.SetLocked(True);board.Add(t)
                via=p.PCB_VIA(board);via.SetPosition(vv(r['via']));via.SetWidth(p.FromMM(.6));via.SetDrill(p.FromMM(.3))
                via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(board.FindNet('GND'));via.SetLocked(True);board.Add(via)
    sync(board)
    # The router's optional SMD fanout can create electrically pointless stubs
    # on single-pad no-connect nets. They have no schematic connection and
    # must not be retained as dangling copper.
    for item in list(board.GetTracks()):
        if item.GetNetname().startswith('unconnected-'):
            assert not item.IsLocked()
            board.Remove(item); item.thisown=False
        elif isinstance(item,p.PCB_TRACK) and not isinstance(item,p.PCB_VIA):
            if item.GetWidth()<p.FromMM(.127): item.SetWidth(p.FromMM(.127))
    # Local solid returns avoid isolated single-spoke islands at these pads.
    # This is copper geometry, not a DRC exclusion; solder process remains to qualify.
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if (fp.GetReference()=='J1' and pad.GetNumber()=='SH') or (fp.GetReference()=='U2' and pad.GetNumber()=='11') or (fp.GetReference() in ('U6','U7') and pad.GetNumber()=='2') or (fp.GetReference()=='U3' and pad.GetNumber() in ('3','5','7')) or (fp.GetReference()=='D1' and pad.GetNumber()=='2') or (fp.GetReference()=='U7' and pad.GetNumber()=='2'):
                pad.SetLocalZoneConnection(p.ZONE_CONNECTION_FULL)
    for item in list(board.Zones()):
        if not item.GetIsRuleArea(): board.Remove(item);item.thisown=False
    for layer in [p.F_Cu,p.B_Cu]:
        zone=p.ZONE(board);zone.SetLayer(layer);zone.SetNet(board.FindNet('GND'))
        zone.SetLocalClearance(p.FromMM(.15));zone.SetThermalReliefGap(p.FromMM(.2))
        zone.SetThermalReliefSpokeWidth(p.FromMM(.2));zone.SetMinThickness(p.FromMM(.15))
        outline=zone.Outline();outline.NewOutline()
        for x,y in [(.4,.4),(41.6,.4),(41.6,53.6),(.4,53.6)]:outline.Append(p.FromMM(x),p.FromMM(y))
        board.Add(zone)
    p.ZONE_FILLER(board).Fill(board.Zones())
    p.SaveBoard(str(path),board)
    # Explicit requested construction. Fabricator material and tolerances are
    # unqualified; this is a two-layer quotation candidate, not fabrication
    # authorization. 35+1530+35 micrometres totals the standard 1.6 mm that the
    # MX hot-swap sockets require (switch pin length).
    source=path.read_text()
    if '(stackup' not in source:
        stack='''
        (stackup
            (layer "F.SilkS" (type "Top Silk Screen") (color "White"))
            (layer "F.Paste" (type "Top Solder Paste"))
            (layer "F.Mask" (type "Top Solder Mask") (color "Green"))
            (layer "F.Cu" (type "copper") (thickness 0.035))
            (layer "dielectric 1" (type "core") (thickness 1.53) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
            (layer "B.Cu" (type "copper") (thickness 0.035))
            (layer "B.Mask" (type "Bottom Solder Mask") (color "Green"))
            (layer "B.Paste" (type "Bottom Solder Paste"))
            (layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))
            (copper_finish "ENIG")
            (dielectric_constraints no)
        )
'''
        assert source.count('\t(setup\n')==1
        path.write_text(source.replace('\t(setup\n','\t(setup\n'+stack,1))
    print('Q5 incremental route and two ground pours saved; fresh DRC required.')


if __name__=='__main__':main()
