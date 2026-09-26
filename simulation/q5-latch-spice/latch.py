#!/usr/bin/env python3
"""Behavioural ngspice transient of the Q5 soft-power latch with bouncing key contacts.

What is modelled (component values from electronics/q5/netlist-Q5.json):
  cell + protector sense path -> SYS (C2) ; SW1 (bouncing) SYS -> PWR_KEY (R34, Q5 gate C) ;
  BAT54C D3 (PWR_KEY, PWR_HOLD -> SYS_ON) ; C40, R35 ; VBUS -> D4 -> R38 -> SYS_ON ;
  U7 TPS22917 behavioural: ON comparator (threshold corner, 50 mV hysteresis), CT-scaled
  turn-on delay and output slew, reverse-blocking, output floats when off ;
  C5 + TLV767 behavioural LDO (dropout, soft start) -> VLOGIC (C6 + 100 nF bypass) ;
  STM32 behavioural: POR/BOR threshold, reset temporisation, then Reset_Handler drives PB2
  (PWR_HOLD) high ; MCU/OLED load currents.
What is NOT modelled: transistor-level internals of TPS22917/TLV767/STM32 (TI's TPS22917 model is
an encrypted PSpice model that ngspice cannot run), temperature, PCB parasitics. Typical-only
datasheet timing is widened by corners. This is a behavioural circuit simulation, not a measurement.

Run: python3 simulation/q5-latch-spice/latch.py   (writes result.json next to this file)
"""
import hashlib
import itertools
import json
import random
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MODEL = ROOT / 'electronics/q5/netlist-Q5.json'
CT = 4.7e-9

NETLIST = """* Q5 latch behavioural transient
.param vcell={vcell} vth={vth} kslew={kslew} tempo={tempo} vbor={vbor} vbus={vbus}
.param tr={{1.6e-6*4700*kslew}} ton={{3.8e-6*4700*kslew}} td={{ton-tr}}
Vcell cell 0 {{vcell}}
Rprot cell sys 3.4
C2 sys 0 10u
* SW1 bouncing contact: control waveform from Python
Vkey kctl 0 PWL({pwl})
S1 sys pwr_key kctl 0 swkey
.model swkey sw vt=0.5 vh=0.05 ron=0.2 roff=1e9
R34 pwr_key 0 100k
Cq5 pwr_key 0 60p
D3a pwr_key sys_on bat54
D3b pwr_hold sys_on bat54
.model bat54 d is=2e-7 n=1.05 rs=2.5 cjo=10p bv=30
C40 sys_on 0 10n
R35 sys_on 0 1meg
Vvbus vbus 0 {{vbus}}
D4 vbus vbus_wake d4148
.model d4148 d is=2.5e-9 n=1.75 rs=0.6 cjo=2p
R38 vbus_wake sys_on 100k
* U7 ON comparator with hysteresis (state node en, 0/1)
Ben en_t 0 V = V(sys_on) > vth ? 1 : (V(sys_on) < vth-0.05 ? 0 : (V(en) > 0.5 ? 1 : 0))
Ren en_t en 1k
Cen en 0 1n
* turn-on delay integrator (restarts whenever ON falls)
Gd 0 dly cur = V(en) > 0.5 ? (V(dly) < 1.05 ? 1/td : 0) : -V(dly)*1e5
Cd dly 0 1
Rd dly 0 1e9
* output voltage ramp after the delay, slope VIN/tR
Gr 0 ramp cur = (V(en) > 0.5 && V(dly) >= 1) ? (V(ramp) < 6 ? V(sys)/tr : 0) : -V(ramp)*1e5
Cr ramp 0 1
Rr ramp 0 1e9
* pass element: sources current SYS -> SYS_LOAD towards min(ramp, SYS), reverse blocked
Gsw sys sys_load cur = V(en) > 0.5 ? max(min(V(ramp), V(sys)) - V(sys_load), 0) / 0.09 : 0
C5 sys_load 0 2.2u
Rleak sys_load 0 10meg
* TLV767 behavioural: soft start 0.5 ms once SYS_LOAD > 1.4 V, 3.205 V set point, 0.12 V dropout
Gss 0 ss cur = V(sys_load) > 1.4 ? (V(ss) < 1 ? 1/0.5e-3 : 0) : -V(ss)*1e5
Css ss 0 1
Rss ss 0 1e9
Gldo sys_load vlogic cur = max(min(3.205*min(V(ss),1), V(sys_load) - 0.12) - V(vlogic), 0) / 0.5
C6 vlogic 0 10.8u
* STM32: BOR release then reset temporisation, then PB2 high; 1.5 mA running, 0.3 mA in reset
Gpor 0 por cur = V(vlogic) > vbor ? (V(por) < 1.05 ? 1/tempo : 0) : -V(por)*1e5
Cpor por 0 1
Rpor por 0 1e9
Gmcu vlogic 0 cur = V(vlogic) > 1.6 ? (V(por) >= 1 ? 1.5e-3 : 0.3e-3) : V(vlogic)/10k
Bpb2 pb2 0 V = V(por) >= 1 ? V(vlogic) : 0
Rpb2 pb2 pwr_hold 40
.tran 20u {tstop} 0 20u uic
.ic V(sys)={{vcell}} V(sys_on)=0 V(sys_load)=0 V(vlogic)=0 V(en)=0
.control
set wr_singlescale
set wr_vecnames
run
wrdata {out} V(sys_on) V(sys_load) V(vlogic) V(pwr_hold) V(kctl) V(en)
quit
.endc
.end
"""


def contact(press_ms, bounce, rng, t0=1e-3):
    """PWL for a key press lasting press_ms (first make -> final break) with optional bounce."""
    pts = [(0, 0), (t0, 0)]
    t = t0
    def edge(v):
        nonlocal t
        pts.append((t, pts[-1][1])); pts.append((t + 1e-6, v)); t += 1e-6
    end = t0 + press_ms * 1e-3
    if bounce:   # make bounce: 3-8 chatter intervals of 50-600 us over the first ~3 ms
        for _ in range(rng.randint(3, 8)):
            edge(1); t += rng.uniform(50e-6, 600e-6); edge(0); t += rng.uniform(50e-6, 400e-6)
    edge(1)
    brk = end - (rng.uniform(1e-3, 3e-3) if bounce else 0)
    t = max(t, brk)
    if bounce:   # break bounce before the final release
        for _ in range(rng.randint(2, 6)):
            edge(0); t += rng.uniform(50e-6, 500e-6); edge(1); t += rng.uniform(50e-6, 300e-6)
    t = max(t, end)
    edge(0)
    return ' '.join(f'{a:.7g} {b:g}' for a, b in pts)


def run(case, pwl, tstop):
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / 'o.txt'
        net = NETLIST.format(pwl=pwl, tstop=tstop, out=out, **case)
        (Path(d) / 'c.cir').write_text(net)
        r = subprocess.run(['ngspice', '-b', str(Path(d) / 'c.cir')], capture_output=True, text=True, timeout=300)
        if not out.exists():
            raise RuntimeError(r.stdout[-2000:] + r.stderr[-2000:])
        rows = [l.split() for l in out.read_text().splitlines()[1:]]
    return [[float(x) for x in r] for r in rows]


def outcome(rows):
    t_end = rows[-1][0]
    late = [r for r in rows if r[0] > t_end - 5e-3]
    latched = all(r[3] > 3.0 for r in late) and all(r[4] > 2.5 for r in late)
    peak_vlogic = max(r[3] for r in rows)
    partial = (not latched) and peak_vlogic > 1.6          # MCU saw power but the latch dropped
    return dict(latched=latched, peak_vlogic=round(peak_vlogic, 3), partial_start=partial,
                final_sys_load=round(rows[-1][2], 3))


def min_press(case, bounce, seed, lo=2, hi=80):
    rng_seed = seed
    def ok(ms):
        rng = random.Random(rng_seed)
        return outcome(run(case, contact(ms, bounce, rng), (ms + 60) * 1e-3))['latched']
    if not ok(hi):
        return None
    while hi - lo > 0.5:
        mid = (lo + hi) / 2
        if ok(mid):
            hi = mid
        else:
            lo = mid
    return round(hi, 1)


def main():
    model = json.loads(MODEL.read_text())
    parts = {p['ref']: p for p in model['parts']}
    for ref, val in dict(C40='10n', R35='1M', R38='100k', R34='100k', C29='4.7n', C5='2.2u', C6='10u').items():
        assert parts[ref]['value'] == val, (ref, parts[ref]['value'])
    assert parts['D3']['pins'] == {'1': 'PWR_KEY', '2': 'PWR_HOLD', '3': 'SYS_ON'}
    assert parts['SW1']['pins'] == {'1': 'PWR_KEY', '2': 'SYS'}
    results = dict(min_press_ms=[], bounce_trials=[], short_tap=[], usb=[])
    corners = list(itertools.product([3.40, 3.70, 4.20], [0.40, 0.70, 1.00], [0.75, 1.0, 1.25], [1.0e-3, 3.3e-3]))
    base = dict(vbor=2.85, vbus=0)
    # 1. minimum clean press that latches, every corner
    for vcell, vth, kslew, tempo in corners:
        case = dict(base, vcell=vcell, vth=vth, kslew=kslew, tempo=tempo)
        results['min_press_ms'].append(dict(vcell=vcell, vth=vth, kslew=kslew, tempo_ms=tempo * 1e3,
                                            min_clean_press_ms=min_press(case, False, 0)))
    worst = max(r['min_clean_press_ms'] for r in results['min_press_ms'])
    # 2. bouncing presses at 50 ms (the deliberate-press figure) and at the worst clean minimum + 5 ms
    rng = random.Random(1)
    for i in range(120):
        vcell, vth, kslew, tempo = rng.choice(corners)
        case = dict(base, vcell=vcell, vth=vth, kslew=kslew, tempo=tempo)
        ms = 50 if i % 2 == 0 else worst + 5
        o = outcome(run(case, contact(ms, True, random.Random(1000 + i)), (ms + 60) * 1e-3))
        results['bounce_trials'].append(dict(press_ms=ms, vcell=vcell, vth=vth, kslew=kslew, tempo_ms=tempo * 1e3, **o))
    # 3. very short taps must abort cleanly (no latch); record whether the MCU saw a partial start
    for ms in (2, 5, 10, 15):
        for vcell, vth in itertools.product([3.4, 4.2], [0.4, 1.0]):
            case = dict(base, vcell=vcell, vth=vth, kslew=1.0, tempo=1e-3)
            o = outcome(run(case, contact(ms, True, random.Random(ms)), 0.12))
            results['short_tap'].append(dict(press_ms=ms, vcell=vcell, vth=vth, **o))
    # 4. USB present, no key: VBUS alone must turn the board on at 4.4 and 5.25 V
    for vbus, vth in itertools.product([4.40, 5.25], [0.4, 1.0]):
        case = dict(base, vcell=3.7, vth=vth, kslew=1.25, tempo=3.3e-3, vbus=vbus)
        o = outcome(run(case, '0 0 1 0', 0.08))
        results['usb'].append(dict(vbus=vbus, vth=vth, **o))
    bt = results['bounce_trials']
    summary = dict(
        worst_min_clean_press_ms=worst,
        best_min_clean_press_ms=min(r['min_clean_press_ms'] for r in results['min_press_ms']),
        bounce_50ms_latched=f"{sum(r['latched'] for r in bt if r['press_ms'] == 50)}/{sum(1 for r in bt if r['press_ms'] == 50)}",
        bounce_worst_plus5_latched=f"{sum(r['latched'] for r in bt if r['press_ms'] != 50)}/{sum(1 for r in bt if r['press_ms'] != 50)}",
        short_taps_latched=sum(r['latched'] for r in results['short_tap']),
        short_taps_partial_mcu_start=sum(r['partial_start'] for r in results['short_tap']),
        usb_turns_on=all(r['latched'] for r in results['usb']))
    out = dict(schema=1, status='Behavioural ngspice transient; not a measurement or transistor-level simulation',
               model_sha256=hashlib.sha256(MODEL.read_bytes()).hexdigest(),
               script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               ngspice=subprocess.run(['ngspice', '-v'], capture_output=True, text=True).stdout.split('\n')[1].strip(),
               corners=dict(vcell_V=[3.4, 3.7, 4.2], on_threshold_V=[0.4, 0.7, 1.0], slew_scale=[0.75, 1.0, 1.25],
                            reset_temporisation_ms=[1.0, 3.3]),
               summary=summary, **results)
    (HERE / 'result.json').write_text(json.dumps(out, indent=1) + '\n')
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
