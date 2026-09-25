"""Build the separate Q4 circuit candidate from the immutable Q3 JSON.

This is an engineering model, not manufacture authorization.  Explicit gates in
the model and q4-power-design.md remain required even after native ERC/DRC.
Root-owned placement.json may override only physical placement fields.
"""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'electronics/q4'
BASE = ROOT / 'electronics/q3/netlist-Q3.json'


def pinmeta(names, kinds=None):
    kinds = kinds or {}
    return {str(i): {'name': n, 'type': kinds.get(str(i), 'bidirectional')}
            for i, n in enumerate(names, 1)}


MCU_NAMES = ('VDD PC13 PC14 PC15 PH0 PH1 NRST VSSA VDDA PA0 PA1 PA2 PA3 '
             'PA4 PA5 PA6 PA7 PB0 PB1 PB2 PB10 PB11 VSS VDD PB12 PB13 PB14 '
             'PB15 PA8 PA9 PA10 PA11 PA12 PA13 VSS VDD_USB PA14 PA15 PB3 '
             'PB4 PB5 PB6 PB7 BOOT0 PB8 PB9 VSS VDD').split()
MCU_PINS = pinmeta(MCU_NAMES, {
    **{str(i): 'power_in' for i in (1,8,9,23,24,35,36,47,48)},
    '7': 'input', '44': 'input'})
SWITCH_PINS = pinmeta(['VIN','GND','ON','CT','QOD','VOUT'],
    {'1':'power_in','2':'power_in','3':'input','4':'passive','5':'passive','6':'power_out'})


def make_model():
    model = copy.deepcopy(json.loads(BASE.read_text()))
    parts = {p['ref']: p for p in model['parts']}
    # Complete module replaces the bare panel and its external charge-pump path.
    removed = ('L1','Q5','Q6','R20','R21','R22','R23','R26','R27','R28',
               'C17','C18','C19','C21','C22','C23','C24','C25','C26','C27')
    for ref in removed:
        del parts[ref]
    for p in parts.values():
        p['pins'] = {k: ('VLOGIC' if v == 'V3' else v) for k,v in p['pins'].items()}
        p['footprint'] = p['footprint'].replace('CountFidgetQ3:', 'CountFidgetQ4:')

    def add(ref, value, mpn, maker, footprint, pins, notes='', lcsc=None,
            sheet='mcu', x=21, y=35, side='bottom', symbol_pins=None):
        p = dict(ref=ref, value=value, mpn=mpn, manufacturer=maker,
                 footprint='CountFidgetQ4:'+footprint, pins=pins, notes=notes,
                 x=x, y=y, rotation=0, side=side, sheet=sheet)
        if lcsc: p['lcsc'] = lcsc
        if symbol_pins: p['symbol_pins'] = copy.deepcopy(symbol_pins)
        parts[ref] = p
        return p

    def clone(ref, template, pins, sheet, notes=None):
        p = copy.deepcopy(parts[template]); p.update(ref=ref, pins=pins, sheet=sheet)
        if notes is not None: p['notes'] = notes
        parts[ref] = p
        return p

    add('U1','STM32L072CBT6','STM32L072CBT6','STMicroelectronics',
        'Package_QFP_LQFP-48_7x7mm_P0.5mm',
        {'1':'VLOGIC','7':'NRST','8':'GND','9':'VLOGIC','10':'COUNT_N',
         '11':'BOOT_COUNT_RESET','18':'OLED_RESET_N','19':'OLED_ENABLE',
         '23':'GND','24':'VLOGIC','25':'OLED_CS_N','26':'OLED_SCK',
         '27':'OLED_DC','28':'OLED_MOSI',
         '32':'USB_DM','33':'USB_DP','34':'SWDIO','35':'GND','36':'VLOGIC',
         '37':'SWCLK','39':'FRAM_SCK','40':'FRAM_MISO','41':'FRAM_MOSI',
         '44':'BOOT_COUNT_RESET','45':'FRAM_CS_N','47':'GND','48':'VLOGIC'},
        'LQFP48; all supply domains common; ROM USB DFU with BOOT0/nBOOT1; '
        'PA2/PA3/PA9/PA10 forbidden for load-enable or memory-CS controls. '
        'Unused physical pins explicitly NC. All connected GPIO modes are firmware contract.',
        'C465977', symbol_pins=MCU_PINS)
    add('DS1','SPI OLED module 128x64','HS96L01W4S03','HS',
        'HS96L01W4S03_Module_7Pin',
        {'1':'GND','2':'OLED_SUPPLY','3':'OLED_SCK','4':'OLED_MOSI',
         '5':'OLED_RESET_N','6':'OLED_DC','7':'OLED_CS_N'},
        'Drawing controls: PCB27.30x27.80mm, SSD1315, supplied 4-wire SPI. External supply rated3–5V; '
        'logic inputs<=3.3V. Exact header height/internal capacitance/current and '
        'assembly mounting remain first-article gates; no custom glass/FPC soldering.',
        'C5139758', sheet='display', x=21, y=16.7, side='top',
        symbol_pins=pinmeta(['GND','VCC','SCL/SCK','SDA/MOSI','RES#','D/C#','CS#'],
            {'1':'power_in','2':'power_in', **{str(i):'input' for i in range(3,8)}}))
    add('U3','3.20481V adjustable LDO','TLV76701DRVR','Texas Instruments',
        'Package_SON_WSON-6-1EP_2x2mm_P0.65mm_EP1x1.6mm',
        {'1':'VLOGIC','2':'VLOGIC_FB','3':'GND','4':'SYS_LOAD','5':'GND','6':'SYS_LOAD','7':'GND'},
        'Shared MCU/USB/display-logic rail; 150k/49.9k 0.1%25ppm feedback. '
        'Transient, feedback-bias, effective-capacitance and reverse-current bounds '
        'must be validated; this is not a guaranteed end-to-end rail proof.',
        'C2863998', sheet='usb-power', x=28.2, y=7,
        symbol_pins=pinmeta(['OUT','FB','GND','EN','GND','IN','EP'],
            {'1':'power_out','2':'input','3':'power_in','4':'input','5':'power_in','6':'power_in','7':'power_in'}))
    add('U6','OLED power slew switch','TPS22917DBVR','Texas Instruments',
        'Package_TO_SOT_SMD_SOT-23-6',
        {'1':'VLOGIC','2':'GND','3':'OLED_ENABLE','4':'OLED_CT','5':'OLED_SUPPLY','6':'OLED_SUPPLY'},
        'CT capacitor connects to VIN, not GND. QOD connected to OUT. '
        'Module fully off during ROM DFU; all five display signal pins high impedance '
        'before removing power. Slew is typical-only, not a safety current limit.',
        'C2681320', sheet='display', x=21, y=11.5, symbol_pins=SWITCH_PINS)
    add('U7','System startup slew switch','TPS22917DBVR','Texas Instruments',
        'Package_TO_SOT_SMD_SOT-23-6',
        {'1':'SYS','2':'GND','3':'SYS','4':'SYS_CT','6':'SYS_LOAD'},
        'Always-enabled downstream startup slew; QOD explicitly NC. '
        'Does not limit mandatory upstream charger SYS/BAT capacitors. '
        'Battery insertion remains unqualified; do not label this as complete protection proof.',
        'C2681320', sheet='usb-power', x=26, y=15, symbol_pins=SWITCH_PINS)
    # Exact chip has a broad 2.0–3.6V range. Its isolated RC supply and open-drain
    # chip select are deliberate; memory is not on the switched display rail.
    add('U8','SPI F-RAM 32KiB','FM25V02A-GTR','Infineon',
        'Package_SO_SOIC-8_3.9x4.9mm_P1.27mm',
        {'1':'FRAM_CS_N','2':'FRAM_MISO','3':'VFRAM','4':'GND',
         '5':'FRAM_MOSI','6':'FRAM_SCK','7':'VFRAM','8':'VFRAM'},
        'Dedicated SPI1; /WP and /HOLD high. CS pull-up to VFRAM, MCU open-drain. '
        'Sleep B9 before Stop; wake guard>=400us. RC bound conditional on >=6.8uF effective; never waive '
        '50us/V rising and100us/V falling at any point.',
        'C66029', sheet='memory', x=21, y=25,
        symbol_pins=pinmeta(['CS#','SO','WP#','VSS','SI','SCK','HOLD#','VDD'],
            {'1':'input','2':'tri_state','3':'input','4':'power_in',
             '5':'input','6':'input','7':'input','8':'power_in'}))
    parts['J1'].update(value='USB-C power and DFU', mpn='USB4105-GF-A-120', lcsc='C5184243')
    parts['J1']['pins'].update(A6='USB_DP', B6='USB_DP', A7='USB_DM', B7='USB_DM')
    parts['J1']['notes'] = ('1.20+/-0.15mm shell-stake suffix on1mmPCB; nominal0.20mm protrusion; joint/fillet and tolerance inspection required. '
                           'USB FS differential routing, shield and ESD validation required.')
    for r in ('Q1','Q2'):
        parts[r].update(mpn='DMN2056U-13', lcsc='C5208862')
        parts[r]['notes'] += '; exact same-device reel suffix -13; no electrical polarity change'
    parts['R13'].update(mpn='0603WAF1622T5E', manufacturer='UNI-ROYAL', lcsc='C22885')
    # Reset-count becomes active high and doubles as BOOT0. NRST remains separate.
    parts['SW2'].update(value='RESET COUNT / BOOT', pins={'1':'BOOT_COUNT_RESET','2':'VLOGIC'})
    parts['R18'].update(value='100k',mpn=parts['R6']['mpn'],lcsc=parts['R6']['lcsc'],
                        pins={'1':'BOOT_COUNT_RESET','2':'GND'})
    parts['C12']['pins'] = {'1':'BOOT_COUNT_RESET','2':'GND'}
    parts['R16'].update(value='10k',mpn=parts['R5']['mpn'],lcsc=parts['R5']['lcsc'],
                        pins={'1':'VLOGIC','2':'NRST'})
    parts['C10'] = copy.deepcopy(parts['C7'])
    parts['C10'].update(ref='C10',pins={'1':'NRST','2':'GND'},notes='100nF NRST bypass; recovery switch/test pad access required')
    add('SW3','MCU RESET','TS-1088-AR02016','XUNPU',
        'XUNPU_TS-1088-AR02016_SMD',{'1':'NRST','2':'GND'},
        'Normally-open two-terminal pinhole recovery button; hold SW2 during reset for ROM DFU.',
        'C720477',sheet='mcu',symbol_pins=pinmeta(['1','2'],{'1':'passive','2':'passive'}))
    clone('TP11','TP1',{'1':'NRST'},'mcu','NRST recovery contact; short to adjacent GND contact to reset')
    clone('TP12','TP1',{'1':'BOOT_COUNT_RESET'},'mcu','BOOT0/count-reset high contact; SW2 supplies VLOGIC')
    parts['TP11']['value']='NRST'
    parts['TP12']['value']='BOOT_COUNT_RESET'
    for r, net in (('TP2','VLOGIC'),('TP3','SWDIO'),('TP4','SWCLK'),('TP10','BOOT_COUNT_RESET')):
        parts[r].update(value=net,pins={'1':net})
    parts['C5']['pins'] = {'1':'SYS_LOAD','2':'GND'}
    parts['C6']['notes'] = ('10uF package rail bulk; include all MCU/FRAM/module capacitance '
                           'in regulator stability and startup review; effective capacitance unmeasured')
    parts['R25']['pins'] = {'1':'OLED_RESET_N','2':'GND'}
    clone('R29','R6',{'1':'OLED_SUPPLY','2':'OLED_CS_N'},'display','100k CS pull-up to switched module supply; never to always-on rail')
    add('R30','150k','RT0603BRD07150KL','Yageo','Resistor_SMD_R_0603_1608Metric',
        {'1':'VLOGIC','2':'VLOGIC_FB'},'0.1%,25ppm/C; feedback upper resistor','C326734',sheet='usb-power',x=30,y=5)
    add('R31','49.9k','RT0603BRD0749K9L','Yageo','Resistor_SMD_R_0603_1608Metric',
        {'1':'VLOGIC_FB','2':'GND'},'0.1%,25ppm/C; feedback lower resistor',
        'C705780',sheet='usb-power',x=30,y=7)
    add('R32','68','0603WAF680JT5E','UNI-ROYAL','Resistor_SMD_R_0603_1608Metric',
        {'1':'VLOGIC','2':'VFRAM'},'1%; controlled memory rail RC','C27592',sheet='memory',x=18,y=25)
    clone('R33','R6',{'1':'VFRAM','2':'FRAM_CS_N'},'memory','100k external pull-up; MCU CS must be open-drain')
    for ref, a, b in (('C28','VLOGIC','OLED_CT'),('C29','SYS','SYS_CT')):
        add(ref,'22n','GRM188R71H223KA01D','Murata','Capacitor_SMD_C_0603_1608Metric',
            {'1':a,'2':b},'22nF50V X7R; slew timing capacitor to VIN; typical slew only','C77056',
            sheet='display' if ref=='C28' else 'usb-power')
    clone('C30','C6',{'1':'VFRAM','2':'GND'},'memory','10uF25V X5R; require>=6.8uF effective for proposed memory ramp budget')
    for r in ('C31','C32','C33','C34','C35'):
        clone(r,'C7',{'1':'VLOGIC','2':'GND'},'mcu','100nF local STM32 supply bypass; one per VDD/VDDA/USB supply group')
    clone('C36','C7',{'1':'VFRAM','2':'GND'},'memory','100nF local FRAM bypass, in addition to C30')
    for r in ('C38','C39'):
        clone(r,'C7',{'1':'VBUS','2':'GND'},'usb-power','100nF local USBLC6 clamp-rail bypass, adjacent to D1/D2')
    clone('D2','D1',{'1':'USB_DM','2':'GND','3':'USB_DP','4':'USB_DP','5':'VBUS','6':'USB_DM'},'usb-power','USB FS data ESD; exact routing and system ESD tests required')
    parts['D2']['symbol_pins'] = pinmeta(['I/O1','GND','I/O2','I/O2','VBUS','I/O1'],
        {'1':'passive','2':'power_in','3':'passive','4':'passive','5':'power_in','6':'passive'})
    for p in parts.values():
        if 'sheet' not in p:
            r=p['ref']
            p['sheet'] = ('thermal' if r in ('U5','Q3','Q4','R10','R11','R12','R13','R14','R15','C9')
                          else 'battery' if r in ('U4','Q1','Q2','J2','R7','R8','R9','C4')
                          else 'usb-power' if r in ('U2','J1','D1','R1','R2','R3','R4','R5','R6','R19','C1','C2','C3','C5','C13')
                          else 'display' if r in ('DS1','R24','R25','C20') else 'mcu')
    for ref, template, x in (('H3','H1',2.5),('H4','H2',39.5)):
        clone(ref,template,{},'mcu','Front M2 clearance2.2mm NPTH; PCB support and separately removable OLED cover')
        parts[ref].update(x=x,y=2.5,rotation=0,side='top')
    for ref in ('SW1','SW2'):
        parts[ref]['notes'] = ('Exact clicky switch; home through-hole soldering after rear key plate is fitted. '
                               'Verify body/plate/lead fit before soldering; vendor SMT assembly excludes this part.')
    for p in parts.values():
        p['assembly'] = ('pcb_feature' if p['ref'].startswith(('TP','H')) else
                         'home_through_hole' if p['ref'] in ('DS1','SW1','SW2') else 'jlc_smt')
    overrides_path = OUT/'placement.json'
    if overrides_path.exists():
        overrides=json.loads(overrides_path.read_text())
        for ref, placement in overrides.items():
            if ref not in parts: raise ValueError('Unknown placement reference: '+ref)
            if set(placement)-{'x','y','rotation','side'}:
                raise ValueError('Placement override may not change circuit: '+ref)
            parts[ref].update(placement)
    model.update(revision='Q4 STM32 SPI module engineering candidate - NOT RELEASED',
        source_baseline='Frozen Q3 JSON; Q1/Q2/Q3 artifacts unchanged',
        source_baseline_sha256=hashlib.sha256(BASE.read_bytes()).hexdigest(),
        board_mm=[42,54,1], layers=2, hardware_tested=False, manufacturing_released=False,
        placement_status='Unrouted circuit model; root-owned placement overrides; module may require larger outline',
        cost_intent='Complete SPI module, home ROM USB DFU, retained SWD, simple common rail',
        parts=list(parts.values()))
    model['symbol_pins']={r:copy.deepcopy(p['symbol_pins']) for r,p in parts.items() if 'symbol_pins' in p}
    model['sheets']=['mcu','display','memory','usb-power','battery','thermal']
    model['fitted_components']=sum(not p['ref'].startswith(('TP','H')) for p in parts.values())
    model['release_gates']=[
        'Upstream BQ25185 SYS/BAT capacitor insertion transient versus BQ29700 remains unresolved; SYS slew switch only mitigates downstream bulk.',
        'Common rail tolerance, feedback bias, transient droop/overshoot, reverse current and module effective capacitance unmeasured.',
        'FRAM RC bounds assume effective C30>=6.8uF, verified maximum rail3.3V, current<=3mA and no capacitor bypass; review BOR4, PVD5, sleep/wake and signal off-state behavior.',
        'Exact OLED module current/low-voltage operation, mechanical header/retention and assembly process unqualified.',
        'All inherited battery, charge-temperature, low-current charger stability, protection and first-article gates remain.']
    return model


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    model=make_model()
    (OUT/'netlist-Q4.json').write_text(json.dumps(model,indent=2)+'\n')
    print(f'Q4 candidate: {len(model["parts"])} refs, {model["fitted_components"]} fitted; NOT RELEASED')
