# Q4 STM32 target

Separate STM32L072CBT6 firmware for the Q4 hardware candidate. The product target uses FM25V02A-GTR SPI FRAM and the HS96L01W4S03 SPI OLED module. Q3 files are unchanged.

Build using the pinned Arm GNU 14.3.Rel1 compiler:

```sh
python3 -B scripts/build_firmware_q4.py --toolchain /path/to/arm-gnu-toolchain-14.3.rel1-darwin-arm64-arm-none-eabi
python3 -B scripts/build_firmware_q4.py --verify-only
python3 -B scripts/test_firmware_q4.py
python3 -B scripts/test_firmware_q4.py --sanitize
```

The compiler is a free, unpacked toolchain; installation into system directories is unnecessary. `source-records.json` pins the upstream ST and Arm header sources and their licenses. The build manifest binds sources, compiler binaries, included headers, libgcc, commands and every output. ELF, HEX and BIN are equivalent program images, restricted to Flash Bank1. None initializes internal EEPROM, option bytes or external FRAM.

The first successful use of a new/unrecognized FRAM requires a normal count-reset press to establish zero. A queue overflow or storage failure shows ERR and freezes increments until an explicit reset has been committed and read back. A missing/unresponsive FRAM or invalid MCU option bytes requires recovery; no count is claimed saved. After inactivity a quiescent storage fault still permits MCU Stop, with ERR retained. The next increment wakes ERR; a new reset press grants one bounded recovery attempt. Failed FRAM sleep releases CS and isolates SPI; its standby current may remain. The Stop workaround runs entirely from startup-copied SRAM and is checked in the actual ELF for every silicon revision.

An optional `--eeprom-alternate --output /private/tmp/q4-eeprom-alternate` build exercises the same journal using internal EEPROM Bank2. It is an engineering alternative, not an interchangeable update for the product FRAM image. The two storage domains do not migrate counts automatically.

See [the firmware and home-programming guide](../../docs/q4-firmware.md) for pin contracts, timing, power monitoring, exact limitations and USB recovery. These binaries have not executed on a physical MCU. Host tests and ELF inspection are not hardware qualification or manufacturing release.
