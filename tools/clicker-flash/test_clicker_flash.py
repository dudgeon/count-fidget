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
    up = [c for c in st['calls'] if '-U' in c][0]
    assert up[up.index('-s') + 1] == f'0x08000000:{len(image())}:leave'


@case
def corrupted_write_is_rejected_and_logged(td):
    env = Env(td, faults={'corrupt_write_offset': 1234})
    code, out = env.flash()
    assert code == 1 and 'VERIFY FAILED' in out and 'offset 0x4d2' in out, out
    assert env.rows()[0]['result'] == 'FAIL'


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
def read_protected_layout_is_refused(td):
    env = Env(td, devices=[dict(DEVICE, alts={'0': '@Internal Flash  /0x08000000/1536*128 a'})])
    code, out = env.flash()
    assert code == 1 and 'read protection' in out, out
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
        assert 'read protection' in str(e)
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


def real_dfu_util_accepts_arguments():
    """With no device attached, the real dfu-util must fail on 'no device', never on usage."""
    tool = shutil.which('dfu-util')
    if not tool:
        return {'skipped': 'dfu-util not installed'}
    results = {}
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / 'i.bin'; src.write_bytes(image())
        dev = {'serial': '2067368F5041', 'path': '1-1'}
        for name, extra in (('download', ['-s', '0x08000000', '-D', str(src)]),
                            ('upload_leave', ['-s', f'0x08000000:{len(image())}:leave', '-U', str(Path(td) / 'r.bin')])):
            p = subprocess.run([tool] + cf.select_args(dev, 0) + extra, capture_output=True, text=True)
            out = p.stdout + p.stderr
            assert p.returncode != 64 and 'No DFU capable USB device available' in out, (name, p.returncode, out)
            results[name] = {'exit': p.returncode, 'message': 'No DFU capable USB device available'}
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
