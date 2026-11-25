# Q5B: bezel tray, one-piece acrylic faceplate, hidden switch plate (three options)

Q5B is an enclosure for the **ordered, locked Q5 board**. It does not change the board, the BOM or any Q5/Q5A file. The owner set these requirements on 24–25 Nov 2026:

- **Switches and caps:** Kailh Box Jade switches with standard MX keycaps. The caps were measured assembled: the pair is **36.9 × 18.0 mm**.
- **Top:** one solid clear acrylic piece. A two-part bottom is fine.
- **Case:** a printed bezel round the acrylic, thick walls and a bottom chamfer.
- **Keys:** they must not sit proud.
- **Hardware (owner's stock):** M2.5 screws in **20 and 25 mm only**, M2.5 nuts, and **3/16 in (4.76 mm)** clear acrylic. The two board holes at the display end are drilled out to **7/64 in**. They are unplated; the nearest trace is 0.4 mm outside the new hole.
- **Switch plate:** printed, with the pegs built in.

The owner has not chosen yet, so there are three options. All three share the same board stack, faceplate height and key opening. **Option C was redesigned with the owner on 25 Nov 2026** as a two-print sandwich; see its own section below. The "Shared design" and "Parts per option" sections describe A and B.

| | **A: lip** (`lip/`) | **B: four screws** (`four/`) | **C: clear sandwich** (`sandwich/`) |
|---|---|---|---|
| Body | **47.0 × 59.0 × 21.1 mm** (original footprint) | 47.0 × 63.25 × 20.3 mm | 47.0 × 63.25 × 23.8 mm (25.8 on its feet) |
| Faceplate fixing | 2 × M2.5 × 20 at the display end. At the key end, the acrylic edge sits 0.7 mm under a printed lip. | 4 × M2.5 × 20. The key-end pair are on tray posts just outside the board edge. | 4 × **M2.5 × 25** straight through both acrylic sheets, into nuts in hex pockets lasered into the back panel's outside face. |
| Bezel | Stands 0.8 mm above the acrylic all round | Flush with the acrylic | Flush with the acrylic |
| Bottom | Printed floor, nuts in printed pockets | Printed floor, nuts in printed pockets | **Clear 3/16 in panel**, full outline. No printed floor: the board's underside is visible. |
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

## Option C: clear sandwich (`sandwich/`)

The owner's design goals for C are the most view of the board from above and below, and the fewest printed parts.

**Stack, bottom to top:** feet 2.0, back acrylic 4.76, corner standoffs 6.02, board 1.6, upper piece 6.7 (its plate is at the standard MX height), top acrylic 4.76.

| Part | File | Notes |
|---|---|---|
| Top acrylic | `faceplate-acrylic-Q5B.svg` / `.dxf` | 3/16 in clear. Four 2.9 mm holes and the 38.1 × 19.2 mm key opening. |
| **Upper piece** (print 1) | `upper-piece-with-supports-Q5B.stl` | Switch plate (2 mm rings round the switches), two spacer bosses on 3.2 mm arms beside the display, and two key-end blocks. |
| **Surround** (print 2) | `surround-Q5B.stl` | 2.0 mm ring, flush with the top acrylic, with four corner standoffs joined to the walls and a USB shelf. No floor. |
| Back acrylic | `back-panel-acrylic-Q5B.svg` / `.dxf` | 3/16 in clear, full outline. |
| Feet (optional print) | `foot-2.0-Q5B.stl` × 4 | 8 mm discs, glued on. Stick-on bumpers of 2 mm or more also work. |

**Fasteners:**
- 4 × M2.5 × 25 pan head and 4 × M2.5 nuts, through everything.
- 2 × M2 × 10 self-tapping pan head (head 3.8 mm or less). Each goes through a key-end block and the board's key-end hole into a 1.7 mm pilot hole in the surround's standoff, with 4.4 mm of thread in the plastic. They replace printed locating pins (the owner's change).

**Printing (0.4 mm nozzle, 0.2 mm layers, PETG):**
- **Upper piece:** print it as exported, top side down. The arms, bosses and blocks sit on the bed. The plate hangs 1.7 mm above the bed on built-in support ribs (0.5 mm wide, 0.2 mm gap under the plate). Turn slicer supports off, then break the rib grid off the plate afterwards. `upper-piece-no-supports-Q5B.stl` is the same part without ribs, for slicer supports.
- **M2 counterbores:** each has a 0.25 mm sacrificial skin over the screw hole so the counterbore roof bridges cleanly. The screw pierces it.
- **Surround:** print it back-panel side down. It needs no supports. The USB opening's top edge is a 13.4 mm bridge. The bed edge has a 0.3 mm chamfer.
- **Plate fit:** print `plate-fit-coupon-printable-Q5B.stl` first if your printer runs holes small.

**Back panel SVG:**
- **Orientation:** drawn as seen from outside. Lay the panel outside face up.
- **Red:** cut (outline, four screw holes, the 1.5 mm reset pinhole).
- **Grey fill:** the four hex nut pockets. Engrave them **2.05 mm deep**, and test the depth on scrap first.
- **Blue:** the battery warning, to engrave. Convert the text to paths if your laser software needs it.
- **Green dashed:** where the feet go. Reference only; switch it off before cutting.

**Assembly:**
1. Fit the LIR2032 with USB connected (Q5 USB-first rule). Drop the board into the surround, onto the four corner standoffs.
2. Lay the upper piece on the board and drive the two M2 screws. The board is now fixed.
3. Clip the Box Jades into the plate.
4. Press the four nuts into the back panel's pockets from outside. Tape holds them.
5. Put the top acrylic in the bezel, hold the back panel under the surround and drive the four M2.5 × 25 screws.
6. Stick the feet on, clear of the screws. Press the keycaps on.

**The screw tips stand 1.2 mm proud of the back** (0.9 to 1.4 mm over the accepted acrylic thickness range). The 2 mm feet keep them off the table. The alternative is trimming the screws to 23.5 mm.

**Checks:** zero intersections and zero collisions over 427 vertical assembly poses. `sandwich/drawings/` has the agreed plan, the three sections and two views of the printed parts. `scripts/q5b_sections/draw_option_c.py` draws the sections.

## What the generator checks

`scripts/build_q5b_enclosure.py` builds A or B per run (`Q5B_VARIANT=lip|four`). Option C has its own generator, `scripts/build_q5b_sandwich.py`.

For each option, the final build found:
- **Parts:** valid single solids; every STL is manifold and sits on the bed.
- **Static clearance:** zero intersections between the case parts, both acrylic parts, the switches, spacers, collars, standoffs, screws, nuts, the board, every component envelope and the USB plug space.
- **Keycaps:** clear at rest and fully pressed (4.0 mm travel, with a 0.3 mm wobble allowance), against the thickest accepted faceplate (5.0 mm) and everything else.
- **Assembly paths:** zero collisions on straight vertical paths, plus the tilt-and-swing faceplate path in A. That is 520 / 488 poses (427 for C).

## Not established (first-article checks)

Nothing here is a measurement. Before calling Q5B done, check:
- **Switches and caps:**
  - Box Jade fit in the printed plate (use the coupon);
  - keycap **skirt height**, which is assumed at PCB top + 11.0. Only the plan size was measured.
- **Faceplate and lip (A):**
  - lip retention and fit on a real print;
  - the acrylic lip insertion.
- **Option C:** laser nut-pocket depth; support-rib removal; M2 thread strength in the printed standoffs; screw tips against the feet.
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

`scripts/render_q5b/` renders options A and B (C has drawings only, in `sandwich/drawings/`):
- **Board:** the native board textures and KiCad STEP models.
- **Enclosure:** the checked enclosure parts.
- **Display:** firmware OLED frames.
- **Appearance models:** the Box Jade, screws, nuts and keycaps are appearance models.
- **Substitutions:** Blender's bundled `studio.exr` stands in for the Poly Haven HDRIs, and DejaVu for the decal fonts.

```sh
for v in lip four; do
  Q5B_VARIANT=$v python3 -B scripts/build_q5b_enclosure.py --kicad-python /usr/bin/python3
  Q5B_VARIANT=$v python3 -B scripts/render_q5b/build_render_assets.py --kicad-python /usr/bin/python3
  Q5B_VARIANT=$v python3 -B scripts/render_q5b/render_stills.py -- --shots hero,top,exploded2,under --samples 128
done
```
