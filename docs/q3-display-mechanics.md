# Q3 X087 display footprint and mechanical proposal

15 September 2026. Engineering candidate only. This file and the new Q3 footprint do not modify Q1/Q2 or establish vendor process acceptance, a complete quote, physical qualification, or manufacturing release.

## Decision and evidence

Use a nominal **unfolded, viewing-face-up** arrangement of exact **Wisevision X087-2832TSWIG02-H14**, with the glass to the left and the 14-contact FPC tail to the right. The proposed footprint is `electronics/q3/CountFidgetQ3.pretty/X087-2832TSWIG02-H14.kicad_mod`. Its origin is the nominal glass center; this is not the solder-row center or full-module center. Rotation zero uses KiCad +X right, +Y down when viewed from the PCB front.

Controlling dimensional evidence is the [Wisevision preliminary specification, revision A](https://atta.szlcsc.com/upload/public/pdf/source/20231103/222F0746A2795BBD5263EDDBD3E1B824.pdf), PDF pages 4–6, especially the dimensioned drawing on page 5, dated 2022-09-13. The locally inspected PDF SHA-256 is `bf88a9e033ddb6656bc9ddc5f20d3de9188983bb2cdd4278199555ee6e7989ce`. Page 10 supplies the application circuit, not a PCB land pattern or solder profile. Pages 22–24 warn against pressure on the glass/driver, excessive flex bending, and ESD. The manufacturer drawing is preliminary and needs confirmation against the supplied lot.

The [manufacturer product page](https://www.jx-wisevision.com/0-87-micro-128x32-dots-oled-display-module-screen-product/) contains conflicting outline and unrelated table entries. Its 28.54 × 8.58 mm outline must not silently replace the PDF's 29 × 8.8 mm drawing. The [JLCPCB exact-part catalog](https://jlcpcb.com/partdetail/Newvisio-OEL/C18723015) labels this part Wave Soldering / High assembly difficulty. That catalog label does **not** approve exposing this glass to a wave or reflow, our land geometry, its final height, or an assembly fixture. Root is obtaining exact process confirmation from both vendors.

## Dimensions and coordinate convention

Dimensions below are millimeters. Rectangles are nominal projected envelopes, not exact purchased-part 3D models. General drawing tolerance is ±0.30 where no other tolerance is shown. Parenthesized offsets are drawing reference dimensions, not independently guaranteed positioning tolerances.

| Feature | Drawing evidence | Coordinates relative to nominal glass center |
|---|---|---|
| Glass panel | 29 ±0.15 × 8.8 ±0.15, total thickness 1.22 ±0.05 | X −14.5…14.5; Y −4.4…4.4 |
| Active area (AA) | 22.38 × 5.58; reference offset 1.44 from left glass edge and 1.61 from top | X −13.06…9.32; Y −2.79…2.79; center (−1.87, 0) |
| Viewing area (VA) | 23.38 × 6.58, 0.5 wider on each AA edge | X −13.56…9.82; Y −3.29…3.29 |
| Cap/backing length | 25.6 from glass left datum | X −14.5…11.1; its rectangle in Cmts.User is an envelope, not a support approval |
| Polarizer | 25.1 ±0.2 × 7.7 ±0.2; vertical offset 0.5 ±0.3 | Keep the whole front glass face free from contact/preload; do not treat the polarizer as a structural bearing surface |
| FPC tip | 10.5 ±0.2 beyond right glass edge | Tip X =25.0; unfolded glass-plus-tail length 39.5 nominal |
| FPC terminal-end width | 9.0 ±0.2 | Conservative tail envelope X14.5…25, Y−4.5…4.5; actual neck is narrower and the protective/bond region is nonrectangular |
| FPC contacts | 14, pitch 0.62; total center span 8.06 ±0.05; width 0.32 ±0.03; exposed length 2.0 ±0.2 | Nominal exposed metal X23…25; contact n center (24, 4.03−0.62(n−1)) |
| FPC alignment holes | Two Ø0.8 ±0.05, 6.2 ±0.1 center spacing, 6.1 ±0.2 back from tip | Nominal (18.9, ±3.1); drawing-only circles, **not PCB drills**, not fitted parts |
| FPC thickness | 0.10 ±0.03 | Exact assembled solder-face Z needs confirmation, as explained below |
| Protective materials | 7.5 × 7(4) ×0.05 protective tape; removable tape ≤0.15 | Shape/contact zone is not fully defined by a simple rectangular callout; do not clamp the bond/driver region or count removable film as final height |

### Pin orientation

With the page-5 drawing upright, glass on the left, FPC on the right and display face visible, **pin 14 is the top contact and pin 1 is the bottom contact**. Page 5 explicitly labels both FPC contact faces. Contacting its underside does not reverse the front-view pin numbering. Looking from the PCB rear does mirror the appearance; do not reverse the electrical assignment to compensate for that view. A received-part visual/continuity check is still required.

| Pad | Signal | Local Y | Pad | Signal | Local Y |
|---:|---|---:|---:|---|---:|
| 1 | C2P | 4.03 | 8 | VDD | −0.31 |
| 2 | C2N | 3.41 | 9 | RES# | −0.93 |
| 3 | C1P | 2.79 | 10 | SCL | −1.55 |
| 4 | C1N | 2.17 | 11 | SDA | −2.17 |
| 5 | VBAT | 1.55 | 12 | IREF | −2.79 |
| 6 | NC | 0.93 | 13 | VCOMH | −3.41 |
| 7 | VSS | 0.31 | 14 | VCC | −4.03 |

Pad 6 remains a real physical contact/land but electrically NC. Page 6 also uses the name VBREF for that reserved pin; pages 5 and 10 specify no connection. Do not ground it or omit its physical location.

## Proposed PCB lands, routing and assembly

**These are proposed PCB lands derived from the FPC drawing, not a manufacturer-recommended or vendor-approved PCB land pattern.**

- Fourteen rectangular top copper lands, **2.80 long in X ×0.40 wide in Y**, centered at X24 and the Y coordinates above. At nominal contact geometry each extends 0.40 past each end of the 2 mm exposed finger. Nominal side allowance is 0.04 per edge; with the maximum 0.35 mm finger width it is only 0.025 per edge. FPC pitch, placement, pad registration and thermal expansion need real alignment/process evaluation; these allowances do not prove full-tolerance solder overlap.
- Copper gap is **0.22** at 0.62 pitch. Local solder-mask expansion **0.05** gives 0.50-wide openings and **0.12 nominal mask web**. Fabrication registration and the vendor's actual copper/mask capabilities still govern. No whole-row mask opening is implicitly approved.
- Lands have **F.Cu and F.Mask only; no F.Paste**. This intentionally prevents the display lands entering the main SMT stencil. A localized FPC solder process after all oven/wave work is the proposal. Flux/solder volume, tip or thermode, temperature, dwell, pressure, cleaning, inspection and strain relief require supplier approval. No temperature limit from DE188 applies to this OLED.
- F.Fab contains the glass and readable pin labels; Dwgs.User contains AA/VA, the conservative FPC envelope and its alignment holes. Cmts.User contains a rear-cap envelope. F.CrtYd is X−14.95…25.75, Y−4.85…4.85. These graphics are not an automatically enforced 3D keepout or an approved adhesive drawing.
- Route away from the lands toward **−X**, since the distal end is near the PCB's right edge. The final two-layer board uses locked, compact escapes reviewed against actual capacitor positions. The earlier routing study considered staggering tented vias at local X20.2/21.0 on alternating Y positions. With Ø0.60 lands, alternate-column nearest-center spacing is sqrt(0.80²+0.62²)=1.012, giving 0.412 nominal copper gap; same-column spacing is1.24. Those example coordinates are historical calculations; use the final native board and layout review for actual routes. Avoid exposed via copper, solder bumps and components beneath the FPC; do not place a via or other obstruction under either alignment-hole/fixture contact location.
- Put the charge-pump/decoupling parts close to the corresponding contacts on the bottom side. Their actual routes, return loops, clearances, solder-side accessibility and new underside component/pack collisions must be checked after native layout.

## Final routed placement and optical window

The Q3 native board places **DS1=(15.75,5.50), rotation0°, top-side contact lands**. Coordinates below supersede the earlier Y4.90 proposal.

| Feature | Nominal absolute board coordinates, mm |
|---|---|
| Glass | X1.25…30.25; Y1.10…9.90 |
| FPC tip / contact row | X40.75 / X39.75 |
| FPC envelope | X30.25…40.75; Y1.00…10.00 |
| Pad1 / pad14 centers | (39.75,9.53) / (39.75,1.47) |
| AA center and bounds | Center(13.88,5.50); X2.69…25.07, Y2.71…8.29 |
| VA bounds | X2.19…25.57; Y2.21…8.79 |
| Courtyard | X0.80…41.50; Y0.65…10.35 |

The enclosure opening is **24.2×7.4 centered at(13.88,5.50)**, nominal X1.78…25.98/Y1.80…9.20. This gives0.41 per side beyond nominal VA. It is a modeled allowance, not a guarantee against print, glass seating, viewing-angle or part-registration errors. The cover shields the bond region without contact on the glass/polarizer. The final native board and hash-bound mechanical outputs control placement.

## Z seating: a necessary unresolved process detail

**An unfolded XY drawing is not proof that the glass rear and FPC solder faces can both sit flush on an intact PCB.** The page-5 side view shows a **0.5 mm interior glass/tail datum**, the full1.22±0.05 glass thickness, and the0.10±0.03 FPC. The exact 0.5 datum-to-final-contact-face relationship is not sufficiently clear to claim a precise solder-face Z. Independent drawing review confirmed this ambiguity. There is no bend-radius specification, formed-tail endpoint drawing or approved PCB support section.

Proposed low-profile assembly: move U1 and other obstructing SMT parts to the PCB bottom; reserve the whole glass rear area on the top side. Use compliant, electrically insulating rear support. Current CAD proposes two **0.20mm nominal,2×6mm** pads centered at localX−12.5 and+8, Y0, stopping before the bond-side end. This is an assembly proposal requiring supplier confirmation, not an approved glass support specification. Its material, adhesive compatibility, thickness tolerance, compression and exact safe contact region remain to be approved with the display supplier. Keep PCB solder bumps and uninsulated conductors out of the support area.

The nominal rear-glass Z would then be PCB-top+0.20 and nominal glass-front Z PCB-top+1.42 (up to1.47 before support variation). A provisional **approximately0.7 mm gentle downward tail transition**, rather than a180° fold, would bring the contacts to the top lands if the0.5 datum represents the relevant offset. The full pre-contact length is8.5 mm nominal; a straight0.7 mm drop over that length would reduce projected reach by about0.029 mm. This calculation only illustrates scale: protective/bond exclusion lengths reduce the usable bending span, real curvature consumes length, the exact solder face is ambiguous, and **no bend or reach is qualified**. Do not bend at the glass bond, driver or protected region. The vendor must return an approved section/fixture drawing before release.

If the supplier requires an entirely unbent FPC, provide a recessed glass seat or a correctly raised terminal carrier with approved dimensions instead. A board cutout/recess must be explicitly designed and checked; it is not present in this footprint and would prohibit mounting U1 immediately under the removed board area. Do not silently restore the old4 mm LCD standoff: that would require a much larger, unqualified tail form and different pad positions.

## Implemented assembly and enclosure geometry

All SMT is now on the PCB bottom, including U1 and the connectors. The vendor separately solders the top OLED FPC, switches and hybrid USB shell. One SMT side is not one total assembly operation; obtain actual process pricing.

J1 is at(38.9,15.3), facing right; J2 is at(5,16.8), facing left. Native flipped pad coordinates and CAD body envelopes were checked. PCB bottom is11.1mm above the base floor, with1mm board thickness. The height was raised0.6mm after independent review found only0.1mm beneath the keeper screw heads; the reviewed model now gives0.7mm. This remains a simplified envelope check.

The50×45mm body has a stepped front OLED roof at15.6mm and a switch plate top at17.1mm. The OLED has0.2mm proposed support, with0.53mm modeled space above its maximum glass height before support/print tolerances. The USB opening is13.2×4.8mm at nativeY15.3, fromZ7.0 to11.8. A cable overmold remains an unqualified reservation.

The cover is split at the switch center line into front/rear parts with a0.12mm joint and three lapped locating tongues. Each half slides around the already-soldered lower switch housings before the base is fitted. This resolves the one-piece cover assembly trap: a14.05mm hole cannot pass over the larger upper switch housing. Four printable parts are provided: base, front cover, rear cover and battery keeper. See the independent mechanical review and the assembly instructions in mechanical/q3/README.md. Sampled collision checks do not establish printed clip/lap strength or physical fit.

One native courtyard projection exception concerns the J1 rear shell pad and SW2 raised flange. Applying the actual pad rotation gives worldY20.12 at the joint edge versusY21.025 at the switch lower body:0.905mm nominal separation. The flange underside is5mm above the PCB; the checked joint fillet is≤0.5mm. The exact object pair is recorded in the native verifier and layout review. Vendor confirmation of solder height and real tolerances remains required; no copper or short exception is permitted.

CAD export coordinates are right-handed: X=PCB_X−21, Y=20−PCB_Y, Z above the base floor. Internal fit calculations use reflected Y; the global reflection preserves all measured distances/intersections. STL print orientations are separate from assembly placement.

## Checks and remaining gates

- Native KiCad10 loaded the new footprint, recovered all14 unique numbered pads with the expected centers/sizes and no F.Paste, and saved a separate temporary test board. The FPC alignment circles do not create drilled PCB holes. Adjacent nominal pitch/copper/mask-gap calculations are recorded above.
- A second agent independently confirmed the p5 pin direction, glass/tail/contact dimensions and ambiguous Z datum. Page10 pin names agree; pad6 stays NC.
- Q2 remains unchanged: model SHA-256 `3aae3dafcf2b6b5d1c1cac8932200bd2ba3e52ed39507f2c22e9a41b771bb065`; PCB `c80cf17a1d36d74e4c7c8f7cc4e14f5f42169fe0c3224811856b8bff0e5d0867` at this review. No Q2 Gerber, RFQ, firmware or mechanical artifact was regenerated.
- Before manufacture: exact-lot drawing and pin orientation; approved FPC land/mask/solder/cleaning/fixture process; approved Z seating/support/strain relief; new native PCB routing, ERC/DRC and flip/placement checks; the checked two-layer routing evidence; complete Q3 enclosure/pack/connector/screw/keycap fit; first-article OLED operation/current/thermal/lifetime and all retained charger/protection/FRAM gates. A catalog stock or assembly label does not close these checks.

## Associated custom power footprints

The same bounded Q3 library work also created these two exact-package footprints. Their nominal land patterns come from primary sources; mask expansion, courtyard margins, routing and production acceptance are separate engineering choices.

| Library file | Primary source and implemented geometry |
|---|---|
| `TPS63900_DSK0010A_TI.kicad_mod` | [TI TPS63900 revision D](https://www.ti.com/lit/ds/symlink/tps63900.pdf), PDF pp37–39, DSK0010A drawing4218903/C09/2025: ten0.60×0.25 lands,0.50 pitch, row centers2.30; exposed pad11=1.20×2.00. Pad1 top left,5 bottom left,6 bottom right,10 top right. EP11 must be GND and soldered. Two1.13×0.89 paste apertures centered Y±0.555 approximate TI's84% coverage example for a0.125 stencil; corner radius0.05. Mask expansion0.05 is within TI's0.07 maximum NSMD clearance. Optional thermal vias are not inserted automatically. |
| `Inductor_SMD_L_Murata_DFE201612E_2.0x1.6mm.kicad_mod` | [Murata reference specification J(E)TE243A-0006D-01](https://pim.murata.com/asset/pim4/inductor/J%28E%29TE243A-0006_PDF_INDUCTOR), p5: two0.80×1.80 lands at X±0.80,0.80 inside gap,2.40 overall. Page1 body2.0±0.2×1.6±0.2, height1.2 maximum. Page7 prohibits copper beneath the low-insulation core except electrode copper, and through holes beneath the coil. The footprint embeds a central mounting-side copper keepout X±0.40/Y±0.90 and a full maximum-body via keepout X±1.10/Y±0.90. These do not automatically prohibit every possible NPTH or opposite-layer feature: verify all drilled holes and adjacent features in the actual board; obtain clarification before introducing other copper beneath the body. |

Murata's current official selection guide links that exact series specification, which includes `DFE201612E-2R2M=P2`. No nearby DSK/DSQ/DLH package or differently shaped2016 inductor was substituted. No footprints were copied from unverified community library entries.

Native KiCad10 loaded and saved both footprints. TPS63900 has11 numbered copper pads plus2 unnumbered paste-only apertures; Murata has2 numbered copper pads and2 rule areas. A temporary2-layer board confirmed both Murata rule areas change to B.Cu, preserve their track/pad/via restrictions, and save successfully when the footprint flips to the bottom. Native SVG previews were visually inspected. These checks validate the library representation, not a completed Q3 board or solder process.

Source hashes: TPS63900 PDF `06ee84ef9067de0feb67614d3f9c29ab21878b1cac84c0c229fcaf36ebc79b0b`; Murata PDF `6fbbdccedc9f58904a3e60d7e9c0e33917a03b7dd0d96716821988e89e4fb8ad`.
