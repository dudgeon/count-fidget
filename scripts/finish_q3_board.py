"""Import incremental Q3 routing and fill two outer ground pours only."""
import argparse
from pathlib import Path
import pcbnew as p
from sync_q3_board import sync

OUT=Path(__file__).resolve().parents[1]/'electronics/q3'


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--import-route',action='store_true')
    ap.add_argument('--refill-only',action='store_true')
    args=ap.parse_args()
    assert args.import_route != args.refill_only, 'Choose incremental import or refill only'
    path=OUT/'click-counter-Q3.kicad_pcb'
    board=p.LoadBoard(str(path)); assert board.GetCopperLayerCount()==2
    if args.import_route:
        assert any(item.IsLocked() for item in board.GetTracks()), 'Critical fixed seed is required'
        for item in list(board.GetTracks())+list(board.Zones()):
            if not isinstance(item,p.ZONE) and item.IsLocked(): continue
            if isinstance(item,p.ZONE) and item.GetIsRuleArea(): continue
            board.Remove(item); item.thisown=False
        assert p.ImportSpecctraSES(board,str(OUT/'click-counter-Q3.ses'))
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
    # The router leaves the upper-left VBUS divider branch isolated. The
    # comparator supply has its local bypass; connect this low-current branch
    # around the top of its own sense trace, all on B.Cu without a new via.
    if args.import_route:
        points=[(11.8,3.625),(10.8,3.625),(10.8,.7),(19.8,.7),(19.8,5.7),(20.175,6.075),(21,6.075)]
        for a,b in zip(points,points[1:]):
            item=p.PCB_TRACK(board)
            item.SetStart(p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1])))
            item.SetEnd(p.VECTOR2I(p.FromMM(b[0]),p.FromMM(b[1])))
            item.SetWidth(p.FromMM(.2));item.SetLayer(p.B_Cu)
            item.SetNet(board.FindNet('VBUS'));board.Add(item)
        # The OLED logic bypass gets a direct local branch to the display
        # escape, instead of returning through the remote common supply join.
        def xy(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
        via=p.PCB_VIA(board);via.SetPosition(xy(34.775,4.825));via.SetWidth(p.FromMM(.6));via.SetDrill(p.FromMM(.3))
        via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(board.FindNet('V3'));board.Add(via)
        for layer,points in [(p.B_Cu,[(35.625,4.45),(35.15,4.45),(34.775,4.825)]),
                             (p.F_Cu,[(34.775,4.825),(34.775,4.6852)])]:
            for a,b in zip(points,points[1:]):
                item=p.PCB_TRACK(board);item.SetStart(xy(*a));item.SetEnd(xy(*b))
                item.SetWidth(p.FromMM(.15));item.SetLayer(layer);item.SetNet(board.FindNet('V3'));board.Add(item)
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if (fp.GetReference()=='J1' and pad.GetNumber()=='SH') or (fp.GetReference() in ('U2','U6') and pad.GetNumber()=='11') or (fp.GetReference()=='D1' and pad.GetNumber()=='2'):
                pad.SetLocalZoneConnection(p.ZONE_CONNECTION_FULL)
    for item in list(board.Zones()):
        if not item.GetIsRuleArea(): board.Remove(item);item.thisown=False
    for layer in [p.F_Cu,p.B_Cu]:
        zone=p.ZONE(board);zone.SetLayer(layer);zone.SetNet(board.FindNet('GND'))
        zone.SetLocalClearance(p.FromMM(.15));zone.SetThermalReliefGap(p.FromMM(.2))
        zone.SetThermalReliefSpokeWidth(p.FromMM(.2));zone.SetMinThickness(p.FromMM(.15))
        outline=zone.Outline();outline.NewOutline()
        for x,y in [(.4,.4),(41.6,.4),(41.6,39.6),(.4,39.6)]:outline.Append(p.FromMM(x),p.FromMM(y))
        board.Add(zone)
    p.ZONE_FILLER(board).Fill(board.Zones())
    p.SaveBoard(str(path),board)
    # Explicit requested construction. Fabricator material and tolerances are
    # unqualified; this is a two-layer quotation candidate, not fabrication
    # authorization. 35+930+35 micrometres totals the requested1.0mm.
    source=path.read_text()
    if '(stackup' not in source:
        stack='''
        (stackup
            (layer "F.SilkS" (type "Top Silk Screen") (color "White"))
            (layer "F.Paste" (type "Top Solder Paste"))
            (layer "F.Mask" (type "Top Solder Mask") (color "Green"))
            (layer "F.Cu" (type "copper") (thickness 0.035))
            (layer "dielectric 1" (type "core") (thickness 0.93) (material "FR4 Tg150+ requested") (epsilon_r 4.5) (loss_tangent 0.02))
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
    print('Q3 incremental route and two ground pours saved; fresh DRC required.')


if __name__=='__main__':main()
