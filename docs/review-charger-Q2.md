# Charger review for Q2 decisions

Reviewed 2026-09-15 against the existing Q1 sources and routed board. This is a read-only engineering assessment; the Q2 heading does not identify a newly implemented circuit or release. No schematic, board, BOM, firmware, HEX, Gerber or RFQ package was changed by this review. No hardware measurements or new DRC/ERC were performed.

## Result: the alleged U2 pin/resistor error is not supported

The existing **4.2 V, 100 mA input-limit setting and 18.18 mA nominal charge-current setting are intentional and correctly encoded**. `VSET` is the project's net name for the charger's combined **ILIM/VSET** pin; it is not a separate voltage-only control that requires another ILIM resistor. Pins 3 and 9 are optional status outputs, not missing configuration connections.

The controlling source is [TI BQ25185 datasheet, SLUSF65B, revised August 2026](https://www.ti.com/lit/ds/symlink/bq25185.pdf), Table 4-1, Table 6-1, sections 5.5, 6.1.1.4, 6.3.6 and 6.3.9, and package drawing DLH0010A.

### Complete U2 pin comparison

| Pad | TI function | Actual routed Q1 net | Board line |
|---|---|---|---:|
| 1 | SYS | SYS | 7885 |
| 2 | BAT | CELL_P | 7893 |
| 3 | STAT2 | Unconnected | 7901 |
| 4 | CE, active low | CE_N | 7908 |
| 5 | GND | GND | 7916 |
| 6 | TS/MR | TS_FIXED | 7924 |
| 7 | ILIM/VSET | VSET | 7932 |
| 8 | ISET | ISET | 7940 |
| 9 | STAT1 | Unconnected | 7948 |
| 10 | IN | VBUS | 7955 |
| 11, exposed pad | Thermal/ground pad | GND | 7963 |

Board references above are in `electronics/click-counter-Q1.kicad_pcb`. The U2 footprint begins at line 7663. Its 2.2 × 2.0 mm body, 0.4 mm pitch and 0.9 × 1.5 mm exposed pad correspond to DLH0010A. The bottom-side pad arrangement is consistent with the selected footprint. This establishes package/pin identity, not solder-process qualification.

This agrees with `electronics/build_pcb.py:84`, `electronics/netlist.json:162`, and the schedule at `electronics/design.md:118`. TI permits unused STAT1/STAT2 to float. The grounded exposed pad is present; its soldering and thermal performance still require assembly review.

### Programming components and expected behavior

| Item | Actual source/routed connection | Assessment |
|---|---|---|
| R3, 24 kΩ | VSET–GND; source line 96, board pad line 4932 | TI Table 6-1 selects 4.2 V and ILIM100. |
| R4, 16.5 kΩ | ISET–GND; source line 97, board pad line 5854 | Nominal current = 300 AΩ / 16,500 Ω = 18.18 mA. |
| R5, 10 kΩ | TS_FIXED–GND; source line 98, board pad line 8680 | TI permits this fixed resistance when native TS monitoring is unused. It does not measure the cell. |
| R19, 2 kΩ; C13, 4.7 nF | ISET–R19–RC_COMP–C13–GND; source lines 112/124, board pad lines 6122/8814 | Series compensation branch; it is not connected to SYS and does not replace R4. |

Source line numbers in this table refer to `electronics/build_pcb.py`; board line numbers refer to `electronics/click-counter-Q1.kicad_pcb`.

**“100 mA” names the programmed input-limit option.** TI's electrical table specifies 80–98 mA, typically 90 mA, at 5 V for this option. It is distinct from battery charging current. Nominal precharge and termination are approximately 3.64 mA and 1.82 mA. R3 open disables charging; R3 short selects battery-only operation. ISET-open behavior is approximately 1.5 mA, while detected ISET shorts inhibit charging. These fault behaviors do not justify leaving the programming pins unconnected.

The datasheet's low-current RC wording mentions 50 pF, whereas the [TI EVM guide](https://www.ti.com/lit/ug/sluucs1/sluucs1.pdf?ts=1779971432886) specifies R12 = 2 kΩ and C7 = 4.7 nF. A [TI engineer's clarification](https://e2e.ti.com/support/power-management-group/power-management/f/power-management-forum/1477929/bq25185-extra-rc-circuit-at-low-charge-currents) expressly identifies that EVM pair as the intended compensation network and says its need depends on stability. Q1 follows that EVM topology. This is evidence for retaining the documented implementation pending qualification, not proof that Q1's charging loop is stable.

## Thermal behavior and newly explicit fault-analysis gap

The external window circuit's normal polarity is consistent with [TI TLV7042 datasheet](https://www.ti.com/lit/gpn/TLV7042), Table 4-2: U5 compares TEMP_SENSE against TEMP_COLD and TEMP_HOT, with its open-drain outputs joined at TEMP_OK. U5, Q3 and R10–R15 are defined at `electronics/build_pcb.py:89` and lines 103–108. Routed U5 pad connections begin at `electronics/click-counter-Q1.kicad_pcb:3150` and agree with the source.

From the resistor ratios, the nominal enabled NTC resistance interval is approximately **6.704–20.160 kΩ**. The assumed NTC curve produces the documented roughly 8–36°C interval. An open NTC raises TEMP_SENSE toward VBUS and a short pulls it toward GND; either condition requests charge disable in the normally powered circuit. At 25°C/5 V, the 10 kΩ excitation arrangement dissipates approximately **0.625 mW in the NTC**. Its temperature error depends on actual thermal coupling and must be measured.

**Additional inferred single-fault mechanism:** loss of U5's supply connection can permit charging. TI section 6.4 specifies high-impedance TLV7042 outputs while unpowered/POR. If U5 loses its VBUS connection while R14 retains VBUS, R14 = 100 kΩ and R15 = 1 MΩ pull TEMP_OK toward 4.55 V at a 5 V input. Q3 then pulls CE_N low, enabling the charger; R5 still presents the fixed normal-temperature resistance to TS/MR. Thus a failed monitor supply can defeat temperature inhibition even though ordinary NTC open/short detection is correctly polarized.

This is a **fault-analysis gap inferred from connectivity and component specifications**, not a demonstrated fault on a built board. It is not an instruction to rewrite Q1 automatically. A controlled Q2 review should either implement a temperature interlock that defaults to charge-disabled when monitor power is lost, or qualify an independent temperature-inhibit path with limits appropriate to the cell. Validate supply-loss, startup, ramp-down, sensor faults and recovery before release. Nominal threshold checks alone do not close this mechanism.

## Cell qualification and release implications

The [EEMB LIR2032 specification currently linked from its product page](https://eemb.oss-accelerate.aliyuncs.com//uploads/20230323/ba65f4e593715c5dedf377f550c58f6b.pdf) is document ZJQM-RD-SPC-H0339 dated 2019-04-19. It specifies 45 mAh nominal capacity and, at 25°C, standard 0.2C and fast 1C CC/CV characterization to 4.20 V, ending below 0.05C. Q1's nominal 18.18 mA is about 0.404C; its nominal 1.82 mA termination is below 0.05C = 2.25 mA. These comparisons do not establish the approved charge envelope across temperature, cell variation or the custom pack construction.

The pin/resistor allegation requires **no demonstrated electrical correction**. A useful documentation refinement would label 100 mA as the selected option and distinguish it from its specified current range. Continue the existing gates in `docs/open-issues.md:7`: E01 protection limits, E03 cell/NTC pack approval, E04 low-current CC/CV/termination/stability and power-path tests, E05 thermal tolerance/contact tests, and E06 independent schematic/ERC review. The inferred monitor-supply fault above adds a specific failure case for that review. Preserve E11 package/placement/DFM qualification as well.

In particular, generic charge-current accuracy stated for currents at or above 40 mA must not be presented as qualification at 18.18 mA. The programmed voltage/current and correct pin map are necessary evidence, but they do not release this lithium-ion product for manufacture or use.

## Read-only verification scope

A direct comparison of the routed board's pad/net assignments against `electronics/netlist.json` passed for 19 relevant footprints: U2, U5, Q3, J2, R3, R4, R5, R6, R10–R15, R19, C1, C2, C3 and C13. Values and compensation topology were also inspected against `electronics/build_pcb.py:96`–124. This comparison checks agreement between artifacts; it is not an independent proof of copper connectivity, fresh DRC, ERC, thermal performance or hardware safety.
