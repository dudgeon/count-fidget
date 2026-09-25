#!/usr/bin/env python3
"""Stand-in for dfu-util that emulates an STM32 ROM DfuSe device, for tests only.

Behaviour copied from dfu-util 0.11 (src/main.c, src/dfuse.c): `-l` output
format, `-s address[:length][:leave]` parsing, O_EXCL on the upload file, page
erase before raw download, and leave after download or upload. State lives in
the JSON file named by $MOCK_DFU_STATE:

  {"devices": [{"serial": ..., "path": ..., "alts": {"0": "@Internal Flash  /0x08000000/1536*128 g"},
                "flash": "<hex of first bytes>", "in_dfu": true}],
   "faults": {"corrupt_write_offset": n, "leave_exit": 74, "download_exit": 74}}
"""
import json
import os
import sys

STATE = os.environ['MOCK_DFU_STATE']


def load():
    with open(STATE) as f:
        return json.load(f)


def save(state):
    with open(STATE, 'w') as f:
        json.dump(state, f)


def main(argv):
    state = load()
    state.setdefault('calls', []).append(argv)
    faults = state.get('faults', {})
    if '--version' in argv or '-V' in argv:
        print('dfu-util 0.11\n\nCopyright 2005-2009 Weston Schmidt, Harald Welte and OpenMoko Inc.')
        save(state); return 0
    devices = [d for d in state['devices'] if d.get('in_dfu', True)]
    if '-l' in argv:
        print('dfu-util 0.11\n')
        for n, d in enumerate(devices):
            for alt, name in sorted(d['alts'].items()):
                print(f'Found DFU: [0483:df11] ver=2200, devnum={n + 5}, cfg=1, intf=0, path="{d["path"]}", '
                      f'alt={alt}, name="{name}", serial="{d["serial"]}"')
        save(state); return 0
    opts = dict(zip(argv[::2], argv[1::2]))
    if opts.get('-d') != '0483:df11':
        print('mock: -d 0483:df11 expected'); return 64
    if '-S' in opts:
        devices = [d for d in devices if d['serial'] == opts['-S']]
    if '-p' in opts:
        devices = [d for d in devices if d['path'] == opts['-p']]
    if not devices:
        print('dfu-util: No DFU capable USB device available'); save(state); return 74
    if len(devices) > 1:
        print('dfu-util: More than one DFU capable USB device found!'); save(state); return 74
    dev = devices[0]
    parts = opts['-s'].split(':')
    address = int(parts[0], 16)
    length = next((int(p) for p in parts[1:] if p.isdigit()), None)
    leave = 'leave' in parts[1:]
    if address != 0x08000000:
        print('mock: unexpected address'); return 64
    flash = bytearray.fromhex(dev.get('flash', ''))
    code = 0
    if '-D' in opts:
        if faults.get('download_exit'):
            save(state); print('dfu-util: Error during download get_status'); return faults['download_exit']
        data = bytearray(open(opts['-D'], 'rb').read())
        if 'corrupt_write_offset' in faults:
            data[faults['corrupt_write_offset']] ^= 0x40
        pages = (len(data) + 127) // 128 * 128
        if len(flash) < pages:
            flash.extend(b'\xff' * (pages - len(flash)))
        flash[:pages] = b'\xff' * pages
        flash[:len(data)] = data
        dev['flash'] = flash.hex()
        print(f'Download\t[=========================] 100%\t{len(data)} bytes\nFile downloaded successfully')
    elif '-U' in opts:
        try:
            fd = os.open(opts['-U'], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_TRUNC, 0o666)
        except FileExistsError:
            print('dfu-util: Cannot open file for writing'); save(state); return 73
        want = length or 0x4000
        out = bytes(flash[:want]) + b'\xff' * max(0, want - len(flash))
        os.write(fd, out); os.close(fd)
        print(f'Upload\t[=========================] 100%\t{len(out)} bytes\nUpload done.')
    if leave:
        print('Submitting leave request...')
        dev['in_dfu'] = False
        dev['app_started'] = dev.get('app_started', 0) + 1
        code = faults.get('leave_exit', 0)
    save(state)
    return code


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
