# Count Fidget

A lightweight, rechargeable two-key fidget that counts clicks, resets with a second key, and remembers its count while asleep or unpowered. Designed for a home-printed enclosure and professionally assembled electronics.

**Q5 is the active engineering candidate:** the Q4 STM32L072CBT6 / USB-C home programming / SPI OLED / SPI FRAM design, plus:
- a soft power key (COUNT turns it on; it switches itself off after 30 s, drawing ~8 µA);
- a vendor-soldered LIR2032 coin-cell holder in place of a custom battery pack;
- a battery gauge with LO warning and storage cut-off, and charge status;
- a reset pinhole;
- hold-to-reset key logic;
- a smaller 47.2 × 59.2 × 16.2 mm printed enclosure with printed keycaps.

JLC performs all SMT from standard inventory parts; home completion is 18 through-hole joints (display header and two keys). Q1–Q4 remain historical, unchanged packages.

**No quote submission, purchase or manufacture is authorized.** The design files, firmware, emulation and CAD checks pass; nothing has been built or measured.

Start with [the Q5 engineering review](docs/REVIEW-Q5-2026-09-25.md), [PROJECT.md](PROJECT.md) for status, and [HANDOFF.md](HANDOFF.md) for continuation.

| Area | Current Q5 files |
|---|---|
| PCB | [KiCad project](electronics/q5/click-counter-Q5.kicad_pro), [board](electronics/q5/click-counter-Q5.kicad_pcb), [schematic PDF](electronics/q5/schematic-Q5.pdf), [power design](docs/q5-power-design.md) |
| Firmware and programming | [Q5 source/build](firmware/q5-stm32/README.md), [keys, power and USB procedure](docs/q5-firmware.md) |
| Inventory and assembly | [Stock evidence](procurement/q5/stock.json), [exports](procurement/q5/REVIEW-EXPORTS-Q5.md) |
| Enclosure | [Assembly and parts](mechanical/q5/README.md), [rendering](mechanical/q5/assembled-Q5.png), [STEP assembly](mechanical/q5/enclosure-Q5.step) |
| Verification | [Build workflow](docs/build-and-verify.md), Q5 reports in `verification/`, [firmware emulation](simulation/q5-firmware-emulation/README.md), [bounded power checks](simulation/q5-power/result.json) |
| Product history | [Specification](docs/product-spec.md), [user context](docs/user-research.md), [decisions](docs/decisions.md), [Q4 review](docs/REVIEW-Q4-2026-09-24.md), [Q4 simulation review](docs/REVIEW-Q4-simulation-2026-09-25.md) |
| Vendor history | [Vendor status](procurement/vendor-status.md); retained RFQ packages in `dist/` do not authorize new submissions |

Quick checks, with Python 3 and a C compiler:

```sh
python3 scripts/verify_project.py
python3 scripts/run_host_tests.py
```

These verify files, package consistency and portable firmware logic, not physical electronics. Toolchains, credentials, private mailbox content and customer account sessions are not stored in this public repository.
