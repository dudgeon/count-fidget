# Q3 firmware adversarial recheck — 22 September 2026

## Conclusion

**No new firmware defect was demonstrated by this review.** The existing host regressions and a new deterministic harness linking the unchanged production counter, input queue and OLED modules pass. This is bounded software evidence, not a physical qualification or permission to manufacture. No production firmware, previous report, native board or frozen RFQ was changed.

The candidate remains MSP430FR4133IG48R firmware, not ESP32 firmware. Current source/output validation passes. The reviewed application ELF is SHA-256 `953169cd3b0b0eec37e43c150530148bdbc00dafabb90ea326252ff03af4a515`; application HEX is `b19f9e62fe9833ebb61fa75e94a7adef5664e51c7bcb7ffaa619a7c00bf910bf`. The existing build records 5,033 addressed load bytes and 546 bytes of static RAM; static RAM is not a measurement of worst-case stack use.

## Reproduce and inspect the evidence

From the repository root:

```sh
python3 -B scripts/build_firmware_q3.py --verify-only
python3 -B scripts/run_host_tests_q3.py
python3 -B scripts/test_q3_behavior_model.py --output verification/q3-behavior-model-2026-09-22.json
```

All three completed successfully. The new [result](../verification/q3-behavior-model-2026-09-22.json) records compiler identity, flags, exact harness/production/image hashes, coverage and limits. The [runner](../scripts/test_q3_behavior_model.py) builds a separate [C harness](../firmware/tests/q3_behavior_model_2026_09_22.c) with warnings treated as errors and checks that all its inputs remain unchanged. It executes production `counter.c`, `input.c` and `oled.c`, not a Python reimplementation. No MCU was connected or flashed. The target ELF was hash/load validated this session, not newly executed in an MSP430 simulator.

| New deterministic coverage | Cases | Independent expectation |
|---|---:|---|
| Qualified button waveforms | 7,350 | Analytic press/release events for seven pulse widths, relative reset phases, saturation boundaries and timestamp wrap; reset wins a simultaneous press. |
| Queue schedules and capacity | 65,665 | Every drain/no-drain schedule over 12 samples for eight input profiles and two clock bases; capacity 1–128; 64,000-sample ring-wrap exercise. Queue results equal immediate processing when history fits, and overflow freezes confidence. |
| Interrupted journal destination words | 2,359,296 | Four old/new-count scenarios × nine write positions × every 16-bit damaged word. Reboot chooses the previous committed count or the fully committed new count, including sequence wrap and blank memory. |
| Fault/reset durable write prefixes | 24 | Cuts before each possible marker/journal/clear write with either a fresh or preexisting fault. A cleared durable marker after writing starts implies a committed zero. |
| Interrupted marker clearing | 65,536 | Every damaged clear-word value; a failed write acknowledgment retains the RAM fault. Only `FFFF` means clear after reboot, at which point zero was already committed. |
| OLED fault and sleep schedules | 5,441 | START rejection or partial-packet failure, wrap, slow foreground polling, and sleep at 480 service phases with four sleep lengths. Logical power guards hold and recovery converges to clean-run RAM. |

The OLED schedule sweep includes transfer indices beyond those reached in some trials; the JSON separately records actual injected faults. Indices 1–195 must be reached and fail as requested. Faults during final shutdown are checked for safe shutdown; faults before convergence also require a fully recovered frame. The controller model checks full RAM clearing before the selected pump command, external IREF, power/reset ordering, and 105 nominal-millisecond guards. It deliberately advances the clock inside a completion callback to attack stale entry timestamps.

The existing regressions additionally cover bounce, held-key no-repeat, sleep/wake first press, 100,000 journal commits, CRC fallback, absent-display timeouts while counts continue, the previous nine-millisecond missed-reset reproduction, queue-marker write failures, and held increment throughout reset recovery.

## Source findings and remaining limits

1. **No reopened prior fix.** `main_msp430.c:119–131` captures both port edges and timer samples. Lines 158–162 dequeue with interrupts masked, while lines 178–193 check queue/gap and pending wake conditions atomically before sleep. The new harness explores foreground drain schedules; it does not execute those target registers or model electrical interrupt timing.
2. **Recovery ordering remains conservative once the fault is persisted.** `input.c:20–39` freezes uncertain increments while still tracking real held keys. `main_msp430.c:164–172` persists the gap marker, commits the journal and then permits marker clearing. `input.c:49–53` requires a committed zero and successful clear write. A held increment does not become a new press when confidence returns.
3. **There is a real persistence boundary, not a guarantee of every physical click.** A new queue gap lives in RAM until the foreground marker write (`main_msp430.c:166`); power loss before that write cannot preserve the new diagnosis. Likewise, queued or uncommitted presses can be lost on removal of power. The retained value is the last valid committed journal entry. The prefix test explicitly includes the cut before the first marker write. It does not convert that window into a successful durability claim.
4. **Display recovery does not certify the module.** `oled.c:58–63, 77–105, 161–181` uses reset and fresh completion/pin timestamps around shutdown/retry guards. The model assumes reset stops panel/pump activity. Its clean-run RAM comparison checks recovery consistency, not whether the exact X087 bonded pixels match that RAM, whether `8D 72` generates the intended rail, or whether analog discharge meets the guard under every load.
5. **Torn writes are a defined fault model.** One destination word may take any value, then execution stops; the old active record and other words remain intact. This does not prove immunity to multiple-word corruption, wrong-voltage operation, ECC behavior, or a sustained fault affecting both records.

The earlier Q1/Q2 source/binary allegation remains refuted: TI's `LCD4MUX` definition includes `LCDSON`. This review does not revive it or alter the earlier evidence.

### Physical gates still required

On an assembled Q3, measure actual ISR latency and bounce capture during render/journal traffic, stack margin, first/held wake, rail/reset/pump timing at battery extremes, absent/shorted OLED recovery, physical pixel mapping, and current. Interrupt power during real journal and marker writes and inspect recovery. The 1 ms clock and guard margins depend on the actual REFO tolerance; the host model uses the firmware's integer clock domain. A successful host model cannot qualify these measurements.

## Home programming and preservation

The board's existing USB-C port supplies charging power; its data pins are not routed for MCU programming. Q3 already exposes the four SBW fixture contacts below. A compatible TI MSP-FET/SBW probe and a reliable pogo/contact fixture are a practical route to home programming; host OS/driver/probe integration still needs an actual trial. This review purchased no adapter and makes no cost-saving claim.

| Q3 contact | Purpose for an externally powered target |
|---|---|
| TP1 | Common ground |
| TP2 | Sense the board's V3 rail; do not feed programmer supply voltage into it |
| TP3 | RST/NMI/SBWTDIO |
| TP4 | TEST/SBWTCK |

TI documents SBW in the [FR4133 datasheet, §§9.6 and 10.1.3, Figure 10-4](https://www.ti.com/lit/ds/symlink/msp430fr4133.pdf). With an MSP-FET 14-pin connector, target-voltage sense is pin 4 and tool supply is pin 2; they must not be tied together. Use the board's approved power path and leave the probe's target supply disconnected to avoid driving the Q3 regulator output. The board's C10 is 1 nF; TI specifies an SBW reset-capacitance limit of 1.1 nF, so fixture capacitance matters too.

For an existing counter, first back up and decode **all information FRAM, `0x1800–0x19FF`**, with the target halted and buttons untouched. The journal occupies `0x1800–0x181F`; the input-gap marker occupies `0x1820–0x1821`. Load only the verified application HEX, read back/verify the application, and compare every information byte with the backup before resuming. The separate factory initializer deliberately clears the count and fault marker and is unsuitable for an ordinary update.

[TI MSP Flasher guide, Table 1 and §6](https://www.ti.com/lit/pdf/slau654) documents reading memory, verifying an image, and `-e NO_ERASE` to preserve regions outside the addressed image blocks. Its default `ERASE_ALL` and FR4xx `ERASE_USER_CODE` erase information memory. A preservation procedure must select and validate the explicit no-erase FRAM path; defaults are unsafe here. Do not use the debug-locking `-f` option. These are workflow requirements, not a claim that a complete unattended flashing command has been bench-tested on Q3.

### Could USB-C program this MCU after a board change?

The FR4133 has a ROM UART bootloader. Its TX is **P1.0** and RX is **P1.1**, the same pins used by Q3's increment and reset inputs. A USB-to-UART bridge would therefore need a board revision that resolves switch/RC loading and contention, plus reset/TEST control; fitting a bridge alone is insufficient. [TI datasheet, §9.4/Table 9-3](https://www.ti.com/lit/ds/symlink/msp430fr4133.pdf).

BSL entry requires at least two TEST rising edges while RST is low, with TEST high when RST rises, followed by the specified completion sequence. The first TEST-high interval must satisfy the device's enable timing. The password is the current 32 bytes at `0xFFE0–0xFFFF`. **On FR4xx, an incorrect password initiates mass erase including information FRAM**, which would erase both saved count and gap marker. A future USB update flow must use the known current password, avoid mass erase, preserve/verify information FRAM and handle interrupted updates. No such board or updater change was made here. [TI FRAM BSL guide, §3.3.2, §4.1.5.2 and §7.2](https://www.ti.com/lit/pdf/slau550).
