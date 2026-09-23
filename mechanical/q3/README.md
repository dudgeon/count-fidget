# Q3 enclosure engineering candidate

Four print parts: base-Q3.stl, lid-front-Q3.stl, lid-rear-Q3.stl and battery-keeper-Q3.stl. The STEP assembly and renderings are assembled views; the STLs use proposed print orientations. No enclosure has been printed or physically qualified.

## Customer assembly sequence

1. Inspect the completed vendor PCBA, with OLED and both switches already soldered. Leave the battery disconnected and the keycaps off.
2. Slide the front cover toward the lower switch bodies from the display end, then slide the rear cover from the opposite end. Engage the three cover-joint tongues; do not push a cover over the upper switch housings. Printed tolerances and clip engagement need a sample check.
3. Install the insulated, finished battery pack in the base and fit its keeper with two proposed M2×5 screws. Do not trap or puncture the pack or leads. The harness path and actual screw heads require a fit check.
4. Mate the keyed battery connector and lower the PCBA/cover assembly onto the base supports. Engage the front retention features, route the harness in its reserved corridor and fit the two proposed M2×12 rear screws. Do not tighten against the OLED glass or crush the board/pack.
5. Install the loose keycaps. Verify both keys return freely through full travel and the USB cable fits without loading the display or switches.

## Dimensions and evidence

Body50×45mm; switch plate top17.1mm; provisional keycap envelope30.4mm. PCB42×40×1mm, bottomZ11.1mm. Plate1.5mm thick with14.05mm openings and top5mm above the PCB. OLED roof15.6mm and proposed support0.2mm.

The build manifest binds the native board/model, generator and exact current STEP/STL/render outputs. The fit report requires four valid single solids, manifold STLs and zero reported modeled intersections. Independent review found and corrected initial shell collisions, the one-piece cover assembly trap and inadequate battery-keeper screw clearance. The reviewed split-cover approach was sampled at0.25mm increments without collisions; this is not a real assembly or tolerance test.

Simplified body/screw/keycap envelopes are not vendor 3D models. OLED FPC solder-face height/bend/support, clip/lap strength, print tolerances, actual keycaps, harness/JST insertion, fasteners, USB overmold/strain, battery retention, drop behavior and mass remain open. Preserve all engineering gates in the RFQ. Customer enclosure assembly requires no soldering.
