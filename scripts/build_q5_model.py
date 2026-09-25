"""Build the separate Q5 circuit candidate from the frozen Q4 JSON.

Q5 adds the COUNT-key soft power latch on the existing U7 switch, a
vendor-assembled LIR2032 holder with an onboard NTC (no custom pack or
harness), a switched-rail battery divider, charger status inputs and the
issue #8 display-supply decisions. It is an engineering model, not
manufacture authorization. Root-owned placement.json may override only
physical placement fields.
"""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'electronics/q5'
BASE = ROOT / 'electronics/q4/netlist-Q4.json'


def pinmeta(names, kinds=None):
    kinds = kinds or {}
    return {str(i): {'name': n, 'type': kinds.get(str(i), 'bidirectional')}
            for i, n in enumerate(names, 1)}


def make_model():
    model = copy.deepcopy(json.loads(BASE.read_text()))
    parts = {p['ref']: p for p in model['parts']}
    for p in parts.values():
        p['footprint'] = p['footprint'].replace('CountFidgetQ4:', 'CountFidgetQ5:')
    symbol_pins = copy.deepcopy(model['symbol_pins'])

    def add(ref, value, mpn, maker, footprint, pins, notes, lcsc, sheet, x=21, y=30,
            side='bottom', symbol=None, assembly='jlc_smt'):
        p = dict(ref=ref, value=value, mpn=mpn, manufacturer=maker,
                 footprint='CountFidgetQ5:' + footprint, pins=pins, notes=notes,
                 x=x, y=y, rotation=0, side=side, sheet=sheet, lcsc=lcsc, assembly=assembly)
        if symbol:
            p['symbol_pins'] = symbol
        parts[ref] = p
        return p

    def clone(ref, template, pins, sheet, notes):
        p = copy.deepcopy(parts[template])
        p.update(ref=ref, pins=pins, sheet=sheet, notes=notes)
        p.pop('symbol_pins', None)
        parts[ref] = p
        return p

    # Issue #13: no custom pack/harness. A vendor-soldered LIR2032 holder and an
    # onboard 0603 NTC replace the four-wire connector.
    del parts['J2']
    add('BT1', 'LIR2032 holder', 'CR2032-BS-6-1', 'Q&J', 'BatteryHolder_QJ_CR2032-BS-6-1',
        {'1': 'CELL_P', '2': 'CELL_N_RAW'},
        'SMD 2032 coin-cell holder, pad1 + (frame) / pad2 -; accepts the user-supplied rechargeable '
        'LIR2032 only (never a primary CR2032/ML2032); every insertion is a cold insertion - see USB-first procedure.',
        'C70377', 'battery', symbol=pinmeta(['+', '-'], {'1': 'passive', '2': 'passive'}))
    add('TH1', '10k NTC B3380', 'NCP18XH103F03RB', 'Murata', 'Resistor_SMD_R_0603_1608Metric',
        {'1': 'TEMP_SENSE', '2': 'GND'},
        'Same NTC the Q2-Q4 window was designed for (10k, B25/50 3380K, 1%); placed against the holder '
        'body. Board-mounted sensing measures holder/board temperature, not the cell core.',
        'C13564', 'thermal')
    # Issue #13: TLV7012DGKR had 22 in stock; the SOT-23-8 package of the same
    # die has the identical OUTA/INA-/INA+/VEE/INB+/INB-/OUTB/VCC pinout.
    parts['U5'].update(mpn='TLV7012DDFR', lcsc='C2871502',
                       footprint='CountFidgetQ5:Package_TO_SOT_SMD_SOT-23-8',
                       notes='Same TLV7012 die and pin order as DGK (datasheet Table 5-2); push-pull outputs; '
                             'charge enable requires both in-window indications; USB-powered.')
    # Issue #12: soft power latch on U7. ON = VBUS diode OR COUNT key (SYS) OR PWR_HOLD.
    parts['U7']['pins'] = {'1': 'SYS', '2': 'GND', '3': 'SYS_ON', '4': 'SYS_CT', '6': 'SYS_LOAD'}
    parts['U7']['value'] = 'System soft-power latch switch'
    parts['U7']['notes'] = ('ON driven by D3/D4 OR and pulled down by R35; QOD NC. Off state removes every '
                            'load downstream of SYS. Does not limit upstream charger SYS/BAT capacitors.')
    parts['SW1'].update(value='COUNT / POWER', pins={'1': 'PWR_KEY', '2': 'SYS'})
    parts['SW1']['notes'] = ('Exact clicky switch closing SYS to PWR_KEY: powers the board on and, through Q5, '
                             'drives COUNT_N low. Home through-hole soldering after the rear key plate is fitted.')
    add('D3', 'BAT54C', 'BAT54C,215', 'Nexperia', 'Package_TO_SOT_SMD_SOT-23',
        {'1': 'PWR_KEY', '2': 'PWR_HOLD', '3': 'SYS_ON'},
        'Common-cathode Schottky OR into U7 ON: A1 from the COUNT key, A2 from MCU PB2 PWR_HOLD.',
        'C37704', 'usb-power', symbol=pinmeta(['A1', 'A2', 'K'], {'1': 'passive', '2': 'passive', '3': 'passive'}))
    add('D4', '1N4148WS', '1N4148WS', 'Changjiang', 'Diode_SMD_D_SOD-323',
        {'1': 'SYS_ON', '2': 'VBUS'},
        'VBUS into U7 ON: valid USB always powers the board for charging and ROM DFU. Pad1 cathode.',
        'C2128', 'usb-power', symbol=pinmeta(['K', 'A'], {'1': 'passive', '2': 'passive'}))
    clone('Q5', 'Q3', {'1': 'PWR_KEY', '2': 'GND', '3': 'COUNT_N'}, 'mcu',
          'Mirrors the SYS-referenced COUNT key onto the unchanged active-low COUNT_N (R17/C11) input.')
    parts['Q5']['value'] = 'COUNT key level shift'
    clone('R34', 'R6', {'1': 'PWR_KEY', '2': 'GND'}, 'usb-power', '100k PWR_KEY pull-down; draws current only while COUNT is held.')
    add('R35', '1M', '0603WAF1004T5E', 'UNI-ROYAL', 'Resistor_SMD_R_0603_1608Metric',
        {'1': 'SYS_ON', '2': 'GND'},
        '1M U7 ON pull-down: the TPS22917 smart pull-down disconnects after ON is driven high (datasheet 7.3).',
        'C22935', 'usb-power')
    # Slew capacitors reduced so a normal key press latches (tON 3.8us/pF x 4.7nF = 17.9ms typ).
    for ref in ('C28', 'C29'):
        parts[ref].update(value='4.7n', mpn='GRM1885C1H472JA01D', lcsc='C85980',
                          notes='4.7nF 50V C0G slew capacitor to VIN; tON 17.9ms typical; typical slew only')
    # Issue #8: U6 QOD no longer grounds the module supply (SSD1315 6.9.2 note 2).
    parts['U6']['pins'] = {'1': 'VLOGIC', '2': 'GND', '3': 'OLED_ENABLE', '4': 'OLED_CT', '6': 'OLED_SUPPLY'}
    parts['U6']['notes'] = ('CT capacitor connects to VIN. QOD NC so VBAT/VCC floats when off (SSD1315 6.9.2). '
                            'All five display signal pins high impedance before removing power.')
    # Battery gauge: divider on the switched SYS_LOAD rail, so it draws nothing while off.
    for ref, pins in (('R36', {'1': 'SYS_LOAD', '2': 'VBAT_SENSE'}), ('R37', {'1': 'VBAT_SENSE', '2': 'GND'})):
        clone(ref, 'R30', pins, 'mcu', '150k 0.1% 25ppm; SYS_LOAD/2 to PA4 ADC_IN4; zero current while U7 is off')
    clone('C37', 'C7', {'1': 'VBAT_SENSE', '2': 'GND'}, 'mcu', '100nF charge reservoir for the 75k-source ADC input')
    parts['U1']['pins'].update({'14': 'VBAT_SENSE', '15': 'CHG_STAT1', '16': 'CHG_STAT2', '20': 'PWR_HOLD'})
    parts['U1']['notes'] = ('LQFP48; all supply domains common; ROM USB DFU with BOOT0/nBOOT1. PB2 PWR_HOLD, PA4 battery '
                            'sense, PA5/PA6 charger status. PA2/PA3/PA9/PA10 remain free (ROM USART pins). Unused pins NC.')
    parts['U2']['pins'].update({'3': 'CHG_STAT2', '9': 'CHG_STAT1'})
    parts['U2']['notes'] = ('4.2 V; 100 mA input limit; 18.2 mA nominal battery charge; STAT1/STAT2 open drain to MCU '
                            'inputs with internal pull-ups enabled only while awake.')
    # DFM: the holder pads expose CELL_P/CELL_N_RAW and TP12 already exposes
    # BOOT_COUNT_RESET beside TP11, so three redundant lands are removed.
    for ref in ('TP7', 'TP8', 'TP10'):
        del parts[ref]
    clone('TP13', 'TP1', {'1': 'SYS_ON'}, 'usb-power', 'Bring-up: bridge to TP6 SYS to hold the board on without firmware')
    parts['TP13']['value'] = 'SYS_ON'
    for ref in ('SW1', 'SW2'):
        parts[ref]['assembly'] = 'home_through_hole'
    for p in parts.values():
        p.setdefault('assembly', 'jlc_smt')
    overrides_path = OUT / 'placement.json'
    if overrides_path.exists():
        overrides = json.loads(overrides_path.read_text())
        for ref, placement in overrides.items():
            if ref not in parts: raise ValueError('Unknown placement reference: ' + ref)
            if set(placement) - {'x', 'y', 'rotation', 'side'}:
                raise ValueError('Placement override may not change circuit: ' + ref)
            parts[ref].update(placement)
    for ref, p in parts.items():
        if 'symbol_pins' in p:
            symbol_pins[ref] = copy.deepcopy(p['symbol_pins'])
        elif ref in symbol_pins:
            p['symbol_pins'] = copy.deepcopy(symbol_pins[ref])
    model.update(revision='Q5 STM32 soft-power, on-board cell engineering candidate - NOT RELEASED',
        source_baseline='Frozen Q4 JSON; Q1/Q2/Q3/Q4 artifacts unchanged',
        source_baseline_sha256=hashlib.sha256(BASE.read_bytes()).hexdigest(),
        board_mm=[42, 54, 1], layers=2, hardware_tested=False, manufacturing_released=False,
        placement_status='Root-owned placement overrides; single-sided (bottom) factory SMT',
        cost_intent='Standard JLC inventory only; no custom pack/harness; home through-hole limited to display/header and keys',
        parts=sorted(parts.values(), key=lambda p: p['ref']))
    model['symbol_pins'] = {r: copy.deepcopy(p['symbol_pins']) for r, p in parts.items() if 'symbol_pins' in p}
    model['fitted_components'] = sum(not p['ref'].startswith(('TP', 'H')) for p in parts.values())
    model['release_gates'] = [
        'Every cell insertion into BT1 is a cold insertion; the upstream BQ25185 SYS/BAT capacitor transient versus BQ29700 SCC remains a conditional counterexample. Prefer USB-first insertion.',
        'U7 latch: key-press-to-PWR_HOLD timing, ON-node leakage, VLOGIC/VFRAM fall ramps on release and USB unplug in Stop must be measured.',
        'Battery gauge thresholds are loaded-cell engineering choices; confirm on the qualified LIR2032 and holder contact resistance.',
        'Board-mounted NTC senses holder/board temperature, not the cell core; validate the 8-36 C window lag during charge.',
        'Holder accepts primary CR2032/ML2032 cells mechanically; charging one is hazardous. Labelling and user instructions are mandatory.',
        'Common rail tolerance, transients, reverse current, module effective capacitance and OLED low-voltage operation remain unmeasured.',
        'FRAM RC bounds assume effective C30>=6.8uF, maximum rail 3.3V, current<=3mA; review BOR4, PVD5, sleep/wake and off-state behavior.']
    return model


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    model = make_model()
    (OUT / 'netlist-Q5.json').write_text(json.dumps(model, indent=2) + '\n')
    print(f'Q5 candidate: {len(model["parts"])} refs, {model["fitted_components"]} fitted; NOT RELEASED')
