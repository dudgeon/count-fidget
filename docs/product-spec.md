# Product specification — Q1 baseline

Engineering prototype for quotation, not manufacturing release. Provenance is in `user-research.md`; changes are in `decisions.md`.

## Product outcome

A compact, lightweight two-key fidget for children that records clicks visibly. Deliver professionally assembled/programmed electronics, prepared rechargeable battery harness and removable caps, plus home-printable enclosure CAD. Geoff prints/fits the shell, mates the keyed battery plug and fits caps. All electrical soldering, pack preparation and initial programming belong in vendor scope.

## Functional behavior

| ID | Requirement / implementation choice | Verification |
|---|---|---|
| F1 | Increment once per accepted press | 8 ms stable debounce; RFQ specifies 20 ordinary and 150 fast pulses; host tested, hardware pending |
| F2 | Separate reset to zero | Single press implemented; priority over simultaneous qualified count |
| F3 | No hold auto-repeat | Release before next press; host tested |
| F4 | Visible numeric count | Current 8-digit DE188, 0–99,999,999; no silent rollover |
| F5 | Automatic inactivity behavior | LCD blank after 30 seconds, MCU wakeable LPM4; functional auto-off, not physical disconnection |
| F6 | First count after sleep increments | Wake from 123 should show 124; release must not add another |
| F7 | Retention without battery | Dual-record CRC FRAM journal; a cut during unfinished update may lose newest click, with previous committed record as recovery target |
| F8 | USB-C recharge and operation | Charge-only, both cable orientations; intended to run while charging |
| F9 | Saturation feedback | Saturation implemented; core overflow flag exists, but earlier visible-overflow proposal is not rendered in target code |

The DE188's 440 ms combined optical response is unqualified. Correct rapid click capture does not prove crisp visible transitions for each click.

## Physical/electrical baseline

| Item | Choice |
|---|---|
| PCB | 42 × 40 × 1.0 mm, four layers, 2 mm outline corner radius |
| Keys | Two Cherry MX1A-E1NW PCB-mount clicky Blue; 19.05 mm stem spacing |
| Caps | Two loose MX DSA caps; Adafruit 4997 pack source, quote actual quantity/MOQ |
| Display | DE188-RU-30/7,5/V (3 V), 8 digits, 34.9 × 13 mm glass, 20 leads; rear glass 4 mm above PCB |
| MCU | MSP430FR4133IG48R, 48-pin TSSOP, integrated LCD controller/FRAM |
| Battery | Genuine EEMB LIR2032 rechargeable Li-ion 45 mAh; custom CC-BAT-001 four-wire NTC pack |
| USB | GCT USB4105-GF-A, charge-only 5 V, separate CC1/CC2 resistors |
| Charger / regulator | BQ25185: 4.2 V, nominal 18.2 mA charge, 100 mA input limit; TPS7A02 fixed 3.0 V |
| Protection | BQ29700 plus opposing FETs; raw cell negative isolated through protection |
| Thermal inhibit | USB-powered TLV7042/NTC window near 8–36°C nominal; tolerance/contact tests pending |
| Programming | Spy-Bi-Wire via bottom pogo lands; not USB |
| Enclosure | Screw-secured battery access; printed plate supports click loads; editable CAD and final STLs required |

Mass target is provisionally 25–30 g, unmeasured. Old shell solids calculate to 9.901 g in solid PLA at 1.24 g/cm³. Fit-study envelope is 46 × 44 × 18 mm including bezel, 28.8 mm maximum keycap height. These are not final Q1 enclosure dimensions or user-specified limits.

The earlier LCD budget used ≤10 µA sleep and 50–250 µA active at 10 minutes/day. A 45 mAh cell derated to 70% led to a rough 2–4 month charging-interval target after allowances. This is not measured runtime. Active/sleep leakage, self-discharge and usable capacity remain to be checked.

## Assembly and release

Use the approved rechargeable chemistry, never a primary CR2032. Vendor prepares insulated welded tabs and cell-contact NTC; no direct iron soldering to a bare cell. Provide strain relief, clearance from solder tails/components, screw-retained battery access and mechanically supported LCD/USB/switches. Do not use unqualified battery electronics with children.

BQ29700 undervoltage tolerance may fall below EEMB's 2.75 V endpoint. Resolve with cell-maker approval or redesign. Verify CC/CV/termination, low-current stability, thermal inhibit, protection trips/recovery and physical fit against approved parts. The RFQ specifies first-article and recurring tests; no hardware qualification is claimed.

## Complete-quote acceptance

Separate vendor-reviewed quotes for 5 and 10 functioning assemblies to postal code 20815, including PCB/net test, every part/MOQ leftover, both-side SMT and THT, LCD jig, switch/USB soldering, battery/NTC pack, loose caps, programming/fixture/setup, first-article engineering, recurring tests, tooling/stencil, packaging, lithium freight, duty/brokerage/tax, lead time and validity. Unsupported/pending lines remain explicit, never $0 placeholders.

JLCPCB's battery exclusion and prepayment test-pricing restriction prevent treating its supported-scope subtotal as a complete quote. No final vendor, quantity, budget ceiling, purchase or manufacturing release is approved.

## Scope boundary

Wireless, app/cloud sync, sound, RGB, USB data, keyboard/macropad mode, games and volume production were not requested. A dedicated counter IC was permitted if suitable, but no fully suitable off-the-shelf solution was established; the MCU also handles persistence, display and sleep.
