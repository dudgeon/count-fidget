# Independent review and controlled Q2 work

Reviewed 15 September 2026 following Geoff's supplied adversarial review. **Q1 is on engineering hold.** Its submitted manufacturing files and firmware are preserved as historical evidence. The separate Q2 LCD firmware candidate corrects timing; it does not fix or qualify the board.

## Findings and dispositions

| Review claim | Independent result | Disposition |
|---|---|---|
| Missing LCD bias reservoirs on U1 pins 7/8/9 | **Confirmed.** TI Mode 2 requires three external 100 nF capacitors to ground at R13/R23/R33. | E15: add them in a consistent schematic/layout/BOM revision if retaining this LCD drive architecture. Existing C8 at 100 nF agrees with TI's device specification; 1 µF is not established as mandatory. |
| Source omits LCDSON and differs from shipped firmware | **Refuted.** TI support 1.212 defines LCD4MUX to include LCDSON. Unmodified source reproduces the archived Q1 Intel HEX byte-for-byte. | Correct the review record. Explicit LCDSON is now written for clarity, with no behavioral change. E16's provenance improvement is implemented by the new build manifest. |
| 64 Hz frame timing has insufficient margin | **Confirmed.** REFO tolerance gives 61.76–66.24 Hz against a 64 Hz maximum. | Separate candidate uses divider 8: 32 Hz nominal, 30.88–33.12 Hz. E17 remains a physical qualification item. |
| DE188 row centers should be 13.0 mm, not 13.5 mm | **Confirmed nominal drawing discrepancy.** Actual forced preload is not proved with the existing 1.7 mm holes. | E11: resolve lead/position/drill tolerances and sample fit. Do not automatically shrink holes to 1.2 mm; the maximum rectangular lead diagonal already exceeds that. |
| BQ25185 resistor/pin settings may be wrong | **Refuted.** Pin 7 is combined ILIM/VSET; 24 kΩ selects 4.2 V and the 100 mA input-limit option. Pin 8 with 16.5 kΩ selects about 18.18 mA charge current. Pins 3/9 are optional status outputs. | No demonstrated wiring correction. Existing low-current charge, thermal, cell and protection qualification gates remain. |

Detailed primary-source evidence and calculations: [LCD and firmware](review-lcd-firmware-Q2.md), [charger](review-charger-Q2.md), [protection, thermal and regulator](review-protection-Q2.md), and [enclosure](review-mechanical-Q2.md).

### Correction to our initial assessment

The initial manual check incorrectly repeated the source/binary allegation. An exact TI compilation disproved it. Both vendors received an explicit correction after the initial hold notice: PCBWay at **02:17:56 UTC**, JLCPCB at approximately **02:17 UTC**. This correction does not clear the independently confirmed hardware and timing concerns. Complete ELF files differ in metadata, while every allocated initialized byte and the entire generated Q1 HEX match. Do not describe the old firmware as compiled from different source.

## Additional power findings

- **E18, inferred fault mechanism:** if the TLV7042 loses its supply connection while its output pull-up remains powered, its high-impedance outputs can let Q3 enable charging. The fixed charger TS resistor still reports normal temperature. Review a charge-disabled response to monitor power loss and validate startup, sensor faults and recovery. This is an inference from documented component behavior, not a demonstrated board failure.
- **E03, quantified NTC self-heating:** at 5 V and 25°C the sensor receives 0.250 mA and dissipates 0.625 mW. That exceeds Murata's 0.1°C self-heating measurement condition; it is not a destructive-current limit. Actual insulated cell-pack temperature error remains unmeasured.
- **E01, corrected tolerance evidence:** TI specifies protector UV tolerance of ±50 mV at 25°C. The old blanket ±0.1 V assertion was unsupported by the retrieved revision. Cell endpoint compatibility across temperature and recovery charging remain unresolved.
- No new protection-FET orientation, comparator polarity or regulator pin-assignment defect was found. Effective ceramic output capacitance, transient behavior and the stocked regulator's active-output-discharge feature still need review. Agreement among source, JSON and board pad labels does not prove copper connectivity or replace ERC/DRC and measurements.

## Enclosure findings

The existing Rev0 fit study has concrete Q1 mismatches: rear screw centers are displaced 1.118 mm radially; the two front screws have no Q1 holes; the LCD pocket is displaced 1.25 mm and the USB opening 2.1 mm; the 20.9 mm battery bore is smaller than the permitted 21.0 mm insulated pack. Its generic MCU is modeled on the wrong board side, and many actual components, leads and tolerances are absent. These source-coordinate comparisons strengthen E08; they are not fresh solid-intersection or sample-fit tests. Existing STEP/STLs remain obsolete.

## Work implemented and checked

On `codex/q2-engineering-audit`, `firmware/main_msp430.c` uses divider 8 and makes LCDSON explicit. New `scripts/build_firmware.py` produces separate `firmware/q2-lcd-check/` outputs. The manifest records source/header/build-script hashes, exact compiler/support provenance, command flags, dependencies and output hashes.

The candidate differs from Q1 in exactly **one loaded byte**, the LCD divider at 0xc53d. Compiled register writes, ELF/HEX equality and exclusion of information FRAM 0x1800–0x19ff are checked. Repeated builds reproduce all candidate files, and portable host tests pass. Verification continues to check frozen Q1 archive/member hashes; only the explicitly identified, manifest-bound main-source divergence is permitted.

No PCB, BOM, placements, Gerbers, Q1 HEX/ELF/map, factory initializer or RFQ archive was changed. No target was flashed, fresh DRC/ERC run or physical test performed.

## Display and quotation consequences

The user's original display choice was arbitrary. Eight digits, 35 × 13 mm and the months-of-use target are design assumptions rather than fixed user requirements. [Display sourcing research](display-options-Q2.md) has not established a qualified replacement. The available OLED example's 23–29 mA specification could approach the current protection trip near 30 mA; its module-level 3 V operation and application consumption are also unverified. A stocked part alone is insufficient to select it.

A broader search found the four-digit reflective Lumex LCD-S401M16KR as a smaller, credible low-power redesign lead with external distributor stock. JLCPCB stock is still unverified and LCSC reports zero, so it does not establish an easier two-vendor path. Choosing four digits would also require an explicit count-presentation decision. No display has been selected or removed from the existing scope.

JLCPCB says no alternative to the requested LCD is stocked and suggests paid Global Sourcing preorder for DE188. That does not establish an exhaustive catalog search or authorize a purchase. Its battery-assembly exclusion and test-pricing restriction also remain, so replacing the display alone does not produce the requested complete delivered quote.

Both vendors retain existing Q1 references for sourcing and budgetary discussion. PCBWay has the submitted five-unit PCB/assembly pair **W914112AS1N4 / T-1N5W914112A**. JLCPCB has the saved import draft but no formal order/quote number. Neither has supplied complete reviewed 5/10-unit prices. See [vendor ledger](../procurement/vendor-status.md).

## Next controlled engineering sequence

1. Select a sourceable low-power display using exact electrical/mechanical data and assembler confirmation. Resolve U3's valid ordering variant and power consequences in the same revision.
2. Create and review a native schematic, including the confirmed LCD correction where applicable and the power/thermal fault cases. Reconcile netlist, footprints, component values, routing and assembly files. Keep Q1 frozen.
3. Complete fresh ERC/DRC, assembly review and a revised enclosure fit study for the selected hardware. Existing mechanical exports are obsolete study files.
4. Reissue one identified package to the existing vendor cases for itemized 5/10 quotes and a priced first-article/qualification plan. Preserve every unresolved gate in [open issues](open-issues.md).
5. Present a concrete order before any chargeable procurement or manufacturing release. No money or manufacture is authorized by this review.
