# Q2 protection, thermal and regulator review

Reviewed 2026-09-15 UTC. Read-only review of Q1 source definitions, JSON netlist, routed-board pad assignments and primary manufacturer documents. No engineering source, BOM, routed board or firmware was changed or rebuilt. Q1 remains a quotation prototype; this review is not physical validation or release approval.

## Newly quantified findings

### NTC excitation and self-heating

**Confirmed calculation:** [R10 is 10 kΩ from VBUS to TEMP_SENSE](../electronics/build_pcb.py#L103); the [specified sensor is NCP18XH103F03RB, 10 kΩ at 25°C](../procurement/RFQ-Q1.md#L60). At nominal 5 V and 25°C, sensor current is 0.250 mA and dissipation is 0.625 mW. Current is approximately 0.166–0.299 mA across the nominal enabled resistance window.

[Murata's specification, §2.2](https://www.murata.com/-/media/webrenewal/products/thermistor/ntc/ncp/ncp18.ashx?cvid=20231225010000000000&la=en) gives 0.100 mA maximum operating current under a **0.1°C self-heating condition**. This is not a destructive-current limit. Its approximate dissipation constants imply 0.625°C rise for the unmounted still-air condition, or 0.208°C on its specified 12 × 12 × 1.6 mm test PCB.

**Inference and remaining gap:** Those thermal models do not establish the temperature rise of the insulated cell-mounted assembly. Q1 exceeds the manufacturer's low-self-heating measurement condition; it does not thereby demonstrate overheating or a violated cell-temperature limit. This quantifies existing E03. Excitation, component tolerance and actual thermal contact must be qualified together before release.

### Display replacement versus discharge protection

**Calculated constraint:** [R9 is 3.3 Ω](../electronics/build_pcb.py#L102). The BQ29700's nominal 100 mV discharge-overcurrent threshold divided by that resistance plus both conducting FET resistances gives a trip near **30 mA**. An illustrative tolerance calculation reaches about 25 mA; it is not a complete worst-case bound because hot FET resistance, gate voltage and routing resistance remain relevant. [BQ2970, device table and §6.6](https://www.ti.com/lit/gpn/BQ2970), [DMN2056U electrical characteristics](https://www.diodes.com/datasheet/download/DMN2056U.pdf)

**Inference:** An OLED operating around the 23–29 mA example in [display-options-Q2.md](display-options-Q2.md), plus MCU and other loads, could approach or trigger protection. That display example is not a measured battery current or established sparse-digit consumption. This is a replacement-design constraint, not a demonstrated Q1 fault. No replacement is selected by this review.

### UV tolerance evidence needs correction

[E01](open-issues.md#L7) states 2.8 V ±0.1 V. The retrieved BQ2970 Rev. I table specifies **±50 mV at 25°C**. The blanket ±0.1 V figure and resulting assertion of a below-2.75 V threshold need their original source or temperature evidence. This does not establish an all-temperature 2.75 V minimum; retain the cell-maker approval gate. Recovery charging below UV also belongs in cell compatibility review. [TI datasheet, §6.6 and §8.4.6–8.4.7](https://www.ti.com/lit/gpn/BQ2970)

## Checks with no new wiring defect found

| Area | Result and remaining qualification |
| --- | --- |
| Protection wiring | [U4, Q1 and Q2 definitions](../electronics/build_pcb.py#L86) match the manufacturer topology: opposing common-drain FETs, correct BAT/VSS/V− references, 330 Ω BAT filter and 2.2 kΩ V− resistor. JSON and actual board pad-net assignments agree. This is not a new DRC run or proof of routed connectivity/fault performance. Preserve the prohibition on bypassing CELL_N_RAW to GND. [TI application circuit](https://www.ti.com/lit/gpn/BQ2970) |
| Thermal comparator logic | [U5 and resistor connections](../electronics/build_pcb.py#L89) have the correct polarity and joined open-drain outputs. Open/short NTC conditions inhibit charging. Calculated nominal thresholds are 20.160 kΩ and 6.704 kΩ, approximately 7.63°C and 35.90°C using the nominal beta approximation. These are not qualified temperature limits. The dual TLV7042 table specifies 10 mV typical hysteresis, 3–25 mV, rather than the single-device 7 mV figure; typical equivalent hysteresis is approximately 0.21–0.24°C. Full tolerance, startup and attached-sensor checks remain open. [TLV7042, pin table and §5.9](https://www.ti.com/lit/gpn/TLV7042) |
| LDO connection and capacitance | [U3](../electronics/build_pcb.py#L85) has the correct pin mapping; EN may connect to IN and pin 4 may be grounded. [C6](../electronics/build_pcb.py#L122) is 2.2 µF X7R, an appropriate capacitor type. TI requires at least 0.5 µF effective output capacitance and supports low-ESR ceramics. Exact bias/temperature derating was not verified; nominal capacitance alone does not close stability qualification. [TPS7A02, §6.3 and §8.1](https://www.ti.com/lit/gpn/TPS7A02) |
| Exact U3 ordering identity | Existing E14 remains confirmed: exact TPS7A0230DBVR is unmatched; TI lists active TPS7A0230PDBVR. P denotes active output discharge, requiring electrical review including brownout/FRAM behavior. No substitution is authorized by this review. [Existing adapter record](../procurement/JLCPCB-IMPORT-ADAPTER-Q1.md#L37), [TI orderable part](https://www.ti.com/product/TPS7A02/part-details/TPS7A0230PDBVR), [TPS7A02, §7.3.2 and §9.1.1](https://www.ti.com/lit/gpn/TPS7A02) |

## Preserved gates

Cell-maker approval, NTC pack design/lifecycle, charge-current and low-current-loop qualification, protection fault tests, effective capacitance, physical board testing and the other [open issues](open-issues.md) remain unresolved. Existing uploaded quote artifacts remain Q1. A quote, engineering release and paid order are separate approvals.
