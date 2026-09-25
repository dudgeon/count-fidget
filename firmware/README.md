# Firmware: frozen Q1 and Q2 LCD verification candidate

`main_msp430.c` now contains the **unreleased Q2 LCD verification candidate** for MSP430FR4133IG48R, 48-pin package. The existing Q1 ELF/HEX/map, `SHA256.json`, factory HEX and submitted RFQ ZIP remain unchanged. The ZIP retains its matching Q1 source. All boards remain on hardware hold: Q1 lacks three required LCD bias reservoir capacitors.

The allegation that Q1 source omitted segment enable is **refuted**. TI support 1.212 defines `LCD4MUX` to include `LCDSON`. Rebuilding the original source with TI GCC 9.3.1.11 produces the exact archived Q1 application HEX; no loaded-byte source/binary drift was found. Complete ELF metadata differs across builds. See `../docs/review-lcd-firmware-Q2.md` for evidence and the inferred build recipe.

Q2 changes the divider from 4 to 8 for **32 Hz nominal**, giving margin for REFO tolerance. Explicit `LCDSON` is added for readability and makes no additional binary change. Outputs and source/header/toolchain provenance are separate in `q2-lcd-check/`; build them with `../scripts/build_firmware.py` as described in `../docs/build-and-verify.md`. This image has not been flashed or qualified and is not authorized for manufacture.

Behavior: 8 ms stable-state debounce; one count per press; single-press reset with priority; eight digits with saturation at 99,999,999; first wake click counts; display blanks after 30 seconds; LPM4 wake on either edge; 16-bit aligned, CRC-protected dual-record journal at information FRAM 0x1800–0x181F. An interrupted newest commit can lose that newest click; the previous committed record remains the recovery target. Display updates follow successful commits.

LCD commons use L0–3; segment lines use L8–19 and L24–27. Mode 2 uses the 3.0 V rail, 1/3 bias and 1/4 mux: Q1 is nominally 64 Hz, Q2 is 32 Hz. The pump capacitor and three R13/R23/R33 reservoir capacitors are required; firmware cannot replace missing hardware. All common and segment pins are held at the same GPIO low level during sleep. REFO clocks the debounce timer and LCD; no crystal is fitted. The watchdog is disabled and additional firmware robustness review remains a production gate.

factory-display-info.hex is a factory-only information-FRAM record that starts at 88,888,888 for display inspection. Load it once during factory test, then reset to zero and execute the RFQ tests. Do not use it for field firmware updates: application-only HEX intentionally preserves the saved count.

No target hardware validation has occurred. Host tests validate counter behavior and interruption boundaries between complete journal words, not analog brownout behavior, MCU pin multiplexing or LCD contrast. Programming and test procedure: procurement/RFQ-Q1.md. USB is charging only; use MSP-FET Spy-Bi-Wire and the ten labeled pogo lands.

Compiler: https://www.ti.com/tool/download/MSP430-GCC-OPENSOURCE
