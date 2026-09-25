#!/usr/bin/env python3
"""Bounded analytical checks for the Q5 power changes (not a circuit simulation).

Each check states its datasheet inputs and assumptions and produces a number
that the Q5 power document quotes. Physical measurement remains required for
every item; typical-only datasheet values are labelled as such.
"""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / 'electronics/q5/netlist-Q5.json'
OUT = Path(__file__).resolve().parent / 'result.json'


def check_latch(model):
    parts = {p['ref']: p for p in model['parts']}
    ct = 4.7e-9
    assert parts['C29']['value'] == '4.7n' and parts['C29']['pins'] == {'1': 'SYS', '2': 'SYS_CT'}
    ton = 3.8e-6 * ct * 1e12          # TPS22917 tON 3.8 us/pF at VIN 3.3-3.6 V (typical only)
    tr = 1.6e-6 * ct * 1e12           # tR 1.6 us/pF (typical only)
    tempo_max = 3.3e-3                # DS10689 Table 27 TRSTTEMPO, VDD rising, BOR enabled
    ldo = 0.5e-3                      # TLV767 soft start typical
    firmware = 0.1e-3                 # Reset_Handler -> setup(): PB2 driven high (emulated ~20 us, allowance)
    typ = ton + ldo + 2e-3 + firmware
    worst = 1.25 * ton + ldo + tempo_max + firmware   # +25% allowance on the typical-only slew
    # ON-node levels: VIH(ON) min 1.0 V; BAT54C VF at a few uA ~0.25 V; 1N4148WS ~0.6 V at uA levels.
    levels = dict(pwr_hold_min=3.151 - 0.3, key_min_battery=3.0 - 0.3, vbus_min=4.4 - 0.7, vbus_max=5.25 - 0.4)
    ok = all(v >= 1.0 for v in levels.values()) and levels['vbus_max'] <= 5.5
    return dict(ton_typ_ms=round(ton * 1e3, 2), tr_typ_ms=round(tr * 1e3, 2), press_needed_typ_ms=round(typ * 1e3, 1),
                press_needed_allowance_ms=round(worst * 1e3, 1), deliberate_press_ms=50,
                margin_factor_at_50ms=round(0.050 / worst, 2), on_node_levels_V=levels, on_levels_within_VIH_and_abs_max=ok,
                note='TPS22917 slew figures are typical only; the press-duration bound is an allowance, not a guarantee.')


def check_inrush(model):
    caps_uF = dict(C5=2.2, C6=10.0, C30=10.0, bypass_100n=0.1 * 8)   # C31-C35, C7, C36, C37 on SYS_LOAD/VLOGIC
    total = sum(caps_uF.values()) * 1.10                               # +10% capacitance tolerance
    tr = 1.6e-6 * 4.7e-9 * 1e12
    i = total * 1e-6 * 3.3 / tr * 1e3 + 1.5                            # plus MCU start-up current
    ocd_min_mA = 0.09 / 3.3 * 1e3                                     # BQ29700 VOCD lower bound / R9 (see q4 power doc)
    half = total * 1e-6 * 3.3 / (tr / 2) * 1e3 + 1.5
    return dict(downstream_capacitance_uF_plus10pct=round(total, 2), inrush_typ_slew_mA=round(i, 1),
                inrush_if_slew_twice_as_fast_mA=round(half, 1), bq29700_ocd_min_mA=round(ocd_min_mA, 1),
                passes_typical=i < ocd_min_mA, note='X5R/X7R DC-bias derating lowers effective C; measure inrush at first article.')


def check_off_current():
    typ = dict(bq29700=4.0, bq25185_bat=4.0, tps22917_isd=0.01, diode_reverse_at_0V=0.0)
    mx = dict(bq29700=5.5, bq25185_bat=5.0, tps22917_isd=0.5, diode_reverse_at_0V=0.1)
    return dict(typ_uA=round(sum(typ.values()), 2), max_uA=round(sum(mx.values()), 2),
                removed_versus_q4_asleep_uA=['TLV767 IQ 50', 'feedback 16', 'FRAM sleep 5', 'MCU Stop 3.3', 'U7 on 0.5'],
                note='Everything downstream of U7 (regulator, dividers, MCU, FRAM, OLED) is unpowered when off.')


def check_battery_adc():
    vref_budget = 0.018622      # Q4 VREFINT estimate budget (q4-power-design.md), 1.8622 %
    divider = 0.002             # two 0.1 % resistors, worst-case ratio
    err = vref_budget + divider
    usb_min = 4.5 * 0.98 * (1 - err)
    cell_max = 4.2 * 1.005 * (1 + err)          # BQ25185 VBATREG accuracy +/-0.5 %
    threshold = 4.313
    leak = 50e-9 * 75e3                          # PA4 input leakage max x Thevenin source
    cut_lo, cut_hi = 3.35 / (1 + err), 3.35 / (1 - err)
    return dict(total_error_pct=round(err * 100, 3), usb_sys_min_reading_V=round(usb_min, 4), full_cell_max_reading_V=round(cell_max, 4),
                usb_threshold_V=threshold, separation_ok=cell_max < threshold < usb_min,
                leakage_error_mV=round(leak * 1e3, 2), cutoff_actual_range_V=[round(cut_lo, 3), round(cut_hi, 3)],
                divider_current_while_on_uA=round(3.7 / 300e3 * 1e6, 1), divider_current_off_uA=0.0,
                note='STAT1/STAT2 low also classify USB, covering the charging and fault states at any ADC error.')


def check_cold_insertion():
    rs = 3.333
    def exposure(c):
        return c * 4.2 * rs / (math.e * 0.4)
    c_upstream = (10.0 + 2.2) * 1.10 * 1.15e-6
    c3 = 2.2 * 1.10 * 1.15e-6
    return dict(cold_insert_upstream_us=round(exposure(c_upstream) * 1e6, 3), usb_first_c3_only_us=round(exposure(c3) * 1e6, 3),
                bq2970_scc_delay_min_us=125, cold_insertion_bound_passes=exposure(c_upstream) < 125e-6,
                usb_first_passes=exposure(c3) < 125e-6,
                latch_effect='U7 is OFF at insertion (no key, no USB), so SYS_LOAD capacitance never loads the cell at insertion; the upstream C2/C3 counterexample of Q4 is unchanged.',
                bq2970_first_connection='SLUSBU9I 8.4.1: discharge may not enable until a charger is connected - insert the cell with USB present.')


def check_storage():
    cap = {'min_40mAh': 36.0, 'nominal_45mAh': 40.5}
    off = check_off_current()['typ_uA'] * 1e-3 * 24
    self_d = 0.03 * 45 / 30
    reserve_mAh = 0.05 * 45
    return dict(shelf_days_to_cutoff={k: round(v / (off + self_d), 0) for k, v in cap.items()},
                days_cutoff_to_protector=round(reserve_mAh / (off + self_d), 1),
                recommendation='Store charged to about 50-60 %, top up every 3 months; after the 3.35 V firmware cut-off the protector disconnects at 2.8 V roughly a week later.')


def main():
    model = json.loads(MODEL.read_text())
    result = dict(schema=1, scope='Analytical bounds from stated datasheet values; not a simulation or measurement',
                  model_sha256=hashlib.sha256(MODEL.read_bytes()).hexdigest(),
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  latch=check_latch(model), inrush=check_inrush(model), off_current=check_off_current(),
                  battery_adc=check_battery_adc(), cold_insertion=check_cold_insertion(), storage=check_storage())
    expected_pass = [result['latch']['on_levels_within_VIH_and_abs_max'], result['inrush']['passes_typical'],
                     result['battery_adc']['separation_ok'], result['cold_insertion']['usb_first_passes']]
    result['bounded_checks_pass'] = all(expected_pass)
    result['retained_counterexample'] = 'Unrestricted cold insertion (upstream C2+C3) still exceeds the 125 us minimum SCC delay.'
    OUT.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    if not result['bounded_checks_pass'] or result['cold_insertion']['cold_insertion_bound_passes']:
        raise SystemExit('Unexpected check outcome')


if __name__ == '__main__':
    main()
