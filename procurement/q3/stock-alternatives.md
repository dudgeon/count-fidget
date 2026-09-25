# Q3 stock alternatives — engineering and catalog check

Research date: 15 September 2026. This is a candidate selection note, not a
purchase, stock reservation, physical qualification or authorization to omit
required parts. Q1/Q2 remain frozen. Live JLC orderable quantities must control
over search-engine snapshots or LCSC inventory.

## U5 comparator

Select **TI TLV7012DGKR / C2859969**: the root agent verified native JLC
stock22, available21, MOQ1 and SMT support on the research date. Final five/ten
quote allocation plus assembly allowance remains to complete. It preserves the DGK land pattern
and the separate push-pull outputs. TI's current ordering list does not list a
TLV7032DGKT small-reel option; do not create that MPN by changing a suffix.
Sources: [JLC exact TLV7012DGKR](https://jlcpcb.com/partdetail/TexasInstruments-TLV7012DGKR/C2859969),
[TI TLV7032 ordering addendum](https://www.ti.com/lit/ds/symlink/tlv7032.pdf).

The [TI TLV7012 datasheet](https://www.ti.com/lit/ds/symlink/tlv7012.pdf),
sections 5, 6.10 and 7.4, verifies:

- Pins 1/2/3/4/5/6/7/8 are OUTA/INA−/INA+/VEE/INB+/INB−/OUTB/VCC.
- Dual-device supply range is 1.6–6.5 V. Push-pull POR holds outputs low during
  supply ramps; inputs remain high impedance when unpowered with inputs up to
  5.5 V. Preserve both 100 kΩ gate pulldowns and the series CE switches.
- Offset is ±8 mV maximum; hysteresis is 2/7.2/15 mV minimum/typical/maximum at
  the table's stated conditions. Its typical 4.7 µA/channel consumption is
  higher than TLV7032's, but this circuit is powered from USB VBUS.

The existing conditional ±21.5 mV thermal error allowance is wider than the
TLV7012 offset plus half its maximum hysteresis plus the existing 1 mV
allowance. This supports retaining the conservative thermal candidate; actual
common-mode, supply, temperature, NTC attachment and fault tests remain release
gates. It does not turn typical specifications into guaranteed limits.

| Exact candidate | Package/change | Inventory evidence and action |
| --- | --- | --- |
| TI TLV7012DGKR / C2859969 | Same VSSOP DGK-8; selected | Root native JLC check:22 stock/21 available/MOQ1, SMT supported. This supersedes the obsolete zero-stock search snapshot. |
| TI TLV7012DDFR / C2871502 | Same electrical function/pin numbering, different TSOT-23-8 land pattern | [JLC page](https://jlcpcb.com/partdetail/TexasInstruments-TLV7012DDFR/C2871502) exposes positive historical quantities, but inconsistent crawl dates/counts; obtain live quantity before selecting. Requires a new manufacturer-derived footprint and fresh layout checks. |
| TI TLV7032DDFR / C2871498 | Original electrical part in different package | [JLC snapshot](https://jlcpcb.com/partdetail/TexasInstruments-TLV7032DDFR/C2871498) showed zero; no current positive quantity established. |

Do not substitute the open-drain TLV7022/TLV7042 or higher-power TLV3202 based
on package alone: their supply/output/power-loss behavior requires its own
review. No comparator BOM substitution is recorded by this document alone.

## SW1/SW2 clicky soldered keys

**HanElectricity CPG151101D13 / C49234235** is the actionable stocked candidate:
the [official JLC category, crawled on the research date](https://jlcpcb.com/parts/2nd/Switches/Mechanical_Keyboard_Shaft_2212)
reports 14,506 pieces, while the exact part page lists wave soldering. The
subsequent root native check verified14,501 stock/14,160 available/MOQ1 and
$0.1070 at one piece, with wave-solder support. Final quote allocation and
allowance remain to complete. This manufacturer is **HanElectricity, not Kailh**.

The [manufacturer-authored HanElectricity specification](https://atta.szlcsc.com/upload/public/pdf/source/20250618/D1C12809F8EDF275373534C56A4C291D.pdf)
identifies a click-tactile SPST switch, MX cross stem, 50 ±10 gf operating force,
4 mm travel and no fixation feet. Its terminal layout uses the conventional
MX geometry; the drawing recommends a 3.90 +0.10/−0 mm central hole,
1.50 ±0.05 mm terminal holes and a 14 mm square plate opening. Its minimum
contact rating is 10 µA. Match the actual Q3 footprint and plate retention to
this exact drawing; do not retain a Cherry/Kailh identity on the selected part.
The text and drawing disagree on the low operating-temperature endpoint;
retain the narrower −10°C bound pending clarification.

**Kailh CPG151101D91 / C400239** remains a genuine alternative if restocked.
The [Kailh manufacturer page](https://www.kailhswitch.com/mechanical-keyboard-switches/rgb-key-switches/rgb-keyboard-blue-switches.html)
identifies it as a clicky DIP switch, plate mounted and compatible with
traditional mechanical-switch caps. It specifies 50 ±10 gf actuation and
approximately 4 mm travel. It is a physical electrical contact, not a magnetic
or optical switch. Its plate retention must be checked in the revised enclosure.

| Exact candidate | Evidence | Qualification/stock status |
| --- | --- | --- |
| Kailh CPG151101D91 / C400239 | [JLC exact part](https://jlcpcb.com/partdetail/Kailh-CPG151101D91/C400239), manufacturer clicky/DIP description above | JLC supports wave soldering, but its category crawled on the research date reports zero. Do not select on catalog presence alone. |
| Kailh CPG151101S13 / C404353 | [JLC exact part](https://jlcpcb.com/partdetail/Kailh-CPG151101S13/C404353) lists wave soldering; [Kailh-authored specification KH-PS1607-37 Rev A](https://atta.szlcsc.com/upload/public/pdf/source/20190830/C404353_03D773C25064FB6981E6251E455188E4.pdf) | Genuine Kailh blue switch with through-hole process/dimensions documented. Public JLC page has not established current inventory. |
| HanElectricity CPG151101D13 / C49234235 | [JLC exact part](https://jlcpcb.com/partdetail/HanElectricity-CPG151101D13/C49234235), manufacturer drawing above | Root native check:14,501 stock/14,160 available/MOQ1, wave soldering. Selected exact identity. **Not Kailh.** |

The S13 drawing (printed page 10, PDF page 12) shows a conventional 1.27 mm
grid, approximately 3.99 mm central hole, 1.50 mm terminal holes and 14.00 mm
plate opening. It depicts options with and without fixation pins. Use the exact
selected part drawing to confirm which option is supplied; the family drawing
alone does not prove locator-pin presence. Existing holes/plate geometry are
not automatically qualified. Its specification gives up to 10 ms bounce after
life testing and a 10 µA minimum contact rating; retain debounce and verify
actual button pull-up current, keycap fit and solder process.

**Required Q3 interface change for these switch candidates:** existing R17/R18
are 470 kΩ and firmware disables the MCU internal pull-ups. A 3 V rail therefore
supplies only about 6.4 µA through a held switch, below all three candidates'
10 µA minimum rating. Use 220 kΩ, 1% pull-ups for margin (about 13.4 µA at
2.97 V/222.2 kΩ); this keeps the same 0603 pads and reduces the 1 nF RC time
constant from 0.47 to 0.22 ms. Keep software debounce and verify actual lifetime
contact behavior. No resistor/model edit was made by this research note.

Exact pull-up candidate: **UNI-ROYAL 0603WAF2203T5E / C22961**, 220kΩ,
1%, 100mW, ±100ppm/°C, Basic0603SMT in the
[official JLC catalog](https://jlcpcb.com/partdetail/0603WAF2203T5E/C22961).
Root owns live inventory verification and model selection.

The new exact local land pattern is
`electronics/q3/CountFidgetQ3.pretty/HanElectricity_CPG151101D13_MX_Plate.kicad_mod`.
It preserves the old pin1 origin and recommended terminal grid; removes the two
unsupported fixation holes; uses a3.95mm central hole; and replaces the old
undersized13.2mm courtyard with a15.7×16.2mm courtyard around the actual body.
The manufacturer requires finished center-hole3.90–4.00mm and terminal
holes1.50±0.05mm; quote these tolerances explicitly. Native KiCad10.0.6 loaded
the footprint with two electrical pads and one NPTH. A Cherry STEP model was
not attached to this different manufacturer's footprint.

Cherry's manufacturer-authored [11 February 2026 EOL notice](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/8884/MX1A-E1NW_EOL_2-11-2026.pdf)
says MX1A-E1NW is no longer available for order and identifies MX2A-E1NW as its
form/fit/function successor. No current JLC listing/allocation for that exact
successor was established here. An out-of-stock MX1A-E1NW or unrelated
E-Switch C5798268 is not a supported substitute.

## Completion condition

Record the live vendor quantity, exact manufacturer/MPN match and assembly
method before changing Q3 BOM/model. Then recheck the revised package,
electrical/netlist parity, physical lands/retention and quote all required
parts. Catalog support and a successful BOM match still do not qualify the
assembled hardware or authorize manufacture.
