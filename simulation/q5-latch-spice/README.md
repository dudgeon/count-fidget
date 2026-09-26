# Q5 soft-power latch — behavioural ngspice transient

`python3 simulation/q5-latch-spice/latch.py` (ngspice 42) writes `result.json`.

The circuit is the real Q5 latch netlist: cell/protector path, a bouncing SW1 contact, BAT54C D3, C40/R35, and the D4/R38 VBUS path. U7 (TPS22917), the TLV767 and the STM32's reset and PB2 hold are modelled behaviourally. The corners are:
- cell voltage: 3.4, 3.7 and 4.2 V;
- U7 ON threshold: 0.4, 0.7 and 1.0 V;
- slew: ±25 %;
- reset temporisation: 1.0 and 3.3 ms.

Results (see `result.json` for every case):
- **Clean press:** the minimum press that latches ranges from 4.4 ms at the best corner to **20.0 ms at the worst corner**, against a ~50 ms deliberate press.
- **Bouncing contact:** 3–8 make chatters and 2–6 break chatters latched **60/60** at 50 ms and **60/60** at the worst minimum + 5 ms.
- **Very short taps:** 2–15 ms taps either latch or abort. Three aborted after the MCU was briefly powered (a "start abort"). The firmware writes nothing during boot, and the emulator covers this case.
- **USB alone:** 4.40–5.25 V turns the board on at every threshold corner.

Limits: this is a behavioural simulation, not a measurement. TI's TPS22917 model is an encrypted PSpice model that ngspice cannot run, so the switch's timing comes from typical datasheet figures widened by the corners. First-article test B2 measures the real minimum press.
