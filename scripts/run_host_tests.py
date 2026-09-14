"""Compile/run the existing portable C tests without touching shipped artifacts."""
from pathlib import Path
import os
import shlex
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    compiler = shlex.split(os.environ.get("CC", "cc"))
    if not compiler or not shutil.which(compiler[0]):
        raise SystemExit("No C compiler available. Set CC or provide a compiler; no installation was attempted.")
    with tempfile.TemporaryDirectory(prefix="count-fidget-tests-") as directory:
        for test, sources in (
            ("counter", ["test_counter.c", "counter.c"]),
            ("lcd", ["test_lcd.c", "lcd_de188.c"]),
        ):
            output = Path(directory) / ("test_" + test)
            command = compiler + ["-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic", "-O2"]
            command += [str(ROOT / "firmware" / name) for name in sources]
            subprocess.run(command + ["-o", str(output)], check=True)
            subprocess.run([str(output)], check=True)
    print("Host tests passed. Target electronics and physical qualification remain untested.")


if __name__ == "__main__":
    main()
