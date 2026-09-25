"""Adversarial corruption checks for Q3; never modifies engineering artifacts.

Default tests exercise independent contracts on deep copies. --full also first
requires a clean semantic baseline, then corrupts temporary PCB/XML copies to
exercise the complete model/schematic/PCB checker. Native DRC remains separate.
--bound additionally requires valid saved native evidence before attempting to
corrupt its hash bindings, command record and semantic/native summaries.
"""
import argparse
import copy
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import xml.etree.ElementTree as ET

import verify_q3 as v


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--full',action='store_true')
    parser.add_argument('--bound',action='store_true')
    args=parser.parse_args()
    passed=[]
    def rejects(name,call,expected):
        try: call()
        except ValueError as error:
            if expected not in str(error):
                raise AssertionError(name+' failed for the wrong reason: '+str(error)) from error
            passed.append(name)
        else: raise AssertionError(name+' was incorrectly accepted')
    model=v.make_model()
    v.verify_model_contract(model)
    comps,*_=v.xml_data(v.PUBLIC_XML)
    for ref,comp in comps.items():v.verify_physical_pins(ref,comp['pins'])
    rejects('Invented unused MCU pin',lambda:v.verify_physical_pins('U1',[str(n) for n in range(1,48)]+['99']),'physical pin identifiers')
    rejects('USB shield physical pad omitted',lambda:v.verify_physical_pins('J1',[p for p in comps['J1']['pins'] if p!='SH']),'physical pin identifiers')
    rejects('Duplicated physical OLED pin',lambda:v.verify_physical_pins('DS1',comps['DS1']['pins']+['6']),'physical pin identifiers')
    def model_corruption(name,mutate,expected):
        candidate=copy.deepcopy(model)
        mutate(candidate,{p['ref']:p for p in candidate['parts']})
        rejects(name,lambda:v.verify_model_contract(candidate),expected)
    model_corruption('Missing PMOS isolation',lambda m,p:m['parts'].remove(p['Q5']),'reference set')
    model_corruption('Missing 4V bulk capacitor',lambda m,p:m['parts'].remove(p['C19']),'reference set')
    model_corruption('Wrong two-layer stack',lambda m,p:m.update(layers=4),'two-layer')
    model_corruption('Wrong MCU enable pin',lambda m,p:p['U1']['pins'].update({'24':'OLED_RESET_N'}),'pin topology')
    model_corruption('Wrong I2C pin mapping',lambda m,p:p['U1']['pins'].update({'28':'OLED_SCL','27':'OLED_SDA'}),'pin topology')
    model_corruption('OLED pin6 incorrectly grounded',lambda m,p:p['DS1']['pins'].update({'6':'GND'}),'pin topology')
    model_corruption('OLED switched VDD',lambda m,p:p['DS1']['pins'].update({'8':'OLED_VBAT'}),'pin topology')
    model_corruption('OLED VBAT directly on SYS',lambda m,p:p['DS1']['pins'].update({'5':'SYS'}),'pin topology')
    model_corruption('PMOS body diode reversed',lambda m,p:p['Q5']['pins'].update({'2':'OLED_VBAT','3':'OLED_4V'}),'pin topology')
    model_corruption('Converter switch pin miswired',lambda m,p:p['U6']['pins'].update({'9':'SYS'}),'pin topology')
    model_corruption('IREF made ten times larger',lambda m,p:p['R28'].update(value='75k'),'component value')
    model_corruption('Pump setting changed',lambda m,p:p['R20'].update(value='5.1k'),'component value')
    model_corruption('I2C pullup on pump rail',lambda m,p:p['R26']['pins'].update({'1':'OLED_4V'}),'pin topology')
    model_corruption('OLED exact part replaced',lambda m,p:p['DS1'].update(mpn='SSD1306-module'),'exact component')
    model_corruption('Wrong capacitor stock code',lambda m,p:p['C17'].update(lcsc='C123'),'exact component')
    model_corruption('Old LCD net reintroduced',lambda m,p:p['U1']['pins'].update({'1':'SEG0'}),'pin topology')
    model_corruption('OLED wrong assembly side',lambda m,p:p['DS1'].update(side='bottom'),'assembly side')
    stock=json.loads((v.ROOT/'procurement/q3/live-stock-2026-09-15.json').read_text())
    parts={p['ref']:p for p in model['parts']}
    for label,mutate,expected in [
        ('Missing recorded part',lambda s:s['records'].clear(),'evidence missing'),
        ('Ambiguous recorded identity',lambda s:s['records'].append(copy.deepcopy(s['records'][0])),'ambiguous'),
        ('No recorded stock',lambda s:s['records'][0].update(stock=0),'positive integer'),
        ('Unattributed sourcing evidence',lambda s:s['records'][0].update(source='https://example.com'),'provenance')]:
        candidate=copy.deepcopy(stock);mutate(candidate)
        rejects(label,lambda:v.verify_stock(parts,candidate),expected)
    board=v.parse(v.BOARD.read_text())
    fps={v.property_value(f,'Reference'):f for f in v.children(board,'footprint')}
    def footprint_corruption(name,ref,verify,mutate,expected):
        candidate=copy.deepcopy(fps[ref]);mutate(candidate)
        rejects(name,lambda:verify(candidate),expected)
    oled=lambda f:v.verify_oled_lands(f,True)
    inductor=lambda f:v.verify_inductor(f,True)
    oled(fps['DS1']);inductor(fps['L1']);v.verify_converter_lands(fps['U6']);v.verify_switch_lands(fps['SW2'])
    footprint_corruption('OLED omitted terminal','DS1',oled,lambda f:f.remove(v.children(f,'pad')[0]),'14 distinct')
    footprint_corruption('OLED wrong land length','DS1',oled,lambda f:v.child(v.children(f,'pad')[0],'size').__setitem__(1,'2.0'),'land length')
    footprint_corruption('OLED wrong pitch','DS1',oled,lambda f:v.child(v.children(f,'pad')[1],'at').__setitem__(2,'3.40'),'number/pitch')
    footprint_corruption('OLED old local pad origin','DS1',oled,lambda f:v.child(v.children(f,'pad')[0],'at').__setitem__(1,'0'),'local X')
    footprint_corruption('OLED stencil paste added','DS1',oled,lambda f:v.child(v.children(f,'pad')[0],'layers').append('F.Paste'),'no-paste')
    footprint_corruption('OLED land numbering reversed','DS1',oled,lambda f:(v.children(f,'pad')[0].__setitem__(1,'14'),v.children(f,'pad')[-1].__setitem__(1,'1')),'number/pitch')
    footprint_corruption('Murata omitted rule area','L1',inductor,lambda f:f.remove(v.children(f,'zone')[0]),'both embedded')
    footprint_corruption('Murata inner copper allowed','L1',inductor,lambda f:v.child(v.child(v.children(f,'zone')[0],'keepout'),'tracks').__setitem__(1,'allowed'),'permissions')
    footprint_corruption('Murata keepout lost on flip','L1',inductor,lambda f:v.child(v.children(f,'zone')[0],'layer').__setitem__(1,'F.Cu'),'footprint flip')
    footprint_corruption('Murata keepout moved','L1',inductor,lambda f:v.children(v.child(v.child(v.children(f,'zone')[0],'polygon'),'pts'),'xy')[0].__setitem__(1,'0'),'geometry/transform')
    footprint_corruption('Converter EP omitted','U6',v.verify_converter_lands,lambda f:f.remove([p for p in v.children(f,'pad') if p[1]=='11'][0]),'10 leads')
    footprint_corruption('Converter lead mapping changed','U6',v.verify_converter_lands,lambda f:v.child(next(p for p in v.children(f,'pad') if p[1]=='1'),'at').__setitem__(2,'-1'),'numbered land Y')
    footprint_corruption('Switch incorrect finished hole','SW2',v.verify_switch_lands,lambda f:v.child(v.children(f,'pad')[0],'drill').__setitem__(1,'4.1'),'finished hole')
    candidate=copy.deepcopy(board)
    v.child(candidate,'layers').append(['2','In1.Cu','power'])
    rejects('Hidden inner copper layer',lambda:v.verify_two_layer_copper(candidate,{}),'inner copper')
    candidate=copy.deepcopy(board);candidate.append(['segment',['layer','In1.Cu']])
    rejects('Trace references obsolete inner layer',lambda:v.verify_two_layer_copper(candidate,{}),'inner layer')
    candidate=copy.deepcopy(board);candidate.append(['segment',['layer','F.Cu'],['net','LCDCAP']])
    rejects('Obsolete LCD copper retained',lambda:v.verify_two_layer_copper(candidate,{}),'LCD net carries copper')
    with tempfile.TemporaryDirectory(prefix='q3-negative-',dir='/private/tmp') as directory:
        directory=Path(directory)
        fixture={'$schema':'https://schemas.kicad.org/drc.v1.json','included_severities':['error','warning','exclusion'],
                 'ignored_checks':[],'kicad_version':'10.0.6','source':v.BOARD.name,'date':'test fixture, not a native run',
                 'violations':[],'unconnected_items':[],'schematic_parity':[]}
        def report_corruption(label,mutate,expected):
            candidate=copy.deepcopy(fixture);mutate(candidate)
            path=directory/'negative-drc.json';path.write_text(json.dumps(candidate))
            rejects(label,lambda:v.report_checks(path,'drc'),expected)
        report_corruption('Unrouted connection',lambda d:d['unconnected_items'].append({}),'not zero')
        report_corruption('Schematic parity mismatch',lambda d:d['schematic_parity'].append({}),'not zero')
        report_corruption('Copper short',lambda d:d['violations'].append({'type':'shorting_items','severity':'error'}),'Unapproved')
        report_corruption('Silently ignored clearance',lambda d:d['ignored_checks'].append({'key':'clearance'}),'silently ignores')
        report_corruption('Warnings omitted',lambda d:d.update(included_severities=['error','exclusion']),'all severities')
        report_corruption('Different board native report',lambda d:d.update(source='other.kicad_pcb'),'source board')
        exception={'type':'pth_inside_courtyard','severity':'error','description':'PTH inside courtyard','items':[
            {'uuid':v.J1_SHELL_PAD_UUID,'description':'PTH pad SH [GND] of J1','pos':{'x':35.795,'y':19.62}},
            {'uuid':v.SW2_FOOTPRINT_UUID,'description':'Footprint SW2','pos':{'x':33.065,'y':22.92}}]}
        v.courtyard_exception(exception,board)
        wrong=copy.deepcopy(exception);wrong['items'][0]['uuid']='different-pad'
        rejects('Courtyard exception broadened to another pad',lambda:v.courtyard_exception(wrong,board),'exact J1')
        wrong=copy.deepcopy(exception);wrong['items'][0]['pos']['y']+=1
        rejects('Courtyard exception stale geometry',lambda:v.courtyard_exception(wrong,board),'native item Y')
        if args.full:
            # A successful unchanged baseline prevents unrelated staleness from
            # masquerading as successful corruption detection.
            v.verify_semantics()
            text=v.BOARD.read_text()
            def write_sexpr(node):
                if isinstance(node,list):return '('+' '.join(map(write_sexpr,node))+')'
                return json.dumps(node)
            def full_board(label,mutate,expected):
                candidate=v.parse(text);mutate(candidate)
                path=directory/'corrupt.kicad_pcb';path.write_text(write_sexpr(candidate))
                with patch.object(v,'BOARD',path):rejects(label,v.verify_semantics,expected)
            def byref(b,ref):return next(f for f in v.children(b,'footprint') if v.property_value(f,'Reference')==ref)
            full_board('Full parity: missing PCB regulator',lambda b:b.remove(byref(b,'U6')),'reference sets')
            full_board('Full parity: OLED pad net changed',lambda b:v.child(v.children(byref(b,'DS1'),'pad')[0],'net').__setitem__(-1,'GND'),'pad net differs')
            full_board('Full parity: component moved',lambda b:v.child(byref(b,'R20'),'at').__setitem__(1,'0'),'R20 x')
            full_board('Full parity: duplicate footprint UUID',lambda b:v.child(byref(b,'R20'),'uuid').__setitem__(1,v.child(byref(b,'R21'),'uuid')[1]),'Duplicate native PCB UUID')
            full_board('Full parity: no traces',lambda b:b.__setitem__(slice(None),[x for x in b if not isinstance(x,list) or x[0]!='segment']),'routed board')
            full_board('Full parity: no ground zones',lambda b:b.__setitem__(slice(None),[x for x in b if not isinstance(x,list) or x[0]!='zone']),'routed board')
            def full_xml(label,mutate,expected):
                xml=ET.parse(v.PUBLIC_XML);mutate(xml.getroot())
                path=directory/'corrupt.xml';xml.write(path)
                rejects(label,lambda:v.verify_semantics(path),expected)
            full_xml('Full parity: schematic reference omitted',lambda x:x.find('components').remove(x.find("components/comp[@ref='Q5']")),'reference sets')
            full_xml('Full parity: schematic MPN corrupted',lambda x:x.find("components/comp[@ref='DS1']/fields/field[@name='MPN']").__setattr__('text','DE188'),'mpn differs')
            full_xml('Full parity: connected pin omitted',lambda x:next(n for n in x.findall('nets/net') if n.find("node[@ref='U6'][@pin='6']") is not None).remove(x.find("nets/net/node[@ref='U6'][@pin='6']")),'Missing exported physical pin')
        if args.bound:
            baseline=v.saved()
            def bound_report(label,mutate,expected):
                report=copy.deepcopy(baseline);mutate(report)
                path=directory/'corrupt-validation.json';path.write_text(json.dumps(report))
                with patch.object(v,'REPORT',path):rejects(label,v.saved,expected)
            bound_report('Native binding: input hash corrupted',lambda r:r['inputs_sha256'].__setitem__('electronics/q3/netlist-Q3.json','0'*64),'reports are stale')
            bound_report('Native binding: report hash corrupted',lambda r:r['reports_sha256'].__setitem__('verification/q3-native-drc.json','0'*64),'report content changed')
            bound_report('Native binding: parity check omitted',lambda r:r['commands'][2].remove('--schematic-parity'),'commands do not match')
            bound_report('Native binding: semantic summary corrupted',lambda r:r['semantic_checks'].update(connected_physical_pins=217),'Semantic checks no longer')
            bound_report('Native binding: exception hidden',lambda r:r['native_checks']['drc'].update(explicit_engineering_exceptions=[{'fabricated':True}]),'Native check summaries differ')
    print(json.dumps({'status':'PASS','negative_corruptions_rejected':len(passed),'full_semantic_integration':args.full,
                      'bound_native_evidence_checked':args.bound,'checks':passed,'fresh_native_checks_run_by_this_test':False},indent=2))


if __name__=='__main__':main()
