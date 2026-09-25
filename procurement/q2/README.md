# Q2 quotation package

This directory is a separate **engineering quotation candidate**. Existing website submissions contain Q1. Q2 has not been uploaded, accepted, purchased or released for manufacture.

## Vendor inputs

- Gerber-only field: `click-counter-Q2-Gerbers.zip`.
- Controlling PCB BOM / PCBWay: `BOM-PCBA-Q2.csv`.
- JLCPCB exact-MPN import adapter: `BOM-JLCPCB-Q2.csv` plus `CPL-JLCPCB-Q2.csv`.
- Generic placement: `placements-KiCad-Q2.csv`; native KiCad rotations, X right/Y up. Bottom views are mirrored for direct underside viewing. Vendor must review pad1 and machine rotations.
- Full technical/commercial supplement: `../../dist/q2/click-counter-Q2-RFQ.zip`, including `RFQ-Q2.md`/HTML and native schematic/PCB/reports.
- All50 fitted PCB refs must be retained. Offboard BAT1 and K1/K2 have no placement coordinates and are separately specified in `OFFBOARD-items-Q2.csv`; include their complete preparation/supply cost.

Catalog codes preserve verified exact identities where available. They do not establish live stock, allocation or electrical qualification. U5 TLV7032DGKR is not a drop-in match to the previous open-drain part; its two outputs must remain separate.

The native Gerber job now records ENIG, 1.0 mm board thickness and 0.0175 mm inner copper. Copper/dielectric allocation totals 1.0 mm; KiCad also records provisional 0.01 mm mask per side. This requested stackup is a proposed quote baseline, not an approved fabrication construction. Confirm actual material, copper, finished thickness and tolerances. The outline centerline is42×40mm; stroke bounds may read42.05×40.05mm. U5 mask bridge acceptance and the remaining engineering gates are explicit in the RFQ.

## Evidence and reproduction

`export-manifest-Q2.json` binds the source board/model/validation and exact CLI export commands to all fabrication, placement and assembly exports. The full RFQ manifest binds every packaged file. Packaging refuses stale native or mechanical evidence. These checks do not prove measured electronics, physical fit or vendor acceptance.

The RFQ archive is a vendor review bundle. It includes current source/provenance and comparison inputs, but is **not a standalone build environment**. Full regeneration requires the Git revision containing this manifest in [dudgeon/count-fidget](https://github.com/dudgeon/count-fidget/pull/1), its preserved Q1 baseline PCB/archive/compiler-comparison files, and the documented KiCad10.0.6, Freerouting2.4.1, TI compiler/support and CadQuery tooling. Never execute the Q1 builders over frozen outputs. No toolchain or credentials are shipped in the RFQ.

Use the existing vendor cases to arrange coordinated replacement of the Q1 files. Do not approve DNP, chargeable sourcing or a manufacturing order merely to obtain a quote.
