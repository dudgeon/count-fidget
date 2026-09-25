"""Run Q4 ideal RC envelope subcircuits with libngspice; no IC/whole-board claim.

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
    deck = HERE / 'ideal-envelope.cir'
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

    times=vector('time')
    usense,ucap=vector('v(u_sense)'),vector('v(u_cap)')
    csense,ccap=vector('v(c_sense)'),vector('v(c_cap)')
    rise,fall=vector('v(fram_rise)'),vector('v(fram_fall)')
    usb_above=cross(times,[a-b for a,b in zip(usense,ucap)],.4,False)
    cold_above=cross(times,[a-b for a,b in zip(csense,ccap)],.4,False)
    rt=4.2*3.333/(math.e*.4)
    expect_usb=2.783e-6*rt
    expect_cold=15.433e-6*rt
    rise_slopes=[(b-a)/(tb-ta) for a,b,ta,tb in zip(rise,rise[1:],times,times[1:]) if tb>ta]
    fall_slopes=[(a-b)/(tb-ta) for a,b,ta,tb in zip(fall,fall[1:],times,times[1:]) if tb>ta]
    rise_us_v=1e6/max(rise_slopes)
    fall_us_v=1e6/max(fall_slopes)
    expected_rise=66.878*6.8e-6/3.3*1e6
    expected_fall=6.8e-6/(3.3/66.878+.003)*1e6
    assert abs(usb_above-expect_usb)<50e-9
    assert abs(cold_above-expect_cold)<50e-9
    assert abs(rise_us_v-expected_rise)<.05
    assert abs(fall_us_v-expected_fall)<.05
    assert usb_above<125e-6<cold_above
    assert not any('error' in line.lower() for line in logs), logs
    report = {
        'status':'IDEAL_ENVELOPES_ONLY_NOT_HARDWARE_PASS',
        'engine':next(x.removeprefix('stdout ').strip('* ') for x in logs if 'ngspice-' in x),
        'engine_library_sha256':digest(args.library),
        'input_sha256':{p.name:digest(p) for p in (deck,Path(__file__))},
        'sample_count':len(times),
        'spice':{'usb_first_c3_scc_exposure_us':usb_above*1e6,
                 'cold_upstream_scc_exposure_us':cold_above*1e6,
                 'fram_rise_fastest_us_per_v':rise_us_v,
                 'fram_fall_fastest_us_per_v':fall_us_v},
        'analytic':{'usb_first_c3_scc_exposure_us':expect_usb*1e6,
                    'cold_upstream_scc_exposure_us':expect_cold*1e6,
                    'fram_rise_fastest_us_per_v':expected_rise,
                    'fram_fall_fastest_us_per_v':expected_fall},
        'scope':['Ideal R/C/voltage and current sources only; no semiconductor model.',
                 'Series resistance maximizes an analytical capacitor envelope, not an actual cell ESR.',
                 'C3-only USB case requires upstream SYS already powered and downstream loads settled.',
                 'Separate check.py adds the conservative BAT_SENSE branch current.',
                 'Memory3mA sink at all voltages and effective6.8uF are unverified qualification conditions.',
                 'No charger/protector recovery, connector bounce, regulator dropout or OLED current behavior.',
                 'No extracted PCB parasitics, physical qualification or manufacturing approval.'],
        'warnings':[x for x in logs if 'warning' in x.lower()]}
    (HERE/'spice-result.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report['spice'],indent=2))
    print('Analytical agreement verified; no whole-board or hardware PASS is asserted.')


if __name__ == '__main__':
    main()
