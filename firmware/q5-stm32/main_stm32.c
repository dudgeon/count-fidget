#include "stm32l072xx.h"
#include "board.h"
#include "app.h"
#include "oled.h"
#include "fram.h"
#include "rail.h"
#include "battery.h"
#define BIT(n) (1UL<<(n))
#define BUTTONS (BIT(BOARD_INC_PIN)|BIT(BOARD_COUNT_RESET_PIN))
#define FLASH_ERRORS (FLASH_SR_WRPERR|FLASH_SR_PGAERR|FLASH_SR_SIZERR|FLASH_SR_OPTVERR|FLASH_SR_RDERR|FLASH_SR_NOTZEROERR|FLASH_SR_FWWERR)
/* >=512 core cycles (128us at 4MHz) after every FRAM CS release: about five
 * cycles per iteration on Cortex-M0+ with zero flash wait states. */
#define FRAM_CS_GUARD_LOOPS 110U
/* A battery power-off that has not removed the supply within this time means
 * USB or a held COUNT key is keeping U7 on: fall back to Stop. */
#define POWER_RELEASE_MS 200U
/* LO is shown this long before a low-battery power-off. */
#define CUTOFF_NOTICE_MS 2000U
uint32_t SystemCoreClock=CORE_HZ;
static App app;
static InputQueue inputs;
static Oled display;
static Rail rail;
static Battery battery;
static uint8_t adc_state,adc_channel;
static uint16_t vref_raw;
static uint32_t adc_deadline;
static volatile uint32_t milliseconds;
static volatile bool tick_running;
/* Button capture starts only once the foreground loop can drain the queue:
 * the boot-time journal scan can exceed the queue's 255 ms of samples. */
static volatile bool capture_enabled;
/* During the boot journal scan only level changes (plus one settle sample per
 * change) are queued, so presses made while storage loads are kept without
 * filling the queue with identical samples. */
static volatile bool early_capture,early_pending;
static volatile uint8_t early_raw;
static volatile uint32_t early_settle;
static volatile uint8_t tx[OLED_TX_MAX],tx_length,tx_position,bus_status;
static uint32_t bus_started;
static bool configuration_ok,wake_key;
static uint32_t reset_flags;
static bool shutdown_latched;
static uint32_t shutdown_at;
static NvHal nv;
static Fram memory;
static bool storage_idle_attempted,release_tried;
static uint32_t now(void){return milliseconds;}
static uint8_t raw_buttons(void){uint32_t pins=GPIOA->IDR;return (uint8_t)((~pins&BIT(BOARD_INC_PIN))|(pins&BIT(BOARD_COUNT_RESET_PIN)));}
static void mode(GPIO_TypeDef *p,unsigned pin,unsigned value){p->MODER=(p->MODER&~(3UL<<(pin*2)))|(value<<(pin*2));}
static void pull(GPIO_TypeDef *p,unsigned pin,unsigned value){p->PUPDR=(p->PUPDR&~(3UL<<(pin*2)))|(value<<(pin*2));}
static void alternate(GPIO_TypeDef *p,unsigned pin,unsigned af){unsigned i=pin/8U,shift=(pin%8U)*4U;p->AFR[i]=(p->AFR[i]&~(15UL<<shift))|(af<<shift);mode(p,pin,2);}
static void hold_power(bool on){GPIOB->BSRR=BIT(BOARD_PWR_HOLD_PIN+(on?0:16));}
static void power(bool on){
    if(!on){SPI2->CR2=0;SPI2->CR1=0;mode(GPIOB,0,3);mode(GPIOB,12,3);mode(GPIOB,13,3);mode(GPIOB,14,3);mode(GPIOB,15,3);}
    GPIOB->BSRR=BIT(BOARD_OLED_ENABLE_PIN+(on?0:16));
}
static void reset(bool asserted){mode(GPIOB,BOARD_OLED_RESET_PIN,1);GPIOB->BSRR=BIT(BOARD_OLED_RESET_PIN+(asserted?16:0));}
void panic(void) {
    __disable_irq();RCC->IOPENR|=RCC_IOPENR_GPIOBEN;(void)RCC->IOPENR;
    reset(true);mode(GPIOB,BOARD_OLED_RESET_PIN,1);
    /* No FRAM writes on an unrecoverable core fault. Conservative discharge
     * delay does not depend on interrupts; then release the power latch so a
     * battery-only board switches itself off. Hardware boot remains available. */
    for(volatile uint32_t i=0;i<2000000UL;i++)__NOP();
    power(false);mode(GPIOB,BOARD_OLED_ENABLE_PIN,1);hold_power(false);
    for(;;)__WFI();
}
static bool supply_good(void){return !(PWR->CSR&PWR_CSR_PVDO);}
static bool power_good(void){return configuration_ok && supply_good();}
static bool spi1_wait(uint32_t flag,bool set){
    for(unsigned budget=0;budget<1000;budget++){
        if(SPI1->SR&(SPI_SR_MODF|SPI_SR_OVR))return false;
        if(((SPI1->SR&flag)!=0)==set)return true;
    }
    return false;
}
static bool fram_exchange(void*ctx,const uint8_t*tx_data,uint8_t*rx_data,unsigned length){
    (void)ctx;if(!length||length>35||!power_good())return false;
    GPIOB->BSRR=BIT(8); /* CS is OD with external pull-up to isolated VFRAM. */
    unsigned budget=1000;while(!(GPIOB->IDR&BIT(8))&&--budget){}if(!budget)return false;
    GPIOB->BSRR=BIT(8+16);
    bool okay=true;
    for(unsigned i=0;i<length;i++){
        if(!spi1_wait(SPI_SR_TXE,true)){okay=false;break;}
        *((volatile uint8_t*)&SPI1->DR)=tx_data[i];
        if(!spi1_wait(SPI_SR_RXNE,true)){okay=false;break;}
        rx_data[i]=*((volatile uint8_t*)&SPI1->DR);
    }
    if(okay)okay=spi1_wait(SPI_SR_TXE,true)&&spi1_wait(SPI_SR_BSY,false);
    GPIOB->BSRR=BIT(8);
    for(unsigned delay=0;delay<FRAM_CS_GUARD_LOOPS;delay++)__NOP(); /* >100us CS rise guard including clock tolerance */
    if(!okay){SPI1->CR1=0;mode(GPIOB,3,3);mode(GPIOB,4,3);mode(GPIOB,5,3);}
    return okay;
}
static void storage_isolate(void){
    GPIOB->BSRR=BIT(8); /* external VFRAM pull-up, never drive high */
    SPI1->CR1=0;SPI1->CR2=0;mode(GPIOB,3,3);mode(GPIOB,4,3);mode(GPIOB,5,3);
}
static void storage_init(void){
    RCC->APB2RSTR|=RCC_APB2RSTR_SPI1RST;RCC->APB2RSTR&=~RCC_APB2RSTR_SPI1RST;
    /*20ms exceeds the specified isolated-rail RC settle + memory power-up
     * interval. No FRAM pin is actively high while its rail is settling. */
    uint32_t begin=now();while((uint32_t)(now()-begin)<20U)__WFI();
    GPIOB->BSRR=BIT(8);GPIOB->OTYPER|=BIT(8);mode(GPIOB,8,1);
    alternate(GPIOB,3,0);alternate(GPIOB,4,0);alternate(GPIOB,5,0);
    SPI1->CR1=SPI_CR1_MSTR|SPI_CR1_SSM|SPI_CR1_SSI|SPI_CR1_BR_1|SPI_CR1_SPE; /*500kHz, below1MHz with oscillator tolerance*/
    /* NRST may reset only MCU while FRAM remains asleep. Wake first and
     * wait independently of POR before identification/status probing. */
    uint8_t wake_tx[4]={3,0,0,0},wake_rx[4];(void)fram_exchange(0,wake_tx,wake_rx,4);
    begin=now();while((uint32_t)(now()-begin)<2U)__WFI();
    const FramBus bus={fram_exchange,0};(void)fram_init(&memory,&bus);nv=fram_storage(&memory);
}
static void charger_inputs(bool enabled){
    /* BQ25185 STAT1/STAT2 are open drain; internal pull-ups only while awake. */
    for(unsigned pin=BOARD_STAT1_PIN;pin<=BOARD_STAT2_PIN;pin++){
        if(enabled){pull(GPIOA,pin,1);mode(GPIOA,pin,0);}else{mode(GPIOA,pin,3);pull(GPIOA,pin,0);}
    }
}
/* ADC is polled without waiting. HCLK/2=2MHz (LFMEN set: RM0376 requires it
 * below 3.5MHz), 160.5-cycle acquisition exceeds
 * VREFINT 10us and settles the 75k-source SYS divider held by its 100nF
 * capacitor. Conversions alternate VREFINT (rail) and IN4 (SYS_LOAD/2). */
static void adc_service(bool awake,uint32_t t){
    if(!awake || adc_state==8){
        if(adc_state!=8)adc_deadline=t+5;
        adc_state=8;rail_invalid(&rail);
        if((ADC1->CR&(ADC_CR_ADSTART|ADC_CR_ADEN)) && (int32_t)(t-adc_deadline)>=0){
            /* A peripheral that never acknowledges stop/disable cannot hold
             * the application awake indefinitely. Reset only the ADC. */
            RCC->APB2RSTR|=RCC_APB2RSTR_ADC1RST;RCC->APB2RSTR&=~RCC_APB2RSTR_ADC1RST;
        }
        if(ADC1->CR&ADC_CR_ADSTART){ADC1->CR|=ADC_CR_ADSTP;return;}
        if(ADC1->CR&ADC_CR_ADEN){ADC1->CR|=ADC_CR_ADDIS;return;}
        ADC1->CR&=~ADC_CR_ADVREGEN;ADC->CCR&=~ADC_CCR_VREFEN;SYSCFG->CFGR3&=~SYSCFG_CFGR3_ENBUF_VREFINT_ADC;
        adc_state=0;charger_inputs(false);return;
    }
    if(!adc_state){
        rail_invalid(&rail);ADC1->CFGR1=0;ADC1->CFGR2=ADC_CFGR2_CKMODE_0;
        ADC1->SMPR=ADC_SMPR_SMP;adc_channel=17;vref_raw=0;ADC1->CHSELR=ADC_CHSELR_CHSEL17;
        SYSCFG->CFGR3|=SYSCFG_CFGR3_ENBUF_VREFINT_ADC;
        ADC->CCR|=ADC_CCR_VREFEN|ADC_CCR_LFMEN;ADC1->CR|=ADC_CR_ADVREGEN;charger_inputs(true);
        adc_deadline=t+5;adc_state=1;return;
    }
    if(adc_state==1){
        if((int32_t)(t-adc_deadline)<0)return;
        if(!(SYSCFG->CFGR3&SYSCFG_CFGR3_VREFINT_RDYF)){if((int32_t)(t-adc_deadline)>=10){rail_invalid(&rail);adc_state=7;}return;}
        ADC1->CR|=ADC_CR_ADCAL;adc_deadline=t+5;adc_state=2;return;
    }
    if(adc_state==2){
        if(!(ADC1->CR&ADC_CR_ADCAL)){adc_deadline=t+1;adc_state=3;return;}
    }else if(adc_state==3){
        if((int32_t)(t-adc_deadline)>=0){ADC1->ISR=ADC_ISR_ADRDY;ADC1->CR|=ADC_CR_ADEN;adc_deadline=t+5;adc_state=4;}return;
    }else if(adc_state==4){
        if(ADC1->ISR&ADC_ISR_ADRDY){adc_deadline=t;adc_state=5;return;}
    }else if(adc_state==5){
        if((int32_t)(t-adc_deadline)>=0){
            ADC1->CHSELR=adc_channel==17?ADC_CHSELR_CHSEL17:(1UL<<BOARD_VBAT_ADC_CHANNEL);
            ADC1->ISR=ADC_ISR_EOC|ADC_ISR_OVR;ADC1->CR|=ADC_CR_ADSTART;adc_deadline=t+5;adc_state=6;
        }
        return;
    }else if(adc_state==6){
        if(ADC1->ISR&ADC_ISR_OVR){rail_invalid(&rail);adc_state=7;return;}
        if(ADC1->ISR&ADC_ISR_EOC){
            uint16_t raw=(uint16_t)ADC1->DR;
            if(adc_channel==17){
                uint16_t cal=*(volatile const uint16_t*)0x1ff80078UL;
                rail_sample(&rail,cal,raw,t);vref_raw=rail.valid?raw:0;adc_channel=BOARD_VBAT_ADC_CHANNEL;adc_deadline=t+1;
            }else{
                if(vref_raw){
                    /* SYS_LOAD = 2 x IN4 x VDDA/4095, VDDA = 3000mV x VREFINT_CAL/VREFINT.
                     * Two steps keep every product below 2^32. */
                    uint32_t cal=*(volatile const uint16_t*)0x1ff80078UL;
                    uint32_t vdda=(3000UL*cal)/vref_raw;
                    uint32_t mv=(2UL*raw*vdda)/4095UL;
                    battery_sample(&battery,(uint16_t)(mv>65535U?65535U:mv),(GPIOA->IDR&BIT(BOARD_STAT1_PIN))!=0,(GPIOA->IDR&BIT(BOARD_STAT2_PIN))!=0);
                }
                adc_channel=17;adc_deadline=t+7;
            }
            adc_state=5;return;
        }
    }else return; /* Latched ADC fault: display staysOFF untilsleep/restart. */
    if((int32_t)(t-adc_deadline)>=0){rail_invalid(&rail);adc_state=7;}
}
static void bus_abort(void) {
    SPI2->CR2=0;SPI2->CR1=0;
    GPIOB->BSRR=BIT(BOARD_SPI_CS_PIN);
    RCC->APB1RSTR|=RCC_APB1RSTR_SPI2RST;RCC->APB1RSTR&=~RCC_APB1RSTR_SPI2RST;
    bus_status=0;
}
static bool bus_start(const uint8_t *bytes,uint8_t length,uint32_t t) {
    if(!length || length>OLED_TX_MAX || bus_status==1)return false;
    bus_abort();tx_length=length;tx_position=0;
    for(unsigned i=0;i<length;i++)tx[i]=bytes[i];
    bus_started=t;bus_status=1;
    /* Common renderer's first byte is command/data classification; SPI uses
     * the D/C pin and never transmits it. */
    tx_position=1;
    GPIOB->BSRR=BIT(BOARD_SPI_CS_PIN);mode(GPIOB,BOARD_SPI_CS_PIN,1);mode(GPIOB,BOARD_SPI_DC_PIN,1);
    alternate(GPIOB,BOARD_SPI_SCK_PIN,0);alternate(GPIOB,BOARD_SPI_MOSI_PIN,0);
    GPIOB->BSRR=BIT(BOARD_SPI_DC_PIN+((bytes[0]&0x40U)?0:16));
    GPIOB->BSRR=BIT(BOARD_SPI_CS_PIN+16);
    SPI2->CR1=SPI_CR1_MSTR|SPI_CR1_SSM|SPI_CR1_SSI|SPI_CR1_BIDIMODE|SPI_CR1_BIDIOE;
    SPI2->CR2=SPI_CR2_TXEIE|SPI_CR2_ERRIE;
    SPI2->CR1|=SPI_CR1_SPE;
    return true;
}
void SPI2_IRQHandler(void) {
    if(SPI2->SR&(SPI_SR_MODF|SPI_SR_OVR)){SPI2->CR2=0;bus_status=3;return;}
    if(SPI2->SR&SPI_SR_TXE) {
        if(tx_position<tx_length)*((volatile uint8_t *)&SPI2->DR)=tx[tx_position++];
        else SPI2->CR2&=~SPI_CR2_TXEIE;
    }
}
static OledBusResult bus_poll(uint32_t t) {
    if(bus_status==1 && tx_position==tx_length && (SPI2->SR&SPI_SR_TXE) && !(SPI2->SR&SPI_SR_BSY))bus_status=2;
    if(bus_status==2){bus_abort();return OLED_BUS_OK;}
    if(bus_status!=1 || (uint32_t)(t-bus_started)>=OLED_BUS_TIMEOUT_MS){bus_abort();return OLED_BUS_ERROR;}
    return OLED_BUS_BUSY;
}
static const OledHal oled_hal={power,reset,bus_start,bus_poll,bus_abort,now};
static void tick_start(void){SysTick->LOAD=CORE_HZ/1000UL-1U;SysTick->VAL=0;tick_running=true;SysTick->CTRL=SysTick_CTRL_CLKSOURCE_Msk|SysTick_CTRL_TICKINT_Msk|SysTick_CTRL_ENABLE_Msk;}
void SysTick_Handler(void){
    ++milliseconds;
    if(capture_enabled){input_push(&inputs,raw_buttons(),milliseconds);return;}
    if(!early_capture)return;
    uint8_t raw=raw_buttons();
    if(raw!=early_raw){early_raw=raw;early_settle=milliseconds+DEBOUNCE_MS+1U;early_pending=true;input_push(&inputs,raw,milliseconds);}
    else if(early_pending && (int32_t)(milliseconds-early_settle)>=0){early_pending=false;input_push(&inputs,raw,milliseconds);}
}
void EXTI0_1_IRQHandler(void) {
    /* A press re-latches the supply; a bare release (e.g. a key that was held
     * through the power-off) must not, or the board would stay on. */
    if(raw_buttons())hold_power(true);
    EXTI->PR=BUTTONS;if(capture_enabled)input_push(&inputs,raw_buttons(),milliseconds);
    if(!tick_running){tick_start();shutdown_latched=false;}
}
/* Option bytes left at the RM0376 factory value (BOR off) would disable all
 * storage. Program the reviewed USER half-word once, then reload. RDP is
 * never written. A second failure after the reload leaves OPT on screen. */
static bool options_ok(uint32_t optr){
    return ((optr&FLASH_OPTR_BOR_LEV)>>16)==BOARD_BOR_REQUIRED &&
           (optr&0xffU)==0xaaU && (optr&BIT(31)) && !(optr&BIT(23));
}
static void provision_options(void){
    uint32_t optr=FLASH->OPTR;
    if(options_ok(optr) || (optr&0xffU)!=0xaaU || (reset_flags&RCC_CSR_OBLRSTF))return;
    /* PVDO is meaningful only once VREFINT is ready and the PVD has settled. */
    uint32_t begin=now();
    while(!(PWR->CSR&PWR_CSR_VREFINTRDYF) && (uint32_t)(now()-begin)<5U){}
    begin=now();while((uint32_t)(now()-begin)<2U)__WFI();
    if(!(PWR->CSR&PWR_CSR_VREFINTRDYF) || !supply_good())return;
    uint32_t user=(optr>>16)&0xffffU;
    user=(user&~0x008fU&0xffffU)|BIT(15)|BOARD_BOR_REQUIRED; /* BOR_LEV=0xC, BFB2=0, nBOOT1=1 */
    if(user!=BOARD_OPTR_USER)return; /* unexpected WDG/STOP/STDBY choices: do not guess */
    uint32_t word=((~user&0xffffU)<<16)|user;
    /* Already stored but still not loaded as expected: show OPT rather than
     * rewriting the option word on every power-on. */
    if(*(volatile const uint32_t*)(OB_BASE+4U)==word)return;
    FLASH->SR=FLASH_ERRORS|FLASH_SR_EOP;
    if(FLASH->PECR&FLASH_PECR_PELOCK){FLASH->PEKEYR=0x89abcdefUL;FLASH->PEKEYR=0x02030405UL;}
    if(FLASH->PECR&FLASH_PECR_OPTLOCK){FLASH->OPTKEYR=0xfbead9c8UL;FLASH->OPTKEYR=0x24252627UL;}
    if(FLASH->PECR&(FLASH_PECR_PELOCK|FLASH_PECR_OPTLOCK))return;
    *(volatile uint32_t*)(OB_BASE+4U)=word;
    for(unsigned t=0;t<200000U && (FLASH->SR&FLASH_SR_BSY);t++){}
    if((FLASH->SR&(FLASH_SR_BSY|FLASH_ERRORS))){FLASH->PECR|=FLASH_PECR_OPTLOCK|FLASH_PECR_PELOCK;return;}
    FLASH->PECR|=FLASH_PECR_OBL_LAUNCH; /* system reset reloading option bytes */
    for(;;){}
}
static void setup(void) {
    /* Latch the system supply first: on battery, COUNT's contact is all that
     * holds U7 on until PB2 drives D3. */
    RCC->IOPENR|=RCC_IOPENR_GPIOAEN|RCC_IOPENR_GPIOBEN|RCC_IOPENR_GPIOCEN;(void)RCC->IOPENR;
    hold_power(true);GPIOB->OTYPER&=~BIT(BOARD_PWR_HOLD_PIN);mode(GPIOB,BOARD_PWR_HOLD_PIN,1);
    reset_flags=RCC->CSR;RCC->CSR|=RCC_CSR_RMVF;
    GPIOA->PUPDR&=~15UL;mode(GPIOA,0,0);mode(GPIOA,1,0);
    /* A COUNT press that powered the board is still closing its contact now. */
    for(volatile unsigned i=0;i<8U;i++){}
    bool first=!(GPIOA->IDR&BIT(BOARD_INC_PIN));
    for(volatile unsigned i=0;i<8U;i++){}
    wake_key=(reset_flags&RCC_CSR_PORRSTF) && first && !(GPIOA->IDR&BIT(BOARD_INC_PIN));
    RCC->APB1ENR|=RCC_APB1ENR_PWREN|RCC_APB1ENR_SPI2EN;
    RCC->APB2ENR|=RCC_APB2ENR_SYSCFGEN|RCC_APB2ENR_SPI1EN|RCC_APB2ENR_ADC1EN;(void)RCC->APB2ENR;
    GPIOB->PUPDR&=~(15UL|(255UL<<24));
    power(false);reset(true);
    mode(GPIOB,BOARD_OLED_ENABLE_PIN,1);mode(GPIOB,BOARD_OLED_RESET_PIN,1);
    GPIOB->OTYPER&=~BIT(BOARD_OLED_RESET_PIN); /* common-rail module, external reset pull-down */
    mode(GPIOA,BOARD_VBAT_ADC_PIN,3);charger_inputs(false);mode(GPIOA,7,3);
    mode(GPIOA,8,3);GPIOA->PUPDR&=~(3UL<<16); /* PA8 NC */
    GPIOB->PUPDR&=~((3UL<<6)|(3UL<<8)|(3UL<<10)|(3UL<<16));
    mode(GPIOB,3,3);mode(GPIOB,4,3);mode(GPIOB,5,3);mode(GPIOB,8,3);
    /* Range1, HSI16/4 through AHB prescaler. No PLL or external crystal.
     * RM0376 Table 12: zero flash wait states are valid to 16MHz in Range 1. */
    PWR->CR=(PWR->CR&~PWR_CR_VOS)|PWR_CR_VOS_0|PWR_CR_PVDE|PWR_CR_PLS_LEV5;
    FLASH->ACR&=~(FLASH_ACR_SLEEP_PD|FLASH_ACR_LATENCY);
    RCC->CR|=RCC_CR_HSION;RCC->CR&=~RCC_CR_HSIDIVEN;
    unsigned timeout=100000U;while(!(RCC->CR&RCC_CR_HSIRDY) && --timeout){}if(!timeout)panic();
    RCC->CFGR=(RCC->CFGR&~(RCC_CFGR_SW|RCC_CFGR_HPRE))|RCC_CFGR_SW_HSI|RCC_CFGR_HPRE_DIV4|RCC_CFGR_STOPWUCK;
    timeout=100000U;while((RCC->CFGR&RCC_CFGR_SWS)!=RCC_CFGR_SWS_HSI && --timeout){}if(!timeout)panic();
    configuration_ok=options_ok(FLASH->OPTR);
    SYSCFG->EXTICR[0]&=~255UL;EXTI->IMR|=BUTTONS;EXTI->RTSR|=BUTTONS;EXTI->FTSR|=BUTTONS;EXTI->PR=BUTTONS;
    NVIC_SetPriority(EXTI0_1_IRQn,1);NVIC_SetPriority(SysTick_IRQn,1);
    NVIC_EnableIRQ(EXTI0_1_IRQn);
    mode(GPIOB,12,3);mode(GPIOB,13,3);mode(GPIOB,14,3);mode(GPIOB,15,3);
    NVIC_SetPriority(SPI2_IRQn,2);NVIC_EnableIRQ(SPI2_IRQn);
}
/* ES0292 Rev8 section2.1.2: use the RUN_PD workaround on every silicon
 * revision. The complete function AND its literal pool live in initialized
 * SRAM. The caller masks IRQs through Flash recovery; no helper is called
 * while Flash is off. Range1 also avoids section2.1.3's regulator condition. */
__attribute__((section(".ramfunc.stop"),noinline,used))
void stop_from_ram(void) {
    FLASH->PDKEYR=0x04152637UL;FLASH->PDKEYR=0xfafbfcfdUL;
    FLASH->ACR|=FLASH_ACR_RUN_PD;
    __DSB();__ISB();__WFI();
    FLASH->ACR&=~FLASH_ACR_RUN_PD;
    __DSB();__ISB();
}
static void view_of(OledView *v){
    v->count=app.journal.count;v->hide_digits=!configuration_ok;
    v->bars=battery.usb?(battery.charge==CHARGE_IDLE?4U:OLED_BARS_HIDDEN):battery.valid?battery.bars:OLED_BARS_HIDDEN;
    /* RST outranks ERR: releasing an armed reset is how ERR is cleared. */
    v->label=!configuration_ok?OLED_LABEL_OPT:app.counter.reset_armed?OLED_LABEL_RST:app_fault(&app)?OLED_LABEL_ERR:
             app.journal.count>=COUNTER_MAX?OLED_LABEL_MAX:
             (shutdown_latched||(battery.valid&&battery.low&&!battery.usb))?OLED_LABEL_LO:
             battery.charge==CHARGE_ACTIVE?OLED_LABEL_CHG:battery.charge==CHARGE_FAULT?OLED_LABEL_BAT:OLED_LABEL_NONE;
}
int main(void) {
    __disable_irq();setup();tick_start();__enable_irq();
    provision_options();
    battery_reset(&battery);
    /* Power the module (held in reset) before the journal scan so its supply
     * settling overlaps boot; nothing is sent until the rail is measured. */
    OledView view={0,OLED_LABEL_NONE,OLED_BARS_HIDDEN,true};
    oled_init(&display,&oled_hal);
    oled_service(&display,&oled_hal,supply_good(),false,&view,now());
    __disable_irq();uint8_t boot_keys=raw_buttons();uint32_t boot_ms=milliseconds;
    early_raw=boot_keys;early_capture=true;__enable_irq();
    storage_init();app_init(&app,&nv,boot_ms,boot_keys);
    if(wake_key)app_wake_press(&app,boot_ms);
    if(!configuration_ok)app_storage_error(&app);
    __disable_irq();early_capture=false;input_push(&inputs,raw_buttons(),milliseconds);capture_enabled=true;__enable_irq();
    for(;;) {
        for(unsigned n=0;n<8;n++) {
            InputSample sample;uint32_t mask=__get_PRIMASK();__disable_irq();
            InputResult r=input_take(&inputs,&sample);__set_PRIMASK(mask);
            if(r==INPUT_EMPTY)break;
            app_input(&app,r,&sample);
        }
        /* Storage-protecting power-off below the battery cut-off, after LO
         * has been visible; never from a USB-regulated SYS reading. */
        if(battery.cutoff && !battery.usb && !shutdown_latched){shutdown_latched=true;shutdown_at=now()+CUTOFF_NOTICE_MS;}
        if(battery.usb)shutdown_latched=false; /* USB arrived during the LO notice: keep running and charge */
        bool shutdown=shutdown_latched && (int32_t)(now()-shutdown_at)>=0;
        bool run=app.counter.awake && !shutdown;
        if(run)hold_power(true);
        OledState prior_display=display.state;bool prior_bus=display.pending;
        unsigned prior_step=app.journal.step;bool prior_pending=app.journal.pending,prior_nv=app.journal.busy;
        uint8_t prior_adc=adc_state;
        bool storage_good=power_good();
        if(run) {
            storage_idle_attempted=false;
            /* A newly committed count reset grants one bounded recovery
             * attempt. No timer/held-key loop retries a failed peripheral. */
            if(!app.storage_failed && app.input.reset_requested && !memory.ready && power_good())storage_init();
            if(!app.storage_failed)(void)fram_wake(&memory,now());
        }
        if(!memory.ready && configuration_ok)app_storage_error(&app);
        storage_good=storage_good&&fram_available(&memory);
        app_service(&app,&nv,now(),storage_good);
        adc_service(run,now());
        view_of(&view);
        oled_service(&display,&oled_hal,run && supply_good(),rail_display_allowed(&rail,now()),&view,now());
        bool made_progress=display.state!=prior_display || display.pending!=prior_bus || app.journal.step!=prior_step || app.journal.pending!=prior_pending || app.journal.busy!=prior_nv || adc_state!=prior_adc;
        bool settled=app.counter.increment.stable==app.counter.increment.candidate && app.counter.reset.stable==app.counter.reset.candidate;
        bool quiet=!run && app_can_idle(&app) && settled && oled_is_off(&display) && adc_state==0;
        if(quiet && !storage_idle_attempted){
            storage_idle_attempted=true;
            if(memory.ready && !fram_sleep(&memory)){app_storage_error(&app);storage_isolate();}
            continue;
        }
        bool backend_idle=!memory.pending;
        if(run)release_tried=false;
        if(quiet && backend_idle && !battery.usb && !release_tried) {
            /* Battery only: release the latch. Supply collapse ends execution.
             * Still running afterwards means USB or a held COUNT key keeps U7
             * on: leave the latch released, drain the queued samples, then use
             * the Stop path, so letting go of the key switches the board off. */
            release_tried=true;hold_power(false);
            uint32_t begin=now();
            while((uint32_t)(now()-begin)<POWER_RELEASE_MS && !raw_buttons())__WFI();
            continue;
        }
        __disable_irq();
        if(inputs.gap || inputs.head!=inputs.tail || (EXTI->PR&BUTTONS)){__enable_irq();continue;}
        if(quiet && backend_idle) {
            /* USB-held (or key-held) fallback: Stop with the latch released, so
             * unplugging USB then switches the board off cleanly. */
            hold_power(false);
            SysTick->CTRL=0;tick_running=false;
            SCB->ICSR=SCB_ICSR_PENDSTCLR_Msk;
            PWR->CR&=~(PWR_CR_PDDS|PWR_CR_DSEEKOFF);PWR->CR|=PWR_CR_LPSDSR;
            SCB->SCR|=SCB_SCR_SLEEPDEEP_Msk;
            /* WFI with PRIMASK set closes the test/sleep race: a newly pending
             * EXTI wakes the core, then is serviced when interrupts unmask. */
            stop_from_ram();SCB->SCR&=~SCB_SCR_SLEEPDEEP_Msk;if(raw_buttons())hold_power(true);__enable_irq();
            battery_reset(&battery);
        } else {if(!made_progress && !display.pending){__DSB();__WFI();}__enable_irq();}
    }
}
