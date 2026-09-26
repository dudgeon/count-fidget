/* Portable battery-policy model: thresholds, hysteresis, USB detection and
 * cut-off debouncing. Voltages are inputs; no analog or cell model. */
#include "battery.h"
#include <assert.h>
#include <stdio.h>
static void feed(Battery*b,unsigned mv,unsigned n){for(unsigned i=0;i<n;i++)battery_sample(b,(uint16_t)mv,true,true);}
int main(void){
    unsigned cases=0;
    /* Steady readings map to monotonic bars and never cut off above 3350mV. */
    for(unsigned mv=3000;mv<=4300;mv++){
        Battery b;battery_reset(&b);feed(&b,mv,BATTERY_FILTER_SAMPLES+BATTERY_CUTOFF_SAMPLES);
        unsigned bars=mv>=3950?4:mv>=3800?3:mv>=3700?2:mv>=3550?1:0;
        assert(b.valid&&!b.usb&&b.bars==bars&&b.low==(bars==0));
        assert(b.cutoff==(mv<BATTERY_CUTOFF_MV));
        assert(b.charge==CHARGE_NONE);++cases;
    }
    /* Hysteresis: a bar survives a dip of less than 30mV, drops below it. */
    {Battery b;battery_reset(&b);feed(&b,3805,8);assert(b.bars==3);feed(&b,3775,8);assert(b.bars==3);feed(&b,3765,8);assert(b.bars==2);
     feed(&b,3799,8);assert(b.bars==2);feed(&b,3800,8);assert(b.bars==3);}
    /* One noisy low reading (or five) cannot power off; six consecutive can. */
    {Battery b;battery_reset(&b);feed(&b,3700,8);
     for(unsigned k=1;k<BATTERY_CUTOFF_SAMPLES;k++){feed(&b,3200,k);assert(!b.cutoff);feed(&b,3700,1);}
     feed(&b,3200,BATTERY_CUTOFF_SAMPLES);assert(b.cutoff);}
    /* USB: charger-regulated SYS is never read as a cell; STAT decoding follows
     * BQ25185 Table 6-2; a USB reading clears any pending cut-off count. */
    {Battery b;battery_reset(&b);feed(&b,3200,5);
     battery_sample(&b,4500,true,false);assert(b.usb&&b.charge==CHARGE_ACTIVE&&!b.cutoff&&!b.low);
     battery_sample(&b,4400,true,true);assert(b.charge==CHARGE_IDLE);
     battery_sample(&b,4600,false,true);assert(b.charge==CHARGE_FAULT);
     battery_sample(&b,4600,false,false);assert(b.charge==CHARGE_FAULT);
     battery_sample(&b,4312,true,true);assert(!b.usb&&b.charge==CHARGE_NONE);
     battery_sample(&b,4250,true,false);assert(b.usb&&b.charge==CHARGE_ACTIVE&&!b.low&&!b.cutoff); /* ADC low corner, STAT proves USB */
     battery_sample(&b,4250,false,true);assert(b.usb&&b.charge==CHARGE_FAULT);
     battery_sample(&b,4308,true,true);assert(!b.usb); /* full cell at +2.06% error stays a cell reading */
     feed(&b,3200,BATTERY_CUTOFF_SAMPLES-1);assert(!b.cutoff);}
    printf("PASS: %u steady battery readings, bar hysteresis, cut-off debounce, USB/STAT decoding; policy only, no cell model\n",cases);
}
