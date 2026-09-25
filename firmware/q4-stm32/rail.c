#include "rail.h"
void rail_invalid(Rail*r){r->valid=false;r->enabled=false;r->rising_samples=0;}
void rail_sample(Rail*r,uint16_t cal,uint16_t raw,uint32_t now){
    if(cal<1000||cal>2000||!raw||raw>=4095){rail_invalid(r);return;}
    uint32_t mv=(3000UL*cal)/raw;
    if(mv<1600||mv>3650){rail_invalid(r);return;}
    r->millivolts=(uint16_t)mv;r->sampled_at=now;r->valid=true;
    if(mv<RAIL_OFF_MV){r->enabled=false;r->rising_samples=0;}
    else if(!r->enabled){
        if(mv>=RAIL_ON_MV){if(++r->rising_samples>=3)r->enabled=true;}
        else r->rising_samples=0;
    }
}
bool rail_display_allowed(const Rail*r,uint32_t now){return r->valid&&r->enabled&&(uint32_t)(now-r->sampled_at)<=RAIL_STALE_MS;}
