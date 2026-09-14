# Q1 website import notes — 14 September 2026

No circuit, placement, Gerber or firmware change is made by this clarification.

Use **BOM-PCBA-Q1.csv** for the automated PCB-assembly BOM importer. It contains exactly the 46 fitted PCB designators in CPL-JLCPCB-Q1.csv. Use CPL-JLCPCB-Q1.csv for JLCPCB, or placements-KiCad-Q1.csv for a generic pick-and-place import. BOM-Q1.csv remains the complete commercial BOM.

**OFFBOARD-items-Q1.csv** lists BAT1 (the specified factory-prepared cell/NTC/JST harness) and K1/K2 (two loose keycaps). These are supplied items with no PCB mounting coordinates. Do not invent placement coordinates or treat their absence from the CPL as missing PCB component positions.

PCBWay: please include the off-board items and all programming/fixture/testing/freight work in the quotation. The website form offers 1 oz inner copper as its minimum; please quote that standard stack and identify whether the preferred 0.5 oz inner copper option is available. The board is 42 x 40 x 1.0 mm, four layers, ENIG 1 microinch, green/white, Tg150+, 5/5 mil, minimum plated drill 0.3 mm. Outer copper is 1 oz. Identify stackup and tooling cost explicitly. Please quote quantities 5 and 10 separately.

JLCPCB: battery assembly is excluded by your stated capability. The keycaps are loose supplied items; please identify whether they can be supplied separately. Include every excluded or pending amount explicitly. Manual component matching and inventory shortages still require resolution. No components or alternates have been approved simply by separating this BOM.

RFQ-Q1.md/HTML remains the controlling technical, commercial, programming and test scope. This is a prototype quotation package; no charge, paid procurement, manufacturing or production release is authorized.
