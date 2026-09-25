"""Import the Q2 route and fill its ground planes; never changes Q1."""
import argparse
from pathlib import Path
import pcbnew as p
from sync_q2_board import sync

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'electronics/q2'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--import-route', action='store_true', help='Keep locked critical routes and import the matching incremental SES')
    parser.add_argument('--refill-only', action='store_true', help='Keep current routes, synchronize fields and refill zones')
    args = parser.parse_args()
    assert not (args.import_route and args.refill_only)
    path = OUT / 'click-counter-Q2.kicad_pcb'
    board = p.LoadBoard(str(path))
    if args.import_route:
        assert any(item.IsLocked() for item in board.GetTracks()), 'Run the Q2 builder and critical prerouter before importing its incremental SES'
        for item in list(board.GetTracks()) + list(board.Zones()):
            if not isinstance(item, p.ZONE) and item.IsLocked():
                continue
            board.Remove(item)
            item.thisown = False
    if not args.refill_only:
        assert args.import_route or not len(board.GetTracks()), 'Use --import-route to keep the fixed seed and replace general routes, or --refill-only'
        if not p.ImportSpecctraSES(board, str(OUT / 'click-counter-Q2.ses')):
            raise RuntimeError('Q2 route import failed')
    sync(board)
    # The saved general-router session terminates at the earlier Q4 return
    # location. Keep that session usable after moving the locked via clear of
    # the solderable source land; move every incident GND endpoint together.
    old_return = p.VECTOR2I(p.FromMM(19.05), p.FromMM(27.55))
    new_return = p.VECTOR2I(p.FromMM(19.05), p.FromMM(26.8))
    for item in board.GetTracks():
        if item.GetNetname() != 'GND':
            continue
        if isinstance(item, p.PCB_VIA):
            if item.GetPosition() == old_return:
                item.SetPosition(new_return)
        else:
            if item.GetStart() == old_return:
                item.SetStart(new_return)
            if item.GetEnd() == old_return:
                item.SetEnd(new_return)
    # This through-hole switch ground land otherwise connects only to a small
    # thermal island on In1.Cu. Use a solid plane connection and disclose the
    # resulting solder heat demand in the assembly instructions.
    for fp in board.GetFootprints():
        if fp.GetReference() == 'SW2':
            for pad in fp.Pads():
                if pad.GetNumber() == '2':
                    pad.SetLocalZoneConnection(p.ZONE_CONNECTION_FULL)
    # Specctra conversion can round a nominal five-mil track down by 1 nm.
    for item in board.GetTracks():
        if isinstance(item, p.PCB_TRACK) and not isinstance(item, p.PCB_VIA):
            if item.GetWidth() < p.FromMM(.127):
                item.SetWidth(p.FromMM(.127))
    if not len(board.Zones()):
        for layer in [p.In1_Cu, p.In2_Cu]:
            zone = p.ZONE(board)
            zone.SetLayer(layer)
            zone.SetNet(board.FindNet('GND'))
            zone.SetLocalClearance(p.FromMM(.15))
            zone.SetThermalReliefGap(p.FromMM(.2))
            zone.SetThermalReliefSpokeWidth(p.FromMM(.2))
            zone.SetMinThickness(p.FromMM(.15))
            outline = zone.Outline()
            outline.NewOutline()
            for x, y in [(1.3,1.3),(40.7,1.3),(40.7,38.7),(1.3,38.7)]:
                outline.Append(p.FromMM(x), p.FromMM(y))
            board.Add(zone)
    p.ZONE_FILLER(board).Fill(board.Zones())
    p.SaveBoard(str(path), board)
    # Requested construction only; dielectric allocation is provisional until
    # the fabricator confirms its material, process and finished tolerances.
    text = path.read_text()
    if '(stackup' not in text:
        stack = '''
        (stackup
            (layer "F.SilkS" (type "Top Silk Screen") (color "White"))
            (layer "F.Paste" (type "Top Solder Paste"))
            (layer "F.Mask" (type "Top Solder Mask") (color "Green"))
            (layer "F.Cu" (type "copper") (thickness 0.035))
            (layer "dielectric 1" (type "prepreg") (thickness 0.2) (material "FR4 Tg150+ requested") (epsilon_r 4.5) (loss_tangent 0.02))
            (layer "In1.Cu" (type "copper") (thickness 0.0175))
            (layer "dielectric 2" (type "core") (thickness 0.495) (material "FR4 Tg150+ requested") (epsilon_r 4.5) (loss_tangent 0.02))
            (layer "In2.Cu" (type "copper") (thickness 0.0175))
            (layer "dielectric 3" (type "prepreg") (thickness 0.2) (material "FR4 Tg150+ requested") (epsilon_r 4.5) (loss_tangent 0.02))
            (layer "B.Cu" (type "copper") (thickness 0.035))
            (layer "B.Mask" (type "Bottom Solder Mask") (color "Green"))
            (layer "B.Paste" (type "Bottom Solder Paste"))
            (layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))
            (copper_finish "ENIG")
            (dielectric_constraints no)
        )
'''
        assert text.count('\t(setup\n') == 1
        path.write_text(text.replace('\t(setup\n','\t(setup\n'+stack,1))
    print('Q2 routes imported and ground planes filled; DRC remains required.')


if __name__ == '__main__':
    main()
