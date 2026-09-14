# Q1 electronics — routed prototype for quotation

Q1 supersedes the Rev0 topology and pin allocation. The actual KiCad 10 board, four copper Gerbers, drill files, BOM and placements now exist. KiCad DRC reports zero violations and zero unconnected items after routing/ground fill. This is a geometric/connectivity check, not a safety certification. A native schematic with electrical-rule validation has not yet been produced; netlist.json and build_pcb.py define the current connectivity explicitly. Prototype quotation is authorized; manufacture is not released.

The MCU is MSP430FR4133IG48R, 48-pin TSSOP. The earlier 64-pin allocation is obsolete. Two Cherry MX1A-E1NW keys count/reset; DS1 is the eight-digit DE188 reflective LCD, with L0..3 as commons and L8..19 plus L24..27 as segments. The compiled firmware uses 3.0 V supply-referenced internal 1/3-bias generation, 1/4 multiplex and about 64 Hz frame rate. It saves a two-record FRAM journal after each accepted count, blanks the LCD and sleeps after 30 seconds, and wakes on either button edge. Flashing/bench qualification remains required.

USB-C has independent 5.1k CC pull-downs and USBLC6-2SC6 ESD protection. Data and SBU pins are unused. BQ25185DLHR provides the power path, 4.2 V charge target, 100 mA input limit (24k), and 18.2 mA nominal charge current (16.5k). Low-current compensation is ISET -> 2k -> 4.7n -> GND, following the TI EVM R12/C7 topology. It is NOT connected to SYS. SYS feeds a TPS7A0230DBVR 3.0 V regulator. No always-on LED is fitted.

The thermistor is part of the off-board CC-BAT-001 lead assembly. A USB-powered TLV7042DGKR window comparator and 2N7002 gate the charger's CE input independently of firmware. R10=10k excites the NTC; the 49.9k / 40.2k / 60.4k reference ladder gives conservative nominal charge-enable boundaries near 8 and 36 C. Open/short NTC inhibit charging. A fixed 10k on TS is part of this alternative hardware temperature-control scheme; it does not replace the real cell sensor. Verify tolerance, self-heating and thermal contact before release.

BQ29700DSER, two DMN2056U-7 FETs and a 3.3-ohm sense resistor provide independent cell protection. RAW cell negative is isolated from system ground through the FET path. The nominal 2.8 V protection threshold has a tolerance that can fall below the EEMB 2.75 V discharge endpoint; this specific issue requires cell-maker approval or a protection redesign before release. Do not characterize the battery protection as qualified.

Mechanical integration: 42x40x1 mm board, four layers, 5 mil minimum tracks/clearance, 0.3 mm through vias. LCD glass rear is 4.0 mm above the top, keeping it above U1 and the connector bodies. Hand solder the LCD within its 260 C / 5 s limit and trim tails <=1 mm. Bottom SMT is mostly under the LCD area; the cell rests in the enclosure floor, disconnected during soldering. Q1 has two rear mounting holes and a right-side USB port at y=13.3 mm. The old enclosure study must be updated to these positions before final printing.

Outstanding engineering: display response qualification (Rev4 combined on/off 440 ms), exact cell/NTC pack approval, protection-limit resolution, first-article charging and fault tests, MCU hardware behavior and brownout tests, a conventional validated schematic, and final enclosure fit. See procurement/RFQ-Q1.md for the full test scope and primary sources. Do not fabricate until these release decisions and a purchase are approved.

## Current pin-to-net schedule

Unlisted IC pads are deliberately not connected in Q1. Pin functions and numbering are based on the selected package's primary data sheets; this schedule permits independent review against them.

### DS1 — DE188-RU-30/7,5/V(3V)

| Pin | Net |
|---|---|
|20|COM0|
|1|COM1|
|11|COM2|
|10|COM3|
|2|SEG0|
|3|SEG1|
|4|SEG2|
|5|SEG3|
|6|SEG4|
|7|SEG5|
|8|SEG6|
|9|SEG7|
|12|SEG8|
|13|SEG9|
|14|SEG10|
|15|SEG11|
|16|SEG12|
|17|SEG13|
|18|SEG14|
|19|SEG15|

### SW1 — MX1A-E1NW

| Pin | Net |
|---|---|
|1|COUNT_N|
|2|GND|

### SW2 — MX1A-E1NW

| Pin | Net |
|---|---|
|1|RESET_N|
|2|GND|

### J1 — USB4105-GF-A

| Pin | Net |
|---|---|
|A1|GND|
|A12|GND|
|B1|GND|
|B12|GND|
|A4|VBUS|
|A9|VBUS|
|B4|VBUS|
|B9|VBUS|
|A5|CC1|
|B5|CC2|
|SH|GND|

### J2 — SM04B-SRSS-TB(LF)(SN)

| Pin | Net |
|---|---|
|1|CELL_P|
|2|CELL_N_RAW|
|3|TEMP_SENSE|
|4|GND|

### U1 — MSP430FR4133IG48R

| Pin | Net |
|---|---|
|6|COM0|
|5|COM1|
|4|COM2|
|3|COM3|
|14|GND|
|15|V3|
|16|SBWTDIO|
|17|SBWTCK|
|26|COUNT_N|
|25|RESET_N|
|10|LCDCAP1|
|11|LCDCAP0|
|2|SEG0|
|1|SEG1|
|48|SEG2|
|47|SEG3|
|46|SEG4|
|45|SEG5|
|44|SEG6|
|43|SEG7|
|42|SEG8|
|41|SEG9|
|40|SEG10|
|39|SEG11|
|38|SEG12|
|37|SEG13|
|36|SEG14|
|35|SEG15|

### U2 — BQ25185DLHR

| Pin | Net |
|---|---|
|1|SYS|
|2|CELL_P|
|4|CE_N|
|5|GND|
|6|TS_FIXED|
|7|VSET|
|8|ISET|
|10|VBUS|
|11|GND|

### U3 — TPS7A0230DBVR

| Pin | Net |
|---|---|
|1|SYS|
|2|GND|
|3|SYS|
|4|GND|
|5|V3|

### U4 — BQ29700DSER

| Pin | Net |
|---|---|
|2|COUT|
|3|DOUT|
|4|CELL_N_RAW|
|5|BAT_SENSE|
|6|VMINUS|

### Q1 — DMN2056U-7

| Pin | Net |
|---|---|
|1|DOUT|
|2|CELL_N_RAW|
|3|FET_DRAIN|

### Q2 — DMN2056U-7

| Pin | Net |
|---|---|
|1|COUT|
|2|SENSE_FET|
|3|FET_DRAIN|

### U5 — TLV7042DGKR

| Pin | Net |
|---|---|
|1|TEMP_OK|
|2|TEMP_SENSE|
|3|TEMP_COLD|
|4|GND|
|5|TEMP_SENSE|
|6|TEMP_HOT|
|7|TEMP_OK|
|8|VBUS|

### Q3 — 2N7002

| Pin | Net |
|---|---|
|1|TEMP_OK|
|2|GND|
|3|CE_N|

### D1 — USBLC6-2SC6

| Pin | Net |
|---|---|
|1|CC1|
|2|GND|
|3|CC2|
|4|CC2|
|5|VBUS|
|6|CC1|

### R1 — RC0603FR-075K1L

| Pin | Net |
|---|---|
|1|CC1|
|2|GND|

### R2 — RC0603FR-075K1L

| Pin | Net |
|---|---|
|1|CC2|
|2|GND|

### R3 — RC0603FR-0724KL

| Pin | Net |
|---|---|
|1|VSET|
|2|GND|

### R4 — RC0603FR-0716K5L

| Pin | Net |
|---|---|
|1|ISET|
|2|GND|

### R5 — RC0603FR-0710KL

| Pin | Net |
|---|---|
|1|TS_FIXED|
|2|GND|

### R6 — RC0603FR-07100KL

| Pin | Net |
|---|---|
|1|VBUS|
|2|CE_N|

### R7 — RC0603FR-07330RL

| Pin | Net |
|---|---|
|1|CELL_P|
|2|BAT_SENSE|

### R8 — RC0603FR-072K2L

| Pin | Net |
|---|---|
|1|GND|
|2|VMINUS|

### R9 — RC0603FR-073R3L

| Pin | Net |
|---|---|
|1|SENSE_FET|
|2|GND|

### R10 — RC0603FR-0710KL

| Pin | Net |
|---|---|
|1|VBUS|
|2|TEMP_SENSE|

### R11 — RC0603FR-0749K9L

| Pin | Net |
|---|---|
|1|VBUS|
|2|TEMP_COLD|

### R12 — RC0603FR-0740K2L

| Pin | Net |
|---|---|
|1|TEMP_COLD|
|2|TEMP_HOT|

### R13 — RC0603FR-0760K4L

| Pin | Net |
|---|---|
|1|TEMP_HOT|
|2|GND|

### R14 — RC0603FR-07100KL

| Pin | Net |
|---|---|
|1|VBUS|
|2|TEMP_OK|

### R15 — RC0603FR-071ML

| Pin | Net |
|---|---|
|1|TEMP_OK|
|2|GND|

### R16 — RC0603FR-0747KL

| Pin | Net |
|---|---|
|1|V3|
|2|SBWTDIO|

### R17 — RC0603FR-07470KL

| Pin | Net |
|---|---|
|1|V3|
|2|COUNT_N|

### R18 — RC0603FR-07470KL

| Pin | Net |
|---|---|
|1|V3|
|2|RESET_N|

### R19 — RC0603FR-072KL

| Pin | Net |
|---|---|
|1|ISET|
|2|RC_COMP|

### C4 — GRM188R71H104KA93D

| Pin | Net |
|---|---|
|1|BAT_SENSE|
|2|CELL_N_RAW|

### C7 — GRM188R71H104KA93D

| Pin | Net |
|---|---|
|1|V3|
|2|GND|

### C8 — GRM188R71H104KA93D

| Pin | Net |
|---|---|
|1|LCDCAP1|
|2|LCDCAP0|

### C9 — GRM188R71H104KA93D

| Pin | Net |
|---|---|
|1|VBUS|
|2|GND|

### C1 — GRM21BR71E225KA73L

| Pin | Net |
|---|---|
|1|VBUS|
|2|GND|

### C2 — GRM21BR61E106KA73L

| Pin | Net |
|---|---|
|1|SYS|
|2|GND|

### C3 — GRM21BR71E225KA73L

| Pin | Net |
|---|---|
|1|CELL_P|
|2|GND|

### C5 — GRM21BR71E225KA73L

| Pin | Net |
|---|---|
|1|SYS|
|2|GND|

### C6 — GRM21BR71E225KA73L

| Pin | Net |
|---|---|
|1|V3|
|2|GND|

### C10 — GRM1885C1H102JA01D

| Pin | Net |
|---|---|
|1|SBWTDIO|
|2|GND|

### C11 — GRM1885C1H102JA01D

| Pin | Net |
|---|---|
|1|COUNT_N|
|2|GND|

### C12 — GRM1885C1H102JA01D

| Pin | Net |
|---|---|
|1|RESET_N|
|2|GND|

### C13 — C0603C472J5RACTU

| Pin | Net |
|---|---|
|1|RC_COMP|
|2|GND|

