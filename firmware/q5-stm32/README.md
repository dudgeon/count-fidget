# Q5 STM32 target

Separate STM32L072CBT6 firmware for the Q5 hardware candidate. It adds the COUNT-key soft power latch (PB2), the SYS_LOAD/2 battery gauge (PA4), charger status (PA5/PA6), hold-to-reset keys, option-byte self-provisioning and the boot, latency and display-power fixes described in [the Q5 firmware guide](../../docs/q5-firmware.md). It targets the FM25V02A-GTR FRAM and HS96L01W4S03 SPI OLED module like Q4, and reads Q4 journals unchanged. Q4 files are unchanged.

Build using the pinned Arm GNU 14.3.Rel1 compiler:

```sh
python3 -B scripts/build_firmware_q5.py --toolchain /path/to/arm-gnu-toolchain-14.3.rel1-<host>-arm-none-eabi
python3 -B scripts/build_firmware_q5.py --verify-only
python3 -B scripts/test_firmware_q5.py
python3 -B scripts/test_firmware_q5.py --sanitize   # add --cc gcc where clang lacks the UBSan runtime
python3 -B scripts/test_firmware_q5.py --image-only
```

`source-records.json` pins the upstream ST and Arm header sources and licenses. The build manifest binds sources, compiler binaries, included headers, libgcc, commands and every output. ELF, HEX and BIN are equivalent program images restricted to Flash Bank1. None of them initialises internal EEPROM, option bytes or external FRAM. The application may program the option-byte USER half-word once at run time (BOR_LEV only; never RDP); see the guide.

The first use of new or unrecognised FRAM shows `0 ERR`; hold RESET COUNT for 2 s and release it to establish a verified zero. A queue overflow or storage failure shows ERR and freezes increments until such a reset has been committed and read back. Option bytes the firmware cannot safely provision show OPT with the digits hidden, and the FRAM is never accessed.

These binaries have not executed on a physical MCU. Host tests, instruction-level emulation and ELF inspection are not hardware qualification or manufacturing release.
