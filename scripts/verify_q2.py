"""Independently verify the unreleased Q2 model, native schematic and native PCB.

Uses only the Python standard library. Default mode checks saved native reports
and their input hashes; --kicad-cli regenerates those reports without editing the
board. --semantic-only checks data agreement but cannot certify fresh DRC/ERC.
This is design-file verification, never manufacturing release or hardware proof.
"""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

from build_q2_model import make_model
from kicad_sexpr import child, children, parse, property_value

ROOT = Path(__file__).resolve().parents[1]
Q2 = ROOT / 'electronics/q2'
VERIFY = ROOT / 'verification'
BOARD = Q2 / 'click-counter-Q2.kicad_pcb'
SCHEMATIC = Q2 / 'click-counter-Q2.kicad_sch'
PUBLIC_XML = Q2 / 'schematic-netlist-Q2.xml'
REPORT = VERIFY / 'q2-validation.json'
DRC = VERIFY / 'q2-native-drc.json'
ERC = VERIFY / 'q2-native-erc.json'
NATIVE_XML = VERIFY / 'q2-native-netlist.xml'
SCHEMATIC_EVIDENCE = Q2 / 'schematic-validation-Q2.json'
SCHEMA_VERSION = 1
ERC_IGNORED = {'single_global_label', 'four_way_junction', 'simulation_model_issue', 'footprint_filter'}
DRC_IGNORED = {'missing_courtyard', 'track_not_centered_on_via', 'tuning_profile_track_geometries',
               'footprint_filters_mismatch', 'footprint_type_mismatch'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def input_hashes():
    paths = {BOARD, Q2 / 'click-counter-Q2.kicad_pro', Q2 / 'netlist-Q2.json',
             PUBLIC_XML, Q2 / 'schematic-paths-Q2.json', Q2 / 'sym-lib-table', Q2 / 'fp-lib-table',
             ROOT / 'electronics/netlist.json', Path(__file__).resolve(), ROOT / 'scripts/kicad_sexpr.py',
             ROOT / 'scripts/build_q2_model.py', ROOT / 'scripts/build_q2_schematic.py',
             ROOT / 'scripts/build_q2_board.py', ROOT / 'scripts/sync_q2_board.py', ROOT / 'scripts/finish_q2_board.py', ROOT / 'scripts/preroute_q2.py'}
    paths.update(Q2.glob('*.kicad_sch'))
    paths.update(Q2.glob('*.kicad_sym'))
    paths.update(Q2.glob('*.kicad_dru'))
    paths.update(Q2.glob('*.pretty/*.kicad_mod'))
    paths.add(SCHEMATIC_EVIDENCE)
    paths.update(schematic_artifacts())
    return {relative(path): digest(path) for path in sorted(paths)}


def schematic_artifacts():
    return {*(Q2.glob('*.kicad_sch')), Q2 / 'CountFidgetQ2.kicad_sym', Q2 / 'sym-lib-table',
            Q2 / 'schematic-paths-Q2.json', PUBLIC_XML, Q2 / 'erc-Q2.json', Q2 / 'schematic-Q2.pdf',
            *(Q2 / 'schematic-svg').glob('*.svg')}


def verify_schematic_evidence():
    report = json.loads(SCHEMATIC_EVIDENCE.read_text())
    require(len(list(Q2.glob('*.kicad_sch'))) == 6 and len(list((Q2 / 'schematic-svg').glob('*.svg'))) == 6, 'Expected six native schematic sheets and six SVG exports')
    inputs = {ROOT / 'scripts/build_q2_schematic.py', ROOT / 'scripts/build_q2_model.py', ROOT / 'electronics/netlist.json'}
    require(report['inputs_sha256'] == {relative(path):digest(path) for path in inputs}, 'Schematic export evidence has stale generator/model inputs; regenerate the schematic')
    require(report['artifacts_sha256'] == {relative(path):digest(path) for path in schematic_artifacts()}, 'Schematic PDF/SVG/ERC/native export evidence is stale or incomplete')
    require(report['sheets'] == 6 and report['components_and_pcb_features'] == 62 and report['fitted_components'] == 50
            and report['connected_pins_matched'] == 195 and report['explicit_unused_pins'] == 28 and report['erc_violations'] == 0,
            'Schematic evidence counts differ')
    report_checks(Q2 / 'erc-Q2.json', 'erc')


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


def verify_semantics(xml_path=PUBLIC_XML):
    model = make_model()
    verify_schematic_evidence()
    require(model['board_mm'] == [42,40,1], 'Model board dimensions differ from the verified candidate')
    require(json.loads((Q2 / 'netlist-Q2.json').read_text()) == model, 'Saved Q2 model is stale; rebuild from make_model()')
    require(model['hardware_tested'] is False and model['manufacturing_released'] is False, 'Candidate release gates changed')
    parts = {part['ref']: part for part in model['parts']}
    require(len(parts) == len(model['parts']) == 62, 'Expected 62 unique model references')
    fitted = sum(not ref.startswith(('TP', 'H')) for ref in parts)
    require(fitted == model['fitted_components'] == 50, 'Expected 50 fitted components')
    require(sum(ref.startswith('TP') for ref in parts) == 10 and sum(ref.startswith('H') for ref in parts) == 2,
            'Expected ten fixture lands and two mounting holes')
    comps, nets, nodes, types = xml_data(xml_path)
    require(set(comps) == set(parts), 'Schematic/model reference sets differ')
    mapping = json.loads((Q2 / 'schematic-paths-Q2.json').read_text())
    require(set(mapping['parts']) == set(parts), 'Schematic path map reference sets differ')
    connected, nc = {}, {}
    for ref, part in parts.items():
        comp, entry = comps[ref], mapping['parts'][ref]
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
    require(len(connected) == 195 and len(nc) == 28 and len(nets) == 223, 'Connected/NC physical pin counts differ from 195/28')
    require(len(set(nc.values())) == 28, 'NC net names are not unique')
    for key in [('U5', '1'), ('U5', '7')]:
        require(types[key] == 'output', 'Comparator must retain a push-pull output pin type: ' + str(key))
    for key in [('U2', '1'), ('U3', '5')]:
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
    require(len(copper_layers) == model['layers'] == 4, 'Expected four copper layers')
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

    # Explicit engineering invariants supplement agreement between generated files.
    critical_lcd = {}
    for net in ('LCD_R13','LCD_R23','LCD_R33','LCDCAP0','LCDCAP1'):
        require(len(nodes.get(net,[])) == 2, net + ' must remain an isolated two-pin capacitor net')
        traces = [item for item in children(board,'segment') if net_name(item,numeric_nets) == net]
        vias = [item for item in children(board,'via') if net_name(item,numeric_nets) == net]
        require(traces and all(['locked','yes'] in item for item in traces), net + ' must retain only locked critical traces')
        require(len(vias) == 1 and ['locked','yes'] in vias[0], net + ' must retain one locked through via')
        require(child(vias[0],'layers')[1:] == ['F.Cu','B.Cu'], net + ' critical via must span the complete board')
        near(child(vias[0],'drill')[1],0.3,net + ' critical via drill')
        near(child(vias[0],'size')[1],0.6,net + ' critical via land')
        require(not any(net_name(item,numeric_nets) == net for kind in ('arc','zone') for item in children(board,kind)),
                net + ' has unexpected non-segment copper')
        length = sum(math.hypot(float(child(item,'start')[1])-float(child(item,'end')[1]),
                               float(child(item,'start')[2])-float(child(item,'end')[2])) for item in traces)
        require(0 < length < 5, f'{net} routed copper length {length:.4f} mm exceeds the reviewed <5 mm bound')
        critical_lcd[net] = {'trace_length_mm':round(length,6),'locked_segments':len(traces),'locked_through_vias':1}
    for pin, cap, net in [('7','C14','LCD_R13'), ('8','C15','LCD_R23'), ('9','C16','LCD_R33')]:
        require(connected[('U1',pin)] == net and parts[cap]['pins'] == {'1':net,'2':'GND'}, 'Mode-2 bias capacitor topology differs')
        require(parts[cap]['value'] == '100n' and parts[cap]['mpn'] == 'GRM188R71H104KA93D', cap + ' bias reservoir type differs')
    require(parts['C8']['pins'] == {'1':'LCDCAP1','2':'LCDCAP0'} and parts['C8']['value'] == '100n'
            and parts['U1']['pins']['10'] == 'LCDCAP1' and parts['U1']['pins']['11'] == 'LCDCAP0', 'LCD charge-pump capacitor/pin mapping differs')
    require(parts['C6']['value'] == '10u' and parts['C6']['mpn'] == 'GRM21BR61E106KA73L' and set(parts['C6']['pins'].values()) == {'V3','GND'}, 'MCU bulk correction differs')
    require(parts['U3']['mpn'] == 'TPS7A0230PDBVR' and parts['U3']['pins'] == {'1':'SYS','2':'GND','3':'SYS','4':'GND','5':'V3'}, 'Explicit output-discharge regulator variant/topology differs')
    require(parts['U5']['mpn'] == 'TLV7032DGKR' and parts['U5']['pins'] == {'1':'TEMP_COLD_OK','2':'TEMP_SENSE','3':'TEMP_COLD','4':'GND','5':'TEMP_SENSE','6':'TEMP_HOT','7':'TEMP_HOT_OK','8':'VBUS'}, 'Separate push-pull comparator topology differs')
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
    rows = defaultdict(list)
    for number, repeated in pads['DS1'].items():
        require(len(repeated) == 1, 'Duplicate DE188 pad number')
        pad = repeated[0]; at = child(pad,'at')
        rows[round(float(at[2]),6)].append(float(at[1]))
        near(child(pad,'drill')[1], 1.7, 'DE188 retained quote drill')
    require(set(rows) == {-6.5,6.5} and all(len(xs) == 10 for xs in rows.values()), 'DE188 must have ten pads in each nominal 13.0 mm row')
    for xs in rows.values():
        ordered = sorted(xs)
        for a,b in zip(ordered,ordered[1:]):
            near(b-a, 2.54, 'DE188 lead pitch')
    return {'references':62,'fitted_components':50,'fixture_lands':10,'mounting_holes':2,
            'connected_physical_pins':195,'explicit_nc_physical_pins':28,'native_named_pads_including_duplicates':physical_pad_count,
            'critical_lcd_paths':critical_lcd,'all_fields_nets_placements_and_paths_match':True,'pcb_uuid_count':len(uuid_nodes),
            'comparator_land_mm':[1.4,0.45],'comparator_nsmd_margin_mm':0.05,
            'display_row_pitch_mm':13.0,'display_retained_drill_mm':1.7,'gate_pulldown_pad_distances_mm':distances,
            'series_fet_body_diode_direction':'GND -> CE_MID -> CE_N; no CE_N -> GND body-diode bypass',
            'nc_nets':{ref+'.'+pin:net for (ref,pin),net in sorted(nc.items())}}


def report_checks(path, kind):
    data = json.loads(path.read_text())
    require(data.get('$schema') == f'https://schemas.kicad.org/{kind}.v1.json', 'Unexpected native report schema')
    require(set(data.get('included_severities',[])) == {'error','warning','exclusion'}, kind + ' did not include all severities')
    ignored = {item['key'] for item in data.get('ignored_checks',[])}
    allowed = DRC_IGNORED if kind == 'drc' else ERC_IGNORED
    require(ignored <= allowed, f'{kind} silently ignores additional checks: {sorted(ignored-allowed)}')
    require(str(data.get('kicad_version','')).startswith('10.'), 'This verifier has been validated with KiCad 10 native reports')
    if kind == 'drc':
        require(data.get('source') == BOARD.name, 'DRC source board differs')
        for key in ('violations','unconnected_items','schematic_parity'):
            require(key in data and data[key] == [], f'DRC {key} is not zero')
    else:
        require(data.get('source') == SCHEMATIC.name and len(data.get('sheets',[])) == 6, 'ERC source/sheet count differs')
        require(all(sheet.get('violations') == [] for sheet in data['sheets']), 'ERC violations remain')
    return {'kicad_version':data['kicad_version'],'included_severities':sorted(data['included_severities']),
            'ignored_checks':sorted(ignored),'date_from_native_report':data.get('date')}


def commands(cli):
    return [
        [str(cli),'sch','export','netlist','--format','kicadxml','--output',relative(NATIVE_XML),relative(SCHEMATIC)],
        [str(cli),'sch','erc','--format','json','--severity-all','--exit-code-violations','--output',relative(ERC),relative(SCHEMATIC)],
        [str(cli),'pcb','drc','--format','json','--schematic-parity','--all-track-errors','--severity-all','--exit-code-violations','--output',relative(DRC),relative(BOARD)],
    ]


def fresh(cli):
    cli = cli.resolve()
    require(cli.is_file(), 'KiCad CLI not found')
    VERIFY.mkdir(exist_ok=True)
    before = input_hashes()
    verify_semantics()
    version = subprocess.check_output([str(cli),'version'],cwd=ROOT,text=True).strip()
    require(version.startswith('10.'), 'KiCad 10 is required for the validated native workflow')
    calls = commands(cli)
    for call in calls:
        subprocess.run(call,cwd=ROOT,check=True)
    # Only public path metadata is normalized, as in the schematic exporter.
    xml = ET.parse(NATIVE_XML)
    xml.getroot().find('design/source').text = relative(SCHEMATIC)
    xml.write(NATIVE_XML,encoding='utf-8',xml_declaration=True)
    require(xml_data(NATIVE_XML) == xml_data(PUBLIC_XML), 'Fresh native schematic export differs from saved public netlist')
    results = verify_semantics(NATIVE_XML)
    checks = {'drc':report_checks(DRC,'drc'),'erc':report_checks(ERC,'erc')}
    require(input_hashes() == before, 'Q2 design inputs changed during native checks; rerun after edits stop')
    report = {'schema_version':SCHEMA_VERSION,'status':'PASS — unreleased engineering candidate',
              'hardware_tested':False,'manufacturing_released':False,
              'inputs_sha256':before,'reports_sha256':{relative(path):digest(path) for path in (DRC,ERC,NATIVE_XML)},
              'tool':{'version':version,'executable_sha256':digest(cli)},'commands':calls,
              'native_checks':checks,'semantic_checks':results,
              'limitations':['File agreement, ERC and DRC do not establish analog behavior, battery safety, component sourcing or physical fit.',
                             'DE188 1.7 mm drill remains a quote/fit assumption, not a validated assembly tolerance.',
                             'Pulldown distance is pad-center straight-line proximity, not trace length or parasitic simulation.',
                             'Recorded native ignored checks remain explicit; clean reports are under that check configuration.',
                             'Q1 frozen package verification is separate: run scripts/verify_project.py.']}
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    return report


def saved():
    report = json.loads(REPORT.read_text())
    require(report.get('schema_version') == SCHEMA_VERSION and report.get('hardware_tested') is False and report.get('manufacturing_released') is False,
            'Invalid Q2 validation report version or release status')
    require(report['inputs_sha256'] == input_hashes(), 'Native Q2 reports are stale: an input or source file changed; run with --kicad-cli')
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
    args=parser.parse_args()
    try:
        if args.semantic_only:
            results=verify_semantics()
            print(json.dumps(results,indent=2))
            print('SEMANTICS PASS only; fresh native DRC/ERC/parity and hash binding were not checked.')
        else:
            report=fresh(args.kicad_cli) if args.kicad_cli else saved()
            print('PASS: Q2 model/schematic/PCB agree: 62 references, 195 connected pins, 28 explicit NC pins; fresh-bound DRC/ERC/parity zero.')
            print('Engineering candidate only. Q1 verification and physical release gates remain separate.')
    except (ValueError,KeyError,StopIteration,OSError,ET.ParseError,subprocess.CalledProcessError) as error:
        print('FAIL: '+str(error),file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
