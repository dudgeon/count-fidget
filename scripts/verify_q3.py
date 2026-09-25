"""Independently verify the unreleased Q3 model, native schematic and native PCB.

Uses only the Python standard library. Default mode checks saved native reports
and their input hashes; --kicad-cli regenerates those reports without editing the
board. Alternatively --prepare-native freezes inputs, prints exact CLI commands,
then --bind-native accepts only newer outputs for unchanged inputs. The single
documented J1 shell/SW2 courtyard projection exception is disclosed explicitly.
--semantic-only checks data agreement but cannot certify fresh DRC/ERC.
This is design-file verification, never manufacturing release or hardware proof.
"""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from datetime import datetime, timezone
import re
import shlex
import time
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

from build_q3_model import make_model
from kicad_sexpr import child, children, parse, property_value

ROOT = Path(__file__).resolve().parents[1]
Q3 = ROOT / 'electronics/q3'
VERIFY = ROOT / 'verification'
BOARD = Q3 / 'click-counter-Q3.kicad_pcb'
SCHEMATIC = Q3 / 'click-counter-Q3.kicad_sch'
PUBLIC_XML = Q3 / 'schematic-netlist-Q3.xml'
REPORT = VERIFY / 'q3-validation.json'
DRC = VERIFY / 'q3-native-drc.json'
ERC = VERIFY / 'q3-native-erc.json'
NATIVE_XML = VERIFY / 'q3-native-netlist.xml'
SCHEMATIC_EVIDENCE = Q3 / 'schematic-validation-Q3.json'
PREPARE = VERIFY / 'q3-native-preparation.json'
SCHEMA_VERSION = 1
ERC_IGNORED = {'single_global_label', 'four_way_junction', 'simulation_model_issue', 'footprint_filter'}
DRC_IGNORED = {'missing_courtyard', 'track_not_centered_on_via', 'tuning_profile_track_geometries',
               'footprint_filters_mismatch', 'footprint_type_mismatch'}
J1_SHELL_PAD_UUID = '0f8e645e-7bc1-4813-a865-8937f378b8ad'
SW2_FOOTPRINT_UUID = 'bd72eaff-b653-4b41-8a04-10369b9143df'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def input_hashes():
    paths = {BOARD, Q3 / 'click-counter-Q3.kicad_pro', Q3 / 'netlist-Q3.json',
             PUBLIC_XML, Q3 / 'schematic-paths-Q3.json', Q3 / 'sym-lib-table', Q3 / 'fp-lib-table',
             ROOT / 'electronics/q2/netlist-Q2.json', ROOT / 'procurement/q3/power-candidates.json', ROOT / 'procurement/q3/live-stock-2026-09-15.json', Path(__file__).resolve(), ROOT / 'scripts/kicad_sexpr.py',
             ROOT / 'scripts/build_q3_model.py', ROOT / 'scripts/build_q3_schematic.py',
             ROOT / 'scripts/build_q3_board.py', ROOT / 'scripts/sync_q3_board.py', ROOT / 'scripts/finish_q3_board.py', ROOT / 'scripts/preroute_q3.py', ROOT / 'scripts/prepare_q3_route.py', ROOT / 'scripts/test_verify_q3.py'}
    paths.update(Q3.glob('*.kicad_sch'))
    paths.update(Q3.glob('*.kicad_sym'))
    paths.update(Q3.glob('*.kicad_dru'))
    paths.update(Q3.glob('*.pretty/*.kicad_mod'))
    paths.update({Q3/'routing-checkpoint-Q3.json',Q3/'routing-checkpoint-native-drc.json'})
    paths.add(SCHEMATIC_EVIDENCE)
    paths.update(schematic_artifacts())
    return {relative(path): digest(path) for path in sorted(paths)}


def schematic_artifacts():
    return {*(Q3.glob('*.kicad_sch')), Q3 / 'CountFidgetQ3.kicad_sym', Q3 / 'sym-lib-table',
            Q3 / 'schematic-paths-Q3.json', PUBLIC_XML, Q3 / 'erc-Q3.json', Q3 / 'schematic-Q3.pdf',
            *(Q3 / 'schematic-svg').glob('*.svg')}


def verify_schematic_evidence():
    report = json.loads(SCHEMATIC_EVIDENCE.read_text())
    require(len(list(Q3.glob('*.kicad_sch'))) == 8 and len(list((Q3 / 'schematic-svg').glob('*.svg'))) == 8, 'Expected eight native schematic sheets and eight SVG exports')
    inputs = {ROOT / 'scripts/build_q3_schematic.py', ROOT / 'scripts/build_q3_model.py', ROOT / 'electronics/q2/netlist-Q2.json', ROOT / 'procurement/q3/power-candidates.json', ROOT / 'procurement/q3/live-stock-2026-09-15.json'}
    require(report['inputs_sha256'] == {relative(path):digest(path) for path in inputs}, 'Schematic export evidence has stale generator/model inputs; regenerate the schematic')
    require(report['artifacts_sha256'] == {relative(path):digest(path) for path in schematic_artifacts()}, 'Schematic PDF/SVG/ERC/native export evidence is stale or incomplete')
    require(report['sheets'] == 8 and report['components_and_pcb_features'] == 82 and report['fitted_components'] == 70
            and report['connected_pins_matched'] == 218 and report['explicit_unused_pins'] == 50 and report['erc_violations'] == 0,
            'Schematic evidence counts differ')
    report_checks(Q3 / 'erc-Q3.json', 'erc')


def xml_data(path):
    root = ET.parse(path).getroot()
    components = {}
    for comp in root.findall('components/comp'):
        ref = comp.attrib['ref']
        require(ref not in components, 'Duplicate schematic reference ' + ref)
        mpn_fields = [field.text or '' for field in comp.findall('fields/field') if field.attrib['name'] == 'MPN']
        require(len(mpn_fields) == 1 and len(comp.findall('value')) == 1 and len(comp.findall('footprint')) == 1,
                'Missing or duplicated schematic identity field: ' + ref)
        components[ref] = {
            'value': comp.findtext('value'), 'footprint': comp.findtext('footprint'),
            'mpn': mpn_fields[0],
            'pins': sorted(pin.attrib['num'] for pin in comp.findall('units/unit/pins/pin')),
            'symbol_uuid': comp.findtext('tstamps'),
            'sheet_path': comp.find('sheetpath').attrib['tstamps'],
        }
    nets, nodes, types = {}, defaultdict(list), {}
    for net in root.findall('nets/net'):
        name = net.attrib['name']
        require(name not in nodes, 'Duplicate schematic net ' + name)
        for node in net.findall('node'):
            key = node.attrib['ref'], node.attrib['pin']
            require(key not in nets, 'Physical schematic pin assigned twice: ' + str(key))
            nets[key] = name
            nodes[name].append(key)
            types[key] = node.attrib.get('pintype')
    return components, nets, dict(nodes), types


def near(a, b, label, tolerance=1e-5):
    require(abs(float(a) - float(b)) <= tolerance, f'{label}: {a} != {b}')


def net_name(node, numeric_nets):
    values = children(node, 'net')
    if not values:
        return ''
    require(len(values) == 1, 'Multiple nets on PCB item')
    value = values[0]
    name = value[2] if len(value) > 2 else numeric_nets.get(value[1], value[1])
    # Native PCB net identifiers escape '/' inside generated pin names; XML does not.
    return name.replace('{slash}', '/')


def world_pad(footprint, pad):
    position = child(footprint, 'at')
    x, y = map(float, position[1:3])
    angle = math.radians(float(position[3]) if len(position) > 3 else 0)
    local = child(pad, 'at')
    px, py = map(float, local[1:3])
    # KiCad stores local coordinates already mirrored for a flipped footprint.
    return x + px * math.cos(angle) + py * math.sin(angle), y - px * math.sin(angle) + py * math.cos(angle)


def verify_stock(parts, stock):
    """Recorded availability, never a promise of present stock or allocation."""
    observed = datetime.fromisoformat(stock['recorded_utc'])
    require(observed.tzinfo is not None, 'Stock evidence needs a timezone')
    by_mpn, by_code = {}, {}
    for record in stock['records']:
        require(record['mpn'] not in by_mpn and record['lcsc'] not in by_code,
                'Duplicate or ambiguous stock identity')
        require(re.fullmatch(r'C[0-9]+', record['lcsc']) is not None, 'Invalid stock code')
        require(type(record['stock']) is int and record['stock'] > 0, 'Recorded stock must be a positive integer')
        require((record['source'],record['kind']) in {
                    ('https://jlcpcb.com/parts/bom-tool','Native Chrome live BOM availability result'),
                    ('https://jlcpcb.com/partdetail/'+record['lcsc'],'Native Chrome live exact part page')},
                'Unexpected stock evidence provenance')
        by_mpn[record['mpn']], by_code[record['lcsc']] = record, record
    fitted = [p for p in parts.values() if not p['ref'].startswith(('TP','H'))]
    for part in fitted:
        require(part['mpn'] in by_mpn and by_mpn[part['mpn']]['lcsc'] == part.get('lcsc'),
                'Exact MPN/stock code evidence missing: ' + part['ref'])
    return {'fitted_references_with_exact_recorded_identity':len(fitted), 'recorded_utc':stock['recorded_utc'],
            'current_availability_or_allocation_established':False}


def verify_physical_pins(ref, pins):
    counts={'U1':48,'U2':11,'U3':5,'U4':6,'U5':8,'U6':11,'DS1':14,'D1':6,'L1':2}
    if ref in counts:expected=set(map(str,range(1,counts[ref]+1)))
    elif ref=='J1':expected={side+str(n) for side in ('A','B') for n in (1,4,5,6,7,8,9,12)}|{'SH'}
    elif ref=='J2':expected={'1','2','3','4','MP1','MP2'}
    elif ref.startswith(('R','C','SW')):expected={'1','2'}
    elif ref.startswith('Q'):expected={'1','2','3'}
    elif ref.startswith('TP'):expected={'1'}
    elif ref.startswith('H'):expected=set()
    else:raise ValueError('No independent physical-pin contract for '+ref)
    require(len(pins)==len(expected) and set(pins)==expected, 'Exact physical pin identifiers differ: '+ref)


def verify_model_contract(model):
    parts = {part['ref']:part for part in model['parts']}
    baseline = {p['ref']:p for p in json.loads((ROOT/'electronics/q2/netlist-Q2.json').read_text())['parts']}
    removed = {'C8','C14','C15','C16'}
    added = {'U6','L1','Q5','Q6', *(f'R{i}' for i in range(20,29)), *(f'C{i}' for i in range(17,28))}
    require(set(parts) == (set(baseline)-removed)|added and len(parts) == len(model['parts']) == 82,
            'Reviewed Q3 reference set differs; critical part omitted or obsolete LCD part retained')
    require(model['layers'] == 2 and model['board_mm'] == [42,40,1], 'Q3 requires the reviewed two-layer board stack')
    pins = {
        'U1':{'14':'GND','15':'V3','16':'SBWTDIO','17':'SBWTCK','26':'COUNT_N','25':'RESET_N',
              '24':'OLED_ENABLE','23':'OLED_RESET_N','28':'OLED_SDA','27':'OLED_SCL'},
        'DS1':dict(zip(map(str,[1,2,3,4,5,7,8,9,10,11,12,13,14]),
                    ['OLED_C2P','OLED_C2N','OLED_C1P','OLED_C1N','OLED_VBAT','GND','V3','OLED_RESET_N',
                     'OLED_SCL','OLED_SDA','OLED_IREF','OLED_VCOMH','OLED_VCC'])),
        'U6':dict(zip(map(str,range(1,12)),['OLED_ENABLE','SYS','OLED_CFG1','OLED_CFG2','OLED_CFG3',
                                         'OLED_4V','OLED_LX2','GND','OLED_LX1','SYS','GND'])),
        'L1':{'1':'OLED_LX1','2':'OLED_LX2'},
        'Q5':{'1':'OLED_SWITCH_GATE','2':'OLED_4V','3':'OLED_VBAT'},
        'Q6':{'1':'OLED_ENABLE','2':'GND','3':'OLED_SWITCH_GATE'},
    }
    two_terminal = {
        'R20':('OLED_CFG1','GND'),'R21':('OLED_CFG2','GND'),'R22':('OLED_CFG3','GND'),
        'R23':('OLED_4V','OLED_SWITCH_GATE'),'R24':('OLED_ENABLE','GND'),'R25':('OLED_RESET_N','GND'),
        'R26':('V3','OLED_SCL'),'R27':('V3','OLED_SDA'),'R28':('OLED_IREF','GND'),
        'C17':('SYS','GND'),'C18':('OLED_4V','GND'),'C19':('OLED_4V','GND'),
        'C20':('V3','GND'),'C21':('V3','GND'),'C22':('OLED_VCOMH','GND'),
        'C23':('OLED_VCC','GND'),'C24':('OLED_VCC','GND'),
        'C25':('OLED_C2P','OLED_C2N'),'C26':('OLED_C1P','OLED_C1N'),'C27':('OLED_VBAT','GND')}
    pins.update({ref:dict(zip(('1','2'),nets)) for ref,nets in two_terminal.items()})
    for ref,part in parts.items():
        expected = pins[ref] if ref in pins else baseline[ref]['pins']
        require(part['pins'] == expected, 'Reviewed pin topology differs: '+ref)
        require(not any(net.startswith(('LCD','COM','SEG')) for net in part['pins'].values()), 'Obsolete LCD connection: '+ref)
        require('DE188' not in part['mpn'].replace(' ','').upper(), 'Obsolete LCD identity retained')
        require(part['side'] == ('top' if ref in {'DS1','SW1','SW2','H1','H2'} else 'bottom'), 'Reviewed assembly side differs: '+ref)
    identities = {
        'U1':('MSP430FR4133IG48R','C2053877'),'DS1':('X087-2832TSWIG02-H14','C18723015'),
        'U2':('BQ25185DLHR','C19725033'),'U3':('TPS7A0230PDBVR','C3747031'),
        'U4':('BQ29700DSER','C183096'),'U5':('TLV7012DGKR','C2859969'),
        'U6':('TPS63900DSKR','C1518762'),'L1':('DFE201612E-2R2M=P2','C337893'),
        'Q5':('DMP2035U-7','C110499'),'Q6':('DMN2056U-7','C332302'),
        'R20':('RC0603FR-075K11L','C112314'),'R21':('RC0603FR-0720K5L','C273789'),
        'R22':('RC0603FR-0724K9L','C137761'),'R23':('0603WAF4702T5E','C25819'),
        'R24':('RC0603FR-07100KL','C14675'),'R25':('RC0603FR-07100KL','C14675'),
        'R26':('RC0603FR-074K7L','C99782'),'R27':('RC0603FR-074K7L','C99782'),
        'R28':('RC0603FR-07750KL','C137684'),
    }
    for ref in ('C1','C3','C5','C22'): identities[ref] = ('GRM21BR71E225KE11L','C77081')
    for ref in ('C17','C18','C19'): identities[ref] = ('CL21A226MAYNNNE','C602037')
    for ref in ('C20','C24','C27'): identities[ref] = ('GRM188R71H104KA93D','C77055')
    for ref in ('C6','C21'): identities[ref] = ('GRM21BR61E106KA73L','C84416')
    identities.update(C23=('GRM21BZ71H475KE15L','C437557'),C25=('CL10B105KA8NNNC','C29936'),
                      C26=('CL10B105KA8NNNC','C29936'),C13=('GRM1885C1H472JA01D','C85980'))
    for ref in ('SW1','SW2'): identities[ref] = ('CPG151101D13','C49234235')
    for ref in ('R17','R18'): identities[ref] = ('0603WAF2203T5E','C22961')
    for ref,(mpn,code) in identities.items():
        require((parts[ref]['mpn'],parts[ref]['lcsc']) == (mpn,code), 'Reviewed exact component differs: '+ref)
    values = {'L1':'2.2u','R20':'5.11k','R21':'20.5k','R22':'24.9k','R23':'47k','R24':'100k','R25':'100k',
              'R26':'4.7k','R27':'4.7k','R28':'750k','C17':'22u','C18':'22u','C19':'22u','C20':'100n',
              'C21':'10u','C22':'2.2u','C23':'4.7u','C24':'100n','C25':'1u','C26':'1u','C27':'100n',
              'R17':'220k','R18':'220k','C13':'4.7n','R19':'2k'}
    for ref,value in values.items(): require(parts[ref]['value'] == value, 'Reviewed component value differs: '+ref)
    power = json.loads((ROOT/'procurement/q3/power-candidates.json').read_text())
    require(power['rails']['logic'] == {'net':'V3','nominal_V':3.0,'always_on':True}, 'OLED logic rail contract changed')
    pump = power['rails']['pump_input']
    require(pump['net'] == 'OLED_VBAT' and pump['nominal_V'] == 4.0 and pump['required_V'] == [3.8,4.2]
            and pump['static_converter_tolerance_V'] == [3.94,4.06] and pump['requires_measured_transient_validation'] is True,
            'OLED pump rail qualification contract changed')
    require(power['rails']['panel'] == {'net':'OLED_VCC','nominal_V':9.0,'internal_charge_pump_command':['8D','72'],
                                      'no_external_9V_source':True}, 'OLED internal 9V pump contract changed')
    return {'independent_pin_maps_checked':len(parts), 'removed_lcd_references':sorted(removed),
            'oled_vdd_always_on_3V':True, 'oled_vbat_regulated_4V_isolated_by_pmos':True,
            'stock_evidence':verify_stock(parts,json.loads((ROOT/'procurement/q3/live-stock-2026-09-15.json').read_text()))}


def verify_oled_lands(footprint, embedded):
    require(child(footprint,'layer')[1] == 'F.Cu', 'OLED must remain on the top side')
    pads = children(footprint,'pad')
    require(len(pads) == 14 and {p[1] for p in pads} == set(map(str,range(1,15))), 'OLED requires exactly 14 distinct lands')
    near(child(footprint,'solder_mask_margin')[1],.05,'OLED mask margin')
    for pad in pads:
        require(pad[2:4] == ['smd','rect'], 'OLED land must be rectangular SMT, not drilled')
        require(child(pad,'layers')[1:] == ['F.Cu','F.Mask'], 'OLED no-paste localized solder process changed')
        require(not children(pad,'drill'), 'OLED terminal must not be drilled')
        near(child(pad,'size')[1],2.8,'OLED land length'); near(child(pad,'size')[2],.4,'OLED land width')
        at = child(pad,'at')
        near(at[1],24,'OLED land local X'); near(at[2],4.03-(int(pad[1])-1)*.62,'OLED land number/pitch')
        near((float(at[3]) if len(at)>3 else 0)%180,0,'OLED land orientation')
    def reject_paste(node):
        if isinstance(node,list):
            require(not (node and node[0] in ('layer','layers') and 'F.Paste' in node[1:]), 'OLED contains paste artwork')
            for item in node: reject_paste(item)
    reject_paste(footprint)
    return {'pad_count':14,'pad_size_mm':[2.8,.4],'pitch_mm':.62,'local_x_mm':24,'paste_apertures':0,
            'vendor_fpc_process_and_physical_fit_qualified':False}


def verify_inductor(footprint, embedded):
    side = child(footprint,'layer')[1]
    require(side in ('F.Cu','B.Cu'), 'Inductor side invalid')
    bottom = side == 'B.Cu'
    pads = children(footprint,'pad')
    require(len(pads) == 2 and {p[1] for p in pads} == {'1','2'}, 'Murata inductor pad set differs')
    for pad in pads:
        require(pad[2:4] == ['smd','rect'], 'Murata inductor land type differs')
        near(child(pad,'at')[1], -.8 if pad[1]=='1' else .8, 'Murata land X')
        near(child(pad,'at')[2], 0, 'Murata land Y')
        near(child(pad,'size')[1],.8,'Murata land width'); near(child(pad,'size')[2],1.8,'Murata land height')
        require(set(child(pad,'layers')[1:]) == {side,side.replace('.Cu','.Mask'),side.replace('.Cu','.Paste')}, 'Murata land layer set differs')
    zones = children(footprint,'zone')
    require(len(zones) == 2, 'Murata requires both embedded keepouts')
    expected = {
        'not_allowed':(.4, {'tracks':'not_allowed','vias':'not_allowed','pads':'not_allowed','copperpour':'not_allowed','footprints':'allowed'}),
        'allowed':(1.1, {'tracks':'allowed','vias':'not_allowed','pads':'allowed','copperpour':'allowed','footprints':'allowed'})}
    seen = set()
    for zone in zones:
        flags = {item[0]:item[1] for item in child(zone,'keepout')[1:]}
        key = flags.get('tracks')
        require(key in expected and key not in seen and flags == expected[key][1], 'Murata keepout permissions altered or duplicated')
        seen.add(key)
        require(child(zone,'layer')[1] == side, 'Murata keepout lost on footprint flip')
        require(not children(zone,'net') or child(zone,'net')[1] == '0', 'Murata keepout must not carry a net')
        require(not children(zone,'net_name') or child(zone,'net_name')[1] == '', 'Murata keepout has a named net')
        width = expected[key][0]
        target = [(-width,-.9),(width,-.9),(width,.9),(-width,.9)]
        if embedded:
            at = child(footprint,'at'); x,y = map(float,at[1:3])
            angle = math.radians(float(at[3]) if len(at)>3 else 0)
            if bottom: target = [(px,-py) for px,py in target]
            target = [(x+px*math.cos(angle)+py*math.sin(angle), y-px*math.sin(angle)+py*math.cos(angle)) for px,py in target]
        polys = children(zone,'polygon')
        require(len(polys) == 1, 'Murata keepout polygon missing or duplicated')
        actual = [tuple(map(float,p[1:3])) for p in children(child(polys[0],'pts'),'xy')]
        require(len(actual) == 4, 'Murata keepout must retain its four vertices')
        require(all(any(math.hypot(a[0]-b[0],a[1]-b[1]) < 1e-5 for b in actual) for a in target), 'Murata keepout geometry/transform differs')
    return {'embedded_rule_areas':2,'inner_no_copper_rectangle_mm':[.8,1.8], 'body_no_vias_rectangle_mm':[2.2,1.8], 'layer':side}


def verify_converter_lands(footprint):
    side = child(footprint,'layer')[1]
    require(side in ('F.Cu','B.Cu'), 'Converter side invalid')
    flip = -1 if side == 'B.Cu' else 1
    pads = children(footprint,'pad')
    named = {p[1]:p for p in pads if p[1]}
    require(len(pads) == 13 and len(named) == 11 and set(named) == set(map(str,range(1,12))), 'TI DSK0010A requires 10 leads, EP and two paste apertures')
    near(child(footprint,'solder_mask_margin')[1],.05,'Converter NSMD margin')
    for number,pad in named.items():
        require(pad[2:4] == ['smd','roundrect'], 'Converter lead type differs')
        n = int(number)
        x,y = (0,0) if n==11 else (-1.15,-1+(n-1)*.5) if n<=5 else (1.15,1-(n-6)*.5)
        near(child(pad,'at')[1],x,'Converter numbered land X'); near(child(pad,'at')[2],flip*y,'Converter numbered land Y')
        w,h = (1.2,2) if n==11 else (.6,.25)
        near(child(pad,'size')[1],w,'Converter land width'); near(child(pad,'size')[2],h,'Converter land height')
        layers = {side,side.replace('.Cu','.Mask')}
        if n!=11: layers.add(side.replace('.Cu','.Paste'))
        require(set(child(pad,'layers')[1:]) == layers, 'Converter pad/paste layer set differs')
    paste = [p for p in pads if not p[1]]
    require(len(paste)==2, 'Converter EP requires two separate paste apertures')
    for pad in paste:
        require(child(pad,'layers')[1:] == [side.replace('.Cu','.Paste')], 'Converter unnamed pad must be paste only')
        near(child(pad,'at')[1],0,'Converter paste X'); near(abs(float(child(pad,'at')[2])),.555,'Converter paste Y')
        near(child(pad,'size')[1],1.13,'Converter paste width'); near(child(pad,'size')[2],.89,'Converter paste height')
    require(float(child(paste[0],'at')[2])*float(child(paste[1],'at')[2])<0,'Converter paste apertures overlap')


def verify_switch_lands(footprint):
    require(child(footprint,'layer')[1] == 'F.Cu','Switch must remain on top')
    pads = children(footprint,'pad')
    require(len(pads)==3 and {p[1] for p in pads}=={'','1','2'},'Plate switch requires two terminals and one central hole')
    for pad in pads:
        n = pad[1]
        x,y,diameter,drill = {'':(-2.54,5.08,3.95,3.95),'1':(0,0,2.2,1.5),'2':(-6.35,2.54,2.2,1.5)}[n]
        require(pad[2:4] == ['thru_hole' if n else 'np_thru_hole','circle'], 'Switch land/hole type differs')
        near(child(pad,'at')[1],x,'Switch terminal/hole X'); near(child(pad,'at')[2],y,'Switch terminal/hole Y')
        near(child(pad,'size')[1],diameter,'Switch land diameter'); near(child(pad,'size')[2],diameter,'Switch land diameter')
        near(child(pad,'drill')[1],drill,'Switch finished hole')
        require(set(child(pad,'layers')[1:]) == {'*.Cu','*.Mask'}, 'Switch pad layers differ')


def verify_two_layer_copper(board, numeric_nets):
    for net in numeric_nets.values():
        require(not net.startswith(('LCD','COM','SEG')), 'Obsolete LCD net retained on PCB')
    for kind in ('segment','arc','via','zone'):
        for item in children(board,kind):
            require(not net_name(item,numeric_nets).startswith(('LCD','COM','SEG')), 'Obsolete LCD net carries copper')
    for node in child(board,'layers')[1:]:
        if isinstance(node,list) and node[1].endswith('.Cu'):
            require(node[1] in ('F.Cu','B.Cu'), 'Unexpected inner copper layer')
    def visit(node):
        if not isinstance(node,list): return
        if node and node[0] in ('layer','layers'):
            require(not any(isinstance(x,str) and x.endswith('.Cu') and x not in ('F.Cu','B.Cu','*.Cu') for x in node[1:]),
                    'Copper item still references an inner layer')
        for item in node: visit(item)
    visit(board)
    for via in children(board,'via'):
        require(child(via,'layers')[1:] == ['F.Cu','B.Cu'], 'Q3 via must span the two outer layers')
        require(not any(x in via for x in ('blind','micro')), 'Q3 must not contain blind or microvias')
    zones = children(board,'zone')
    require(len(zones) >= 2 and all(not children(zone,'keepout') and net_name(zone,numeric_nets) == 'GND' for zone in zones),
            'Board copper zones must be explicit ground fills; no broad suppressing rule areas')
    require({child(z,'layer')[1] for z in zones} == {'F.Cu','B.Cu'}, 'Both copper layers require ground zones')


def verify_semantics(xml_path=PUBLIC_XML):
    model = make_model()
    verify_schematic_evidence()
    require(model['board_mm'] == [42,40,1], 'Model board dimensions differ from the verified candidate')
    require(json.loads((Q3 / 'netlist-Q3.json').read_text()) == model, 'Saved Q3 model is stale; rebuild from make_model()')
    require(model['hardware_tested'] is False and model['manufacturing_released'] is False, 'Candidate release gates changed')
    parts = {part['ref']: part for part in model['parts']}
    require(len(parts) == len(model['parts']) == 82, 'Expected 82 unique model references')
    fitted = sum(not ref.startswith(('TP', 'H')) for ref in parts)
    require(fitted == model['fitted_components'] == 70, 'Expected 70 fitted components')
    require(sum(ref.startswith('TP') for ref in parts) == 10 and sum(ref.startswith('H') for ref in parts) == 2,
            'Expected ten fixture lands and two mounting holes')
    comps, nets, nodes, types = xml_data(xml_path)
    require(set(comps) == set(parts), 'Schematic/model reference sets differ')
    mapping = json.loads((Q3 / 'schematic-paths-Q3.json').read_text())
    require(set(mapping['parts']) == set(parts), 'Schematic path map reference sets differ')
    connected, nc = {}, {}
    for ref, part in parts.items():
        comp, entry = comps[ref], mapping['parts'][ref]
        verify_physical_pins(ref,comp['pins'])
        for key in ('value', 'mpn', 'footprint'):
            require(comp[key] == part[key], f'Schematic/model {ref} {key} differs')
        require(set(comp['pins']) == set(entry['pins']) and len(comp['pins']) == len(set(comp['pins'])), f'{ref} physical pin set differs')
        require(comp['symbol_uuid'] == entry['symbol_uuid'], f'{ref} symbol UUID differs')
        expected_path = '/' + mapping['root_uuid'] + comp['sheet_path'] + comp['symbol_uuid']
        require(expected_path == entry['path'], f'{ref} full schematic path differs')
        for pin in comp['pins']:
            key = ref, pin
            require(key in nets, 'Missing exported physical pin ' + str(key))
            if pin in part['pins']:
                require(nets[key] == part['pins'][pin], f'Schematic/model net differs: {key}')
                connected[key] = nets[key]
            else:
                require(nets[key].startswith('unconnected-') and nodes[nets[key]] == [key], f'NC pin is not unique and isolated: {key}')
                nc[key] = nets[key]
            require(entry['pins'][pin]['net'] == part['pins'].get(pin), f'Pin map/model differs: {key}')
        require(set(part['pins']) <= set(comp['pins']), f'Model has nonphysical pins: {ref}')
    require(len(connected) == 218 and len(nc) == 50 and len(nets) == 268, 'Connected/NC physical pin counts differ from 218/50')
    require(len(set(nc.values())) == 50, 'NC net names are not unique')
    for key in [('U5', '1'), ('U5', '7')]:
        require(types[key] == 'output', 'Comparator must retain a push-pull output pin type: ' + str(key))
    for key in [('U2', '1'), ('U3', '5'), ('U6', '6'), ('DS1', '13'), ('DS1', '14')]:
        require(types[key] == 'power_out', 'Actual supply output electrical type changed: ' + str(key))

    board = parse(BOARD.read_text())
    require(board[0] == 'kicad_pcb', 'Not a native KiCad board')
    footprints = {}
    for fp in children(board, 'footprint'):
        ref = property_value(fp, 'Reference')
        require(ref not in footprints, 'Duplicate PCB reference ' + ref)
        footprints[ref] = fp
    require(set(footprints) == set(parts), 'PCB/model reference sets differ')
    numeric_nets = {node[1]: node[2] for node in children(board, 'net') if len(node) > 2}
    pads = {}
    physical_pad_count = 0
    for ref, part in parts.items():
        fp = footprints[ref]
        require(fp[1] == part['footprint'], f'PCB footprint identity differs: {ref}')
        for prop, key in [('Value', 'value'), ('MPN', 'mpn')]:
            fields = [value[2] for value in children(fp, 'property') if value[1] == prop]
            require(fields == [part[key]], f'PCB {prop} absent, duplicated or differs: {ref}')
        require(child(fp, 'path')[1] == mapping['parts'][ref]['path'], f'PCB schematic path differs: {ref}')
        at = child(fp, 'at')
        near(at[1], part['x'], ref + ' x'); near(at[2], part['y'], ref + ' y')
        rotation = float(at[3]) if len(at) > 3 else 0
        near((rotation - part['rotation'] + 180) % 360 - 180, 0, ref + ' rotation')
        require(child(fp, 'layer')[1] == {'top': 'F.Cu', 'bottom': 'B.Cu'}[part['side']], f'PCB side differs: {ref}')
        by_number = defaultdict(list)
        for pad in children(fp, 'pad'):
            if pad[1]:
                by_number[pad[1]].append(pad)
                physical_pad_count += 1
            else:
                require(not net_name(pad, numeric_nets), f'Unnamed mechanical pad carries a net: {ref}')
        require(set(by_number) == set(comps[ref]['pins']), f'PCB physical pad set differs: {ref}')
        for pin, repeated in by_number.items():
            require(all(net_name(pad, numeric_nets) == nets[(ref, pin)] for pad in repeated), f'PCB pad net differs: {ref}.{pin}')
        pads[ref] = dict(by_number)
    uuid_nodes = []
    def visit(node):
        if isinstance(node, list):
            if node and node[0] == 'uuid':
                uuid_nodes.append(node[1])
            for item in node:
                if isinstance(item, list):
                    visit(item)
    visit(board)
    require(len(uuid_nodes) == len(set(uuid_nodes)), 'Duplicate native PCB UUIDs')
    for kind in ('segment', 'arc', 'via', 'zone'):
        for item in children(board, kind):
            require(net_name(item, numeric_nets) not in set(nc.values()), 'Copper added to an explicitly unused net')
    require(len(children(board, 'segment')) > 0 and len(children(board, 'zone')) >= 2, 'Expected routed board with ground zones')
    near(child(child(board, 'general'), 'thickness')[1], 1, 'Board thickness')
    copper_layers = [x for x in child(board, 'layers')[1:] if isinstance(x, list) and len(x) > 2 and x[1].endswith('.Cu')]
    require(len(copper_layers) == model['layers'] == 2 and {x[1] for x in copper_layers} == {'F.Cu','B.Cu'}, 'Expected exactly two copper layers F.Cu/B.Cu')
    edges = [item for item in board if isinstance(item,list) and ['layer','Edge.Cuts'] in item]
    expected_lines = [((0,2),(0,38)),((2,0),(40,0)),((42,2),(42,38)),((2,40),(40,40))]
    corner = 2 - math.sqrt(2)
    expected_arcs = [((0,2),(2,0),(corner,corner)),
                     ((40,0),(42,2),(42-corner,corner)),
                     ((42,38),(40,40),(42-corner,40-corner)),
                     ((2,40),(0,38),(corner,40-corner))]
    require(len(edges) == 8 and sum(item[0] == 'gr_line' for item in edges) == 4
            and sum(item[0] == 'gr_arc' for item in edges) == 4, 'Expected four lines and four corner arcs in the board outline')
    for item in edges:
        points = sorted(tuple(map(float,child(item,name)[1:3])) for name in ('start','end'))
        options = expected_lines if item[0] == 'gr_line' else expected_arcs
        matches = [option for option in options if all(abs(a-b) <= 1e-5 for actual,target in zip(points,sorted(option[:2])) for a,b in zip(actual,target))]
        require(len(matches) == 1, 'Unexpected outline segment endpoints')
        matched = matches[0]
        options.remove(matched)
        if item[0] == 'gr_arc':
            middle = child(item,'mid')
            near(middle[1],matched[2][0],'Outline corner arc midpoint x')
            near(middle[2],matched[2][1],'Outline corner arc midpoint y')
    require(not expected_lines and not expected_arcs, 'Incomplete 42x40 mm outline with 2 mm corners')
    require(not any(['layer','Edge.Cuts'] in item for footprint in footprints.values() for item in footprint if isinstance(item,list)),
            'Unexpected footprint-owned Edge.Cuts geometry')

    # Hard-coded reviewed topology is independent of generated-file agreement.
    contract = verify_model_contract(model)
    oled_lands = verify_oled_lands(footprints['DS1'], True)
    verify_oled_lands(parse((Q3 / 'CountFidgetQ3.pretty/X087-2832TSWIG02-H14.kicad_mod').read_text()), False)
    inductor = verify_inductor(footprints['L1'], True)
    verify_inductor(parse((Q3 / 'CountFidgetQ3.pretty/Inductor_SMD_L_Murata_DFE201612E_2.0x1.6mm.kicad_mod').read_text()), False)
    verify_converter_lands(footprints['U6'])
    verify_converter_lands(parse((Q3/'CountFidgetQ3.pretty/TPS63900_DSK0010A_TI.kicad_mod').read_text()))
    for ref in ('SW1','SW2'): verify_switch_lands(footprints[ref])
    verify_switch_lands(parse((Q3/'CountFidgetQ3.pretty/HanElectricity_CPG151101D13_MX_Plate.kicad_mod').read_text()))
    verify_two_layer_copper(board, numeric_nets)
    require(parts['C6']['value'] == '10u' and parts['C6']['mpn'] == 'GRM21BR61E106KA73L' and set(parts['C6']['pins'].values()) == {'V3','GND'}, 'MCU bulk correction differs')
    require(parts['U3']['mpn'] == 'TPS7A0230PDBVR' and parts['U3']['pins'] == {'1':'SYS','2':'GND','3':'SYS','4':'GND','5':'V3'}, 'Explicit output-discharge regulator variant/topology differs')
    require(parts['U5']['mpn'] == 'TLV7012DGKR' and parts['U5']['pins'] == {'1':'TEMP_COLD_OK','2':'TEMP_SENSE','3':'TEMP_COLD','4':'GND','5':'TEMP_SENSE','6':'TEMP_HOT','7':'TEMP_HOT_OK','8':'VBUS'}, 'Separate push-pull comparator topology differs')
    expected_fets = {'Q3':{'1':'TEMP_COLD_OK','2':'CE_MID','3':'CE_N'}, 'Q4':{'1':'TEMP_HOT_OK','2':'GND','3':'CE_MID'}}
    for ref, pins in expected_fets.items():
        require(parts[ref]['pins'] == pins and parts[ref]['mpn'] == '2N7002,215', ref + ' series FET G/S/D topology differs')
    distances = {}
    for resistor, fet, net in [('R14','Q3','TEMP_COLD_OK'),('R15','Q4','TEMP_HOT_OK')]:
        require(parts[resistor]['value'] == '100k' and parts[resistor]['pins'] == {'1':net,'2':'GND'}, resistor + ' gate pulldown differs')
        a = world_pad(footprints[resistor], pads[resistor]['1'][0]); b = world_pad(footprints[fet], pads[fet]['1'][0])
        distance = math.hypot(a[0]-b[0], a[1]-b[1])
        require(distance < 3, f'{resistor} gate-net pad is {distance:.4f} mm from {fet} gate; require <3 mm')
        distances[resistor + '.1-to-' + fet + '.1'] = round(distance, 6)
    require(parts['R6']['value'] == '100k' and set(parts['R6']['pins'].values()) == {'VBUS','CE_N'}, 'CE_N default inhibit pull-up changed')
    # Preserve the specific TI DGK quote geometry; library agreement alone
    # would also accept a consistently mis-edited board and local footprint.
    land_rows = defaultdict(list)
    for number, repeated in pads['U5'].items():
        require(len(repeated) == 1, 'Duplicate comparator pad number')
        pad = repeated[0]
        require(pad[2:4] == ['smd','roundrect'], 'Comparator land type differs')
        size = child(pad,'size')
        near(size[1],1.4,'Comparator land length'); near(size[2],0.45,'Comparator land width')
        at = child(pad,'at')
        near(abs(float(at[1])),2.2,'Comparator land row offset')
        land_rows[round(float(at[1]),6)].append(float(at[2]))
        near(child(pad,'solder_mask_margin')[1],0.05,'Comparator NSMD margin')
        near(float(child(pad,'roundrect_rratio')[1])*0.45,0.05,'Comparator land corner radius')
    require(set(land_rows) == {-2.2,2.2} and all(len(ys) == 4 for ys in land_rows.values()), 'Comparator requires two rows of four lands')
    for ys in land_rows.values():
        for a,b in zip(sorted(ys),sorted(ys)[1:]):
            near(b-a,0.65,'Comparator land pitch')
    # The two body diodes point S->D: GND->CE_MID->CE_N, never CE_N->GND.
    return {'references':82,'fitted_components':70,'fixture_lands':10,'mounting_holes':2,
            'connected_physical_pins':218,'explicit_nc_physical_pins':50,'native_named_pads_including_duplicates':physical_pad_count,
            'all_fields_nets_placements_and_paths_match':True,'pcb_uuid_count':len(uuid_nodes),
            'comparator_land_mm':[1.4,0.45],'comparator_nsmd_margin_mm':0.05,
            'oled_lands':oled_lands,'inductor_keepouts':inductor,'reviewed_model_contract':contract,
            'gate_pulldown_pad_distances_mm':distances,
            'series_fet_body_diode_direction':'GND -> CE_MID -> CE_N; no CE_N -> GND body-diode bypass',
            'nc_nets':{ref+'.'+pin:net for (ref,pin),net in sorted(nc.items())}}


def courtyard_exception(violation, board=None):
    """One disclosed 3D projection overlap, never a copper/clearance exception.

    Engineering accepts J1's upper solder fillet <=0.5 mm below the switch's
    raised flange underside at 5 mm. Real soldering and fit remain unqualified.
    Both item identities and the specific reviewed XY geometry are locked.
    """
    require(violation.get('type') == 'pth_inside_courtyard' and violation.get('severity') == 'error'
            and violation.get('description') == 'PTH inside courtyard', 'Unapproved DRC violation')
    items = violation.get('items',[])
    require(len(items) == 2 and {x.get('uuid') for x in items} == {J1_SHELL_PAD_UUID,SW2_FOOTPRINT_UUID},
            'Courtyard exception is restricted to one exact J1 SH / SW2 pair')
    board = parse(BOARD.read_text()) if board is None else board
    fps = {property_value(fp,'Reference'):fp for fp in children(board,'footprint')}
    require(child(fps['SW2'],'uuid')[1] == SW2_FOOTPRINT_UUID, 'Approved switch identity changed')
    candidates = [p for p in children(fps['J1'],'pad') if child(p,'uuid')[1] == J1_SHELL_PAD_UUID]
    require(len(candidates) == 1, 'Approved shell pad missing')
    pad = candidates[0]
    require(pad[1:4] == ['SH','thru_hole','oval'], 'Approved shell pad type changed')
    require(property_value(fps['J1'],'MPN') == 'USB4105-GF-A' and property_value(fps['SW2'],'MPN') == 'CPG151101D13',
            'Approved mechanical exception part identities changed')
    near(child(fps['SW2'],'at')[1],33.065,'Approved SW2 X'); near(child(fps['SW2'],'at')[2],22.92,'Approved SW2 Y')
    near(float(child(fps['SW2'],'at')[3]) if len(child(fps['SW2'],'at'))>3 else 0,0,'Approved SW2 rotation')
    require(child(fps['J1'],'layer')[1] == 'B.Cu' and child(fps['SW2'],'layer')[1] == 'F.Cu', 'Approved exception assembly sides changed')
    point = world_pad(fps['J1'],pad)
    near(point[0],35.795,'Approved shell X'); near(point[1],19.62,'Approved shell Y')
    near(child(pad,'size')[1],1,'Approved shell pad local width'); near(child(pad,'size')[2],2.1,'Approved shell pad local height')
    near(float(child(pad,'at')[3])%180,90,'Approved shell pad world rotation')
    verify_switch_lands(fps['SW2'])
    central = next(p for p in children(fps['SW2'],'pad') if p[1] == '')
    switch_center = world_pad(fps['SW2'],central)
    lower_body_start_y = switch_center[1]-13.95/2
    shell_top_joint_end_y = point[1]+.5  # 1.0 mm world-Y size at 270 degrees.
    planar_gap = lower_body_start_y-shell_top_joint_end_y
    near(planar_gap,.905,'Approved shell/lower switch body planar gap')
    expected = {J1_SHELL_PAD_UUID:('PTH pad SH [GND] of J1',(35.795,19.62)),
                SW2_FOOTPRINT_UUID:('Footprint SW2',(33.065,22.92))}
    for item in items:
        label,point = expected[item['uuid']]
        require(item.get('description') == label, 'Approved exception item description changed')
        near(item['pos']['x'],point[0],'Exception native item X'); near(item['pos']['y'],point[1],'Exception native item Y')
    return {'type':'pth_inside_courtyard','count':1,'item_uuids':sorted(expected),
            'nominal_planar_gap_to_lower_switch_body_mm':round(planar_gap,6),'maximum_upper_solder_fillet_mm':.5,
            'raised_flange_underside_above_pcb_mm':5,
            'physical_vendor_fit_and_solder_height_acceptance_required':True}


def report_checks(path, kind):
    data = json.loads(path.read_text())
    require(data.get('$schema') == f'https://schemas.kicad.org/{kind}.v1.json', 'Unexpected native report schema')
    require(set(data.get('included_severities',[])) == {'error','warning','exclusion'}, kind + ' did not include all severities')
    ignored = {item['key'] for item in data.get('ignored_checks',[])}
    allowed = DRC_IGNORED if kind == 'drc' else ERC_IGNORED
    require(ignored <= allowed, f'{kind} silently ignores additional checks: {sorted(ignored-allowed)}')
    require(str(data.get('kicad_version','')).startswith('10.'), 'This verifier has been validated with KiCad 10 native reports')
    exceptions = []
    if kind == 'drc':
        require(data.get('source') == BOARD.name, 'DRC source board differs')
        for key in ('unconnected_items','schematic_parity'):
            require(key in data and data[key] == [], f'DRC {key} is not zero')
        require('violations' in data and len(data['violations']) <= 1, 'DRC has additional violations')
        if data['violations']: exceptions.append(courtyard_exception(data['violations'][0]))
    else:
        require(data.get('source') == SCHEMATIC.name and len(data.get('sheets',[])) == 8, 'ERC source/sheet count differs')
        require(all(sheet.get('violations') == [] for sheet in data['sheets']), 'ERC violations remain')
    return {'kicad_version':data['kicad_version'],'included_severities':sorted(data['included_severities']),
            'ignored_checks':sorted(ignored),'date_from_native_report':data.get('date'),'explicit_engineering_exceptions':exceptions}


def commands(cli):
    return [
        [str(cli),'sch','export','netlist','--format','kicadxml','--output',relative(NATIVE_XML),relative(SCHEMATIC)],
        [str(cli),'sch','erc','--format','json','--severity-all','--exit-code-violations','--output',relative(ERC),relative(SCHEMATIC)],
        [str(cli),'pcb','drc','--format','json','--schematic-parity','--all-track-errors','--severity-all','--exit-code-violations','--output',relative(DRC),relative(BOARD)],
    ]


def prepare_native(cli):
    cli = cli.resolve()
    require(cli.is_file(), 'KiCad CLI not found')
    VERIFY.mkdir(exist_ok=True)
    before = input_hashes()
    verify_semantics()
    version = subprocess.check_output([str(cli),'version'],cwd=ROOT,text=True).strip()
    require(version.startswith('10.'), 'KiCad 10 is required for the validated native workflow')
    require(input_hashes() == before, 'Q3 inputs changed during preparation')
    preparation = {'schema_version':SCHEMA_VERSION,'prepared_ns':time.time_ns(),
                   'prepared_utc':datetime.now(timezone.utc).isoformat(),'inputs_sha256':before,
                   'tool':{'version':version,'executable_sha256':digest(cli)},'commands':commands(cli)}
    PREPARE.write_text(json.dumps(preparation,indent=2,sort_keys=True)+'\n')
    return preparation


def bind_native():
    preparation = json.loads(PREPARE.read_text())
    require(preparation.get('schema_version') == SCHEMA_VERSION, 'Invalid native preparation')
    before, calls = preparation['inputs_sha256'], preparation['commands']
    require(input_hashes() == before, 'Q3 design inputs changed after native preparation; prepare and run again')
    require(len(calls) == 3 and calls == commands(Path(calls[0][0])), 'Prepared native commands differ')
    cli = Path(calls[0][0])
    require(digest(cli) == preparation['tool']['executable_sha256'], 'Prepared KiCad executable changed')
    for path in (DRC,ERC,NATIVE_XML):
        require(path.stat().st_mtime_ns >= preparation['prepared_ns'], 'Native output predates preparation: '+relative(path))
    checks = {'drc':report_checks(DRC,'drc'),'erc':report_checks(ERC,'erc')}
    require(all(check['kicad_version'] == preparation['tool']['version'] for check in checks.values()), 'Native report/tool versions differ')
    # Only public path metadata is normalized, as in the schematic exporter.
    xml = ET.parse(NATIVE_XML)
    original_source = xml.getroot().findtext('design/source')
    require(original_source in (str(SCHEMATIC),relative(SCHEMATIC)), 'Fresh native XML source differs')
    xml.getroot().find('design/source').text = relative(SCHEMATIC)
    xml.write(NATIVE_XML,encoding='utf-8',xml_declaration=True)
    require(xml_data(NATIVE_XML) == xml_data(PUBLIC_XML), 'Fresh native schematic export differs from saved public netlist')
    results = verify_semantics(NATIVE_XML)
    require(input_hashes() == before, 'Q3 design inputs changed during native checks; rerun after edits stop')
    report = {'schema_version':SCHEMA_VERSION,'status':'PASS with disclosed courtyard exception — unreleased engineering candidate' if checks['drc']['explicit_engineering_exceptions'] else 'PASS — unreleased engineering candidate',
              'hardware_tested':False,'manufacturing_released':False,
              'inputs_sha256':before,'reports_sha256':{relative(path):digest(path) for path in (DRC,ERC,NATIVE_XML)},
              'tool':preparation['tool'],'commands':calls,
              'native_preparation_utc':preparation['prepared_utc'],'native_binding_utc':datetime.now(timezone.utc).isoformat(),
              'native_checks':checks,'semantic_checks':results,
              'limitations':['File agreement, ERC and DRC do not establish analog behavior, battery safety, component sourcing or physical fit.',
                             'OLED XY lands, FPC Z transition, no-paste assembly process and actual module fit still require vendor approval.',
                             'Pulldown distance is pad-center straight-line proximity, not trace length or parasitic simulation.',
                             'Recorded native ignored checks remain explicit; clean reports are under that check configuration.',
                             'One UUID-specific J1 shell/SW2 courtyard projection exception is allowed only under the recorded geometry; solder-height and physical fit acceptance remain required.',
                             'Q1 frozen package verification is separate: run scripts/verify_project.py.']}
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    return report


def fresh(cli):
    preparation = prepare_native(cli)
    for index,call in enumerate(preparation['commands']):
        result = subprocess.run(call,cwd=ROOT,check=False)
        # KiCad returns 5 for the one explicitly reviewed courtyard violation.
        # Never accept that exit code without parsing the exact final report.
        require(result.returncode == 0 or (index == 2 and result.returncode == 5), 'Native check failed: '+shlex.join(call))
    return bind_native()


def saved():
    report = json.loads(REPORT.read_text())
    require(report.get('schema_version') == SCHEMA_VERSION and report.get('hardware_tested') is False and report.get('manufacturing_released') is False,
            'Invalid Q3 validation report version or release status')
    require(report['inputs_sha256'] == input_hashes(), 'Native Q3 reports are stale: an input or source file changed; run with --kicad-cli')
    expected = {relative(path):digest(path) for path in (DRC,ERC,NATIVE_XML)}
    require(report['reports_sha256'] == expected, 'Native report content changed after validation')
    calls = report['commands']
    require(len(calls) == 3 and calls == commands(Path(calls[0][0])), 'Recorded native commands do not match the required parity/ERC/export invocation')
    require(xml_data(NATIVE_XML) == xml_data(PUBLIC_XML), 'Public and fresh native schematic netlists differ')
    require(report['semantic_checks'] == verify_semantics(NATIVE_XML), 'Semantic checks no longer match saved validation')
    require(report['native_checks'] == {'drc':report_checks(DRC,'drc'),'erc':report_checks(ERC,'erc')}, 'Native check summaries differ')
    require(all(check['kicad_version'] == report['tool']['version'] for check in report['native_checks'].values()), 'Native report/tool versions differ')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--kicad-cli',type=Path,help='Run fresh native export/ERC/DRC with schematic parity and save bound evidence')
    mode.add_argument('--semantic-only',action='store_true',help='Check file agreement only; does not validate native report freshness')
    mode.add_argument('--prepare-native',type=Path,help='Freeze inputs and print the three native commands for separately approved execution')
    mode.add_argument('--bind-native',action='store_true',help='Validate and bind reports freshly produced after --prepare-native; rejects changed inputs')
    args=parser.parse_args()
    try:
        if args.prepare_native:
            preparation=prepare_native(args.prepare_native)
            print('Prepared exact Q3 inputs. Run these native commands from '+str(ROOT)+', then use --bind-native:')
            for call in preparation['commands']: print(shlex.join(call))
            print('Preparation is not validation and does not establish clean native checks.')
        elif args.semantic_only:
            results=verify_semantics()
            print(json.dumps(results,indent=2))
            print('SEMANTICS PASS only; fresh native DRC/ERC/parity and hash binding were not checked.')
        else:
            report=bind_native() if args.bind_native else fresh(args.kicad_cli) if args.kicad_cli else saved()
            exceptions=len(report['native_checks']['drc']['explicit_engineering_exceptions'])
            print('PASS: Q3 model/schematic/PCB agree: 82 references, 218 connected pins, 50 explicit NC pins; fresh-bound ERC/unconnected/parity zero; '+str(exceptions)+' disclosed courtyard exception(s).')
            print('Engineering candidate only. Q1/Q2 preservation and physical release gates remain separate.')
    except (ValueError,KeyError,StopIteration,OSError,ET.ParseError,subprocess.CalledProcessError) as error:
        print('FAIL: '+str(error),file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
