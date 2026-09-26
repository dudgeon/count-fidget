# Q5 first-article test plan

This plan closes the Q5 physical gates listed in [REVIEW-Q5](REVIEW-Q5-2026-09-25.md) and the Q4 gates that still apply. Run it on the first assembled boards **before** any volume order. Every result goes in a dated file under `verification/first-article/` (measurement, instrument, unit serial from the flash log, pass/fail). A board that fails a **stop** test is not shipped, and the design issue goes back to engineering.

## Equipment (about US$250 if bought new)

| Item | Use |
|---|---|
| Nordic PPK2 power profiler (or Joulescope / µCurrent + DMM) | µA-to-mA supply current, as a source standing in for the cell |
| Coin-cell dummy adapter (CR2032-size insulated shim with leads) | Feed the BT1 holder from the PPK2 or a bench supply without a cell |
| 2-channel oscilloscope (≥ 20 MHz) | Latch, rail and SPI timing |
| Adjustable bench supply 0–5 V with current limit | Cell-voltage sweeps |
| USB-C power meter + 3 data cables of different brands | Charge current; USB fit |
| Thermocouple thermometer; hair dryer and freezer pack | Charge temperature window |
| 5 × LIR2032 from two sources, 1 × CR2032 (for the do-not-charge check only), calipers | Cells; fit |

Test points: TP1 GND, TP2 VLOGIC, TP5 VBUS, TP6 SYS, TP9 COUNT_N, TP11 NRST, TP12 BOOT/RESET key, TP13 SYS_ON (U7 ON).

## A. Bring-up and programming (every unit)

| # | Test | Pass |
|---|---|---|
| A1 | Visual/X-ray from JLC: BT1, J1 stakes, QFN/WSON joints | No bridges; J1 stakes wetted |
| A2 | Unpowered: resistance VBUS–GND, SYS–GND, VLOGIC–GND | > 1 kΩ each (no shorts) |
| A2b | **BT1 polarity before any cell:** meter from the holder's spring contact that meets the cell's + (can) face to TP pad CELL_P (BT1 pad 1, marked +) | < 1 Ω to CELL_P. **Stop** if the + contact reads to CELL_N_RAW (the holder is placed 180° wrong; a cell would be reverse-connected) |
| A3 | USB only, no cell, current limit 100 mA | Board powers (VBUS via D4). VLOGIC 3.15–3.26 V. Current < 30 mA |
| A4 | DFU entry and `clicker_flash.py flash --check` | PASS, and all four commissioning answers pass. **Stop** if DFU never enumerates on two cables |
| A5 | Unplug/replug, pinhole restart | Count returns without ERR |
| A6 | After the flasher's automatic DFU leave, the display comes up without pressing the pinhole | Digits appear within 1 s. The firmware's ROM-leftover reset path has worked |
| A7 | With a cell fitted: enter DFU, then unplug USB **without** leaving DFU. Watch TP13 and the current | Expected: the board stays on (D+ pull-up back-feed through D2 holds the latch), drawing several mA. Record the current. The pinhole must turn it off. This confirms the "pinhole before unplugging" rule |

## B. Power latch (5 units)

| # | Test | Pass |
|---|---|---|
| B1 | Dummy cell 3.7 V from the PPK2, board off: off current | ≤ 11 µA (expect ~8). **Stop** if > 20 µA |
| B2 | Scope TP13 + TP2; single COUNT presses of decreasing length (a finger tap, then a fast flick) | Every press ≥ 50 ms latches; count +1 per power-on; no double count. Record the shortest tap that latches |
| B3 | Wait 30 s | Display off, then VLOGIC falls to 0 with no re-latch or oscillation on TP13. Current returns to B1 |
| B4 | Hold COUNT 60 s from off | One count; turns off within 1 s of releasing after the timeout |
| B5 | On: plug USB; wait 30 s; unplug USB during Stop | Board off after the unplug; no half-powered state (VLOGIC 0 V, not floating mid-rail) |
| B6 | Inrush: PPK2 at 3.0 V, capture power-on | Peak < 25 mA, and the protector does not trip over 20 power-ons |
| B7 | Pinhole on battery | Board turns off; next COUNT press restores the count |
| B8 | Fallback check (1 unit): bridge TP13 SYS_ON to TP6 SYS with a wire | Board powers and counts without the latch (the recovery route if latch control fails); remove the bridge afterwards |

## C. Battery sense, gauge and charger status (3 units)

| # | Test | Pass |
|---|---|---|
| C1 | Dummy cell stepped 4.20 → 3.30 V in 10 mV steps (wait 2 s each), display on | Bars change within ±40 mV of 3.95/3.80/3.70/3.55 V. LO below 3.55 ± 0.04 V. Save-and-off between 3.28 and 3.42 V |
| C2 | Repeat rising | Hysteresis ≈ 30 mV; no flicker between bar states |
| C3 | Real LIR2032 discharged at typical use (log with PPK2) | Record days and gauge behaviour; LO appears before the display dims or resets |
| C4 | USB on a half-charged cell | **CHG** shown. Charge current per BQ25185 ISET (record). Ends in full gauge with no label |
| C5 | USB with the NTC below 0 °C (freezer pack) and above 45 °C (hair dryer) | Charging inhibited (no CHG, or CHG stops), and resumes in range. Record trip temperatures |
| C6 | USB with a full cell (4.20 V) | Never shows LO; never powers off on the USB threshold |
| C7 | **CR2032 primary inserted** (do-not-charge check, 1 unit, supervised, < 1 min) | Record what happens. Labelling must forbid primary cells, since the charger will attempt to charge |

## D. Cell and holder (5 units, 2 cell brands)

| # | Test | Pass |
|---|---|---|
| D1 | Insert the cell with USB connected (documented procedure), 20 cycles | Always powers normally; no protector lock-out |
| D2 | Cold insertion without USB, 20 cycles | Record: works / needs USB to wake. If it needs USB, keep the USB-first instruction (datasheet-expected). **Stop** only if the unit stays dead after USB is applied |
| D3 | Holder retention: shake and 1 m drop onto carpet with the enclosure closed | No reset; count kept |
| D4 | Holder contact resistance (4-wire, dummy shim) | < 0.2 Ω |
| D5 | Protector recovery: discharge a cell below 2.8 V (bench), then USB | Charges and recovers; count intact |

## E. Display (3 units)

| # | Test | Pass |
|---|---|---|
| E1 | Module power tree: photograph the module; measure VBAT/VDD on the module at VLOGIC 3.15 and 3.26 V | Record. Pump output about 7.5 V; digits readable in room light |
| E2 | Display current, all digits 8, contrast as shipped | Record. The energy model assumes 1.0 mA module current at contrast 0x10 with ~20 % of pixels lit (estimate 0.6–2.0 mA): update battery-life figures with the measured value |
| E3 | 200 × NRST pulses with the display on (script with USB + a relay, or by hand) | No latch-up; display recovers every time |
| E4 | Response: high-speed phone video of 20 presses | New digits visible ≤ 100 ms after the click |
| E5 | Display-on droop: scope SYS_LOAD and VLOGIC at a 3.40 V dummy cell while the display turns on | VLOGIC stays ≥ 3.15 V; no brown-out or gauge step |

## F. Count integrity (3 units)

| # | Test | Pass |
|---|---|---|
| F1 | Remove the cell at random points during 200 counting bursts (USB unplugged) | After reinsertion the count equals the last shown value or that value + 1. Never ERR, never lower. **Stop** on any lower or corrupted count |
| F2 | 10,000 presses (a press jig or fidgeting sessions) | Count exact; no ERR |
| F3 | Firmware re-flash on a unit with count 1234 | Count still 1234 after the update |
| F4 | Reset-key abuse: quick taps, 1 s holds, 11 s hold, COUNT during hold, both keys together | Only a ≥ 2 s hold-and-release before 10 s resets; increment always wins |

## G. Enclosure and assembly (all units in the first batch)

| # | Test | Pass |
|---|---|---|
| G1 | Home assembly per `mechanical/q5/README.md`; record time and any rework | ≤ 30 min per unit after the first; no lifted pads |
| G2 | USB-C plug fit: 3 cable brands, both orientations | Fully mates and charges with the enclosure closed |
| G0 | Print the tolerance coupon first (plate holes 13.95/14.05/14.15 mm; cross sockets ±0.05 mm) | Choose the hole and socket that give a firm switch clip and a snug keycap; update the generator |
| G2b | Hot-swap: clip both switches into the plate, press plate + switches into SW1/SW2 | Both switches seat fully (housing flush on the PCB) and click; 20 remove/insert cycles with no loose socket |
| G3 | Keycaps: travel, wobble, return; 1,000 presses each | Full travel, no binding or cracking; the pressed keycap clears the plate and screw bores |
| G4 | Pinhole reaches SW3 with a standard paper clip | Clean click; no need to open the case |
| G5 | Self-tapping M2 × 6 screws (C357360): 5 open/close cycles | Threads hold in the 1.7 mm pilots (or specify heat-set inserts in the next print) |
| G6 | Cell replacement by a non-technical person following the README | Succeeds without tools other than a screwdriver |

## Exit criteria for a production quote

All **stop** tests pass on every tested unit. Each recorded value is inside its pass band, or has an accepted design change. Then update `docs/REVIEW-Q5-2026-09-25.md` and `docs/open-issues.md` (E28–E32), and only then request production quotes for more than the first-article quantity.
