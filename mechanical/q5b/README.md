# Q5B: bezel tray, one-piece acrylic faceplate, hidden switch plate (three options)

Q5B is an enclosure for the **ordered, locked Q5 board**. It does not change the board, the BOM or any Q5/Q5A file. The owner set these requirements on 24–25 Nov 2026:

- **Switches and caps:** Kailh Box Jade switches with standard MX keycaps. The caps were measured assembled: the pair is **36.9 × 18.0 mm**.
- **Top:** one solid clear acrylic piece. A two-part bottom is fine.
- **Case:** a printed bezel round the acrylic, thick walls and a bottom chamfer.
- **Keys:** they must not sit proud.
- **Hardware (owner's stock):** M2.5 screws in **20 and 25 mm only**, M2.5 nuts, and **3/16 in (4.76 mm)** clear acrylic. The two board holes at the display end are drilled out to **7/64 in**. They are unplated; the nearest trace is 0.4 mm outside the new hole.
- **Switch plate:** printed, with the pegs built in.

The owner has not chosen yet, so there are three options. All three share the same board stack, faceplate height and key opening.

| | **A: lip** (`lip/`) | **B: four screws** (`four/`) | **C: clear back** (`back/`) |
|---|---|---|---|
| Body | **47.0 × 59.0 × 21.1 mm** (original footprint) | 47.0 × 63.25 × 20.3 mm | 47.0 × 59.0 × 26.2 mm |
| Faceplate fixing | 2 × M2.5 × 20 at the display end. At the key end, the acrylic edge sits 0.7 mm under a printed lip. | 4 × M2.5 × 20. The key-end pair are on tray posts just outside the board edge. | As A, but with 2 × **M2.5 × 25**. They go through the back panel into nuts in hex pockets lasered into its outside face. |
| Bezel | Stands 0.8 mm above the acrylic all round | Flush with the acrylic | Stands 0.8 mm above the acrylic all round |
| Bottom | Printed floor, nuts in printed pockets | Printed floor, nuts in printed pockets | **Clear 3/16 in panel** on a 1.6 mm frame ledge. Loose printed standoffs carry the board on it. |
| Hidden screws | none | none | none |

Renders: `renders/<option>-<view>.jpg`.

## Shared design

| Decision | Why |
|---|---|
| **Faceplate:** 3/16 in clear cast acrylic, one piece. Its underside is 1.0 mm above the OLED maximum. One **38.1 × 19.2 mm** opening round both caps. | The opening is the measured caps plus 0.6 mm all round. The cap skirts rest 0.46 mm below the acrylic top, and only the caps stand up (8.1 mm above the bezel in A and C). |
| **Switch plate:** hidden, 1.5 mm, at the standard MX height (top = PCB top + 5.0). **Printed in PETG with the two pegs built in.** | The Box Jade clips lock under the plate, so pulling a keycap can't pull a switch out of its hot-swap socket, and key presses load the plate rather than the solder joints. The pegs sit in the board's key-end holes. They locate the plate and hold the board down. |
| **Print the plate top face down.** | The pegs then point up, so it needs no supports. Use 0.25 or 0.15 mm layers so 1.5 mm is a whole number of layers. Print `plate-fit-coupon-printable-Q5B.stl` (13.9–14.2 mm holes) first if your printer runs holes small. |
| **Key-end screws: none in A and C; off the board in B** | The board's key-end holes sit at the keycaps' corners. A screw hole there leaves only about 0.2 mm of acrylic beside the opening. |
| **M2.5 nuts** (5.0 AF × 2.0) in 5.15 AF pockets | With 3/16 in sheet, every screw has the full 2.0 mm of thread in its nut. The tips stay 0.28–0.45 mm inside the bottom surface. |

## Parts per option

**Every option:**
- **Printed:**
  - `plate-with-pegs-printable-Q5B.stl` (PETG, top face down);
  - 2 × `spacer-6.7-Q5B.stl` (OD 5.0 / ID 2.7, solid).
- **Faceplate:** `faceplate-acrylic-Q5B.svg` / `.dxf`, cut from 3/16 in clear acrylic.
- **Screws:** M2.5 pan head (ISO 7045 / DIN 7985), with one M2.5 nut per screw.
- **Not printing the plate:** `plate-acrylic-Q5B.svg` (1.5 mm acrylic) plus the separate `peg-for-acrylic-plate-3.5-Q5B.stl` is the alternative.

| Option | Body | Screws | Extra printed parts | Extra laser parts |
|---|---|---|---|---|
| A | `lip/tray-Q5B.stl` | 2 × M2.5 × 20 | 2 × `collar-1.7-Q5B.stl` (washers between the plate and the faceplate, pinned into the plate) | — |
| B | `four/tray-Q5B.stl` | 4 × M2.5 × 20 | 2 × `spacer-1.7-Q5B.stl` (between the plate and the faceplate on the key-end screws) | — |
| C | `back/frame-Q5B.stl` (walls only) | 2 × M2.5 × **25** | Collars as A, plus loose standoffs: 2 × `screw-standoff`, 2 × `standoff`, 2 × `post`, 1 × `usb-support`. Each is pinned into the panel. | `back-panel-acrylic-Q5B.svg` / `.dxf`, 3/16 in clear |

**Back panel SVG (C):**
- **Orientation:** drawn as seen from outside. Lay the panel outside face up.
- **Red:** cut.
- **Grey fill:** the two hex nut pockets. Engrave them **2.05 mm deep**, and test the depth on scrap first.
- **Blue:** the battery warning, to engrave. Convert the text to paths if your laser software needs it.
- **Reset hole:** the 1.5 mm hole is the reset pinhole.

## Assembly

**A (lip):**
1. Press the two nuts into the pockets under the tray.
2. Fit the LIR2032 with USB connected (Q5 USB-first rule), then drop the board in.
3. Clip the Box Jades into the plate. Lower the plate so the switch pins enter the sockets and the peg pins enter the board's key-end holes.
4. Put a collar on each peg position and a 6.7 mm spacer on each display-end hole.
5. **Fit the faceplate.** Hold it with the display end tipped up about 7° and shifted 1 mm toward the display end. Lower it until the key-end edge is level with the lip, slide that edge under the lip, then swing the display end down. The generator checks this path.
6. Drive the two M2.5 × 20 screws. Press the keycaps on.

**B (four screws):** as A, with these changes:
- In step 4, put 1.7 mm spacers on the plate over the key-end posts instead of collars.
- In step 5, lower the faceplate straight down.
- Drive four screws.

**C (clear back):**
1. Press the two nuts into the panel's pockets from outside. Tape holds them until the screws are in.
2. Lay the panel in the frame on the bottom ledge.
3. Stand the loose standoffs, posts and USB support in their panel holes.
4. Continue as A from step 2.

## What the generator checks

`scripts/build_q5b_enclosure.py` builds one option per run. Select it with `Q5B_VARIANT=lip|four|back`.

For each option, the final build found:
- **Parts:** valid single solids; every STL is manifold and sits on the bed.
- **Static clearance:** zero intersections between the case parts, both acrylic parts, the switches, spacers, collars, standoffs, screws, nuts, the board, every component envelope and the USB plug space.
- **Keycaps:** clear at rest and fully pressed (4.0 mm travel, with a 0.3 mm wobble allowance), against the thickest accepted faceplate (5.0 mm) and everything else.
- **Assembly paths:** zero collisions on straight vertical paths, plus the tilt-and-swing faceplate path in A and C. That is 520 / 488 / 642 poses.

## Not established (first-article checks)

Nothing here is a measurement. Before calling Q5B done, check:
- **Switches and caps:**
  - Box Jade fit in the printed plate (use the coupon);
  - keycap **skirt height**, which is assumed at PCB top + 11.0. Only the plan size was measured.
- **Faceplate and lip (A, C):**
  - lip retention and fit on a real print;
  - the acrylic lip insertion.
- **Back panel (C):** laser nut-pocket depth.
- **Hardware fit:**
  - nut-pocket fit;
  - spacer and collar lengths (check with calipers);
  - peg-pin fit in the 2.2 mm holes.
- **Board:** the drilled 7/64 in holes.
- **Acrylic:** crazing at the screw holes. Don't over-tighten, and **don't use anaerobic threadlocker (Loctite 242/243/271)**: it stress-cracks acrylic and PETG.
- **Use:**
  - OLED readability through 4.76 mm of acrylic;
  - USB cable fit;
  - drop behaviour.

## Renders

`scripts/render_q5b/` renders each option:
- **Board:** the native board textures and KiCad STEP models.
- **Enclosure:** the checked enclosure parts.
- **Display:** firmware OLED frames.
- **Appearance models:** the Box Jade, screws, nuts and keycaps are appearance models.
- **Substitutions:** Blender's bundled `studio.exr` stands in for the Poly Haven HDRIs, and DejaVu for the decal fonts.

```sh
for v in lip four back; do
  Q5B_VARIANT=$v python3 -B scripts/build_q5b_enclosure.py --kicad-python /usr/bin/python3
  Q5B_VARIANT=$v python3 -B scripts/render_q5b/build_render_assets.py --kicad-python /usr/bin/python3
  Q5B_VARIANT=$v python3 -B scripts/render_q5b/render_stills.py -- --shots hero,top,exploded2,under --samples 128
done
```
