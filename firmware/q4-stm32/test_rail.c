#include "rail.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static void mv(Rail*r,unsigned v,uint32_t t){rail_sample(r,1638,(uint16_t)(3000UL*1638/v),t);}
int main(void){
    unsigned cases=0;
    /* Sweep actual rails and ±2% bounded estimate error, including raw ADC
     * quantization, starting from both OFF and a previously ON state. */
    for(unsigned cal=1620;cal<=1710;cal+=3)for(unsigned actual=2700;actual<=3300;actual++)for(int error=-20;error<=20;error++){
        uint32_t estimate=actual*(1000+error)/1000;uint16_t raw=(uint16_t)(3000UL*cal/estimate);
        for(unsigned initial=0;initial<2;initial++){
            Rail r={0};r.enabled=initial;
            for(unsigned i=0;i<3;i++)rail_sample(&r,(uint16_t)cal,raw,i*10);
            if(rail_display_allowed(&r,20))assert(actual>=3000);
            ++cases;
        }
    }
    Rail r={0};mv(&r,3150,0xfffffff0UL);assert(!r.enabled);mv(&r,3150,0xfffffffaUL);assert(!r.enabled);mv(&r,3150,4);assert(r.enabled);
    assert(rail_display_allowed(&r,34));assert(!rail_display_allowed(&r,35));
    mv(&r,3080,10);assert(r.enabled);mv(&r,3050,20);assert(!r.enabled);mv(&r,3075,30);assert(!r.enabled);
    rail_sample(&r,0,1600,40);assert(!r.valid);rail_sample(&r,1638,0,50);assert(!r.valid);rail_sample(&r,1638,4095,60);assert(!r.valid);
    for(unsigned i=0;i<3;i++)mv(&r,3150,70+i*10);assert(r.enabled);rail_invalid(&r);assert(!r.enabled&&!r.valid);
    printf("PASS: %u voltage/error/initial-state corners, hysteresis, invalid calibration/ADC, stale samples and timestamp wrap;2%% bounded error model, no analog execution\n",cases);
}
