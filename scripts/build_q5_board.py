"""Build the separate two-layer Q5 placement candidate using exact local lands.

Run with KiCad's pcbnew Python. This intentionally clears Q5 routing when
--replace-candidate is given; never writes the submitted Q1 or Q2 files.
"""
import argparse
import json
from pathlib import Path
import pcbnew as p
from build_q5_model import make_model

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'electronics/q5'
LIB = OUT / 'CountFidgetQ5.pretty'


def v(x,y):
    return p.VECTOR2I(p.FromMM(x),p.FromMM(y))


def remove_sexpr(text, key):
    start=text.find('('+key+'\n')
    if start < 0:
        return text
    depth=0; quoted=False; escape=False
    for i in range(start,len(text)):
        c=text[i]
        if escape:
            escape=False; continue
        if quoted and c=='\\':
            escape=True; continue
        if c=='"': quoted=not quoted
        if not quoted:
            if c=='(':depth+=1
            if c==')':
                depth-=1
                if depth==0:return text[:start]+text[i+1:]
    raise ValueError('Unbalanced '+key)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--replace-candidate',action='store_true')
    args=ap.parse_args()
    path=OUT/'click-counter-Q5.kicad_pcb'
    if path.exists() and not args.replace_candidate:
        ap.error('Q5 exists: explicit --replace-candidate required to clear its routing')
    LIB.mkdir(parents=True,exist_ok=True)
    model=make_model()
    for part in model['parts']:
        name=part['footprint'].split(':')[1]
        if not (LIB/(name+'.kicad_mod')).exists():
            raise FileNotFoundError('Exact reviewed Q5 footprint required: '+name)
    board=p.LoadBoard(str(ROOT/'electronics/q4/click-counter-Q4.kicad_pcb'))
    discarded=[]
    for item in list(board.GetTracks())+list(board.Zones())+list(board.GetFootprints()):
        board.Remove(item);item.thisown=False;discarded.append(item)
    board.SetCopperLayerCount(2)
    board.GetDesignSettings().SetBoardThickness(p.FromMM(model['board_mm'][2]))
    for item in list(board.GetDrawings()):
        board.Remove(item); item.thisown=False; discarded.append(item)
    w,h,_=model['board_mm']
    for a,b in [((0,0),(w,0)),((w,0),(w,h)),((w,h),(0,h)),((0,h),(0,0))]:
        edge=p.PCB_SHAPE(board);edge.SetShape(p.SHAPE_T_SEGMENT);edge.SetLayer(p.Edge_Cuts)
        edge.SetStart(v(*a));edge.SetEnd(v(*b));edge.SetWidth(p.FromMM(.05));board.Add(edge)
    names={name for part in model['parts'] for name in part['pins'].values()}
    nets={item.GetNetname():item for item in board.GetNetsByNetcode().values()}
    for name in sorted(names):
        if name not in nets:
            net=p.NETINFO_ITEM(board,name);board.Add(net);nets[name]=net
    records=json.loads((OUT/'schematic-paths-Q5.json').read_text())['parts']
    for part in model['parts']:
        lib,name=part['footprint'].split(':')
        fp=p.FootprintLoad(str(LIB),name)
        assert fp is not None, part['ref']
        fp.SetReference(part['ref']);fp.SetValue(part['value']);fp.SetFPID(p.LIB_ID(lib,name))
        fp.SetUuid(p.KIID())
        for item in list(fp.Pads())+list(fp.GraphicalItems())+list(fp.GetFields()):
            item.SetUuid(p.KIID())
        board.Add(fp)
        fp.SetPosition(v(0,0));fp.SetOrientationDegrees(0)
        if fp.IsFlipped():fp.Flip(v(0,0),False)
        if part['side']=='bottom':fp.Flip(v(0,0),False)
        fp.SetOrientationDegrees(part['rotation']);fp.SetPosition(v(part['x'],part['y']))
        fp.SetPath(p.KIID_PATH(records[part['ref']]['path']))
        fp.SetField('MPN',part['mpn']);fp.SetField('Description',part['notes'])
        for name in ('Reference','Value','MPN','Description'):
            field=fp.GetField(name)
            if field:field.SetVisible(False)
        for pad in fp.Pads():
            name=part['pins'].get(pad.GetNumber())
            pad.SetNet(nets[name] if name else nets[''])
            if pad.GetNumber() in part['pins']:
                meta=records[part['ref']]['pins'][pad.GetNumber()]
                pad.SetPinFunction(meta['name']);pad.SetPinType(meta['type'])
        if part['ref'].startswith(('TP','H')):
            fp.SetAttributes(fp.GetAttributes()|p.FP_EXCLUDE_FROM_BOM|p.FP_EXCLUDE_FROM_POS_FILES)
    for item in board.GetDrawings():
        if isinstance(item,p.PCB_TEXT):
            item.SetText(item.GetText().replace('Q4','Q5'))
    pro=json.loads((ROOT/'electronics/q4/click-counter-Q4.kicad_pro').read_text())
    pro['meta']['filename']='click-counter-Q5.kicad_pro'
    pro['board']['design_settings']['drc_exclusions']=[]
    (OUT/'click-counter-Q5.kicad_pro').write_text(json.dumps(pro,indent=2)+'\n')
    (OUT/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "CountFidgetQ5") (type "KiCad") (uri "${KIPRJMOD}/CountFidgetQ5.pretty") (options "") (descr "Q5 exact reviewed lands; assembler acceptance pending")))\n')
    board.SetFileName(str(path));p.SaveBoard(str(path),board)
    source=remove_sexpr(path.read_text(),'stackup')
    path.write_text(source)
    board=p.LoadBoard(str(path))
    assert board.GetCopperLayerCount()==2
    assert p.ExportSpecctraDSN(board,str(OUT/'click-counter-Q5.dsn'))
    (OUT/'netlist-Q5.json').write_text(json.dumps(model,indent=2)+'\n')
    print('Q5 two-layer placement candidate:',model['fitted_components'],'fitted parts; no routing/physical qualification claimed.')


if __name__=='__main__':main()
