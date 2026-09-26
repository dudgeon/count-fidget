# Count Fidget Q5 — pin-assignment / footprint audit against manufacturer datasheets

Date: 2026-09-26. Read-only audit. No repo files were modified.

## Scope and method

- **Netlist:** `electronics/q5/netlist-Q5.json` (parts[].pins, symbol_pins). I also cross-checked the passive endpoints on every net that touches an IC pin.
- **Board:** I dumped absolute pad positions and nets from the routed board `electronics/q5/click-counter-Q5.kicad_pcb` with pcbnew 10.0.6, so bottom-side flips and rotations are included.
- **Footprints:** each `CountFidgetQ5.pretty` footprint was compared pad by pad (number, x, y) with the current official KiCad library copy (gitlab.com/kicad/libraries/kicad-footprints, master). All 10 standard-package footprints are identical in pad number and position to the KiCad originals: LQFP-48, SOIC-8, SOT-23/-6/-8, WSON-6 DRV, WSON-6 DSE, WSON-10 DLH, SOD-323 and USB4105.
- **Custom footprints** were checked against the vendor drawings: hot-swap socket, battery holder, OLED module, TS-1088 and the MX switch.
- **Datasheets:** fetched from ti.com (`/lit/ds/symlink/*.pdf`) and from the LCSC product pages. Where LCSC was delisted I used the JLCPCB part page. st.com refused the connection, so the STM32 datasheet (DS10689 Rev 5) came via LCSC.

## Result summary (ranked)

**No fatal pin-assignment error was found.** Every active or polarised part's pin-number-to-function mapping matches its manufacturer datasheet. Every standard footprint matches KiCad's library exactly. The custom footprints match the vendor drawings.

| Rank | Severity | Item | Finding |
|---|---|---|---|
| 1 | UNCERTAIN (process, not netlist) | All bottom-side polarised parts (every IC, D1–D4, Q1–Q5, BT1, SW1/2) | Pad numbering is correct in KiCad. **JLC bottom-side CPL rotation and mirroring was not audited.** This is the other classic first-spin fatal error. It is resolved by checking JLC's DFM/placement preview, pin-1/cathode/+ by pin-1/cathode/+, before approval. Most critical: U1, U2 (WSON-10), U4, U3, D4 and BT1. |
| 2 | LOW / UNCERTAIN | BT1 CR2032-BS-6-1 land size | Polarity is OK (pad1 = + matches the vendor "+" side). The lands differ from Q&J's recommended layout. Vendor: pad span 26.0–32.0 mm, 4.2 mm wide. Footprint: 24.58–32.98 mm long, 3.8 mm wide, against a 3.5 ±0.1 mm tab. The tab is still fully covered, so this is not a pinout error. Fillet/retention is already a physical gate. Also confirm in JLC's preview that the model's + tab lands on pad 1. |
| 3 | LOW | U2 BQ25185 STAT1/STAT2 pull-up | The datasheet asks for a 1–20 kΩ pull-up. The design uses the MCU internal pull-up (~40 kΩ typ.). Functionally fine for a static status read, but outside the datasheet's stated range. |
| 4 | INFO | U4 / Q1 / Q2 / R9 | The arrangement matches the TI typical application. R9 (3.3 Ω) sits in series between the CHG-FET source and PACK−. The V− sense therefore includes it, and the discharge over-current trip is only ~25–30 mA. This is intentional and documented in `docs/q5-power-design.md` §35. It is not a pinout error, but it is a hard load-current ceiling for the OLED plus MCU on battery. |
| 5 | INFO | SW1/SW2 hot-swap | Geometry matches the HanElectricity drawing and the MX pin pattern once flipped to the bottom. It accepts only 3-pin (plate-mount) switches. CPG151101D13 is 3-pin, so this is OK. |

## Per-part detail

### U1 STM32L072CBT6, LQFP48
- **Pinout:** DS10689 Rev 5, Fig. 8, p.41, via [LCSC C465977](https://www.lcsc.com/product-detail/C465977.html) → datasheet.lcsc.com/…/536ccbd6392d4702041e586324d918c6.pdf.

| Pin | Datasheet | Net | Result |
|---|---|---|---|
| 1 | VDD | VLOGIC | OK |
| 7 | NRST | NRST (10k up, 100n, SW3 to GND) | OK |
| 8 | VSSA | GND | OK |
| 9 | VDDA | VLOGIC | OK |
| 10 | PA0 | COUNT_N | OK (also WKUP1) |
| 11 | PA1 | BOOT_COUNT_RESET | OK |
| 14 | PA4 | VBAT_SENSE (ADC_IN4) | OK |
| 15 / 16 | PA5 / PA6 | CHG_STAT1 / CHG_STAT2 | OK |
| 18 / 19 | PB0 / PB1 | OLED_RESET_N / OLED_ENABLE | OK |
| 20 | PB2 | PWR_HOLD | OK (on L0, BOOT1 is the nBOOT1 option bit, not PB2) |
| 23 / 35 / 47 | VSS | GND | OK |
| 24 / 48 | VDD | VLOGIC | OK |
| 25 | PB12 | OLED_CS_N (GPIO) | OK |
| 26 | PB13 | OLED_SCK | OK: AF0 = SPI2_SCK (Table 18) |
| 27 | PB14 | OLED_DC (GPIO) | OK |
| 28 | PB15 | OLED_MOSI | OK: AF0 = SPI2_MOSI |
| 32 / 33 | PA11 / PA12 | USB_DM / USB_DP | OK |
| 34 / 37 | PA13 / PA14 | SWDIO / SWCLK | OK |
| 36 | VDD_USB | VLOGIC | OK |
| 39 / 40 / 41 | PB3 / PB4 / PB5 | FRAM_SCK / MISO / MOSI | OK: AF0 = SPI1_SCK / SPI1_MISO / SPI1_MOSI |
| 44 | BOOT0 | BOOT_COUNT_RESET (100k to GND, SW2 to VLOGIC) | OK |
| 45 | PB8 | FRAM_CS_N (GPIO open-drain, 100k to VFRAM) | OK |

- **Firmware agreement:** `firmware/q5-stm32/board.h` and `main_stm32.c` use `alternate(GPIOB,3/4/5,0)` for SPI1 and `alternate(GPIOB,13/15,0)` for SPI2 (TX-only, BIDIOE). This matches the AF table.
- **Footprint:** identical to the KiCad `LQFP-48_7x7mm_P0.5mm`.
- Unused pins, including the ROM USART pins PA2/3/9/10, are NC. That is acceptable electrically; firmware should set them to analog mode for current.

### U2 BQ25185DLHR, WSON-10 DLH
- **Pinout:** [ti.com bq25185.pdf](https://www.ti.com/lit/ds/symlink/bq25185.pdf), SLUSF65B, Table 4-1 p.4.

| Pin | Datasheet | Net | Result |
|---|---|---|---|
| 1 | SYS | SYS | OK |
| 2 | BAT | CELL_P | OK |
| 3 | STAT2 | CHG_STAT2 | OK |
| 4 | /CE | CE_N (100k to VBUS, pulled low by the Q3+Q4 series stack) | OK: high disables, low enables |
| 5 | GND | GND | OK |
| 6 | TS/MR | R5 10k to GND | OK: the datasheet says "if TS not required connect 10 kΩ to GND" (§6.3.9.1). 38 µA × 10k = 0.38 V, which is above the 90 mV MR-press threshold, so there is no false factory-mode entry. |
| 7 | ILIM/VSET | R3 24k to GND | OK: Table 6-1 gives 24k = ILIM100, 4.2 V |
| 8 | ISET | R4 16.5k to GND, plus R19 2k + C13 4.7n RC | OK: 300 AΩ / 16.5k = 18.2 mA; the RC is the recommended form for low current |
| 9 | STAT1 | CHG_STAT1 | OK (see pull-up note, rank 3) |
| 10 | IN | VBUS | OK |
| 11 (EP) | Thermal pad | GND | OK |

- **Footprint:** identical to the KiCad `Texas_DLH0010A…`.

### U3 TLV76701DRVR, WSON-6 DRV (adjustable)
- **Pinout:** [ti.com tlv767.pdf](https://www.ti.com/lit/ds/symlink/tlv767.pdf), Table 5-1 p.4.
- Pin 1 OUT = VLOGIC. OK.
- Pin 2 FB = VLOGIC_FB (150k / 49.9k). OK: VFB = 0.8 V gives 3.205 V.
- Pins 3 and 5 are both **GND** per the datasheet ("all ground pins must be grounded"). Pin 5 → GND. OK.
- Pin 4 EN = SYS_LOAD, tied to IN. OK (the datasheet allows EN tied to IN).
- Pin 6 IN = SYS_LOAD. OK.
- EP = GND. OK.
- **Footprint:** identical to the KiCad `WSON-6-1EP_2x2mm_P0.65mm`.

### U4 BQ29700DSER, WSON-6 DSE
- **Pinout:** [ti.com bq2970.pdf](https://www.ti.com/lit/ds/symlink/bq2970.pdf), Table 5-1 p.3.
- Pin 1 is NC and is left open. OK.
- Pin 2 COUT = Q2 gate. OK.
- Pin 3 DOUT = Q1 gate. OK.
- Pin 4 VSS = CELL_N_RAW (cell −). OK.
- Pin 5 BAT = BAT_SENSE (330 Ω from CELL_P, 0.1 µF to VSS). OK: matches the typical application in Fig. 9-1.
- Pin 6 V− = 2.2k to GND (PACK−). OK: matches §5.1.3.
- **Footprint:** identical to the KiCad `WSON-6_1.5x1.5mm_P0.5mm`.

### Q1/Q2 DMN2056U-13 and the protection topology
- **Pinout:** [LCSC C5208862](https://www.lcsc.com/product-detail/C5208862.html), Diodes DS38480 p.1 top view: G = 1, S = 2, D = 3, standard SOT-23.
- Q1 (DSG): G = DOUT, S = CELL_N_RAW, D = FET_DRAIN.
- Q2 (CHG): G = COUT, S = SENSE_FET (→ R9 3.3 Ω → PACK−/GND), D = FET_DRAIN.
- TI Fig. 9-1 has the DSG source at CELLN, the CHG source at PACK− and common drains. **This matches.** The body-diode orientations are correct: the DSG diode passes charge current and the CHG diode passes discharge current.
- COUT is referenced to PACK− through its internal 5 MΩ, and Q2's source sits 3.3 Ω above PACK−. The offset is negligible at these currents.
- See rank 4 for the R9 over-current ceiling.

### U5 TLV7012DDFR, SOT-23-8
- **Pinout:** [ti.com tlv7011.pdf](https://www.ti.com/lit/ds/symlink/tlv7011.pdf), SLVSDM5F p.4, "TLV7012/22 DGK, DDF": 1 OUTA, 2 INA−, 3 INA+, 4 VEE, 5 INB+, 6 INB−, 7 OUTB, 8 VCC.
- Netlist: 1 TEMP_COLD_OK, 2 TEMP_SENSE, 3 TEMP_COLD, 4 GND, 5 TEMP_SENSE, 6 TEMP_HOT, 7 TEMP_HOT_OK, 8 VBUS. OK.
- **Polarity sense is correct.** The NTC is low-side, so cold makes TEMP_SENSE high, which drives OUTA low and removes COLD_OK. Hot makes TEMP_SENSE fall below TEMP_HOT, which drives OUTB low.
- **Footprint:** identical to the KiCad `SOT-23-8` (0.65 mm pitch, matching DDF).

### U6 / U7 TPS22917DBVR, SOT-23-6
- **Pinout:** [ti.com tps22917.pdf](https://www.ti.com/lit/ds/symlink/tps22917.pdf), Table 6-1 p.4: 1 VIN, 2 GND, 3 ON, 4 CT, 5 QOD, 6 VOUT.
- U7: 1 SYS, 2 GND, 3 SYS_ON (R35 1M pull-down plus D3/D4 OR), 4 SYS_CT, 6 SYS_LOAD. OK.
- U6: 1 VLOGIC, 3 OLED_ENABLE (R24 100k pull-down), 4 OLED_CT, 6 OLED_SUPPLY. OK.
- **CT:** the datasheet says "connect capacitor from this pin **to VIN**". C29 is SYS–SYS_CT and C28 is VLOGIC–OLED_CT. OK.
- **QOD floating:** explicitly allowed ("Disabling QOD by leaving pin floating"). OK on both.
- **ON must not float:** it has an external pull-down on both parts. OK. VIH is 1 V, so the ON drive through BAT54 from 3.2 V is fine.

### U8 FM25V02A-GTR, SOIC-8
- **Pinout:** [LCSC C66029](https://www.lcsc.com/product-detail/C66029.html) Infineon datasheet, Fig. 1: 1 CS, 2 SO, 3 WP, 4 VSS, 5 SI, 6 SCK, 7 HOLD, 8 VDD.
- Netlist: 1 FRAM_CS_N, 2 FRAM_MISO (PB4), 3 VFRAM, 4 GND, 5 FRAM_MOSI (PB5), 6 FRAM_SCK (PB3), 7 VFRAM, 8 VFRAM. OK.
- **Footprint:** identical to the KiCad `SOIC-8_3.9x4.9mm`.

### D1 / D2 USBLC6-2SC6, SOT-23-6
- **Pinout:** [LCSC C7519](https://www.lcsc.com/product-detail/C7519.html) ST datasheet, Fig. 1: 1 I/O1, 2 GND, 3 I/O2, 4 I/O2, 5 VBUS, 6 I/O1.
- D2: 1/6 USB_DM, 3/4 USB_DP, 2 GND, 5 VBUS. OK.
- D1: 1/6 CC1, 3/4 CC2, 2 GND, 5 VBUS. OK.

### D3 BAT54C,215, SOT-23
- **Pinout:** [LCSC C37704](https://www.lcsc.com/product-detail/C37704.html) Nexperia Table 2: 1 A1, 2 A2, 3 common K.
- Netlist: 1 PWR_KEY, 2 PWR_HOLD, 3 SYS_ON. OK.

### D4 1N4148WS, SOD-323
- **Datasheet:** [LCSC C2128](https://www.lcsc.com/product-detail/C2128.html). The CJ datasheet marks polarity by the cathode band only.
- **Footprint:** pad 1 at (−1.05, 0). The silk bar at x = −1.61 and the Fab arrow tip both point to pad 1, so **pad 1 = cathode** (KiCad convention). It is identical to the KiCad `D_SOD-323`.
- Netlist: K (pad 1) = VBUS_WAKE, A (pad 2) = VBUS. That gives forward conduction from VBUS into the R38 → SYS_ON path, which is correct.
- UNCERTAIN only for JLC's orientation (rank 1).

### Q3 / Q4 / Q5 2N7002 (CJ), SOT-23
- **Pinout:** [LCSC C8545](https://www.lcsc.com/product-detail/C8545.html): 1 Gate, 2 Source, 3 Drain.
- Q4: G = TEMP_HOT_OK, S = GND, D = CE_MID.
- Q3: G = TEMP_COLD_OK, S = CE_MID, D = CE_N. This is a series pull-down on /CE. OK: gate drive is from the 5 V push-pull comparator.
- Q5: G = PWR_KEY, S = GND, D = COUNT_N. OK.
- Q5 note: Vth max is 2.5 V against a ≥3.0 V SYS gate drive while it sinks a 220k pull-up. Margin is adequate but not large.

### J1 GCT USB4105-GF-A-120
- **Drawing:** [LCSC C5184243](https://www.lcsc.com/product-detail/C5184243.html) GCT sheet 1 pin table.
  - GND: A1, A12, B1, B12
  - Vbus: A4, A9, B4, B9
  - CC1 A5; Dp1 A6; Dn1 A7; SBU1 A8
  - CC2 B5; Dp2 B6; Dn2 B7; SBU2 B8
  - Shell = GND
- Netlist matches: DP on A6/B6, DM on A7/B7, SBU unconnected.
- **Footprint:** identical to the KiCad `USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal`. Its layout matches GCT's recommended PCB layout (0.5 mm pitch; 2x Ø0.65 pegs; 4 shell slots).

### BT1 Q&J CR2032-BS-6-1 (C70377)
- The LCSC product page now returns "Page Not Found". The drawing came from the [JLCPCB part page](https://jlcpcb.com/partdetail/QJ-CR2032_BS_61/C70377) (QJ.BS-6, Ø20 mm holder).
- **Polarity:** the "PCB LAYOUT DIAGRAM, Top View" marks + and − on the two end pads. The + side is the same end as the positive-pin tab (item 2) in the body top view.
- **Footprint:** pad 1 (+x, CELL_P) carries the "+" silk cross and pad 2 carries "−". This is consistent with the drawing.
- **Dimensions:** land deviation as in rank 2. Pad centres are at ±14.39 mm against the vendor's ±14.5 mm.

### SW3 XUNPU TS-1088-AR02016
- **Drawing:** [LCSC C720477](https://www.lcsc.com/product-detail/C720477.html): two terminals, lands 5.50 outer / 3.40 inner, 2.00 tall. "R" means no locating post.
- **Footprint:** pads at ±2.225 mm, 1.05 × 2.0 mm. Exact.
- Netlist 1 NRST / 2 GND, which is a two-terminal N.O. switch. OK.

### SW1 / SW2 HanElectricity CPG151101S11-16 hot-swap socket, with K1/K2 CPG151101D13
- **Socket drawing:** [LCSC C41430893](https://www.lcsc.com/product-detail/C41430893.html). Recommended PCB layout: Ø3.00 holes spaced 6.35 × 2.54, pads 2.55 × 2.5 outboard of each hole. The layout is drawn from the socket side, with the left hole high and the right hole low.
- **Footprint (local):** holes at (−3.81, +2.54) and (2.54, +5.08), pads at (−7.085, 2.54) and (5.842, 5.08), 4.0 mm centre hole. It is authored in the socket-side view, and the builder mirrors local Y when placing on the bottom.
- **Absolute holes on the board, relative to the switch centre (top view):**
  - SW1: (−2.54, +3.81) and (−5.08, −2.54)
  - SW2: (+2.54, −3.81) and (+5.08, +2.54)
- **Check against the switch pins:** the MX pin pattern in top view is (−3.81, −2.54) and (+2.54, −5.08). This was confirmed from KiCad `SW_Cherry_MX_1.00u_PCB` (pins at (0,0) and (−6.35, 2.54), centre at (−2.54, 5.08)) and from the CPG151101D13 drawing. SW1 is exactly that pattern rotated 90° and SW2 is it rotated −90°. The pattern is a pure rotation, not a mirror, so the switch pins will enter the socket holes.
- **Pad offsets:** each SMD pad lies 3.275 / 3.302 mm outboard of its hole. That matches the widely used Kailh MX hot-swap footprint values (−7.085 / 5.842) and the vendor pad size.
- **Switch:** the switch drawing ([LCSC C49234235](https://www.lcsc.com/product-detail/C49234235.html), p.6 and p.8) shows 3-pin plate-mount with no fixation pegs and a Ø3.9 centre post. The board has no peg holes, which is OK for this switch.
- **Not independently verified:** I could not fetch ai03/marbastlib raw files (GitHub access blocked, and the KiCad official library has no hot-swap footprint in `Button_Switch_Keyboard`). The comparison therefore rests on the vendor drawing plus the KiCad Cherry MX pin geometry.

### DS1 HS96L01W4S03 OLED module (C5139758)
- **Pin order:** the HS datasheet ([LCSC C5139758](https://www.lcsc.com/product-detail/C5139758.html)) §1.5 Pin Definition and the outline drawing p.6 "4SPI" table give 1 GND, 2 VCC, 3 SCL, 4 SDA, 5 RES, 6 DC, 7 CS.
- **Netlist:** 1 GND, 2 OLED_SUPPLY, 3 OLED_SCK, 4 OLED_MOSI, 5 OLED_RESET_N, 6 OLED_DC, 7 OLED_CS_N. OK. SCL/SDA are the SPI SCK/MOSI inputs.
- **Physical orientation (front / display-side view):**
  - the header runs along the top edge, 1.50 mm in from a 27.80 mm edge, i.e. 12.40 mm from centre;
  - pin 1 (square pad, GND) is at the left;
  - the pins are on a 2.54 mm pitch, 15.24 mm span, centred.
- **Footprint** (placed top side, rot 0): pin 1 at (−7.62, −12.40), square, left and top. It matches.
- **Supply:** VCC is rated 3–5 V and logic ≤ 3.3 V, against a 3.2 V rail. OK.

## Items needing resolution (not resolvable from datasheets)
1. JLC bottom-side placement preview: confirm pin 1, the cathode band and the holder "+" on each polarised part (rank 1).
2. BT1 land versus the vendor recommended 3.0 × 4.2 mm land (rank 2). Covered by the first-article retention gate.
3. Optional: an independent comparison of the hot-swap footprint with an open-source library (marbastlib / ai03) once GitHub access is available.
