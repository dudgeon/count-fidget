# Bring-up log — CF-0N

Procedure: [docs/board-bring-up.md](../../docs/board-bring-up.md). Record measured values. Mark each row PASS / FAIL / SKIP and note anything odd.

| Field | Value |
|---|---|
| Board ID | CF-0N |
| Date | |
| Operator | |
| DFU serial (from the flasher) | |
| Firmware image SHA-256 (first 12) | |
| Instruments (multimeter; USB meter or "none") | |
| **Status** | NOT STARTED / PASS-BARE / PASS-NOMETER / PASS / HOLD / REJECT |

## Stages 0–1 — Identify, rails

| Step | Result | Notes |
|---|---|---|
| Photos taken (both sides) | | |
| Edge rails removed, edges smoothed | | |

## Stage 2 — Visual (A1)

| Check | Result | Notes |
|---|---|---|
| BT1 seated, + on CELL_P | | |
| U2 pin 1 | | |
| U7 pin 1 | | |
| U1, U3–U6, U8, Q1–Q5, D1–D4 orientation | | |
| No bridges / tombstones / balls | | |
| J1 stakes, mouth clear | | |
| SW1/SW2 sockets flat and soldered | | |
| SW3 present, clicks | | |
| DS1 flat, glass OK, pins trimmed | | |

## Stage 3 — Unpowered resistance (A2, A2b)

| Measure | Value | Result |
|---|---|---|
| VBUS (TP5) → GND | Ω | |
| SYS (TP6) → GND | Ω | |
| VLOGIC (TP2) → GND | Ω | |
| BT1 + contact → pad 1 (CELL_P) | Ω | |

## Stage 4 — Switches

| Step | Result | Notes |
|---|---|---|
| SW1 COUNT fitted, clicks | | |
| SW2 RESET fitted, clicks | | |

## Stage 5 — First power, USB only (A3)

| Measure | Value | Pass band | Result |
|---|---|---|---|
| 5 s power-on: no warm part, smell or port shutdown | | | |
| USB current (if a meter is available) | mA | < 30 mA | |
| TP5 VBUS | V | ≈ 5 V | |
| TP6 SYS | V | ≈ 4.5 V | |
| TP2 VLOGIC | V | 3.15–3.26 V | |
| No warm parts after 1 min | | | |

## Stage 6 — Flash and commission (A4, A6)

| Step | Result | Notes |
|---|---|---|
| DFU enumerates (`list`) | | cable: |
| Flash PASS (attempts) | | |
| A6: digits within ~1 s after flash, no pinhole | | |
| Q1 after flash: `0 ERR` or previous count | | |
| Q2 hold RESET 2 s: RST then `0`, no ERR | | |
| Q3 COUNT ×3: `3`, bars or CHG | | |
| Q4 hold RESET 2 s: `0` | | |

## Stage 7 — Restart, cell, battery (A5, B7)

| Step | Result | Notes |
|---|---|---|
| USB unplug/replug: count kept, no ERR | | |
| Pinhole with USB: count kept, no ERR | | |
| Cell fitted USB-first: CHG or full gauge | | cell brand: |
| On battery: count + bars shown | | |
| Display off after 30 s | | |
| COUNT wakes, +1 exactly | | before → after: |
| Pinhole on battery: off; COUNT restores count | | |

## Stage 8 — Enclosure (G1–G4)

| Step | Result | Notes |
|---|---|---|
| Enclosure used (Q5 / Q5A) | | |
| G1 assembly time, rework | | min |
| G2 USB-C fit, both orientations, 2 cables, CHG | | |
| G3 keycaps travel/return | | |
| G4 pinhole reachable | | |
| Count correct after assembly | | |

## Notes and faults

