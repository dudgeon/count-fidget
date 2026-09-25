#include "stm32l072xx.h"
#include "board.h"
#include "app.h"
#include "oled.h"
#include "fram.h"
#include "rail.h"
#define BIT(n) (1UL<<(n))
#define BUTTONS (BIT(BOARD_INC_PIN)|BIT(BOARD_COUNT_RESET_PIN))
#define FLASH_ERRORS (FLASH_SR_WRPERR|FLASH_SR_PGAERR|FLASH_SR_SIZERR|FLASH_SR_OPTVERR|FLASH_SR_RDERR|FLASH_SR_NOTZEROERR|FLASH_SR_FWWERR)
uint32_t SystemCoreClock=CORE_HZ;
static App app;
static InputQueue inputs;
static Oled display;
static Rail rail;
static uint8_t adc_state;
static uint32_t adc_deadline;
static volatile uint32_t milliseconds;
static volatile bool tick_running;
static volatile uint8_t tx[OLED_TX_MAX],tx_length,tx_position,bus_status;
static uint32_t bus_started;
static bool configuration_ok;
#if !BOARD_STORAGE_FRAM
static uint32_t nv_started;
static bool nv_active,nv_voltage_fault;
#endif
static NvHal nv;
#if BOARD_STORAGE_FRAM
static Fram memory;
static bool storage_idle_attempted;
#endif
static uint32_t now(void){return milliseconds;}
static uint8_t raw_buttons(void){uint32_t pins=GPIOA->IDR;return (uint8_t)((~pins&BIT(BOARD_INC_PIN))|(pins&BIT(BOARD_COUNT_RESET_PIN)));}
static void mode(GPIO_TypeDef *p,unsigned pin,unsigned value){p->MODER=(p->MODER&~(3UL<<(pin*2)))|(value<<(pin*2));}
static void alternate(GPIO_TypeDef *p,unsigned pin,unsigned af){unsigned i=pin/8U,shift=(pin%8U)*4U;p->AFR[i]=(p->AFR[i]&~(15UL<<shift))|(af<<shift);mode(p,pin,2);}
static void power(bool on){
    if(!on){SPI2->CR2=0;SPI2->CR1=0;mode(GPIOB,0,3);mode(GPIOB,12,3);mode(GPIOB,13,3);mode(GPIOB,14,3);mode(GPIOB,15,3);}
    GPIOB->BSRR=BIT(BOARD_OLED_ENABLE_PIN+(on?0:16));
}
static void reset(bool asserted){mode(GPIOB,BOARD_OLED_RESET_PIN,1);GPIOB->BSRR=BIT(BOARD_OLED_RESET_PIN+(asserted?16:0));}
void panic(void) {
    __disable_irq();RCC->IOPENR|=RCC_IOPENR_GPIOBEN;(void)RCC->IOPENR;
    reset(true);mode(GPIOB,BOARD_OLED_RESET_PIN,1);
    RCC->APB1ENR&=~RCC_APB1ENR_WWDGEN;
    /* No EEPROM writes on an unrecoverable core fault. Hardware boot remains
     * available. Conservative discharge delay does not depend on interrupts. */
    for(volatile uint32_t i=0;i<2000000UL;i++)__NOP();
    power(false);mode(GPIOB,BOARD_OLED_ENABLE_PIN,1);
    for(;;)__WFI();
}
static bool power_good(void){return configuration_ok && !(PWR->CSR&PWR_CSR_PVDO);}
#if !BOARD_STORAGE_FRAM
static bool nv_read(void *ctx,unsigned word,uint32_t *value) {
    (void)ctx;if(word>=NV_SLOTS*NV_WORDS || (FLASH->SR&FLASH_SR_BSY))return false;
    FLASH->SR=FLASH_SR_RDERR;
    *value=((volatile const uint32_t *)NV_BASE)[word];__DSB();
    return !(FLASH->SR&FLASH_SR_RDERR);
}
static bool nv_start(void *ctx,unsigned word,uint32_t value,uint32_t t) {
    (void)ctx;
    if(nv_active || word>=NV_SLOTS*NV_WORDS || !power_good() || (FLASH->SR&FLASH_SR_BSY))return false;
    FLASH->SR=FLASH_ERRORS|FLASH_SR_EOP;
    if(FLASH->PECR&FLASH_PECR_PELOCK){FLASH->PEKEYR=0x89abcdefUL;FLASH->PEKEYR=0x02030405UL;}
    if(FLASH->PECR&FLASH_PECR_PELOCK)return false;
    FLASH->PECR&=~(FLASH_PECR_PROG|FLASH_PECR_DATA|FLASH_PECR_FIX|FLASH_PECR_ERASE|FLASH_PECR_FPRG|FLASH_PECR_PARALLBANK);
    nv_started=t;nv_voltage_fault=false;nv_active=true;
    /* Aligned normal EEPROM write: hardware erases a dirty word as needed.
     * Only Bank2 data is addressed; code, vectors and literals are Bank1. */
    ((volatile uint32_t *)NV_BASE)[word]=value;__DSB();
    return true;
}
static NvResult nv_poll(void *ctx,uint32_t t) {
    (void)ctx;if(!nv_active)return NV_ERROR;
    if(!power_good())nv_voltage_fault=true;
    if(FLASH->SR&FLASH_SR_BSY) {
        /* A stuck busy flag must never trigger a read of the busy bank. */
        if((uint32_t)(t-nv_started)>25U){nv_voltage_fault=true;return NV_ERROR;}
        return NV_BUSY;
    }
    uint32_t status=FLASH->SR;
    FLASH->PECR|=FLASH_PECR_PELOCK;nv_active=false;
    return (nv_voltage_fault || (status&FLASH_ERRORS))?NV_ERROR:NV_OK;
}
static void storage_init(void){NvHal h={nv_read,nv_start,nv_poll,0};nv=h;}
#else
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
    for(unsigned delay=0;delay<512;delay++)__NOP(); /* >=512 cycles: >100us CS rise guard including clock tolerance */
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
#endif
/* ADC is polled without waiting. HCLK/2=2MHz,160.5-cycle acquisition
 * exceeds VREFINT10us. Internal regulator/reference settle5ms beforecal. */
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
        ADC1->CR&=~ADC_CR_ADVREGEN;ADC->CCR&=~ADC_CCR_VREFEN;adc_state=0;return;
    }
    if(!adc_state){
        rail_invalid(&rail);ADC1->CFGR1=0;ADC1->CFGR2=ADC_CFGR2_CKMODE_0;
        ADC1->SMPR=ADC_SMPR_SMP;ADC1->CHSELR=ADC_CHSELR_CHSEL17;
        ADC->CCR|=ADC_CCR_VREFEN;ADC1->CR|=ADC_CR_ADVREGEN;
        adc_deadline=t+5;adc_state=1;return;
    }
    if(adc_state==1){if((int32_t)(t-adc_deadline)>=0){ADC1->CR|=ADC_CR_ADCAL;adc_deadline=t+5;adc_state=2;}return;}
    if(adc_state==2){
        if(!(ADC1->CR&ADC_CR_ADCAL)){adc_deadline=t+1;adc_state=3;return;}
    }else if(adc_state==3){
        if((int32_t)(t-adc_deadline)>=0){ADC1->ISR=ADC_ISR_ADRDY;ADC1->CR|=ADC_CR_ADEN;adc_deadline=t+5;adc_state=4;}return;
    }else if(adc_state==4){
        if(ADC1->ISR&ADC_ISR_ADRDY){adc_deadline=t;adc_state=5;return;}
    }else if(adc_state==5){
        if((int32_t)(t-adc_deadline)>=0){ADC1->ISR=ADC_ISR_EOC|ADC_ISR_OVR;ADC1->CR|=ADC_CR_ADSTART;adc_deadline=t+5;adc_state=6;}return;
    }else if(adc_state==6){
        if(ADC1->ISR&ADC_ISR_OVR){rail_invalid(&rail);adc_state=7;return;}
        if(ADC1->ISR&ADC_ISR_EOC){
            uint16_t raw=(uint16_t)ADC1->DR;
            rail_sample(&rail,*(volatile const uint16_t*)0x1ff80078UL,raw,t);
            adc_deadline=t+8;adc_state=5;return;
        }
    }else return; /* Latched ADC fault: display staysOFF untilsleep/restart. */
    if((int32_t)(t-adc_deadline)>=0){rail_invalid(&rail);adc_state=7;}
}
static void bus_abort(void) {
    I2C1->CR1=0;SPI2->CR2=0;SPI2->CR1=0;
    GPIOB->BSRR=BIT(BOARD_SPI_CS_PIN);
    RCC->APB1RSTR|=RCC_APB1RSTR_SPI2RST;RCC->APB1RSTR&=~RCC_APB1RSTR_SPI2RST;
    bus_status=0;
}
static bool bus_start(const uint8_t *bytes,uint8_t length,uint32_t t) {
    if(!length || length>OLED_TX_MAX || bus_status==1)return false;
    bus_abort();tx_length=length;tx_position=0;
    for(unsigned i=0;i<length;i++)tx[i]=bytes[i];
    bus_started=t;bus_status=1;
#if BOARD_DISPLAY_SPI
    /* Common renderer's first byte is command/data classification; SPI uses
     * the D/C pin and never transmits the I2C control byte. */
    tx_position=1;
    GPIOB->BSRR=BIT(BOARD_SPI_CS_PIN);mode(GPIOB,BOARD_SPI_CS_PIN,1);mode(GPIOB,BOARD_SPI_DC_PIN,1);
    alternate(GPIOB,BOARD_SPI_SCK_PIN,0);alternate(GPIOB,BOARD_SPI_MOSI_PIN,0);
    GPIOB->BSRR=BIT(BOARD_SPI_DC_PIN+((bytes[0]&0x40U)?0:16));
    GPIOB->BSRR=BIT(BOARD_SPI_CS_PIN+16);
    SPI2->CR1=SPI_CR1_MSTR|SPI_CR1_SSM|SPI_CR1_SSI|SPI_CR1_BIDIMODE|SPI_CR1_BIDIOE;
    SPI2->CR2=SPI_CR2_TXEIE|SPI_CR2_ERRIE;
    SPI2->CR1|=SPI_CR1_SPE;
#else
    if((I2C1->ISR&I2C_ISR_BUSY) || (GPIOB->IDR&(BIT(6)|BIT(7)))!=(BIT(6)|BIT(7))) {bus_abort();return false;}
    I2C1->TIMINGR=0x00322727UL; /* PCLK4MHz, approximately50kHz, AF enabled. */
    I2C1->ICR=I2C_ICR_STOPCF|I2C_ICR_NACKCF|I2C_ICR_BERRCF|I2C_ICR_ARLOCF|I2C_ICR_OVRCF;
    I2C1->CR1=I2C_CR1_PE|I2C_CR1_TXIE|I2C_CR1_STOPIE|I2C_CR1_NACKIE|I2C_CR1_ERRIE;
    I2C1->CR2=((uint32_t)OLED_ADDRESS<<1)|((uint32_t)length<<16)|I2C_CR2_AUTOEND|I2C_CR2_START;
#endif
    return true;
}
void I2C1_IRQHandler(void) {
    uint32_t s=I2C1->ISR;
    if(s&(I2C_ISR_NACKF|I2C_ISR_BERR|I2C_ISR_ARLO|I2C_ISR_OVR)) {
        I2C1->CR1=0;bus_status=3;return;
    }
    if(s&I2C_ISR_STOPF) {
        I2C1->ICR=I2C_ICR_STOPCF;I2C1->CR1=0;
        bus_status=tx_position==tx_length?2:3;return;
    }
    if((s&I2C_ISR_TXIS) && tx_position<tx_length)I2C1->TXDR=tx[tx_position++];
}
void SPI2_IRQHandler(void) {
    if(SPI2->SR&(SPI_SR_MODF|SPI_SR_OVR)){SPI2->CR2=0;bus_status=3;return;}
    if(SPI2->SR&SPI_SR_TXE) {
        if(tx_position<tx_length)*((volatile uint8_t *)&SPI2->DR)=tx[tx_position++];
        else SPI2->CR2&=~SPI_CR2_TXEIE;
    }
}
static OledBusResult bus_poll(uint32_t t) {
#if BOARD_DISPLAY_SPI
    if(bus_status==1 && tx_position==tx_length && (SPI2->SR&SPI_SR_TXE) && !(SPI2->SR&SPI_SR_BSY))bus_status=2;
#endif
    if(bus_status==2){bus_abort();return OLED_BUS_OK;}
    if(bus_status!=1 || (uint32_t)(t-bus_started)>=OLED_BUS_TIMEOUT_MS){bus_abort();return OLED_BUS_ERROR;}
    return OLED_BUS_BUSY;
}
static const OledHal oled_hal={power,reset,bus_start,bus_poll,bus_abort,now};
static void tick_start(void){SysTick->LOAD=CORE_HZ/1000UL-1U;SysTick->VAL=0;tick_running=true;SysTick->CTRL=SysTick_CTRL_CLKSOURCE_Msk|SysTick_CTRL_TICKINT_Msk|SysTick_CTRL_ENABLE_Msk;}
void SysTick_Handler(void){++milliseconds;input_push(&inputs,raw_buttons(),milliseconds);}
void EXTI0_1_IRQHandler(void) {
    EXTI->PR=BUTTONS;input_push(&inputs,raw_buttons(),milliseconds);
    if(!tick_running)tick_start();
}
static void setup(void) {
    RCC->IOPENR|=RCC_IOPENR_GPIOAEN|RCC_IOPENR_GPIOBEN|RCC_IOPENR_GPIOCEN;
    RCC->APB1ENR|=RCC_APB1ENR_PWREN|RCC_APB1ENR_I2C1EN|RCC_APB1ENR_SPI2EN;
    RCC->APB2ENR|=RCC_APB2ENR_SYSCFGEN|RCC_APB2ENR_SPI1EN|RCC_APB2ENR_ADC1EN;(void)RCC->APB2ENR;
    GPIOB->PUPDR&=~(15UL|(255UL<<24));
    power(false);reset(true);GPIOA->BSRR=BIT(BOARD_BYPASS_PIN+16);
    mode(GPIOB,BOARD_OLED_ENABLE_PIN,1);mode(GPIOB,BOARD_OLED_RESET_PIN,1);
    GPIOB->OTYPER&=~BIT(BOARD_OLED_RESET_PIN); /* common-rail module, external reset pull-down */
    /* PA4/5/6 reserved, no firmware-controlled battery bypass in Q4. */
    mode(GPIOA,4,3);mode(GPIOA,5,3);mode(GPIOA,6,3);
    mode(GPIOA,8,3);GPIOA->PUPDR&=~(3UL<<16); /* PA8 NC; no USB-presence divider. */
    GPIOB->PUPDR&=~((3UL<<6)|(3UL<<8)|(3UL<<10)|(3UL<<16));
    mode(GPIOB,3,3);mode(GPIOB,4,3);mode(GPIOB,5,3);mode(GPIOB,8,3);
    /* Range1, HSI16/4 through AHB prescaler. No PLL or external crystal. */
    PWR->CR=(PWR->CR&~PWR_CR_VOS)|PWR_CR_VOS_0|PWR_CR_PVDE|PWR_CR_PLS_LEV5;
    FLASH->ACR=(FLASH->ACR&~FLASH_ACR_SLEEP_PD)|FLASH_ACR_LATENCY;
    RCC->CR|=RCC_CR_HSION;RCC->CR&=~RCC_CR_HSIDIVEN;
    unsigned timeout=100000U;while(!(RCC->CR&RCC_CR_HSIRDY) && --timeout){}if(!timeout)panic();
    RCC->CFGR=(RCC->CFGR&~(RCC_CFGR_SW|RCC_CFGR_HPRE))|RCC_CFGR_SW_HSI|RCC_CFGR_HPRE_DIV4|RCC_CFGR_STOPWUCK;
    timeout=100000U;while((RCC->CFGR&RCC_CFGR_SWS)!=RCC_CFGR_SWS_HSI && --timeout){}if(!timeout)panic();
    configuration_ok=((FLASH->OPTR&FLASH_OPTR_BOR_LEV)>>16)==BOARD_BOR_REQUIRED &&
                     (FLASH->OPTR&0xffU)==0xaaU && (FLASH->OPTR&BIT(31)) && !(FLASH->OPTR&BIT(23));
    mode(GPIOA,0,0);mode(GPIOA,1,0);GPIOA->PUPDR&=~15UL;
    SYSCFG->EXTICR[0]&=~255UL;EXTI->IMR|=BUTTONS;EXTI->RTSR|=BUTTONS;EXTI->FTSR|=BUTTONS;EXTI->PR=BUTTONS;
    NVIC_SetPriority(EXTI0_1_IRQn,1);NVIC_SetPriority(SysTick_IRQn,1);
    NVIC_EnableIRQ(EXTI0_1_IRQn);
#if BOARD_DISPLAY_SPI
    mode(GPIOB,12,3);mode(GPIOB,13,3);mode(GPIOB,14,3);mode(GPIOB,15,3);
    NVIC_SetPriority(SPI2_IRQn,2);NVIC_EnableIRQ(SPI2_IRQn);
#else
    GPIOB->OTYPER|=BIT(6)|BIT(7);GPIOB->PUPDR&=~((3UL<<12)|(3UL<<14));
    alternate(GPIOB,6,1);alternate(GPIOB,7,1);NVIC_SetPriority(I2C1_IRQn,2);NVIC_EnableIRQ(I2C1_IRQn);
#endif
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
int main(void) {
    __disable_irq();setup();input_push(&inputs,raw_buttons(),0);tick_start();__enable_irq();
    storage_init();app_init(&app,&nv,0);oled_init(&display,&oled_hal);
    if(!configuration_ok)app_storage_error(&app);
    for(;;) {
        for(unsigned n=0;n<8;n++) {
            InputSample sample;uint32_t mask=__get_PRIMASK();__disable_irq();
            InputResult r=input_take(&inputs,&sample);__set_PRIMASK(mask);
            if(r==INPUT_EMPTY)break;
            app_input(&app,r,&sample);
        }
        OledState prior_display=display.state;bool prior_bus=display.pending;
        unsigned prior_step=app.journal.step;bool prior_pending=app.journal.pending,prior_nv=app.journal.busy;
        uint8_t prior_adc=adc_state;
        bool storage_good=power_good();
#if BOARD_STORAGE_FRAM
        if(app.counter.awake) {
            storage_idle_attempted=false;
            /* A newly qualified count-reset grants one bounded recovery
             * attempt. No timer/held-key loop retries a failed peripheral. */
            if(!app.storage_failed && app.input.reset_requested && !memory.ready && power_good())storage_init();
            if(!app.storage_failed)(void)fram_wake(&memory,now());
        }
        if(!memory.ready)app_storage_error(&app);
        storage_good=storage_good&&fram_available(&memory);
#endif
        app_service(&app,&nv,now(),storage_good);
        adc_service(app.counter.awake,now());
        oled_service(&display,&oled_hal,app.counter.awake && power_good() && rail_display_allowed(&rail,now()),app.journal.count,app_fault(&app),now());
        bool made_progress=display.state!=prior_display || display.pending!=prior_bus || app.journal.step!=prior_step || app.journal.pending!=prior_pending || app.journal.busy!=prior_nv || adc_state!=prior_adc;
        bool settled=app.counter.increment.stable==app.counter.increment.candidate && app.counter.reset.stable==app.counter.reset.candidate;
#if BOARD_STORAGE_FRAM
        if(!app.counter.awake && app_can_idle(&app) && settled && oled_is_off(&display) && adc_state==0 && !storage_idle_attempted){
            storage_idle_attempted=true;
            if(!fram_sleep(&memory)){app_storage_error(&app);storage_isolate();}
            continue;
        }
        bool backend_idle=!memory.pending;
#else
        bool backend_idle=!nv_active && !(FLASH->SR&FLASH_SR_BSY);
#endif
        __disable_irq();
        if(inputs.gap || inputs.head!=inputs.tail || (EXTI->PR&BUTTONS)){__enable_irq();continue;}
        if(!app.counter.awake && app_can_idle(&app) && backend_idle && settled && oled_is_off(&display) && adc_state==0) {
            SysTick->CTRL=0;tick_running=false;
            SCB->ICSR=SCB_ICSR_PENDSTCLR_Msk;
            PWR->CR&=~(PWR_CR_PDDS|PWR_CR_DSEEKOFF);PWR->CR|=PWR_CR_LPSDSR;
            SCB->SCR|=SCB_SCR_SLEEPDEEP_Msk;
            /* WFI with PRIMASK set closes the test/sleep race: a newly pending
             * EXTI wakes the core, then is serviced when interrupts unmask. */
            stop_from_ram();SCB->SCR&=~SCB_SCR_SLEEPDEEP_Msk;__enable_irq();
        } else {if(!made_progress){__DSB();__WFI();}__enable_irq();}
    }
}
