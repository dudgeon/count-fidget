"""Create the Q3 two-layer OLED candidate without changing submitted revisions.

Identity/net changes are explicit here and in the reviewed power schedule.
Physical qualification and vendor process acceptance remain separate gates.
"""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'electronics/q3'
POWER = ROOT / 'procurement/q3/power-candidates.json'


def make_model():
    model = copy.deepcopy(json.loads((ROOT / 'electronics/q2/netlist-Q2.json').read_text()))
    power = json.loads(POWER.read_text())
    parts = {p['ref']: p for p in model['parts']}
    for ref in ('C8', 'C14', 'C15', 'C16'):
        del parts[ref]
    parts['DS1'] = {**power['display'], 'x':15.75, 'y':4.9, 'rotation':0,
                   'footprint':'CountFidgetQ3:X087-2832TSWIG02-H14',
                   'pins':{k:v for k,v in power['display']['pins'].items() if v is not None}}
    parts['DS1']['notes'] = ('Vendor localized FPC solder after SMT reflow; proposed planar XY lands, '
        'glass support and terminal Z transition require approval; do not reflow glass; '
        'no customer soldering; exact vendor process and first article pending')
    parts['U1']['pins'] = {k:v for k,v in parts['U1']['pins'].items()
                          if not v.startswith(('COM','SEG','LCD'))}
    parts['U1']['pins'].update(power['U1_pin_net_updates'])
    # Move the MCU below the switch row; all SMT now uses the bottom face.
    # TP locations are moved out of its body/pads. Native collision checks follow.
    positions = {
        'DS1':(15.75,5.5,0), 'H1':(2,38.2,0), 'H2':(40,38.2,0),
        'U1':(21,35,270), 'J1':(38.9,15.3,270), 'J2':(5,16.8,270),
        'U5':(16,5.5,0), 'R10':(11.8,2.8,90), 'C9':(21,5.3,90),
        'C6':(25.6,28.4,90), 'C7':(22.7,28.6,90),
        'R16':(13.1,33.95,90), 'C10':(13.1,37.3,90),
        'Q3':(20,22.5,0), 'Q4':(20,26.5,0),
        'R14':(16.5,23.45,180), 'R15':(16.5,27.45,180),
        'TP1':(3,23,0), 'TP2':(3,26,0), 'TP3':(3,29,0), 'TP4':(3,32,0),
        'TP5':(10,21.4,0), 'TP6':(15,14.5,0), 'TP7':(11.8,24,0), 'TP8':(13,31.1,0),
        'TP9':(9,31.7,0), 'TP10':(31,31.7,0),
        'U6':(21,11.5,0), 'L1':(24.4,10.9,90),
        'C17':(24.2,14.2,270), 'C18':(21,8.6,180), 'C19':(24,7.4,90),
        'R20':(15,10.5,0), 'R21':(15,12.4,0), 'R22':(18.3,9.2,90),
        'U3':(28.2,7,0), 'C5':(28.5,10.5,0),
        'U2':(32,11.3,0), 'C1':(32.1,8.1,0), 'C2':(28.6,13.4,270), 'C3':(32,14.1,0),
        'C13':(23.5,17,0), 'R19':(23.5,19,0),
        'Q5':(27.5,17,0), 'Q6':(31.8,17,180), 'R23':(27.5,20,0),
        'R24':(17.8,16.5,0), 'R25':(29,23.1,90),
        'R26':(29.2,37,90), 'R27':(32,37,90), 'R28':(33.7,2.1,0),
        'C20':(36.4,4.45,0), 'C21':(33.6,5.15,90),
        'C22':(36.5,1.9,90), 'C23':(39.3,1.85,90), 'C24':(39.3,5.1,90),
        'C25':(39.3,8.2,90), 'C26':(36.3,8.35,90), 'C27':(36.25,6.05,180),
        'R1':(31.8,19.9,0), 'R2':(36.9,26,0), 'R3':(29.4,2.1,0),
        'R4':(26.2,22.6,0), 'R5':(11.5,16.8,0), 'R6':(23,23.2,90),
        'R11':(12,18.8,0), 'R12':(15.3,18.8,0), 'R13':(18.6,18.8,0),
        'D1':(37.8,23,0),
    }

    for p in power['parts']:
        assert p['ref'] not in parts, 'Duplicate new reference '+p['ref']
        parts[p['ref']] = copy.deepcopy(p)
    # Exact alternatives checked against native JLC inventory on 2026-09-15.
    # Identity changes belong in the engineering model, not only the quote BOM.
    replacements = {
        'U5': ('TLV7012DGKR', 'Texas Instruments', 'C2859969'),
        'R3': ('0603WAF2402T5E', 'UNI-ROYAL', 'C23352'),
        'R9': ('0603WAF330KT5E', 'UNI-ROYAL', 'C22979'),
        'R11': ('0603WAF1153T5E', 'UNI-ROYAL', 'C22783'),
        'R16': ('0603WAF4702T5E', 'UNI-ROYAL', 'C25819'),
        'R23': ('0603WAF4702T5E', 'UNI-ROYAL', 'C25819'),
        'R17': ('0603WAF2203T5E', 'UNI-ROYAL', 'C22961'),
        'R18': ('0603WAF2203T5E', 'UNI-ROYAL', 'C22961'),
        'C13': ('GRM1885C1H472JA01D', 'Murata', 'C85980'),
    }
    for ref in ('C1','C3','C5'):
        replacements[ref] = ('GRM21BR71E225KE11L','Murata','C77081')
    for ref in ('C17','C18','C19'):
        replacements[ref] = ('CL21A226MAYNNNE','Samsung Electro-Mechanics','C602037')
    for ref in ('SW1','SW2'):
        replacements[ref] = ('CPG151101D13','HanElectricity','C49234235')
        parts[ref]['footprint'] = 'CountFidgetQ3:HanElectricity_CPG151101D13_MX_Plate'
        parts[ref]['notes'] = ('Click-tactile SPST, MX cross stem, plate mounted; vendor soldered; '
                              'exact manufacturer lands and enclosure retention require first-article fit')
    for ref,(mpn,maker,code) in replacements.items():
        parts[ref].update(mpn=mpn,manufacturer=maker,lcsc=code)
    for ref in ('R17','R18'):
        parts[ref]['value'] = '220k'
        parts[ref]['notes'] = '1%, 0603, 0.1 W; >=13.4 uA held-contact current at 2.97 V, above switch 10 uA minimum'
    parts['U5']['notes'] += '; TLV7012 same DGK pins/POR; USB-powered; conditional thermal error budget retained'
    parts['C13']['notes'] = ('4.7 nF, 50 V, C0G, 5%; same nominal TI EVM compensation '
                            'ISET -> 2k -> 4.7n -> GND; low-current stability still requires measurement')
    stock = json.loads((ROOT/'procurement/q3/live-stock-2026-09-15.json').read_text())
    codes = {p['mpn']:p['lcsc'] for p in stock['records']}
    for ref,p in parts.items():
        if not ref.startswith(('TP','H')):
            assert p['mpn'] in codes, 'Selected PCB MPN lacks live stock evidence: '+ref
            p['lcsc'] = codes[p['mpn']]
    parts['L1']['footprint'] = 'CountFidgetQ3:Inductor_SMD_L_Murata_DFE201612E_2.0x1.6mm'
    for ref,p in parts.items():
        if ref not in ('DS1','SW1','SW2','H1','H2'):
            p['side'] = 'bottom'
        if ref in positions:
            p['x'],p['y'],p['rotation'] = positions[ref]
        assert all(k in p for k in ('x','y','rotation','side')), ref
        fp = p['footprint']
        if not fp.startswith('CountFidgetQ3:'):
            p['source_footprint_Q3'] = fp
            lib,name = fp.split(':')
            if lib in ('ClickCounterQ2','ClickCounterQ3'):
                p['footprint'] = 'CountFidgetQ3:'+name
            else:
                p['footprint'] = 'CountFidgetQ3:'+lib+'_'+name
    model.update(revision='Q3 OLED two-layer engineering candidate — not released',
                 layers=2, source_baseline='Frozen coordinated Q2; submitted Q1/Q2 unchanged',
                 hardware_tested=False,manufacturing_released=False,
                 placement_status='Q3 trial positions; native routing/fit verification required',
                 parts=list(parts.values()))
    model['fitted_components'] = sum(not p['ref'].startswith(('TP','H')) for p in model['parts'])
    model['cost_intent'] = 'Two copper layers; bottom SMT reflow; separate vendor OLED and key soldering'
    return model


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    model = make_model()
    (OUT/'netlist-Q3.json').write_text(json.dumps(model,indent=2)+'\n')
    print('Created Q3 model:', model['fitted_components'], 'fitted parts; two-layer candidate only.')
