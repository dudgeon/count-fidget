# Q5 power design — soft power latch, coin-cell holder, battery gauge

Status: implemented engineering candidate, 25 September 2026. Every number below comes from a stated datasheet value, a bounded calculation in [`simulation/q5-power/check.py`](../simulation/q5-power/result.json), or the instruction-level emulator. **None of it is a measurement.** Q4's [power design](q4-power-design.md) remains the reference for the unchanged charger, protector, regulator, FRAM and OLED-rail circuits.

## What changed from Q4 and why

| Change | Parts | Issue | Reason |
|---|---|---|---|
| **Soft power latch** on the existing U7 load switch | U7 ON now on SYS_ON; D3 BAT54C, D4 1N4148WS, Q5 2N7002, R34 100k, R35 1M, TP13 | #12, #5 | Q4 slept at ~80 µA, most of it the TLV767 IQ plus its feedback divider, giving 2–3 weeks of battery. Switching everything below SYS off removes that drain without replacing the reviewed regulator. |
| **Faster U7 slew** | C28, C29 22 nF → 4.7 nF (C0G) | #12 | A short, deliberate press must be able to latch power. |
| **ON-node protection and hold** (design lock) | R38 100k in series from D4, C40 **10 nF** on SYS_ON (4.7 nF at the 25 Sep lock, raised 26 Sep) | review | VBUS hot-plug ringing is filtered below U7 ON's 6 V absolute maximum (τ 0.9 ms). C40 bridges contact bounce up to about 9.9 ms and turns U7 off about 21 ms after the last source releases. |
| **Basic-part values** (26 Sep) | R4 18k (charge 16.7 mA), temperature window 56k/82k/18k/12k (7.3–35.8 °C nominal), R32 75 Ω, Q1/Q2 AO3400A, 50 V 0805 capacitors | cost review | See the REVIEW-Q5 Basic-part review. Each Extended type was a $3.07 feeder fee per order. |
| **U5 supply filter** (26 Sep) | R39 1k from VBUS to U5_VCC, with C9 100 nF | first-order review | The TLV7012 has a 6 V absolute maximum and sat on raw VBUS, where cable hot-plug ringing can overshoot. The 0.1 ms RC filter removes it; U5's ~1.3 µA supply current drops about 1 mV. |
| **Cell holder and onboard NTC** replace the J2 pack harness | BT1 CR2032-BS-6-1 (C70377), TH1 NCP18XH103F03RB; J2 removed | #13 | The Q4 pack/NTC harness was not a JLC inventory part and was unqualified. The holder is vendor-soldered SMT. The cell is a user-supplied LIR2032. |
| **Battery sense** | R36/R37 150k 0.1 %, C37 100 nF, PA4 | #9.4, #12 | Low-battery warning, a gauge and a storage cut-off. |
| **Charger status** | BQ25185 STAT1 → PA5, STAT2 → PA6 | new | CHG, done and fault indication. It also detects USB independently of the ADC. |
| **OLED supply not grounded on hard reset** | U6 QOD pin now NC | #8 | Q4 discharged the module supply through QOD on every NRST. That is outside SSD1315 §6.9.2 power-down sequencing. |
| **Comparator package** | U5 TLV7012DGKR → TLV7012DDFR (same die and pinout, SOT-23-8) | #13 | The DGKR had 21 units of JLC stock, below the ten-board screen with spares. The DDFR had 881. |

The regulator (TLV767), its divider and the rail monitor are unchanged. They now run only while the board is on, so issue #5's recommended nano-IQ LDO swap is unnecessary. Keeping the reviewed rail avoids re-opening the USB-PHY and OLED-logic rail corners (E26).

## Soft power latch

```
SYS ──SW1(COUNT)──► PWR_KEY ──D3.A1─┐
                     │  R34 100k    ├─► SYS_ON ──► U7 ON   (R35 1M to GND)
PB2 PWR_HOLD ──────────────D3.A2────┤   C40 10n to GND
VBUS ──────D4──R38 100k─────────────┘
PWR_KEY ──► Q5 gate: Q5 pulls COUNT_N (PA0) low while COUNT is pressed
```

- **Off:** U7 is off, and the TLV767, MCU, FRAM, OLED, dividers and pull-ups are unpowered. Off current is the BQ29700 (4 µA) plus the BQ25185 battery quiescent current (4 µA): **8.0 µA typical, 11.1 µA maximum**.
- **Power-on by COUNT:** the key puts SYS on U7 ON through D3. tON is 17.9 ms typical. `Reset_Handler` drives PB2 before RAM initialisation, and C40 keeps ON high for about 9.9 ms after the key opens. The press must last about **10.5 ms typical, 16.3 ms with a 25 % slew allowance**; a deliberate press is ≥ 50 ms. The behavioural ngspice transient ([q5-latch-spice](../simulation/q5-latch-spice/README.md)) gives a worst-corner minimum of 14.5 ms and latched 120/120 bouncing presses. A shorter tap simply does not latch. The ON node stays ≥ 2.7 V on a 3.0 V cell, above VIH 1.0 V. The power-on press is counted once (firmware sees the POR flag and COUNT still low).
- **USB:** VBUS through D4 and R38 always holds U7 on, so the ROM DFU and charging work with the application unloaded. The ON node sits at 3.36–4.41 V (R38/R35 divider), above VIH and inside the check's 5.5 V limit.
- **Power-off:** firmware releases PB2 after 30 s of inactivity on battery, following display power-down and FRAM sleep. If the board is still powered after 200 ms (USB present, or the COUNT key held), firmware falls back to Q4-style Stop with PB2 low. Then unplugging USB or releasing the key turns the board off.
- **Inrush at switch-on:** 25.3 µF downstream (with +10 %) over the 7.5 ms tR gives **12.6 mA** (23.7 mA if the slew were twice as fast).
  - The BQ29700 overcurrent threshold over temperature is at least **24.8 mA**: VOCD 100 ±15 mV into R9 3.3 Ω +1 % plus two AO3400A RDS(on) (≤ 48 mΩ at VGS 2.5 V). This corrects the review's finding that the earlier 27.3 mA figure was optimistic.
  - More importantly, OCD cannot trip on inrush at all: the pulse (7.5 ms) is shorter than the minimum OCD delay tOCDD (20 ms −20 % = 16 ms), and the short-circuit threshold needs ≥ 117 mA.
  - DC-bias derating lowers the real value. Measure it on a first article.
- **NRST pinhole on battery** releases PB2, so it acts as a full power cycle. The count is safe because a reset commits only on a completed hold-and-release (issue #3).

## Display supply (issue #8)

- **QOD policy:** U6 QOD (pin 5) is unconnected. On any hard reset (NRST, BOR, DFU entry), PB1 goes Hi-Z, R24 turns U6 off, and the module supply now floats and decays through the module's own load. SSD1315 Rev 1.1 §6.9.2 forbids pulling VBAT to ground. The firmware's normal shutdown order is unchanged (AEh, 8Dh 10h, 120 ms guard, then off), and the emulator checks it on every power-off.
- **Supply voltage:** the module still runs from VLOGIC through U6, 3.151–3.259 V regulated. The module drawing gives an external supply range of 3–5 V (§2). The 3.5–4.2 V figure (§3.2) is the SSD1315 internal DC/DC VBAT specification. Which one governs depends on the module's undocumented internal power tree.
  - Q5 improves the margin: the 3.35 V storage cut-off shuts the board down before the TLV767 leaves regulation. The display therefore no longer runs down to the Q4 3.01 V corner.
  - The firmware's 3.07 V display-off threshold is kept as a fault guard.
  - Feeding the module from SYS_LOAD instead was rejected for now. Its 4.5 V USB level is inside the module's VCC range but above the SSD1315's recommended VBAT maximum of 4.5 V if there is no internal regulator; the absolute maximum is 6 V. That cannot be decided without a sample.
- **First-article gates** (added to the Q5 review):
  - identify the module power tree;
  - measure VBAT/VDD, pump regulation, readability and current at 3.15 and 3.26 V input;
  - 200 NRST pulses with the display on: no latch-up, and the display recovers each time.

## Cell, holder and temperature

- BT1 accepts a 20 mm coin cell. **Use a LIR2032 only** (4.2 V Li-ion, 40–45 mAh). The BQ25185 is set to its existing 4.2 V/ISET values; see the Q4 power document for the current setting. Never fit a primary CR2032/ML2032.
- TH1 is on the board next to BT1, not on the cell. It follows board and ambient temperature, not cell core temperature. For a 40 mAh cell at ≤ 1C that is a reasonable proxy, but it is a qualification item.
- **Insert the cell with USB connected.** The BQ2970 family may not enable discharge on first connection until a charger is present (SLUSBU9I §8.4.1). The upstream C2 + C3 cold-insertion counterexample from Q4 remains: 198.7 µs above 0.4 V against the 125 µs minimum SCC delay. USB-first insertion loads only C3: 35.8 µs. The latch helps because U7 is off at insertion, so SYS_LOAD capacitance never loads the cell.

## Battery gauge, low warning and storage cut-off

The firmware reads SYS_LOAD/2 at PA4 with VDDA derived from factory VREFINT. The divider is downstream of U7, so it draws 12.3 µA only while on and nothing while off.

| Condition (4-sample average, on battery) | Display |
|---|---|
| ≥ 3.95 V | 4 bars |
| ≥ 3.80 / 3.70 / 3.55 V | 3 / 2 / 1 bars (30 mV hysteresis on the way down) |
| < 3.55 V | empty gauge + **LO** |
| 6 consecutive raw samples < 3.35 V | LO for 2 s, count saved, power-off |

- The worst-case estimate error is 2.062 % (the Q4 VREFINT budget plus the 0.1 % divider). The 3.35 V cut-off therefore acts somewhere between 3.28 and 3.42 V. PA4 leakage into the 75 kΩ source adds ≤ 3.75 mV.
- The 3.35 V cut-off keeps the TLV767 out of dropout and the display off a collapsing rail. From cut-off, a few percent of capacity remains before the BQ25185 disconnects the battery from SYS at its ~3.0 V battery UVLO. That happens before the BQ29700's 2.8 V disconnect, so the time to disconnect at the 8 µA off current is shorter than the earlier 9.5-day figure. After a protector disconnect, the cell recovers by charging from USB.
- **USB detection** does not depend on the ADC alone. The BQ25185 regulates SYS to 4.5 V ±2 % with USB. A full cell (≤ 4.221 V) reads at most 4.308 V, and USB SYS reads at least 4.319 V. So ≥ 4.313 V means USB, and STAT1 or STAT2 low independently proves USB. With USB: no LO and no cut-off; CHG while charging; a full gauge when done or disabled (including the temperature window); BAT on a charger fault.

## Battery life (emulated firmware + datasheet currents)

From `simulation/q5-firmware-emulation/results/energy-model.json`, for 40 mAh minimum / 45 mAh nominal capacity at 90 % usable:

| Use | mAh/day | Days |
|---|---:|---:|
| On a shelf (off) | 0.194 | 150 – 169 |
| Light: 10 sessions × 10 presses | 0.398 | 81 – 91 |
| Moderate: 30 × 10 | 0.805 | 42 – 48 |
| Heavy: 20 × 30 + 1 h continuous | 2.479 | 14 – 16 |

Q4 with the same pack model lasted 2–3 weeks regardless of use. Self-discharge (~3 %/month) is included in the shelf figure. **Storage advice:** charge to about 50–60 %, and top up every three months.

## Physical gates specific to Q5 power

1. Latch timing with a real bouncing MX contact at the minimum press. Measure how short a tap turns the board on. The 2N7002 threshold spread at the COUNT_N mirror.
2. Rail behaviour on PB2 release: that U7 falls cleanly without MCU brown-out chatter, and that USB unplug during Stop turns the board off.
3. ADC accuracy through the 75 kΩ source and 100 nF C37 at the firmware's sampling time. Gauge thresholds against a real LIR2032 discharge curve under display load.
4. STAT1/STAT2 timing and levels across charge, done, temperature-hold and fault.
5. Holder contact resistance and retention, cell insertion with USB present, and the NTC's thermal coupling to the cell.
6. Off current (expected ~8 µA) and the protector's recovery after deep discharge.
