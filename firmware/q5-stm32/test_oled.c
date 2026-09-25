#include "oled.h"
#include "counter.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static uint32_t time_ms,started,last_disable_ack,powered_at;
static unsigned transfers,failures,data_bytes;
static unsigned fail_on_transfer,transfer_delay;
static bool powered,reset_low,busy,always_fail,panel_on,pump_on,pump_ever;
static uint8_t queued[OLED_TX_MAX],length,ram[8][128],page,column;
static bool written[8][128];
static OledView view;
static void power(bool on) {
    if(on){powered_at=time_ms;memset(written,0,sizeof written);pump_ever=false;}
    /* SSD1315 6.9.2: after 8Dh 10h, typical tOFF 100ms before supply removal;
     * a controller whose pump never ran may be removed from reset directly. */
    if(!on && powered && pump_ever)assert((uint32_t)(time_ms-last_disable_ack)>=100U);
    powered=on;
}
static void reset(bool low) {
    if(!low)assert(powered && (uint32_t)(time_ms-powered_at)>=OLED_RESET_HOLD_MS);
    reset_low=low;
    if(low){panel_on=false;if(pump_on)last_disable_ack=time_ms;pump_on=false;}
}
static void abort_bus(void){busy=false;}
static bool start(const uint8_t *data,uint8_t count,uint32_t now) {
    assert(!busy && count && count<=OLED_TX_MAX);
    assert(powered && !reset_low);
    memcpy(queued,data,count);length=count;started=now;busy=true;++transfers;
    return true;
}
static bool frame_complete(void){for(unsigned p=0;p<8;p++)for(unsigned x=0;x<128;x++)if(!written[p][x])return false;return true;}
static void consume(void) {
    if(queued[0]==0x40) {
        assert(length>=2 && length<=OLED_CHUNK+1);
        for(unsigned i=1;i<length;i++) {
            assert(page<8 && column<128);written[page][column]=true;ram[page][column++]=queued[i];++data_bytes;
        }
    } else {
        assert(queued[0]==0);
        for(unsigned i=1;i<length;i++) {
            uint8_t command=queued[i];
            if(command==0x8d) {
                uint8_t argument=queued[++i];
                assert(argument==0x10 || argument==0x14);
                if(argument==0x14){assert(frame_complete());pump_ever=true;}
                if(pump_on && argument==0x10)last_disable_ack=time_ms;
                pump_on=argument==0x14;
            } else if(command==0xaf) {
                /* Complete first frame is in GDDRAM before the panel turns on. */
                assert(frame_complete() && pump_on);panel_on=true;
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
static bool rail=true;
static void step(Oled *d,bool awake){oled_service(d,&hal,awake,rail,&view,time_ms++);}
static void fresh(Oled *d,uint32_t now) {
    time_ms=now;powered=false;reset_low=true;busy=false;always_fail=false;
    transfers=0;failures=0;fail_on_transfer=0;transfer_delay=0;data_bytes=0;rail=true;
    panel_on=false;pump_on=false;pump_ever=false;page=0;column=0;
    view=(OledView){0,OLED_LABEL_NONE,OLED_BARS_HIDDEN,false};
    memset(ram,0xa5,sizeof ram);oled_init(d,&hal);
}
static bool shown(const Oled *d){
    return d->state==OLED_READY && !d->pending && d->shown_valid && d->shown.count==view.count && d->shown.label==view.label &&
           d->shown.bars==view.bars && d->shown.hide_digits==view.hide_digits;
}
static uint32_t await_render(Oled *d) {
    unsigned bounded=0;uint32_t begin=time_ms;
    while(!shown(d)) {step(d,true);assert(++bounded<6000);}
    assert(panel_on);
    for(unsigned p=0;p<8;p++)for(unsigned x=0;x<128;x++)
        assert(ram[p][x]==oled_frame_byte(&view,(uint8_t)p,(uint8_t)x));
    return time_ms-begin;
}
int main(void) {
    Oled d;fresh(&d,0);view.count=12345678;uint32_t startup=await_render(&d);
    assert(panel_on && powered && pump_on);
    /* Power enable to AFh in service steps: reset hold, init, one 128-packet
     * full frame, 8Dh and AFh; each packet costs a start and a completion
     * step here. The panel lights tAF (~100ms) after AFh. */
    assert(startup<=OLED_RESET_HOLD_MS+6U+2U*(1U+80U+2U));
    unsigned idle_transfers=transfers;
    for(unsigned n=0;n<1000;n++)step(&d,true);
    assert(transfers==idle_transfers); /* genuinely dirty, not repeated frames */
    /* A one-digit change sends only that 10-column cell: 6 pages x 2 packets. */
    unsigned before=transfers,bytes=data_bytes;view.count=12345679;await_render(&d);
    assert(transfers-before==12 && data_bytes-bytes==60);
    before=transfers;view.count=12345680;await_render(&d);assert(transfers-before==24);
    view.count=87654321;step(&d,true);step(&d,true);view.count=5;await_render(&d); /* changed mid-frame is not lost */
    view.count=COUNTER_MAX;view.label=OLED_LABEL_MAX;await_render(&d);
    assert(oled_frame_byte(&view,7,58)==0x7c);
    assert(oled_pixel_byte(123,7,58)==0 && oled_pixel_byte(0,8,0)==0 && oled_pixel_byte(0,0,128)==0);
    for(uint8_t label=OLED_LABEL_ERR;label<OLED_LABEL_COUNT;label++){
        before=transfers;view.label=label;await_render(&d);assert(transfers-before==2); /* label only */
        unsigned lit=0;for(unsigned x=58;x<69;x++)lit+=oled_frame_byte(&view,7,(uint8_t)x)!=0;assert(lit>=6);
    }
    for(uint8_t bars=0;bars<=4;bars++){
        before=transfers;view.bars=bars;await_render(&d);assert(transfers-before<=4);
        unsigned full=0;for(unsigned x=0;x<128;x++)full+=oled_frame_byte(&view,0,(uint8_t)x)==0x7e;
        assert(full==2U+3U*bars); /* end walls plus 3 columns per bar */
    }
    view.bars=OLED_BARS_HIDDEN;await_render(&d);for(unsigned x=0;x<128;x++)assert(oled_frame_byte(&view,0,(uint8_t)x)==0);
    view.hide_digits=true;view.label=OLED_LABEL_OPT;await_render(&d);
    for(unsigned p=1;p<7;p++)for(unsigned x=0;x<128;x++)assert(oled_frame_byte(&view,(uint8_t)p,(uint8_t)x)==0);
    view.hide_digits=false;view.label=OLED_LABEL_NONE;await_render(&d);
    transfer_delay=19; /* longest successful modeled transfer before timeout */
    unsigned limit=0;
    while(!oled_is_off(&d)){step(&d,false);assert(++limit<500);}
    assert(!powered && reset_low && !panel_on && !pump_on);
    assert((uint32_t)(time_ms-last_disable_ack)>=OLED_OFF_GUARD_MS);
    puts("PASS: HS96 SPI startup, first frame in GDDRAM before 8Dh/AFh, partial digit/label/icon redraw, MAX/labels/bars, shutdown guard");

    fresh(&d,0);view.count=77;await_render(&d);
    fail_on_transfer=transfers+4;view.count=88;await_render(&d);
    assert(d.errors==1 && failures==1);
    puts("PASS: injected mid-frame transport error discards display state and recovers the latest committed count");

    fresh(&d,0xfffffff0UL);view.count=1;await_render(&d);
    while(!oled_is_off(&d))step(&d,false);
    assert(!powered);
    for(unsigned cut=0;cut<300;cut++) {
        fresh(&d,0);
        for(unsigned n=0;n<cut;n++)step(&d,true);
        /* Sleep at every early startup tick: no SPI command to an unready IC,
         * and the tOFF guard applies whenever the pump could have run. */
        limit=0;while(!oled_is_off(&d)){step(&d,false);assert(++limit<500);}
        assert(!powered);
    }
    puts("PASS: deadline wrap and sleep during every early startup tick");
    /* Early power with no rail measurement: RES# stays low and nothing is
     * sent; the rail arriving later starts initialization immediately. */
    fresh(&d,0);rail=false;view.count=3;
    for(unsigned n=0;n<500;n++){step(&d,true);assert(transfers==0 && reset_low);}
    assert(powered);rail=true;uint32_t late=await_render(&d);assert(late<=6U+2U*(1U+128U+2U));
    /* Rail lost while running: orderly shutdown, stays off until rail returns. */
    rail=false;limit=0;while(!oled_is_off(&d)){step(&d,true);assert(++limit<500);}
    for(unsigned n=0;n<300;n++){step(&d,true);assert(!powered);}
    rail=true;await_render(&d);
    puts("PASS: module held in reset until the rail is measured; rail loss shuts down and waits for recovery");
    for(unsigned fault=1;fault<=80;fault++) {
        fresh(&d,0);fail_on_transfer=fault;view.count=42;await_render(&d);
        assert(d.errors==1 && failures==1);
    }
    puts("PASS: transport failure at each of80 startup/frame packet positions");
    puts("Host model only; target ISR timing, rail sequencing, pixels and current require hardware tests.");
}
