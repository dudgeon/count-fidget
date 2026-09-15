# LCD and firmware audit — Q2 verification candidate

The submitted Q1 board, BOM, HEX/ELF/map, factory initializer and RFQ archive are preserved. No target was flashed and no hardware qualification or manufacturing release occurred. Three review concerns are confirmed, with qualifications below; the alleged missing segment enable/source mismatch is **refuted by the actual TI header and exact HEX reproduction**.

## 1. Mode-2 bias reservoirs are missing — confirmed hardware blocker

`electronics/build_pcb.py:79`, `electronics/netlist.json` and native Q1 PCB U1 pads 7/8/9 omit nets for R13/R23/R33. The only LCD capacitor is C8, 100 nF between pins 10/11 (LCDCAP1/0), generated at `build_pcb.py:117`. These three unconnected pads are independently visible in `click-counter-Q1.kicad_pcb` at lines 457/464/471.

For this 48-pin DGG device, pins 7/8/9 are R13/R23/R33. Mode 2 requires capacitors from all three bias nodes to ground in addition to the pump capacitor; internal VDD selection does not remove the R33 capacitor. See [TI family guide, Figure 17-9, printed p457](https://www.ti.com/lit/ug/slau445i/slau445i.pdf). The [device datasheet, §8.12.8.1, p35](https://www.ti.com/lit/ds/symlink/msp430fr4133.pdf) specifies nominal 0.1 µF for each reservoir and the pump. Consequently the existing 0.1 µF pump is consistent with the device specification; a reference board using 1 µF does not by itself establish a mandatory change.

Required controlled hardware correction: add three capacitor nets/parts at R13/R23/R33, reconcile native schematic/netlist/generator/layout/BOM, reroute and re-export under a new revision, then measure LCD bias/DC and optical behavior. This audit does not modify the board or approve cap placement/DFM.

## 2. Missing LCDSON/source-to-image mismatch — refuted

Q1 `main_msp430.c:58` uses `LCDSSEL__ACLK|LCDDIV__4|LCD4MUX|LCDON`. In the exact **TI support 1.212** `include/msp430fr4133.h:1089`, `LCD4MUX` is defined as `(LCDMX1+LCDMX0+LCDSON)`. `LCDSON` is 0x0004. The expression therefore evaluates to **0x185d**, matching the archived instruction at **0xc53a**: bytes `b2 40 5d 18 00 06`, `MOV #0x185d,&0x0600`. Both source and archived image set `LCDVCTL=0xf0a0` at 0xc534.

The review's 0x1859 calculation omitted the segment bit embedded in `LCD4MUX`. The initial manual audit repeated that mistake; exact preprocessing/compilation corrected it. Adding explicit `|LCDSON` alone changes no application byte. Segment enable is not an outstanding defect. Firmware still cannot compensate for the missing bias hardware.

### Independent Q1 reproduction

Read-only copies of all five target C/header files were built in a temporary directory with the official macOS TI GCC **9.3.1.11**, support **1.212**. The unmodified source and an explicit-SON-only copy each reproduced the archived **entire Intel HEX file byte-for-byte**:

| Evidence | SHA-256 / result |
|---|---|
| Original Q1 `main_msp430.c` | `40b1529be1c165102e68546ad00af45330aa28dffeff1426075bf49e2df4ea06` |
| Archived and both rebuilt Q1 application HEXs | `98e775d027c6de064d5f0e2c25695ad2b998d30e9aae37ea2704a56c85b46b18` |
| Archived ELF | `f0b097a8ada422daa1f2760f866c7d3d97dbafa786782e333109e910620a819a` |
| Rebuilt unmodified-source ELF | `80067a300d841921ce0392f442d5511d17602dc5827ac5c7c0f145767ef1ca41` |
| Loaded bytes / size | 2,336 identical address/value bytes; 2,238 text, 98 data, 68 BSS |

The original shell history is unavailable; this is a verified reconstruction of the recipe, not a recovered historical command. Run from a directory containing copies of the five Q1 C/header files, with `TI_BIN` and `TI_SUPPORT_INCLUDE` set to installation paths:

```sh
"$TI_BIN/msp430-elf-gcc" -mmcu=msp430fr4133 -I"$TI_SUPPORT_INCLUDE" -L"$TI_SUPPORT_INCLUDE" -std=c11 -Os -Wall -Wextra -Werror -ffunction-sections -fdata-sections main_msp430.c counter.c lcd_de188.c -Wl,--gc-sections,-Map,image.map -o image.elf
"$TI_BIN/msp430-elf-objcopy" -O ihex image.elf image.hex
"$TI_BIN/msp430-elf-objdump" -d --disassemble=lcd_start image.elf
```

Full ELF files are not byte-identical, but all allocated initialized sections and generated HEX bytes match. No other loaded-byte source/binary drift was found. Prior hash/host checks alone did not establish that; the new build manifest now also binds sources to outputs.

## 3. Divide-by-4 timing lacks tolerance margin — corrected in candidate

Q1 calculation: 32768 / 4 / 16 / (2 × 4) = **64 Hz** frame rate (512 Hz LCD clock). TI specifies REFO ±3.5% and recommended frame frequency 16/32/64 Hz minimum/typical/maximum; Q1 therefore spans **61.76–66.24 Hz**. See [TI device datasheet, §8.12.3.3 p24 and §8.12.8.1 p35](https://www.ti.com/lit/ds/symlink/msp430fr4133.pdf).

Q2 uses divide-by-8: **32 Hz nominal, 30.88–33.12 Hz** at that tolerance. The [DE188 Rev4 electrical table, printed p4](https://display-elektronik.de/filter/DE188-RU-30_75_3V.pdf) gives 30/32/100 Hz minimum/typical/maximum, so this calculated range fits both stated recommendations. Actual waveform, contrast, response and temperature qualification remain necessary.

The [TI guide Table 17-3, p451](https://www.ti.com/lit/ug/slau445i/slau445i.pdf) labels dividers “4 to 16” and warns about `LCDDIVx <4`; its register description uses raw field +1. The table's numerical examples use actual divisor 4. This notation is ambiguous, so do not claim the footnote alone unambiguously prohibits divide-by-4. The tolerance calculation independently justifies divide-by-8.

## 4. DE188 nominal row pitch is wrong — confirmed; fit failure not proven

Generator line 68 and the local footprint put rows at ±6.75 mm (**13.5 mm**); RFQ line 41 repeats that spacing. The [specific DE188 Rev4 mechanical drawing, printed p3](https://display-elektronik.de/filter/DE188-RU-30_75_3V.pdf) dimensions the outer lead span as 13.3 ±0.5 mm and lead thickness as 0.3 mm. The inferred nominal center spacing is **13.0 mm**, requiring nominal ±6.5 mm rows after manufacturer/sample confirmation.

The current 1.7 mm holes do not prove unavoidable preload: a nominal 1.1 ×0.3 mm rectangular lead offset 0.25 mm has a far-corner radius about 0.68 mm, inside the 0.85 mm hole radius. Full positional/lead/hole tolerances still need review. Do not simply shrink drills to 1.2 mm: a maximum-width 1.2 ×0.3 mm lead has a 1.237 mm diagonal before any clearance. Final drill/slot and standoff require the specific lead drawing, tolerance stack, assembler input and sample fit. Generic application-note hole guidance is insufficient for these flat leads.

## Candidate outputs and release limits

`firmware/main_msp430.c` now identifies Q2 and uses `/8`; explicit `LCDSON` is readability only. `scripts/build_firmware.py` creates separate `firmware/q2-lcd-check/` ELF/HEX/map/disassembly and `build-manifest.json`. Validation binds the frozen Q1 application HEX to SHA-256 `98e775d027c6de064d5f0e2c25695ad2b998d30e9aae37ea2704a56c85b46b18` and requires identical loaded addresses with exactly one changed byte: `0xc53d`, `0x18` to `0x38`. It also checks the compiled `LCDCTL0=0x385d` and mode-2 `LCDVCTL=0xf0a0` instructions, ELF/HEX load-byte equality and exclusion of information FRAM 0x1800–0x19ff. ELF initialized sections are mapped through their PT_LOAD physical addresses, including sections whose RAM runtime address differs from their load address. The manifest records this validation and source/header/build/toolchain provenance.

This is deliberately an exact candidate check, not a general firmware verifier. Instruction-pattern presence alone would accept a later overriding register write; the enforced complete-image difference rejects that case. An isolated negative test adding `LCDCTL0=0` after the expected write is rejected. An isolated build containing initialized RAM data verifies the load-address mapping but is correctly rejected as outside the approved one-byte candidate. A changed frozen-Q1 HEX is also rejected. Local repeat builds reproduce the Q2 outputs and manifest; portable host tests pass. Cross-host or different-toolchain byte reproducibility is not established by these local results.

`scripts/verify_project.py` preserves every Q1 archive member hash and allows only the named Q2 main-source divergence with both historical and newly compiled hashes. All Q1 manufacturing and firmware outputs remain unchanged. These checks establish current artifact integrity and the exact reviewed image change, not physical electrical behavior. LCD hardware correction, schematic/ERC, charger/thermal/protection, footprint fit, power/current, FRAM brownout and first-article release gates remain open.
