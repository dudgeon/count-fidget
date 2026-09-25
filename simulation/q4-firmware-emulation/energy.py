#!/usr/bin/env python3
"""Battery-life model driven by the emulated firmware state timeline.

Firmware behaviour (how long the MCU runs/sleeps/stops, OLED powered time, FRAM
standby vs sleep, ADC time) comes from executing the real image in q4emu.py.
Currents come from datasheets (typ at 25 C) or stated estimates.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from q4emu import Sim, fram_journal  # noqa: E402
from scenarios import full_journal, DEFAULT_ELF  # noqa: E402

ELF = str(DEFAULT_ELF)

# mA, typical at 25 C unless noted
I = dict(
    mcu_run=1.10,      # 4 MHz HSI16/4, Range 1, flash (DS10689 Table 30 interpolated; estimate)
    mcu_sleep=0.35,    # Sleep at 4 MHz Range 1 incl. HSI16 (Table 34 interpolated; estimate)
    mcu_stop=0.0033,   # Stop 0.43 uA + PVD/BOR 1.2 uA + VREFINT 1.7 uA (Tables 37, 41), ULP not set
    adc=0.05,          # regulator + VREFINT buffer + ~100 SPS conversions (estimate)
    fram_standby=0.090,  # FM25V02A ISB typ (150 max)
    fram_sleep=0.005,    # FM25V02A IZZ typ (8 max)
    oled=1.00,         # HS96L01W4S03 at contrast 0x10, ~20% pixels lit (estimate, 0.6-2.0 mA)
    ldo_tlv767=0.050,  # TLV767 IQ typ (80 max)
    divider=0.016,     # 150k + 49.9k at 3.205 V
    bq29700=0.004, bq25185=0.004, u7=0.0005)
NANO_LDO = 0.000025   # TPS7A02-class fixed regulator IQ, no external divider


def integrate(sim, t0, t1):
    """Charge (mAs) from t0 to t1 using the timeline of state changes."""
    state = {'mcu': 'run', 'oled': 'off', 'fram': 'standby', 'adc': 'off'}
    events = sorted(sim.timeline)
    for t, n, v in events:
        if t > t0: break
        state[n] = v
    charge = 0.0
    breakdown = {}
    t = t0
    idx = [i for i, e in enumerate(events) if e[0] > t0]
    i = idx[0] if idx else len(events)
    while t < t1:
        nxt = events[i][0] if i < len(events) and events[i][0] < t1 else t1
        dt = nxt - t
        parts = {'mcu_' + state['mcu']: I['mcu_' + state['mcu']] if state['mcu'] in ('run', 'sleep', 'stop') else 0,
                 'oled': I['oled'] if state['oled'] == 'on' else 0,
                 'fram': I['fram_standby'] if state['fram'] == 'standby' else I['fram_sleep'],
                 'adc': I['adc'] if state['adc'] == 'on' else 0}
        for k, v in parts.items():
            breakdown[k] = breakdown.get(k, 0) + v * dt
            charge += v * dt
        t = nxt
        if i < len(events) and events[i][0] <= t:
            _, n, v = events[i]; state[n] = v; i += 1
    return charge, breakdown


def session(n_presses, period=1.0):
    s = Sim(ELF, flash_ws_penalty=0.5)
    s.fram.mem[:] = full_journal(count=500)
    s.press(1.5, 'rst', 0.2)          # clear any boot-time ERR so every build counts normally
    s.run(40.0)                       # then 30 s inactivity -> Stop
    assert s.in_stop or s.stop_count, 'did not reach Stop'
    t_start = 45.0
    for k in range(n_presses):
        s.press(t_start + k * period, 'inc', 0.1)
    t_end = t_start + n_presses * period + 35.0
    s.run(t_end)
    q, br = integrate(s, t_start, t_end)
    # asleep baseline over same window
    j = fram_journal(s.fram)['latest']
    return dict(presses=n_presses, window_s=t_end - t_start, charge_mAs=q, breakdown_mAs=br,
                final_count=j['count'], stops=s.stop_count)


def main():
    global ELF
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--elf', type=Path, default=DEFAULT_ELF)
    ap.add_argument('--output', type=Path)
    a = ap.parse_args()
    ELF = str(a.elf)
    out = {'elf': ELF}
    for n in (1, 10, 30):
        r = session(n)
        out[f'session_{n}'] = r
        print(f"session {n:3d} presses: window {r['window_s']:.0f} s, MCU/OLED/FRAM/ADC charge {r['charge_mAs']:.1f} mAs "
              f"({r['charge_mAs']/3.6:.2f} uAh) count={r['final_count']}  breakdown={ {k: round(v,1) for k,v in r['breakdown_mAs'].items()} }")
    # standby (asleep) current, per regulator option
    common_sleep = I['mcu_stop'] + I['fram_sleep'] + I['bq29700'] + I['bq25185'] + I['u7']
    standby = {'TLV76701 + 150k/49.9k (as built)': common_sleep + I['ldo_tlv767'] + I['divider'],
               'nano-IQ fixed LDO (TPS7A02-class)': common_sleep + NANO_LDO}
    out['standby_mA'] = standby
    # extra charge per session above standby: session charge minus asleep MCU/FRAM over the same window
    def extra(n):
        r = out[f'session_{n}']
        return r['charge_mAs'] - (I['mcu_stop'] + I['fram_sleep']) * r['window_s']
    profiles = {'shelf (no use)': [], 'light: 10 sessions x 10 presses': [(10, 10)],
                'moderate: 30 sessions x 10 presses': [(30, 10)], 'heavy: 20 x 30 presses + 1 h continuous': [(20, 30), ('hour', 1)]}
    capacity = {'40 mAh min x 0.9 usable': 36.0, '45 mAh nominal x 0.9 usable': 40.5}
    res = {}
    print('\nstandby current:', {k: round(v * 1000, 1) for k, v in standby.items()}, 'uA')
    for reg, isb in standby.items():
        for pname, spec in profiles.items():
            daily = isb * 24  # mAh baseline
            for item in spec:
                if item[0] == 'hour':
                    # continuous fidgeting: display on, MCU mostly sleeping, FRAM standby, ADC on
                    awake_mA = I['oled'] + 0.45 + I['fram_standby'] + I['adc']
                    daily += awake_mA * item[1]
                else:
                    sessions, presses = item
                    daily += sessions * extra(presses) / 3600.0
            days = {c: round(cap / daily, 1) for c, cap in capacity.items()}
            res[f'{reg} | {pname}'] = dict(mAh_per_day=round(daily, 3), days=days)
            print(f'{reg:38s} {pname:40s} {daily:6.3f} mAh/day -> {days}')
    out['profiles'] = res
    out['currents_mA'] = I
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(out, indent=1) + '\n')


if __name__ == '__main__':
    main()
