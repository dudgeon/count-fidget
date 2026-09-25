#include <stdint.h>
#include "stm32l072xx.h"
#include "board.h"
extern uint32_t _estack,_sidata,_sdata,_edata,_sbss,_ebss;
int main(void);
void panic(void);
void SysTick_Handler(void);
void EXTI0_1_IRQHandler(void);
void SPI2_IRQHandler(void);
/* State only the ROM bootloader leaves behind: this application never enables
 * the USB clock, never moves the vector table and never remaps memory. */
static int rom_leftovers(void) {
    return SCB->VTOR!=0U || (RCC->APB1ENR&RCC_APB1ENR_USBEN) || (SYSCFG->CFGR1&SYSCFG_CFGR1_MEM_MODE);
}
void Reset_Handler(void) {
    /* A DFU "leave" may arrive with the ROM's USB interrupt enabled and pending:
     * mask interrupts first (main() unmasks them after setup()). */
    __disable_irq();
    /* Then drive PWR_HOLD high so a short COUNT press latches
     * U7 before .data/.bss initialisation (about 2 ms at the 2.1 MHz MSI). */
    RCC->IOPENR|=RCC_IOPENR_GPIOBEN;(void)RCC->IOPENR;
    GPIOB->BSRR=1UL<<BOARD_PWR_HOLD_PIN;
    GPIOB->MODER=(GPIOB->MODER&~(3UL<<(2U*BOARD_PWR_HOLD_PIN)))|(1UL<<(2U*BOARD_PWR_HOLD_PIN));
    /* Entered without a reset (the ROM bootloader's DFU "leave" jumps here with
     * its clocks, USB and vector table still configured): take a clean system
     * reset so setup() always starts from reset-default RCC/NVIC/VTOR state. */
    if(rom_leftovers() || (RCC->CFGR&RCC_CFGR_SWS)!=RCC_CFGR_SWS_MSI)NVIC_SystemReset();
    uint32_t *s=&_sidata;
    for(uint32_t *d=&_sdata;d<&_edata;d++)*d=*s++;
    for(uint32_t *d=&_sbss;d<&_ebss;d++)*d=0;
    (void)main();panic();
}
/* An interrupt the ROM left pending can arrive before Reset_Handler runs: a
 * clean system reset, not a panic, is the recovery for that case. */
void Default_Handler(void){if(rom_leftovers())NVIC_SystemReset();panic();}
/* Exact STM32L072 IRQ enumeration from the pinned ST header. */
__attribute__((section(".isr_vector"),used))
const uintptr_t vector_table[48]={
    [0]=(uintptr_t)&_estack,[1]=(uintptr_t)Reset_Handler,
    [2]=(uintptr_t)Default_Handler,[3]=(uintptr_t)Default_Handler,
    [11]=(uintptr_t)Default_Handler,[14]=(uintptr_t)Default_Handler,
    [15]=(uintptr_t)SysTick_Handler,
    [16+0]=(uintptr_t)Default_Handler,[16+1]=(uintptr_t)Default_Handler,
    [16+2]=(uintptr_t)Default_Handler,[16+3]=(uintptr_t)Default_Handler,
    [16+4]=(uintptr_t)Default_Handler,[16+5]=(uintptr_t)EXTI0_1_IRQHandler,
    [16+6]=(uintptr_t)Default_Handler,[16+7]=(uintptr_t)Default_Handler,
    [16+8]=(uintptr_t)Default_Handler,[16+9]=(uintptr_t)Default_Handler,
    [16+10]=(uintptr_t)Default_Handler,[16+11]=(uintptr_t)Default_Handler,
    [16+12]=(uintptr_t)Default_Handler,[16+13]=(uintptr_t)Default_Handler,
    [16+14]=(uintptr_t)Default_Handler,[16+15]=(uintptr_t)Default_Handler,
    [16+16]=(uintptr_t)Default_Handler,[16+17]=(uintptr_t)Default_Handler,
    [16+18]=(uintptr_t)Default_Handler,[16+19]=(uintptr_t)Default_Handler,
    [16+20]=(uintptr_t)Default_Handler,[16+21]=(uintptr_t)Default_Handler,
    [16+22]=(uintptr_t)Default_Handler,[16+23]=(uintptr_t)Default_Handler,
    [16+24]=(uintptr_t)Default_Handler,[16+25]=(uintptr_t)Default_Handler,
    [16+26]=(uintptr_t)SPI2_IRQHandler,[16+27]=(uintptr_t)Default_Handler,
    [16+28]=(uintptr_t)Default_Handler,[16+29]=(uintptr_t)Default_Handler,
    [16+30]=(uintptr_t)Default_Handler,[16+31]=(uintptr_t)Default_Handler
};
