"""Deterministic Q3 electrical sensitivity analysis, not circuit qualification.

Uses the frozen model's selected values. Analytical counterexamples demonstrate
why specified information is insufficient; they do not predict a built board.
Only writes the separate dated report, never Q3 design/export/package files.
"""
import hashlib
import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / 'electronics/q3/netlist-Q3.json'
OUT = ROOT / 'verification/q3-hardware-corners-2026-09-22.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def value(part):
    text = part['value']
    factors = {'k': 1e3, 'u': 1e-6, 'n': 1e-9}
    return float(text[:-1]) * factors[text[-1]] if text[-1] in factors else float(text)


def temperature(resistance, r25=10000.0, beta=3380.0):
    return 1.0 / (1.0 / 298.15 + math.log(resistance / r25) / beta) - 273.15


def thermal(parts, tolerance, error_v):
    refs = ['R10', 'R11', 'R12', 'R13']
    results = {'cold': [], 'hot': []}
    cases = 0
    for signs in itertools.product((-1, 1), repeat=8):
        r10, r11, r12, r13 = [value(parts[r]) * (1 + tolerance * s)
                              for r, s in zip(refs, signs[:4])]
        r25 = 10000 * (1 + 0.01 * signs[4])
        beta = 3380 * (1 + 0.01 * signs[5])
        vbus = 2.95 if signs[6] == -1 else 5.5
        error = error_v * signs[7]
        total = r11 + r12 + r13
        for label, ratio in (('cold', (r12 + r13) / total), ('hot', r13 / total)):
            a = ratio + error / vbus
            assert 0 < a < 1
            results[label].append(temperature(r10 * a / (1 - a), r25, beta))
        cases += 1
    return {'independent_corner_combinations': cases,
            'resistor_tolerance_fraction': tolerance, 'threshold_error_v': error_v,
            'vbus_v': [2.95, 5.5], 'r25_and_beta_tolerance_fraction': 0.01,
            'temperature_c': {k: [round(min(v), 6), round(max(v), 6)] for k, v in results.items()},
            'qualification': 'Conditional beta/offset model; not guaranteed installed-cell temperatures'}


def inrush_time(vcell, rsense, rother, cap, threshold):
    """Hard-connected, initially empty lumped C; no load, inductance or slew."""
    total_r = rsense + rother
    initial_sense = vcell * rsense / total_r
    return (0.0 if initial_sense <= threshold else
            total_r * cap * math.log(initial_sense / threshold))


def main():
    model = json.loads(MODEL.read_text())
    parts = {p['ref']: p for p in model['parts']}
    expected = {'U2': 'BQ25185DLHR', 'U4': 'BQ29700DSER',
                'U5': 'TLV7012DGKR', 'U6': 'TPS63900DSKR',
                'DS1': 'X087-2832TSWIG02-H14'}
    assert all(parts[ref]['mpn'] == mpn for ref, mpn in expected.items()), 'Review component assumptions'
    assert parts['R9']['pins'] == {'1': 'SENSE_FET', '2': 'GND'}
    assert parts['U6']['pins']['10'] == 'SYS'
    assert parts['R26']['pins'] == {'1': 'V3', '2': 'OLED_SCL'}
    assert parts['R27']['pins'] == {'1': 'V3', '2': 'OLED_SDA'}
    sys_caps = [p for p in parts.values() if p['ref'].startswith('C')
                and set(p['pins'].values()) == {'SYS', 'GND'}]
    assert {p['ref'] for p in sys_caps} == {'C2', 'C5', 'C17'}
    r10, r11, r12, r13 = (value(parts[r]) for r in ('R10', 'R11', 'R12', 'R13'))
    total = r11 + r12 + r13
    nominal = {label: temperature(r10 * ratio / (1 - ratio)) for label, ratio in
               [('cold', (r12 + r13) / total), ('hot', r13 / total)]}
    pullup = value(parts['R27'])
    assert pullup == value(parts['R26']) == 4700
    # A hypothetical linear 6k sink meets <=0.6V at100uA/3V, yet fails ACK
    # with4.7k. This is a logical counterexample, not a fitted device model.
    weak_sink_ohm = 6000
    ack = 3.0 * weak_sink_ohm / (pullup + weak_sink_ohm)
    assert weak_sink_ohm * 100e-6 <= 0.2 * 3.0
    assert ack > 1.65  # MSP430 specified maximum negative-going threshold at3V.
    rise_constant = math.log(0.7 / 0.3)
    buses = []
    for resistance in (pullup, 25500.0, 33000.0):
        buses.append({'pullup_nominal_ohm': resistance,
                      'rise_300ns_max_total_capacitance_pf_at_plus_1pct_r':
                          300e-9 / (rise_constant * resistance * 1.01) * 1e12,
                      'sink_ua_at_zero_v_3p09v_minus_1pct_r': 3.09 / (resistance * .99) * 1e6,
                      'sink_ua_at_0p2vdd_3p09v_minus_1pct_r': .8 * 3.09 / (resistance * .99) * 1e6})
    rsense = value(parts['R9'])
    inrush = []
    for voltage, other_r, cap_uf, threshold in itertools.product(
            (3.2, 3.7, 4.2), (0.2, 1.0, 5.0, 20.0, 40.0), (12.0, 20.0, 34.2), (.4, .5, .6)):
        duration = inrush_time(voltage, rsense, other_r, cap_uf * 1e-6, threshold) * 1e6
        inrush.append({'cell_v': voltage, 'other_series_r_ohm': other_r,
                       'effective_sys_c_uf': cap_uf, 'short_threshold_v': threshold,
                       'above_threshold_us': round(duration, 6),
                       'exceeds_minimum_125us_delay': duration > 125})
    demo_us = inrush_time(4.2, rsense, 1.0, 20e-6, .4) * 1e6
    # Independent fixed-step RC integration checks the analytic example.
    dt, voltage, crossed = 10e-9, 0.0, None
    for step in range(100000):
        current = (4.2 - voltage) / (rsense + 1.0)
        if current * rsense <= .4:
            crossed = step * dt * 1e6
            break
        voltage += current / 20e-6 * dt
    assert crossed is not None and abs(crossed - demo_us) < .05
    output_budget = [{'sys_v': vin, 'assumed_efficiency': eta,
                      'pump_feed_ma_from_nominal_10ma_input_at4v': 10 * vin * eta / 4}
                     for vin, eta in itertools.product((3.0, 3.7, 4.5), (.7, .8, .9, 1.0))]
    report = {
        'date': '2026-09-22', 'status': 'CONDITIONAL_ANALYSIS_NOT_HARDWARE_QUALIFICATION',
        'inputs_sha256': {p.relative_to(ROOT).as_posix(): sha(p) for p in
                         (MODEL, Path(__file__).resolve(), ROOT / 'firmware/q3-oled/main_msp430.c',
                          ROOT / 'firmware/q3-oled/oled.c', ROOT / 'electronics/q3/click-counter-Q3.kicad_pcb')},
        'thermal': {'nominal_trip_c': nominal,
                    'retained_conservative_error_model': thermal(parts, .0201, .0215),
                    'tlv7012_half_supply_table_plus_assumed_1mv_allowance': thermal(parts, .0201, .0165),
                    'warning': 'Neither offset model bounds arbitrary common-mode, board leakage, NTC beta fit or attachment error'},
        'i2c': {'module_vol_test_current_ua': 100, 'module_vol_max_fraction_vdd': .2,
                'module_max_rise_ns': 300, 'mcu_negative_threshold_range_at3v': [.75, 1.65],
                'hypothetical_compliant_weak_sink': {'linear_resistance_ohm': weak_sink_ohm,
                                                   'vol_at100ua_v': weak_sink_ohm * 100e-6,
                                                   'ack_voltage_with_actual4700ohm_at3v_v': ack,
                                                   'actual_module_resistance_known': False},
                'pullup_sensitivities': buses,
                '100pf_bus_actual4700ohm_plus1pct_r_rise_ns': rise_constant * pullup * 1.01 * 100e-12 * 1e9},
        'battery_insertion': {'sys_capacitors': {p['ref']: p['value'] for p in sys_caps},
                              'sys_nominal_total_uf': sum(value(p) for p in sys_caps) * 1e6,
                              'short_circuit_threshold_25c_v': [.4, .5, .6],
                              'short_circuit_delay_us': [125, 250, 375],
                              'example_above_threshold_us': demo_us,
                              'independent_euler_example_us': crossed,
                              'sample_grid': inrush,
                              'limitations': ['Hard BATFET/protector turn-on assumed; actual slew not established.',
                                              'Unknown cell impedance and nonlinear capacitance; selected grid is sensitivity, not component limits.',
                                              'No direct BAT-capacitor or LDO/MCU startup load modeled; no protector state-machine or recovery model.',
                                              'TPS63900 current limit does not limit charging its VIN capacitor.']},
        'oled_power': {'nominal_input_limit_ma': 10, 'limit_minmax_guaranteed': False,
                       'output_budget_sensitivities': output_budget,
                       'panel_all_on_vbat_typ_ma': 13,
                       'sparse_firmware_current_guaranteed': False,
                       'note': 'No linear pixel/contrast scaling assumed; logic current and converter/pump losses remain separate.'},
        'model_checks': {'rc_analytic_crosschecked_by_euler': True,
                         'i2c_spec_consistent_failure_counterexample_reproduced': True},
        'limitations': ['No SPICE/macromodel, oscilloscope data, new DRC or physical qualification.',
                        'No artifact/design change or vendor communication. Source references and dispositions are in the dated hardware review.']}
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print('Conditional hardware analysis saved:', OUT.relative_to(ROOT))
    print('I2C spec-consistent counterexample ACK voltage:', round(ack, 6), 'V')
    print('Conditional inrush example above0.4V:', round(demo_us, 6), 'us; minimum delay125us')
    print('No hardware PASS or manufacturing release is asserted.')


if __name__ == '__main__':
    main()
