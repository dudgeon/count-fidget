# Q3 OLED firmware adversarial review

Date: 15 September 2026. Scope: separate `firmware/q3-oled/`, target build/verification scripts, exact ELF/HEX and applicable controller/MCU documentation. This review does not certify physical hardware or release manufacture. Q1/Q2 submitted sources and images were not changed. In particular, the historical Q1 source/binary allegation remains refuted: TI's `LCD4MUX` includes `LCDSON`.

**Final status: FQ3-01, FQ3-02 and FQ3-03 were corrected and independently retested in the final image identified below. No unresolved reproducible firmware defect was found in this review scope.** This is a software-review result, not physical qualification or manufacturing approval. The initial findings and exact-image evidence are retained below as history.

## Confirmed finding FQ3-01 — P1: input history disappears during foreground work

**Locations in the reviewed initial source:** `main_msp430.c:104–112`, `main_msp430.c:136–143`, `oled.c:108–112`, `oled.c:141–147`, `counter.c:60–74`; the sampling contract is in `counter.h:13–16`.

The port interrupt only clears the input flags, rearms the next edge and wakes the CPU. The timer interrupt advances time and wakes the CPU. Neither captures a sample or preserves the time/history of an edge. Only the foreground calls `counter_sample`. Its following journal and OLED operations can run for longer than the entire 8 ms debounce interval. Both edges of a valid short press can occur and be handled by the port ISR while these operations run. The next foreground sample sees the released key, so that press is forgotten.

### Independent target evidence

TI GDB's MSP430 CPU simulator executed the **stored ELF**, with entry registers and RAM set for each ordinary function call. This was not a native-host speed measurement and did not use the supplied host tests to infer target timing.

A coherent reachable state is an existing display frame for **88,888,888**, page 0, columns 80–95, while a newly accepted increment commits **88,888,889**. The two valid journal records have sequence/count pairs `(100,88888887)` and `(101,88888888)`.

| Consecutive foreground operation | Executed target instructions | Conservative minimum CPU cycles |
|---|---:|---:|
| `journal_save`, including real target `write_word` | 2,878 | 3,943 |
| `oled_service`, data generation up to entry to `bus_start` | 3,511 | 5,079 |
| Combined, before the next input sample | 6,389 | **9,022** |

At the configured nominal **1.048576 MHz**, that lower bound is **8.604 ms**. The bound counts at least one cycle per executed instruction, two for jumps, four for calls/returns, two for ordinary memory-source operations and three for memory destinations. It deliberately omits additional costs of immediate operands, repeated instructions, multiple-register stack operations, omitted surrounding foreground work and interrupt service. It is a lower bound, not a claim of measured worst-case hardware time. TI SLAU445I §4.5.1.5 documents the underlying instruction timings.

Even a single high-value digit conversion takes **1,956 target instructions**, already more than 1 ms before multi-cycle instructions. The `% 10` and `/ 10` expressions produce separate software arithmetic helper calls in this ELF, despite the source's “one division” comment. The frame-data renderer also performs repeated software divisions inside its 16-column step.

### Missed-pulse reproduction

Choose a stable RESET pulse at physical time **0.05–8.30 ms**, within the above gap. An ideal 1 ms timer sample phase of `0.10, 1.10, …, 8.10 ms`, with integer millisecond timestamps `0…8`, accepts that reset. The initial Q3 foreground cannot observe either level change during the gap; both port interrupts return without preserving their samples. Its next sample still sees RESET released.

A targeted reproduction using the actual `counter.c` confirms the consequence:

> Ideal timer sampling resets to 0; the existing foreground gap retains 88888889 (reset missed).

Local audit materials are in `/private/tmp/`, not production sources:

- `/private/tmp/q3-journal-coherent.gdb` and `.log`: exact-ELF journal call, valid CRC records, resulting committed target words and instruction trace.
- `/private/tmp/q3-data80-count.gdb` and `.log`: exact-ELF renderer entry state and trace to the start of the transfer.
- `/private/tmp/q3-digit-count.gdb` and `.log`: high-value digit conversion.
- `/private/tmp/q3-press-gap.c` and `/private/tmp/q3-press-gap`: explicit pulse/sampling-schedule counterexample.

Run a GDB reproduction with `/private/tmp/count-fidget-toolchain/msp430-gcc-9.3.1.11_macos/bin/msp430-elf-gdb --batch -x <script> firmware/q3-oled/build/click-counter-Q3-oled.elf`. The scripts set the original image's exact symbol addresses; they are historical evidence and must not be run unchanged against a rebuilt image with shifted addresses.

**Required correction:** preserve timestamped input samples/events independently of foreground work, or demonstrate that every foreground path, including journal validation/CRC and rendering, meets the sampling bound. A bounded ISR-to-foreground queue is a reasonable correction, but its capacity, overflow behavior, atomic access, draining, held-key sleep and first wake sample must be reviewed. Keep FRAM writes outside interrupt handlers. Regression testing must include a pulse fully enclosed by a real target foreground interval, not only one ideal host sample per loop.

## Build and binary evidence for the initial reviewed image

The stored manifest verification passed. The supplied counter and OLED tests passed, but their ideal sampling schedule cannot detect FQ3-01. An independent TI GCC 9.3.1.11/support 1.212 build into `/private/tmp/q3-firmware-independent-build/` reproduced ELF, HEX, MAP and listing **byte-for-byte**.

| Initial reviewed file | SHA-256 |
|---|---|
| `main_msp430.c` | `f7ce246bc6b5a2342b06abf397098ac23a6f71d739b3764fa8b076ad7ede9ceb` |
| `oled.c` | `029ff138ad2a6e3a8a36e64138976946afa28576a3e8e3b3b9099097b57bd7e6` |
| ELF | `c4c02b4170370eec0dd3abfc11e06b6c82b44c7972e0d70effca8c210e1caf95` |
| HEX | `b698351064fe97a6b7923440d29c4fc8ba246d2a7623c2adba1403a1637f6ce5` |

Direct disassembly inspection confirmed:

- Reset vector `0xFFFE → 0xC4C4`; port `0xFFE6 → 0xC696`; eUSCI_B0 `0xFFEA → 0xC61C`; Timer0_A0 `0xFFF8 → 0xC6CA`.
- Correct eUSCI vector cases for arbitration loss, NACK, STOP and TX-ready; byte counter contains the control/data length, excluding the slave address, matching TI §24.3.8.2. Automatic STOP is enabled. Completion is checked before sleeping.
- `write_word` writes `0xA501` to SYSCFG0, writes the aligned information-FRAM word, restores `0xA503`, reads the word back and then changes the shadow. `journal_save` invalidates the destination marker, writes seven payload/CRC words, then commits `0xC17C`; the previous slot remains untouched.
- The application load is 4,244 bytes, excludes information FRAM `0x1800–0x19FF` and security signatures, and uses 146 bytes of static RAM. Stack-usage output is not a measured stack maximum.
- Timer CCR0 is 32, giving 33 ACLK periods per repeated tick. Adding `232/32768` of an extra millisecond per tick correctly compensates the nominal `33/32768` second period. Unsigned time differences and signed short-deadline comparisons handle ordinary 32-bit wrap. REFO tolerance still affects real-time guards.

## Controller and state-machine review

The SSD1312 manufacturer-authored Rev 1.2 document, including its appended Rev 1.4 command table, was inspected. The reset/power-sequence and pump-command table pages were also visually rendered. Module and controller documentation conflict; the following are evidence-supported choices, not proof of module behavior.

- `AD 40` selects external IREF, consistent with the fitted resistor. The explicit pump sequence `8D 72; AF` selects nominal 9 V. The module example's `8D 12` means 7.5 V; its adjacent “external” labeling and 1/28 comment do not override the actual bytes or 128 × 32 geometry.
- The controller's 9 V operating condition uses VBAT at least 3.8 V, motivating regulated 4.0 V within the module's maximum 4.2 V. Tolerance/transient and current verification belongs to the hardware review.
- Initial clear covers all eight controller RAM pages. Subsequent count frames use a stable snapshot and four pages, with dirty-state convergence to the latest committed count. Partial-frame tearing is possible and disclosed. Neither the supplied test's RAM model nor the stateless renderer comparison proves the module's bonded row/segment map.
- Bus failure invalidates display state, asserts reset and follows bounded shutdown/backoff. Early sleep while reset is asserted avoids commands to an unready controller. A press during shutdown remains processed by the counter and the display restarts after shutdown completes, subject to fixing FQ3-01.
- Nominal shutdown and startup waits are nonblocking. Real-time guards need allowance for the fastest REFO clock and the possibility that the stored foreground timestamp predates the transfer. The author is revising the guard margins alongside FQ3-01.

## Required physical gates remain open

No board or display has been tested. Before release, verify actual OLED address/bonding, ACK/NACK and stuck-bus recovery, orientation and all four visible pages, minimum accepted input pulse width under worst rendering/commit load, ISR latency, real clock frequency, supply/reset/pump waveforms, graceful and fault shutdown, panel voltage/current/brightness, sleep leakage and first-press wake behavior. The reset substitution for normal command shutdown needs a waveform check under bus failure.

Exercise power cuts and slow/fast brownouts at the actual protected 3 V rail during journal writes, including repeated failed readback, erased/one-valid/two-valid records and ordinary update preservation. CPU simulation and between-word host tests do not prove electrical FRAM atomicity, effective supply capacitance or reset supervision. Retain the independent cell/protection, charger/temperature, assembly/FPC and mechanical qualification gates.

Sources: [TI family guide](https://www.ti.com/lit/ug/slau445i/slau445i.pdf), [TI MSP430FR4133 datasheet](https://www.ti.com/lit/ds/symlink/msp430fr4133.pdf), [Solomon SSD1312 manufacturer-authored document](https://admin.osptek.com/uploads/SSD_1312_1_2_6a7ea26d1f.pdf), and the exact X087 module PDF recorded by `firmware/q3-oled/source-records.json`.

## Correction review: further issues found before the final build

### FQ3-02 — P2: fault recovery synthesized a held increment

In the first queue correction, `input.c:31` passed increment=false throughout an input fault. After a held RESET qualified, the foreground committed zero and cleared the fault. If INC had remained held throughout, releasing only RESET made the newly unmasked increment input qualify as another press. A target-independent test of the actual corrected `input.c` and unchanged `counter.c`, `/private/tmp/q3-fault-held-inc.c`, confirmed count **1** after resetting to zero without a new INC press.

Reproduction: start with a latched fault; feed INC+RESET at timestamps 0 through 8; commit the resulting reset and clear the fault as the foreground does; feed INC alone at timestamps 9 through 17. Increment must remain zero until INC is released and pressed again. The initial correction instead returned one. The author was given the reproduction and is correcting the release/held-state handling before the final build.

### FQ3-03 — P2: after-ACK guard was inferred from an unenforced timeout

The original shutdown used a deadline 120 nominal milliseconds after starting pump-disable, with an asserted 100 ms after-ACK guarantee based on a 20 ms transaction timeout. However, `bus_poll` accepts a completed transfer before checking elapsed time; late foreground polling may therefore accept an ACK after that nominal timeout. REFO may also run 3.5% fast. A larger start-based delay alone is insufficient as a strict proof.

The in-progress correction starts a **105 nominal ms** guard when a successful pending transfer is observed, for both display-on and pump-off. It also refreshes the foreground time immediately before calling the OLED service, so earlier journal work cannot backdate that completion observation. Startup and reset/fault guard margins are also being revised. Final source/image verification and delayed-ACK tests are pending below.


## Final corrected-image retest — findings closed in software

The firmware author froze the corrected source, then this reviewer independently rebuilt it with TI GCC 9.3.1.11/support 1.212 into `/private/tmp/q3-firmware-final-independent-build/`. ELF, HEX, MAP and disassembly again reproduce the stored outputs byte-for-byte. Manifest verification and the complete supplied host suite pass. Q1/Q2 baseline file records match those captured by the initial independent build.

| Final reviewed artifact | SHA-256 |
|---|---|
| ELF | `953169cd3b0b0eec37e43c150530148bdbc00dafabb90ea326252ff03af4a515` |
| HEX | `b19f9e62fe9833ebb61fa75e94a7adef5664e51c7bcb7ffaa619a7c00bf910bf` |
| `main_msp430.c` | `2f85d8195801e232dae80d5868771f6805203ee08b13a9b20523db599b419dc0` |
| `input.c` | `bc228e7f25e075f082e07e726a3f7be6c575853a5fe8384f0d17a49e671b5934` |
| `oled.c` | `6227d98c0dfbc48c5cd5d460fea6006f80a0f4c0cf26b71f1ef3413ac829f508` |

Final image: **5,033 addressed load bytes; 546 static RAM bytes**. Reset/port/eUSCI/timer vectors now resolve to `0xC4D4 / 0xC6E2 / 0xC668 / 0xC732`. The application still excludes the complete information-FRAM and security-signature regions. An independently parsed, separate **factory-only** `factory-blank-info-Q3.hex` contains exactly 34 bytes of `FF` at `0x1800–0x1821`; it initializes the journal plus new input-gap marker and must not be included in ordinary firmware updates.

### Independent tests beyond the supplied suite

- **FQ3-01 closed:** `/private/tmp/q3-target-input-check.gdb` executes the real final timer ISR nine times with RESET pressed, while performing no foreground sampling. The real port ISR records release; the real `input_take`/`input_apply` functions then consume all ten retained samples and reset the count to zero. This directly checks the corrected target path that the original ideal host schedule missed.
- The same target test fills the actual 63-usable-entry queue with 70 timer samples. It observes exactly seven dropped samples, an explicit `INPUT_GAP`, and a latched input fault. A simulated held-key release with the timer stopped restarts the timer and clears the saved LPM4 exit bits. The test checks register-level CPU behavior, not electrical wake timing.
- The final timer ISR was independently stepped through the millisecond/fraction wrap path: **66 executed instructions**, with `0xFFFFFFFF + two nominal milliseconds → 1`, including the real sample enqueue. There is no journal or renderer in that ISR. Hardware scheduling and accepted pulse width still need measurement.
- `/private/tmp/q3-target-isr-check.gdb` executes the final `bus_start` and eUSCI ISR with emulated register events. Seventeen TX-ready events produce the exact seventeen queued bytes; STOP produces success; NACK produces error, disables I2C interrupts and asserts eUSCI reset. This does not emulate analog line behavior or controller ACK timing.
- **FQ3-02 closed:** the independently written held-increment recovery reproduction, with expected count changed to zero, now passes. `input_apply` tracks actual held INC state while suppressing count changes during a fault. The supplied extended test also verifies that a later release and new press increments once.
- **FQ3-03 closed:** `/private/tmp/q3-guard-independent.c` injects an ACK 250 ms after START, passes a deliberately stale caller timestamp, and advances the clock another 17 ms inside the poll callback. The final service starts the guard from its subsequent fresh HAL clock read. VBAT stays enabled until 105 more nominal milliseconds have elapsed. A separate case crosses 32-bit wrap. The test verifies the +3.5% REFO/one-tick-phase margin, independently of the provided delay-19-ms test.
- Final disassembly and source agree on marker-write/readback protection and ordering: persist fault before journal work; clear uncertainty only after zero is committed and marker clearing reads back successfully. The supplied fault tests exercise rejected writes, rejected clears and reset recovery. The final sleep condition also refuses LPM4 while a fault marker still needs persistence.

The queue has one non-nesting interrupt context as producer and a foreground consumer whose dequeue is interrupt-masked. Each volatile sample is written before its head index is published. An atomic queue-empty/gap check gates LPM4. FIFO overflow cannot silently overwrite old samples: it explicitly discards uncertain history, displays ERR, freezes count changes and requires a debounced reset to establish a new trusted count. This policy is documented; it is not a claim that arbitrary interrupt storms or failed hardware cannot lose input.

**Conclusion:** the reproduced lost-pulse, held-key recovery and guard defects are resolved in the hashes above. No further reproducible firmware defect remains from this audit. All physical gates listed earlier remain open, including input timing under real I2C traffic, display bonding/orientation, rail/reset waveforms and electrical FRAM brownout behavior.
