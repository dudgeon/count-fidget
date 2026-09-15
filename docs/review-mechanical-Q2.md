# Enclosure audit against the submitted Q1 board

**The existing STEP/STLs are an obsolete Rev0 fit study, not final Q1 print files.** This review reads the CAD source, saved geometry report, embedded native PCB footprints and RFQ. It does not rebuild CAD, measure a sample, simulate assembled solids or establish physical fit. No mechanical, electrical or manufacturing artifact was changed.

The comparison uses the existing CAD's centered coordinates: `CAD x = PCB x −21`, `CAD y = PCB y −20`. Q1 PCB coordinates are top view, top-left origin, Y down. This mapping reproduces the matching board outline and both key centers. Dimensions below are nominal millimetres.

## Verified geometry comparison

| Feature | Existing `mechanical/enclosure.py` | Actual Q1 evidence | Consequence |
|---|---|---|---|
| Board envelope | 42 ×40 ×1, corner radius 2; bottom Z=9.5 (lines 13,46) | Native PCB outline and thickness agree; generator lines 13,57–60 | This envelope is correct. Nominal straight-wall clearance is 0.8 per side inside the 43.6 ×41.6 cavity. This does not establish print/component clearance. |
| Board mounts | Four centers at CAD (±19,±18.5), with matching posts/lid holes (lines 15,30–32,41–47) | Only two 2.2-diameter Q1 holes: H1 (2.5,37.5), H2 (39.5,37.5), or CAD (±18.5,17.5) | Old rear centers map to PCB (2,38.5)/(40,38.5), displaced 0.5 horizontally and 1 vertically (1.118 radial). Old front centers map to (2,1.5)/(40,1.5), where Q1 has no mounting holes. Existing screw/post design cannot be assumed usable. |
| LCD position/pocket | Glass and pocket centered at CAD (0,−12.5); pocket 35.5 ×13.6 (lines 38–40,54) | DS1 is PCB (21,8.75), hence CAD (0,−11.25), glass 34.9 ×13 | Q1 glass is 1.25 toward the keys from the old pocket. With the board centered as modeled, its rear edge is −4.75 while the pocket ends at −5.7: **0.95 nominal overlap with the uncut pocket edge** in the source model. Recenter pocket/support/viewing aperture; verify with real glass. |
| LCD height | Glass rear Z=14.5, board top Z=10.5 (lines 13,54) | RFQ line 41 calls for 4.0 board-top-to-rear-glass standoff | This nominal standoff agrees. Leads, lead tails, compliant support and solder are absent; it is not a clearance result. Q1's separate LCD row-spacing defect remains in `review-lcd-firmware-Q2.md`. |
| USB access | Right-wall cut centered CAD y=−4.6, width along Y=10; generic connector center (19.5,−4.6), height 3.2 (lines 34,55) | J1 native footprint origin (38.9,13.3), rotation 90°, hence CAD centerline y=−6.7 | Opening is displaced **2.1** along Y. Native F.Fab body width along Y is 8.94; its projected interval is −11.17 to −2.23 versus opening −9.6 to +0.4. The opening does not cover that nominal projection. Exact mouth position, shell/board-edge recess, vertical cut and cable overmold require the approved GCT drawing/sample; the generic envelope does not establish access. |
| Key centers | CAD (−9.525,8)/(9.525,8), spacing 19.05 (line 16) | Native central 4 mm post holes at PCB (11.475,28)/(30.525,28) | Centers match. Footprint placement origins are contact pin 1, not stem centers. Actual clips, housing, travel, 14.2-square plate cutouts, plate height and load transfer still require qualified geometry/sample fit. |
| Battery tray | Internal diameter 20.9; bare-cell envelope 20 ×3.4 (lines 27,53) | RFQ lines 49–60 allow finished insulated body diameter up to 21.0, plus tab/wire exit and up to 0.8 added face thickness | Largest permitted body exceeds the tray bore by 0.1 before print tolerance. Model the approved finished pack and give deliberate clearance/retention. Bare-cell fit does not prove pack fit. |
| MCU and other parts | Generic 12 ×12 ×1.4 MCU below PCB, at CAD (0,−12.5), Z=8.1 (line 56) | U1 is top-side TSSOP-48 at PCB (21,8.75), rotated 90°; J2 is top-side at (5,16.8); many other Q1 parts are bottom-side | Old MCU is on the wrong side and has the wrong envelope/position. No accurate Q1 top/bottom component assembly is represented. Under-glass and below-board clearance remain unverified. |

The LCD overlap above is a coordinate calculation using the nominal source-model cut and the RFQ glass envelope at the matching Z height. It is not a new CAD intersection test or a measurement of printed parts. Likewise the USB projection establishes a location mismatch, not a measured connector/cable insertion result.

## What the saved geometry report establishes

`mechanical/geometry-check.json` records one solid per shell part, zero base/lid intersection, nominal body 46 ×44 ×18 and keycap envelope height 28.8. It reports solid-PLA shell masses 7.221 +2.680 =9.901 g. Those are historical model results, not new checks, printed mass or assembly validation.

Its 4.6 mm battery-to-PCB gap is simply `9.5 −(1.5 +3.4)`: bare cell top to bare board bottom. Applying the allowed 0.8 face addition alone reduces that to 3.8, before seating materials, bottom components, solder tails, wiring and tolerances. Neither number establishes usable free space. The source/report explicitly omit LCD leads, battery leads, thermistor, solder fillets, passives, screws and cable overmold.

## Required work before final print files

1. Freeze the revised PCB and approved component/pack geometry, including the LCD row/capacitor corrections and any selected display change, before committing the enclosure to another obsolete board.
2. Align the two real mounting holes and design a reviewed screw/boss/support scheme. Provide switch load support and USB strain support without unintended PCB/glass bending; check the printed material, thread engagement and assembly sequence.
3. Correct LCD pocket/window/support and USB access using actual drawings. Model lead rows, clips, solder/stake tails, component courtyards/heights and cable plug/overmold envelopes on the correct board sides.
4. Model the approved insulated cell/NTC/tab/plug assembly, 40 ±5 mm leads, bends and strain relief. Check insertion/removal, separation from conductors, screw-retained battery access and retention under handling/drop loads.
5. Run reviewed component-to-shell and component-to-component clearance checks with explicit tolerances, then print a fit prototype and measure actual switch travel/clip engagement, LCD support, connector access, screw retention and pack clearance. Only then issue final STEP/STLs and print orientation/settings. Electrical first-article and purchase approvals remain separate.

## Read-only artifact identity

These files were read and preserved; their hashes identify the audited historical artifacts without claiming they were regenerated from the current source:

| File | SHA-256 |
|---|---|
| `mechanical/enclosure.py` | `29b81bf46bdb849dc6e22e12ed8315b5811353168755f823c2d5e738e2b62821` |
| `mechanical/geometry-check.json` | `4d58ae20726feea0dca6c7771ebffdd177677fe44cef917de34709745d449d9d` |
| `mechanical/fit-study.step` | `754fab2f0405745701952a5c7d7c29df752684952b4f93f49db4194fe5386472` |
| `mechanical/base-fit-study.stl` | `435aa1403ad855f890878a9b7f8814c79354f54b68b30b002997193326dd3879` |
| `mechanical/lid-fit-study.stl` | `a38c0b664dfdef61bc2db845b2af4f44e9f9953c7ca6adf63543e5c7d907a14a` |
