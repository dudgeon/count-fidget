ENTRY(Reset_Handler)
MEMORY {
  FLASH (rx) : ORIGIN = 0x08000000, LENGTH = 64K
  RAM (rwx) : ORIGIN = 0x20000000, LENGTH = 20K
}
_estack = ORIGIN(RAM) + LENGTH(RAM);
SECTIONS {
  .isr_vector : { KEEP(*(.isr_vector)) } > FLASH
  .text : { *(.text*) *(.rodata*) KEEP(*(.init)) KEEP(*(.fini)) } > FLASH
  .ARM.extab : { *(.ARM.extab*) } > FLASH
  .ARM.exidx : { __exidx_start = .; *(.ARM.exidx*) __exidx_end = .; } > FLASH
  .data : ALIGN(4) { . = ALIGN(4); _sdata = .; *(.data*) . = ALIGN(4); _sramfunc = .; KEEP(*(.ramfunc*)) _eramfunc = .; . = ALIGN(4); _edata = .; } > RAM AT> FLASH
  _sidata = LOADADDR(.data);
  ASSERT((_sidata & 3) == 0, "Initialized RAM load source must be word aligned")
  .bss (NOLOAD) : { . = ALIGN(4); _sbss = .; *(.bss*) *(COMMON) . = ALIGN(4); _ebss = .; } > RAM
  .noinit (NOLOAD) : { . = ALIGN(4); *(.noinit*) . = ALIGN(4); } > RAM
  /DISCARD/ : { *(.comment) *(.note*) }
  ASSERT(_ebss <= _estack - 4096, "Q4 requires at least4KiB unallocated stack margin")
}
