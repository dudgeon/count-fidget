/* Unreleased Q3 OLED candidate. MSP430FR4133IG48R; never flash onto Q1/Q2.
 * Power and display parameters require the coordinated Q3 hardware. */
#include <msp430.h>
#include <stdbool.h>
#include <stdint.h>
#include "counter.h"
#include "oled.h"
#include "input.h"

#define BUTTONS (BIT0|BIT1)
#define OLED_ENABLE BIT2 /* P1.2, physical pin24, active HIGH */
#define OLED_RESET BIT3  /* P1.3, physical pin23, active LOW */
#define OLED_BUS_PINS (BIT2|BIT3) /* P5.2 pin28 SDA, P5.3 pin27 SCL */
#define JOURNAL ((volatile uint16_t *)0x1800U)
#define INPUT_FAULT_WORD ((volatile uint16_t *)0x1820U)
#define FRAM_PASSWORD 0xa500U
static Counter counter;
static Record shadow[2];
static Oled display;
static InputQueue inputs;
static InputState input_state;
static volatile uint32_t milliseconds;
static volatile uint16_t fraction;
static volatile uint8_t tick_running;
static volatile uint8_t tx[OLED_TX_MAX], tx_length, tx_position;
static volatile uint8_t bus_status; /* 0 idle, 1 transmitting, 2 success, 3 error */
static uint32_t bus_started;

static void load_journal(void) {
    for(unsigned s=0;s<2;s++)for(unsigned w=0;w<JOURNAL_WORDS;w++)
        shadow[s].words[w]=JOURNAL[s*JOURNAL_WORDS+w];
}
static uint16_t read_fault_word(void *unused) { (void)unused;return *INPUT_FAULT_WORD; }
static bool write_fault_word(void *unused,uint16_t value) {
    (void)unused;
    SYSCFG0=FRAM_PASSWORD|PFWP;
    __asm__ volatile ("" ::: "memory");
    *INPUT_FAULT_WORD=value;
    __asm__ volatile ("" ::: "memory");
    SYSCFG0=FRAM_PASSWORD|PFWP|DFWP;
    return *INPUT_FAULT_WORD==value;
}
static bool write_word(void *unused,unsigned slot,unsigned word,uint16_t value) {
    (void)unused;unsigned index=slot*JOURNAL_WORDS+word;
    SYSCFG0=FRAM_PASSWORD|PFWP;
    __asm__ volatile ("" ::: "memory");
    JOURNAL[index]=value;
    __asm__ volatile ("" ::: "memory");
    SYSCFG0=FRAM_PASSWORD|PFWP|DFWP;
    if(JOURNAL[index]!=value)return false;
    shadow[slot].words[word]=value;return true;
}
static void power(bool enabled) {
    if(enabled)P1OUT|=OLED_ENABLE;else P1OUT&=~OLED_ENABLE;
}
static void reset(bool asserted) {
    if(asserted)P1OUT&=~OLED_RESET;else P1OUT|=OLED_RESET;
}
static void bus_abort(void) {
    UCB0IE=0;UCB0CTLW0|=UCSWRST;bus_status=0;
    /* A reset or physical short may hold SDA low. No polling loop here:
     * the state machine backs off and counter/journal operation continues. */
}
static bool bus_start(const uint8_t *data,uint8_t length,uint32_t now) {
    if(!length || length>OLED_TX_MAX || bus_status==1)return false;
    UCB0IE=0;
    UCB0CTLW0=UCSWRST|UCMST|UCMODE_3|UCSYNC|UCSSEL__SMCLK|UCTR;
    UCB0CTLW1=UCASTP_2; /* Hardware STOP after the exact transmitted byte count. */
    UCB0BRW=16; /* Nominal 1.048576 MHz / 16 = 65.536 kHz, below 400 kHz max. */
    UCB0I2CSA=OLED_ADDRESS;UCB0TBCNT=length;
    tx_length=length;tx_position=0;
    for(unsigned i=0;i<length;i++)tx[i]=data[i];
    P5SEL0|=OLED_BUS_PINS;
    UCB0CTLW0&=~UCSWRST;
    if((P5IN&OLED_BUS_PINS)!=OLED_BUS_PINS || (UCB0STATW&UCBBUSY)) {
        bus_abort();return false;
    }
    UCB0IFG=0;bus_started=now;bus_status=1;
    UCB0IE=UCTXIE0|UCSTPIE|UCNACKIE|UCALIE;
    UCB0CTLW0|=UCTXSTT;
    return true;
}
static OledBusResult bus_poll(uint32_t now) {
    uint8_t status=bus_status;
    if(status==2){bus_abort();return OLED_BUS_OK;}
    if(status==3 || status==0 || (uint32_t)(now-bus_started)>=OLED_BUS_TIMEOUT_MS) {
        bus_abort();return OLED_BUS_ERROR;
    }
    return OLED_BUS_BUSY;
}
static uint32_t now(void);
static const OledHal hal={power,reset,bus_start,bus_poll,bus_abort,now};
void __attribute__((interrupt(USCI_B0_VECTOR))) i2c_isr(void) {
    switch(UCB0IV) {
    case USCI_I2C_UCALIFG:
    case USCI_I2C_UCNACKIFG:
        UCB0IE=0;UCB0CTLW0|=UCSWRST;bus_status=3;
        __bic_SR_register_on_exit(LPM4_bits);break;
    case USCI_I2C_UCSTPIFG:
        UCB0IE=0;bus_status=(tx_position==tx_length)?2:3;
        __bic_SR_register_on_exit(LPM4_bits);break;
    case USCI_I2C_UCTXIFG0:
        if(tx_position<tx_length)UCB0TXBUF=tx[tx_position++];
        else UCB0IE&=~UCTXIE0;
        break;
    default: break;
    }
}
static void tick_start(void) {
    TA0CCR0=32;TA0CCTL0=CCIE;
    TA0CTL=TASSEL__ACLK|MC__UP|TACLR;tick_running=1;
}
static uint32_t now(void) {
    __disable_interrupt();uint32_t t=milliseconds;__enable_interrupt();return t;
}
static void arm_edges(void) {
    P1IES=(P1IES&~BUTTONS)|(P1IN&BUTTONS);
}
void __attribute__((interrupt(PORT1_VECTOR))) port1_isr(void) {
    P1IFG&=~BUTTONS;arm_edges();
    /* Edge samples close the race between an awake timer tick and LPM4 entry;
     * repeated timer samples still establish the full debounce interval. */
    input_push(&inputs,(uint8_t)(~P1IN&BUTTONS),milliseconds);
    if(!tick_running)tick_start();
    __bic_SR_register_on_exit(LPM4_bits);
}
void __attribute__((interrupt(TIMER0_A0_VECTOR))) timer0_isr(void) {
    ++milliseconds;fraction+=232U;
    if(fraction>=32768U){fraction-=32768U;++milliseconds;}
    input_push(&inputs,(uint8_t)(~P1IN&BUTTONS),milliseconds);
    __bic_SR_register_on_exit(LPM4_bits);
}
int main(void) {
    WDTCTL=WDTPW|WDTHOLD;
    P1OUT=0;P2OUT=0;P3OUT=0;P4OUT=0;P5OUT=0;P6OUT=0;P7OUT=0;
    P1DIR=(uint8_t)~BUTTONS;P2DIR=0xff;P3DIR=0xff;P4DIR=0xff;
    P5DIR=(uint8_t)~OLED_BUS_PINS;P6DIR=0xff;P7DIR=0xff;
    P1REN=0;P5REN=0;P1SEL0=0;P5SEL0=0;
    LCDCTL0=0;LCDVCTL=0;LCDPCTL0=0;LCDPCTL1=0;LCDPCTL2=0;
    SYSCFG2&=~LCDPCTL;
    /* Explicit 32*REFO nominal DCO/FLL. No oscillator-lock wait can stall
     * button sampling. Serial starts only after the timed reset interval. */
    __bis_SR_register(SCG0);
    CSCTL3=SELREF__REFOCLK;CSCTL0=0;CSCTL1=DCORSEL_0;
    CSCTL2=FLLD__1|31;CSCTL4=SELA__REFOCLK|SELMS__DCOCLKDIV;
    CSCTL5=0;__bic_SR_register(SCG0);
    SYSCFG0=FRAM_PASSWORD|PFWP|DFWP;PM5CTL0&=~LOCKLPM5;
    load_journal();uint32_t saved,sequence;unsigned slot;
    (void)journal_load(shadow,&saved,&sequence,&slot);
    counter_init(&counter,saved,0);uint32_t committed=saved;
    input_state.fault=*INPUT_FAULT_WORD!=0xffffU;input_state.reset_requested=false;
    oled_init(&display,&hal);
    arm_edges();P1IFG&=~BUTTONS;P1IE|=BUTTONS;
    input_push(&inputs,(uint8_t)(~P1IN&BUTTONS),0);tick_start();
    __enable_interrupt();
    for(;;) {
        uint32_t t=now();uint8_t raw=(uint8_t)(~P1IN&BUTTONS);
        for(unsigned n=0;n<8;n++) {
            InputSample sample;__disable_interrupt();
            InputResult result=input_take(&inputs,&sample);__enable_interrupt();
            if(result==INPUT_EMPTY)break;
            input_apply(&input_state,&counter,result,&sample);
        }
        /* An explicit information-FRAM marker preserves an input-history gap
         * across reboot. The existing version-1 counter journal is unchanged. */
        input_persist_fault(&input_state,read_fault_word,write_fault_word,0);
        if(counter.dirty && journal_save(shadow,counter.count,write_word,0)) {
            committed=counter.count;counter.dirty=false;
        }
        /* Clear uncertainty only after a debounced reset has committed zero.
         * A cut before marker clearing leaves a conservative ERR after reboot. */
        input_after_commit(&input_state,&counter,committed,write_fault_word,0);
        /* FRAM writes stay in the foreground; timer samples keep accumulating. */
        t=now(); /* Do not start a power guard from a pre-journal timestamp. */
        oled_service(&display,&hal,counter.awake,committed,input_state.fault,t);
        bool settled=counter.increment.stable==counter.increment.candidate &&
                     counter.reset.stable==counter.reset.candidate;
        __disable_interrupt();
        if(inputs.gap || inputs.head!=inputs.tail ||
           (uint8_t)(~P1IN&BUTTONS)!=raw || (P1IFG&BUTTONS)) {
            __enable_interrupt();continue;
        }
        if(!counter.awake && !counter.dirty && settled && oled_is_off(&display) &&
           (!input_state.fault || *INPUT_FAULT_WORD==INPUT_FAULT_MARKER)) {
            TA0CTL=MC__STOP;TA0CCTL0=0;tick_running=0;arm_edges();
            __bis_SR_register(LPM4_bits|GIE);
        } else if(bus_status==2 || bus_status==3) {
            /* Completion just before sleep must not be lost. */
            __enable_interrupt();
        } else {
            /* Keep SMCLK alive during a transaction; otherwise REFO tick
             * and port edges wake LPM3. No full-frame busy loop exists. */
            __bis_SR_register((bus_status==1?LPM0_bits:LPM3_bits)|GIE);
        }
    }
}
