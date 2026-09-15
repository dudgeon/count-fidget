# Q2 enclosure fit candidate

These are real, editable/exported Q2 CAD files for a **50 × 45 × 19.8 mm** enclosure around the current 42 × 40 × 1 mm PCB. Estimated overall height with the provisional keycaps is 29.8 mm. They replace the obsolete fit assumptions for this candidate only; all files in the parent `mechanical/` directory remain historical Rev0 evidence.

**Engineering fit candidate, not released print files.** The shell/keeper are generated solids. Purchased components, pins, screws and keycaps are simplified envelopes. No printed sample, finished battery pack, actual keycap or cable has been fitted. The current electronics retain their documented qualification gates.

## Files

| File | Contents |
|---|---|
| `enclosure-Q2.step` | Assembled base, lid, keeper and named component envelopes, in assembly coordinates |
| `base-Q2.stl` | Printable base, upright with floor at Z=0 |
| `lid-Q2.stl` | Lid inverted, bezel face at Z=0; supports needed under the surrounding face |
| `battery-keeper-Q2.stl` | Separate screw-retained keeper, flat at Z=0 |
| `assembled-Q2.png`, `exploded-Q2.png` | Rendered CAD views |
| `interior-Q2.png`, `battery-bay-Q2.png` | Internal layout and battery access views |
| `board-geometry.json` | Native KiCad footprint bounding boxes, pads/drills and board/model hashes used for this build |
| `fit-report.json` | Solid validity, intersection checks, model distances and explicit limitations |
| `build-manifest.json` | Generator, board/model and generated-output SHA-256 identities |

No enclosure printing charge is included in the vendor electronics quote: Geoff prints and fits the case. The STEP/STLs support quotation review and the later physical fit prototype; they do not authorize manufacture of the electronics.

## Geometry and design choices

Coordinates in the source are millimetres, with `CAD X = board X −21`, `CAD Y = board Y −20`; Y follows the board's top-view convention. Z starts at the base bottom. The script reads the native Q2 board without modifying it, compares all placed parts with `electronics/q2/netlist-Q2.json`, and rejects changed dimensions or component anchors.

| Feature | Candidate geometry |
|---|---|
| PCB | Bottom Z=10.5; top Z=11.5; nominal 2 mm outline corner radius |
| Base | 1.6 mm floor/walls; nominal board-side clearance 2.4 mm along X and 0.9 mm along Y |
| Mounts | Existing board holes at (2.5,37.5), (39.5,37.5); two base bosses and corresponding lid spacers/screws |
| Switches | Stem centers (11.475,28), (30.525,28); 16.4 mm square lid clearances; PCB-load support posts at (6,30.5), (36,30.5) |
| LCD | Center (21,8.75); rear glass 4.0 mm above PCB top; nominal 34.9 ×13 ×2.2 mm; 13.0 mm lead rows |
| LCD pocket | 36.2 ×14.8 mm; roof above pocket at Z=18.8; viewing aperture 32.7 ×7.2 mm; raised bezel top Z=19.8 |
| USB | Right-side opening centered at board Y=13.3, 13.2 mm wide ×5.0 mm high, bottom Z=11.1 |
| Pack | Finished insulated cylindrical body up to Ø21 ×4.2 mm; bottom Z=1.9 on a 0.3 mm seating layer; tray bore Ø21.8 mm |
| Keeper | Plate underside Z=6.4, 0.3 mm nominal above maximum pack; independent screws retain it before the PCB is fitted |
| Harness | 2.0 mm-wide side corridor around the left PCB edge, plus under-board and flexible tab/NTC exit reservations |

The width and PCB height increases provide a route around the intact PCB edge for the four-wire harness and room for the keeper below the switch tails. They are explicit enclosure choices, not changes to the electrical layout. The specified 40 ±5 mm, 30 AWG pack leads still require a finished-pack drawing and a trial route; the reservation boxes are not a qualified cable model. The mating JST plug and its insertion/bend sweep remain to be confirmed.

The LCD's manufacturer drawing includes a **2.85 mm maximum thickness** and ±0.2 mm body-length/general tolerances. The clearance check therefore uses 35.1 ×13.2 ×2.85 mm, not just the 2.2 mm nominal render. At the specified 4 mm standoff this leaves 0.45 mm nominal below the pocket roof. The enlarged pocket also allows space around the bent lead rows. It does not resolve hole/lead tolerances, solder exposure or LCD qualification. [Display Elektronik DE188 Rev4 drawing](https://display-elektronik.de/filter/DE188-RU-30_75_3V.pdf).

Two **nonconductive compliant pads**, nominal 4 mm assembled thickness, support the glass rear near board coordinates (5.5,8.5) and (36.5,5). Their material, final compressed thickness, adhesive and contact pressure require approval with the actual LCD. They are separate envelope parts in STEP; do not replace them with an unqualified hard clamp. The lid intentionally clears the glass.

The USB body envelope uses 7.35 ×8.94 ×3.31 mm and the native right-facing anchor. A 12 ×4.6 mm cable-entry reservation passes through the wall opening. This is an explicit candidate plug limit, not a claim that every USB-C cable overmold fits the recessed receptacle. [GCT USB4105 dimensions](https://gct.co/connector/usb4105).

The switch envelope distinguishes a 14 mm lower region through the first 5 mm above the board from the 15.6 mm upper envelope. Keycap bodies are provisional 18.2 mm square envelopes with a checked 4 mm downward travel. Actual clips, stem fit, keycap skirt, bottom-out height and board loading still need a sample. The lid clearance is not a qualified MX mounting plate. [Cherry MX series drawing](https://media.digikey.com/PDF/Data%20Sheets/Cherry%20PDFs/MX%20Series.pdf).

## Retention and assembly sequence

The following is a prototype assembly procedure for unpowered parts. It does not approve installing or charging an unqualified cell.

1. Print and deburr all three parts. Inspect the pilot/clearance holes and remove support material completely. Check the base/lid fit with an empty board before installing the battery assembly.
2. Fit the insulated approved pack on its 0.3 mm seating layer. Orient the flexible tab/NTC exit toward the left-front tray notch. Fit the keeper with **two M2 ×5 screws**. It limits upward travel while leaving 0.3 mm nominal pack clearance; do not tighten a changed geometry onto the cell or its sensor.
3. Route the insulated leads through the left-side corridor, protecting them from PCB edges and keeper screws. Complete connector engagement and strain relief using the approved pack drawing. The current reservation requires a routed bundle no thicker than 2.0 mm at the side passage.
4. Seat the PCB on its two mounting bosses and two load-support posts, without trapping wiring or touching solder tails. Programming and electrical tests occur before final enclosure closure; the keeper can obstruct access to underside fixture lands.
5. Confirm the installed LCD standoff and compliant supports. With keycaps removed, engage the two front lid hooks, lower the lid and fit **two M2 ×12 rear screws** through the real board holes into the base bosses. Fit the keycaps afterward and check their full travel.

Fastener models assume **head diameter ≤4.0 mm and head height ≤1.7 mm**. Rear screw heads seat at Z=16.5; nominal tips end at Z=4.5. Keeper screw heads seat at Z=7.6; nominal tips end at Z=2.6. These limits avoid the model's cell and base floor. Obtain actual screws meeting this envelope; a longer screw is not automatically acceptable.

Base pilot holes are provisionally Ø1.7 mm and lid/keeper clearance holes Ø2.4 mm. Qualify thread formation, material strength and torque on a spare printed boss before assembly; the pilot dimension is not a validated universal thread specification. The rear lid spacers are Ø3.6/2.4 mm and need careful print inspection. Front hooks provide nominal 0.3 mm engagement clearance. Screw and hook durability, pack capture and board bending remain physical tests.

## What was checked

`fit-report.json` records checks on the actual generated solids:

- Each printed part is one valid solid; base, lid and keeper have zero mutual overlap.
- Printed parts do not intersect the checked PCB/component envelopes or the specified wire/USB reservation volumes.
- The pack/keeper and fastener envelopes do not intersect the modeled bottom components or switch/LCD tails.
- Quantified nominal distances include pack-to-board, pack-to-switch-tails, keeper screws to bottom components, and maximum LCD glass to MCU/USB/JST.

Bottom-component X/Y envelopes come from native KiCad footprint bounding boxes, including courtyard/pad graphics. Height allowances are 1.1 mm for resistors/0603 parts and 1.6 mm for other bottom parts, including mounting/solder allowance; they are conservative family assumptions, not independently approved maximum drawings for every line item. Pin/post solids primarily preserve position and protrusion assumptions, and do not qualify the actual molded-post/hole diameters. The entire solder fillet and flexible-harness geometry is not modeled.

The intersection list is intentionally narrow and reproducible. It does not represent complete component-to-component mechanical DRC, toleranced motion simulation, strength analysis, electrical insulation approval or a physical fit test. In particular, nominal zero overlap does not establish tolerance clearance.

## Printing and remaining gates

For a first fit prototype, use a dimensionally calibrated printer and inspect walls/bosses before use. The base prints upright; the keeper prints flat; the lid's exported STL rests on its bezel face and needs support under the surrounding lid face, with the underside spacers/hooks facing upward. The nominal wall is 1.6 mm. Material, layer settings, shrink compensation and thread method remain to be qualified; these files do not prescribe an untested heat-resistant or child-ready assembly.

Before final print release, measure: finished pack and wire bends; USB plug reach and strain; real switch/keycap travel; mounting and click-load deflection; LCD glass/lead/support fit; all screw clearances/engagement; and retention after handling/drop tests. Keep the existing battery, charger, thermal, protection, programming and display electrical release gates. No purchasing or electronics manufacturing release follows from these CAD outputs.

## Rebuild and provenance

Run from the repository with a Python environment containing CadQuery 2.8.0, NumPy and Pillow. Pass the installed KiCad Python interpreter explicitly:

```sh
python scripts/build_q2_enclosure.py --kicad-python /path/to/KiCad/Python.framework/Versions/3.9/bin/python3
```

The local build used the temporary `/private/tmp/count-fidget-cadquery` environment and the mounted KiCad 10.0.6 runtime. No global Python environment, Rev0 file or electronics source is modified. Input changes during generation cause failure; rebuild after the final native board/model are stable. The manifest identifies geometry inputs and outputs; STEP headers may contain export timestamps, so byte-identical STEP reproduction is not claimed across runs or runtime versions.
