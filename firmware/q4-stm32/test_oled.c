#include "oled.h"
#include "counter.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static uint32_t time_ms,started,last_disable_ack,powered_at;
static unsigned transfers,failures;
static unsigned fail_on_transfer,transfer_delay;
static bool powered,reset_low,busy,always_fail,panel_on,pump_on;
static uint8_t queued[OLED_TX_MAX],length,ram[8][128],page,column;
static bool initial_clear_complete,input_fault;
static unsigned cleared;
static void power(bool on) {
    if(on){powered_at=time_ms;cleared=0;initial_clear_complete=false;}
    if(!on && powered && !reset_low)assert(((uint32_t)(time_ms-last_disable_ack)-1U)*1000U>=120000U);
    powered=on;
}
static void reset(bool low) {
    if(!low)assert((uint32_t)(time_ms-powered_at)>=OLED_STABLE_20_MS+2U);
    reset_low=low;
    if(low){panel_on=false;pump_on=false;}
}
static void abort_bus(void){busy=false;}
static bool start(const uint8_t *data,uint8_t count,uint32_t now) {
    assert(!busy && count && count<=OLED_TX_MAX);
    assert(powered && !reset_low);
    memcpy(queued,data,count);length=count;started=now;busy=true;++transfers;
    return true;
}
static void consume(void) {
    if(queued[0]==0x40) {
        assert(length==OLED_CHUNK+1);
        for(unsigned i=1;i<length;i++) {
            assert(page<8 && column<128);ram[page][column++]=queued[i];
            if(!panel_on && queued[i]==0)++cleared;
        }
        if(cleared==1024)initial_clear_complete=true;
    } else {
        assert(queued[0]==0);
        for(unsigned i=1;i<length;i++) {
            uint8_t command=queued[i];
            if(command==0x8d) {
                uint8_t argument=queued[++i];
                assert(argument==0x10 || argument==0x14);
                pump_on=argument==0x14;
                if(!pump_on)last_disable_ack=time_ms;
            } else if(command==0xaf) {
                assert(initial_clear_complete && pump_on);
                assert((uint32_t)(time_ms-powered_at)>=100);panel_on=true;
            } else if(command==0xae)panel_on=false;
            else if(command==0xa8 || command==0xad || command==0xd3 || command==0x81 ||
                    command==0xd9 || command==0xd5 || command==0xda || command==0x20 || command==0xdb)++i;
            else if(command>=0xb0 && command<=0xb7)page=command&7U;
            else if(command<=0x0f)column=(uint8_t)((column&0xf0U)|command);
            else if(command>=0x10 && command<=0x1f)column=(uint8_t)((column&15U)|((command&15U)<<4));
        }
    }
}
static OledBusResult poll(uint32_t now) {
    assert(busy);
    if(always_fail) {
        if((uint32_t)(now-started)<OLED_BUS_TIMEOUT_MS)return OLED_BUS_BUSY;
        busy=false;++failures;return OLED_BUS_ERROR;
    }
    if((uint32_t)(now-started)<transfer_delay)return OLED_BUS_BUSY;
    if(fail_on_transfer && transfers==fail_on_transfer){busy=false;++failures;return OLED_BUS_ERROR;}
    consume();busy=false;return OLED_BUS_OK;
}
static uint32_t clock_now(void){return time_ms;}
static const OledHal hal={power,reset,start,poll,abort_bus,clock_now};
static void step(Oled *d,bool awake,uint32_t count){oled_service(d,&hal,awake,count,input_fault,time_ms++);}
static void fresh(Oled *d,uint32_t now) {
    time_ms=now;powered=false;reset_low=true;busy=false;always_fail=false;
    input_fault=false;transfers=0;failures=0;fail_on_transfer=0;transfer_delay=2;
    panel_on=false;pump_on=false;page=0;column=0;
    memset(ram,0xa5,sizeof ram);oled_init(d,&hal);
}
static void await_render(Oled *d,uint32_t count) {
    unsigned bounded=0;
    while(!(d->state==OLED_READY && d->displayed_valid && d->displayed_count==count && d->displayed_fault==input_fault)) {
        step(d,true,count);assert(++bounded<6000);
    }
    for(unsigned p=0;p<8;p++)for(unsigned x=0;x<128;x++)
        assert(ram[p][x]==oled_status_byte(count,input_fault,(uint8_t)p,(uint8_t)x));
}
int main(void) {
    Oled d;fresh(&d,0);await_render(&d,12345678);
    assert(panel_on && powered && pump_on);
    unsigned idle_transfers=transfers;
    for(unsigned n=0;n<1000;n++)step(&d,true,12345678);
    assert(transfers==idle_transfers); /* genuinely dirty, not repeated frames */
    step(&d,true,12345679);
    for(unsigned n=0;n<20;n++)step(&d,true,12345679);
    await_render(&d,87654321); /* a changed count during a frame is not lost */
    await_render(&d,COUNTER_MAX);
    assert(oled_pixel_byte(COUNTER_MAX,7,58)==0x7c);
    assert(oled_pixel_byte(123,7,58)==0);
    assert(oled_pixel_byte(0,8,0)==0 && oled_pixel_byte(0,0,128)==0);
    input_fault=true;await_render(&d,COUNTER_MAX);
    assert(d.displayed_fault && oled_status_byte(COUNTER_MAX,true,7,59)==0x54);
    input_fault=false;await_render(&d,COUNTER_MAX);
    transfer_delay=19; /* longest successful modeled transfer before timeout */
    unsigned limit=0;
    while(!oled_is_off(&d)){step(&d,false,COUNTER_MAX);assert(++limit<500);}
    assert(!powered && reset_low && !panel_on && !pump_on);
    assert(((uint32_t)(time_ms-last_disable_ack)-1U)*1000U>=120000U);
    puts("PASS: HS96 SPI startup/clear/charge-pump commands, bounded chunks, dirty/coalesced frames, MAX, shutdown guard");

    fresh(&d,0);await_render(&d,77);
    fail_on_transfer=transfers+4;await_render(&d,88);
    assert(d.errors==1 && failures==1);
    puts("PASS: injected mid-frame transport error discards display state and recovers the latest committed count");

    fresh(&d,0xfffffff0UL);await_render(&d,1);
    while(!oled_is_off(&d))step(&d,false,1);
    assert(!powered);
    for(unsigned cut=0;cut<300;cut++) {
        fresh(&d,0);
        for(unsigned n=0;n<cut;n++)step(&d,true,0);
        /* Sleep before reset release needs no SPI command to an unready IC. */
        limit=0;while(!oled_is_off(&d)){step(&d,false,0);assert(++limit<500);}
        assert(!powered);
    }
    puts("PASS: deadline wrap and sleep during every early startup tick");
    for(unsigned fault=1;fault<=259;fault++) {
        fresh(&d,0);fail_on_transfer=fault;await_render(&d,42);
        assert(d.errors==1 && failures==1);
    }
    puts("PASS: transport failure at each of259 startup/frame packet positions");
    puts("Host model only; target ISR timing, rail sequencing, pixels and current require hardware tests.");
}
