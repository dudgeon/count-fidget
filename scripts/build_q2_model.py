"""Create a separate, unreleased Q2 connectivity model from the frozen Q1 model.

Does not edit Q1 or run its archived board/RFQ generators. The resulting model is
an engineering candidate; schematic, layout and measurements must be verified.
"""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'electronics/q2'


def make_model():
    model = copy.deepcopy(json.loads((ROOT / 'electronics/netlist.json').read_text()))
    parts = {p['ref']: p for p in model['parts']}
    model['revision'] = 'Q2 engineering candidate — not released'
    model['source_baseline'] = 'Q1; all original files preserved'
    model['hardware_tested'] = False
    model['manufacturing_released'] = False
    # Preserve the eight-digit low-power baseline while fixing its known drive
    # and nominal mechanical errors. No qualified alternate solves JLC sourcing.
    parts['DS1']['footprint'] = 'ClickCounterQ2:DE188_20P_rows13.0mm'
    parts['DS1']['notes'] += '; Q2 nominal lead rows 13.0 mm; retained 1.7 mm drills pending assembler/tolerance review'
    parts['U1']['pins'].update({'7': 'LCD_R13', '8': 'LCD_R23', '9': 'LCD_R33'})
    for ref, net, x in [('C14', 'LCD_R13', 17.8), ('C15', 'LCD_R23', 19.4), ('C16', 'LCD_R33', 21)]:
        p = copy.deepcopy(parts['C7'])
        p.update(ref=ref, x=x, y=12.5, rotation=270, side='bottom',
                 pins={'1': net, '2': 'GND'},
                 notes='Required LCD Mode-2 bias reservoir; 100 nF X7R; place near corresponding U1 bias pin')
        parts[ref] = p
    # Current orderable variant. Functional output-discharge feature is explicit.
    parts['U3'].update(mpn='TPS7A0230PDBVR', notes='3.0 V; active output discharge variant; EN tied to SYS; power-fall/FRAM validation required')
    # MCU DVCC bulk recommendation is 4.7 uF minimum, 10 uF nominal. Keep the
    # existing 0805 land and use the already specified 10 uF SYS capacitor type.
    parts['C6'].update(value=parts['C2']['value'], mpn=parts['C2']['mpn'],
        notes='10 uF 25 V X5R, nominal +/-10%; MCU V3 bulk correction E19; require >=4.7 uF effective at 3 V after bias/temperature/tolerance; rail startup and reverse-current qualification required')
    # Independent comparator outputs operate two series enable FETs. No output
    # pull-up can enable charging after comparator supply loss.
    parts['U5'].update(mpn='TLV7032DGKR', value='Push-pull temperature window',
        footprint='ClickCounterQ2:TLV7032_DGK0008A_TI',
        pins={'1':'TEMP_COLD_OK','2':'TEMP_SENSE','3':'TEMP_COLD','4':'GND',
              '5':'TEMP_SENSE','6':'TEMP_HOT','7':'TEMP_HOT_OK','8':'VBUS'},
        notes='Separate push-pull outputs; charge enable requires both in-window indications; POR/supply-loss tests required')
    parts['Q3'].update(pins={'1':'TEMP_COLD_OK','2':'CE_MID','3':'CE_N'}, x=21, y=24.5,
                       mpn='2N7002,215', notes='Upper series charge-enable N-MOSFET; gate has ground pulldown')
    q4 = copy.deepcopy(parts['Q3'])
    q4.update(ref='Q4', value='Charge enable hot gate', x=21, y=28.5,
              pins={'1':'TEMP_HOT_OK','2':'GND','3':'CE_MID'},
              notes='Lower series charge-enable N-MOSFET; gate has ground pulldown')
    parts['Q4'] = q4
    for ref, value, code in [('R10','57.6k','57K6'),('R11','115k','115K'),('R12','24.3k','24K3'),('R13','16.2k','16K2'),('R14','100k','100K'),('R15','100k','100K')]:
        parts[ref].update(value=value, mpn='RC0603FR-07'+code+'L')
    parts['R14']['pins'] = {'1':'TEMP_COLD_OK','2':'GND'}
    parts['R15']['pins'] = {'1':'TEMP_HOT_OK','2':'GND'}
    parts['R14'].update(x=17.5, y=25.45, rotation=180,
        notes='Local upper charge-enable gate pulldown; keep connected close to Q3 gate')
    parts['R15'].update(x=17.5, y=29.6, rotation=180,
        notes='Local lower charge-enable gate pulldown; keep connected close to Q4 gate')
    parts['R16'].update(x=23.5, y=9.8, rotation=0)
    parts['C7'].update(x=22.6, y=12.5, rotation=270,
        notes='100 nF MCU decoupler beside U1 DVCC/DVSS; short via connections required')
    parts['C8'].update(x=20, y=9.6, rotation=0,
        notes='LCD charge-pump capacitor; short direct routing to U1 LCDCAP1/0')
    parts['C9'].update(x=21.1, y=7.3, rotation=90, notes='100 nF local VBUS decoupler beside U5; nearby plane return')
    parts['C10'].update(x=26.2)
    # Q1 deliberately stripped silkscreen from its embedded library footprints.
    # Preserve that geometry as an explicit project library, with provenance,
    # rather than pretending the modified footprints equal today's stock library.
    for part in parts.values():
        if not part['footprint'].startswith('ClickCounterQ2:'):
            part['source_footprint'] = part['footprint']
            lib, name = part['footprint'].split(':')
            part['footprint'] = 'ClickCounterQ2:' + lib + '_' + name
    # Final placement is a separate, verified layout operation.
    model['parts'] = list(parts.values())
    model['fitted_components'] = sum(not p['ref'].startswith(('TP','H')) for p in model['parts'])
    model['placement_status'] = 'Q2 design positions; native board and CPL must match and pass DRC'
    assert model['fitted_components'] == 50
    return model


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'netlist-Q2.json').write_text(json.dumps(make_model(), indent=2) + '\n')
    print('Created separate 50-component Q2 connectivity candidate; no Q1 files changed.')
