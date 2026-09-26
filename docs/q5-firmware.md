# Q5 firmware and home programming

Status: implemented engineering target, 25 September 2026. **Physical MCU, OLED, storage, power-latch and battery testing remains required.** Quotes, purchases and manufacturing release remain paused. Q4 sources and artifacts remain historical and unchanged; Q5 lives in `firmware/q5-stm32/`.

Q5 keeps the Q4 MCU (STM32L072CBT6), ROM USB DFU, SPI2 OLED module, SPI1 FRAM and the 96-slot journal format. A Q4 FRAM image is read unchanged by Q5. The changes are listed per issue in the [Q5 review](REVIEW-Q5-2026-09-25.md).

## Pin contract

| Function | Contract |
|---|---|
| COUNT / POWER key | SW1 closes **SYS → PWR_KEY**. D3 (A1) ORs PWR_KEY into U7 ON, and Q5 mirrors it onto **PA0 COUNT_N** (active low, unchanged R17/C11 input) |
| Power hold | **PB2 PWR_HOLD**, push-pull HIGH keeps U7 on through D3 (A2); released for power-off |
| USB power | VBUS → D4 → U7 ON: valid USB always powers the board (charging, ROM DFU) |
| Count reset / boot selection | PA1 and BOOT0 share SW2 (VLOGIC-referenced), active high, external pull-down |
| Battery sense | **PA4 ADC_IN4** reads SYS_LOAD/2 through R36/R37 (150k/150k 0.1 %, 100 nF C37); the divider is downstream of U7, so it draws nothing while off |
| Charger status | **PA5 STAT1, PA6 STAT2** (BQ25185 open-drain); internal pull-ups only while awake |
| OLED reset / switched supply | PB0 push-pull while powered; PB1 active-high enable (U6 QOD now unconnected) |
| OLED SPI2 | PB13 SCK, PB15 MOSI, PB12 CS, PB14 D/C |
| FRAM SPI1 | PB3 SCK, PB4 MISO, PB5 MOSI, PB8 open-drain CS |
| USB / debug | PA11/PA12 USB; PA13/PA14 SWD; SW3 NRST behind the base pinhole |

The ROM bootloader in this part (AN2606 §60.1, V4.x) uses only USART1 (PA9/PA10), USART2 (PA2/PA3) and USB DFU, so the new PA4–PA6 and PB2 functions are never driven by the ROM. The ROM does not drive PB2 either: in DFU the board stays powered only through USB (D4) or a held COUNT key.

## Keys: counting, reset and power

- **COUNT** adds one per debounced press (8 ms), saturating at 99,999,999 (MAX). A held key never repeats.
- **Power on:** pressing COUNT on a switched-off device turns U7 on (typical tON 17.9 ms with C29 = 4.7 nF). C40 (10 nF) holds U7's ON input through contact bounce, and for about 9.9 ms after release. The first instructions of `Reset_Handler`, before RAM initialisation, drive PB2, so the latch holds within microseconds of reset release. That **power-on press counts once**: it is recognised from the POR reset flag plus two agreeing reads of COUNT_N low at setup. A tap shorter than about 11 ms typical (16 ms with allowance) may not latch; the device then simply stays off. Emulation shows lit digits about 0.45 s after the press (0.35 s to AFh plus the SSD1315's ~100 ms tAF).
- **Reset requires a deliberate hold.** Hold RESET COUNT for 2 s: the label **RST** appears. Release it within 10 s of pressing to zero the count. Releasing earlier, holding past 10 s (for example a key trapped in a pocket), or pressing COUNT at any time during the hold cancels the reset.
- **Increment wins.** If both keys are pressed together, or COUNT is pressed while RESET is held, the count increments and the reset is cancelled.
- A key already held when the MCU starts (NRST, DFU attempt, OBL reload) is treated as a level, not a press. Its later release never counts or resets.
- **Presses during boot are kept.** While the journal loads (~0.2 s), the SysTick handler queues only key-level changes, plus one settle sample per change. The counter is seeded with the key level at setup. A second press made right after the power-on press therefore counts.
- **Key releases are not activity.** Only presses restart the 30 s timeout, so releasing a key does not wake the display.
- ERR (uncertain saved value) freezes increments. Only a complete, newly observed reset hold-and-release, committed and read back, restores confidence. The power-on press does not count while ERR.

## Power behaviour

- **On battery:** 30 s after the last key activity the display shuts down (AEh, 8Dh 10h, 120 ms, power off), the journal settles, FRAM receives B9 sleep and PB2 is released. U7 turns off and the whole board below SYS loses power. The off-state drain is the protector and charger battery quiescent current, ~8 µA typical.
- **With USB:** VBUS keeps U7 on, so the release does nothing. Firmware notices it is still running after 200 ms and falls back to Q4-style MCU Stop with PB2 low. A key press wakes it; unplugging USB during Stop switches the board off cleanly.
- **Held COUNT at power-off time:** the key's own contact keeps U7 on, so firmware uses the Stop fallback with PB2 released. On wake, PB2 is re-latched only if a key is actually pressed, so releasing the key switches the board off. (The review found and the emulator now reproduces the earlier behaviour: the release re-latched the board and opened another 30 s display session.)
- **PB2 policy:** held whenever the application is awake; driven first thing in `Reset_Handler`; released only by the power-off and Stop paths.
- **Pinhole reset (SW3) on battery** is a hardware power cycle: NRST releases PB2, the board switches off, and the next COUNT press powers it on. With USB connected it is an ordinary MCU reset.
- **Low battery (issues #9, #5):** SYS_LOAD/2 is sampled with the display ADC (VDDA derived from factory VREFINT). On battery, a four-sample average drives a 4-bar gauge in the top-right corner (≥3.95 / 3.80 / 3.70 / 3.55 V, 30 mV hysteresis). Below 3.55 V the gauge is empty and **LO** is shown (roughly the last 10–15 %). Six consecutive readings below **3.35 V** trigger a storage-protecting shutdown: LO stays visible for 2 s, the count is saved, and the board powers off. This leaves a reserve above the BQ29700's 2.8 V disconnect and keeps the regulator out of dropout, so the display is never run on a collapsing rail. Presses at that level still count before the next shutdown.
- **USB detection:** with valid USB the BQ25185 regulates SYS to 4.5 V ±2 % (VBATREG ≤ 4.3 V). With the 2.06 % worst-case estimate error, a full cell (≤ 4.221 V) reads ≤ 4.308 V and USB SYS reads ≥ 4.319 V, so ≥ 4.313 V means "USB". STAT1 or STAT2 low independently proves USB, so charging and faults are recognised even at the ADC's low corner. Then no LO warning or cut-off is ever raised. **CHG** shows while charging (STAT1 H / STAT2 L). A full gauge means charge done or disabled (H/H, which includes the temperature window holding CE off), and **BAT** means a charger fault (STAT1 L). USB arriving during a LO notice cancels the shutdown.
- Label priority: OPT > RST > ERR > MAX > LO > CHG/BAT.

## Boot and responsiveness (issues #2 and #7)

- Button capture starts only after the journal is loaded and the application initialised. Emulated boot with all 96 slots valid first drains the queue at 207 ms, and **no sample is dropped at any boot**. In Q4 the full queue overflowed after 255 ms and latched ERR after every reset.
- `FLASH_ACR.LATENCY` is 0 (RM0376 Table 12 allows zero wait states to 16 MHz in Range 1).
- The FRAM CS guard is 110 loop iterations (about 550 cycles, ≥512 cycles ≈ 128 µs) instead of ~2,600.
- The journal CRC-32 uses a 16-entry nibble table; it is identical to the bitwise form (host-tested on 20,000 random records).
- The display module is powered, held in reset, **while** the journal is scanned. Initialisation starts once the ADC confirms the rail.
- The first frame is written into GDDRAM **before** 8Dh/AFh, so there is no separate clear pass and no post-AFh blank wait.
- Later frames redraw only changed digit cells, the label and the icon. A one-digit change is 12 packets instead of 128. Packets carry up to 31 data bytes, and the main loop does not WFI while an SPI packet is in flight.
- Emulated results: press to new digits **60–66 ms** with the display on (Q4: 200–225 ms). Wake from USB-held Stop to lit digits about 0.34 s (Q4: 0.77 s). From off to lit digits about 0.45 s.
- Only committed values are shown (product decision retained): at 12 Hz fidgeting the display lags by at most one commit. The emulated 100-press/12 Hz run lost no count.

## ADC

The ADC runs from PCLK/2 = 2 MHz. RM0376 makes ADC_CCR.LFMEN mandatory below 3.5 MHz, so it is set, which the review found missing (also in Q4). The VREFINT ADC buffer (SYSCFG_CFGR3.ENBUF_VREFINT_ADC) is enabled with the channel, and calibration waits for VREFINT_RDYF; if it never sets, the display stays off. The emulator flags any conversion below 3.5 MHz without LFMEN.

## Entering the application from the ROM bootloader

A DfuSe "leave", as used by `tools/clicker-flash`, makes the ST ROM jump to the application without a reset. Its clocks, USB peripheral and interrupt, vector table and memory remap may still be configured. `Reset_Handler` and `Default_Handler` detect that state (USB clock enabled, VTOR non-zero, flash not mapped at 0, or SYSCLK not MSI) and take a clean `NVIC_SystemReset()`. `setup()` therefore always starts from reset-default hardware. Emulator scenario D5 models the jump with a pending USB interrupt; the pre-review image crashed into `panic()` there.

## Option bytes (issue #6)

The application still requires BOR_LEV raw **0xC** (RM0376 "BOR LEVEL 5", VBOR4 falling 2.68–2.85 V), RDP 0xAA, nBOOT1 = 1 and BFB2 = 0. If the USER half-word differs from the reviewed value **0x807C** only in those fields — for example the RM0376 factory value 0x8070 — firmware programs 0x807C once (PEKEY + OPTKEY, word written with its complement, BSY polled) and triggers OBL_LAUNCH. It never writes RDP. It first waits for VREFINT/PVD to be ready, so PVDO is meaningful, and it never rewrites an option word that is already stored (that case shows OPT). A reload that still fails, or any unexpected WDG/STOP/STDBY choice, shows **OPT** with the digits hidden, and FRAM is never accessed. The emulated factory-option scenario programs once, reloads and then counts normally. PVD level 5 remains a best-effort write gate, not a guaranteed pre-BOR warning: DS10689 Table 27 PVD5 falling is 2.77–2.88 V versus BOR4 at 2.68–2.85 V (issue #9.1). The tear-safe journal does not depend on it.

## Home USB programming

A USB data cable and STM32CubeProgrammer are the intended tools. This repository has not exercised a physical DFU connection.

1. Verify the Q5 build manifest (`python3 -B scripts/build_firmware_q5.py --verify-only`). Use the Q5 image only.
2. **Connect USB first.** USB powers the board through D4, and it stays powered while the ROM runs.
3. Enter ROM DFU in either order. Both preserve the count, because a reset only commits on release after a completed hold:
   - hold RESET COUNT, press and release the base pinhole (NRST), then release RESET COUNT; or
   - hold the pinhole, press RESET COUNT, release the pinhole, then release RESET COUNT.
   Without USB, NRST simply powers the board off (issue #3's data loss cannot happen).
4. On a Mac, use the bundled tool: `python3 tools/clicker-flash/clicker_flash.py flash --check`. It verifies the image against the build manifest, flashes over DFU, reads back and compares, starts the application and logs the unit; see `tools/clicker-flash/README.md` and the `flash-clickers` Claude skill. STM32CubeProgrammer also works: select USB, connect to the DFU device, download `count-fidget-Q5-stm32.hex` (or the BIN at 0x08000000) and verify. Setting option bytes by hand is optional: the application provisions BOR_LEV itself. If you set them, use RDP AA, nBOOT1 = 1, BFB2 = 0 and BOR_LEV raw 0xC ("BOR LEVEL 5" in RM0376 naming, VBOR4). Some GUIs label raw 0xB as "level 4"; that is wrong for this firmware.
5. Reset normally. With valid FRAM the saved count returns without ERR. New or unrecognised FRAM shows `0 ERR`: hold RESET COUNT for 2 s and release it to establish a verified zero.

The external FRAM is outside the DFU address space, so updates never touch the count. SWD pads remain a second recovery route.

## Build and evidence

`firmware/q5-stm32/build/` holds the ELF, Intel HEX, raw BIN, map, disassembly, stack usage, host-test log and the source-bound manifest built with the pinned Arm GNU 14.3.Rel1 compiler (x86_64 Linux build; the Q4 record used the macOS arm64 build of the same release). `scripts/test_firmware_q5.py` runs the portable production code against deterministic models:

- the behaviour suite: journal tears, key semantics, queue/storage schedules, recovery and fault-idle;
- FRAM transaction faults;
- the OLED startup/partial-redraw/fault suite;
- VREFINT rail corners;
- the battery policy.

`simulation/q5-firmware-emulation/` executes the actual Q5 image on an instruction-level model of the MCU and the Q5 board. It models the power latch, USB presence, the SYS/2 ADC input, the charger STAT pins, RCC reset flags and option-byte programming. See its README and `results/` for the exact scenario list; `scenarios.py --check` fails on any violated expectation.

Not modelled, and still hardware gates:
- analog rail behaviour on latch release and USB unplug;
- the U7 ON-node timing with a real bouncing contact;
- ADC accuracy of the high-impedance divider;
- real cell voltage under load;
- charger STAT timing;
- OLED pixels and current;
- silicon ISR latency;
- USB enumeration.
