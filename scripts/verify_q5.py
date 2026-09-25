"""Verify Q5 native agreement and freshly bound ERC/DRC evidence.

This checks design files and native connectivity, not physical electrical function.
No courtyard or electrical DRC exceptions are accepted in Q5.
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from build_q5_model import make_model
from kicad_sexpr import child, children, parse, property_value
ROOT=Path(__file__).resolve().parents[1]
Q5=ROOT/'electronics/q5'
VERIFY=ROOT/'verification'
BOARD=Q5/'click-counter-Q5.kicad_pcb'
SCHEMATIC=Q5/'click-counter-Q5.kicad_sch'
PUBLIC_XML=Q5/'schematic-netlist-Q5.xml'
NATIVE_XML=VERIFY/'q5-native-netlist.xml'
DRC=VERIFY/'q5-native-drc.json'
ERC=VERIFY/'q5-native-erc.json'
REPORT=VERIFY/'q5-validation.json'
PREPARE=VERIFY/'q5-native-preparation.json'
ERC_IGNORED={'single_global_label','four_way_junction','simulation_model_issue','footprint_filter'}
DRC_IGNORED={'missing_courtyard','track_not_centered_on_via','tuning_profile_track_geometries','footprint_filters_mismatch','footprint_type_mismatch'}

def require(condition,message):
    if not condition: raise ValueError(message)

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def relative(path): return path.relative_to(ROOT).as_posix()

def input_hashes():
    paths={BOARD,SCHEMATIC,PUBLIC_XML,Q5/'netlist-Q5.json',Q5/'click-counter-Q5.kicad_pro',
           Q5/'schematic-paths-Q5.json',Q5/'sym-lib-table',Q5/'fp-lib-table',Path(__file__).resolve(),
           ROOT/'scripts/kicad_sexpr.py',ROOT/'scripts/build_q5_model.py',ROOT/'scripts/build_q5_schematic.py',
           ROOT/'scripts/build_q5_board.py',ROOT/'scripts/sync_q5_board.py',
           ROOT/'scripts/preroute_q5.py',ROOT/'scripts/prepare_q5_route.py',ROOT/'scripts/finish_q5_board.py',ROOT/'scripts/plan_q5_stitching.py',
           ROOT/'scripts/measure_q5_routes.py',
           ROOT/'electronics/q4/netlist-Q4.json'}
    for pattern in ('*.kicad_sch','*.kicad_sym','*.kicad_dru','*.pretty/*.kicad_mod'):
        paths.update(Q5.glob(pattern))
    for name in ('placement.json','circuit-contract.json','locked-route-seed.json'):
        if (Q5/name).exists(): paths.add(Q5/name)
    return {relative(p):digest(p) for p in sorted(paths)}

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
    model=make_model()
    require(json.loads((Q5/'netlist-Q5.json').read_text())==model,'Saved Q5 model is stale')
    require(model.get('hardware_tested') is False and model.get('manufacturing_released') is False,'Release status must remain false')
    parts={p['ref']:p for p in model['parts']}
    require(len(parts)==len(model['parts']),'Duplicate model reference')
    require(parts['U1']['mpn']=='STM32L072CBT6','Selected Q5 MCU differs')
    fitted=sum(not r.startswith(('TP','H')) for r in parts)
    require(fitted==model['fitted_components'],'Fitted count differs')
    comps,nets,nodes,types=xml_data(xml_path)
    require(set(comps)==set(parts),'Schematic/model reference sets differ')
    mapping=json.loads((Q5/'schematic-paths-Q5.json').read_text())
    require(set(mapping['parts'])==set(parts),'Pin/path mapping references differ')
    connected,nc={},{}
    for ref,part in parts.items():
        comp,entry=comps[ref],mapping['parts'][ref]
        for key in ('value','mpn','footprint'):
            require(comp[key]==part[key],f'Schematic identity differs: {ref}.{key}')
        require(set(comp['pins'])==set(entry['pins']),f'Physical pin set differs: {ref}')
        require(set(part['pins'])<=set(comp['pins']),f'Nonphysical intended pin: {ref}')
        require(comp['symbol_uuid']==entry['symbol_uuid'],f'Symbol UUID differs: {ref}')
        require('/'+mapping['root_uuid']+comp['sheet_path']+comp['symbol_uuid']==entry['path'],f'Symbol path differs: {ref}')
        for pin in comp['pins']:
            key=(ref,pin)
            require(key in nets,f'Physical pin absent in native export: {key}')
            if pin in part['pins']:
                require(nets[key]==part['pins'][pin],f'Native schematic net differs: {key}')
                connected[key]=nets[key]
            else:
                require(nets[key].startswith('unconnected-') and nodes[nets[key]]==[key],f'NC pin is not isolated: {key}')
                nc[key]=nets[key]
            require(entry['pins'][pin]['net']==part['pins'].get(pin),f'Pin mapping differs: {key}')
    require(set(comps['U1']['pins'])=={str(i) for i in range(1,49)},'MCU package must expose48physical pins')
    require(len(set(nc.values()))==len(nc),'Different NC pins share a net')
    tree=parse(BOARD.read_text())
    require(tree[0]=='kicad_pcb','Not a KiCad board')
    fps={}
    for fp in children(tree,'footprint'):
        ref=property_value(fp,'Reference')
        require(ref not in fps,'Duplicate PCB reference '+ref);fps[ref]=fp
    require(set(fps)==set(parts),'PCB/model reference sets differ')
    numeric={n[1]:n[2] for n in children(tree,'net') if len(n)>2}
    named_pads=0
    for ref,part in parts.items():
        fp=fps[ref]
        require(fp[1]==part['footprint'],f'PCB footprint differs: {ref}')
        for prop,key in [('Value','value'),('MPN','mpn')]:
            require([v[2] for v in children(fp,'property') if v[1]==prop]==[part[key]],f'PCB property differs: {ref}.{prop}')
        require(child(fp,'path')[1]==mapping['parts'][ref]['path'],f'PCB schematic path differs: {ref}')
        at=child(fp,'at');near(at[1],part['x'],ref+' x');near(at[2],part['y'],ref+' y')
        angle=float(at[3]) if len(at)>3 else 0
        near((angle-part['rotation']+180)%360-180,0,ref+' angle')
        require(child(fp,'layer')[1]=={'top':'F.Cu','bottom':'B.Cu'}[part['side']],f'PCB side differs: {ref}')
        by_pin=defaultdict(list)
        for pad in children(fp,'pad'):
            if pad[1]: by_pin[pad[1]].append(pad);named_pads+=1
            else: require(not net_name(pad,numeric),f'Mechanical pad has net: {ref}')
        require(set(by_pin)==set(comps[ref]['pins']),f'PCB physical pad set differs: {ref}')
        for pin,pads in by_pin.items():
            require(all(net_name(p,numeric)==nets[(ref,pin)] for p in pads),f'PCB pad net differs: {ref}.{pin}')
        # Match local land geometry to embedded geometry, allowing the native backside mirror.
        local=Q5/(part['footprint'].split(':')[0]+'.pretty')/(part['footprint'].split(':')[1]+'.kicad_mod')
        require(local.is_file(),f'Local footprint missing: {ref}')
        land=parse(local.read_text())
        lp=children(land,'pad'); ep=children(fp,'pad')
        require(len(lp)==len(ep),f'Local/embedded pad count differs: {ref}')
        def pad_geometry(p,local=False):
            at=child(p,'at');px,py=map(float,at[1:3]);pa=float(at[3]) if len(at)>3 else 0
            layers=child(p,'layers')[1:]
            if local:
                if part['side']=='bottom':
                    py=-py;pa=-pa
                    layers=[('B.'+x[2:]) if x.startswith('F.') else ('F.'+x[2:]) if x.startswith('B.') else x for x in layers]
                pa+=part['rotation']
            def number(v):
                try:return round(float(v),6)
                except ValueError:return v
            drill=tuple(tuple(number(v) for v in d[1:]) for d in children(p,'drill'))
            return (p[1],p[2],p[3],round(px,6),round(py,6),round(pa%180,6),
                    tuple(round(float(v),6) for v in child(p,'size')[1:]),drill,tuple(sorted(layers)))
        require(sorted(pad_geometry(p,True) for p in lp)==sorted(pad_geometry(p) for p in ep),
                f'Local/embedded pad positions, shapes, layers or drills differ: {ref}')
    uuids=[]
    def walk(n):
        if isinstance(n,list):
            if n and n[0]=='uuid': uuids.append(n[1])
            for x in n: walk(x)
    walk(tree);require(len(uuids)==len(set(uuids)),'Duplicate PCB UUID')
    for kind in ('segment','arc','via','zone'):
        for item in children(tree,kind):
            require(net_name(item,numeric) not in set(nc.values()),'Copper on NC net')
    require(children(tree,'segment'),'No routes')
    layers=[n[1] for n in child(tree,'layers')[1:] if isinstance(n,list) and n[1].endswith('.Cu')]
    require(set(layers)=={'F.Cu','B.Cu'} and model['layers']==2,'Q5 must use two copper layers')
    near(child(child(tree,'general'),'thickness')[1],model['board_mm'][2],'Board thickness')
    edge_graphics=[g for g in tree[1:] if isinstance(g,list) and g and g[0].startswith('gr_')
                   and children(g,'layer') and child(g,'layer')[1]=='Edge.Cuts']
    require(all(g[0]=='gr_line' for g in edge_graphics),'Native rectangular outline differs from model: extra primitive')
    edges=edge_graphics
    w,h,_=model['board_mm']
    actual_edges={tuple(sorted((tuple(map(float,child(g,'start')[1:3])),tuple(map(float,child(g,'end')[1:3]))))) for g in edges}
    expected_edges={tuple(sorted((a,b))) for a,b in [((0.,0.),(w,0.)),((w,0.),(w,h)),((w,h),(0.,h)),((0.,h),(0.,0.))]}
    require(len(edges)==4 and actual_edges==expected_edges,'Native rectangular outline differs from model')
    for via in children(tree,'via'):
        require(child(via,'layers')[1:]==['F.Cu','B.Cu'],'Unexpected via span')
    zones=children(tree,'zone')
    require(len(zones)>=2 and {child(z,'layer')[1] for z in zones}=={'F.Cu','B.Cu'},'Both ground fills required')
    require(all(net_name(z,numeric)=='GND' and not children(z,'keepout') for z in zones),'Unexpected power zone or suppressing rule area')
    # The explicit package topology contract is reviewed separately from generator agreement.
    contract=Q5/'circuit-contract.json'
    require(contract.exists(),'Reviewed Q5 circuit contract missing')
    c=json.loads(contract.read_text())
    for ref,entry in {**c['parts'],**c.get('critical_controls',{})}.items():
        require(ref in parts,f'Critical part omitted: {ref}')
        for key in ('mpn','value','footprint','pins'):
            if key in entry:
                require(parts[ref].get(key)==entry[key],f'Critical circuit contract differs: {ref}.{key}')
        if 'nc' in entry:
            require(set(entry['nc'])==set(comps[ref]['pins'])-set(parts[ref]['pins']),
                    f'Critical circuit contract differs: {ref}.nc')
        if 'physical_pin_count' in entry:
            require(len(comps[ref]['pins'])==entry['physical_pin_count'],
                    f'Critical circuit contract differs: {ref}.physical_pin_count')
    require(c.get('manufacturing_released') is False,'Contract cannot authorize manufacture')
    return dict(references=len(parts),fitted_components=fitted,connected_physical_pins=len(connected),
                explicit_nc_physical_pins=len(nc),named_pads_including_duplicates=named_pads,
                all_fields_nets_placements_paths_outline_and_local_land_geometry_match=True,
                nc_nets={ref+'.'+pin:net for (ref,pin),net in sorted(nc.items())})


def report_checks(path,kind):
    data=json.loads(path.read_text())
    require(data.get('$schema')==f'https://schemas.kicad.org/{kind}.v1.json','Unexpected native report schema')
    require(set(data.get('included_severities',[]))=={'error','warning','exclusion'},'All native severities required')
    ignored={v['key'] for v in data.get('ignored_checks',[])}
    require(ignored<=(DRC_IGNORED if kind=='drc' else ERC_IGNORED),'Additional native checks suppressed')
    require(str(data.get('kicad_version','')).startswith('10.'),'KiCad10native workflow required')
    if kind=='drc':
        require(data.get('source')==BOARD.name,'Wrong native board source')
        for key in ('violations','unconnected_items','schematic_parity'):
            require(key in data and data[key]==[],f'Native DRC {key} is not zero')
    else:
        require(data.get('source')==SCHEMATIC.name,'Wrong native schematic source')
        require(len(data.get('sheets',[]))==len(list(Q5.glob('*.kicad_sch'))),'ERC sheet count differs')
        require(all(x.get('violations')==[] for x in data['sheets']),'ERC violations remain')
    return dict(kicad_version=data['kicad_version'],ignored_checks=sorted(ignored),included_severities=sorted(data['included_severities']),date=data.get('date'))


def commands(cli):
    return [[str(cli),'sch','export','netlist','--format','kicadxml','--output',relative(NATIVE_XML),relative(SCHEMATIC)],
            [str(cli),'sch','erc','--format','json','--severity-all','--exit-code-violations','--output',relative(ERC),relative(SCHEMATIC)],
            [str(cli),'pcb','drc','--format','json','--schematic-parity','--all-track-errors','--severity-all','--exit-code-violations','--output',relative(DRC),relative(BOARD)]]


def fresh(cli):
    cli=cli.resolve();before=input_hashes();verify_semantics()
    VERIFY.mkdir(exist_ok=True)
    preparation=dict(prepared_ns=time.time_ns(),inputs_sha256=before,commands=commands(cli),tool_sha256=digest(cli))
    PREPARE.write_text(json.dumps(preparation,indent=2)+'\n')
    for call in preparation['commands']: subprocess.run(call,cwd=ROOT,check=True)
    require(input_hashes()==before,'Inputs changed during native checks')
    for p in (DRC,ERC,NATIVE_XML): require(p.stat().st_mtime_ns>=preparation['prepared_ns'],'Native output predates run')
    xml=ET.parse(NATIVE_XML);xml.getroot().find('design/source').text=relative(SCHEMATIC)
    xml.write(NATIVE_XML,encoding='utf-8',xml_declaration=True)
    require(xml_data(NATIVE_XML)==xml_data(PUBLIC_XML),'Native/public netlists differ')
    result=dict(schema_version=1,status='PASS_NATIVE_DESIGN_CHECKS_ONLY',hardware_tested=False,manufacturing_released=False,
                checked_utc=datetime.now(timezone.utc).isoformat(),inputs_sha256=before,
                reports_sha256={relative(p):digest(p) for p in (DRC,ERC,NATIVE_XML)},
                commands=preparation['commands'],tool_sha256=preparation['tool_sha256'],
                native_checks={k:report_checks(p,k) for p,k in ((DRC,'drc'),(ERC,'erc'))},
                semantic_checks=verify_semantics(NATIVE_XML),
                limitations=['No electrical/courtyard DRC exception accepted. Recorded ignored checks are explicit.',
                             'Native agreement does not establish measured power, USB, battery safety, inventory or physical fit.'])
    require(input_hashes()==before,'Inputs changed while binding native evidence')
    REPORT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');return result


def saved():
    r=json.loads(REPORT.read_text())
    require(r.get('schema_version')==1 and r.get('status')=='PASS_NATIVE_DESIGN_CHECKS_ONLY' and r.get('hardware_tested') is False and r.get('manufacturing_released') is False,'Invalid saved status')
    require(r['inputs_sha256']==input_hashes(),'Stale native evidence; design inputs changed')
    require(r['reports_sha256']=={relative(p):digest(p) for p in (DRC,ERC,NATIVE_XML)},'Native reports changed after binding')
    require(r['commands']==commands(Path(r['commands'][0][0])),'Recorded native invocation differs')
    require(xml_data(NATIVE_XML)==xml_data(PUBLIC_XML),'Native/public netlists differ')
    require(r['semantic_checks']==verify_semantics(NATIVE_XML),'Saved semantic summary differs')
    require(r['native_checks']=={k:report_checks(p,k) for p,k in ((DRC,'drc'),(ERC,'erc'))},'Saved native summary differs')
    return r


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--kicad-cli',type=Path);ap.add_argument('--semantic-only',action='store_true')
    args=ap.parse_args()
    try:
        r=verify_semantics() if args.semantic_only else fresh(args.kicad_cli) if args.kicad_cli else saved()
        print(json.dumps(r if args.semantic_only else r['semantic_checks'],indent=2))
        print('Q5 design-file checks passed; physical qualification and release remain separate.')
    except (ValueError,KeyError,OSError,ET.ParseError,subprocess.CalledProcessError) as e:
        print('FAIL: '+str(e),file=sys.stderr);return 1
    return 0
if __name__=='__main__': sys.exit(main())
