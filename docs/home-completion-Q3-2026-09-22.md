# Home completion and cost decision — 22 September 2026

## Recommended review scope

Retain the reviewed two-layer Q3 electronics for the independent review. Allow a future assembly split with **home firmware loading and the two through-hole switches soldered at home** if the actual reduction exceeds adapter/fixture/supply costs. Do not change a vendor draft or request new pricing now. This note supersedes the older assumption that every solder joint and initial programming must be vendor work; it does not alter the frozen RFQ.

The current processor is MSP430FR4133IG48R, not ESP32. Its FRAM journal and low-power firmware are already implemented. Merely making home programming possible does not justify replacing it with an ESP32, rerouting the board, rewriting retention and requalifying the coin-cell power budget. The LCD peripheral is now unused; a smaller MCU remains a future cost option, not a change included here.

## What the existing prices actually support

The September15 five-unit JLCPCB automatic total was $255.86 before depaneling, final freight and additional services. Components were $83.77; setup $51.12; feeder loading $62.73; assembly fixture $16.42; hand-soldering $3.58 and manual assembly $1.48. These are historical quote inputs, not current guaranteed prices.

- The two manual-labor lines total only **$5.06 per batch**. They include work beyond the switches; removing the switches does not establish that all $5.06 disappears.
- Even crediting the entire $16.42 fixture would produce only a **$21.48 batch ceiling for those three displayed lines**. That is an illustrative upper bound on those lines, not a savings quote; the OLED/USB may still need the fixture. Do not delete all setup, feeder or fixture charges in a comparison.
- JLCPCB's September15 email specifically lists programming at **$8.15 engineering plus $8.15/hour**, subject to review. Hardware testing is a separate activity. Home programming is economically attractive if a compatible adapter is already available, or if avoided programming charges exceed the adapter and fixture cost. No adapter price or vendor hours are established, so net savings are unproven.
- Home switch soldering does **not** make the OLED disappear from the top side or turn its fine-pitch FPC into a simple header. Standard versus Economic assembly eligibility and actual one-pass pricing need a later approved inquiry.
- Four layers have already been reduced to **two**, and reflow SMT is concentrated on the bottom. The stocked OLED increases fitted components from50 to70; these reductions alone do not prove a cheaper complete device.

The dominant assembly cost opportunities in this snapshot are fewer distinct feeder setups and a simpler display/power assembly, rather than four switch joints. They require a coherent engineering change and later comparison, not repeated vendor uploads. Keep charger/protection/thermal and first-article qualification intact.

## Practical home boundary

| Work | Proposed responsibility | Prerequisite |
|---|---|---|
| Bottom SMT, exposed-pad power ICs, USB hybrid connector | Vendor | Reviewed paste/reflow and numbered-pad placement |
| OLED14-contact FPC | Qualified assembler | Exact supported heat/land/support process; no home FPC work assumed |
| SW1/SW2 | Home option | Exact switches; fixture/plate seats both squarely before four terminal joints; inspect joints and test both inputs |
| Battery welding, insulation, NTC attachment and keyed pack | Qualified pack supplier | Approved genuine cell, sensor drawing/process and qualification; never assign bare-cell iron soldering to home assembly |
| Firmware loading | Home option | Compatible Spy-Bi-Wire programmer and reliable four-signal contact fixture |
| Enclosure printing, fitting, caps and keyed battery connection | Home | Final print/fit/retention checks |
| Electrical and charging qualification | Required regardless of who assembles | Measurements and fault tests in the engineering release plan; a successful flash is not qualification |

## Home programming interface

TI documents MSP-FET support for Spy-Bi-Wire and the FR4133 LaunchPad's ability to program other MSP430 targets. Use an adapter that can sense the actual3.0V target rail and handle its logic levels; an unmodified LaunchPad power output is not automatically an approved supply for this board. See [MSP-FET](https://www.ti.com/tool/MSP-FET) and [FR4133 LaunchPad guide, external-device programming](https://www.ti.com/lit/ug/slau595b/slau595b.pdf).

The existing board exposes TP1=GND, TP2=V3 sense, TP3=RST/SBWTDIO and TP4=TEST/SBWTCK. USB on Count Fidget is charge-only. The connector/fixture must follow the Q3 pad drawing, not Q1/Q2 coordinates. Use a stable approved target supply arrangement, common ground and short programming leads; do not drive the output of the board's unpowered/discharging regulator from a programmer. Exact adapter wiring, contact pressure and programming software on the user's computer require a bench trial before this is a turnkey home procedure.

For a **new factory device**, verify the factory initializer clears exactly0x1800–0x1821, then load and verify the Q3 application. For an **ordinary firmware update**, load only the application and preserve all information FRAM0x1800–0x19FF. The factory initializer erases the saved count/error marker and must never be part of the ordinary update workflow. Keep programming/debug access unlocked.

After programming, check one increment per press, held-key no-repeat, reset priority, wake counting, persistence after power removal and OLED fault recovery. Commission charging/protection separately with suitable instruments before use. No hardware has yet passed these tests.

## Could USB-C replace the external programmer?

The connector has data contacts, but the Q3 board leaves them disconnected. The selected MSP430FR4133 has no native USB peripheral; a charging cable cannot program this design. [TI device capabilities](https://www.ti.com/product/MSP430FR4133).

Two separate engineering options exist: add an onboard USB-to-UART bridge and the target bootloader-entry connections, or redesign around an MCU with native USB programming. The former adds bridge/support parts and a validated bootloader workflow to every unit; the latter also changes the firmware, retention strategy and power budget. A single compatible external Spy-Bi-Wire programmer serves the entire batch. No current adapter-versus-bridge cost comparison has been established, so neither savings nor a specific implementation is approved by this discussion.

TI assigns this device's UART bootloader to P1.0/P1.1, which Q3 already uses for the two buttons. A bridge redesign therefore must resolve button loading/contention and boot-entry control. An incorrect bootloader password can erase both application and information FRAM, including the retained count. See the [dated firmware review](review-Q3-2026-09-22-firmware.md) for exact primary references and retention conditions.

The user's September22 question raises a useful convenience option; it does not select a new MCU or authorize another vendor quote. Review exact ROM bootloader entry, pin sharing, password/unlock behavior and information-FRAM retention before turning USB flashing into a design change. Keep the existing programming test points for recovery/debugging even if USB updates are later added.

## Approval state

This is an internal engineering/cost option. No revised vendor scope, new quote request, purchase, hardware release or claim of realized savings is made. The next agent should review the complete candidate and remaining blockers before the user decides whether to authorize one consolidated vendor revision.
