# Q4 firmware emulation (instruction-level)

Runs the **actual Q4 firmware image** (`firmware/q4-stm32/build/count-fidget-Q4-stm32.elf`) on an emulated Cortex-M0+ with models of the board it drives. It exists to catch behaviour that the portable host tests cannot see: vector/startup/linker effects, pin and peripheral configuration, SPI framing to the real device protocols, interrupt timing against the foreground loop, Stop entry/exit and multi-second product scenarios.

**This is a model, not hardware.** Results are "reproduced in emulation". They do not replace the physical gates in `docs/REVIEW-Q4-2026-09-24.md`.

## What is modelled

| Block | Model |
|---|---|
| CPU | Unicorn 2 (QEMU Thumb, Cortex-M0 model). Exceptions, NVIC priority/pending/masking, PRIMASK, WFI and SLEEPDEEP are handled by the harness. Instruction time uses Cortex-M0+ TRM cycle costs per executed instruction plus a flash wait-state penalty (`flash_ws_penalty`, default +0.5 cycle per flash-resident instruction for `LATENCY=1` without prefetch; `0.0` gives the optimistic zero-wait bound). |
| MCU peripherals | RCC (clock enables, peripheral resets, HSI/SWS), PWR (PVD level vs. modelled VLOGIC, Stop/Standby selection), FLASH (`ACR`, `RUN_PD` with the RM0376 §3.6.4 `PDKEYR` lock, `OPTR`), GPIO A/B/C (modes, open-drain, AF numbers, BSRR/BRR, IDR from board nets), EXTI lines 0/1, SYSCFG EXTICR, SysTick, SCB (ICSR, SCR, AIRCR), SPI1/SPI2 (TXE/RXNE/BSY/OVR, BIDIMODE, prescaler timing), ADC (ADVREGEN, ADCAL, ADEN/ADRDY, conversion time from SMPR, VREFINT from `VREFINT_CAL`). |
| Board | SW1/SW2 with configurable bounce; NRST pulse or hold; BOOT0 sampling on reset release (enters "ROM bootloader" and stops); VLOGIC value; FRAM and OLED nets exactly as in `electronics/q4/netlist-Q4.json` (pull-ups/downs R17, R18, R24, R25, R29, R33). |
| FM25V02A | Opcodes WREN/WRDI/RDSR/WRSR/READ/FSTRD/WRITE/SLEEP/RDID, 2-byte addressing, WEL, device ID `7F×6 C2 22 08`, sleep with wake on CS fall and `tREC` 400 µs, `tPU` check. |
| HS96L01W4S03 / SSD1315 | TPS22917 switch (typical tON 84 ms at 22 nF CT), RES#, D/C, command decoder with parameters, page-mode GDDRAM, charge pump/display state, power-off order check (AEh, 8Dh 10h, ≥100 ms before supply removal), back-power check on the five signal lines, pixel decode of the rendered digits and ERR/MAX label. |

Not modelled: analog rails and droop, currents (the energy model multiplies emulated state durations by datasheet currents), charger/protector state machines, oscillator tolerance, silicon errata beyond the Stop sequence check, USB.

## Running

Requires Python 3.10+ with `unicorn==2.1.4`, `capstone==5.0.7` and `pyelftools`.

```sh
python3 simulation/q4-firmware-emulation/scenarios.py --output simulation/q4-firmware-emulation/results/committed-firmware-scenarios.json
python3 simulation/q4-firmware-emulation/scenarios.py --elf /path/to/new/count-fidget-Q4-stm32.elf --check
python3 simulation/q4-firmware-emulation/energy.py --output simulation/q4-firmware-emulation/results/energy-model.json
python3 simulation/q4-firmware-emulation/q4emu.py firmware/q4-stm32/build/count-fidget-Q4-stm32.elf --seconds 1.5
```

`--check` asserts the documented product behaviour (first-use ERR, counting, sleep/wake, NRST restore, fast presses, low rail, held key, key priority, no input-queue overflow at boot). Scenarios marked informational (DFU-entry variants, unprovisioned option bytes) are reported but do not fail the run. A full suite takes about 2–3 minutes.

## Results for the committed image (SHA-256 `9a982e43…`)

`results/committed-firmware-scenarios.json` — 9 expectation failures, all caused by one defect: the boot-time FRAM journal scan keeps the foreground loop from draining the 255-sample button queue for 245–409 ms, so the queue overflows and the application latches ERR and persists `fault=1` after a reset. A candidate patch (capture enabled only after `oled_init()`) passes every expectation. The report is `docs/REVIEW-Q4-simulation-2026-09-25.md`.

`results/energy-model.json` — per-session charge from emulated state timelines and the daily-use battery model.
