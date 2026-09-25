# Count Fidget

A lightweight, rechargeable two-key fidget that counts clicks, resets with a second key, and remembers its count while asleep or unpowered. Designed for a home-printed enclosure and professionally assembled electronics.

**Q4 is the active engineering candidate:** STM32L072CBT6 with USB-C home programming, a complete SPI OLED module, external SPI FRAM count storage, and a two-layer PCB. JLC performs bottom-side SMT; home completion adds the display/header and two through-hole keys. Q1/Q2/Q3 remain historical, unchanged packages.

**No new quote submission, purchase or manufacture is authorized.** The coordinated engineering files and independent review are complete; physical power, battery/harness, USB and enclosure qualification remain open.

Start with [the Q4 engineering review](docs/REVIEW-Q4-2026-09-24.md), [Q4 implementation and rationale](docs/Q4-implementation.md), [PROJECT.md](PROJECT.md) for status, and [HANDOFF.md](HANDOFF.md) for continuation.

| Area | Current Q4 files |
|---|---|
| PCB | [KiCad project](electronics/q4/click-counter-Q4.kicad_pro), [board](electronics/q4/click-counter-Q4.kicad_pcb), [schematic PDF](electronics/q4/schematic-Q4.pdf), [power design](docs/q4-power-design.md) |
| Firmware and programming | [Q4 source/build](firmware/q4-stm32/README.md), [USB and retention procedure](docs/q4-firmware.md) |
| Inventory and assembly | [Stock evidence](procurement/q4/inventory.md), [local footprint review](docs/review-native-footprints-Q4.md) |
| Enclosure | [Assembly and parts](mechanical/q4/README.md), [rendering](mechanical/q4/assembled-Q4.png), [STEP assembly](mechanical/q4/enclosure-Q4.step) |
| Verification | [Build workflow](docs/build-and-verify.md), Q4 reports in `verification/`, [conditional power model](simulation/q4-power/result.json) |
| Product history | [Specification](docs/product-spec.md), [user context](docs/user-research.md), [decisions](docs/decisions.md), [Q3 review](docs/REVIEW-Q3-2026-09-22.md) |
| Vendor history | [Vendor status](procurement/vendor-status.md); retained RFQ packages in `dist/` do not authorize new submissions |

Quick checks, with Python 3 and a C compiler:

```sh
python3 scripts/verify_project.py
python3 scripts/run_host_tests.py
```

These verify files, package consistency and portable firmware logic, not physical electronics. Toolchains, credentials, private mailbox content and customer account sessions are not stored in this public repository.
