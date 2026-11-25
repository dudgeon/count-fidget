#!/usr/bin/env python3
"""Flash Count Fidget Q5 clickers over USB-C from a Mac (or Linux) with dfu-util.

The STM32L072 ROM bootloader exposes USB DFU (ST "DfuSe"); no drivers and no
application USB stack are needed. This tool:

  1. verifies the firmware image against the committed build manifest
     (size, SHA-256, vector table, Flash Bank 1 limits);
  2. waits for exactly one STM32 DFU device and checks its flash layout;
  3. downloads the image to 0x08000000;
  4. reads the same range back and compares it byte for byte;
  5. only after a matching read-back, leaves DFU (the application starts) and
     appends a line to a unit log;
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
# STM32L072CB (DS10689 Table 2): 128 KiB of Flash in two 64 KiB banks; Bank 2 starts at 0x08010000.
# The firmware linker script and build_firmware_q5.py both confine the image to Bank 1.
BANK1_BYTES = 64 * 1024
DEVICE_FLASH_BYTES = 128 * 1024
# The L07x ROM bootloader is shared by the 128 and 192 KiB parts. Its DfuSe descriptor has been
# reported as "@Internal Flash /0x08000000/1536*128g" (192 KiB) on 128 KiB parts, so accept both.
ROM_LAYOUT_BYTES = (128 * 1024, 192 * 1024)
# STM32L0 NVM reads 0 after an erase (RM0376 section 3.3): a factory-blank part reads all zero.
ERASED_BYTE = 0x00
OPTION_BASE = 0x1FF80000
OPTION_FIRMWARE_USER = 0x807C     # firmware/q5-stm32/board.h BOARD_OPTR_USER
RAM_BASE, RAM_BYTES = 0x20000000, 20 * 1024
DEFAULT_LOG = Path.home() / 'count-fidget-flash-log.csv'
DEFAULT_BACKUPS = Path.home() / 'count-fidget-flash-backups'
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
            raise FlashError('Flash pages for the image are not readable/erasable/writable in the DfuSe layout')
        warnings = []
        if segments[-1]['end'] - FLASH_BASE not in ROM_LAYOUT_BYTES:
            warnings.append(f'device reports {(segments[-1]["end"] - FLASH_BASE) // 1024} KiB flash, expected the '
                            'STM32L07x ROM layout (192 KiB, or 128 KiB): check this is a Count Fidget Q5 board')
        return alt, warnings
    raise FlashError('No "@Internal Flash" DfuSe interface: this is not the STM32 ROM bootloader')


def wait_for_device(tool, timeout, exclude=(), poll=0.5, say=print, serial=None):
    deadline = time.monotonic() + timeout
    announced = False
    while True:
        devices = [d for d in list_devices(tool) if (d['path'], d['serial']) not in exclude]
        if serial:
            devices = [d for d in devices if d['serial'] == serial]
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

# A unit left in ROM DFU keeps its USB D+ pull-up on; after unplugging, that back-feeds VBUS through the
# ESD diode and holds the power latch on (draining the cell) until the pinhole resets it.
STUCK_HINT = 'Press the pinhole (reset) BEFORE unplugging: a clicker unplugged while still in DFU mode stays powered and drains its cell.'
# The first application boot programs the BOR option byte (about 6.4 ms of NVM write, then a reload
# reset); power loss during that write leaves an invalid option word. The ROM jump after leave is
# also not guaranteed to restart cleanly on silicon (first-article test A6); a pinhole press is a
# clean hardware reset with BOOT0 low.
FIRST_BOOT_HINT = ('Keep USB connected for at least 5 s. Digits (or 0 ERR) should appear within about 1 s; '
                   'if the display stays dark, press the pinhole once (a clean reset) and record that it was needed.')


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
        say('Reading back and comparing...')
        code, out, readback = upload(tool, device, alt, len(image))
        if readback is None:
            raise FlashError('Read-back produced no file:\n' + tail(out))
        if readback != image:
            first = next((i for i, (a, b) in enumerate(zip(readback, image)) if a != b), min(len(readback), len(image)))
            raise FlashError(f'VERIFY FAILED: read-back differs from the image at offset 0x{first:x} '
                             f'({len(readback)} bytes read). The unit is still in DFU mode: re-flash it. '
                             'Do not ship it.')
        if code != 0:
            raise FlashError('Read-back reported an error:\n' + tail(out))
    if not leave:
        return sha256(readback), (0, '')
    # Start the application only once the read-back has matched, so the ROM never jumps into a
    # partly written image. The leave is a zero-length DfuSe download after an 8-byte read; it writes
    # nothing. The ROM jumps to the application and may drop off the bus before answering the final
    # status request, so a non-zero exit here is expected on some hosts (libusb pipe/timeout errors).
    say('Verified. Starting the application...')
    code, out, _ = upload(tool, device, alt, 8, leave=True)
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
        device = wait_for_device(tool, a.timeout, exclude=seen, serial=a.serial)
        row = {'utc': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'serial': device['serial'],
               'usb_path': device['path'], 'image_sha256': info['sha256'], 'image_bytes': info['bytes'], 'dfu_util': version}
        try:
            readback, (code, _) = flash_device(tool, device, image, leave=not a.no_leave)
            row.update(result='PASS', readback_sha256=readback,
                       note='' if code == 0 else f'dfu-util exit {code} after verified read-back and leave (expected on some hosts)')
            print(f'PASS: {device["serial"]} verified ({info["bytes"]} bytes).' + ('' if a.no_leave else ' ' + FIRST_BOOT_HINT))
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
            print(STUCK_HINT)
        append_log(a.log, row)
        print(f'Logged to {a.log}')
        if not a.batch:
            emit({'step': 'flash', 'ok': failures == 0, 'serial': device['serial'], 'result': row['result'],
                  'leave_requested': not a.no_leave and row['result'] != 'FAIL', 'note': row.get('note', '')})
            return 0 if failures == 0 else 1
        seen = set()
        if a.no_leave or not wait_for_departure(tool, device, timeout=15):
            # Never re-flash a unit that is still sitting in DFU; it must be unplugged first.
            seen = {(device['path'], device['serial'])}
            if not a.no_leave:
                print('WARNING: this unit is still in DFU mode after leave.', STUCK_HINT)
        print(f'\n{done} flashed, {failures} failed. Connect the next clicker in DFU mode, or Ctrl-C to stop.')


# ---------------------------------------------------------------- step-by-step commands (agent-operated)
#
# Each command below does one thing, never prompts, and prints a final machine-readable line
# `RESULT {json}` so an operator script or agent can drive a first-article flash one step at a time:
#   wait -> probe -> backup -> flash --no-leave -> verify-device -> leave -> record-check
# Only `flash` writes to the device. probe/backup/verify-device/leave only list or read.

def emit(obj):
    print('RESULT ' + json.dumps(obj, sort_keys=True))


def one_device(tool, serial=None):
    devices = list_devices(tool)
    if serial:
        devices = [d for d in devices if d['serial'] == serial]
    if not devices:
        raise FlashError('No STM32 DFU device found' + (f' with serial {serial}' if serial else '') +
                         '. With USB connected: hold RESET, press and release the pinhole, then release RESET')
    if len(devices) > 1:
        raise FlashError('More than one STM32 DFU device is connected; connect one clicker at a time')
    return devices[0]


def flash_size(device):
    for alt, name in sorted(device['alts'].items()):
        if name.startswith('@Internal Flash'):
            _, segments = parse_layout(name)
            return alt, segments[-1]['end'] - FLASH_BASE
    raise FlashError('No "@Internal Flash" DfuSe interface: this is not the STM32 ROM bootloader')


def upload(tool, device, alt, length, leave=False, address=FLASH_BASE):
    """Read `length` bytes from `address`. Read-only; with leave=True the ROM then starts the application."""
    with tempfile.TemporaryDirectory(prefix='clicker-read-') as td:
        back = Path(td) / 'read.bin'        # dfu-util refuses to overwrite: path must not exist
        opts = f'0x{address:08x}:{length}' + (':leave' if leave else '')
        code, out = run([tool] + select_args(device, alt) + ['-s', opts, '-U', str(back)], timeout=180)
        data = back.read_bytes() if back.is_file() else None
    return code, out, data


def describe_contents(data, image):
    if data[:len(image)] == image:
        return 'q5-image'
    if all(b == ERASED_BYTE for b in data):
        return 'blank'          # STM32L0 erased NVM reads 0x00, not 0xFF
    return 'other'


READ_FAIL_HINT = ('If this repeats on a board that was never flashed, its flash may be read-protected (RDP level 1): '
                  'stop and set the board aside. Never use dfu-util :unprotect or "read unprotect": it mass-erases.')


def decode_option_bytes(data):
    """Decode the RDP and USER option words (RM0376 option byte layout: value in bits 15:0, complement in 31:16)
    and predict what the Q5 firmware's first boot will do (firmware/q5-stm32/main_stm32.c provision_options)."""
    w0, w1 = struct.unpack_from('<II', data, 0)
    valid0, valid1 = (w0 >> 16) == (~w0 & 0xFFFF), (w1 >> 16) == (~w1 & 0xFFFF)
    rdp, user = w0 & 0xFF, w1 & 0xFFFF
    level = {0xAA: 0, 0xCC: 2}.get(rdp, 1)
    if not (valid0 and valid1):
        firmware = 'OPT (option word and complement disagree: the loader applies its default values)'
    elif level != 0:
        firmware = 'OPT (read protection active)'
    elif user == OPTION_FIRMWARE_USER:
        firmware = 'already provisioned'
    elif ((user & ~0x008F) | 0x800C) == OPTION_FIRMWARE_USER:
        firmware = 'programs USER 0x807C once on first boot, then resets itself'
    else:
        firmware = 'OPT (unexpected watchdog/stop/standby option bits: not changed by the firmware)'
    return {'rdp_word': f'0x{w0:08x}', 'user_word': f'0x{w1:08x}', 'complements_valid': valid0 and valid1,
            'rdp_level': level, 'bor_lev': f'0x{user & 0xF:x}', 'bfb2': bool(user & 0x80), 'nboot1': bool(user & 0x8000),
            'firmware_first_boot': firmware}


def read_option_bytes(tool, device):
    """Best-effort read-only upload of the first two option words through the ROM's '@Option Bytes' alt."""
    alt = next((k for k, v in sorted(device['alts'].items()) if v.startswith('@Option Bytes')), None)
    if alt is None:
        return {'error': 'no @Option Bytes alt'}
    code, out, data = upload(tool, device, alt, 8, address=OPTION_BASE)
    if code != 0 or data is None or len(data) != 8:
        return {'error': 'option byte read failed: ' + (tail(out, 2) or f'exit {code}')}
    return decode_option_bytes(data)


def cmd_wait(a):
    tool = dfu_util_path(a.dfu_util)
    d = wait_for_device(tool, a.timeout, serial=a.serial)
    print(f'Found STM32 DFU device serial={d["serial"]} path={d["path"]}')
    emit({'step': 'wait', 'ok': True, 'serial': d['serial'], 'path': d['path']})
    return 0


def cmd_probe(a):
    image, info = load_image(a.build, a.image)
    tool = dfu_util_path(a.dfu_util)
    d = one_device(tool, a.serial)
    alt, warnings = flash_alt(d, len(image))
    _, total = flash_size(d)
    option_alt = next((k for k, v in d['alts'].items() if v.startswith('@Option Bytes')), None)
    print(f'serial={d["serial"]} path={d["path"]} bootloader ver={d["ver"]}')
    for k, v in sorted(d['alts'].items()):
        print(f'  alt {k}: {v}')
    print(f'Flash alt {alt}: descriptor {total // 1024} KiB (the STM32L072CB has {DEVICE_FLASH_BYTES // 1024} KiB); '
          'image pages readable/erasable/writable in the layout. Read protection does not change the descriptor; '
          '`backup` is the first step that proves the flash can be read.')
    for w in warnings:
        print('WARNING: ' + w)
    emit({'step': 'probe', 'ok': not warnings, 'serial': d['serial'], 'path': d['path'], 'bootloader_ver': d['ver'],
          'flash_alt': alt, 'flash_kib': total // 1024, 'option_bytes_alt': option_alt, 'warnings': warnings})
    return 0 if not warnings else 3


def cmd_backup(a):
    image, _ = load_image(a.build, a.image)
    tool = dfu_util_path(a.dfu_util)
    d = one_device(tool, a.serial)
    alt, descriptor = flash_size(d)
    # The ROM descriptor can claim 192 KiB on this 128 KiB part; never read past the real Flash.
    total = min(descriptor, DEVICE_FLASH_BYTES)
    print(f'Reading all {total // 1024} KiB of flash from {d["serial"]} (read-only, stays in DFU)...')
    code, out, data = upload(tool, d, alt, total)
    if code != 0 or data is None or len(data) != total:
        raise FlashError(f'Backup read returned {0 if data is None else len(data)} of {total} bytes '
                         f'(dfu-util exit {code}). {READ_FAIL_HINT}\n' + tail(out))
    options = read_option_bytes(tool, d)
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    a.out.mkdir(parents=True, exist_ok=True)
    path = a.out / f'{d["serial"] or "unknown"}-{stamp}.bin'
    path.write_bytes(data)
    contents = describe_contents(data, image)
    print(f'Saved {path} ({len(data)} bytes, SHA-256 {sha256(data)}); contents: {contents}')
    print('Option bytes: ' + (options['error'] if 'error' in options else
                              f"RDP word {options['rdp_word']}, USER word {options['user_word']}: "
                              f"firmware first boot {options['firmware_first_boot']}"))
    emit({'step': 'backup', 'ok': True, 'serial': d['serial'], 'file': str(path), 'bytes': len(data),
          'sha256': sha256(data), 'contents': contents, 'dfu_exit': code, 'option_bytes': options})
    return 0


def cmd_verify_device(a):
    image, info = load_image(a.build, a.image)
    tool = dfu_util_path(a.dfu_util)
    d = one_device(tool, a.serial)
    alt, _ = flash_alt(d, len(image))
    code, out, data = upload(tool, d, alt, len(image))
    if code != 0 or data is None:
        raise FlashError(f'Read-back failed (dfu-util exit {code}). {READ_FAIL_HINT}\n' + tail(out))
    match = data == image
    first = None if match else next((i for i, (x, y) in enumerate(zip(data, image)) if x != y), min(len(data), len(image)))
    print(('MATCH' if match else f'MISMATCH at offset 0x{first:x}') + f': {d["serial"]} flash vs {Path(info["path"]).name}')
    emit({'step': 'verify-device', 'ok': match, 'serial': d['serial'], 'readback_sha256': sha256(data),
          'image_sha256': info['sha256'], 'first_difference': first})
    return 0 if match else 1


def cmd_leave(a):
    tool = dfu_util_path(a.dfu_util)
    d = one_device(tool, a.serial)
    alt, _ = flash_size(d)
    # Never ask the ROM to jump into a blank or foreign image: on a factory-blank STM32L0 the vector
    # table reads zero and the core would lock up until the pinhole is pressed.
    code, out, head = upload(tool, d, alt, 8)
    if code != 0 or head is None or len(head) != 8:
        raise FlashError(f'Could not read the vector table (dfu-util exit {code}). {READ_FAIL_HINT}\n' + tail(out))
    sp, reset = struct.unpack('<II', head)
    if not (RAM_BASE < sp <= RAM_BASE + RAM_BYTES) or not reset & 1 or not FLASH_BASE <= (reset & ~1) < FLASH_BASE + BANK1_BYTES:
        raise FlashError(f'Flash does not start with an application vector table (SP 0x{sp:08x}, reset 0x{reset:08x}); '
                         'not leaving DFU. Flash the board first. ' + STUCK_HINT)
    print(f'Asking the ROM bootloader on {d["serial"]} to start the application (no write)...')
    code, out, _ = upload(tool, d, alt, 8, leave=True)
    departed = wait_for_departure(tool, d, timeout=a.timeout)
    print(('Device left DFU mode. ' + FIRST_BOOT_HINT) if departed else 'WARNING: still in DFU mode. ' + STUCK_HINT)
    emit({'step': 'leave', 'ok': departed, 'serial': d['serial'], 'dfu_exit': code})
    return 0 if departed else 1


def parse_checks(text):
    checks = {}
    keys = [k for k, _ in COMMISSIONING]
    for part in filter(None, (p.strip() for p in text.split(','))):
        k, _, v = part.partition('=')
        if k not in keys or v not in ('pass', 'FAIL', 'fail', 'skipped'):
            raise FlashError(f'Bad check {part!r}; use {",".join(k + "=pass|fail|skipped" for k in keys)}')
        checks[k] = 'FAIL' if v.lower() == 'fail' else v
    return checks


def cmd_record_check(a):
    checks = parse_checks(a.checks)
    _, info = load_image(a.build, a.image)
    failed = 'FAIL' in checks.values()
    row = {'utc': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'serial': a.serial,
           'result': 'FLASHED_CHECK_FAIL' if failed else 'COMMISSIONED', 'image_sha256': info['sha256'],
           'image_bytes': info['bytes'], 'checks': ';'.join(f'{k}={v}' for k, v in checks.items()), 'note': a.note or ''}
    append_log(a.log, row)
    print(f'Logged {row["result"]} for {a.serial} to {a.log}')
    emit({'step': 'record-check', 'ok': not failed, 'serial': a.serial, 'result': row['result'], 'checks': checks})
    return 0 if not failed else 1


def cmd_summary(a):
    if not Path(a.log).exists():
        print(f'No log at {a.log}')
        emit({'step': 'summary', 'ok': True, 'units': {}})
        return 0
    with Path(a.log).open() as f:
        rows = list(csv.DictReader(f))
    units = {}
    for r in rows:
        units.setdefault(r['serial'], []).append(r['result'])
    for serial, results in units.items():
        print(f'{serial}: {" -> ".join(results)}')
    emit({'step': 'summary', 'ok': True, 'units': {s: r[-1] for s, r in units.items()}, 'rows': len(rows)})
    return 0


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
    f.add_argument('--serial', help='only flash the DFU device with this serial')
    s = sub.add_parser('wait', help='wait for exactly one STM32 DFU device (no access beyond listing)')
    s.add_argument('--timeout', type=float, default=300); s.add_argument('--serial')
    for name, text in (('probe', 'check the connected device layout and protection (list only)'),
                       ('backup', 'read the whole flash to a file (read-only; stays in DFU)'),
                       ('verify-device', 'read the image range back and compare with the image (read-only)'),
                       ('leave', 'start the application from DFU without writing')):
        s = sub.add_parser(name, help=text); s.add_argument('--serial')
        if name == 'backup':
            s.add_argument('--out', type=Path, default=DEFAULT_BACKUPS)
        if name == 'leave':
            s.add_argument('--timeout', type=float, default=10)
    s = sub.add_parser('record-check', help='log on-device commissioning answers for a unit (no device access)')
    s.add_argument('--serial', required=True)
    s.add_argument('--checks', required=True, help='e.g. blank=pass,reset=pass,count=pass,zero=fail')
    s.add_argument('--note'); s.add_argument('--log', type=Path, default=DEFAULT_LOG)
    s = sub.add_parser('summary', help='latest result per unit from the log')
    s.add_argument('--log', type=Path, default=DEFAULT_LOG)
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    try:
        return {'doctor': cmd_doctor, 'verify-image': cmd_verify_image, 'list': cmd_list, 'flash': cmd_flash,
                'wait': cmd_wait, 'probe': cmd_probe, 'backup': cmd_backup, 'verify-device': cmd_verify_device,
                'leave': cmd_leave, 'record-check': cmd_record_check, 'summary': cmd_summary}[a.command](a)
    except FlashError as e:
        print('FAIL:', e, file=sys.stderr)
        if a.command in ('wait', 'probe', 'backup', 'verify-device', 'leave', 'record-check', 'summary', 'flash'):
            emit({'step': a.command, 'ok': False, 'error': str(e).splitlines()[0]})
        return 2
    except KeyboardInterrupt:
        print('\nStopped.')
        return 130


if __name__ == '__main__':
    sys.exit(main())
