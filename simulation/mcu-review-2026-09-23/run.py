"""Run three idealized subcircuits with libngspice; no IC/whole-board claim.

Usage: python3 run.py --library /absolute/path/to/libngspice.dylib
Works through ngspice's public shared-library API. No vendor model is bundled.
"""
import argparse
import ctypes as ct
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cross(times, values, target, increasing):
    for i in range(1, len(times)):
        a, b = values[i - 1], values[i]
        if (a <= target <= b if increasing else a >= target >= b):
            return times[i - 1] + (times[i] - times[i - 1]) * (target - a) / (b - a)
    raise AssertionError(f'No crossing of {target}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library', required=True, type=Path)
    args = parser.parse_args()
    lib = ct.CDLL(str(args.library.resolve()))
    logs = []
    callback_type = ct.CFUNCTYPE(ct.c_int, ct.c_char_p, ct.c_int, ct.c_void_p)

    @callback_type
    def output(message, ident, context):
        logs.append(message.decode(errors='replace'))
        return 0

    lib.ngSpice_Init.argtypes = [ct.c_void_p] * 7
    lib.ngSpice_Init.restype = ct.c_int
    assert lib.ngSpice_Init(output, None, None, None, None, None, None) == 0
    lib.ngSpice_Command.argtypes = [ct.c_char_p]
    lib.ngSpice_Command.restype = ct.c_int
    lib.ngSpice_Command(b'version')
    deck = HERE / 'interface-and-inrush.cir'
    lines = deck.read_bytes().splitlines()
    array = (ct.c_char_p * (len(lines) + 1))(*lines, None)
    lib.ngSpice_Circ.argtypes = [ct.POINTER(ct.c_char_p)]
    lib.ngSpice_Circ.restype = ct.c_int
    assert lib.ngSpice_Circ(array) == 0
    assert lib.ngSpice_Command(b'tran 10n 500u 0 10n uic') == 0

    class Vector(ct.Structure):
        _fields_ = [('name', ct.c_char_p), ('type', ct.c_int), ('flags', ct.c_short),
                    ('real', ct.POINTER(ct.c_double)), ('complex', ct.c_void_p),
                    ('length', ct.c_int)]

    lib.ngGet_Vec_Info.argtypes = [ct.c_char_p]
    lib.ngGet_Vec_Info.restype = ct.POINTER(Vector)

    def vector(name):
        ptr = lib.ngGet_Vec_Info(name.encode())
        assert ptr and ptr.contents.real and ptr.contents.length > 0, name
        v = ptr.contents
        return [v.real[i] for i in range(v.length)]

    times, sense, sys = vector('time'), vector('v(sense)'), vector('v(sys)')
    edge, ack = vector('v(edge)'), vector('v(ack)')
    above = cross(times, [s - v for s, v in zip(sense, sys)], .4, False)
    rise = cross(times, edge, 2.1, True) - cross(times, edge, .9, True)
    analytic_above = 4.3 * 20e-6 * math.log(4.2 * 3.3 / (4.3 * .4))
    analytic_rise = 4700 * 100e-12 * math.log(.7 / .3)
    analytic_ack = 3 * 6000 / 10700
    assert abs(above - analytic_above) < 50e-9
    assert abs(rise - analytic_rise) < 1e-9
    assert abs(ack[-1] - analytic_ack) < 1e-6
    assert not any('error' in line.lower() for line in logs), logs
    report = {
        'date': '2026-09-23', 'status': 'BEHAVIORAL_SUBCIRCUITS_ONLY_NOT_HARDWARE_PASS',
        'engine': next(x.removeprefix('stdout ').strip('* ') for x in logs if 'ngspice-' in x),
        'engine_library_sha256': digest(args.library),
        'input_sha256': {p.name: digest(p) for p in (deck, Path(__file__))},
        'sample_count': len(times),
        'spice': {'hypothetical_ack_v': ack[-1], 'rc_rise_30_to_70_ns': rise * 1e9,
                  'hypothetical_inrush_above_0p4v_us': above * 1e6},
        'analytic': {'hypothetical_ack_v': analytic_ack,
                     'rc_rise_30_to_70_ns': analytic_rise * 1e9,
                     'hypothetical_inrush_above_0p4v_us': analytic_above * 1e6},
        'scope': ['Ideal R/C/source elements only; no semiconductor manufacturer model run.',
                  '6k sink,100pF bus,1ohm extra source resistance and20uF effective C are hypothetical.',
                  'No actual charger/protector slew/state machine, OLED behavior, CPU current or USB protocol.',
                  'No board/parasitic extraction, temperature qualification, assembly or manufacturing approval.'],
        'warnings': [x for x in logs if 'warning' in x.lower()],
    }
    (HERE / 'result.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps(report['spice'], indent=2))
    print('Analytical agreement verified; no whole-board or hardware PASS is asserted.')


if __name__ == '__main__':
    main()
