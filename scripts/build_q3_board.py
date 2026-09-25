"""Build the separate two-layer Q3 placement candidate using exact local lands.

Run with KiCad's pcbnew Python. This intentionally clears Q3 routing when
--replace-candidate is given; never writes the submitted Q1 or Q2 files.
"""
import argparse
import json
from pathlib import Path
import shutil
import pcbnew as p
from build_q3_model import make_model

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'electronics/q3'
LIB = OUT / 'CountFidgetQ3.pretty'


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
    path=OUT/'click-counter-Q3.kicad_pcb'
    if path.exists() and not args.replace_candidate:
        ap.error('Q3 exists: explicit --replace-candidate required to clear its routing')
    LIB.mkdir(parents=True,exist_ok=True)
    model=make_model()
    for part in model['parts']:
        name=part['footprint'].split(':')[1]
        target=LIB/(name+'.kicad_mod')
        if target.exists():continue
        source=ROOT/'electronics/q2/ClickCounterQ2.pretty'/(name+'.kicad_mod')
        if source.exists():shutil.copyfile(source,target)
        else:raise FileNotFoundError('Exact reviewed footprint required: '+str(target))
    board=p.LoadBoard(str(ROOT/'electronics/q2/click-counter-Q2.kicad_pcb'))
    discarded=[]
    for item in list(board.GetTracks())+list(board.Zones())+list(board.GetFootprints()):
        board.Remove(item);item.thisown=False;discarded.append(item)
    board.SetCopperLayerCount(2)
    board.GetDesignSettings().SetBoardThickness(p.FromMM(1.0))
    names={name for part in model['parts'] for name in part['pins'].values()}
    nets={item.GetNetname():item for item in board.GetNetsByNetcode().values()}
    for name in sorted(names):
        if name not in nets:
            net=p.NETINFO_ITEM(board,name);board.Add(net);nets[name]=net
    records=json.loads((OUT/'schematic-paths-Q3.json').read_text())['parts']
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
            item.SetText(item.GetText().replace('Q2','Q3'))
    pro=json.loads((ROOT/'electronics/q2/click-counter-Q2.kicad_pro').read_text())
    pro['meta']['filename']='click-counter-Q3.kicad_pro'
    pro['board']['design_settings']['drc_exclusions']=[]
    (OUT/'click-counter-Q3.kicad_pro').write_text(json.dumps(pro,indent=2)+'\n')
    (OUT/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "CountFidgetQ3") (type "KiCad") (uri "${KIPRJMOD}/CountFidgetQ3.pretty") (options "") (descr "Q3 exact reviewed lands; assembler acceptance pending")))\n')
    board.SetFileName(str(path));p.SaveBoard(str(path),board)
    source=remove_sexpr(path.read_text(),'stackup')
    path.write_text(source)
    board=p.LoadBoard(str(path))
    assert board.GetCopperLayerCount()==2
    assert p.ExportSpecctraDSN(board,str(OUT/'click-counter-Q3.dsn'))
    (OUT/'netlist-Q3.json').write_text(json.dumps(model,indent=2)+'\n')
    print('Q3 two-layer placement candidate:',model['fitted_components'],'fitted parts; no routing/physical qualification claimed.')


if __name__=='__main__':main()
