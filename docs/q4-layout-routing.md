# Q4 routed engineering checkpoint — 25 September 2026 UTC

The 42 × 54 × 1 mm, two-layer board has **86 references, 70 fitted positions** (67 JLC SMT and three home through-hole parts). Four 2.2 mm mounting holes support the PCB. This is an engineering candidate; quotations, purchases and manufacture remain paused.

## Native result and reproducibility

Final PCB SHA-256: `2b073a519171d1632d67138ff7be2bf7271f6a5f8a328d8e9e5b5cff7cc47780`.

Fresh native KiCad checks found **zero physical violations, zero unconnected items and zero schematic parity issues**, with no DRC exclusions. Root's full validation and artifact manifests provide the separate final source binding. Requested construction is 35 µm copper per side, 0.93 mm FR4 core, green mask and ENIG; no fabricator has approved that construction for Q4.

[`preroute_q4.py`](../scripts/preroute_q4.py) fixes 128 local copper items before the headless router. [`finish_q4_board.py`](../scripts/finish_q4_board.py) preserves exactly that recorded seed, imports the incremental SES, removes pointless no-connect fanout, makes the explicit local USB/fanout corrections, synchronizes native fields, and fills both GND pours. Its replay check compares actual track/via geometry, rather than claiming byte-identical native UUIDs. The DSN/SES remain ignored local exchange files; their hashes are recorded in [routing evidence](../electronics/q4/routing-audit.json) and [replay evidence](../verification/q4-routing-replay.json).

Local solid GND connections are used on the USB shell, charger exposed pad, D1 ground, battery connector ground and U7 ground where isolated thermal spokes were unsuitable. They are explicit copper choices, not waived errors; soldering and thermal behavior still require qualification.

## Actual routed paths

Measurements include pad-center joins and planar copper length. They exclude package propagation and ground-plane travel; they do not establish impedance, transient response or physical function.

| Connection | Planar length | Vias |
|---|---:|---:|
| MCU D− to USB-C A7 / B7 | 12.613 / 10.013 mm | 0 / 0 |
| MCU D+ to USB-C A6 / B6 | 8.623 / 7.765 mm | 0 / 0 |
| U3 input to C5 / output to C6 | 1.570 / 4.106 mm | 0 / 0 |
| U3 feedback to R30 / R31 | 1.309 / 2.959 mm | 0 / 0 |
| Charger input / SYS / BAT bypass | 1.816 / 2.748 / 4.550 mm | 0 / 0 / 2 |
| Five MCU supply bypass branches | 1.969–3.413 mm | 0 |
| FRAM VDD to C36 / C30 | 2.295 / 3.770 mm | 0 / 0 |
| OLED / SYS slew capacitor connections | 1.997 / 1.888 mm | 0 / 0 |
| Thermal comparator supply bypass | 2.050 mm | 0 |
| Raw-negative / battery-sense bypass | 2.966 / 6.634 mm | 0 / 0 |
| D1 / D2 clamp-rail bypass | 2.716 / 5.099 mm | 0 / 2 |

The USB data paths stay on B.Cu. A local VBUS layer change replaces the router's unnecessary pair of D− signal vias. These short full-speed paths are not claimed to be length-matched or controlled-impedance qualified; USB recovery, cable interoperability, eye/ESD behavior and return-current paths require first-article testing.

Bypass ground stubs reach a same-net via in 1.10–2.55 mm, excluding the plane path. The FRAM feed remains exclusively through R32. The U4 raw-negative sense remains a separate net with a dedicated local return; no blanket opposite-layer keepout was invented. The final same-net through-via audit found no overlap with SMT solder lands and no conservative gap below 0.1 mm; round test pads use their circular geometry. Through-via tenting and solder-mask process acceptance remain open.

## Placement and retained gates

Regulator bypass/divider, FRAM bypass, comparator bypass and OLED-switch input bypass were moved locally to improve their actual routes. R31 was moved to y=6.2 mm, R30 to y=7.85 mm and C6 to y=9.75 mm to clear the module-header solder envelope while preserving the local regulator circuit. No selected component identity changed during routing.

Native checks do not close the common-rail tolerance/transient, effective-capacitance, insertion-current/protector, charger/temperature, battery-pack, FRAM brownout, OLED current/interface, home-soldering, mechanical-tolerance or runtime gates. See the power contract, firmware review and final mechanical review for their separate evidence and limitations.
