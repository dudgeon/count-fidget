# Research source index

Primary references carried from the original research. These links document the selected parts and reasoning; they were not all re-fetched during repository migration. Verify current revision/stock directly before substitutions or release. Downloaded PDFs/toolchains from the old scratch environment are not included; editable project outputs and explicit engineering findings are.

| Source | What it supports / review needed |
|---|---|
| [DE188 Rev4 specification](https://display-elektronik.de/filter/DE188-RU-30_75_3V.pdf) | 3 V display, pin matrix, dimensions, soldering limit and 440 ms combined response |
| [Display Elektronik catalog](https://display-elektronik.de/wp-content/uploads/2021/05/company-profile.pdf) | Display family/context; exact drawing takes precedence over generic notes |
| [MSP430FR4133 datasheet](https://www.ti.com/lit/ds/symlink/msp430fr4133.pdf) | Selected package/pins, power and memory; review against IG48R |
| [MSP430 family/LCD_E guide](https://www.ti.com/lit/ug/slau445i/slau445i.pdf) | LCD bias/mux, FRAM and MCU behavior |
| [BQ25185 datasheet](https://www.ti.com/lit/ds/symlink/bq25185.pdf) | Power path, charge target/current/input limit, TS and termination |
| [BQ25185 EVM guide](https://www.ti.com/lit/ug/sluucs1/sluucs1.pdf) | Low-current ISET → resistor → capacitor → GND compensation topology |
| [TPS7A02 datasheet](https://www.ti.com/lit/ds/symlink/tps7a02.pdf) | 3 V regulator and effective capacitance requirements |
| [BQ2970 family datasheet](https://www.ti.com/lit/ds/symlink/bq2970.pdf) | Protector thresholds/tolerances; unresolved cell-endpoint issue |
| [TLV7042 datasheet](https://www.ti.com/lit/ds/symlink/tlv7042.pdf) | Hardware temperature-window comparator |
| [USBLC6-2 datasheet](https://www.st.com/resource/en/datasheet/usblc6-2.pdf) | USB/CC ESD protection |
| [GCT USB4105 drawing/product](https://gct.co/connector/usb4105) | Exact GF-A/standard-stake connector geometry |
| [EEMB LIR2032 manufacturer](https://www.eemb.com/product-9) | 45 mAh rechargeable cell limits; current pack/cell approval required |
| [Adafruit 4997](https://www.adafruit.com/product/4997) | Keycap source is a pack; quote two caps per unit and leftovers |
| [TI MSP430 GCC](https://www.ti.com/tool/download/MSP430-GCC-OPENSOURCE) | Original compiler 9.3.1.11 and support files 1.212 |
| [JLCPCB quote website](https://cart.jlcpcb.com/quote) | Actual quote workflow, not an authoritative complete price until reviewed |
| [PCBWay assembly quote website](https://www.pcbway.com/quotesmt.aspx) | Existing-account RFQ route |

Full manufacturer part numbers for resistors, capacitors, FETs, switches, connectors and thermistor are in `procurement/BOM-Q1.csv` and the CC-BAT-001 RFQ section. Obtain current manufacturer drawings/lifecycle data for each before release; do not assume a distributor match proves geometry or cell compatibility. Vendor conversation findings and their dates are in `procurement/vendor-status.md`.
