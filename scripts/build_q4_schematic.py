"""Generate the separate Q4 native schematic from its controlled connectivity model.

All IC/package pins are explicit. Unused physical pins receive no-connect marks.
Run KiCad ERC/export separately; generation alone is not electrical verification.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import uuid
import xml.etree.ElementTree as ET

from build_q4_model import make_model

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "electronics/q4"
PROJECT = "click-counter-Q4"
LIB = "CountFidgetQ4"
NS = uuid.UUID("3600bd11-75f6-5b7e-b663-0e10c096e390")


def uid(name):
    return str(uuid.uuid5(NS, name))


ROOT_ID = uid("root")
q = json.dumps


def effects(size=1.27, hidden=False, justify=""):
    return f'(effects (font (size {size} {size}))' + (f' (justify {justify})' if justify else '') + (' (hide yes)' if hidden else '') + ')'


def prop(name, value, x, y, hidden=False, size=1.27):
    return f'(property {q(name)} {q(value)} (at {x} {y} 0) {effects(size, hidden)})'


def text(value, x, y, size=1.524):
    return f'(text {q(value)} (at {x} {y} 0) {effects(size, justify="left top")} (uuid "{uid("text/"+value+str(x)+str(y))}"))'


IC_PINS = {
    'U6': [('EN','input'),('SEL','input'),('CFG1','input'),('CFG2','input'),('CFG3','input'),('VOUT','power_out'),('LX2','passive'),('GND','power_in'),('LX1','passive'),('VIN','power_in'),('EP/GND','power_in')],
    'U2': [('SYS','power_out'),('BAT','passive'),('STAT2','open_collector'),('~{CE}','input'),
           ('GND','power_in'),('TS/MR','input'),('ILIM/VSET','input'),('ISET','input'),
           ('STAT1','open_collector'),('IN','power_in'),('EP/GND','power_in')],
    'U3': [('IN','power_in'),('GND','power_in'),('EN','input'),('NC/GND-permitted','passive'),('OUT','power_out')],
    'U4': [('NC','no_connect'),('COUT','output'),('DOUT','output'),('VSS','power_in'),('BAT','power_in'),('V-','input')],
    'U5': [('OUTA','output'),('INA-','input'),('INA+','input'),('VEE','power_in'),
           ('INB+','input'),('INB-','input'),('OUTB','output'),('VCC','power_in')],
}


def pins_for(p):
    ref = p['ref']
    if p.get('symbol_pins'):
        return [(str(n), v['name'], v['type']) for n,v in p['symbol_pins'].items()]
    if ref == 'U1':
        raise ValueError('Q4 MCU needs reviewed physical symbol_pins metadata')
    if ref in IC_PINS:
        return [(str(i), name, kind) for i,(name,kind) in enumerate(IC_PINS[ref],1)]
    if ref.startswith('Q'):
        return [('1','G','input'),('2','S','passive'),('3','D','passive')]
    if ref == 'D1':
        return [(str(i), name, 'power_in' if i in (2,5) else 'passive') for i,name in enumerate(('I/O1','GND','I/O2','I/O2','VBUS','I/O1'),1)]
    if ref == 'J1':
        functions = {'1':'GND','4':'VBUS','5':'CC','6':'D+','7':'D-','8':'SBU','9':'VBUS','12':'GND'}
        return [(side+number,functions[number]+(side if number in ('5','8') else ''),'passive')
                for side in ('A','B') for number in ('1','4','5','6','7','8','9','12')] + [('SH','SHIELD','passive')]
    if ref == 'J2':
        return [('1','CELL+','passive'),('2','CELL-RAW','passive'),('3','NTC','passive'),('4','NTC-RETURN','passive'),('MP1','ANCHOR1','passive'),('MP2','ANCHOR2','passive')]
    if ref == 'DS1':
        names=['C2P','C2N','C1P','C1N','VBAT','NC','VSS','VDD','RES#','SCL','SDA','IREF','VCOMH','VCC']
        return [(str(i),name,'power_in' if i in (5,7,8) else 'power_out' if i in (13,14) else 'input' if i in (9,10) else 'bidirectional' if i==11 else 'no_connect' if i==6 else 'passive') for i,name in enumerate(names,1)]
    return [(str(i),str(i),'passive') for i in p['pins']]


def layout(p):
    pins = pins_for(p)
    if p['ref'][0] in 'RC' or p['ref'].startswith('SW'):
        return 5.08, 2.54, [('1','1','passive',-10.16,0,0),('2','2','passive',10.16,0,180)]
    if p['ref'].startswith('TP'):
        return 2.54, 2.54, [('1','1','passive',-7.62,0,0)]
    if not pins:
        return 5.08, 3.81, []
    left=(len(pins)+1)//2
    width=45.72 if p['ref']=='U1' else 22.86 if p['ref']=='U3' else 17.78
    half=max(7.62,(left+1)*2.54)
    result=[]
    for i,(number,name,kind) in enumerate(pins):
        side=-1 if i<left else 1
        j=i if i<left else i-left
        yy=(left-1)*2.54-j*5.08
        result.append((number,name,kind,side*(width+5.08),yy,0 if side<0 else 180))
    return width,half,result


def library_symbol(p):
    ref=p['ref']; w,h,pins=layout(p); prefix=re.match(r'[A-Z]+',ref)[0]
    body=f'(rectangle (start {-w} {h}) (end {w} {-h}) (stroke (width 0.254) (type default)) (fill (type background)))'
    if ref.startswith('C'):
        body=''.join(f'(polyline (pts (xy {x} -2.54) (xy {x} 2.54)) (stroke (width 0.254) (type default)) (fill (type none)))' for x in (-1.27,1.27))
        body+=''.join(f'(polyline (pts (xy {x} 0) (xy {y} 0)) (stroke (width 0) (type default)) (fill (type none)))' for x,y in ((-5.08,-1.27),(1.27,5.08)))
    if ref.startswith('SW'):
        body='(polyline (pts (xy -5.08 0) (xy 3.81 2.54)) (stroke (width .254) (type default)) (fill (type none)))'
        body+=''.join(f'(circle (center {x} 0) (radius .508) (stroke (width .254) (type default)) (fill (type none)))' for x in (-5.08,5.08))
    if ref.startswith(('TP','H')):
        body='(circle (center 0 0) (radius 2.54) (stroke (width .254) (type default)) (fill (type none)))'
    content=''.join(f'(pin {kind} line (at {x} {y} {angle}) (length 5.08) (name {q(name)} {effects(1.524)}) (number {q(number)} {effects(1.27)}))'
                    for number,name,kind,x,y,angle in pins)
    hidden = ref[0] in 'RC' or ref.startswith(('SW','TP','H'))
    return f'''(symbol {q(ref)} (pin_names (offset 1.016){' hide' if hidden else ''}) {'(pin_numbers hide)' if hidden else ''} (exclude_from_sim no)
      (in_bom {"no" if ref.startswith(("TP","H")) else "yes"}) (on_board yes)
      {prop('Reference',prefix,0,h+3.81)} {prop('Value',p['mpn'],0,-h-3.81)}
      {prop('Footprint',p['footprint'],0,0,True)}
      (symbol {q(ref+'_0_1')} {body}) (symbol {q(ref+'_1_1')} {content}))'''


def glabel(net,x,y,angle,key):
    return f'''(global_label {q(net)} (shape bidirectional) (at {x} {y} {angle})
      {effects(1.524,justify='left' if angle==0 else 'right')} (uuid "{uid(key)}")
      {prop('Intersheetrefs','${INTERSHEET_REFS}',x,y,True)})'''


def place(p,x,y,sheet):
    x,y=round(round(x/1.27)*1.27,4),round(round(y/1.27)*1.27,4)
    ref=p['ref']; w,h,pins=layout(p); inst=uid('symbol/'+ref)
    sheetid=uid('sheet/'+sheet)
    path=f'/{ROOT_ID}/{sheetid}'
    show_mpn=not (ref[0] in 'RC' or ref.startswith(('SW','TP','H')))
    value=p['value']
    symbol=f'''(symbol (lib_id "{LIB}:{ref}") (at {x} {y} 0) (unit 1) (exclude_from_sim no)
      (in_bom {"no" if ref.startswith(("TP","H")) else "yes"}) (on_board yes) (dnp no)
      (uuid "{inst}") {prop('Reference',ref,x,y-h-6.35,False,1.524)} {prop('Value',value,x,y-h-2.54,show_mpn,1.524)}
      {prop('Footprint',p['footprint'],x,y,True)} {prop('MPN',p['mpn'],x,y-h-2.54,not show_mpn,1.524)}
      {prop('Description',p['notes'],x,y,True)}
      {''.join('(pin '+q(pin[0])+' (uuid "'+uid('pin/'+ref+'/'+pin[0])+'"))' for pin in pins)}
      (instances (project "{PROJECT}" (path "{path}" (reference "{ref}") (unit 1)))))'''
    extras=[]
    for number,name,kind,px,py,angle in pins:
        ax,ay=round(x+px,4),round(y-py,4)
        if number not in p['pins']:
            extras.append(f'(no_connect (at {ax} {ay}) (uuid "{uid("nc/"+ref+"/"+number)}"))')
        else:
            bx=round(ax+(-7.62 if px<0 else 7.62),4)
            extras.append(f'(wire (pts (xy {ax} {ay}) (xy {bx} {ay})) (stroke (width 0) (type default)) (uuid "{uid("wire/"+ref+"/"+number)}"))')
            extras.append(glabel(p['pins'][number],bx,ay,180 if px<0 else 0,'label/'+ref+'/'+number))
    return symbol+'\n'+'\n'.join(extras), {'sheet':sheet,'sheet_file':sheet+'.kicad_sch','symbol_uuid':inst,'path':path+'/'+inst,
                                          'pins':{n:{'name':name,'type':kind,'net':p['pins'].get(n)} for n,name,kind,*_ in pins}}


FLAG = '''(symbol "SupplyAssertion" (pin_names (offset 0) hide) (exclude_from_sim no) (in_bom no) (on_board no)
 (property "Reference" "#FLG" (at 0 3.81 0) (effects (font (size 1.016 1.016)) (hide yes)))
 (property "Value" "PWR_FLAG" (at 0 3.81 0) (effects (font (size 1.016 1.016))))
 (symbol "SupplyAssertion_0_1" (polyline (pts (xy 0 0) (xy -2.54 1.27) (xy 0 2.54) (xy 2.54 1.27) (xy 0 0)) (stroke (width 0) (type default)) (fill (type none))))
 (symbol "SupplyAssertion_1_1" (pin power_out line (at 0 0 90) (length 0) (name "pwr" (effects (font (size 1.016 1.016)))) (number "1" (effects (font (size 1.016 1.016)))))))'''


def supply_assertion(net,x,y,sheet,index):
    x,y=round(round(x/1.27)*1.27,4),round(round(y/1.27)*1.27,4)
    ref='#FLG'+str(index); path=f'/{ROOT_ID}/{uid("sheet/"+sheet)}'; sid=uid('flag/'+net)
    return f'''(symbol (lib_id "{LIB}:SupplyAssertion") (at {x} {y} 0) (unit 1)
      (exclude_from_sim no) (in_bom no) (on_board no) (dnp no) (uuid "{sid}")
      {prop('Reference',ref,x,y,True)} {prop('Value','SUPPLY ASSERTION',x,y-5.08,False,1.016)}
      (pin "1" (uuid "{uid('flagpin/'+net)}"))
      (instances (project "{PROJECT}" (path "{path}" (reference "{ref}") (unit 1)))))
      '''+glabel(net,x,y,0,'flaglabel/'+net)


PAGES = []

SHEET_INFO = {
 'mcu': ('STM32 and USB boot controls', 'STM32L072CBT6. USB ROM DFU uses BOOT0 held high during NRST reset.\nAll supplies share VLOGIC; unused physical pins are explicitly NC. SWD is retained.'),
 'display': ('SPI OLED module and power control', 'Complete HS96L01W4S03 module; seven-pin SPI interface.\nSignals must be high impedance before module power is disabled. Mechanical drawing controls the footprint.'),
 'memory': ('Independent SPI retained-count memory', 'FM25V02A F-RAM on an isolated RC supply; dedicated SPI1.\nPower-ramp, chip-select and interrupted-write behavior require separate analysis and physical qualification.'),
 'usb-power': ('USB, charging and common supply', 'USB-C carries power and USB full-speed data in either orientation.\nShared adjustable supply and downstream slew do not prove battery cold-insertion recovery.'),
 'battery': ('Battery connection and protection', 'CELL_N_RAW is isolated from system ground by the protection path.\nCell compatibility, protection, USB rearm and the final battery harness remain qualification gates.'),
 'thermal': ('Independent charge-temperature window', 'Both temperature-window outputs must enable their series FETs for charging.\nGate pulldowns disable charging when comparator power is absent; threshold and fault tests remain required.'),
}

def make_pages(parts):
    pages=[]
    for group,(title,note) in SHEET_INFO.items():
        refs=[r for r,p in parts.items() if p.get('sheet')==group]
        page=0
        if 'U1' in refs:
            group_refs=['U1']+[r for r in ('C31','C32','C33','C34') if r in refs]
            positions=[('U1',105,140)]+[(r,310,75+i*48) for i,r in enumerate(group_refs[1:])]
            pages.append((group+'-1',title,positions,note)); page=1
            refs=[r for r in refs if r not in group_refs]
        while refs:
            selected=refs[:6]; refs=refs[6:];page+=1
            positions=[(r,105+(i%2)*190,83+(i//2)*78) for i,r in enumerate(selected)]
            pages.append((group+'-'+str(page),title+' / '+str(page),positions,note))
    return pages


def header(identity,title):
    return f'''(kicad_sch (version 20250114) (generator "eeschema") (generator_version "10.0")
      (uuid "{identity}") (paper "A3") (title_block (title {q(title)}) (rev "Q4 candidate")
      (company "Count Fidget") (comment 1 "ENGINEERING CANDIDATE - NOT RELEASED FOR MANUFACTURE"))'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kicad-cli',type=Path,help='Also run sequential native export/ERC/model checks with this KiCad CLI')
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    model=make_model(); parts={p['ref']:dict(p) for p in model['parts']}
    for ref,pins in model.get('symbol_pins',{}).items():
        parts[ref]['symbol_pins']=pins
    global PAGES
    PAGES = make_pages(parts)
    placed=[ref for _,_,positions,_ in PAGES for ref,_,_ in positions]
    assert set(placed)==set(parts) and len(placed)==len(parts), 'Every PCB part/feature must appear once'
    definitions={ref:library_symbol(p) for ref,p in parts.items()}
    (OUT/(LIB+'.kicad_sym')).write_text('(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor")\n'+'\n'.join(definitions.values())+'\n'+FLAG+'\n)\n')
    (OUT/'sym-lib-table').write_text(f'(sym_lib_table (version 7) (lib (name "{LIB}")(type "KiCad")(uri "${{KIPRJMOD}}/{LIB}.kicad_sym")(options "")(descr "Q4 exact package pins; reviewed custom symbols")))\n')
    mapping={}; rootitems=[]
    for index,(name,title,positions,note) in enumerate(PAGES,2):
        libs='\n'.join(definitions[ref].replace('(symbol '+q(ref),'(symbol '+q(LIB+':'+ref),1) for ref,_,_ in positions)
        flags = [('VBUS',80,275,1),('GND',185,275,2)] if name=='usb-power-1' else [('CELL_N_RAW',75,275,3),('BAT_SENSE',210,275,4)] if name=='battery-1' else [('VFRAM',300,275,5)] if name=='memory-1' else []
        if flags:
            libs+='\n'+FLAG.replace('(symbol "SupplyAssertion"',f'(symbol "{LIB}:SupplyAssertion"',1)
        content=[header(uid('file/'+name),title),'(lib_symbols '+libs+')',text(note,20,22,1.27)]
        for net,x,y,number in flags:
            content.append(supply_assertion(net,x,y,name,number))
        for ref,x,y in positions:
            symbol,record=place(parts[ref],x,y,name);content.append(symbol);mapping[ref]=record
        content.append(')')
        (OUT/(name+'.kicad_sch')).write_text('\n'.join(content)+'\n')
        x=14+((index-2)%3)*133; y=48+((index-2)//3)*37
        rootitems.append(f'''(sheet (at {x} {y}) (size 126 28) (stroke (width .254) (type solid))
          (fill (color 0 0 0 0)) (uuid "{uid('sheet/'+name)}")
          {prop('Sheetname',title,x+63,y-3.81,False,1.016)} {prop('Sheetfile',name+'.kicad_sch',x+63,y+31.81,False,1.016)}
          (instances (project "{PROJECT}" (path "/{ROOT_ID}" (page "{index}")))))''')
        rootitems.append(text(' / '.join(ref for ref,_,_ in positions),x+4,y+9,1.016))
    rootitems.insert(0,text(f'Q4 schematic index - {model["fitted_components"]} fitted PCB parts plus non-fitted test lands and mounts.\nGlobal net labels connect the functional sheets. Crosses explicitly mark unused physical pins.\nQ1 submitted files remain frozen. This candidate still requires ERC, layout, first-article and safety qualification.',20,20,1.27))
    (OUT/(PROJECT+'.kicad_sch')).write_text(header(ROOT_ID,'Count Fidget - Q4 engineering candidate')+'\n(lib_symbols)\n'+'\n'.join(rootitems)+'\n(sheet_instances (path "/" (page "1")))\n)\n')
    (OUT/'schematic-paths-Q4.json').write_text(json.dumps({'root_uuid':ROOT_ID,'namespace':str(NS),'parts':mapping},indent=2)+'\n')
    print('Generated native Q4 sheets, exact package pin symbols, and deterministic PCB/schematic paths.')
    if args.kicad_cli:
        validate(args.kicad_cli.resolve(),model,mapping)


def validate(cli,model,mapping):
    """Export native KiCad artifacts, then compare native nets to the intended model."""
    schematic='electronics/q4/'+PROJECT+'.kicad_sch'
    commands=[
        ['sch','export','netlist','--format','kicadxml','-o','electronics/q4/schematic-netlist-Q4.xml',schematic],
        ['sch','erc','--format','json','--severity-all','--exit-code-violations','-o','electronics/q4/erc-Q4.json',schematic],
        ['sch','export','pdf','-o','electronics/q4/schematic-Q4.pdf',schematic],
        ['sch','export','svg','-o','electronics/q4/schematic-svg/',schematic],
    ]
    # CLI instances share a macOS lock; keep these sequential even though exports are independent.
    for command in commands:
        subprocess.run([str(cli),*command],cwd=ROOT,check=True)
    xml=OUT/'schematic-netlist-Q4.xml'; native=ET.parse(xml); tree=native.getroot()
    # KiCad's source metadata exposes the local checkout path. Keep the public artifact portable.
    tree.find('design/source').text=schematic
    native.write(xml,encoding='utf-8',xml_declaration=True)
    parts={p['ref']:p for p in model['parts']}
    components={c.attrib['ref']:c for c in tree.find('components') if not c.attrib['ref'].startswith('#')}
    assert set(components)==set(parts), 'Native schematic component references differ from Q4 model'
    for ref,c in components.items():
        assert c.findtext('value')==parts[ref]['value'], 'Native value mismatch: '+ref
        assert c.findtext('footprint')==parts[ref]['footprint'], 'Native footprint mismatch: '+ref
        fields={f.attrib['name']:f.text for f in c.findall('fields/field')}
        assert fields['MPN']==parts[ref]['mpn'], 'Native MPN mismatch: '+ref
    actual={}
    for net in tree.find('nets'):
        for node in net.findall('node'):
            key=(node.attrib['ref'],node.attrib['pin'])
            assert key not in actual, 'Pin appears in multiple native nets'
            actual[key]=net.attrib['name']
    intended={(p['ref'],pin):net for p in parts.values() for pin,net in p['pins'].items()}
    for pair,net in intended.items():
        assert actual.get(pair)==net, 'Native connectivity mismatch: '+str(pair)
    unused=[(ref,pin) for ref,item in mapping.items() for pin,info in item['pins'].items() if info['net'] is None]
    for pair in unused:
        assert pair not in actual or actual[pair].startswith('unconnected-'), 'Unused pin connected: '+str(pair)
    nc_nets={pair:actual[pair] for pair in unused if pair in actual}
    assert len(nc_nets)==len(unused), 'Native export must identify every explicit NC physical pin'
    assert len(set(nc_nets.values()))==len(unused), 'Different physical NC pins share a native net'
    for pair,net in nc_nets.items():
        assert [other for other,value in actual.items() if value==net]==[pair], 'NC net joins another pin: '+str(pair)
    extra={pair:net for pair,net in actual.items() if pair[0] in parts and pair not in intended and pair not in unused}
    assert not extra, 'Unexpected physical pins: '+str(extra)
    erc=json.loads((OUT/'erc-Q4.json').read_text())
    violations=[v for sheet in erc['sheets'] for v in sheet.get('violations',[])]
    assert not violations, 'Native ERC has violations'
    files=[OUT/(PROJECT+'.kicad_sch'),*(OUT/(name+'.kicad_sch') for name,_,_,_ in PAGES),
           OUT/(LIB+'.kicad_sym'),OUT/'sym-lib-table',OUT/'schematic-paths-Q4.json',
           xml,OUT/'erc-Q4.json',OUT/'schematic-Q4.pdf',*sorted((OUT/'schematic-svg').glob('*.svg'))]
    inputs=[Path(__file__).resolve(),ROOT/'scripts/build_q4_model.py',OUT/'netlist-Q4.json']
    if (OUT/'placement.json').exists(): inputs.append(OUT/'placement.json')
    report={'status':'Native Q4 schematic candidate; not a hardware release','kicad_version':erc['kicad_version'],
            'sheets':len(erc['sheets']),'components_and_pcb_features':len(parts),'fitted_components':model['fitted_components'],
            'connected_pins_matched':len(intended),'explicit_unused_pins':len(unused),'erc_violations':len(violations),
            'nc_nets':{ref+'.'+pin:net for (ref,pin),net in nc_nets.items()},
            'erc_ignored_checks':erc['ignored_checks'],'commands':[['kicad-cli',*c] for c in commands],
            'supply_assertions':{'VBUS':'External USB source','GND':'System return via reviewed power topology',
                                 'CELL_N_RAW':'External cell return','BAT_SENSE':'Cell supply through R7','OLED_VBAT':'Regulated OLED_4V through Q5 switch'},
            'limitations':['ERC does not verify analog thresholds, startup, protection bypass or battery safety.',
                           'Supply assertions describe external/passive power paths; they are not extra fitted parts.',
                           'The drawing uses global labels between functional sheets; pin names/types are explicit.',
                           'All existing first-article, mechanical, firmware and purchase approval gates remain.'],
            'inputs_sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
            'artifacts_sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    (OUT/'schematic-validation-Q4.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS: {len(parts)} references, {len(intended)} connected pins, {len(unused)} explicit NC pins; ERC zero under recorded check configuration.')


if __name__=='__main__':
    main()
