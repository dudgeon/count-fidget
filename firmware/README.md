# Q1 target firmware

main_msp430.c binds the host-tested counter and LCD encoder to the MSP430FR4133IG48R, 48-pin package. The binary was built with TI MSP430 GCC 9.3.1.11 and support files 1.212 with warnings treated as errors. ELF, Intel HEX, map and SHA-256 manifest are included.

Behavior: 8 ms stable-state debounce; one count per press; single-press reset with priority; eight digits with saturation at 99,999,999; first wake click counts; display blanks after 30 seconds; LPM4 wake on either edge; 16-bit aligned, CRC-protected dual-record journal at information FRAM 0x1800–0x181F. An interrupted newest commit can lose that newest click; the previous committed record remains the recovery target. Display updates follow successful commits.

LCD commons use L0–3; segment lines use L8–19 and L24–27. Mode 2 uses the 3.0 V rail, 1/3 bias, 1/4 mux and approximately 64 Hz frame rate. All common and segment pins are held at the same GPIO low level during sleep. REFO clocks the debounce timer and LCD; no crystal is fitted. The watchdog is disabled in this engineering build and additional firmware robustness review remains a production gate.

factory-display-info.hex is a factory-only information-FRAM record that starts at 88,888,888 for display inspection. Load it once during factory test, then reset to zero and execute the RFQ tests. Do not use it for field firmware updates: application-only HEX intentionally preserves the saved count.

No target hardware validation has occurred. Host tests validate counter behavior and interruption boundaries between complete journal words, not analog brownout behavior, MCU pin multiplexing or LCD contrast. Programming and test procedure: procurement/RFQ-Q1.md. USB is charging only; use MSP-FET Spy-Bi-Wire and the ten labeled pogo lands.

Compiler: https://www.ti.com/tool/download/MSP430-GCC-OPENSOURCE
