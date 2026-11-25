#!/usr/bin/env python3
"""Tests for clicker_flash.py against the mock DfuSe device (and the real dfu-util if installed).

Run: python3 tools/clicker-flash/test_clicker_flash.py [--output report.json]
"""
import argparse
import contextlib
import csv
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import clicker_flash as cf  # noqa: E402

FLASH_192K = '@Internal Flash  /0x08000000/1536*128 g'
DEVICE = {'serial': '2067368F5041', 'path': '20-1', 'alts': {'0': FLASH_192K, '1': '@Option Bytes  /0x1FF80000/01*032 e'}}


class Env:
    def __init__(self, td, devices=None, faults=None):
        self.td = Path(td)
        self.state = self.td / 'state.json'
        self.state.write_text(json.dumps({'devices': devices if devices is not None else [dict(DEVICE)],
                                          'faults': faults or {}}))
        self.tool = self.td / 'dfu-util'
        self.tool.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{HERE / "mock_dfu_util.py"}" "$@"\n')
        self.tool.chmod(self.tool.stat().st_mode | stat.S_IEXEC)
        os.environ['MOCK_DFU_STATE'] = str(self.state)
        self.log = self.td / 'log.csv'

    def read(self):
        return json.loads(self.state.read_text())

    def flash(self, *extra, answers=()):
        answers = iter(answers)
        args = cf.build_parser().parse_args(['--dfu-util', str(self.tool), 'flash', '--timeout', '1', '--log', str(self.log), *extra])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            try:
                code = cf.cmd_flash(args, ask=lambda prompt: next(answers))
            except cf.FlashError as e:
                print('FAIL:', e); code = 2
        return code, out.getvalue()

    def rows(self):
        with self.log.open() as f:
            return list(csv.DictReader(f))


def image():
    return cf.load_image()[0]


CASES = []


def case(fn):
    CASES.append(fn)
    return fn


@case
def happy_path(td):
    env = Env(td)
    code, out = env.flash()
    st = env.read()
    dev = st['devices'][0]
    assert code == 0 and 'PASS' in out, out
    assert bytes.fromhex(dev['flash'])[:len(image())] == image()
    assert dev['app_started'] == 1 and dev['in_dfu'] is False
    row = env.rows()[0]
    assert row['result'] == 'PASS' and row['serial'] == DEVICE['serial'] and row['readback_sha256'] == row['image_sha256']
    dl = [c for c in st['calls'] if '-D' in c][0]
    assert dl[dl.index('-S') + 1] == DEVICE['serial'] and dl[dl.index('-s') + 1] == '0x08000000'
    ups = [c[c.index('-s') + 1] for c in st['calls'] if '-U' in c]
    # Verify first without leaving, then a separate 8-byte read that carries the leave.
    assert ups == [f'0x08000000:{len(image())}', '0x08000000:8:leave'], ups
    assert st['calls'].index(dl) < [i for i, c in enumerate(st['calls']) if '-U' in c][0]


@case
def corrupted_write_is_rejected_and_logged(td):
    env = Env(td, faults={'corrupt_write_offset': 1234})
    code, out = env.flash()
    assert code == 1 and 'VERIFY FAILED' in out and 'offset 0x4d2' in out, out
    assert env.rows()[0]['result'] == 'FAIL'
    dev = env.read()['devices'][0]
    # A corrupt image must never be started: the unit stays in DFU for a retry.
    assert dev.get('in_dfu', True) is True and not dev.get('app_started'), dev
    assert not any(':leave' in ' '.join(c) for c in env.read()['calls'])


@case
def download_error_is_reported(td):
    env = Env(td, faults={'download_exit': 74})
    code, out = env.flash()
    assert code == 1 and 'Download failed' in out, out
    assert not any('-U' in c for c in env.read()['calls'])


@case
def leave_error_after_verified_readback_passes_with_note(td):
    env = Env(td, faults={'leave_exit': 74})
    code, out = env.flash()
    row = env.rows()[0]
    assert code == 0 and row['result'] == 'PASS' and 'exit 74' in row['note'], (out, row)


@case
def two_devices_are_refused(td):
    second = dict(DEVICE, serial='2067368F5042', path='20-2')
    env = Env(td, devices=[dict(DEVICE), second])
    code, out = env.flash()
    assert code == 2 and 'More than one' in out, out
    assert not any('-D' in c for c in env.read()['calls'])


@case
def no_device_times_out_with_instructions(td):
    env = Env(td, devices=[])
    code, out = env.flash()
    assert code == 2 and 'pinhole' in out, out


@case
def non_writable_layout_is_refused(td):
    env = Env(td, devices=[dict(DEVICE, alts={'0': '@Internal Flash  /0x08000000/1536*128 a'})])
    code, out = env.flash()
    assert code == 1 and 'DfuSe layout' in out, out
    assert not any('-D' in c for c in env.read()['calls'])


@case
def not_a_rom_bootloader_is_refused(td):
    env = Env(td, devices=[dict(DEVICE, alts={'0': '@SPI Flash /0x90000000/64*4Kg'})])
    code, out = env.flash()
    assert code == 1 and 'Internal Flash' in out, out


@case
def unexpected_flash_size_warns_but_flashes(td):
    env = Env(td, devices=[dict(DEVICE, alts={'0': '@Internal Flash  /0x08000000/512*128 g'})])
    code, out = env.flash()
    assert code == 0 and 'WARNING' in out and '64 KiB' in out, out


@case
def kib_layout_syntax_is_parsed(td):
    label, segs = cf.parse_layout('@Internal Flash /0x08000000/4*001Ka,124*001Kg')
    assert label == 'Internal Flash' and segs[0]['end'] == 0x08001000 and not segs[0]['writable']
    assert segs[1]['start'] == 0x08001000 and segs[1]['end'] == 0x08020000 and segs[1]['writable']
    # The first 4 KiB are read-only here, so an image at 0x08000000 must be refused.
    try:
        cf.flash_alt({'alts': {0: '@Internal Flash /0x08000000/4*001Ka,124*001Kg'}}, 10196)
    except cf.FlashError as e:
        assert 'DfuSe layout' in str(e)
    else:
        raise AssertionError('read-only first pages accepted')


@case
def commissioning_answers_are_logged(td):
    env = Env(td)
    code, out = env.flash('--check', answers=['y', 'y', 'n', 'y'])
    row = env.rows()[0]
    assert code == 1 and row['result'] == 'FLASHED_CHECK_FAIL' and 'count=FAIL' in row['checks'], (out, row)


@case
def tampered_image_is_refused(td):
    build = Path(td) / 'build'
    shutil.copytree(cf.DEFAULT_BUILD, build)
    p = build / (cf.STEM + '.bin')
    data = bytearray(p.read_bytes()); data[100] ^= 1; p.write_bytes(data)
    try:
        cf.load_image(build)
    except cf.FlashError as e:
        assert 'does not match the build manifest' in str(e)
    else:
        raise AssertionError('tampered image accepted')


@case
def unrecorded_image_is_refused(td):
    p = Path(td) / 'other.bin'
    p.write_bytes(image())
    try:
        cf.load_image(cf.DEFAULT_BUILD, p)
    except cf.FlashError as e:
        assert 'not an output listed' in str(e)
    else:
        raise AssertionError('unrecorded image accepted')


@case
def bad_vector_table_is_refused(td):
    for offset, word, text in ((0, 0, 'stack pointer'), (4, 0x08000100, 'Reset vector'), (4, 0x08020001, 'Reset vector')):
        d = bytearray(image()); d[offset:offset + 4] = word.to_bytes(4, 'little')
        try:
            cf.check_vector_table(bytes(d))
        except cf.FlashError as e:
            assert text in str(e), e
        else:
            raise AssertionError('bad vector table accepted')


@case
def batch_flashes_successive_units(td):
    env = Env(td)
    st = env.read()
    st['devices'].append(dict(DEVICE, serial='2067368F5042', path='20-1', in_dfu=False))
    env.state.write_text(json.dumps(st))
    orig_wait = cf.wait_for_device
    calls = {'n': 0}

    def wait(tool, timeout, exclude=(), **kw):
        calls['n'] += 1
        if calls['n'] == 2:      # operator connects the second unit in DFU mode
            s = env.read(); s['devices'][1]['in_dfu'] = True; env.state.write_text(json.dumps(s))
        if calls['n'] == 3:
            raise KeyboardInterrupt
        return orig_wait(tool, timeout, exclude, **kw)
    cf.wait_for_device = wait
    try:
        try:
            env.flash('--batch')
        except KeyboardInterrupt:
            pass
    finally:
        cf.wait_for_device = orig_wait
    rows = env.rows()
    assert [r['serial'] for r in rows] == ['2067368F5041', '2067368F5042'] and all(r['result'] == 'PASS' for r in rows), rows


def step(env, *args):
    """Run one step-by-step command through main() and return (exit, RESULT dict, output)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cf.main(['--dfu-util', str(env.tool), *args])
    text = out.getvalue() + err.getvalue()
    results = [json.loads(l[7:]) for l in out.getvalue().splitlines() if l.startswith('RESULT ')]
    assert len(results) == 1, text
    return code, results[0], text


def writes(env):
    return [c for c in env.read().get('calls', []) if '-D' in c]


@case
def stepwise_first_article_sequence(td):
    env = Env(td)
    backups = Path(td) / 'backups'
    code, r, _ = step(env, 'wait', '--timeout', '1')
    assert code == 0 and r['serial'] == DEVICE['serial']
    code, r, _ = step(env, 'probe')
    assert code == 0 and r['ok'] and r['flash_kib'] == 192 and r['option_bytes_alt'] == 1
    code, r, _ = step(env, 'leave')
    assert code == 2 and 'vector table' in r['error'], r      # blank part: never jump into it
    code, r, _ = step(env, 'backup', '--out', str(backups))
    # The ROM descriptor says 192 KiB but the STM32L072CB has 128 KiB; erased STM32L0 Flash reads 0x00.
    assert code == 0 and r['contents'] == 'blank' and r['bytes'] == 128 * 1024 and Path(r['file']).is_file(), r
    assert r['option_bytes']['firmware_first_boot'].startswith('programs USER 0x807C'), r
    code, r, _ = step(env, 'verify-device')
    assert code == 1 and not r['ok'], r
    assert not writes(env), 'read-only steps must never download'
    assert env.read()['devices'][0].get('in_dfu', True) is True, 'read-only steps must not leave DFU'
    code, r, _ = step(env, 'flash', '--no-leave', '--timeout', '1', '--log', str(env.log))
    assert code == 0 and r['result'] == 'PASS' and r['leave_requested'] is False
    assert env.read()['devices'][0].get('in_dfu', True) is True
    code, r, _ = step(env, 'verify-device')
    assert code == 0 and r['ok'] and r['readback_sha256'] == r['image_sha256']
    code, r, _ = step(env, 'backup', '--out', str(backups))
    assert r['contents'] == 'q5-image'
    code, r, _ = step(env, 'leave')
    assert code == 0 and r['ok'] and env.read()['devices'][0]['app_started'] == 1
    assert len(writes(env)) == 1
    code, r, _ = step(env, 'record-check', '--serial', DEVICE['serial'], '--checks',
                      'blank=pass,reset=pass,count=pass,zero=pass', '--log', str(env.log))
    assert code == 0 and r['result'] == 'COMMISSIONED'
    code, r, _ = step(env, 'summary', '--log', str(env.log))
    assert r['units'] == {DEVICE['serial']: 'COMMISSIONED'} and r['rows'] == 2


@case
def stepwise_commands_refuse_ambiguity_and_absence(td):
    other = dict(DEVICE, serial='3A1F00000001', path='20-2')
    env = Env(td, devices=[dict(DEVICE), other])
    for cmd in ('probe', 'backup', 'verify-device', 'leave'):
        code, r, _ = step(env, cmd, *(['--out', str(Path(td) / 'b')] if cmd == 'backup' else []))
        assert code == 2 and not r['ok'] and 'More than one' in r['error'], (cmd, r)
    code, r, _ = step(env, 'probe', '--serial', other['serial'])
    assert code == 0 and r['serial'] == other['serial']
    env2 = Env(Path(td), devices=[])
    code, r, _ = step(env2, 'wait', '--timeout', '0.2')
    assert code == 2 and 'No STM32 DFU device' in r['error']
    assert not writes(env) and not writes(env2)


@case
def stepwise_probe_refuses_non_writable_layout(td):
    env = Env(td, devices=[dict(DEVICE, alts={'0': '@Internal Flash  /0x08000000/1536*128 a'})])
    code, r, _ = step(env, 'probe')
    assert code == 2 and 'DfuSe layout' in r['error']


@case
def flash_serial_filter_ignores_other_units(td):
    env = Env(td, devices=[dict(DEVICE)])
    code, r, _ = step(env, 'flash', '--serial', 'NOT-THIS-ONE', '--timeout', '0.3', '--log', str(env.log))
    assert code == 2 and not r['ok'] and not writes(env)


@case
def record_check_rejects_bad_input_and_logs_failures(td):
    env = Env(td)
    code, r, _ = step(env, 'record-check', '--serial', 'X', '--checks', 'blank=maybe', '--log', str(env.log))
    assert code == 2 and not env.log.exists()
    code, r, _ = step(env, 'record-check', '--serial', 'X', '--checks', 'blank=pass,reset=fail', '--log', str(env.log))
    assert code == 1 and r['result'] == 'FLASHED_CHECK_FAIL' and env.rows()[0]['checks'] == 'blank=pass;reset=FAIL'


@case
def backup_reads_only_the_real_128k(td):
    env = Env(td)
    code, r, _ = step(env, 'backup', '--out', str(Path(td) / 'b'))
    up = [c for c in env.read()['calls'] if '-U' in c and c[c.index('-a') + 1] == '0'][0]
    assert code == 0 and up[up.index('-s') + 1] == f'0x08000000:{128 * 1024}', up
    # A device that really has 192 KiB is still only read to 128 KiB (the Q5 part).
    other = Path(td) / 'x'; other.mkdir()
    env2 = Env(other, devices=[dict(DEVICE, flash_bytes=192 * 1024)])
    code, r, _ = step(env2, 'backup', '--out', str(Path(td) / 'b2'))
    assert code == 0 and r['bytes'] == 128 * 1024


@case
def read_protected_part_fails_reads_and_is_never_written(td):
    # RDP level 1: same descriptor (AN3156), but every read, erase and write fails.
    env = Env(td, devices=[dict(DEVICE, rdp1=True)])
    backups = Path(td) / 'b'
    code, r, _ = step(env, 'probe')
    assert code == 0                                   # the layout alone cannot reveal RDP
    for cmd in ('backup', 'verify-device', 'leave'):
        code, r, _ = step(env, cmd, *(['--out', str(backups)] if cmd == 'backup' else []))
        assert code == 2 and not r['ok'] and 'read-protected' in r['error'] + _, (cmd, r)
    assert not backups.exists() or not any(backups.iterdir()), 'no partial backup file may be saved'
    code, out = env.flash()
    assert code == 1 and 'Download failed' in out and 'pinhole' in out, out
    calls = env.read()['calls']
    assert not any(':leave' in ' '.join(c) for c in calls)
    assert not any(a in c for c in calls for a in (':force', ':unprotect', ':mass-erase')), calls


@case
def only_flash_downloads_and_nothing_writes_option_bytes(td):
    env = Env(td)
    for cmd in (['wait', '--timeout', '1'], ['probe'], ['backup', '--out', str(Path(td) / 'b')], ['verify-device'],
                ['list'], ['doctor']):
        try:
            step(env, *cmd)
        except AssertionError:      # list/doctor print no RESULT line
            pass
    assert not writes(env)
    step(env, 'flash', '--no-leave', '--timeout', '1', '--log', str(env.log))
    step(env, 'leave')
    calls = env.read()['calls']
    assert len(writes(env)) == 1
    for c in calls:
        if '-a' in c and env.read()['devices'][0]['alts'].get(c[c.index('-a') + 1], '').startswith('@Option Bytes'):
            assert '-U' in c and '-D' not in c and ':leave' not in ' '.join(c), c
        assert not any(x in ' '.join(c) for x in (':force', ':unprotect', ':mass-erase', '-E', '-R')), c


@case
def rom_descriptor_of_128k_is_accepted_without_warning(td):
    env = Env(td, devices=[dict(DEVICE, alts={'0': '@Internal Flash  /0x08000000/1024*128 g'})])
    code, r, _ = step(env, 'probe')
    assert code == 0 and r['ok'] and r['flash_kib'] == 128 and not r['warnings'], r


@case
def image_limit_is_bank1_of_the_128k_part(td):
    assert cf.BANK1_BYTES == 0x08010000 - cf.FLASH_BASE
    d = bytearray(64 * 1024 + 4); d[0:8] = bytes(image()[0:8])
    try:
        cf.check_vector_table(bytes(d))
    except cf.FlashError as e:
        assert 'Bank 1' in str(e)
    else:
        raise AssertionError('image past Bank 1 accepted')


@case
def option_byte_decoding_predicts_first_boot(td):
    def words(w0, w1):
        return w0.to_bytes(4, 'little') + w1.to_bytes(4, 'little')
    factory = cf.decode_option_bytes(words(0xFF5500AA, 0x7F8F8070))
    assert factory['rdp_level'] == 0 and factory['complements_valid'] and factory['firmware_first_boot'].startswith('programs')
    done = cf.decode_option_bytes(words(0xFF5500AA, 0x7F83807C))
    assert done['firmware_first_boot'] == 'already provisioned' and done['bor_lev'] == '0xc' and done['nboot1']
    torn = cf.decode_option_bytes(words(0xFF5500AA, 0x00000000))
    assert not torn['complements_valid'] and torn['firmware_first_boot'].startswith('OPT')
    rdp1 = cf.decode_option_bytes(words(0xFFFF0000, 0x7F8F8070))   # RDP byte 0x00: level 1
    assert rdp1['rdp_level'] == 1 and rdp1['firmware_first_boot'].startswith('OPT')
    wdg = cf.decode_option_bytes(words(0xFF5500AA, 0x7F9F8060))
    assert wdg['firmware_first_boot'].startswith('OPT (unexpected')


def real_dfu_util_accepts_arguments():
    """With no device attached, the real dfu-util must fail on 'no device', never on usage."""
    tool = shutil.which('dfu-util')
    if not tool:
        return {'skipped': 'dfu-util not installed'}
    # Never send real commands (one of them is a DOWNLOAD) while any DFU device is attached:
    # only the serial filter would stand between this test and a real board.
    if cf.list_devices(tool):
        return {'skipped': 'a DFU device is attached; real dfu-util argument check not run'}
    results = {}
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / 'i.bin'; src.write_bytes(image())
        dev = {'serial': '2067368F5041', 'path': '1-1'}
        for name, extra in (('download', ['-s', '0x08000000', '-D', str(src)]),
                            ('upload_leave', ['-s', f'0x08000000:{len(image())}:leave', '-U', str(Path(td) / 'r.bin')]),
                            ('upload_verify', ['-s', f'0x08000000:{len(image())}', '-U', str(Path(td) / 'v.bin')]),
                            ('upload_leave8', ['-s', '0x08000000:8:leave', '-U', str(Path(td) / 'l.bin')]),
                            ('upload_backup', ['-s', f'0x08000000:{128 * 1024}', '-U', str(Path(td) / 'b.bin')])):
            p = subprocess.run([tool] + cf.select_args(dev, 0) + extra, capture_output=True, text=True)
            out = p.stdout + p.stderr
            assert p.returncode != 64 and 'No DFU capable USB device available' in out, (name, p.returncode, out)
            results[name] = {'exit': p.returncode, 'message': 'No DFU capable USB device available'}
        # Option-byte read used by `backup` (alt 1, read-only upload of the first two words).
        p = subprocess.run([tool] + cf.select_args(dev, 1) + ['-s', f'0x{cf.OPTION_BASE:08x}:8', '-U', str(Path(td) / 'o.bin')],
                           capture_output=True, text=True)
        assert p.returncode != 64 and 'No DFU capable USB device available' in p.stdout + p.stderr, p
        results['upload_option_bytes'] = {'exit': p.returncode, 'message': 'No DFU capable USB device available'}
        results['version'] = cf.dfu_version(tool)
        results['list_parses'] = cf.list_devices(tool) == []
    return results


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--output', type=Path)
    a = ap.parse_args()
    passed = []
    for fn in CASES:
        with tempfile.TemporaryDirectory() as td:
            fn(td)
        passed.append(fn.__name__)
        print('PASS', fn.__name__)
    real = real_dfu_util_accepts_arguments()
    print('real dfu-util:', real)
    report = {'schema': 1, 'tool_sha256': cf.sha256((HERE / 'clicker_flash.py').read_bytes()),
              'mock_sha256': cf.sha256((HERE / 'mock_dfu_util.py').read_bytes()),
              'test_sha256': cf.sha256(Path(__file__).read_bytes()),
              'image_sha256': cf.sha256(image()), 'passed': passed, 'real_dfu_util': real,
              'hardware_executed': False,
              'limits': 'Mock DfuSe device reproduces dfu-util 0.11 CLI semantics only; no USB transfer, ROM bootloader or macOS libusb behaviour is exercised.'}
    if a.output:
        a.output.write_text(json.dumps(report, indent=2) + '\n')
    print(f'{len(passed)} cases passed')


if __name__ == '__main__':
    main()
