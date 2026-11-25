# Q5 board bring-up — one board at a time

This is the repeatable procedure for taking one assembled Count Fidget Q5 board from the JLC box to a flashed, commissioned clicker. Run every stage on one board, fill in its log, then start the next board. Do not batch stages across boards: a fault found on board 1 should stop you before you power board 2.

It is the every-unit part (section A, plus the enclosure checks in G) of the [first-article test plan](q5-first-article-test-plan.md), written as an operator procedure. The sampled tests in sections B–F are listed at the end; they need a power profiler and a scope and are run on selected boards afterwards.

**What arrived:** the 26 Sep 2026 JLC order ([order record](../procurement/q5/JLC-QUOTE-Q5.md#order-placed--26-september-2026)): Q5 boards, Standard PCBA, both sides. All SMT is on the **bottom**; the OLED module DS1 is fitted by JLC on its header on the **top**. Nothing needs soldering. The boards still have 5 mm Standard-PCBA edge rails. This first order was made from the Gerbers before pin-1 silkscreen dots were added, so use the polarity reference sheets, not the silkscreen, for the polarity check.

## Stop rules (read once)

A **STOP** means: do not continue on this board, do not power it again, mark it **HOLD** in its log and in the summary table, and move on to the next board only once you understand the fault is not common to all boards.

- Any short in stage 2, or BT1 reversed.
- More than 100 mA, a hot part, smell or smoke in stage 3.
- VLOGIC outside 3.15–3.26 V.
- DFU never enumerates on two different data cables.
- Flash VERIFY FAILED twice.
- Any lower or corrupted count, or ERR that a reset hold does not clear.

**Never unplug a board that is in DFU mode** (dark display after RESET + pinhole, after a failed flash, or after Ctrl-C). Press the pinhole first. With a cell fitted it otherwise stays powered and drains the cell.

**Cells: rechargeable LIR2032 only.** Never a CR2032 or ML2032: the charger will try to charge it.

## Kit

Required:
- Mac with this repository checked out, Python 3 and `dfu-util` (one-time setup below)
- USB-C **data** cable (a charge-only cable never enumerates); a second cable of another brand for troubleshooting
- Inline **USB-C power meter** (shows V and mA) between the Mac and the board
- Multimeter with resistance, diode/continuity and DC volts; fine probes
- Loupe or phone macro camera
- 2 × CPG151101D13 clicky switches (LCSC C49234235) per board; they can be moved between boards for bring-up
- 1 × LIR2032 per board, charged or part-charged
- Paper clip (pinhole), flush cutters or pliers for the edge rails, a fine file or sandpaper, safety glasses

Useful, not required: current-limited bench supply (0–5 V), PPK2 or similar for the sampled tests, printed enclosure parts and M2 × 6 self-tapping screws (C357360) for stage 8.

Reference files to have open:
- [`POLARITY-REFERENCE-Q5-BOTTOM.png`](../procurement/q5/POLARITY-REFERENCE-Q5-BOTTOM.png) and [`-TOP.png`](../procurement/q5/POLARITY-REFERENCE-Q5-TOP.png) (or the [PDF](../procurement/q5/POLARITY-REFERENCE-Q5.pdf))
- [`tools/clicker-flash/README.md`](../tools/clicker-flash/README.md)

## One-time setup (Mac)

```sh
xcode-select --install                       # only if python3 is missing
brew install dfu-util
cd ~/repos/count-fidget                       # this repository
git status firmware/q5-stm32/build            # must be clean
python3 tools/clicker-flash/clicker_flash.py doctor
```

`doctor` must report dfu-util ≥ 0.9 and the image **OK** against the build manifest. If the image check fails, do not flash: restore the committed build (`git checkout -- firmware/q5-stm32/build`).

Keep the flasher's unit log outside the repository (the default `~/count-fidget-flash-log.csv` is fine). It is private; only the board IDs and results go into the committed logs.

## Per-board procedure

Copy [`verification/first-article/bring-up-log-TEMPLATE.md`](../verification/first-article/bring-up-log-TEMPLATE.md) to `verification/first-article/CF-0N.md` (the four logs CF-01 to CF-04 are already created) and fill it in as you go. Record measured values, not just ticks.

### Stage 0 — Identify (2 min)

1. Pick the next board. Give it the next ID (CF-01, CF-02, …). Put a small sticker or marker dot with the ID on the **edge rail** for now; move it to the inside of the base after assembly.
2. Photograph both sides in good light. Save the photos with the ID in the filename (locally, not in the repo).

### Stage 1 — Remove the edge rails (3 min)

1. Wear safety glasses. Support the board right up to the break line (V-score or mouse-bite tabs), with the display (top) facing up and nothing pressing on the glass.
2. Bend the rail away from the board along the break line with pliers gripping the **rail**, not the board. Do not flex the board itself: ceramic capacitors near the edge can crack.
3. File or sand the broken edge smooth. Brush off the dust; keep it away from J1 and the display.

### Stage 2 — Visual inspection (5 min) — test A1

Under the loupe, against the polarity reference sheets:

| Check | Pass |
|---|---|
| BT1 holder | Seated flat, both tabs wetted; the **+** side matches the reference (CELL_P pad, X ≈ 35.4 mm) |
| U2 (BQ25185) and **U7** (TPS22917) | Pin-1 corner matches the reference. These two were 180° wrong in JLC's first engineering placement and were corrected; check them specifically |
| U1, U3–U6, U8, Q1–Q5, D1–D4 | Pin-1 / cathode / single pin as on the reference |
| QFN/WSON parts | No bridges, no tombstoned passives, no solder balls |
| J1 USB-C | Mouth at the board edge; shell stakes soldered; no solder in the mouth |
| SW1, SW2 hot-swap sockets | Flat on their pads, both pads soldered, socket holes clear |
| SW3 pinhole switch | Present, clicks |
| DS1 display (top) | Module parallel to the board on its 7-pin header; glass uncracked; header pins on the bottom trimmed (≤ 1 mm) and not touching anything |

Any defect you are unsure about: photograph it and record it; do not power the board until it is understood.

### Stage 3 — Unpowered resistance (5 min) — tests A2, A2b

No USB, no cell. Black probe on **TP1 GND**. Let each reading settle for a few seconds (the capacitors charge from the meter).

| Measure | Pass |
|---|---|
| TP5 VBUS → TP1 GND | > 1 kΩ |
| TP6 SYS → TP1 GND | > 1 kΩ |
| TP2 VLOGIC → TP1 GND | > 1 kΩ |
| **BT1 polarity:** the holder contact that touches the cell's **+** face (the can) → BT1 pad 1, marked + (CELL_P) | < 1 Ω. **STOP** if it reads to pad 2 (CELL_N_RAW) instead: the holder is 180° wrong and a cell would be reversed |

Test points are on the bottom; see the bottom polarity sheet for positions (TP1 GND, TP2 VLOGIC and TP3/TP4 sit in a row near the pinhole end; TP5 VBUS is near J1; TP6 SYS is between the key sockets).

### Stage 4 — Fit the key switches (2 min)

Fitting them now lets you enter DFU and run the commissioning check without the enclosure.

1. Lay the board top-up on a flat, firm surface so the sockets on the bottom are supported.
2. Line each switch's two pins up with the socket holes and press straight down until the housing sits flush. **SW1 = COUNT (+)**, **SW2 = RESET (○)**; both are the same switch.
3. Press each switch: clean click, returns fully.

### Stage 5 — First power, USB only, no cell (5 min) — test A3

1. Connect: Mac → USB-C power meter → data cable → board. Watch the meter as you plug in; unplug at once if the current goes above **100 mA** or anything gets warm.
   With a bench supply instead: 5.0 V, current limit 100 mA, into the USB-C port through a breakout.
2. The display stays dark (the flash is blank). That is expected.
3. Record the current. Pass: **< 30 mA**.
4. Measure to TP1 GND and record:
   - TP5 VBUS ≈ 5 V
   - TP6 SYS ≈ 4.5 V (the charger regulates SYS with USB present)
   - **TP2 VLOGIC 3.15–3.26 V** (STOP outside this band)
5. Touch-test U2, U5, U7 and the MCU: none should be warm.

### Stage 6 — Flash and commission (5 min) — tests A4, A6

1. Enter DFU, with USB still connected:
   1. **Hold RESET (○).**
   2. Press and release the **pinhole** (SW3) with the paper clip.
   3. **Release RESET.**
2. `python3 tools/clicker-flash/clicker_flash.py list` shows one `[0483:df11]` device with `@Internal Flash`. If not, see troubleshooting.
3. Flash with the commissioning questions:
   ```sh
   python3 tools/clicker-flash/clicker_flash.py flash --check
   ```
   The tool verifies the image, flashes, reads back, starts the application and logs the chip's DFU serial. Copy the serial into the board log.
4. **A6:** the digits should appear within about 1 s of the flash finishing, without pressing the pinhole. Record yes/no. (If blank, press the pinhole once and record that it needed it.)
5. Answer the tool's four questions honestly by looking at the display:

| Step | Expected |
|---|---|
| After flashing | `0` with **ERR** (new FRAM), or the previous count |
| Hold RESET 2 s, release | **RST** appears, then `0` without ERR |
| Press COUNT three times | `3`; battery bars or **CHG** visible |
| Hold RESET 2 s, release | `0` |

A first boot may reset itself once while the firmware programs its brown-out option byte; that is normal. **OPT** with no digits is a fail (record it, STOP).

Result handling: **PASS** → continue. **VERIFY FAILED** or download failed → run step 6.3 once more on the same board; a second failure is a STOP. If anything fails while the board is in DFU, **press the pinhole before unplugging**.

### Stage 7 — Restart, cell and battery checks (10 min) — tests A5, B7, assembly step 5

1. **A5 (USB):** count to a number you'll recognise (e.g. 7). Unplug USB, plug it back in: the count returns, no ERR. Press the pinhole with USB connected: the count returns, no ERR.
2. **Fit the cell with USB connected** (USB-first; the protector chip may not wake on a cold insertion). LIR2032, **+ side as marked on the holder**. The display should stay on and show **CHG** (or a full gauge for a full cell). Record which.
3. Leave it on USB for a minute, then unplug USB. Now on battery:
   - The display shows the count with battery bars (or **LO** if the cell is nearly empty: charge it on USB and come back).
   - Wait **30 s** without touching anything: the display turns off.
   - Press COUNT once: the board wakes and the count goes up by **exactly 1** (the power-on press counts once). Record before/after.
   - Press the pinhole (**B7**): the board turns off. Press COUNT: it comes back with the count kept (+1 for that press).

### Stage 8 — Enclosure and final checks (20–30 min) — tests G1–G4

Only once you have chosen and made an enclosure. There are two:

- **Q5 printed** ([`mechanical/q5/README.md`](../mechanical/q5/README.md)): print the tolerance coupon first (G0). Follow its assembly sequence, but skip its solder step (DS1 is already fitted) and its cell step (already done). The keys move from the sockets into the rear key plate: pull them straight out, clip them into the plate, then press the plate and switches into SW1/SW2 together. Screws: 4 × M2 × 6 (C357360).
- **Q5A printed tray + acrylic lid** (`mechanical/q5-acrylic/README.md`, on the open PR #15 branch until it merges): the switches stay in the sockets as fitted in stage 4, and the lid drops over them. Cut the laser coupon first. Screws: 4 × M2 × 14 (the M2 × 6 are too short); stop tightening as soon as the heads seat.

Then check and record:
- **G2:** USB-C plug mates fully and charges (CHG) with the case closed, in both orientations, with at least two cable brands.
- **G3:** both keycaps travel fully, return, and don't bind.
- **G4:** the paper clip reaches the pinhole and clicks it cleanly.
- Count still correct after assembly; no ERR.
- **G1:** assembly time and any rework.

Move the ID sticker inside the base.

### Stage 9 — Close the log (2 min)

1. Set the board's status in its log and in the [summary table](../verification/first-article/README.md): **PASS** (all stages), **PASS-BARE** (stages 0–7 passed, no enclosure yet), **HOLD** (a STOP, under investigation) or **REJECT** (confirmed hardware fault).
2. Commit the log (`verification/first-article/CF-0N.md`). Do not commit the flasher's CSV, photos with personal details, or anything else private.
3. Start the next board at stage 0.

About 40 minutes per bare board, plus the enclosure.

## Troubleshooting

| Symptom | Try |
|---|---|
| No DFU device | Data cable (try the second brand); RESET must still be held when the pinhole is released; another port or a powered hub |
| More than one DFU device | One board at a time |
| `WARNING: device reports … KiB flash` | Not an STM32L072CB: re-check the board and the MCU marking |
| Display blank after PASS | Press the pinhole once. Still blank: record a commissioning fail (DS1, its header or the module supply) |
| `0 ERR` won't clear | The reset hold must be ≥ 2 s and released before 10 s, with no COUNT press during it. Still ERR: FRAM (U8) fault, STOP |
| No CHG with USB and a part-charged cell | The NTC window holds charging off outside about 0–45 °C; check the room. Otherwise record a C4 fail |
| Board won't wake on battery after cell insertion | Plug USB in (wakes the protector). Insert cells with USB connected from now on |
| Board stays on after unplugging during DFU | Expected (USB pull-up back-feeds the latch). Press the pinhole |

## After all four boards: sampled tests

These need the PPK2, a dummy cell, a scope and a bench supply, and run on chosen boards per the [first-article plan](q5-first-article-test-plan.md). Record them in a dated file under `verification/first-article/`.

| Section | What | Boards |
|---|---|---|
| A7 | DFU-then-unplug current with a cell (confirms the pinhole rule) | 1 |
| B1–B8 | Off current, latch timing, timeout power-off, inrush, TP13–TP6 bypass | up to all 4 |
| C1–C7 | Gauge thresholds, charging, temperature window, primary-cell check | 3 |
| D1–D5 | Cell insertion cycles, cold insertion, retention, contact resistance | 4, 2 cell brands |
| E1–E5 | Display power tree, current, reset abuse, response, droop | 3 |
| F1–F4 | Count integrity under cell pulls, 10,000 presses, re-flash, reset-key abuse | 3 |

The plan was written for 5 units; with four boards, use all four where it says 5. Production quotes still wait for every **stop** test to pass.
