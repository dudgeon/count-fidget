#!/usr/bin/env python3
"""Q5 battery-life model driven by the emulated firmware state timeline.

Firmware behaviour (board on/off from the U7 latch, MCU run/sleep, OLED powered
time, FRAM standby/sleep, ADC time) comes from executing the real Q5 image in
q5emu.py. Currents are datasheet typicals at 25 C or stated estimates.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from q5emu import Sim  # noqa: E402
from scenarios import full_journal, DEFAULT_ELF  # noqa: E402

# mA, typical at 25 C unless noted
I = dict(
    mcu_run=1.10,      # 4 MHz HSI16/4, Range 1, 0 WS (DS10689 Table 30 interpolated; estimate)
    mcu_sleep=0.35,    # Sleep at 4 MHz Range 1 incl. HSI16 (Table 34 interpolated; estimate)
    mcu_stop=0.0033,   # Stop with PVD/BOR/VREFINT (Tables 37, 41); USB-held fallback only
    adc=0.05,          # regulator + VREFINT buffer + conversions (estimate)
    fram_standby=0.090, fram_sleep=0.005,     # FM25V02A ISB / IZZ typ
    oled=1.00,         # HS96L01W4S03 at contrast 0x10, ~20% pixels lit (estimate, 0.6-2.0 mA)
    ldo=0.050, feedback=0.016, vbat_divider=0.012,   # TLV767 IQ, 150k/49.9k, 150k/150k at ~3.7 V
    u7_on=0.0005, stat_pullups=0.0,           # STAT pins are high impedance on battery
    protector=0.004, charger_bat=0.004)       # BQ29700 INORMAL, BQ25185 IQ_BAT (always on the cell)
OFF_LEAKAGE = 0.0001        # TPS22917 ISD 10 nA + BAT54C/1N4148WS reverse leakage at <5 V (allowance)
SELF_DISCHARGE_MAH_PER_DAY = 0.03 * 45 / 30   # LIR2032 worst-case 3 %/month (EEMB spec 5.2.6)
ALWAYS = I['protector'] + I['charger_bat']
BOARD_ON = I['ldo'] + I['feedback'] + I['vbat_divider'] + I['u7_on']


def integrate(sim, t0, t1):
    """Charge (mAs) from t0 to t1 from the emulated state timeline."""
    state = {'board': 'off', 'mcu': 'off', 'oled': 'off', 'fram': 'off', 'adc': 'off'}
    events = sorted(sim.timeline)
    for t, n, v in events:
        if t > t0: break
        state[n] = v
    charge, breakdown, t = 0.0, {}, t0
    pending = [e for e in events if t0 < e[0] < t1]
    for nxt, name, value in pending + [(t1, None, None)]:
        dt = nxt - t
        on = state['board'] == 'on'
        parts = {'always': ALWAYS, 'board_rails': BOARD_ON if on else 0.0,
                 'mcu': I['mcu_' + state['mcu']] if on and state['mcu'] in ('run', 'sleep', 'stop') else 0.0,
                 'oled': I['oled'] if on and state['oled'] == 'on' else 0.0,
                 'fram': (I['fram_standby'] if state['fram'] == 'standby' else I['fram_sleep']) if on and state['fram'] in ('standby', 'sleep') else (I['fram_standby'] if on else 0.0),
                 'adc': I['adc'] if on and state['adc'] == 'on' else 0.0,
                 'off_leakage': OFF_LEAKAGE if not on else 0.0}
        for k, v in parts.items():
            breakdown[k] = breakdown.get(k, 0.0) + v * dt
            charge += v * dt
        t = nxt
        if name is not None:
            state[name] = value
    return charge, breakdown


def session(elf, presses, period=1.0):
    """Power on from off with a COUNT press, press `presses` times, then let it auto power off."""
    s = Sim(elf, start='off', usb=False, vbat=3.85)
    s.fram.mem[:] = full_journal(count=500)
    t_start = 1.0
    s.press(t_start, 'inc', 0.1)
    for k in range(1, presses):
        s.press(t_start + k * period, 'inc', 0.1)
    t_end = t_start + presses * period + 40.0
    s.run(t_end)
    assert s.board_state == 'off', 'board did not power off'
    q, br = integrate(s, t_start, t_end)
    on_time = sum(b - a for (a, n, v), (b, _, _) in zip(s.timeline, s.timeline[1:]) if n == 'board' and v == 'on')
    return dict(presses=presses, window_s=t_end - t_start, charge_mAs=q, breakdown_mAs=br, power_events=s.power_events)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--elf', type=Path, default=DEFAULT_ELF)
    ap.add_argument('--output', type=Path)
    a = ap.parse_args()
    root = Path(__file__).resolve().parents[2]
    elf_path = a.elf.resolve()
    out = {'elf': str(elf_path.relative_to(root)) if root in elf_path.parents else str(a.elf),
           'elf_sha256': hashlib.sha256(elf_path.read_bytes()).hexdigest(), 'currents_mA': I, 'off_mA': ALWAYS + OFF_LEAKAGE}
    for n in (1, 10, 30):
        r = session(str(a.elf), n)
        # Subtract the off-state baseline of the window so sessions add on top of the daily off drain.
        r['extra_mAs'] = r['charge_mAs'] - (ALWAYS + OFF_LEAKAGE) * r['window_s']
        out[f'session_{n}'] = r
        print(f"session {n:3d} presses: {r['charge_mAs']:.1f} mAs in {r['window_s']:.0f} s window, "
              f"{r['extra_mAs']/3.6:.2f} uAh above off; breakdown={ {k: round(v, 1) for k, v in r['breakdown_mAs'].items()} }")
    off = ALWAYS + OFF_LEAKAGE
    profiles = {'idle / on a shelf': [], 'light: 10 sessions x 10 presses': [(10, 10)],
                'moderate: 30 sessions x 10 presses': [(30, 10)], 'heavy: 20 x 30 presses + 1 h continuous': [(20, 30), ('hour', 1)]}
    capacity = {'40 mAh min x 0.9 usable': 36.0, '45 mAh nominal x 0.9 usable': 40.5}
    res = {}
    for pname, spec in profiles.items():
        daily = off * 24
        for item in spec:
            if item[0] == 'hour':
                awake = I['oled'] + 0.45 + I['fram_standby'] + I['adc'] + BOARD_ON
                daily += item[1] * awake
            else:
                sessions, presses = item
                daily += sessions * out[f'session_{presses}']['extra_mAs'] / 3600.0
        days = {c: round(cap / (daily + SELF_DISCHARGE_MAH_PER_DAY), 1) for c, cap in capacity.items()}
        res[pname] = dict(mAh_per_day=round(daily, 4), days=days)
        print(f'{pname:42s} {daily:6.3f} mAh/day -> {days}')
    # Storage: from full to the firmware cut-off, then from cut-off to the BQ29700 2.8 V disconnect.
    out['profiles'] = res
    out['storage_note'] = ('Off drain ~8.1 uA (protector + charger battery quiescent) plus up to 3 %/month self-discharge. '
                           'After the BQ29700 disconnects at 2.8 V only its ~0.1 uA and self-discharge remain.')
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(out, indent=1, default=str) + '\n')


if __name__ == '__main__':
    main()
