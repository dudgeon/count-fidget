# Independent review of the Q2 power proposal

**2026-09-15.** Reviewed [q2-power-design.md](q2-power-design.md), `scripts/build_q2_model.py`, the original netlist and primary component specifications. The proposed topology is suitable to continue into a separately checked Q2 schematic/layout. **No new wiring or pin-polarity defect was found in this proposal.** This review is not hardware qualification or a release decision.

## Connectivity and fault direction

- U5's TLV7032DGKR pin assignments match the dual-device table: channel A compares cold reference (+) with sensor (−); channel B compares sensor (+) with hot reference (−). Separate outputs command the two enable FETs. Both conditions must permit charging. [TI TLV7032/42 datasheet, Table 4-2](https://www.ti.com/lit/ds/symlink/tlv7032.pdf).
- Nexperia's 2N7002 pins are **1 gate, 2 source, 3 drain**. Q3 runs CE_N to CE_MID; Q4 runs CE_MID to ground. Their source-to-drain body diodes do not provide a positive CE_N-to-ground bypass when either device is OFF. This supports the intended series-AND behavior. [Nexperia pinning and device characteristics](https://assets.nexperia.com/documents/data-sheet/2N7002.pdf).
- R14/R15 are now **100 kΩ to ground** in both proposal and model. The earlier provisional model's 1 MΩ values have been corrected. The old powered output pullup is absent. This removes the identified monitor-supply-loss command path; it does not prove immunity to every component fault.
- An open comparator-output trace is passively disabled only if the gate-to-ground pulldown remains connected to the gate. A break between the gate and that resistor, including a package connection fault, can leave the gate floating. Do not describe all gate-open faults as covered. R12-open, stuck-HIGH output, FET-short and monitor-ground faults also remain outside the demonstrated protection.

TI describes TLV7032 POR outputs as LOW during supply ramp-up/down below minimum supply, unlike the prior open-drain device's high impedance. Its **200 µs** startup value is typical. No guaranteed zero-supply sink strength or complete fault-disable time was established. The proposal appropriately keeps powered LOW/HIGH levels, leakage, passive gate decay and brownout behavior as separate validation questions. See [TI §6.4 and §5.9–5.10](https://www.ti.com/lit/ds/symlink/tlv7032.pdf).

## Independent temperature calculation

An independent 256-corner calculation used R10/R11/R12/R13 = 57.6/115/24.3/16.2 kΩ, each ±2.01%; sensor R25 and B25/50 each ±1%; supply endpoints 2.95/5.5 V; and additive threshold error ±21.5 mV. It reproduced the proposal:

| Calculated envelope | Cold threshold | Hot threshold |
|---|---:|---:|
| Conditional constant-beta model | **4.8316–10.2040°C** | **31.8461–40.4963°C** |

This is a calculation cross-check, not a certified 0–45°C operating envelope. B25/50 is not a guaranteed full R/T curve below 25°C. Comparator specifications have stated supply/common-mode test conditions; the additional 1 mV allowance is an engineering assumption. Installed sensor contact, lag, contamination and actual component tolerances must still be checked.

The excitation improvement is real, but current alone must not be converted into a blanket self-heating claim. With R10 at −2.01% and VBUS=5.5 V:

- Branch-current upper bound: **97.445 µA** for any nonnegative sensor resistance.
- Dissipation with a nominal 10 kΩ sensor: **0.06852 mW**.
- Maximum dissipation over any sensor resistance: `VBUS²/(4×R10)` = **0.13399 mW**, reached when sensor resistance equals R10.

[Murata's NCP18 specification §2.2](https://www.murata.com/-/media/webrenewal/products/thermistor/ntc/ncp/ncp18.ashx?cvid=20231225010000000000&la=en) relates its 0.100 mA figure to 0.1°C self-heating under specified conditions and gives approximate dissipation constants. Using the bare still-air 1 mW/°C figure, the last bound is about **0.134°C**, not universally below 0.1°C. The installed battery-contact assembly differs from that condition. The proposal does not claim otherwise; retain its measurement gate.

## U3 and implementation limits

**TPS7A0230PDBVR** is an actual orderable 3.0 V DBV part. The proposed 1 IN/2 GND/3 EN/4 NC/5 OUT mapping is correct; NC-to-ground and EN-to-IN are permitted. Active discharge operates on disable/UVLO, so choosing the P variant must retain output-collapse, reverse-current and FRAM interruption tests. The brief reverse-current limit is 5% of rated current, not an allowance for continuously driving V3 from a programmer. [TI TPS7A02 Table 5-1, §7.3.2/7.3.4 and ordering addendum](https://www.ti.com/lit/gpn/TPS7A02). The original RFQ already directs the fixture to sense V3 and power through the intended supply.

Adopt the manufacturer-supported DGK footprint treatment in [the solder-mask review](q2-solder-mask-review.md), then check actual native Q2 connectivity, routing, mask and paste. This audit did not run a board generator, inspect a completed Q2 schematic, perform ERC/DRC, flash a target or measure a circuit. Q1 remains preserved. Existing cell/protection, low-current charger, thermal, LCD, fit and first-article release gates remain open.
