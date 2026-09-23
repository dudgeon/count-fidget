"""Exercise the separate Q3 counter and asynchronous OLED state machine."""
from pathlib import Path
import os
import shlex
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "firmware/q3-oled"


def run_tests():
    compiler = shlex.split(os.environ.get("CC", "cc"))
    outputs = []
    with tempfile.TemporaryDirectory(prefix="count-fidget-q3-tests-") as directory:
        for name, sources in (("counter", ("test_counter.c", "counter.c")),
                              ("oled", ("test_oled.c", "oled.c", "counter.c")),
                              ("input", ("test_input.c", "input.c", "counter.c"))):
            target = Path(directory) / name
            command = compiler + ["-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic", "-O2"]
            subprocess.run(command + [str(SOURCE / file) for file in sources] + ["-o", str(target)], check=True)
            outputs.append(subprocess.check_output([str(target)], text=True))
    return "".join(outputs)


if __name__ == "__main__":
    print(run_tests(), end="")
