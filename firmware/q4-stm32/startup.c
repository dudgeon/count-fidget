#include <stdint.h>
extern uint32_t _estack,_sidata,_sdata,_edata,_sbss,_ebss;
int main(void);
void panic(void);
void SysTick_Handler(void);
void EXTI0_1_IRQHandler(void);
void I2C1_IRQHandler(void);
void SPI2_IRQHandler(void);
void Reset_Handler(void) {
    uint32_t *s=&_sidata;
    for(uint32_t *d=&_sdata;d<&_edata;d++)*d=*s++;
    for(uint32_t *d=&_sbss;d<&_ebss;d++)*d=0;
    (void)main();panic();
}
void Default_Handler(void){panic();}
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
    [16+22]=(uintptr_t)Default_Handler,[16+23]=(uintptr_t)I2C1_IRQHandler,
    [16+24]=(uintptr_t)Default_Handler,[16+25]=(uintptr_t)Default_Handler,
    [16+26]=(uintptr_t)SPI2_IRQHandler,[16+27]=(uintptr_t)Default_Handler,
    [16+28]=(uintptr_t)Default_Handler,[16+29]=(uintptr_t)Default_Handler,
    [16+30]=(uintptr_t)Default_Handler,[16+31]=(uintptr_t)Default_Handler
};
