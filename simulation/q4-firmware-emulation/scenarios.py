#!/usr/bin/env python3
"""Scenario suite for the Q4 firmware emulation (model limits: see q4emu.py / README.md).

Runs the real firmware ELF through board-level scenarios and reports display
contents, FRAM journal state, timing and contract violations.  With --check,
the behaviours the product documents as required are asserted (exit status 1
on failure); informational scenarios are reported but never fail the run.
"""
import argparse
import json
import struct
import sys
import time
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from q4emu import Sim, summary, decode_display, fram_journal  # noqa: E402

DEFAULT_ELF = ROOT / 'firmware/q4-stm32/build/count-fidget-Q4-stm32.elf'


def full_journal(count=1234, nvalid=96, seq0=1000):
    """FRAM image with every one of the 96 journal slots holding a valid record (steady state
    after the journal has wrapped once, i.e. after ~96 committed changes)."""
    mem = bytearray(32768)
    for i in range(nvalid):
        seq = seq0 + i
        c = count - (nvalid - 1 - i)
        w = [0x51443401, seq, c, 0, (~seq) & 0xFFFFFFFF, (~c) & 0xFFFFFFFF, 0, 0x434d5434]
        w[6] = zlib.crc32(struct.pack('<6I', *w[:6])) & 0xFFFFFFFF
        struct.pack_into('<8I', mem, i * 32, *w)
    return mem


def ram_state(s):
    q, a = s.symbols['inputs'], s.symbols['app']
    m = bytes(s.uc.mem_read(q + 0x808, 8))
    app = bytes(s.uc.mem_read(a, 0x6c))
    return dict(queue_dropped=struct.unpack_from('<H', m, 4)[0], input_fault=bool(app[28]),
                journal_fault=bool(app[44]), counter=struct.unpack_from('<I', app, 0)[0])


class Suite:
    def __init__(self, elf, check):
        self.elf, self.check = str(elf), check
        self.results, self.failures = {}, []

    def expect(self, name, ok, detail):
        if not ok:
            self.failures.append(f'{name}: {detail}')
            print(f'    EXPECTATION FAILED: {detail}')

    def record(self, name, sim, extra=None, informational=False):
        r = summary(sim, name)
        r['ram'] = ram_state(sim)
        r['informational'] = informational
        if extra: r.update(extra)
        self.results[name] = r
        print(f"[{name}] t={r['t']}s display={r['display']} halted={r['halted']} "
              f"journal={r['fram']['journal']['latest']} dropped={r['ram']['queue_dropped']} stops={r['stop_entries']}")
        for v in r['violations']:
            print('    note/violation:', v)
        return r

    def watch(self, sim, start, stop, expect, step=0.005):
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

    def clone(self, base, **kw):
        s = Sim(self.elf, **kw)
        s.fram.mem[:] = base.fram.mem
        return s

    # ---------------------------------------------------------------- scenarios
    def first_use_counting_sleep_reset(self):
        s = Sim(self.elf, fram_fill=0x00)
        s.run(1.4)
        r = self.record('S1a blank FRAM first boot', s)
        self.expect('S1a', r['display'] == {'digits': '0', 'status': 'ERR'}, 'blank FRAM must show 0 ERR (uncertain first use)')
        s.press(1.5, 'rst', 0.25)
        lat_reset = self.watch(s, 1.5, 3.0, ('0', ''))
        presses = [3.0 + i for i in range(5)]
        lats = [self.watch(s, t, t + 0.9, (str(i + 1), '')) for i, t in enumerate(presses)]
        for t in presses:
            s.press(t, 'inc', 0.12)
        s.run(8.5)
        r = self.record('S1b count reset then 5 presses', s, dict(latency_ms=dict(
            reset_to_clean_zero=self.ms(lat_reset, 1.5), press_to_display=[self.ms(l, t) for l, t in zip(lats, presses)])))
        print('    latency', r['latency_ms'])
        self.expect('S1b', r['display'] == {'digits': '5', 'status': ''}, 'five presses after reset must show 5')
        s.run(45.0)
        r = self.record('S2a 30 s inactivity -> display off, FRAM sleep, Stop', s)
        self.expect('S2a', not r['oled']['powered'] and r['fram']['asleep'] and r['stop_entries'] >= 1,
                    'module unpowered, FRAM asleep, MCU in Stop')
        t = 50.0
        lat = self.watch(s, t, t + 3.0, ('6', ''))
        s.press(t, 'inc', 0.12)
        s.run(t + 3.0)
        r = self.record('S2b press from Stop', s, dict(latency_ms=dict(wake_press_to_display=self.ms(lat, t))))
        print('    latency', r['latency_ms'])
        self.expect('S2b', r['display'] == {'digits': '6', 'status': ''}, 'first press after sleep counts')
        s.run(90.0)
        self.record('S2c asleep again', s)
        lat = self.watch(s, 95.0, 97.5, ('6', ''))
        s.at(95.0, 'nrst')
        s.run(97.5)
        r = self.record('S3 NRST while FRAM sleeps (warm reset)', s,
                        dict(latency_ms=dict(nrst_to_display=self.ms(lat, 95.0))))
        self.expect('S3', r['display'] == {'digits': '6', 'status': ''} and not r['ram']['input_fault'],
                    'saved count must return without ERR after NRST')
        return s

    def boot_drain(self):
        """Time from reset to the first foreground drain of the 255-sample input queue."""
        out = {}
        for label, mem in (('few records', None), ('96 valid records (wrapped)', full_journal())):
            for ws in (0.0, 0.5):
                if mem is None:
                    b = Sim(self.elf); b.run(1.2); b.press(1.3, 'rst', 0.2); b.run(2.0); m = b.fram.mem
                else:
                    m = mem
                s = Sim(self.elf, flash_ws_penalty=ws)
                s.fram.mem[:] = m
                s.profile_between('oled_init', 'input_take')
                s.run(1.5)
                st = ram_state(s)
                key = f'{label}, flash penalty +{ws} cycle/instr'
                out[key] = dict(first_drain_ms=None if s.profile_end is None else round(1000 * s.profile_end, 1),
                                queue_dropped=st['queue_dropped'], input_fault=st['input_fault'],
                                journal_fault=st['journal_fault'], display=decode_display(s.oled))
                print(f'[boot] {key}: {out[key]}')
                self.expect('boot', st['queue_dropped'] == 0 and not st['input_fault'],
                            f'{key}: boot must not overflow the input queue / latch ERR')
        self.results['boot_drain'] = out

    def dfu_entry(self, base):
        cases = [
            ('S4 DFU as documented: hold count-reset, then NRST', [(2.0, 'key', 'rst', True), (3.5, 'nrst_low'), (3.7, 'nrst_high')], True),
            ('S4b hold count-reset while plugging USB, battery attached (no MCU reset)', [(2.0, 'key', 'rst', True)], True),
            ('S5 DFU with NRST held first, then count-reset, then release NRST', [(2.0, 'nrst_low'), (2.5, 'key', 'rst', True), (3.0, 'nrst_high')], False)]
        for name, events, informational in cases:
            s = self.clone(base)
            s.run(1.5)
            before = fram_journal(s.fram)['latest']
            for e in events:
                s.at(e[0], *e[1:])
            s.run(6.0)
            r = self.record(name, s, dict(journal_before=before), informational=informational)
            print('    journal before', before, 'after', r['fram']['journal']['latest'])
            if not informational:
                self.expect(name, r['dfu'] and r['fram']['journal']['latest']['count'] == before['count'],
                            'ROM DFU entered and saved count preserved')

    def option_bytes(self, base):
        s = self.clone(base, optr=0x807000AA)
        s.run(3.0)
        s.press(3.5, 'inc', 0.12)
        s.run(6.0)
        self.record('S6 RM0376 factory option bytes (BOR_LEV not provisioned)', s, informational=True)

    def fast_fidget(self, base):
        s = self.clone(base)
        s.run(1.5)
        n, period = 100, 1 / 12.0
        for i in range(n):
            s.press(2.0 + i * period, 'inc', period * 0.45, bounce_ms=2.0, bounces=4)
        s.run(2.0 + n * period + 1.5)
        r = self.record('S7 100 bouncy presses at 12 Hz', s)
        self.expect('S7', r['display'] == {'digits': str(6 + n), 'status': ''}, f'expected {6 + n}')

    def low_rail(self, base):
        s = self.clone(base, vlogic=3.05)
        s.run(2.0)
        r = self.record('S8a VLOGIC 3.05 V (below 3.08 V enable)', s)
        self.expect('S8a', not r['oled']['powered'], 'display stays off below threshold')
        s.press(2.2, 'inc', 0.12)
        s.run(3.0)
        r = self.record('S8b press at 3.05 V', s)
        self.expect('S8b', r['fram']['journal']['latest']['count'] == 7, 'count persists with display off')
        s.at(3.2, 'vlogic', 3.20)
        s.run(5.0)
        r = self.record('S8c rail restored to 3.20 V', s)
        self.expect('S8c', r['display'] == {'digits': '7', 'status': ''}, 'display returns with count 7')

    def held_key(self, base):
        s = self.clone(base)
        s.run(1.5)
        s.at(2.0, 'key', 'inc', True)
        s.run(40.0)
        r = self.record('S9a increment held 38 s', s)
        self.expect('S9a', r['stop_entries'] >= 1 and r['fram']['journal']['latest']['count'] == 7,
                    'one count, then sleep while held')
        s.at(41.0, 'key', 'inc', False)
        s.run(42.0)
        self.record('S9b released while asleep', s)
        s.press(43.0, 'inc', 0.1)
        s.run(45.0)
        r = self.record('S9c next press', s)
        self.expect('S9c', r['display'] == {'digits': '8', 'status': ''}, 'release adds nothing; next press counts')

    def both_keys(self, base):
        s = self.clone(base)
        s.run(1.5)
        s.at(2.0, 'key', 'inc', True); s.at(2.0005, 'key', 'rst', True)
        s.at(2.3, 'key', 'inc', False); s.at(2.3, 'key', 'rst', False)
        s.run(4.0)
        r = self.record('S10 both keys together', s)
        self.expect('S10', r['display'] == {'digits': '0', 'status': ''}, 'reset has priority')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--elf', type=Path, default=DEFAULT_ELF)
    ap.add_argument('--output', type=Path)
    ap.add_argument('--check', action='store_true', help='fail on violated product expectations')
    a = ap.parse_args()
    t0 = time.time()
    suite = Suite(a.elf, a.check)
    base = suite.first_use_counting_sleep_reset()
    suite.boot_drain()
    suite.dfu_entry(base)
    suite.option_bytes(base)
    suite.fast_fidget(base)
    suite.low_rail(base)
    suite.held_key(base)
    suite.both_keys(base)
    import hashlib
    out = dict(schema=1, elf=str(a.elf.resolve().relative_to(ROOT)) if ROOT in a.elf.resolve().parents else str(a.elf),
               elf_sha256=hashlib.sha256(Path(a.elf).read_bytes()).hexdigest(),
               model='Instruction-level emulation with modelled peripherals; not hardware execution',
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
