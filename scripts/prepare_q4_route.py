"""Apply the Q4 placement model and explicitly reset Q4 routing, keeping UUIDs."""
import argparse
import json
from pathlib import Path
import pcbnew as p
from build_q4_model import make_model
from sync_q4_board import sync

OUT=Path(__file__).resolve().parents[1]/'electronics/q4'


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--reset-route',action='store_true',required=True)
    ap.parse_args()
    model=make_model();path=OUT/'click-counter-Q4.kicad_pcb'
    board=p.LoadBoard(str(path));assert board.GetCopperLayerCount()==2
    footprints={f.GetReference():f for f in board.GetFootprints()}
    assert set(footprints)=={part['ref'] for part in model['parts']}
    for part in model['parts']:
        fp=footprints[part['ref']]
        assert fp.GetFPID().GetLibItemName()==part['footprint'].split(':')[1]
        assert fp.IsFlipped()==(part['side']=='bottom')
        fp.SetOrientationDegrees(part['rotation'])
        fp.SetPosition(p.VECTOR2I(p.FromMM(part['x']),p.FromMM(part['y'])))
    for item in list(board.GetTracks())+list(board.Zones()):
        if isinstance(item,p.ZONE) and item.GetIsRuleArea():continue
        board.Remove(item);item.thisown=False
    sync(board);p.SaveBoard(str(path),board)
    (OUT/'netlist-Q4.json').write_text(json.dumps(model,indent=2)+'\n')
    print('Q4 placements applied; routes reset with footprint UUIDs preserved. Run preroute_q4 next.')


if __name__=='__main__':main()
