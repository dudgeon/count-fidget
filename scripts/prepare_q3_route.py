"""Apply the Q3 placement model and explicitly reset Q3 routing, keeping UUIDs."""
import argparse
import json
from pathlib import Path
import pcbnew as p
from build_q3_model import make_model
from sync_q3_board import sync

OUT=Path(__file__).resolve().parents[1]/'electronics/q3'


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--reset-route',action='store_true',required=True)
    ap.parse_args()
    model=make_model();path=OUT/'click-counter-Q3.kicad_pcb'
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
    (OUT/'netlist-Q3.json').write_text(json.dumps(model,indent=2)+'\n')
    print('Q3 placements applied; routes reset with footprint UUIDs preserved. Run preroute_q3 next.')


if __name__=='__main__':main()
