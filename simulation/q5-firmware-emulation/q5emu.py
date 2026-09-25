#!/usr/bin/env python3
"""Instruction-level emulation of the actual Q5 STM32L072 firmware image.

Derived from the Q4 emulator (simulation/q4-firmware-emulation/q4emu.py) and
extended with the Q5 board: the U7 soft power latch (COUNT key on SYS, PB2
PWR_HOLD and VBUS diode-ORed into U7 ON), USB presence with the BQ25185 SYS
regulation and STAT1/STAT2 outputs, the SYS_LOAD/2 battery divider on ADC_IN4,
RCC reset flags, and FLASH option-byte programming with OBL_LAUNCH.

Executes the ELF with Unicorn (QEMU Thumb core) and explicit models of the MCU
peripherals the firmware touches (RCC, PWR, FLASH, GPIO, EXTI, SYSCFG,
SysTick, NVIC/SCB, SPI1, SPI2, ADC) plus board devices: two keys with bounce,
NRST/BOOT0, the TPS22917-switched HS96L01W4S03/SSD1315 OLED module and the
FM25V02A F-RAM on its RC rail.

Scope and limits: peripheral behaviour is modelled from RM0376/DS10689 register
descriptions, not from silicon.  Instruction timing uses Cortex-M0+ TRM cycle
costs per executed instruction plus a configurable flash wait-state penalty
(Q5 firmware sets FLASH_ACR.LATENCY=0, so the default penalty is 0; pass 0.5
for the pessimistic Q4 assumption).  SPI shifting, ADC conversion, SysTick,
U6/U7 turn-on (typical tON for 4.7 nF CT) and supply collapse after the latch
releases (stated fixed delays) are event-timed.  Analog behaviour (rail droop,
currents, charge-pump output, protector/charger state machines) is not
simulated.  Results are "reproduced in a model", never "observed on hardware".
"""
import argparse
import json
import random
import struct
import sys
from collections import defaultdict

from elftools.elf.elffile import ELFFile
from unicorn import Uc, UcError, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS, UC_HOOK_CODE
from unicorn.arm_const import (UC_CPU_ARM_CORTEX_M0, UC_ARM_REG_SP, UC_ARM_REG_PC, UC_ARM_REG_LR,
                               UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
                               UC_ARM_REG_R12, UC_ARM_REG_XPSR, UC_ARM_REG_PRIMASK)

HZ = 4_000_000          # HSI16 / AHB prescaler 4, set by setup()
OLED_TON = 3.8e-6 * 4700        # TPS22917 tON 3.8 us/pF (VIN 3.3-3.6 V) x C28 4.7 nF
U7_TON = 3.8e-6 * 4700          # system switch, C29 4.7 nF
BOOT_TEMPO = 0.002              # regulator soft start + STM32 POR temporization allowance
COLLAPSE_RUN = 0.005            # latch released while running: ~1.3 mA from ~15 uF to BOR
COLLAPSE_STOP = 0.080           # latch released in Stop: ~80 uA from ~15 uF to BOR
USB_SYS_V = 4.50                # BQ25185 VSYS_REG with valid input (VBATREG <= 4.3 V)
TRAMP = 0x0FFF0000      # exception-return trampoline (stands in for EXC_RETURN)
IRQ_EXTI0_1, IRQ_SPI2, IRQ_I2C1 = 5, 26, 23
EXC_SYSTICK = 15

def bit(n): return 1 << n


# ----------------------------------------------------------------------------
# Board devices
# ----------------------------------------------------------------------------
class Oled:
    """SSD1315 in 4-wire SPI mode behind the TPS22917 module switch."""
    PARAMS = {0x81: 1, 0x8D: 1, 0xA8: 1, 0xD3: 1, 0xD5: 1, 0xD9: 1, 0xDA: 1, 0xDB: 1, 0x20: 1,
              0x21: 2, 0x22: 2, 0xAD: 1, 0x26: 6, 0x27: 6, 0x29: 5, 0x2A: 5, 0xA3: 2, 0xD6: 1}

    def __init__(self, sim):
        self.sim = sim
        self.supply = 0.0          # module VCC node (V)
        self.switch_on_at = None
        self.powered = False
        self.reset_state()
        self.log = []
        self.pixels_valid = False
        self.frames_seen = 0
        self.off_sequence_ok = True
        self.last_pump_off = None
        self.last_display_off = None
        self.power_cycles = 0

    def reset_state(self):
        self.gddram = [[0] * 128 for _ in range(8)]
        self.display_on = False
        self.pump = False
        self.contrast = 0x7F
        self.page = 0
        self.col = 0
        self.seg_remap = False
        self.com_rev = False
        self.addr_mode = 2
        self.pending = None   # (cmd, remaining params)
        self.params = []
        self.mux = 63

    def command(self, b):
        t = self.sim.now_s()
        if self.pending is not None:
            self.params.append(b)
            if len(self.params) == self.PARAMS[self.pending]:
                self.apply(self.pending, self.params)
                self.pending = None
            return
        if b in self.PARAMS:
            self.pending = b; self.params = []
            return
        self.apply(b, [])

    def apply(self, c, p):
        t = self.sim.now_s()
        if c == 0xAE:
            self.display_on = False; self.last_display_off = t
        elif c == 0xAF:
            if not self.pump:
                self.sim.violation('OLED', 'display ON (AFh) without charge pump enabled (8Dh 14h)')
            self.display_on = True
            self.on_at = t
        elif c == 0x8D:
            self.pump = bool(p[0] & 0x04)
            if not self.pump: self.last_pump_off = t
        elif c == 0x81: self.contrast = p[0]
        elif c == 0xA8: self.mux = p[0]
        elif c == 0x20: self.addr_mode = p[0] & 3
        elif c in (0xA0, 0xA1): self.seg_remap = c == 0xA1
        elif c in (0xC0, 0xC8): self.com_rev = c == 0xC8
        elif 0xB0 <= c <= 0xB7: self.page = c - 0xB0
        elif c <= 0x0F: self.col = (self.col & 0xF0) | c
        elif 0x10 <= c <= 0x1F: self.col = (self.col & 0x0F) | ((c & 0x0F) << 4)
        self.log.append((round(t, 6), 'cmd', c, tuple(p)))

    def data(self, b):
        if self.addr_mode != 2:
            self.sim.violation('OLED', 'data write in non-page addressing mode')
        if self.col < 128:
            self.gddram[self.page][self.col] = b
        self.col = (self.col + 1) % 128

    def byte(self, b, dc):
        if not self.powered:
            self.sim.note('OLED byte clocked into unpowered module (ignored)')
            return
        if self.in_reset:
            self.sim.note('OLED byte while RES# low (ignored)')
            return
        if dc: self.data(b)
        else: self.command(b)

    @property
    def in_reset(self):
        return not self.sim.gpio_level('B', 0)

    def update_power(self):
        """U6 on when PB1 drives high. Rise ~tON 17.9 ms (typ, 4.7 nF CT); QOD NC, supply floats off."""
        en = self.sim.gpio_level('B', 1)
        t = self.sim.now_s()
        if en and self.switch_on_at is None:
            self.switch_on_at = t
        if not en and self.switch_on_at is not None:
            self.switch_on_at = None
            if self.powered:
                # power removal checks: AE and 8D10 >= 100 ms before (SSD1315 tOFF)
                ok = (not self.display_on and not self.pump and self.last_pump_off is not None
                      and t - self.last_pump_off >= 0.100)
                if not ok and self.in_reset:
                    # MCU hard reset: R25 holds RES# low (controller reset: display and pump off)
                    # and Q5 leaves U6 QOD unconnected, so VBAT floats down instead of being grounded.
                    self.sim.note('module supply released after an MCU reset with RES# low (QOD NC: supply floats)')
                elif not ok:
                    self.sim.violation('OLED', 'module supply removed without AEh/8Dh10h and >=100 ms tOFF '
                                       f'(display_on={self.display_on}, pump={self.pump})')
            self.powered = False
            self.reset_state()
            self.power_cycles += 1
            self.sim.ev('oled', 'off')

    def tick(self):
        if self.switch_on_at is not None and not self.powered:
            if self.sim.now_s() - self.switch_on_at >= OLED_TON:   # TPS22917 tON typ at CT=4.7nF
                self.powered = True
                self.powered_at = self.sim.now_s()
                self.reset_state()
                self.sim.ev('oled', 'on')

    def render(self):
        rows = []
        for y in range(64):
            page, bitn = divmod(y, 8)
            line = []
            for x in range(128):
                line.append('#' if (self.gddram[page][x] >> bitn) & 1 else '.')
            rows.append(''.join(line))
        return rows


class Fram:
    """FM25V02A: 32 KiB, 2-byte address, WREN/WRDI/RDSR/WRSR/READ/FSTRD/WRITE/SLEEP/RDID."""
    def __init__(self, sim, fill=0x00):
        self.sim = sim
        self.mem = bytearray([fill]) * 32768
        self.status = 0
        self.wel = False
        self.asleep = False
        self.wake_started = None
        self.selected = False
        self.powered_at = 0.0
        self.writes = 0
        self.ops = defaultdict(int)
        self.sleep_count = 0
        self.wake_count = 0

    def cs_fall(self):
        t = self.sim.now_s()
        if t - self.powered_at < 250e-6:
            self.sim.violation('FRAM', 'CS low before tPU (250 us) after power-up')
        self.selected = True
        self.cmd = None; self.idx = 0; self.addr = 0; self.ignore = False; self.out = b''
        if self.asleep:
            self.asleep = False
            self.wake_started = t
            self.wake_count += 1
            self.sim.ev('fram', 'standby')
            self.ignore = True          # this transaction only wakes the device
        elif self.wake_started is not None and t - self.wake_started < 400e-6:
            self.sim.violation('FRAM', f'access {1e6*(t-self.wake_started):.0f} us after wake (< tREC 400 us)')
            self.ignore = True

    def cs_rise(self):
        if not self.selected: return
        self.selected = False
        if self.ignore: return
        c = self.cmd
        if c == 0x06: self.wel = True
        elif c == 0x04: self.wel = False
        elif c in (0x02, 0x01): self.wel = False
        elif c == 0xB9 and self.idx == 1:
            self.asleep = True; self.sleep_count += 1; self.sim.ev('fram', 'sleep')

    def xfer(self, mosi):
        if not self.selected or self.ignore:
            return 0xFF
        i = self.idx; self.idx += 1
        if i == 0:
            self.cmd = mosi; self.ops[mosi] += 1
            return 0xFF
        c = self.cmd
        if c == 0x05:
            return self.status | (2 if self.wel else 0)
        if c == 0x9F:
            ident = [0x7F] * 6 + [0xC2, 0x22, 0x08]
            return ident[i - 1] if i - 1 < len(ident) else 0x00
        if c in (0x03, 0x02, 0x0B):
            if i <= 2:
                self.addr = ((self.addr << 8) | mosi) & 0x7FFF
                return 0xFF
            if c == 0x0B and i == 3:
                return 0xFF
            if c == 0x03 or c == 0x0B:
                v = self.mem[self.addr]; self.addr = (self.addr + 1) & 0x7FFF
                return v
            if c == 0x02:
                if not self.wel:
                    self.sim.violation('FRAM', 'WRITE without WEL')
                    return 0xFF
                self.mem[self.addr] = mosi; self.addr = (self.addr + 1) & 0x7FFF
                self.writes += 1
                return 0xFF
        if c == 0x01:
            if self.wel and i == 1: self.status = mosi & 0x8C
            return 0xFF
        return 0xFF


# ----------------------------------------------------------------------------
# MCU
# ----------------------------------------------------------------------------
class Spi:
    def __init__(self, sim, name, pclk_div=1):
        self.sim, self.name = sim, name
        self.reset()

    def reset(self):
        self.cr1 = 0; self.cr2 = 0
        self.txe, self.rxne, self.ovr, self.modf = True, False, False, False
        self.tx_buf = None
        self.rx = 0
        self.shift = None
        self.shift_end = None
        self.bytes = 0

    @property
    def spe(self): return bool(self.cr1 & bit(6))

    def busy(self): return self.shift is not None or self.tx_buf is not None

    def prescaler(self): return 2 << ((self.cr1 >> 3) & 7)

    def sr(self):
        v = 0
        if self.rxne: v |= bit(0)
        if self.txe: v |= bit(1)
        if self.modf: v |= bit(5)
        if self.ovr: v |= bit(6)
        if self.busy(): v |= bit(7)
        return v

    def write_dr(self, value):
        value &= 0xFF
        if not self.spe:
            self.tx_buf = value; self.txe = False; return
        if self.shift is None and self.tx_buf is None:
            self.start(value)
        elif self.tx_buf is None:
            self.tx_buf = value; self.txe = False
        else:
            self.sim.violation(self.name, 'DR written while TX buffer full (byte lost)')
            self.tx_buf = value

    def start(self, value):
        self.shift = value
        self.shift_end = self.sim.cyc + 8 * self.prescaler()
        self.txe = True
        self.sim.schedule(self.shift_end)

    def read_dr(self):
        self.rxne = False
        return self.rx

    def set_cr1(self, v):
        was = self.spe
        self.cr1 = v & 0xFFFF
        if was and not self.spe and self.busy():
            self.sim.note(f'{self.name} disabled while busy')
            self.shift = None; self.tx_buf = None; self.txe = True
        if not was and self.spe and self.tx_buf is not None and self.shift is None:
            b = self.tx_buf; self.tx_buf = None; self.start(b)

    def service(self):
        if self.shift is not None and self.sim.cyc >= self.shift_end:
            miso = self.sim.spi_exchange(self, self.shift)
            bidi = bool(self.cr1 & bit(15))
            if not bidi:
                if self.rxne: self.ovr = True
                else: self.rx = miso; self.rxne = True
            self.bytes += 1
            self.shift = None
            if self.tx_buf is not None and self.spe:
                b = self.tx_buf; self.tx_buf = None; self.start(b)

    def irq(self):
        return ((self.cr2 & bit(7)) and self.txe) or ((self.cr2 & bit(6)) and self.rxne) or \
               ((self.cr2 & bit(5)) and (self.ovr or self.modf))


class Adc:
    def __init__(self, sim):
        self.sim = sim
        self.reset()

    def reset(self):
        self.isr = 0; self.ier = 0; self.cr = 0; self.cfgr1 = 0; self.cfgr2 = 0; self.smpr = 0
        self.chselr = 0; self.dr = 0; self.calfact = 0
        self.done_at = None; self.cal_at = None; self.rdy_at = None; self.reg_at = None
        self.conversions = 0

    def adc_clock(self):
        return HZ / 2 if (self.cfgr2 >> 30) == 1 else HZ / 4 if (self.cfgr2 >> 30) == 2 else HZ

    def write_cr(self, v):
        t = self.sim.cyc
        if v & bit(28) and not self.cr & bit(28): self.reg_at = t
        self.cr = (self.cr & ~bit(28)) | (v & bit(28))
        self.sim.ev('adc', 'on' if self.cr & bit(28) else 'off')
        if v & bit(31):   # ADCAL
            if self.cr & bit(0): self.sim.violation('ADC', 'ADCAL with ADEN=1')
            self.cr |= bit(31); self.cal_at = t + 83 * HZ / self.adc_clock(); self.sim.schedule(self.cal_at)
        if v & bit(0) and not self.cr & bit(0):
            self.cr |= bit(0); self.rdy_at = t + 40; self.sim.schedule(self.rdy_at)
        if v & bit(2) and self.cr & bit(0):   # ADSTART
            self.cr |= bit(2)
            smp = [1.5, 3.5, 7.5, 12.5, 19.5, 39.5, 79.5, 160.5][self.smpr & 7]
            self.done_at = t + (smp + 12.5) * HZ / self.adc_clock(); self.sim.schedule(self.done_at)
        if v & bit(4) and self.cr & bit(2):   # ADSTP
            self.cr &= ~(bit(2) | bit(4)); self.done_at = None
        if v & bit(1) and self.cr & bit(0):   # ADDIS
            self.cr &= ~(bit(0) | bit(1)); self.isr &= ~bit(0)

    def service(self):
        t = self.sim.cyc
        if self.cal_at is not None and t >= self.cal_at:
            self.cal_at = None; self.cr &= ~bit(31); self.isr |= bit(11); self.calfact = 0x40
        if self.rdy_at is not None and t >= self.rdy_at:
            self.rdy_at = None
            if self.cr & bit(0): self.isr |= bit(0)
        if self.done_at is not None and t >= self.done_at:
            self.done_at = None
            self.cr &= ~bit(2)
            if self.isr & bit(2): self.isr |= bit(4)
            self.isr |= bit(2) | bit(3)
            self.dr = self.sim.board_adc_sample(self.chselr, self.reg_at)
            self.conversions += 1


class Sim:
    def __init__(self, elf_path, optr=0x807C00AA, vlogic=3.20, fram_fill=0x00, seed=1, flash_ws_penalty=0.0,
                 vbat=3.85, usb=False, charge='done', start='usb'):
        """optr: FLASH_OPTR value (0x807C00AA = provisioned BOR_LEV 0xC; 0x807000AA = RM0376 factory value).
        start: 'usb' boots with USB present, 'key' boots from a COUNT press on battery, 'off' starts unpowered."""
        self.rng = random.Random(seed)
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
        self.uc.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_M0)
        self.optr = optr
        self.vlogic = vlogic
        self.cyc = 0.0
        self.next_event = float('inf')
        self.violations = []
        self.timeline = []
        self.timeline_state = {}
        self.nrst_held = False
        self.profile = None
        from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
        self.md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
        self.cost_cache = {}
        self.flash_ws_penalty = flash_ws_penalty
        self.profile_armed = False
        self.profile_arm_at = None
        self.profile_stop_at = None
        self.profile_end = None
        self.profile_final = None
        self.notes = defaultdict(int)
        self.trace = []
        self.load_elf(elf_path)
        self.oled = Oled(self)
        self.fram = Fram(self, fill=fram_fill)
        self.sw1 = False; self.sw2 = False
        self.scenario = []
        self.halted = None
        self.in_stop = False
        self.stop_count = 0
        self.stop_time = 0.0
        self.sleep_time = 0.0
        self.boot_count = 0
        self.dfu = False
        self.vbat = vbat
        self.usb = usb or start == 'usb'
        self.charge = charge              # 'charging' | 'done' | 'fault' (BQ25185 Table 6-2)
        self.board_state = 'off'
        self.collapse_token = 0
        self.power_events = []
        self.csr_flags = 0
        self.pecr = 0x7; self.pe_unlock = 0; self.opt_unlock = 0; self.ob_word = None
        self.option_writes = 0
        self.map_memory()
        self.gpio = {'B': dict(MODER=0xFFFFFFFF, OTYPER=0, OSPEEDR=0, PUPDR=0, ODR=0, AFR0=0, AFR1=0)}
        if start == 'key':
            self.sw1 = True
            self.at(0.080, 'key', 'inc', False)       # an 80 ms power-on press
        self.board_on('power-on')
        if start == 'off':
            self.board_off(); self.power_events.clear(); self.timeline.clear(); self.timeline_state.clear()
            self.ev('board', 'off'); self.ev('mcu', 'off')

    # ---------------- infrastructure ----------------
    def now_s(self): return self.cyc / HZ

    def violation(self, who, what):
        entry = (round(self.now_s(), 6), who, what)
        if entry[1:] not in [v[1:] for v in self.violations]:
            self.violations.append(entry)

    def note(self, what): self.notes[what] += 1

    def ev(self, name, value):
        last = self.timeline_state.get(name)
        if last != value:
            self.timeline.append((self.now_s(), name, value))
            self.timeline_state[name] = value

    def schedule(self, when):
        if when < self.next_event: self.next_event = when

    def load_elf(self, path):
        with open(path, 'rb') as f:
            elf = ELFFile(f)
            self.segments = []
            for seg in elf.iter_segments():
                if seg['p_type'] == 'PT_LOAD' and seg['p_filesz']:
                    self.segments.append((seg['p_paddr'], seg.data()))
            self.symbols = {}
            symtab = elf.get_section_by_name('.symtab')
            for s in symtab.iter_symbols():
                if s.name: self.symbols[s.name] = s['st_value']
        self.flash = bytearray(b'\xff' * 0x20000)
        for addr, data in self.segments:
            self.flash[addr - 0x08000000: addr - 0x08000000 + len(data)] = data
        self.wfi_addrs = set()
        # scan Thumb code for WFI (0xBF30) at halfword alignment in .text and ramfunc
        for a in range(0, len(self.flash) - 1, 2):
            if self.flash[a] == 0x30 and self.flash[a + 1] == 0xBF:
                self.wfi_addrs.add(0x08000000 + a)
        self.panic_addr = self.symbols['panic'] & ~1
        self.default_addr = self.symbols['Default_Handler'] & ~1

    def map_memory(self):
        uc = self.uc
        uc.mem_map(0x08000000, 0x20000)
        uc.mem_write(0x08000000, bytes(self.flash))
        uc.mem_map(0x20000000, 0x5000)
        uc.mem_map(TRAMP, 0x1000)
        uc.mem_write(TRAMP, b'\x00\xbf' * 0x800)
        sysmem = bytearray(0x1000)
        struct.pack_into('<H', sysmem, 0x78, 1671)      # VREFINT_CAL at 0x1FF80078 (1.224 V @ 3.0 V)
        struct.pack_into('<H', sysmem, 0x7A, 670)
        struct.pack_into('<H', sysmem, 0x7C, 192)
        # Option bytes + factory calibration: MMIO so option-byte programming is observable.
        struct.pack_into('<II', sysmem, 0, 0xFF5500AA, ((~(self.optr >> 16) & 0xFFFF) << 16) | ((self.optr >> 16) & 0xFFFF))
        self.sysmem = sysmem
        uc.mmio_map(0x1FF80000, 0x1000, self.ob_read, None, self.ob_write, None)
        uc.mmio_map(0x40000000, 0x16000, self.apb_read, None, self.apb_write, None)
        uc.mmio_map(0x40020000, 0x4000, self.ahb_read, None, self.ahb_write, None)
        uc.mmio_map(0x50000000, 0x2000, self.gpio_read, None, self.gpio_write, None)
        uc.mmio_map(0xE000E000, 0x1000, self.scs_read, None, self.scs_write, None)
        uc.hook_add(UC_HOOK_CODE, self.on_code)

    # ---------------- reset ----------------
    def mcu_reset(self, cause):
        self.boot_count += 1
        self.csr_flags |= {'NRST': bit(26), 'software': bit(28), 'OBL': bit(25)}.get(cause, 0)
        # BOOT0 is sampled at reset release: PA1 net is BOOT_COUNT_RESET (SW2 high)
        if self.sw2:
            self.dfu = True
            self.halted = f'ROM bootloader (BOOT0 high at {cause})'
        self.ev('mcu', 'run')
        self.rcc = dict(CR=0x300, CFGR=0, IOPENR=0, AHBENR=0x100, APB2ENR=0, APB1ENR=0,
                        APB2RSTR=0, APB1RSTR=0, CSR=self.csr_flags)
        self.pecr = 0x7; self.pe_unlock = 0; self.opt_unlock = 0
        self.pwr_cr = 0x1000; self.pwr_csr = 0x8
        self.flash_acr = 0; self.flash_pd_unlock = 0; self.flash_on = True
        self.gpio = {
            'A': dict(MODER=0xEBFFFCFF, OTYPER=0, OSPEEDR=0x0C000000, PUPDR=0x24000000, ODR=0, AFR0=0, AFR1=0),
            'B': dict(MODER=0xFFFFFFFF, OTYPER=0, OSPEEDR=0, PUPDR=0, ODR=0, AFR0=0, AFR1=0),
            'C': dict(MODER=0xFFFFFFFF, OTYPER=0, OSPEEDR=0, PUPDR=0, ODR=0, AFR0=0, AFR1=0)}
        self.exti = dict(IMR=0x3F840000, EMR=0, RTSR=0, FTSR=0, SWIER=0, PR=0)
        self.syscfg_exticr = [0, 0, 0, 0]
        self.spi1 = Spi(self, 'SPI1'); self.spi2 = Spi(self, 'SPI2')
        self.adc = Adc(self); self.adc_ccr = 0
        self.i2c1_cr1 = 0
        self.nvic_en = 0; self.nvic_pend = 0; self.nvic_pri = [0] * 32
        self.st_ctrl = 0; self.st_load = 0; self.st_next = None; self.st_pend = False; self.st_pri = 0
        self.scr = 0
        self.active = []          # stack of (exception number, priority)
        self.want = None
        self.prev_levels = self.pin_levels()
        uc = self.uc
        # restore flash image (unicorn memory persists), keep RAM contents (warm reset)
        sp, pc = struct.unpack_from('<II', self.flash, 0)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_PRIMASK, 0)
        uc.reg_write(UC_ARM_REG_XPSR, 0x01000000)
        self.pc = pc & ~1
        self.in_stop = False
        self.pins_changed()

    def oled_reset_pins(self):
        # all GPIO return to reset (analog) state while NRST is low; PB2 releases the latch
        self.gpio['B']['MODER'] = 0xFFFFFFFF
        self.gpio['B']['ODR'] = 0
        self.spi1.reset(); self.spi2.reset()
        self.pins_changed()

    def power_on_reset(self):
        self.fram.powered_at = self.now_s() + 0.0034   # RC 68R*10uF, ~5 tau to settle
        self.fram.asleep = False; self.fram.wake_started = None; self.fram.selected = False
        self.uc.mem_write(0x20000000, bytes(0x5000))     # SRAM contents are lost with the supply
        self.csr_flags = bit(27) | bit(26)                # PORRSTF | PINRSTF
        self.mcu_reset('power-on')

    # ---------------- Q5 board power (U7 soft latch) ----------------
    def hold_level(self):
        return self.board_state == 'on' and self.drives('B', 2) == 1

    def sources(self):
        """U7 ON = VBUS diode OR COUNT key (SYS) OR PWR_HOLD (only while powered)."""
        return self.usb or self.sw1 or self.hold_level()

    def board_on(self, cause):
        self.board_state = 'on'
        self.power_events.append((round(self.now_s(), 6), 'on', cause))
        self.ev('board', 'on')
        self.power_on_reset()

    def board_off(self):
        self.board_state = 'off'
        self.power_events.append((round(self.now_s(), 6), 'off', 'supply collapsed'))
        self.ev('board', 'off'); self.ev('mcu', 'off'); self.ev('adc', 'off'); self.ev('fram', 'off')
        if self.oled.powered and (self.oled.display_on or self.oled.pump):
            self.violation('OLED', 'board supply collapsed with the module display/pump on')
        if self.fram.selected:
            self.violation('FRAM', 'board supply collapsed during an FRAM transaction')
        if self.oled.powered or self.oled.switch_on_at is not None:
            self.oled.powered = False; self.oled.switch_on_at = None; self.oled.reset_state()
            self.oled.power_cycles += 1; self.ev('oled', 'off')
        self.in_stop = False; self.wfi_pending = None
        self.st_ctrl = 0; self.st_next = None; self.st_pend = False
        self.adc.reset(); self.spi1.reset(); self.spi2.reset()

    def update_board_power(self):
        if not hasattr(self, 'board_state'):
            return
        src = self.sources()
        if self.board_state == 'on' and not src:
            self.collapse_token += 1
            self.board_state = 'collapsing'
            delay = COLLAPSE_STOP if self.in_stop else COLLAPSE_RUN
            self.at(self.now_s() + delay, 'collapse', self.collapse_token)
        elif self.board_state == 'collapsing' and src and (self.usb or self.sw1 or self.drives('B', 2) == 1):
            self.collapse_token += 1; self.board_state = 'on'           # U7 re-enabled before BOR
        elif self.board_state == 'off' and (self.usb or self.sw1):
            self.collapse_token += 1; self.board_state = 'starting'
            self.at(self.now_s() + U7_TON + BOOT_TEMPO, 'start', self.collapse_token)
        elif self.board_state == 'starting' and not (self.usb or self.sw1):
            self.collapse_token += 1; self.board_state = 'off'          # press too short: U7 never latched

    # ---------------- scenario ----------------
    def at(self, t, action, *args):
        self.scenario.append((t, action, args))
        self.scenario.sort(key=lambda e: e[0])

    def press(self, t, key, hold, bounce_ms=3.0, bounces=6):
        """Schedule a bouncy press of key ('inc' or 'rst') at t seconds held for hold seconds."""
        r = self.rng
        edges = sorted(r.uniform(0, bounce_ms / 1000) for _ in range(bounces))
        state = False
        for e in edges:
            state = not state
            self.at(t + e, 'key', key, state)
        self.at(t + bounce_ms / 1000 + 1e-4, 'key', key, True)
        edges = sorted(r.uniform(0, bounce_ms / 1000) for _ in range(bounces))
        state = True
        for e in edges:
            state = not state
            self.at(t + hold + e, 'key', key, state)
        self.at(t + hold + bounce_ms / 1000 + 1e-4, 'key', key, False)

    def next_scenario_cyc(self):
        return self.scenario[0][0] * HZ if self.scenario else float('inf')

    def run_scenario_events(self):
        while self.scenario and self.scenario[0][0] * HZ <= self.cyc + 1e-9:
            t, action, args = self.scenario.pop(0)
            if action == 'key':
                key, state = args
                if key == 'inc': self.sw1 = state
                else: self.sw2 = state
                self.pins_changed()
            elif action == 'nrst' and self.board_state not in ('on', 'collapsing'):
                self.trace.append((round(self.now_s(), 6), 'NRST pulse on an unpowered board (no effect)'))
            elif action == 'nrst':
                self.trace.append((round(self.now_s(), 6), 'NRST pulse'))
                self.oled_reset_pins()
                self.mcu_reset('NRST')
                raise _Restart()
            elif action == 'nrst_low':
                self.trace.append((round(self.now_s(), 6), 'NRST held low'))
                self.nrst_held = True
                self.oled_reset_pins()
                self.gpio['A']['MODER'] = 0xFFFFFFFF; self.gpio['A']['PUPDR'] = 0
                self.pins_changed()
                self.ev('mcu', 'reset')
                raise _Restart()
            elif action == 'nrst_high' and self.board_state not in ('on', 'collapsing'):
                self.trace.append((round(self.now_s(), 6), 'NRST released on an unpowered board'))
                self.nrst_held = False
            elif action == 'nrst_high':
                self.trace.append((round(self.now_s(), 6), 'NRST released'))
                self.nrst_held = False
                self.mcu_reset('NRST')
                raise _Restart()
            elif action == 'vlogic':
                self.vlogic = args[0]
            elif action == 'vbat':
                self.vbat = args[0]
            elif action == 'charge':
                self.charge = args[0]; self.pins_changed()
            elif action == 'usb':
                self.trace.append((round(self.now_s(), 6), 'USB ' + ('connected' if args[0] else 'removed')))
                self.usb = args[0]; self.pins_changed()
            elif action == 'collapse':
                if args[0] == self.collapse_token and self.board_state == 'collapsing':
                    self.board_off(); raise _Restart()
            elif action == 'start':
                if args[0] == self.collapse_token and self.board_state == 'starting':
                    self.board_on('USB' if self.usb else 'COUNT key'); raise _Restart()
            elif action == 'call':
                args[0](self)

    # ---------------- pins ----------------
    def moder(self, port, pin): return (self.gpio[port]['MODER'] >> (2 * pin)) & 3

    def afn(self, port, pin):
        reg = self.gpio[port]['AFR0'] if pin < 8 else self.gpio[port]['AFR1']
        return (reg >> (4 * (pin % 8))) & 15

    def drives(self, port, pin):
        """Return 1/0 if the MCU actively drives the pin, None if released."""
        m = self.moder(port, pin)
        g = self.gpio[port]
        if m == 1:
            level = (g['ODR'] >> pin) & 1
            if (g['OTYPER'] >> pin) & 1 and level: return None     # open drain released
            return level
        if m == 2:
            return self.af_level(port, pin)
        return None

    def af_level(self, port, pin):
        # SPI outputs: SCK idles at CPOL, MOSI holds last bit; treat as driven low/high accordingly
        if port == 'B' and pin in (13, 15) and self.afn('B', pin) == 0:
            return 0 if pin == 13 else 1
        if port == 'B' and pin in (3, 5) and self.afn('B', pin) == 0:
            return 0 if pin == 3 else 1
        if port == 'B' and pin == 4:
            return None
        return 0

    def gpio_level(self, port, pin):
        d = self.drives(port, pin)
        if d is not None: return d
        # external pulls on nets
        if port == 'A' and pin == 0: return 0 if self.sw1 else 1          # R17 pull-up; Q5 NMOS pulls low while SW1 closes SYS-K1
        if port == 'A' and pin == 1: return 1 if self.sw2 else 0          # R18 pull-down, SW2 to VLOGIC
        if port == 'A' and pin in (5, 6):                                 # BQ25185 STAT1/STAT2 open drain
            low = self.usb and ((pin == 5 and self.charge == 'fault') or (pin == 6 and self.charge == 'charging'))
            if low: return 0
            pupd = (self.gpio[port]['PUPDR'] >> (2 * pin)) & 3
            if pupd != 1: self.note('STAT input read without pull-up (floating)')
            return 1 if pupd == 1 else 0
        if port == 'B' and pin == 2: return 0                             # PWR_HOLD released: D3 anode floats, R35 pulls ON low
        if port == 'B' and pin == 0: return 0                             # R25 pull-down
        if port == 'B' and pin == 1: return 0                             # R24 pull-down
        if port == 'B' and pin == 8: return 1                             # R33 pull-up to VFRAM
        if port == 'B' and pin == 12: return 1 if self.oled.powered else 0  # R29 to switched supply
        pupd = (self.gpio[port]['PUPDR'] >> (2 * pin)) & 3
        return 1 if pupd == 1 else 0

    def pin_levels(self):
        return {(p, n): self.gpio_level(p, n) for p, n in (('A', 0), ('A', 1), ('B', 0), ('B', 1), ('B', 2), ('B', 8), ('B', 12), ('B', 14))}

    def pins_changed(self):
        levels = self.pin_levels()
        prev = getattr(self, 'prev_levels', levels)
        # EXTI on PA0/PA1 (input buffer enabled only when not analog)
        for line in (0, 1):
            a, b = prev[('A', line)], levels[('A', line)]
            if a != b and self.moder('A', line) != 3 and (self.syscfg_exticr[0] >> (4 * line)) & 15 == 0:
                rising = b > a
                if (rising and self.exti['RTSR'] >> line & 1) or (not rising and self.exti['FTSR'] >> line & 1):
                    if self.exti['IMR'] >> line & 1:
                        self.exti['PR'] |= bit(line)
        # FRAM chip select edges
        if prev[('B', 8)] != levels[('B', 8)]:
            if levels[('B', 8)] == 0: self.fram.cs_fall()
            else: self.fram.cs_rise()
        self.prev_levels = levels
        if prev[('B', 2)] != levels[('B', 2)]:
            self.ev('hold', levels[('B', 2)])
        self.update_board_power()
        self.oled.update_power()
        self.check_oled_backpower()
        self.update_irq_lines()

    def check_oled_backpower(self):
        if self.oled.powered or self.oled.switch_on_at is not None:
            return
        for pin, name in ((12, 'CS'), (13, 'SCK'), (14, 'DC'), (15, 'MOSI'), (0, 'RES')):
            if self.drives('B', pin) == 1:
                self.violation('OLED', f'{name} (PB{pin}) driven high while module unpowered')

    # ---------------- SPI routing ----------------
    def spi_exchange(self, spi, mosi):
        if spi is self.spi2:
            ok = self.moder('B', 13) == 2 and self.afn('B', 13) == 0 and self.moder('B', 15) == 2 and self.afn('B', 15) == 0
            cs = self.gpio_level('B', 12)
            dc = self.gpio_level('B', 14)
            if not ok:
                self.note('SPI2 byte with SCK/MOSI not routed to AF0')
            elif cs == 0:
                if self.spi2.cr1 & 3 not in (0, 3):
                    self.violation('OLED', 'SPI mode not 0/3')
                self.oled.byte(mosi, dc)
            else:
                self.note('SPI2 byte with OLED CS high')
            return 0xFF
        # SPI1 -> FRAM
        ok = all(self.moder('B', p) == 2 and self.afn('B', p) == 0 for p in (3, 4, 5))
        if not ok:
            self.note('SPI1 byte with pins not routed')
            return 0xFF
        if self.gpio_level('B', 8) != 0:
            self.note('SPI1 byte with FRAM CS high')
            return 0xFF
        return self.fram.xfer(mosi)

    # ---------------- ADC board input ----------------
    def board_adc_sample(self, chselr, reg_at):
        vrefint = 1.224
        if not self.adc_ccr & bit(22):
            self.violation('ADC', 'VREFINT channel sampled with VREFEN clear')
        if reg_at is None or (self.cyc - reg_at) < 0.003 * HZ:
            self.note('ADC sample before 3 ms VREFINT/regulator settle')
        if chselr == bit(17):
            raw = int(round(vrefint * 4095 / self.vlogic + self.rng.uniform(-1.5, 1.5)))
        elif chselr == bit(4):
            if self.moder('A', 4) != 3:
                self.violation('ADC', 'PA4 (VBAT_SENSE) sampled while not in analog mode')
            sys_v = USB_SYS_V if self.usb else self.vbat
            raw = int(round((sys_v / 2) * 4095 / self.vlogic + self.rng.uniform(-1.5, 1.5)))
        else:
            self.violation('ADC', f'unexpected CHSELR {chselr:#x}')
            raw = 0
        return max(0, min(4095, raw))

    # ---------------- interrupts ----------------
    def irq_lines(self):
        lines = 0
        if self.exti['PR'] & 3: lines |= bit(IRQ_EXTI0_1)
        if self.spi2.irq(): lines |= bit(IRQ_SPI2)
        return lines

    def update_irq_lines(self):
        self.nvic_pend |= self.irq_lines()

    def exc_priority(self, n):
        if n == EXC_SYSTICK: return self.st_pri
        return self.nvic_pri[n - 16]

    def pending_exceptions(self):
        """(number, priority) pending and enabled, sorted by priority then number."""
        out = []
        if self.st_pend: out.append((EXC_SYSTICK, self.st_pri))
        en = self.nvic_pend & self.nvic_en
        for i in range(32):
            if en >> i & 1: out.append((16 + i, self.nvic_pri[i]))
        out.sort(key=lambda e: (e[1], e[0]))
        return out

    def current_priority(self):
        return self.active[-1][1] if self.active else 256

    def deliverable(self, check_primask=True):
        p = self.pending_exceptions()
        if not p: return None
        n, pri = p[0]
        if pri >= self.current_priority(): return None
        if check_primask and self.uc.reg_read(UC_ARM_REG_PRIMASK) & 1: return None
        return n

    def enter_exception(self, n, ret_pc):
        uc = self.uc
        sp = uc.reg_read(UC_ARM_REG_SP)
        xpsr = uc.reg_read(UC_ARM_REG_XPSR)
        pad = sp & 4
        sp = (sp - 32 - (4 if pad else 0))
        frame = [uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R12, UC_ARM_REG_LR)]
        frame += [ret_pc, (xpsr & ~0x1FF) | (bit(9) if pad else 0) | 0x01000000]
        uc.mem_write(sp, struct.pack('<8I', *[f & 0xFFFFFFFF for f in frame]))
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, TRAMP | 1)
        if n == EXC_SYSTICK: self.st_pend = False
        else: self.nvic_pend &= ~bit(n - 16)
        self.active.append((n, self.exc_priority(n)))
        vec = struct.unpack_from('<I', self.flash, 4 * n)[0]
        self.cyc += 15   # exception entry latency
        if sp < 0x20000000 + 0x970:
            self.violation('CPU', f'stack overflow into .bss (sp={sp:#x})')
        return vec & ~1

    def exception_return(self):
        uc = self.uc
        sp = uc.reg_read(UC_ARM_REG_SP)
        r0, r1, r2, r3, r12, lr, pc, xpsr = struct.unpack('<8I', uc.mem_read(sp, 32))
        sp += 32 + (4 if xpsr & bit(9) else 0)
        for reg, v in ((UC_ARM_REG_R0, r0), (UC_ARM_REG_R1, r1), (UC_ARM_REG_R2, r2), (UC_ARM_REG_R3, r3),
                       (UC_ARM_REG_R12, r12), (UC_ARM_REG_LR, lr)):
            uc.reg_write(reg, v)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_XPSR, (xpsr & 0xF0000000) | 0x01000000)
        self.active.pop()
        self.cyc += 10
        self.update_irq_lines()
        return pc & ~1

    # ---------------- time ----------------
    def service_timers(self):
        if self.st_next is not None and self.cyc >= self.st_next:
            period = (self.st_load & 0xFFFFFF) + 1
            while self.st_next <= self.cyc:
                self.st_next += period
            self.st_countflag = True
            if self.st_ctrl & 2: self.st_pend = True
        self.spi1.service(); self.spi2.service(); self.adc.service()
        self.oled.tick()
        if self.scenario and self.next_scenario_cyc() <= self.cyc:
            self.run_scenario_events()
        self.update_irq_lines()
        nxt = [t for t in (self.st_next, self.spi1.shift_end if self.spi1.shift is not None else None,
                           self.spi2.shift_end if self.spi2.shift is not None else None,
                           self.adc.done_at, self.adc.cal_at, self.adc.rdy_at) if t is not None]
        nxt.append(self.next_scenario_cyc())
        if self.oled.switch_on_at is not None and not self.oled.powered:
            nxt.append((self.oled.switch_on_at + OLED_TON) * HZ)
        self.next_event = min(nxt) if nxt else float('inf')

    def insn_cost(self, addr):
        c = self.cost_cache.get(addr)
        if c is None:
            data = bytes(self.uc.mem_read(addr, 4))
            ins = next(self.md.disasm(data, addr), None)
            c = 1.0
            if ins is not None:
                m = ins.mnemonic.split('.')[0]; ops = ins.op_str
                if m in ('ldr', 'ldrb', 'ldrh', 'ldrsb', 'ldrsh', 'str', 'strb', 'strh'): c = 2
                elif m == 'push': c = 1 + ops.count(',') + 1
                elif m == 'pop': n = ops.count(',') + 1; c = (3 + n) if 'pc' in ops else (1 + n)
                elif m in ('ldm', 'stm', 'ldmia', 'stmia'): c = 1 + ops.count(',')
                elif m == 'bl': c = 3
                elif m in ('bx', 'blx'): c = 2
                elif m == 'b': c = 2
                elif m.startswith('b') and m not in ('bic', 'bics'):
                    # conditional: backward (loop) assumed taken, forward assumed not taken
                    try:
                        tgt = int(ops.strip('#'), 16); c = 2 if tgt <= addr else 1
                    except ValueError:
                        c = 1.5
                elif m in ('mrs', 'msr', 'dmb', 'dsb', 'isb'): c = 3
                if 0x08000000 <= addr < 0x08020000: c += self.flash_ws_penalty
            self.cost_cache[addr] = c
        return c

    def on_code(self, uc, addr, size, ud):
        self.cyc += self.insn_cost(addr)
        if self.profile is not None:
            self.profile[addr] = self.profile.get(addr, 0) + 1
            if addr == self.profile_arm_at:
                self.profile_armed = True
            elif addr == self.profile_stop_at and self.profile_armed:
                self.profile_end = self.now_s()
                self.profile_final = self.profile
                self.profile = None
        if addr == TRAMP:
            self.stop_reason = 'excret'; uc.emu_stop(); return
        if addr in self.wfi_addrs or (0x20000000 <= addr < 0x20000038 and bytes(uc.mem_read(addr, 2)) == b'\x30\xbf'):
            self.stop_reason = 'wfi'; uc.emu_stop(); return
        if 0x08000000 <= addr < 0x08020000 and not self.flash_on:
            self.violation('FLASH', f'instruction fetch at {addr:#x} while Flash powered down (RUN_PD)')
        if addr == self.panic_addr:
            self.violation('CPU', 'panic() entered')
        if addr == self.default_addr:
            self.violation('CPU', 'Default_Handler (unexpected exception)')
        if self.cyc >= self.next_event:
            self.service_timers()
        if self.nvic_pend or self.st_pend:
            n = self.deliverable()
            if n is not None:
                self.want = n; self.stop_reason = 'irq'; uc.emu_stop()

    def handle_wfi(self, addr):
        """Sleep until an enabled interrupt is pending (PRIMASK ignored for wake)."""
        deep = bool(self.scr & bit(2))
        if deep:
            if self.pwr_cr & bit(1):
                self.violation('PWR', 'Standby selected instead of Stop')
            if self.pwr_cr & bit(13):
                self.violation('PWR', 'DS_EE_KOFF set: Flash would stay off after Stop')
            if not self.in_stop: self.stop_count += 1
            self.in_stop = True
        start = self.cyc
        self.ev('mcu', 'stop' if deep else 'sleep')
        guard = 0
        while self.deliverable(check_primask=False) is None:
            guard += 1
            if deep:
                # Only EXTI (scenario edges) can wake from Stop; clocks stopped.
                t = self.next_scenario_cyc()
                if t > self.until_cyc:
                    self.cyc = max(self.cyc, self.until_cyc)
                    self.wfi_pending = addr
                    self.stop_time += (self.cyc - start) / HZ
                    return None
                self.cyc = max(self.cyc, t)
                self.run_scenario_events()
                self.update_irq_lines()
            else:
                if self.next_event == float('inf'):
                    self.service_timers()
                if self.next_event > self.until_cyc:
                    self.cyc = max(self.cyc, self.until_cyc)
                    self.wfi_pending = addr
                    self.sleep_time += (self.cyc - start) / HZ
                    return None
                self.cyc = max(self.cyc + 1, self.next_event)
                self.service_timers()
            if guard > 10_000_000:
                self.halted = 'sleep guard'; break
        slept = self.cyc - start
        self.ev('mcu', 'run')
        if deep:
            self.stop_time += slept / HZ
            self.in_stop = False
            if not (self.pwr_cr & bit(13)):
                self.flash_on = True    # hardware wakes NVM on Stop exit (DS_EE_KOFF=0)
        else:
            self.sleep_time += slept / HZ
        return addr + 2

    # ---------------- run ----------------
    def profile_between(self, arm_symbol, stop_symbol):
        """Count executed instructions per address from arm_symbol until stop_symbol runs."""
        self.profile = {}
        self.profile_arm_at = self.symbols[arm_symbol] & ~1
        self.profile_stop_at = self.symbols[stop_symbol] & ~1

    def run(self, until_s):
        pc = self.pc
        until = until_s * HZ
        self.until_cyc = until
        self.service_timers()
        if getattr(self, 'wfi_pending', None) is not None and self.board_state in ('on', 'collapsing'):
            addr = self.wfi_pending; self.wfi_pending = None
            try:
                r = self.handle_wfi(addr)
            except _Restart:
                r = self.pc
            if r is None:
                self.pc = addr; return self
            pc = r
        while self.halted is None and self.cyc < until:
            if self.board_state in ('off', 'starting'):
                t = self.next_scenario_cyc()
                if t > until:
                    self.cyc = max(self.cyc, until); break
                self.cyc = max(self.cyc, t)
                try:
                    self.run_scenario_events()
                except _Restart:
                    pass
                pc = self.pc
                continue
            if self.nrst_held:
                t = self.next_scenario_cyc()
                if t == float('inf'):
                    self.halted = 'held in reset'; break
                self.cyc = max(self.cyc, t)
                try:
                    self.run_scenario_events()
                except _Restart:
                    pass
                pc = self.pc
                continue
            self.stop_reason = None
            try:
                self.uc.emu_start(pc | 1, 0xFFFFFFFF, count=5_000_000)
            except _Restart:
                pc = self.pc; continue
            except UcError as e:
                self.violation('CPU', f'emulation fault {e} at pc={self.uc.reg_read(UC_ARM_REG_PC):#x}')
                self.halted = 'fault'; break
            if getattr(self, '_restart', False):
                self._restart = False; pc = self.pc; continue
            pc = self.uc.reg_read(UC_ARM_REG_PC)
            if self.stop_reason == 'wfi':
                try:
                    r = self.handle_wfi(pc)
                except _Restart:
                    pc = self.pc; continue
                if r is None:
                    break
                pc = r
            elif self.stop_reason == 'irq':
                pc = self.enter_exception(self.want, pc)
            elif self.stop_reason == 'excret':
                pc = self.exception_return()
        # ROM DFU does not drive PB2: without USB or a held COUNT key the supply collapses.
        while self.dfu and self.board_state == 'collapsing' and self.next_scenario_cyc() <= until:
            self.cyc = max(self.cyc, self.next_scenario_cyc())
            try:
                self.run_scenario_events()
            except _Restart:
                pass
        self.pc = pc
        return self

    # ---------------- MMIO: APB ----------------
    def clk(self, reg, b, who):
        if not (self.rcc[reg] >> b) & 1:
            self.violation('RCC', f'{who} accessed with clock disabled')
            return False
        return True

    def apb_read(self, uc, off, size, ud):
        a = 0x40000000 + off
        try:
            return self._apb_read(a) & 0xFFFFFFFF
        except _Restart:
            self._restart = True; uc.emu_stop(); return 0

    def _apb_read(self, a):
        if 0x40003800 <= a < 0x40003C00: return self.spi_read(self.spi2, a - 0x40003800, 'APB1ENR', 14)
        if 0x40013000 <= a < 0x40013400: return self.spi_read(self.spi1, a - 0x40013000, 'APB2ENR', 12)
        if a == 0x40007000: return self.pwr_cr
        if a == 0x40007004:
            v = self.pwr_csr & ~bit(2)
            if self.pwr_cr & bit(4):
                thr = [1.85, 2.04, 2.24, 2.44, 2.64, 2.83, 3.05][min((self.pwr_cr >> 5) & 7, 6)]
                if self.vlogic < thr: v |= bit(2)
            return v
        if 0x40010008 <= a < 0x40010018: return self.syscfg_exticr[(a - 0x40010008) // 4]
        if 0x40010400 <= a < 0x40010418:
            return self.exti[['IMR', 'EMR', 'RTSR', 'FTSR', 'SWIER', 'PR'][(a - 0x40010400) // 4]]
        if 0x40012400 <= a < 0x40012800: return self.adc_read(a - 0x40012400)
        if 0x40005400 <= a < 0x40005800:
            return self.i2c1_cr1 if a == 0x40005400 else 0
        self.note(f'unmodelled APB read {a:#x}')
        return 0

    def apb_write(self, uc, off, size, value, ud):
        a = 0x40000000 + off
        try:
            self._apb_write(a, value & 0xFFFFFFFF, size)
        except _Restart:
            self._restart = True; uc.emu_stop()
        self.pins_changed_if_needed()

    def pins_changed_if_needed(self):
        self.update_irq_lines()
        if self.cyc >= self.next_event: self.service_timers()

    def _apb_write(self, a, v, size):
        if 0x40003800 <= a < 0x40003C00: return self.spi_write(self.spi2, a - 0x40003800, v, 'APB1ENR', 14)
        if 0x40013000 <= a < 0x40013400: return self.spi_write(self.spi1, a - 0x40013000, v, 'APB2ENR', 12)
        if a == 0x40007000:
            if not self.clk('APB1ENR', 28, 'PWR'): return
            self.pwr_cr = v; return
        if a == 0x40007004: return
        if 0x40010008 <= a < 0x40010018:
            self.syscfg_exticr[(a - 0x40010008) // 4] = v; return
        if 0x40010400 <= a < 0x40010418:
            k = ['IMR', 'EMR', 'RTSR', 'FTSR', 'SWIER', 'PR'][(a - 0x40010400) // 4]
            if k == 'PR': self.exti['PR'] &= ~v
            else: self.exti[k] = v
            if k == 'PR':
                self.nvic_pend &= ~bit(IRQ_EXTI0_1) if not (self.exti['PR'] & 3) else ~0
            self.update_irq_lines(); return
        if 0x40012400 <= a < 0x40012800:
            r = self.adc_write(a - 0x40012400, v)
            if a - 0x40012400 == 0x08 and not v & bit(28) and not (self.adc.cr & bit(28)):
                self.ev('adc', 'off')
            return r
        if 0x40005400 <= a < 0x40005800:
            if a == 0x40005400: self.i2c1_cr1 = v
            return
        self.note(f'unmodelled APB write {a:#x}')

    def spi_read(self, spi, off, en_reg, en_bit):
        if not self.clk(en_reg, en_bit, spi.name): return 0
        self.service_timers()
        if off == 0: return spi.cr1
        if off == 4: return spi.cr2
        if off == 8: return spi.sr()
        if off == 12:
            v = spi.read_dr(); self.update_irq_lines(); return v
        return 0

    def spi_write(self, spi, off, v, en_reg, en_bit):
        if not self.clk(en_reg, en_bit, spi.name): return
        self.service_timers()
        if off == 0: spi.set_cr1(v)
        elif off == 4: spi.cr2 = v & 0xFF
        elif off == 8:
            if not v & bit(6): spi.ovr = spi.ovr   # OVR is cleared by DR/SR read sequence in HW
        elif off == 12: spi.write_dr(v)
        self.update_irq_lines()
        self.service_timers()

    def adc_read(self, off):
        adc = self.adc
        if off == 0x308: return self.adc_ccr
        if not self.clk('APB2ENR', 9, 'ADC'): return 0
        self.service_timers()
        return {0x00: adc.isr, 0x04: adc.ier, 0x08: adc.cr, 0x0C: adc.cfgr1, 0x10: adc.cfgr2, 0x14: adc.smpr,
                0x28: adc.chselr, 0x40: adc.dr, 0xB4: adc.calfact}.get(off, 0)

    def adc_write(self, off, v):
        adc = self.adc
        if off == 0x308: self.adc_ccr = v; return
        if not self.clk('APB2ENR', 9, 'ADC'): return
        self.service_timers()
        if off == 0x00: adc.isr &= ~v
        elif off == 0x04: adc.ier = v
        elif off == 0x08: adc.write_cr(v)
        elif off == 0x0C:
            if adc.cr & bit(0): self.violation('ADC', 'CFGR1 written while ADEN=1 (ES0292 2.4.2)')
            adc.cfgr1 = v
        elif off == 0x10: adc.cfgr2 = v
        elif off == 0x14: adc.smpr = v
        elif off == 0x28: adc.chselr = v
        self.service_timers()

    # ---------------- MMIO: option bytes (0x1FF80000) ----------------
    def ob_read(self, uc, off, size, ud):
        return int.from_bytes(self.sysmem[off:off + size], 'little')

    def ob_write(self, uc, off, size, v, ud):
        if off != 4 or size != 4:
            self.violation('FLASH', f'unexpected option/system memory write at {0x1FF80000 + off:#x}')
            return
        if self.pecr & 5:
            self.violation('FLASH', 'option-byte write while PELOCK/OPTLOCK set')
            return
        if ((v >> 16) ^ v) & 0xFFFF != 0xFFFF:
            self.violation('FLASH', f'option USER word {v:#010x} lacks its complement')
        self.sysmem[4:8] = struct.pack('<I', v)
        self.option_writes += 1
        self.flash_busy_until = self.cyc + 0.0032 * HZ      # data-EEPROM-style erase+program time
        self.trace.append((round(self.now_s(), 6), f'option USER word {v:#010x} programmed'))

    # ---------------- MMIO: AHB (RCC, FLASH) ----------------
    RCC_OFF = {0x00: 'CR', 0x0C: 'CFGR', 0x24: 'APB2RSTR', 0x28: 'APB1RSTR', 0x2C: 'IOPENR', 0x30: 'AHBENR',
               0x34: 'APB2ENR', 0x38: 'APB1ENR', 0x50: 'CSR'}

    def ahb_read(self, uc, off, size, ud):
        a = 0x40020000 + off
        if 0x40021000 <= a < 0x40021400:
            k = self.RCC_OFF.get(a - 0x40021000)
            if k is None: return 0
            v = self.rcc[k]
            if k == 'CR':
                v = (v & ~(bit(2) | bit(9))) | (bit(2) if v & 1 else 0) | (bit(9) if v & bit(8) else 0)
            if k == 'CFGR':
                v = (v & ~0xC) | ((v & 3) << 2)
            return v
        if 0x40022000 <= a < 0x40022400:
            o = a - 0x40022000
            if o == 0x00: return self.flash_acr
            if o == 0x04: return self.pecr
            if o == 0x18:
                busy = self.cyc < getattr(self, 'flash_busy_until', 0)
                return (bit(0) if busy else 0) | (0 if busy else bit(3))
            if o == 0x1C: return self.optr
            return 0
        self.note(f'unmodelled AHB read {a:#x}')
        return 0

    def ahb_write(self, uc, off, size, v, ud):
        try:
            self._ahb_write(uc, off, size, v, ud)
        except _Restart:
            self._restart = True; uc.emu_stop()

    def _ahb_write(self, uc, off, size, v, ud):
        a = 0x40020000 + off
        if 0x40021000 <= a < 0x40021400:
            k = self.RCC_OFF.get(a - 0x40021000)
            if k is None: return
            old = self.rcc[k]; self.rcc[k] = v
            if k == 'CSR':
                if v & bit(23): self.csr_flags = 0
                self.rcc[k] = (v & 0x00FFFFFF & ~bit(23)) | self.csr_flags
                return
            if k == 'APB2RSTR':
                if old & bit(12) and not v & bit(12): self.spi1.reset()
                if old & bit(9) and not v & bit(9): self.adc.reset()
            if k == 'APB1RSTR':
                if old & bit(14) and not v & bit(14): self.spi2.reset()
            self.update_irq_lines()
            return
        if 0x40022000 <= a < 0x40022400:
            o = a - 0x40022000
            if o == 0x04:   # PECR: locks can be set, OBL_LAUNCH reloads option bytes
                if v & bit(18):
                    if self.pecr & 5:
                        self.violation('FLASH', 'OBL_LAUNCH while PECR/option bytes locked'); return
                    w = struct.unpack_from('<I', self.sysmem, 4)[0]
                    if ((w >> 16) ^ w) & 0xFFFF == 0xFFFF:
                        self.optr = ((w & 0xFFFF) << 16) | (self.optr & 0xFFFF)
                    else:
                        self.optr |= bit(0)    # model an OPTVERR load as invalid
                    self.trace.append((round(self.now_s(), 6), f'OBL_LAUNCH, OPTR={self.optr:#010x}'))
                    self.oled_reset_pins(); self.mcu_reset('OBL'); raise _Restart()
                self.pecr |= v & 7
                return
            if o == 0x0C:   # PEKEYR
                if self.pe_unlock == 0 and v == 0x89ABCDEF: self.pe_unlock = 1
                elif self.pe_unlock == 1 and v == 0x02030405: self.pe_unlock = 2; self.pecr &= ~1
                else: self.pe_unlock = 0
                return
            if o == 0x14:   # OPTKEYR
                if self.pecr & 1: self.violation('FLASH', 'OPTKEYR written while PELOCK set'); return
                if self.opt_unlock == 0 and v == 0xFBEAD9C8: self.opt_unlock = 1
                elif self.opt_unlock == 1 and v == 0x24252627: self.opt_unlock = 2; self.pecr &= ~4
                else: self.opt_unlock = 0
                return
            if o == 0x18: return            # SR flags write-1-to-clear: none modelled set
            if o == 0x08:   # PDKEYR
                if self.flash_pd_unlock == 0 and v == 0x04152637: self.flash_pd_unlock = 1
                elif self.flash_pd_unlock == 1 and v == 0xFAFBFCFD: self.flash_pd_unlock = 2
                else: self.flash_pd_unlock = 0
                return
            if o == 0x00:
                new = v
                old_pd = self.flash_acr & bit(4)
                if (v & bit(4)) and not old_pd:
                    if self.flash_pd_unlock != 2:
                        new &= ~bit(4)
                        self.note('RUN_PD set ignored: PDKEYR not unlocked')
                    else:
                        self.flash_on = False
                if old_pd and not (v & bit(4)):
                    self.flash_pd_unlock = 0      # RM0376 3.6.4: clearing RUN_PD relocks
                    self.flash_on = True
                self.flash_acr = new
                return
            return
        self.note(f'unmodelled AHB write {a:#x}')

    # ---------------- MMIO: GPIO ----------------
    GPIO_OFF = {0x00: 'MODER', 0x04: 'OTYPER', 0x08: 'OSPEEDR', 0x0C: 'PUPDR', 0x14: 'ODR', 0x20: 'AFR0', 0x24: 'AFR1'}

    def gpio_read(self, uc, off, size, ud):
        port = 'ABC'[off // 0x400] if off < 0xC00 else None
        if port is None: return 0
        if not self.clk('IOPENR', 'ABC'.index(port), 'GPIO' + port): return 0
        o = off % 0x400
        if o == 0x10:
            v = 0
            for pin in range(16):
                if self.moder(port, pin) != 3 and self.gpio_level(port, pin): v |= bit(pin)
            return v
        k = self.GPIO_OFF.get(o)
        return self.gpio[port][k] if k else 0

    def gpio_write(self, uc, off, size, v, ud):
        port = 'ABC'[off // 0x400] if off < 0xC00 else None
        if port is None: return
        if not self.clk('IOPENR', 'ABC'.index(port), 'GPIO' + port): return
        o = off % 0x400
        g = self.gpio[port]
        if o == 0x18:
            g['ODR'] = (g['ODR'] | (v & 0xFFFF)) & ~((v >> 16) & ~v & 0xFFFF)
        elif o == 0x28:
            g['ODR'] &= ~(v & 0xFFFF)
        else:
            k = self.GPIO_OFF.get(o)
            if k: g[k] = v
        try:
            self.pins_changed()
        except _Restart:
            self._restart = True; uc.emu_stop()

    # ---------------- MMIO: SCS ----------------
    def scs_read(self, uc, off, size, ud):
        a = 0xE000E000 + off
        if a == 0xE000E010:
            v = self.st_ctrl | (bit(16) if getattr(self, 'st_countflag', False) else 0)
            self.st_countflag = False
            return v
        if a == 0xE000E014: return self.st_load
        if a == 0xE000E018:
            if self.st_next is None: return 0
            return int(max(0, self.st_next - self.cyc)) & 0xFFFFFF
        if a == 0xE000E100: return self.nvic_en
        if a == 0xE000E200: return self.nvic_pend
        if 0xE000E400 <= a < 0xE000E420:
            i = (a - 0xE000E400)
            return sum((self.nvic_pri[i + k] & 0xC0) << (8 * k) for k in range(4))
        if a == 0xE000ED00: return 0x410CC601
        if a == 0xE000ED04: return bit(26) if self.st_pend else 0
        if a == 0xE000ED10: return self.scr
        if a == 0xE000ED20: return (self.st_pri & 0xC0) << 24
        return 0

    def scs_write(self, uc, off, size, v, ud):
        a = 0xE000E000 + off
        if a == 0xE000E010:
            was = self.st_ctrl & 1
            self.st_ctrl = v & 7
            if self.st_ctrl & 1 and not was:
                self.st_next = self.cyc + (self.st_load & 0xFFFFFF) + 1
                self.schedule(self.st_next)
            if not self.st_ctrl & 1:
                self.st_next = None
            return
        if a == 0xE000E014: self.st_load = v & 0xFFFFFF; return
        if a == 0xE000E018:
            if self.st_ctrl & 1:
                self.st_next = self.cyc + (self.st_load & 0xFFFFFF) + 1; self.schedule(self.st_next)
            return
        if a == 0xE000E100: self.nvic_en |= v; self.update_irq_lines(); return
        if a == 0xE000E180: self.nvic_en &= ~v; return
        if a == 0xE000E200: self.nvic_pend |= v; return
        if a == 0xE000E280: self.nvic_pend &= ~v; self.update_irq_lines(); return
        if 0xE000E400 <= a < 0xE000E420:
            i = a - 0xE000E400
            for k in range(size):
                self.nvic_pri[i + k] = (v >> (8 * k)) & 0xC0
            return
        if a == 0xE000ED04:
            if v & bit(25): self.st_pend = False
            if v & bit(26): self.st_pend = True
            return
        if a == 0xE000ED0C:
            if (v >> 16) == 0x05FA and v & bit(2):
                self.trace.append((round(self.now_s(), 6), 'SYSRESETREQ'))
                self.mcu_reset('software'); self._restart = True; uc.emu_stop()
            return
        if a == 0xE000ED10: self.scr = v; return
        if a == 0xE000ED20: self.st_pri = (v >> 24) & 0xC0; return
        if 0xE000ED1C <= a < 0xE000ED24: return

    # ---------------- introspection ----------------
    def ram_u32(self, sym, off=0):
        return struct.unpack('<I', self.uc.mem_read(self.symbols[sym] + off, 4))[0]

    def ram_bytes(self, sym, n, off=0):
        return bytes(self.uc.mem_read(self.symbols[sym] + off, n))


class _Restart(Exception):
    pass


# ----------------------------------------------------------------------------
# helpers for scenarios
# ----------------------------------------------------------------------------
DIGITS = [[0x3e,0x51,0x49,0x45,0x3e],[0x00,0x42,0x7f,0x40,0x00],[0x42,0x61,0x51,0x49,0x46],[0x21,0x41,0x45,0x4b,0x31],
          [0x18,0x14,0x12,0x7f,0x10],[0x27,0x45,0x45,0x45,0x39],[0x3c,0x4a,0x49,0x49,0x30],[0x01,0x71,0x09,0x05,0x03],
          [0x36,0x49,0x49,0x49,0x36],[0x06,0x49,0x49,0x29,0x1e]]
LABELS = {
    'ERR': [0x1f,0x15,0x11,0,0x1f,0x05,0x1a,0,0x1f,0x05,0x1a],
    'MAX': [0x1f,0x02,0x1f,0,0x1e,0x05,0x1e,0,0x1b,0x04,0x1b],
    'RST': [0x1f,0x05,0x1a,0,0x17,0x15,0x1d,0,0x01,0x1f,0x01],
    'LO':  [0x1f,0x10,0x10,0,0x0e,0x11,0x0e,0,0x00,0x00,0x00],
    'CHG': [0x0e,0x11,0x11,0,0x1f,0x04,0x1f,0,0x0e,0x11,0x1d],
    'BAT': [0x1f,0x15,0x0a,0,0x1e,0x05,0x1e,0,0x01,0x1f,0x01],
    'OPT': [0x0e,0x11,0x0e,0,0x1f,0x05,0x02,0,0x01,0x1f,0x01]}


def decode_display(oled):
    """Recover the eight digit cells and status label from GDDRAM (firmware geometry)."""
    if not (oled.powered and oled.display_on and oled.pump):
        return None
    g = oled.gddram
    def px(x, y): return (g[y // 8][x] >> (y % 8)) & 1
    text = ''
    for cell in range(8):
        cols = []
        for dx in range(5):
            x = 16 + cell * 12 + dx * 2
            col = 0
            for row in range(7):
                if px(x, 8 + row * 6): col |= 1 << row
            cols.append(col)
        if cols == [0] * 5:
            text += ' '
        elif cols in DIGITS:
            text += str(DIGITS.index(cols))
        else:
            text += '?'
    label = []
    for x in range(58, 69):
        v = 0
        for row in range(5):
            if px(x, 58 + row): v |= 1 << row
        label.append(v)
    status = next((k for k, v in LABELS.items() if v == label), '' if not any(label) else '??')
    return text.strip(), status


def battery_icon(oled):
    """Bars shown by the page-0 battery icon (None if hidden or display off)."""
    if not (oled.powered and oled.display_on and oled.pump):
        return None
    row = oled.gddram[0][106:126]
    if not any(row):
        return None
    return sum(1 for b in range(4) if row[2 + 4 * b] == 0x7e)


def fram_journal(fram):
    """Decode the 96-slot journal from FRAM bytes with the firmware's record rules."""
    import zlib
    best = None
    valid = 0
    for s in range(96):
        w = struct.unpack_from('<8I', fram.mem, s * 32)
        crc = zlib.crc32(struct.pack('<6I', *w[:6])) & 0xFFFFFFFF
        ok = (w[0] == 0x51443401 and w[2] <= 99999999 and w[3] <= 1 and w[4] == (~w[1] & 0xFFFFFFFF)
              and w[5] == (~w[2] & 0xFFFFFFFF) and w[6] == crc and w[7] == 0x434d5434)
        if ok:
            valid += 1
            if best is None or ((w[1] - best[0]) & 0xFFFFFFFF) and ((w[1] - best[0]) & 0xFFFFFFFF) < 0x80000000:
                best = (w[1], w[2], w[3], s)
    return dict(valid_slots=valid, latest=None if best is None else dict(sequence=best[0], count=best[1], fault=best[2], slot=best[3]))


def summary(sim, label):
    d = decode_display(sim.oled)
    return dict(label=label, t=round(sim.now_s(), 4), halted=sim.halted,
                display=None if d is None else dict(digits=d[0], status=d[1]),
                oled=dict(powered=sim.oled.powered, on=sim.oled.display_on, pump=sim.oled.pump,
                          contrast=sim.oled.contrast, power_cycles=sim.oled.power_cycles),
                fram=dict(asleep=sim.fram.asleep, writes=sim.fram.writes, sleeps=sim.fram.sleep_count,
                          wakes=sim.fram.wake_count, journal=fram_journal(sim.fram)),
                stop_entries=sim.stop_count, stop_time_s=round(sim.stop_time, 3),
                boots=sim.boot_count, dfu=sim.dfu, board=sim.board_state, battery_bars=battery_icon(sim.oled),
                power_events=list(sim.power_events), option_writes=sim.option_writes, optr=hex(sim.optr),
                violations=list(sim.violations))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Boot the firmware image for N seconds and print a summary.')
    ap.add_argument('elf')
    ap.add_argument('--seconds', type=float, default=1.5)
    a = ap.parse_args()
    s = Sim(a.elf)
    s.run(a.seconds)
    print(json.dumps(summary(s, f'boot {a.seconds} s'), indent=1))
