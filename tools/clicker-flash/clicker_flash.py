#!/usr/bin/env python3
"""Flash Count Fidget Q5 clickers over USB-C from a Mac (or Linux) with dfu-util.

The STM32L072 ROM bootloader exposes USB DFU (ST "DfuSe"); no drivers and no
application USB stack are needed. This tool:

  1. verifies the firmware image against the committed build manifest
     (size, SHA-256, vector table, Flash Bank 1 limits);
  2. waits for exactly one STM32 DFU device and checks its flash layout;
  3. downloads the image to 0x08000000;
  4. reads the same range back and compares it byte for byte;
  5. leaves DFU (the application starts) and appends a line to a unit log;
  6. optionally records the operator's on-device commissioning checks.

Standard library only. Requires dfu-util >= 0.9 (Homebrew: `brew install dfu-util`).
Run `clicker_flash.py --help` or see tools/clicker-flash/README.md.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BUILD = ROOT / 'firmware/q5-stm32/build'
STEM = 'count-fidget-Q5-stm32'
ST_DFU = (0x0483, 0xDF11)
FLASH_BASE = 0x08000000
BANK1_BYTES = 96 * 1024          # STM32L072CB: 192 KiB in two 96 KiB banks
RAM_BASE, RAM_BYTES = 0x20000000, 20 * 1024
DEFAULT_LOG = Path.home() / 'count-fidget-flash-log.csv'
LOG_FIELDS = ['utc', 'serial', 'usb_path', 'result', 'image_sha256', 'image_bytes',
              'readback_sha256', 'dfu_util', 'checks', 'note']
COMMISSIONING = [
    ('blank', 'After the flash the display shows "0" with ERR (new FRAM) or the previous count'),
    ('reset', 'Hold RESET 2 s: RST appears; release: the display shows 0 without ERR'),
    ('count', 'Press COUNT three times: the display shows 3; the battery icon or CHG is visible'),
    ('zero', 'Hold RESET 2 s and release: the display shows 0'),
]
FOUND = re.compile(r'Found (DFU|Runtime): \[([0-9a-fA-F]{4}):([0-9a-fA-F]{4})\] ver=([0-9a-fA-F]{4}), devnum=(\d+), '
                   r'cfg=(\d+), intf=(\d+), path="([^"]*)", alt=(\d+), name="([^"]*)", serial="([^"]*)"')


class FlashError(Exception):
    pass


# ---------------------------------------------------------------- image checks

def sha256(data):
    return hashlib.sha256(data).hexdigest()


def load_image(build_dir=DEFAULT_BUILD, image=None):
    """Return (bytes, info) after checking the image against build-manifest.json."""
    build_dir = Path(build_dir)
    manifest_path = build_dir / 'build-manifest.json'
    if not manifest_path.is_file():
        raise FlashError(f'No build manifest at {manifest_path}')
    manifest = json.loads(manifest_path.read_text())
    if manifest.get('target') != 'STM32L072CBT6':
        raise FlashError(f"Manifest target is {manifest.get('target')!r}, expected STM32L072CBT6")
    image = Path(image) if image else build_dir / (STEM + '.bin')
    record = manifest.get('outputs', {}).get(image.name)
    if record is None:
        raise FlashError(f'{image.name} is not an output listed in {manifest_path.name}; refusing an unrecorded image')
    data = image.read_bytes()
    if len(data) != record['bytes'] or sha256(data) != record['sha256']:
        raise FlashError(f'{image.name} does not match the build manifest (size or SHA-256 differs); rebuild or re-checkout')
    check_vector_table(data)
    validation = manifest.get('validation', {})
    if validation.get('bank1_only') is False or validation.get('elf_hex_bin_equal') is False:
        raise FlashError('Build manifest records a failed image validation')
    return data, {'path': str(image), 'bytes': len(data), 'sha256': sha256(data),
                  'manifest_sha256': sha256(manifest_path.read_bytes())}


def check_vector_table(data):
    if len(data) < 8 or len(data) % 4:
        raise FlashError('Image is too short or not word aligned')
    if len(data) > BANK1_BYTES:
        raise FlashError(f'Image is {len(data)} bytes; the Q5 firmware must fit Flash Bank 1 ({BANK1_BYTES} bytes)')
    sp, reset = struct.unpack_from('<II', data, 0)
    if not (RAM_BASE < sp <= RAM_BASE + RAM_BYTES) or sp % 8:
        raise FlashError(f'Initial stack pointer 0x{sp:08x} is not an 8-byte-aligned SRAM address')
    if not reset & 1 or not FLASH_BASE <= (reset & ~1) < FLASH_BASE + len(data):
        raise FlashError(f'Reset vector 0x{reset:08x} is not a Thumb address inside the image')


# ---------------------------------------------------------------- dfu-util

def dfu_util_path(explicit=None):
    path = explicit or os.environ.get('DFU_UTIL') or shutil.which('dfu-util')
    if not path:
        hint = 'brew install dfu-util' if sys.platform == 'darwin' else 'install dfu-util (e.g. apt install dfu-util)'
        raise FlashError(f'dfu-util not found; {hint}')
    return path


def run(cmd, timeout=120):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise FlashError(f'Timed out: {" ".join(cmd)}')
    return p.returncode, p.stdout + p.stderr


def dfu_version(tool):
    code, out = run([tool, '--version'], timeout=20)
    m = re.search(r'dfu-util (\d+)\.(\d+)', out)
    if not m:
        raise FlashError(f'Could not read the dfu-util version from: {out.strip()[:200]}')
    major, minor = int(m.group(1)), int(m.group(2))
    if (major, minor) < (0, 9):
        raise FlashError(f'dfu-util {major}.{minor} is too old; 0.9 or later is required')
    return f'{major}.{minor}'


def list_devices(tool):
    """Return {(path, serial): {'alts': {alt: name}, ...}} for ST DFU interfaces."""
    _, out = run([tool, '-l'], timeout=30)
    devices = {}
    for m in FOUND.finditer(out):
        kind, vid, pid, ver, devnum, cfg, intf, path, alt, name, serial = m.groups()
        if (int(vid, 16), int(pid, 16)) != ST_DFU or kind != 'DFU':
            continue
        d = devices.setdefault((path, serial), {'path': path, 'serial': serial, 'ver': ver, 'devnum': devnum, 'alts': {}})
        d['alts'][int(alt)] = name
    return list(devices.values())


def parse_layout(name):
    """Parse a DfuSe alt name, e.g. '@Internal Flash  /0x08000000/1536*128 g'."""
    m = re.match(r'@([^/]*)/0x([0-9a-fA-F]+)/(.*)$', name.strip())
    if not m:
        raise FlashError(f'Unrecognised DfuSe memory layout {name!r}')
    label, address, sectors = m.group(1).strip(), int(m.group(2), 16), m.group(3)
    segments, cursor = [], address
    for part in sectors.split(','):
        s = re.match(r'\s*(\d+)\*(\d+)\s*([ KMB])?([a-g])', part)
        if not s:
            raise FlashError(f'Unrecognised DfuSe sector description {part!r}')
        count, size, unit, mode = int(s.group(1)), int(s.group(2)), (s.group(3) or ' '), s.group(4)
        size *= {' ': 1, 'B': 1, 'K': 1024, 'M': 1024 * 1024}[unit]
        segments.append({'start': cursor, 'end': cursor + count * size, 'page': size,
                         'readable': mode in 'aceg', 'erasable': mode in 'bcfg', 'writable': mode in 'defg'})
        cursor += count * size
    return label, segments


def flash_alt(device, image_len):
    for alt, name in sorted(device['alts'].items()):
        if not name.startswith('@Internal Flash'):
            continue
        _, segments = parse_layout(name)
        covered = [s for s in segments if s['start'] < FLASH_BASE + image_len and s['end'] > FLASH_BASE]
        if segments[0]['start'] != FLASH_BASE:
            raise FlashError(f'Flash alt {alt} starts at 0x{segments[0]["start"]:08x}, not 0x{FLASH_BASE:08x}')
        if segments[-1]['end'] < FLASH_BASE + image_len or not covered:
            raise FlashError('Device flash is smaller than the image')
        if not all(s['readable'] and s['erasable'] and s['writable'] for s in covered):
            raise FlashError('Flash pages for the image are not readable/erasable/writable (read protection set?)')
        warnings = []
        if segments[-1]['end'] - FLASH_BASE != 192 * 1024:
            warnings.append(f'device reports {(segments[-1]["end"] - FLASH_BASE) // 1024} KiB flash, '
                            'expected 192 KiB for STM32L072CB: check this is a Count Fidget Q5 board')
        return alt, warnings
    raise FlashError('No "@Internal Flash" DfuSe interface: this is not the STM32 ROM bootloader')


def wait_for_device(tool, timeout, exclude=(), poll=0.5, say=print):
    deadline = time.monotonic() + timeout
    announced = False
    while True:
        devices = [d for d in list_devices(tool) if (d['path'], d['serial']) not in exclude]
        if len(devices) > 1:
            raise FlashError('More than one STM32 DFU device is connected; connect one clicker at a time')
        if devices:
            return devices[0]
        if time.monotonic() >= deadline:
            raise FlashError('No STM32 DFU device found. With USB connected: hold RESET, press and release the '
                             'pinhole, then release RESET (see tools/clicker-flash/README.md)')
        if not announced:
            say('Waiting for a clicker in DFU mode (hold RESET, click the pinhole, release RESET)...')
            announced = True
        time.sleep(poll)


def wait_for_departure(tool, device, timeout=10, poll=0.5):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not any((d['path'], d['serial']) == (device['path'], device['serial']) for d in list_devices(tool)):
            return True
        time.sleep(poll)
    return False


def select_args(device, alt):
    args = ['-d', f'{ST_DFU[0]:04x}:{ST_DFU[1]:04x}', '-a', str(alt)]
    if device['serial'] and device['serial'] != 'UNKNOWN':
        args += ['-S', device['serial']]     # the ROM derives it from the unique device ID
    elif device['path']:
        args += ['-p', device['path']]
    return args


def flash_device(tool, device, image, leave=True, say=print):
    alt, warnings = flash_alt(device, len(image))
    for w in warnings:
        say('WARNING: ' + w)
    with tempfile.TemporaryDirectory(prefix='clicker-flash-') as td:
        src = Path(td) / 'image.bin'
        src.write_bytes(image)
        say(f'Writing {len(image)} bytes to 0x{FLASH_BASE:08x} on {device["serial"] or device["path"]}...')
        code, out = run([tool] + select_args(device, alt) + ['-s', f'0x{FLASH_BASE:08x}', '-D', str(src)], timeout=180)
        if code != 0 or re.search(r'(?i)error during download|status is not ok|cannot open device', out):
            raise FlashError('Download failed:\n' + tail(out))
        back = Path(td) / 'readback.bin'        # dfu-util refuses to overwrite: path must not exist
        opts = f'0x{FLASH_BASE:08x}:{len(image)}' + (':leave' if leave else '')
        say('Reading back and comparing...')
        code, out = run([tool] + select_args(device, alt) + ['-s', opts, '-U', str(back)], timeout=180)
        if not back.is_file():
            raise FlashError('Read-back produced no file:\n' + tail(out))
        readback = back.read_bytes()
        if readback != image:
            first = next((i for i, (a, b) in enumerate(zip(readback, image)) if a != b), min(len(readback), len(image)))
            raise FlashError(f'VERIFY FAILED: read-back differs from the image at offset 0x{first:x} '
                             f'({len(readback)} bytes read). Do not ship this unit; re-flash it.')
        if code != 0 and not leave:
            raise FlashError('Read-back reported an error:\n' + tail(out))
        # With :leave the ROM jumps to the application and may drop off the bus before
        # answering the final status request, so a non-zero exit after a verified
        # read-back is expected on some hosts (libusb pipe/timeout errors).
        return sha256(readback), (code, tail(out))


def tail(text, lines=12):
    return '\n'.join(text.strip().splitlines()[-lines:])


# ---------------------------------------------------------------- logging

def append_log(path, row):
    path = Path(path)
    new = not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', newline='') as f:
        w = csv.DictWriter(f, fieldnames=LOG_FIELDS)
        if new:
            w.writeheader()
        w.writerow({k: row.get(k, '') for k in LOG_FIELDS})


def commissioning(ask):
    results = {}
    print('\nOn-device commissioning (answer y/n; s to skip the rest):')
    for key, text in COMMISSIONING:
        answer = ask(f'  {text}? [y/n/s] ').strip().lower()
        if answer.startswith('s'):
            results[key] = 'skipped'
            break
        results[key] = 'pass' if answer.startswith('y') else 'FAIL'
    return results


# ---------------------------------------------------------------- commands

def cmd_verify_image(a):
    image, info = load_image(a.build, a.image)
    print(f'PASS: {info["path"]}\n  {info["bytes"]} bytes, SHA-256 {info["sha256"]}\n'
          f'  manifest SHA-256 {info["manifest_sha256"]}\n  vector table and Bank 1 limits OK')
    return 0


def cmd_doctor(a):
    ok = True
    print(f'Python {sys.version.split()[0]} on {sys.platform}')
    try:
        tool = dfu_util_path(a.dfu_util)
        print(f'dfu-util {dfu_version(tool)} at {tool}')
    except FlashError as e:
        print('FAIL:', e); ok = False; tool = None
    try:
        cmd_verify_image(a)
    except FlashError as e:
        print('FAIL:', e); ok = False
    if tool:
        devices = list_devices(tool)
        print(f'{len(devices)} STM32 DFU device(s) connected')
        for d in devices:
            print(f'  serial={d["serial"]} path={d["path"]} alts={d["alts"]}')
    print('Ready.' if ok else 'Fix the failures above before flashing.')
    return 0 if ok else 1


def cmd_list(a):
    tool = dfu_util_path(a.dfu_util)
    devices = list_devices(tool)
    for d in devices:
        print(f'serial={d["serial"]} path={d["path"]} ver={d["ver"]}')
        for alt, name in sorted(d['alts'].items()):
            print(f'  alt {alt}: {name}')
    if not devices:
        print('No STM32 DFU device connected.')
    return 0


def cmd_flash(a, ask=input):
    image, info = load_image(a.build, a.image)
    tool = dfu_util_path(a.dfu_util)
    version = dfu_version(tool)
    print(f'Image {Path(info["path"]).name}: {info["bytes"]} bytes, SHA-256 {info["sha256"][:16]}...  (dfu-util {version})')
    done, failures, seen = 0, 0, set()
    while True:
        device = wait_for_device(tool, a.timeout, exclude=seen)
        row = {'utc': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'serial': device['serial'],
               'usb_path': device['path'], 'image_sha256': info['sha256'], 'image_bytes': info['bytes'], 'dfu_util': version}
        try:
            readback, (code, _) = flash_device(tool, device, image, leave=not a.no_leave)
            row.update(result='PASS', readback_sha256=readback,
                       note='' if code == 0 else f'dfu-util exit {code} after verified read-back and leave (expected on some hosts)')
            print(f'PASS: {device["serial"]} verified ({info["bytes"]} bytes).')
            if a.check and not a.no_leave:
                wait_for_departure(tool, device)
                results = commissioning(ask)
                row['checks'] = ';'.join(f'{k}={v}' for k, v in results.items())
                if 'FAIL' in results.values():
                    row['result'] = 'FLASHED_CHECK_FAIL'
                    failures += 1
                    print('Commissioning check FAILED: set this unit aside for diagnosis.')
            done += 1
        except FlashError as e:
            row.update(result='FAIL', note=str(e).splitlines()[0])
            failures += 1
            print('FAIL:', e)
        append_log(a.log, row)
        print(f'Logged to {a.log}')
        if not a.batch:
            return 0 if failures == 0 else 1
        seen = set()
        if a.no_leave or not wait_for_departure(tool, device, timeout=15):
            # Never re-flash a unit that is still sitting in DFU; it must be unplugged first.
            seen = {(device['path'], device['serial'])}
            if not a.no_leave:
                print('WARNING: this unit is still in DFU mode after leave; unplug it (the pinhole also restarts it).')
        print(f'\n{done} flashed, {failures} failed. Connect the next clicker in DFU mode, or Ctrl-C to stop.')


def build_parser():
    p = argparse.ArgumentParser(prog='clicker_flash.py', description=__doc__.split('\n\n')[0])
    p.add_argument('--build', type=Path, default=DEFAULT_BUILD, help='firmware build directory (default: %(default)s)')
    p.add_argument('--image', type=Path, help='a BIN listed in the build manifest (default: the Q5 BIN)')
    p.add_argument('--dfu-util', help='dfu-util executable (default: $DFU_UTIL or PATH)')
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('doctor', help='check dfu-util, the image and connected devices')
    sub.add_parser('verify-image', help='check the image against the build manifest only')
    sub.add_parser('list', help='list connected STM32 DFU devices')
    f = sub.add_parser('flash', help='flash, read back, verify, start the application and log')
    f.add_argument('--batch', action='store_true', help='keep going: flash each clicker as it is connected')
    f.add_argument('--check', action='store_true', help='record on-device commissioning answers in the log')
    f.add_argument('--no-leave', action='store_true', help='stay in DFU after verifying (for debugging)')
    f.add_argument('--timeout', type=float, default=120, help='seconds to wait for a device (default: %(default)s)')
    f.add_argument('--log', type=Path, default=DEFAULT_LOG, help='CSV unit log (default: %(default)s)')
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    try:
        return {'doctor': cmd_doctor, 'verify-image': cmd_verify_image, 'list': cmd_list, 'flash': cmd_flash}[a.command](a)
    except FlashError as e:
        print('FAIL:', e, file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print('\nStopped.')
        return 130


if __name__ == '__main__':
    sys.exit(main())
