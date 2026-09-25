"""Import incremental Q4 routing and fill two outer ground pours only."""
import argparse
import json
from pathlib import Path
import pcbnew as p
from sync_q4_board import sync

OUT=Path(__file__).resolve().parents[1]/'electronics/q4'


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--import-route',action='store_true')
    ap.add_argument('--refill-only',action='store_true')
    args=ap.parse_args()
    assert args.import_route != args.refill_only, 'Choose incremental import or refill only'
    path=OUT/'click-counter-Q4.kicad_pcb'
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
        assert p.ImportSpecctraSES(board,str(OUT/'click-counter-Q4.ses'))
    if args.import_route:
        # Post-router local cleanup, deliberately replayed from the same SES.
        # Keep both USB signals on B.Cu. The autorouter otherwise jumps DM over
        # the ESD clamp's VBUS branch using two avoidable signal vias.
        def xy(q): return (round(p.ToMM(q.x),6),round(p.ToMM(q.y),6))
        def vv(q): return p.VECTOR2I(p.FromMM(q[0]),p.FromMM(q[1]))
        def add_route(net,points,layer=p.B_Cu,width=.2):
            for a,c in zip(points,points[1:]):
                t=p.PCB_TRACK(board);t.SetStart(vv(a));t.SetEnd(vv(c))
                t.SetWidth(p.FromMM(width));t.SetLayer(layer);t.SetNet(board.FindNet(net));t.SetLocked(True);board.Add(t)
        def add_via(net,point):
            t=p.PCB_VIA(board);t.SetPosition(vv(point));t.SetWidth(p.FromMM(.6));t.SetDrill(p.FromMM(.3))
            t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(board.FindNet(net));t.SetLocked(True);board.Add(t)
        removed_dm=0; removed_vbus=0
        old_vbus={frozenset(v) for v in [((30.6625,27.0),(30.908,27.0)),((30.908,27.0),(31.5751,26.3329)),((31.5751,26.3329),(31.5751,24.6))]}
        for t in list(board.GetTracks()):
            a,c=xy(t.GetStart()),xy(t.GetEnd())
            remove=False
            if t.GetNetname()=='USB_DM' and not t.IsLocked() and all(30<x<33.1 and 24.8<y<=26.1 for x,y in (a,c)):
                remove=True;removed_dm+=1
            if t.GetNetname()=='VBUS' and frozenset((a,c)) in old_vbus:
                remove=True;removed_vbus+=1
            if remove:board.Remove(t);t.thisown=False
        assert removed_dm==7 and removed_vbus==3,(removed_dm,removed_vbus)
        add_route('USB_DM',[(30.6625,26.05),(30.6625,25.45),(32.9375,25.45),(32.9375,26.05)])
        add_route('VBUS',[(30.6625,27.0),(31.4,26.6),(31.8,26.1)],width=.15)
        add_via('VBUS',(31.8,26.1));add_via('VBUS',(31.8,24.3))
        add_route('VBUS',[(31.8,26.1),(31.8,24.3)],p.F_Cu,.2)
        add_route('VBUS',[(31.8,24.3),(31.5751,24.6)],width=.2)
        # Give the only close same-net SMT fanout a wider solder-land gap.
        old=(5.8597,34.3153);new=(5.9597,34.2153)
        moved=0
        for t in board.GetTracks():
            if t.GetNetname()!='VLOGIC':continue
            if isinstance(t,p.PCB_VIA):
                if xy(t.GetPosition())==old:t.SetPosition(vv(new));moved+=1
            else:
                if xy(t.GetStart())==old:t.SetStart(vv(new))
                if xy(t.GetEnd())==old:t.SetEnd(vv(new))
        assert moved==1,moved
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
            if (fp.GetReference()=='J1' and pad.GetNumber()=='SH') or (fp.GetReference() in ('U2','U6') and pad.GetNumber()=='11') or (fp.GetReference()=='D1' and pad.GetNumber()=='2') or (fp.GetReference()=='J2' and pad.GetNumber()=='4') or (fp.GetReference()=='U7' and pad.GetNumber()=='2'):
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
    print('Q4 incremental route and two ground pours saved; fresh DRC required.')


if __name__=='__main__':main()
