# Q5 firmware emulation (instruction-level)

Runs the **actual Q5 firmware image** (`firmware/q5-stm32/build/count-fidget-Q5-stm32.elf`) on an emulated Cortex-M0+ with models of the Q5 board. `q5emu.py` is derived from the [Q4 emulator](../q4-firmware-emulation/README.md) and adds the board changes below. **This is a model, not hardware**: results are "reproduced in emulation" and do not replace the physical gates in `docs/REVIEW-Q5-2026-09-25.md`.

## Added to the Q4 model

| Block | Model |
|---|---|
| U7 soft power latch | U7 ON = USB (D4) OR COUNT key (D3 A1) OR PB2 driven high (D3 A2). From off, a COUNT press or USB starts the board after tON 17.9 ms (4.7 nF CT) plus 2 ms. A release with no source collapses the supply after 5 ms while running, or 80 ms in Stop. A source returning before that cancels the collapse. Power loss clears SRAM, resets the OLED and wakes FRAM from sleep. A violation is recorded if the display or pump is on, or an FRAM transaction is open, at collapse. |
| USB and charger | USB presence sets SYS to 4.5 V (BQ25185 VSYS_REG). STAT1/STAT2 are open-drain outputs for charging/done/fault (Table 6-2). A read without pull-up is noted. |
| Battery divider | ADC_IN4 = SYS/2 against the modelled VLOGIC, with ±1.5 LSB noise. A violation is recorded if PA4 is not analog. |
| RCC reset flags | POR+PIN on power-up, PIN on NRST, SFTRST, OBLRST; RMVF clears them. |
| FLASH option bytes | PECR locks, PEKEYR/OPTKEYR sequences, the USER word at 0x1FF80004 with its complement check, BSY for 3.2 ms, and OBL_LAUNCH reload and reset. |
| OLED switch | tON 17.9 ms (C28 4.7 nF). QOD is unconnected: supply released by an MCU reset while RES# is low is noted, not flagged as a sequencing violation. |
| Timing | Default flash wait-state penalty 0 (Q5 sets LATENCY = 0); pass 0.5 for the pessimistic Q4 assumption. |

Not modelled:
- analog rail droop and the real U7/LDO/FRAM ramps;
- contact bounce on the ON node;
- currents (the energy model multiplies emulated state durations by datasheet currents);
- charger or protector state machines;
- oscillator tolerance;
- USB enumeration.

## Running

Requires Python 3.10+ with `unicorn==2.1.4`, `capstone==5.0.7` and `pyelftools`.

```sh
python3 simulation/q5-firmware-emulation/scenarios.py --check --output simulation/q5-firmware-emulation/results/scenarios.json
python3 simulation/q5-firmware-emulation/energy.py --output simulation/q5-firmware-emulation/results/energy-model.json
python3 simulation/q5-firmware-emulation/q5emu.py firmware/q5-stm32/build/count-fidget-Q5-stm32.elf --seconds 1.5
```

`--check` asserts every expectation (a full run takes about six minutes):

- first use shows `0 ERR`; a short reset tap does nothing; a hold-and-release zeroes; the RST prompt appears at 2.0–2.1 s;
- COUNT during a reset hold, and both keys together, increment; an 11 s hold is abandoned;
- press-to-display is under 100 ms;
- on USB: sleep with PB2 released; wake-to-lit under 400 ms; NRST keeps the count without ERR;
- USB removal keeps the latch; the battery timeout powers the board off;
- a wrapped-journal boot drops no samples under both timing models; the power-on press counts once; off-to-lit is under 500 ms;
- a 10 ms tap is too short to power on; a key held 45 s counts once and still powers off; NRST on an off board does nothing;
- three DFU entry orders keep the count; NRST on battery powers off and keeps the count;
- factory option bytes are self-provisioned, then the device counts; an unexpected option set shows OPT with no FRAM access;
- 100 bouncy presses at 12 Hz;
- LO at 3.52 V; cut-off at 3.30 V after LO, with the count saved; USB during the LO notice cancels the cut-off;
- CHG, the full gauge and BAT;
- unplugging USB in Stop powers off;
- a held key on USB counts once.

Every scenario must also record zero contract violations.
