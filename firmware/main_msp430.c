/* Q2 LCD verification candidate, MSP430FR4133IG48R (48 pin).
 * The submitted Q1 images remain frozen. This candidate requires corrected LCD
 * bias hardware and waveform/temperature qualification before any release.
 */
#include <msp430.h>
#include <stdint.h>
#include <stdbool.h>
#include "counter.h"
#include "lcd_de188.h"

#define BUTTONS (BIT0 | BIT1)
#define FRAM_PASSWORD 0xA500U
#define JOURNAL ((volatile uint16_t *)0x1800U)
static Counter c;
static Record shadow[2];
static volatile uint32_t milliseconds;
static volatile uint16_t fraction;
static volatile uint8_t tick_running;
static bool display_on;

/* INFO FRAM 0x1800..0x181f is excluded from normal startup initialization and
 * the application HEX. Factory procedure clears it once; firmware updates
 * preserve it. Reads and writes use volatile aligned 16-bit accesses. */
static void load_journal(void) {
    for (unsigned s=0;s<2;s++) for(unsigned w=0;w<JOURNAL_WORDS;w++)
        shadow[s].words[w]=JOURNAL[s*JOURNAL_WORDS+w];
}
static bool write_word(void *unused,unsigned slot,unsigned word,uint16_t value) {
    (void)unused;
    unsigned index=slot*JOURNAL_WORDS+word;
    SYSCFG0=FRAM_PASSWORD | PFWP; /* program protected, data writable */
    __asm__ volatile ("" ::: "memory");
    JOURNAL[index]=value;
    __asm__ volatile ("" ::: "memory");
    SYSCFG0=FRAM_PASSWORD | PFWP | DFWP;
    if (JOURNAL[index]!=value) return false;
    shadow[slot].words[word]=value;
    return true;
}
static void set_segments(const uint8_t d[16]) {
    volatile uint8_t *const reg[8]={&LCDM4,&LCDM5,&LCDM6,&LCDM7,&LCDM8,&LCDM9,&LCDM12,&LCDM13};
    for(unsigned i=0;i<8;i++) {
        *reg[i]=(uint8_t)(d[2*i]|(d[2*i+1]<<4));
    }
}
static void lcd_start(void) {
    LCDCTL0=0;
    SYSCFG2 |= LCDPCTL; /* disconnect digital drivers on bias/pump pins */
    LCDPCTL0=0xFF0FU; /* L0..3 COM; L8..15 SEG */
    LCDPCTL1=0x0F0FU; /* L16..19 and L24..27 SEG */
    LCDPCTL2=0;
    LCDCSSEL0=0x000FU;LCDCSSEL1=0;LCDCSSEL2=0;
    LCDMEMCTL=LCDCLRM|LCDCLRBM;
    LCDM0=0x21;LCDM1=0x84; /* one-hot COM assignments */
    /* SLAU445I mode 2: VDD=3.0 V, internal 1/3 bias; requires the pump
     * capacitor AND 100 nF reservoirs at R13/R23/R33 (missing on Q1 PCB).
     * REFO 32768 / 8 / 16 / (2*4) = 32 Hz nominal frame rate.
     * LCD4MUX already includes LCDSON in TI support 1.212; explicit for clarity. */
    LCDVCTL=LCDSELVDD|LCDCPEN|(LCDCPFSEL0|LCDCPFSEL1|LCDCPFSEL2|LCDCPFSEL3);
    LCDCTL0=LCDSSEL__ACLK|LCDDIV__8|LCD4MUX|LCDON|LCDSON;
    display_on=true;
}
static void lcd_stop(void) {
    LCDCTL0 &= ~LCDSON;
    LCDCTL0=0;LCDVCTL=0;
    /* Every common and segment changes to GPIO output LOW, so there is
     * no intentional DC differential across the blank glass while asleep. */
    P2OUT=0;P3OUT=0;P6OUT=0;P7OUT=0;
    LCDPCTL0=0;LCDPCTL1=0;LCDPCTL2=0;
    SYSCFG2 &= ~LCDPCTL;
    display_on=false;
}
static void tick_start(void) {
    TA0CCR0=32;TA0CCTL0=CCIE;
    TA0CTL=TASSEL__ACLK|MC__UP|TACLR;
    tick_running=1;
}
static uint32_t now(void) {
    __disable_interrupt();uint32_t t=milliseconds;__enable_interrupt();return t;
}
static void arm_edges(void) {
    /* A high pin arms falling (press); a low pin arms rising (release). */
    P1IES=(P1IES & ~BUTTONS) | (P1IN & BUTTONS);
}
void __attribute__((interrupt(PORT1_VECTOR))) port1_isr(void) {
    P1IFG &= ~BUTTONS;
    arm_edges();
    if (!tick_running) tick_start();
    __bic_SR_register_on_exit(LPM4_bits);
}
void __attribute__((interrupt(TIMER0_A0_VECTOR))) timer0_isr(void) {
    ++milliseconds;
    fraction+=232U; /* 33 REFO cycles = 1 ms plus 232/32768 ms */
    if(fraction>=32768U){fraction-=32768U;++milliseconds;}
    __bic_SR_register_on_exit(LPM4_bits);
}
int main(void) {
    WDTCTL=WDTPW|WDTHOLD;
    P1OUT=0;P2OUT=0;P3OUT=0;P4OUT=0;P5OUT=0;P6OUT=0;P7OUT=0;
    P1DIR=(uint8_t)~BUTTONS;P2DIR=0xFF;P3DIR=0xFF;P4DIR=0xFF;
    P5DIR=0xFF;P6DIR=0xFF;P7DIR=0xFF;
    P1REN=0;P1SEL0=0;
    /* Reset DCO configuration supplies the CPU; debounce and LCD timing use
     * REFO independently, avoiding dependence on an external crystal. */
    CSCTL4=(CSCTL4 & ~SELA)|SELA__REFOCLK;
    SYSCFG0=FRAM_PASSWORD|PFWP|DFWP;
    PM5CTL0 &= ~LOCKLPM5;
    load_journal();
    uint32_t saved,sequence;unsigned slot;
    (void)journal_load(shadow,&saved,&sequence,&slot);
    counter_init(&c,saved,0);
    arm_edges();P1IFG &= ~BUTTONS;P1IE |= BUTTONS;
    tick_start();lcd_start();
    uint8_t lines[16];lcd_de188_encode(c.count,lines);set_segments(lines);
    __enable_interrupt();
    for(;;) {
        uint32_t t=now();
        uint8_t raw=(uint8_t)(~P1IN & BUTTONS);
        counter_sample(&c,(raw&BIT0)!=0,(raw&BIT1)!=0,t);
        if(c.dirty) {
            if(journal_save(shadow,c.count,write_word,0)) c.dirty=false;
            else { /* Keep the previous committed display; retry next tick. */
                __bis_SR_register(LPM3_bits|GIE);continue;
            }
        }
        if(c.awake) {
            if(!display_on)lcd_start();
            lcd_de188_encode(c.count,lines);set_segments(lines);
            __bis_SR_register(LPM3_bits|GIE);
        } else {
            bool settled=c.increment.stable==c.increment.candidate && c.reset.stable==c.reset.candidate;
            if(!settled){__bis_SR_register(LPM3_bits|GIE);continue;}
            __disable_interrupt();
            /* Recheck the input after the last sample: an intervening edge
             * must be processed before entering deep sleep. Do not clear a
             * pending edge here. */
            if((uint8_t)(~P1IN & BUTTONS)!=raw || (P1IFG & BUTTONS)) {
                __enable_interrupt();continue;
            }
            if(display_on)lcd_stop();
            TA0CTL=MC__STOP;TA0CCTL0=0;tick_running=0;
            arm_edges();
            __bis_SR_register(LPM4_bits|GIE);
        }
    }
}
