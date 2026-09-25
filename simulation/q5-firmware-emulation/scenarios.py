#!/usr/bin/env python3
"""Scenario suite for the Q5 firmware emulation (model limits: see q5emu.py / README.md).

Runs the real firmware ELF through board-level scenarios and reports display
contents, FRAM journal state, board power, timing and contract violations. With
--check the product behaviours documented for Q5 are asserted (exit status 1 on
failure). Latencies are measured to the AFh/GDDRAM state the panel shows; the
SSD1315 lights SEG/COM about 100 ms (tAF) after AFh on first power-up.
"""
import argparse
import hashlib
import json
import struct
import sys
import time
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from q5emu import Sim, summary, decode_display, fram_journal, battery_icon  # noqa: E402

DEFAULT_ELF = ROOT / 'firmware/q5-stm32/build/count-fidget-Q5-stm32.elf'
T_AF = 0.100


def full_journal(count=1234, nvalid=96, seq0=1000, fault=0):
    """FRAM image with every one of the 96 journal slots valid (steady state after wrap)."""
    mem = bytearray(32768)
    for i in range(nvalid):
        seq = seq0 + i
        c = max(0, count - (nvalid - 1 - i))
        w = [0x51443401, seq, c, fault if i == nvalid - 1 else 0, (~seq) & 0xFFFFFFFF, (~c) & 0xFFFFFFFF, 0, 0x434d5434]
        w[6] = zlib.crc32(struct.pack('<6I', *w[:6])) & 0xFFFFFFFF
        struct.pack_into('<8I', mem, i * 32, *w)
    return mem


def ram_state(s):
    q, a = s.symbols['inputs'], s.symbols['app']
    m = bytes(s.uc.mem_read(q + 0x808, 8))
    return dict(queue_dropped=struct.unpack_from('<H', m, 4)[0])


class Suite:
    def __init__(self, elf, check):
        self.elf, self.check = str(elf), check
        self.results, self.failures = {}, []

    def expect(self, name, ok, detail):
        if not ok:
            self.failures.append(f'{name}: {detail}')
            print(f'    EXPECTATION FAILED: {detail}')

    def sim(self, **kw):
        mem = kw.pop('mem', None)
        s = Sim(self.elf, **kw)
        if mem is not None:
            s.fram.mem[:] = mem
        return s

    def record(self, name, sim, extra=None):
        r = summary(sim, name)
        if sim.board_state in ('on', 'collapsing'):
            r['ram'] = ram_state(sim)
        if extra: r.update(extra)
        self.results[name] = r
        print(f"[{name}] t={r['t']}s board={r['board']} display={r['display']} bars={r['battery_bars']} "
              f"journal={r['fram']['journal']['latest']} halted={r['halted']} stops={r['stop_entries']}")
        for v in r['violations']:
            print('    violation:', v)
        self.expect(name, not r['violations'], f'no contract violations ({r["violations"]})')
        return r

    def watch(self, sim, start, stop, expect, step=0.002):
        rec = {'first': None}
        t = start
        while t < stop:
            def f(s, rec=rec):
                if rec['first'] is None and decode_display(s.oled) == expect:
                    rec['first'] = s.now_s()
            sim.at(t, 'call', f)
            t += step
        return rec

    @staticmethod
    def ms(rec, t0):
        return None if rec['first'] is None else round(1000 * (rec['first'] - t0), 1)

    def clean(self, name, r):
        self.expect(name, not r['violations'], f'no contract violations ({r["violations"]})')

    # ------------------------------------------------------------------ scenarios
    def first_use_keys(self):
        s = self.sim(fram_fill=0x00)
        s.run(1.4)
        r = self.record('K1 blank FRAM first boot on USB', s)
        self.expect('K1', r['display'] == {'digits': '0', 'status': 'ERR'}, 'blank FRAM must show 0 ERR')
        s.press(1.5, 'rst', 0.30)
        s.run(2.5)
        r = self.record('K2 0.3 s reset tap does not clear ERR', s)
        self.expect('K2', r['display'] == {'digits': '0', 'status': 'ERR'}, 'a tap is not a reset')
        armed = self.watch(s, 2.6, 5.2, ('0', 'RST'))
        s.press(2.6, 'rst', 2.4)
        cleared = self.watch(s, 5.0, 5.8, ('0', ''))
        s.run(5.8)
        r = self.record('K3 2.4 s reset hold-and-release commits zero', s,
                        dict(latency_ms=dict(hold_to_RST_prompt=self.ms(armed, 2.6), release_to_clean_zero=self.ms(cleared, 5.0))))
        print('    latency', r['latency_ms'])
        self.expect('K3', r['display'] == {'digits': '0', 'status': ''} and r['fram']['journal']['latest']['fault'] == 0,
                    'reset after a >=2 s hold clears ERR')
        self.expect('K3', r['latency_ms']['hold_to_RST_prompt'] is not None and 2000 <= r['latency_ms']['hold_to_RST_prompt'] <= 2100,
                    'RST prompt appears 2.0-2.1 s into the hold')
        presses = [6.0 + i * 0.5 for i in range(5)]
        lats = [self.watch(s, t, t + 0.45, (str(i + 1), '')) for i, t in enumerate(presses)]
        for t in presses:
            s.press(t, 'inc', 0.12)
        s.run(9.0)
        r = self.record('K4 five presses', s, dict(latency_ms=dict(press_to_display=[self.ms(l, t) for l, t in zip(lats, presses)])))
        print('    latency', r['latency_ms'])
        self.expect('K4', r['display'] == {'digits': '5', 'status': ''}, 'five presses show 5')
        worst = max((x for x in r['latency_ms']['press_to_display'] if x is not None), default=None)
        self.expect('K4', worst is not None and worst < 100 and None not in r['latency_ms']['press_to_display'],
                    f'press-to-display < 100 ms with the display on (worst {worst})')
        # Increment wins: COUNT during a qualifying reset hold counts and cancels the reset.
        s.at(9.2, 'key', 'rst', True); s.press(10.0, 'inc', 0.1); s.at(11.8, 'key', 'rst', False)
        s.run(12.5)
        r = self.record('K5 COUNT during a 2.6 s reset hold', s)
        self.expect('K5', r['display'] == {'digits': '6', 'status': ''}, 'increment wins; no reset')
        s.at(12.6, 'key', 'inc', True); s.at(12.6004, 'key', 'rst', True)
        s.at(12.8, 'key', 'inc', False); s.at(15.2, 'key', 'rst', False)
        s.run(15.8)
        r = self.record('K6 both keys together, reset held on for 2.6 s', s)
        self.expect('K6', r['display'] == {'digits': '7', 'status': ''}, 'simultaneous press counts; the reset hold is cancelled')
        s.at(16.0, 'key', 'rst', True); s.at(27.0, 'key', 'rst', False)
        s.run(27.5)
        r = self.record('K7 reset held 11 s (abandoned)', s)
        self.expect('K7', r['display'] == {'digits': '7', 'status': ''}, 'a hold beyond 10 s never resets')
        return s

    def usb_sleep_and_nrst(self, base):
        s = self.sim(mem=base.fram.mem)
        s.run(1.5)
        s.run(40.0)
        r = self.record('U1 USB: 30 s inactivity -> display off, FRAM sleep, Stop, latch released', s)
        self.expect('U1', not r['oled']['powered'] and r['fram']['asleep'] and r['stop_entries'] >= 1 and r['board'] == 'on',
                    'USB keeps the board on in Stop')
        self.expect('U1', s.drives('B', 2) != 1, 'PWR_HOLD released in the USB-held Stop fallback')
        lat = self.watch(s, 41.0, 42.0, ('8', ''))
        s.press(41.0, 'inc', 0.12)
        s.run(42.0)
        r = self.record('U2 press from Stop (USB)', s, dict(latency_ms=dict(wake_press_to_AF=self.ms(lat, 41.0))))
        print('    latency', r['latency_ms'])
        self.expect('U2', r['display'] == {'digits': '8', 'status': ''}, 'first press after sleep counts')
        self.expect('U2', r['latency_ms']['wake_press_to_AF'] is not None and r['latency_ms']['wake_press_to_AF'] + 1000 * T_AF < 400,
                    'wake-to-lit < 400 ms from Stop')
        s.at(43.0, 'nrst')
        s.run(45.0)
        r = self.record('U3 NRST on USB returns the saved count without ERR', s)
        self.expect('U3', r['display'] == {'digits': '8', 'status': ''} and r['ram']['queue_dropped'] == 0, 'no ERR after reset')
        s.at(46.0, 'usb', False)
        s.run(47.0)
        r = self.record('U4 USB removed while awake: latch holds the board on battery', s)
        self.expect('U4', r['board'] == 'on', 'PWR_HOLD keeps the board on after USB removal')
        s.run(80.0)
        r = self.record('U5 battery: display timeout -> board powered off', s)
        self.expect('U5', r['board'] == 'off' and r['fram']['journal']['latest']['count'] == 8, 'auto power-off with the count saved')

    def boot_drain(self):
        out = {}
        for ws in (0.0, 0.5):
            for label, start in (('USB', 'usb'), ('COUNT key on battery', 'key')):
                s = self.sim(mem=full_journal(), flash_ws_penalty=ws, start=start, usb=False)
                s.profile_between('oled_init', 'input_take')
                lat = self.watch(s, 0.0, 1.2, ('1235' if start == 'key' else '1234', ''))
                s.run(1.2)
                key = f'96 valid records, {label}, flash penalty +{ws}'
                d = decode_display(s.oled)
                out[key] = dict(first_drain_ms=None if s.profile_end is None else round(1000 * s.profile_end, 1),
                                queue_dropped=ram_state(s)['queue_dropped'], display=d, to_AF_ms=self.ms(lat, 0.0))
                print(f'[boot] {key}: {out[key]}')
                self.expect('boot', out[key]['queue_dropped'] == 0 and d == ((('1235' if start == 'key' else '1234'), '')),
                            f'{key}: wrapped journal boots without ERR; the power-on press counts once')
                if start == 'key' and ws == 0.0:
                    self.expect('boot', lat['first'] is not None and self.ms(lat, 0.0) + 1000 * T_AF < 500,
                                'press-from-off to lit digits < 500 ms (from reset release)')
        self.results['boot_drain'] = out

    def battery_power(self):
        s = self.sim(mem=full_journal(count=500), start='key', usb=False, vbat=3.90)
        s.run(1.0)
        r = self.record('B1 COUNT from off on battery: powers on and counts the press', s)
        self.expect('B1', r['display'] == {'digits': '501', 'status': ''} and r['battery_bars'] == 3, 'wake press counts; 3 bars at 3.90 V')
        s.run(40.0)
        r = self.record('B2 inactivity -> power off', s)
        self.expect('B2', r['board'] == 'off' and not r['oled']['powered'], 'board off after timeout')
        lat = self.watch(s, 45.0, 46.2, ('502', ''))
        s.press(45.0, 'inc', 0.10)
        s.run(46.2)
        r = self.record('B3 next press powers on and counts', s, dict(latency_ms=dict(press_to_AF=self.ms(lat, 45.0))))
        print('    latency', r['latency_ms'])
        self.expect('B3', r['display'] == {'digits': '502', 'status': ''}, 'press from off counts once')
        s.run(80.0)
        s.press(85.0, 'inc', 0.010, bounce_ms=1.0, bounces=2)
        s.run(86.0)
        r = self.record('B4 10 ms tap from off is too short to latch U7', s)
        self.expect('B4', r['board'] == 'off' and r['fram']['journal']['latest']['count'] == 502, 'no power-on, no count')
        s.at(90.0, 'key', 'inc', True); s.at(135.0, 'key', 'inc', False)
        s.run(140.0)
        r = self.record('B5 COUNT held 45 s from off: one count, then off after release', s)
        self.expect('B5', r['board'] == 'off' and r['fram']['journal']['latest']['count'] == 503, 'held key counts once and the board still powers off')
        s.at(141.0, 'nrst')
        s.run(141.5)
        self.expect('B5', s.board_state == 'off', 'pinhole reset of an off board does nothing')

    def dfu(self):
        base = full_journal(count=77)
        cases = [
            ('D1 USB: hold RESET COUNT, then NRST pulse', [(2.0, 'key', 'rst', True), (3.5, 'nrst')]),
            ('D2 USB: NRST held, RESET COUNT pressed, NRST released', [(2.0, 'nrst_low'), (2.5, 'key', 'rst', True), (3.0, 'nrst_high')]),
            ('D3 USB: hold RESET COUNT for 5 s then NRST', [(2.0, 'key', 'rst', True), (7.0, 'nrst')])]
        for name, events in cases:
            s = self.sim(mem=base)
            s.run(1.5)
            for e in events:
                s.at(e[0], *e[1:])
            s.run(9.0)
            r = self.record(name, s)
            self.expect(name, r['dfu'] and r['fram']['journal']['latest']['count'] == 77, 'ROM DFU entered and saved count preserved')
        s = self.sim(mem=base, start='key', usb=False)
        s.run(1.5)
        s.at(2.0, 'key', 'rst', True); s.at(3.0, 'nrst')
        s.run(5.0)
        r = self.record('D4 battery only: NRST during a reset hold powers the board off', s)
        self.expect('D4', r['board'] == 'off' and r['fram']['journal']['latest']['count'] == 78,
                    'without USB, NRST releases the latch; the count is kept')

    def option_bytes(self):
        s = self.sim(mem=full_journal(count=321), optr=0x807000AA)
        s.run(2.0)
        s.press(2.2, 'inc', 0.1)
        s.run(3.0)
        r = self.record('O1 RM0376 factory option bytes: self-provision then count', s)
        self.expect('O1', r['optr'] == '0x807c00aa' and r['option_writes'] == 1 and r['display'] == {'digits': '322', 'status': ''},
                    'BOR_LEV programmed once, reloaded, then normal counting')
        s = self.sim(mem=full_journal(count=321), optr=0x806000AA)
        s.run(2.0)
        r = self.record('O2 unexpected WDG option: no guess, visible OPT diagnostic', s)
        self.expect('O2', r['option_writes'] == 0 and r['display'] == {'digits': '', 'status': 'OPT'} and r['fram']['writes'] == 0,
                    'no FRAM access; OPT shown with digits hidden')

    def fast_fidget(self):
        s = self.sim(mem=full_journal(count=1000))
        s.run(1.5)
        n, period = 100, 1 / 12.0
        for i in range(n):
            s.press(2.0 + i * period, 'inc', period * 0.45, bounce_ms=2.0, bounces=4)
        s.run(2.0 + n * period + 1.0)
        r = self.record('F1 100 bouncy presses at 12 Hz', s)
        self.expect('F1', r['display'] == {'digits': str(1000 + n), 'status': ''}, f'expected {1000 + n}')

    def low_battery(self):
        s = self.sim(mem=full_journal(count=40), start='key', usb=False, vbat=3.52)
        s.run(1.2)
        r = self.record('L1 3.52 V: LO label, empty gauge', s)
        self.expect('L1', r['display'] == {'digits': '41', 'status': 'LO'} and r['battery_bars'] == 0, 'LO below 3.55 V')
        s.press(1.5, 'inc', 0.1)
        s.at(2.0, 'vbat', 3.30)
        s.run(6.0)
        r = self.record('L2 3.30 V: LO shown, count saved, storage power-off', s)
        self.expect('L2', r['board'] == 'off' and r['fram']['journal']['latest']['count'] == 42, 'cut-off saves and powers off')
        s.press(7.0, 'inc', 0.1)
        s.run(9.5)
        r = self.record('L3 press at 3.30 V: counts, LO, then off again', s)
        self.expect('L3', r['board'] == 'off' and r['fram']['journal']['latest']['count'] == 43, 'still counts and protects the cell')
        s = self.sim(mem=full_journal(count=40), start='key', usb=False, vbat=3.30)
        s.at(0.5, 'usb', True); s.at(0.5, 'charge', 'charging')
        s.run(4.0)
        r = self.record('L4 USB connected to a low cell: stays on, CHG', s)
        self.expect('L4', r['board'] == 'on' and r['display'] == {'digits': '41', 'status': 'CHG'}, 'charging, no cut-off from SYS 4.5 V')

    def charging(self):
        s = self.sim(mem=full_journal(count=9), charge='charging')
        s.run(1.3)
        r = self.record('C1 USB charging: CHG label, gauge hidden', s)
        self.expect('C1', r['display'] == {'digits': '9', 'status': 'CHG'} and r['battery_bars'] is None, 'CHG while charging')
        s.at(1.5, 'charge', 'done')
        s.run(1.8)
        r = self.record('C2 charge complete/disabled: full gauge, no label', s)
        self.expect('C2', r['display'] == {'digits': '9', 'status': ''} and r['battery_bars'] == 4, 'full gauge')
        s.at(2.0, 'charge', 'fault')
        s.run(2.3)
        r = self.record('C3 charger fault: BAT label', s)
        self.expect('C3', r['display'] == {'digits': '9', 'status': 'BAT'}, 'BAT on charger fault')
        s.run(40.0)
        s.at(41.0, 'usb', False)
        s.run(41.5)
        r = self.record('C4 USB removed during Stop: board switches off', s)
        self.expect('C4', r['board'] == 'off', 'unplug in Stop powers off')

    def held_key_usb(self):
        s = self.sim(mem=full_journal(count=6))
        s.run(1.5)
        s.at(2.0, 'key', 'inc', True)
        s.run(40.0)
        r = self.record('H1 increment held 38 s (USB)', s)
        self.expect('H1', r['stop_entries'] >= 1 and r['fram']['journal']['latest']['count'] == 7, 'one count, then sleep while held')
        s.at(41.0, 'key', 'inc', False)
        s.run(42.0)
        s.press(43.0, 'inc', 0.1)
        s.run(45.0)
        r = self.record('H2 next press after release', s)
        self.expect('H2', r['display'] == {'digits': '8', 'status': ''}, 'release adds nothing; next press counts')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--elf', type=Path, default=DEFAULT_ELF)
    ap.add_argument('--output', type=Path)
    ap.add_argument('--check', action='store_true', help='fail on violated product expectations')
    a = ap.parse_args()
    t0 = time.time()
    suite = Suite(a.elf, a.check)
    base = suite.first_use_keys()
    suite.usb_sleep_and_nrst(base)
    suite.boot_drain()
    suite.battery_power()
    suite.dfu()
    suite.option_bytes()
    suite.fast_fidget()
    suite.low_battery()
    suite.charging()
    suite.held_key_usb()
    out = dict(schema=1, elf=str(a.elf.resolve().relative_to(ROOT)) if ROOT in a.elf.resolve().parents else str(a.elf),
               elf_sha256=hashlib.sha256(Path(a.elf).read_bytes()).hexdigest(),
               model='Instruction-level emulation with modelled peripherals and board power latch; not hardware execution',
               expectation_failures=suite.failures, scenarios=suite.results, wall_s=round(time.time() - t0, 1))
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(out, indent=1, default=str) + '\n')
    print(f'\n{len(suite.failures)} expectation failure(s); wall {out["wall_s"]} s')
    for f in suite.failures:
        print('  -', f)
    if a.check and suite.failures:
        sys.exit(1)


if __name__ == '__main__':
    main()
