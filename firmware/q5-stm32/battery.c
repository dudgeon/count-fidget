#include "battery.h"
#include <string.h>
void battery_reset(Battery *b){memset(b,0,sizeof(*b));b->charge=CHARGE_UNKNOWN;}
static uint8_t bars_for(uint16_t mv,uint8_t previous){
    static const uint16_t edge[4]={BATTERY_BAR1_MV,BATTERY_BAR2_MV,BATTERY_BAR3_MV,BATTERY_BAR4_MV};
    uint8_t bars=0;
    for(unsigned i=0;i<4;i++){
        /* A level already shown survives until the reading falls a hysteresis
         * band below its edge; it rises only on crossing the plain edge. */
        uint16_t threshold=(previous>i)?(uint16_t)(edge[i]-BATTERY_HYSTERESIS_MV):edge[i];
        if(mv>=threshold)bars=(uint8_t)(i+1U);else break;
    }
    return bars;
}
void battery_sample(Battery *b,uint16_t mv,bool stat1,bool stat2){
    b->usb=mv>=BATTERY_USB_MV || !stat1 || !stat2;
    /* BQ25185 Table 6-2: H/L charging, H/H done or disabled (including the
     * external temperature window), L/x fault. Meaningful only with USB. */
    b->charge=!b->usb?CHARGE_NONE:!stat1?CHARGE_FAULT:!stat2?CHARGE_ACTIVE:CHARGE_IDLE;
    if(b->usb){
        /* SYS is regulated, not the cell: keep the last battery estimate but
         * never power off or warn from a charger-regulated reading. */
        b->low=false;b->cutoff=false;b->low_count=0;b->filled=0;b->next=0;b->sum=0;
        return;
    }
    if(b->filled==BATTERY_FILTER_SAMPLES)b->sum-=b->history[b->next];else ++b->filled;
    b->history[b->next]=mv;b->sum+=mv;b->next=(uint8_t)((b->next+1U)%BATTERY_FILTER_SAMPLES);
    if(b->filled<BATTERY_FILTER_SAMPLES)return;
    b->millivolts=(uint16_t)(b->sum/BATTERY_FILTER_SAMPLES);
    b->bars=bars_for(b->millivolts,b->valid?b->bars:0);b->valid=true;
    b->low=b->bars==0;
    /* Cut-off uses raw consecutive samples so one noisy reading cannot power
     * the device off, and a genuinely exhausted cell cannot keep it on. */
    if(mv<BATTERY_CUTOFF_MV){if(b->low_count<255U)++b->low_count;}else b->low_count=0;
    if(b->low_count>=BATTERY_CUTOFF_SAMPLES)b->cutoff=true;
}
