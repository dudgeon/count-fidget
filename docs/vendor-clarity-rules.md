# Vendor clarity rules (canonical, from 29 September 2026)

**Why these rules exist.** On the first Q5 order, JLC's engineer could not confirm the orientation of D1, D2, U2, U4, U6 and U7. Those were exactly the polarised parts with no silkscreen marking; the footprints had been inherited without silk bodies. JLC's engineer-"corrected" placement then showed U2 and U7 rotated 180°. Placed that way, the charger and the power latch would have been destroyed or dead. The upload preview had been correct.

The root cause was the design, not the vendor: nothing on the board said where pin 1 was. These rules make every future order self-explanatory, and the build enforces them.

## 1. Every polarised part carries unambiguous pin-1 silkscreen (enforced)

- **Accepted marker types:**
  - the footprint's own pin-1 triangle (U1, U3, U5, U8);
  - a diode cathode bar at pad 1 (D4);
  - the battery holder's +/− marks (BT1);
  - otherwise, a **0.5 mm filled silk dot** planned by `scripts/plan_q5_pin1_marks.py` and applied by `finish_q5_board.py`: U2, U4, U6, U7, Q1–Q5, D1, D2 and D3.
- **Dot placement rules** (recorded in `electronics/q5/pin1-markers.json`):
  - it is at most 0.75 × as far from pin 1 as from any other pin of the part, so it can never sit between pins;
  - it is closer to pin 1 than to any pad of another part;
  - it keeps ≥ 0.2 mm (never < 0.15 mm, JLC's minimum) from copper pads and via drills (vias are tented);
  - it keeps ≥ 0.15 mm from other silkscreen;
  - it stays outside every part body, so it remains visible after assembly;
  - it stays ≥ 0.5 mm inside the board edge.
- **The dots are board-level silkscreen**, so footprints stay identical to the library and KiCad reports no library mismatch.
- **`verify_q5.py` fails the build** if any of these holds:
  - a polarised part has no qualifying marker;
  - a planned dot is missing or ambiguous;
  - any fitted U/Q/D part is missing from the rule, so a new chip cannot slip in unmarked.
- **`test_verify_q5.py` proves the rule works:** it corrupts the board by deleting a dot, moving a dot between pins, and leaving U7 unmarked, and each corruption must be rejected.
- **After any placement change**, re-run `plan_q5_pin1_marks.py`, then `finish_q5_board.py --refill-only`, then `verify_q5.py --kicad-cli …`.

## 2. Upload the JLC-corrected placement file (generated, not hand-edited)

`export_q5.py` now also writes, and records in its manifest:
- `CPL-JLCPCB-Q5[-FULL-ASSEMBLY]-JLC-CORRECTED.csv`, the raw KiCad CPL with rotations and centroids corrected to JLC's own library footprints (`scripts/q5_jlc_footprint_check/`). Generation fails if the footprint-fit data is stale; re-run the check after any BOM or footprint change.
- `POLARITY-REFERENCE-Q5.pdf/.png/.csv`: the bottom side drawn as JLC's photos show it (seen from below, mirrored). It rings and labels pin 1 of every polarised part with its function and net. The CSV gives coordinates, marker type and the uploaded CPL rotation.

## 3. Tell the assembler up front

In the JLC order's remark / special-instructions field, paste:

> Single-sided assembly on the BOTTOM side (display DS1 through-hole on top). Please place every part exactly at the uploaded CPL rotations; they are already corrected to JLC library orientation and were checked against the placement preview. Pin 1 of every polarised part is marked on the bottom silkscreen (dot, triangle or cathode bar). If any orientation is unclear, please email the placement photo before changing a rotation; a pin-1 reference drawing (POLARITY-REFERENCE-Q5.pdf) is available.

Keep **"Confirm Parts Placement"** switched on so questions come back before production.

## 4. Answering an engineering query

1. Download the placement photo from the email.
2. Overlay our pin-1 pads by calibrating on the four mounting holes (the method is in `procurement/q5/JLC-QUOTE-Q5.md`, "JLC engineering query"), or compare it by eye with `POLARITY-REFERENCE-Q5-BOTTOM.png`. Both use the same mirrored view.
3. Reply part by part: "correct as shown", or "rotate N°: pin 1 (function) must be on the pad at …". Attach the annotated picture.
4. Never approve an engineer-"corrected" placement without checking every polarised part, not only the ones asked about.
5. Record the outcome in `procurement/q5/JLC-QUOTE-Q5.md`, without order or account numbers.

## 5. Adding parts or footprints later

- **New footprint:** a footprint for a polarised part should bring its own silk body and pin-1 marker. If it doesn't, the planner adds a dot automatically. Either way the verifier requires one.
- **New polarised reference** outside U/Q/D/BT/DS: add it to `POLARISED` in `plan_q5_pin1_marks.py` and `verify_q5.py`.
- **After any BOM or footprint change:** re-run `scripts/q5_jlc_footprint_check/` (fetch → dump → analyze → corrections), then `export_q5.py`.
