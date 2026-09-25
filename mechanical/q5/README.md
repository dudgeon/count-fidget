# Q5 enclosure and home completion

The Q5 body is **47.2 × 59.2 mm with a 16.2 mm display-cover height** and a 27.0 mm keycap envelope height. Q4 was 50 × 60 × 19.6 mm with a 30.4 mm keycap envelope. It fits the unchanged 42 × 54 × 1 mm board outline. The STEP assembly and PNGs use the native Q5 board positions and simplified component envelopes. They are not exact vendor assembly CAD.

Changes from Q4 and why:

| Change | Reason |
|---|---|
| **USB opening 13.4 × 7.2 mm**, centred on the receptacle axis and cut through to the receptacle face | Issue #4. The Q4 opening was 4.8 mm tall and 3.4 mm in front of the receptacle, so standard overmolded plugs could not seat. The fit check reserves a USB-IF maximum 12.35 × 6.5 mm overmold plus 0.1 mm per side, from the outer wall to the receptacle face. |
| **No pack bay, keeper or harness corridor** | Issue #13. The LIR2032 cell sits in the vendor-soldered BT1 holder under the PCB, and the NTC is on the board. The Q4 battery keeper and its two M2 × 5 screws are gone. |
| **PCB 3.4 mm lower, side clearance 1.0 mm** | The holder (5.52 mm) plus 0.58 mm floor gap sets the stack height. This saves 2.8 mm in width, 0.8 mm in depth and 3.4 mm in height. |
| **Printed MX keycaps** with a cross socket and engraved legends (+ on COUNT, ○ on RESET) | Issue #13. Keycaps are no longer an unsourced item. |
| **Bottom reset pinhole** (2.4 mm) under SW3 | Provides the hardware reset (NRST) the user asked for. On battery it is a full power cycle; with USB it is the DFU entry reset. |
| **Two load supports** under the key area (board 5.5, 42.8 and 34.0, 44.0) | Carry key-press force past the holder into the floor. |

## Parts and hardware

| Item | Qty | Specification / status |
|---|---:|---|
| Base, front display cover, rear key plate, COUNT keycap, RESET keycap | 1 each | Five STL files, already in print orientation |
| Board/cover screws | 4 | M2 × 12. The pilots stop 0.8 mm above the outer floor, and the screw-tip check is in the fit report |
| Rear display supports | 2 | Compliant 2.5 mm annuli, as in Q4 |
| OLED module, header, 2 key switches | — | HS96L01W4S03, PZ254V-11-07P, CPG151101D13 (home through-hole, JLC catalogue parts) |
| Cell | 1 | **User-supplied LIR2032 (rechargeable Li-ion, 4.2 V) only.** Never fit a CR2032 or ML2032 primary cell: the charger would try to charge it. |

## Assembly sequence

1. Print and inspect the five parts. Check the keycap cross sockets on one switch before fitting.
2. Seat both switches in the **rear key plate before soldering** their four leads (as in Q4).
3. With the front cover off, solder the seven-pin header between the host PCB and the module: 14 joints. Trim pins to ≤ 1 mm. Home soldering totals **18 joints**, unchanged.
4. Fit the two display supports.
5. **Insert the cell with USB connected** (BQ2970 first-connection behaviour and the retained cold-insertion counterexample; see [the Q5 power design](../../docs/q5-power-design.md)). Observe + up in the holder. The board powers up from USB, shows the count and the CHG label.
6. Lower the PCB assembly vertically into the base and fit the two rear screws. Program/verify firmware now if needed (see [Q5 firmware](../../docs/q5-firmware.md)).
7. Lower the front cover and fit its two screws. Press on the keycaps. Check travel, the USB plug (both orientations) and the reset pinhole.

To replace the cell, remove the four screws and lift the PCB assembly out. The holder is on the underside.

## What the geometry checks establish

`fit-report.json` and `build-manifest.json` bind the native Q5 board and model, the generator and the firmware pixel renderer. The final build found:
- five valid single solids with manifold STL meshes;
- zero static intersections;
- zero collisions in 162 sampled vertical assembly/removal poses (18,063 tests).

The minimum modelled distances are in the report:
- holder to bottom components: 0.05 mm, a bounding-box gap and not an overlap;
- pressed keycap to rear screw: 1.2 mm;
- USB mouth to outer wall: 2.0 mm.

Not established: print tolerances, thread strength, cell retention and insertion force, keycap fit/travel, real USB plug fit, drops, or display support material. Inspect a physical first article.

Build: `python3 -B scripts/build_q5_enclosure.py --kicad-python "$(which python3)"` (CadQuery 2.8, NumPy, Pillow, KiCad Python bindings).
