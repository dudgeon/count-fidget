# Rev0 fit study — not final Q1 print files

**These STEP/STLs do not match Q1.** Preserve them as editable CAD and form-factor work, not a finished electronics assembly. Purchased parts in renders are simplified envelopes; pins/wiring/small parts are missing.

`enclosure.py` generates the STEP, base/lid STLs, CAD renders and geometry report using CadQuery. Recorded checks show one solid per shell part, zero base/lid intersection and solid-PLA masses 7.221 g + 2.680 g. They do not establish component clearance.

## Q1 revision requirements

- Use actual 42 × 40 × 1.0 mm board with 2 mm outline corner radii. Two rear M2 holes are **(2.5, 37.5), (39.5, 37.5) mm**; old model assumes four corner holes/supports.
- J1 opens right at **y=13.3 mm**. Use exact GCT drawing, stakes and real USB cable clearance.
- Switch stem centers: **(11.475, 28.000), (30.525, 28.000) mm**. Footprint placement origin is contact pin 1, not stem. Check clips, travel, plate height and click-load support.
- LCD center: **(21, 8.75) mm**; glass rear 4 mm above PCB top. Model actual glass/pins/standoff, compliant support, MCU/connectors beneath and viewing angle.
- Include bottom components, solder, ≤1 mm LCD lead tails, battery tab/NTC exit, 40 ±5 mm flexible leads, pack diameter ≤21 mm excluding lead exit and ≤0.8 mm added face thickness.
- Keep cell behind screws with strain relief and clearance from conductors. Final screws/retention/drop behavior need validation.

All quoted coordinates are board top view, top-left origin, Y down. Use Q1 files for truth. Render final visuals from corrected CAD after reviewing geometry.

Old body: 46 × 44 mm, 1.2 mm wall/floor, 18 mm with bezel, 28.8 mm keycap height. Old base prints flat; lid puts bezel on bed and needs support under surrounding face. Notes considered two 0.6 mm extrusion lines and transparent PETG, subject to slicer/fit/thermal checks.

CAD dependencies: CadQuery, NumPy, Pillow. Historical renderer uses Linux DejaVu font paths; select available local fonts on macOS. Run changes in a branch; all geometry is mm. Final print files remain owed.
