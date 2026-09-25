"""Synchronize Q4 schematic fields and explicitly unused pad nets, without routes."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import pcbnew as p
from build_q4_model import make_model

OUT = Path(__file__).resolve().parents[1] / 'electronics/q4'


def sync(board):
    model = {part['ref']: part for part in make_model()['parts']}
    xml = ET.parse(OUT / 'schematic-netlist-Q4.xml').getroot()
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    paths = json.loads((OUT / 'schematic-paths-Q4.json').read_text())['parts']
    for comp in xml.findall('components/comp'):
        ref = comp.attrib['ref']
        if ref not in model:
            continue  # Supply assertions have no PCB footprint.
        value = comp.findtext('value')
        assert value == model[ref]['value'], (ref, value)
        fp = footprints[ref]
        fp.SetValue(value)
        fp.SetPath(p.KIID_PATH(paths[ref]['path']))
        for field in comp.findall('fields/field'):
            field_name = field.attrib['name']
            if field_name == 'MPN':
                assert (field.text or '') == model[ref]['mpn']
            if field_name in ('MPN', 'Description', 'Datasheet'):
                fp.SetField(field_name, field.text or '')
                fp.GetField(field_name).SetVisible(False)
    for net in xml.findall('nets/net'):
        name = net.attrib['name']
        # Carry the schematic's electrical pin metadata, including deliberate
        # no-connect markers on multiple physical mounting pads with one number.
        for node in net.findall('node'):
            ref = node.attrib['ref']
            if ref not in footprints:
                continue
            for pad in footprints[ref].Pads():
                if pad.GetNumber() == node.attrib['pin']:
                    pad.SetPinFunction(node.attrib.get('pinfunction', ''))
                    pad.SetPinType(node.attrib.get('pintype', ''))
        if not name.startswith('unconnected-'):
            continue
        nodes = net.findall('node')
        assert len(nodes) == 1, name
        ref, pin = nodes[0].attrib['ref'], nodes[0].attrib['pin']
        assert pin not in model[ref]['pins'], (ref, pin)
        # Native board net names escape slash characters in pin functions. XML
        # carries literal slashes; match KiCad's schematic-to-board convention.
        name = name.replace('/', '{slash}')
        native = board.FindNet(name)
        if native is None:
            native = p.NETINFO_ITEM(board, name)
            board.Add(native)
        for pad in footprints[ref].Pads():
            if pad.GetNumber() == pin:
                pad.SetNet(native)


if __name__ == '__main__':
    path = OUT / 'click-counter-Q4.kicad_pcb'
    board = p.LoadBoard(str(path))
    sync(board)
    p.SaveBoard(str(path), board)
    print('Schematic fields and explicit no-connect nets synchronized in Q4 only.')
