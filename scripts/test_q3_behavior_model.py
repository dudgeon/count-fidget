"""Bounded deterministic review of unchanged Q3 production portable firmware.

Compiles a separate review harness against actual counter.c, input.c and oled.c.
It does not simulate MSP430 peripheral timing, analog rails or physical FRAM.
No frozen source, build, native report or RFQ is rewritten.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'firmware/q3-oled'
HARNESS = ROOT/'firmware/tests/q3_behavior_model_2026_09_22.c'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,help='Write a new review result; must not be an existing frozen Q3 report')
    args=parser.parse_args()
    if args.output:
        target=args.output.resolve()
        if target.parent==ROOT/'verification' and not target.name.startswith('q3-behavior-model-2026-09-22'):
            parser.error('Use the new dated behavior-model report name in verification/')
        if ROOT in target.parents and target.parent!=ROOT/'verification':
            parser.error('Repository results are confined to the new dated verification report')
    paths=[Path(__file__).resolve(),HARNESS]+[SOURCE/name for name in ('counter.c','counter.h','input.c','input.h','oled.c','oled.h','main_msp430.c','build/click-counter-Q3-oled.elf','build/click-counter-Q3-oled.hex','build/build-manifest.json')]
    before={p.relative_to(ROOT).as_posix():sha(p) for p in paths}
    compiler=shlex.split(os.environ.get('CC','cc'))
    version=subprocess.check_output(compiler+['--version'],text=True).splitlines()[0]
    flags=['-std=c11','-O2','-Wall','-Wextra','-Werror','-pedantic']
    with tempfile.TemporaryDirectory(prefix='q3-behavior-model-') as folder:
        executable=Path(folder)/'model'
        command=compiler+flags+['-I',str(SOURCE),str(HARNESS),*[str(SOURCE/name) for name in ('counter.c','input.c','oled.c')],'-o',str(executable)]
        subprocess.run(command,check=True)
        run=subprocess.run([str(executable)],capture_output=True,text=True,timeout=180)
    after={p.relative_to(ROOT).as_posix():sha(p) for p in paths}
    if before!=after:raise RuntimeError('Review inputs changed while running')
    report={'schema_version':1,'completed_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS' if run.returncode==0 else 'FAIL',
            'inputs_sha256':before,'host_compiler':version,'compiler_flags':flags,'exit_code':run.returncode,
            'coverage':json.loads(run.stdout) if run.returncode==0 else {},'stderr':run.stderr,
            'frozen_sources_and_images_unchanged':True,'physical_hardware_qualified':False,
            'limitations':['Finite deterministic schedules, not exhaustive firmware-state or interrupt interleaving proof.',
                           'Journal faults damage one destination word then stop; active-slot corruption, multiword electrical failure and voltage timing are not emulated.',
                           'OLED logical model assumes reset stops pump/panel; recovered RAM is compared with a clean production run, not with physical bonded pixels.',
                           'Host portable modules are executed; MCU HAL, hardware register side effects, ISR timing and stack limits are not executed by this harness.',
                           'A newly detected volatile input gap is not durable until its marker write; a cut before that write cannot preserve that diagnosis.']}
    text=json.dumps(report,indent=2,sort_keys=True)+'\n'
    if args.output:args.output.write_text(text)
    print(text,end='')
    if run.returncode:raise SystemExit(1)


if __name__=='__main__':main()
