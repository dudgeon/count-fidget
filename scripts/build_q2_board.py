"""Build a separate Q2 unrouted board from frozen Q1 footprints/outline.

Run with KiCad 10 pcbnew Python. Routing/import/export are separate steps. This
script deliberately never writes any Q1 PCB, project, BOM or RFQ artifact.
"""
import argparse
import json
from pathlib import Path
import pcbnew as p
from build_q2_model import make_model

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'electronics/q2'


def v(x, y):
    return p.VECTOR2I(p.FromMM(x), p.FromMM(y))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--replace-candidate', action='store_true', help='Explicitly replace Q2 working board; Q1 is always preserved')
    args = ap.parse_args()
    path = OUT / 'click-counter-Q2.kicad_pcb'
    if path.exists() and not args.replace_candidate:
        ap.error('Q2 board exists; use --replace-candidate only for an intentional rebuild')
    OUT.mkdir(exist_ok=True, parents=True)
    model = make_model()
    b = p.LoadBoard(str(ROOT / 'electronics/click-counter-Q1.kicad_pcb'))
    # Component positions and nets change; no stale routes are carried forward.
    keepers = []
    for item in list(b.GetTracks()) + list(b.Zones()):
        b.Remove(item)
        item.thisown = False  # Removed native objects live only until this process exits.
        keepers.append(item)
    fp = {f.GetReference(): f for f in b.GetFootprints()}
    for ref, template in [('C14','C7'), ('C15','C7'), ('C16','C7'), ('Q4','Q3')]:
        f = p.FOOTPRINT(fp[template])
        f.SetReference(ref)
        f.SetUuid(p.KIID())
        for item in list(f.Pads()) + list(f.GraphicalItems()) + list(f.GetFields()):
            item.SetUuid(p.KIID())
        b.Add(f)
        fp[ref] = f
        keepers.append(f)
    nets = {item.GetNetname(): item for item in b.GetNetsByNetcode().values()}
    names = {name for part in model['parts'] for name in part['pins'].values()}
    for name in sorted(names):
        if name not in nets:
            net = p.NETINFO_ITEM(b, name)
            b.Add(net)
            nets[name] = net
    for part in model['parts']:
        f = fp[part['ref']]
        f.SetValue(part['value'])
        lib, name = part['footprint'].split(':')
        f.SetFPID(p.LIB_ID(lib, name))
        f.SetPosition(v(part['x'], part['y']))
        f.SetOrientationDegrees(part['rotation'])
        for pad in f.Pads():
            name = part['pins'].get(pad.GetNumber())
            pad.SetNet(nets[name] if name else nets[''])
        if part['ref'].startswith(('TP','H')):
            f.SetAttributes(f.GetAttributes() | p.FP_EXCLUDE_FROM_BOM | p.FP_EXCLUDE_FROM_POS_FILES)
    paths = OUT / 'schematic-paths-Q2.json'
    if paths.exists():
        paths = json.loads(paths.read_text())
        for ref, record in paths['parts'].items():
            fp[ref].SetPath(p.KIID_PATH(record['path']))
    # Independent connector hold-downs are isolated physical NC pads.
    anchors = sorted([pad for pad in fp['J2'].Pads() if pad.GetNumber() == 'MP'], key=lambda pad: pad.GetPosition().y)
    assert len(anchors) == 2
    for number, pad in enumerate(anchors, 1):
        pad.SetNumber('MP' + str(number))
    for pad in fp['DS1'].Pads():
        number = int(pad.GetNumber())
        index = number - 1 if number <= 10 else 20 - number
        pad.SetPosition(v(21 - 11.43 + index * 2.54, 8.75 + (6.5 if number <= 10 else -6.5)))
    # TI DGK0008A example land pattern, 4214862/A (April 2023).
    # 0.20 mm copper gap, 0.10 mm nominal mask web with 0.05 mm NSMD margin.
    for pad in fp['U5'].Pads():
        number = int(pad.GetNumber())
        x = 17 + (-2.2 if number <= 4 else 2.2)
        y = 7 + ((2.5 - number) if number <= 4 else (number - 6.5)) * .65
        pad.SetPosition(v(x, y))
        pad.SetSize(v(1.4, .45))
        pad.SetShape(p.PAD_SHAPE_ROUNDRECT)
        pad.SetRoundRectCornerRadius(p.FromMM(.05))
        pad.SetLocalSolderMaskMargin(p.FromMM(.05))
    for text in b.GetDrawings():
        if isinstance(text, p.PCB_TEXT):
            text.SetText(text.GetText().replace('CLICK Q1', 'CLICK Q2').replace('QUOTE PROTOTYPE', 'ENGINEERING HOLD'))
    # Save project-specific footprints so update-from-library is reproducible.
    lib = OUT / 'ClickCounterQ2.pretty'
    lib.mkdir(exist_ok=True)
    saved = set()
    for part in model['parts']:
        if part['footprint'] in saved:
            continue
        saved.add(part['footprint'])
        f = p.FOOTPRINT(fp[part['ref']])
        f.SetPosition(v(0,0))
        if f.IsFlipped():
            f.Flip(v(0,0), False)
        f.SetOrientationDegrees(0)
        p.PCB_IO_MGR.FindPlugin(p.PCB_IO_MGR.KICAD_SEXP).FootprintSave(str(lib), f)
    libraries = sorted({part['footprint'].split(':')[0] for part in model['parts']} - {'ClickCounterQ2'})
    entries = ['(lib (name "ClickCounterQ2") (type "KiCad") (uri "${KIPRJMOD}/ClickCounterQ2.pretty") (options "") (descr "Reviewed Q2 display and TI DGK land patterns"))']
    entries += [f'(lib (name "{name}") (type "KiCad") (uri "${{KICAD10_FOOTPRINT_DIR}}/{name}.pretty") (options "") (descr "KiCad 10 library"))' for name in libraries]
    (OUT / 'fp-lib-table').write_text('(fp_lib_table (version 7)\n' + '\n'.join(entries) + ')\n')
    pro = json.loads((ROOT / 'electronics/click-counter-Q1.kicad_pro').read_text())
    pro['meta']['filename'] = 'click-counter-Q2.kicad_pro'
    pro['board']['design_settings']['drc_exclusions'] = []
    for nc in pro['net_settings']['classes']:
        nc['clearance'] = .127
    (OUT / 'click-counter-Q2.kicad_pro').write_text(json.dumps(pro, indent=2) + '\n')
    b.SetFileName(str(path))
    p.SaveBoard(str(path), b)
    if not p.ExportSpecctraDSN(b, str(OUT / 'click-counter-Q2.dsn')):
        raise RuntimeError('DSN export failed')
    (OUT / 'netlist-Q2.json').write_text(json.dumps(model, indent=2) + '\n')
    print('Q2 candidate: 50 fitted components; unrouted. Q1 preserved.')


if __name__ == '__main__':
    main()
