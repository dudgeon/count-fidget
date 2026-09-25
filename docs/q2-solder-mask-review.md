# PCBWay solder-mask question: Q1 evidence and Q2 correction

Reviewed **2026-09-15**. PCBWay's incoming DFM question reports that green solder mask requires **at least 0.19 mm IC-pad spacing** to retain a mask bridge; its stated threshold for black/white, including matte variants, is **0.22 mm**. It asks whether the bridges can be omitted with a combined opening, or the spacing increased. **No permission, modified drawing acceptance or manufacturing release was sent during this review.**

The attached PNG was read through the authenticated email's raw MIME content, without browser access. It highlights the two middle pads on U5's right-hand row; its ruler reports **DX=0, DY=0.15, D=0.15 mm**. Component position and pad geometry identify these as bottom-side **U5 pins 6 (TEMP_HOT) and 7 (TEMP_OK)**. The image is one measured example; neither the image nor prose enumerates all affected components or bounds a proposed combined opening. It does not establish that PCBWay has already changed the files.

## Submitted Q1 geometry

In `electronics/click-counter-Q1.kicad_pcb`, U5 is the VSSOP-8 at **(17,7)**. Its pad row centers are **±2.1125 mm**, with **1.625 ×0.500 mm** lands at **0.650 mm pitch**. Pads 6 and 7 centers are respectively **(19.1125,6.675)** and **(19.1125,7.325)**. The nominal copper-edge gap is therefore **0.150 mm**, agreeing with the vendor image. Other adjacent lands in the same U5 row have the same gap.

The emitted `electronics/gerbers/click-counter-Q1-B_Mask.gbs` defines aperture **D20** at line 42, then uses it for U5 at lines 143–151. Its rounded-rectangle corner Y values ±0.125 and radius 0.125 produce a **0.500 mm** aperture height. At 0.650 mm pitch, the actual exported mask also retains **0.150 mm nominal webs**, using eight separate openings. Thus the vendor's proposal would change retained mask features, not merely acknowledge an existing combined opening. Actual fabricated registration/tolerances are not established by this nominal calculation.

## Manufacturer-supported Q2 option

The [TI TLV7032/42 RevJ datasheet](https://www.ti.com/lit/ds/symlink/tlv7032.pdf), **PDF page 63**, DGK0008A drawing **4214862/A (04/2023)**, gives an example of **eight 1.4 ×0.45 mm lands**, **0.65 mm pitch**, **4.4 mm row-center span** and **R0.05** corners. That yields **0.20 mm copper spacing**, above PCBWay's stated green-mask threshold. The matching stencil example is on PDF page 64. TI's preferred non-solder-mask-defined detail calls for **0.05 mm minimum mask clearance around a land** and notes that mask tolerances vary with fabrication site.

A Q2 footprint following that complete TI example would be better grounded than an arbitrary pad shrink. A width-only change to 0.45 mm would improve the nominal gap but retain Q1's different land length/row positions. **0.40 mm width is not the cited TI example.** Review routing, fillets, courtyard, mask and paste after any footprint change.

With 0.45 mm lands and 0.05 mm opening clearance on each side, nominal mask web is **0.10 mm**, not 0.20 mm. Obtain PCBWay's acceptance of the precise copper/mask/stencil geometry and its fabrication tolerance. If it instead proposes combined openings, require their exact scope and assembly review. This report does not approve blanket removal of IC mask bridges.

Q1 Gerbers and board remain unchanged and on engineering hold. The same DGK geometry review applies if the Q2 thermal circuit changes from TLV7042DGKR to TLV7032DGKR. All other electrical, thermal, cell, fit and first-article release gates remain open.
