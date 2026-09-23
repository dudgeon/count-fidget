/* Independent bounded model tests; links unchanged Q3 production modules.
 * No MCU, electrical bus, rail, real-clock or physical FRAM emulation. */
#include "counter.h"
#include "input.h"
#include "oled.h"
#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <string.h>

static unsigned long input_cases, queue_schedules, torn_words, recovery_cuts, marker_patterns, oled_cases;
static unsigned long injected_bus_faults;
static unsigned case_number;
static const char *suite;
#define CHECK(x) do { if(!(x)){fprintf(stderr,"%s case %u line %d: %s\n",suite,case_number,__LINE__,#x);return 1;} } while(0)

/* Analytic event oracle: one stable press qualifies eight sampled milliseconds
 * after its first sample. Reset suppresses increment until its stable release. */
static int button_waveforms(void) {
    suite="qualified-button-events";
    const unsigned lengths[]={1,7,8,9,10,18,40};
    const uint32_t bases[]={0,0xfffffff0U};
    for(unsigned b=0;b<2;b++)for(unsigned a=0;a<7;a++)for(unsigned z=0;z<7;z++)
    for(unsigned offset=0;offset<=24;offset++)for(unsigned initial=0;initial<3;initial++) {
        const uint32_t values[]={0,99999998U,99999999U};
        unsigned ilen=lengths[a],rlen=lengths[z],is=16,rs=offset;
        uint32_t expected=values[initial];bool rst=false;
        Counter c;counter_init(&c,expected,bases[b]);
        for(unsigned t=0;t<96;t++) {
            /* Release is processed before a press that qualifies at the same
             * instant; simultaneous newly qualified reset has priority. */
            if(rlen>=9 && t==rs+rlen+8)rst=false;
            bool rp=rlen>=9 && t==rs+8,ip=ilen>=9 && t==is+8;
            if(rp){rst=true;expected=0;}
            else if(ip && !rst && expected<COUNTER_MAX)++expected;
            counter_sample(&c,t>=is && t<is+ilen,t>=rs && t<rs+rlen,bases[b]+t);
            CHECK(c.count==expected);
        }
        ++input_cases;++case_number;
    }
    return 0;
}

static void drain(InputQueue *q,InputState *state,Counter *c,unsigned budget) {
    InputSample sample;
    while(budget--) {
        InputResult r=input_take(q,&sample);
        if(r==INPUT_EMPTY)break;
        input_apply(state,c,r,&sample);
    }
}
static bool same_counter(const Counter *a,const Counter *b) {
    return a->count==b->count && a->awake==b->awake && a->dirty==b->dirty && a->overflow==b->overflow &&
        a->last_activity==b->last_activity && a->increment.stable==b->increment.stable &&
        a->increment.candidate==b->increment.candidate && a->increment.since==b->increment.since &&
        a->reset.stable==b->reset.stable && a->reset.candidate==b->reset.candidate && a->reset.since==b->reset.since;
}
static int queue_interleavings(void) {
    suite="queue-interleavings";case_number=0;
    /* All 4096 drain/no-drain schedules for twelve samples. The immediate
     * production counter is a scheduling oracle, not an independent debounce
     * implementation; the analytic waveform suite checks debounce separately. */
    for(unsigned pattern=0;pattern<8;pattern++)for(unsigned wrap=0;wrap<2;wrap++)
    for(unsigned schedule=0;schedule<4096;schedule++) {
        InputQueue q={0};InputState s={0};Counter c,immediate;
        uint32_t base=wrap?0xfffffff8U:0;
        counter_init(&c,12,base);counter_init(&immediate,12,base);
        for(unsigned t=0;t<12;t++) {
            uint8_t raw=(uint8_t)(pattern<4?pattern: t<9?pattern-4:0);
            counter_sample(&immediate,(raw&1)!=0,(raw&2)!=0,base+t);
            input_push(&q,raw,base+t);
            if(schedule&(1U<<t))drain(&q,&s,&c,1+(t%8));
        }
        drain(&q,&s,&c,64);CHECK(!s.fault && q.dropped==0 && same_counter(&c,&immediate));
        ++queue_schedules;++case_number;
    }
    /* Full capacity, overflow, repeated gaps and 1000 ring wraps. */
    for(unsigned n=1;n<=128;n++) {
        InputQueue q={0};InputState s={0};Counter c;counter_init(&c,77,0);
        for(unsigned t=0;t<n;t++)input_push(&q,INPUT_INCREMENT,t);
        drain(&q,&s,&c,128);
        CHECK(s.fault==(n>=64));CHECK(q.dropped==(n>=64?n-63:0));
        CHECK(c.count==(n>=64?77:n>=9?78:77));++queue_schedules;
    }
    InputQueue q={0};InputState s={0};Counter c;counter_init(&c,0,0);
    for(unsigned t=0;t<64000;t++) {
        input_push(&q,(t%32)<12?INPUT_INCREMENT:0,t);
        if(t%23==22)drain(&q,&s,&c,24);
    }
    drain(&q,&s,&c,64);CHECK(c.count==2000 && !s.fault && !q.dropped);++queue_schedules;
    return 0;
}

typedef struct {Record words[2];unsigned position,tear_at;uint16_t tear;bool tearing;} Storage;
static bool store_word(void *context,unsigned slot,unsigned word,uint16_t value) {
    Storage *s=context;
    if(s->tearing && s->position++==s->tear_at){s->words[slot].words[word]=s->tear;return false;}
    s->words[slot].words[word]=value;return true;
}
/* Independent CCITT-FALSE polynomial long division, used only to seed valid
 * sequence-wrap fixtures. The test oracle is old-or-new durable count. */
static uint16_t fixture_crc(const uint16_t *words) {
    uint32_t reg=65535;
    for(unsigned i=0;i<12;i++) {
        unsigned byte=(words[i/2]>>(8*(i%2)))&255;
        for(unsigned bit=0;bit<8;bit++) {
            bool feedback=((reg>>15)^((byte>>(7-bit))&1U))&1U;
            reg=(reg<<1)&65535U;if(feedback)reg^=0x1021U;
        }
    }
    return (uint16_t)reg;
}
static void seed_record(Record *record,uint32_t count,uint32_t sequence) {
    const Record value={{1,0,(uint16_t)sequence,(uint16_t)(sequence>>16),
                        (uint16_t)count,(uint16_t)(count>>16),0,0xc17c}};
    *record=value;record->words[6]=fixture_crc(record->words);
}
static int persistence_tears(void) {
    suite="journal-arbitrary-word-tears";case_number=0;
    for(unsigned scenario=0;scenario<4;scenario++) {
        Storage base;memset(&base,0,sizeof base);memset(base.words,255,sizeof base.words);
        uint32_t old=scenario==0?41:scenario==1?COUNTER_MAX:scenario==2?123:0;
        uint32_t next=scenario==1?0:old+1,sequence=scenario==2?0xffffffffU:10;
        if(scenario!=3){seed_record(&base.words[0],old,sequence);seed_record(&base.words[1],old-1,sequence-1);}
        uint32_t loaded,seq;unsigned slot;
        CHECK(journal_load(base.words,&loaded,&seq,&slot)==(scenario!=3) && loaded==old);
        for(unsigned cut=0;cut<9;cut++)for(unsigned tear=0;tear<65536;tear++) {
            Storage s=base;s.tearing=true;s.tear_at=cut;s.tear=(uint16_t)tear;
            CHECK(!journal_save(s.words,next,store_word,&s));
            bool valid=journal_load(s.words,&loaded,&seq,&slot);
            bool new_record=cut==8 && tear==0xc17c;
            CHECK(loaded==(new_record?next:old));
            CHECK(valid==(scenario!=3 || new_record));
            CHECK(seq==(new_record?(scenario==3?1:sequence+1):(scenario==3?0:sequence)));
            ++torn_words;
        }
        ++case_number;
    }
    return 0;
}

static jmp_buf power_cut;
static struct {Record records[2];uint16_t marker;unsigned writes,cut;} durable;
static void boundary(void){if(durable.writes==durable.cut)longjmp(power_cut,1);++durable.writes;}
static uint16_t marker_read(void *p){(void)p;return durable.marker;}
static bool marker_write(void *p,uint16_t value){(void)p;boundary();durable.marker=value;return true;}
static bool durable_write(void *p,unsigned slot,unsigned word,uint16_t value) {
    (void)p;boundary();durable.records[slot].words[word]=value;return true;
}
static bool torn_marker_write(void *p,uint16_t value){(void)value;durable.marker=*(uint16_t *)p;return false;}
static int recovery_power_cuts(void) {
    suite="fault-reset-power-cuts";case_number=0;
    for(unsigned preexisting=0;preexisting<2;preexisting++)for(unsigned cut=0;cut<=11;cut++) {
        memset(&durable,0,sizeof durable);memset(durable.records,255,sizeof durable.records);
        seed_record(&durable.records[0],77,10);durable.marker=preexisting?INPUT_FAULT_MARKER:INPUT_FAULT_CLEAR;
        durable.cut=cut;
        if(!setjmp(power_cut)) {
            Counter c;counter_init(&c,77,0);InputState s={true,false};
            for(unsigned t=0;t<=8;t++){InputSample sample={t,INPUT_INCREMENT|INPUT_RESET};input_apply(&s,&c,INPUT_SAMPLE,&sample);}
            CHECK(c.count==0 && c.dirty && s.reset_requested);
            input_persist_fault(&s,marker_read,marker_write,0);
            CHECK(journal_save(durable.records,c.count,durable_write,0));c.dirty=false;
            input_after_commit(&s,&c,0,marker_write,0);CHECK(!s.fault);
            for(unsigned t=9;t<32;t++){InputSample sample={t,INPUT_INCREMENT};input_apply(&s,&c,INPUT_SAMPLE,&sample);}
            CHECK(c.count==0); /* held INC is not a new press */
        }
        uint32_t count,seq;unsigned slot;CHECK(journal_load(durable.records,&count,&seq,&slot));
        CHECK(count==77 || count==0);
        if(durable.marker==INPUT_FAULT_CLEAR && (preexisting || durable.writes>0))CHECK(count==0);
        ++recovery_cuts;++case_number;
    }
    for(unsigned value=0;value<65536;value++) {
        Counter c;counter_init(&c,0,0);InputState s={true,true};uint16_t torn=(uint16_t)value;
        durable.marker=INPUT_FAULT_MARKER;
        input_after_commit(&s,&c,0,torn_marker_write,&torn);
        CHECK(s.fault && s.reset_requested); /* failed readback does not clear RAM confidence */
        CHECK((durable.marker==INPUT_FAULT_CLEAR)==(value==65535));++marker_patterns;
    }
    return 0;
}

/* Minimal logical controller: accepts byte prefixes before an injected bus
 * failure. Reset is assumed to stop panel/pump, as required by Q3's hardware
 * contract. We check timing/order and eventual RAM equality, not OLED physics. */
static struct {
    uint32_t now,started,powered_at,quiet_at,visible_at;
    bool powered,reset,busy,pump,panel,quiet,external_iref;
    uint8_t packet[OLED_TX_MAX],length,ram[8][128],page,column;
    unsigned transfers,fail_transfer,mode,stride,delay,poll_advance;
    bool failed;
} bus;
static void model_reset(bool low) {
    if(!low)assert(bus.powered && (uint32_t)(bus.now-bus.powered_at)>=25);
    /* Asserting reset cannot restart an already-running discharge interval. */
    if(low && !bus.quiet){bus.quiet=true;bus.quiet_at=bus.now;}
    bus.reset=low;if(low){bus.pump=false;bus.panel=false;}
}
static void model_power(bool on) {
    if(on){assert(bus.reset);bus.powered_at=bus.now;bus.quiet_at=bus.now;bus.quiet=true;bus.external_iref=false;}
    else if(bus.powered)assert(bus.quiet && (uint32_t)(bus.now-bus.quiet_at)>=105);
    bus.powered=on;
}
static void consume_prefix(unsigned bytes) {
    if(!bytes)return;
    if(bus.packet[0]==0x40) {
        if(bus.panel)assert((uint32_t)(bus.now-bus.visible_at)>=105);
        for(unsigned i=1;i<bytes;i++){assert(bus.page<8 && bus.column<128);bus.ram[bus.page][bus.column++]=bus.packet[i];}
        return;
    }
    assert(bus.packet[0]==0);
    for(unsigned i=1;i<bytes;i++) {
        unsigned op=bus.packet[i];
        if(op==0x8d || op==0xad || op==0xa8 || op==0xd3 || op==0x81 || op==0xd9 || op==0xd5 || op==0xda || op==0x20 || op==0xdb) {
            if(i+1>=bytes)break;
            unsigned arg=bus.packet[++i];
            if(op==0xad){assert(arg==0x40);bus.external_iref=true;}
            if(op==0x8d) {
                assert(arg==0x10 || arg==0x72);
                if(arg==0x72){assert(bus.external_iref && (uint32_t)(bus.now-bus.powered_at)>=105);for(unsigned p=0;p<8;p++)for(unsigned c=0;c<128;c++)assert(bus.ram[p][c]==0);bus.pump=true;bus.quiet=false;}
                else {assert(!bus.panel);if(bus.pump){bus.quiet=true;bus.quiet_at=bus.now;}bus.pump=false;}
            }
        } else if(op==0xaf){assert(bus.pump && (uint32_t)(bus.now-bus.powered_at)>=105);bus.panel=true;bus.visible_at=bus.now;}
        else if(op==0xae)bus.panel=false;
        else if(op>=0xb0 && op<=0xb7)bus.page=(uint8_t)(op&7);
        else if(op<=15)bus.column=(uint8_t)((bus.column&0xf0)|op);
        else if(op>=0x10 && op<=0x1f)bus.column=(uint8_t)((bus.column&15)|((op&15)<<4));
    }
}
static bool model_start(const uint8_t *data,uint8_t length,uint32_t now) {
    assert(bus.powered && !bus.reset && !bus.busy && length && length<=OLED_TX_MAX);
    ++bus.transfers;
    if(!bus.failed && bus.transfers==bus.fail_transfer && bus.mode==1){bus.failed=true;return false;}
    memcpy(bus.packet,data,length);bus.length=length;bus.started=now;bus.busy=true;return true;
}
static OledBusResult model_poll(uint32_t now) {
    assert(bus.busy);
    if((uint32_t)(now-bus.started)<bus.delay)return OLED_BUS_BUSY;
    bus.now+=bus.poll_advance;bus.busy=false;
    if(!bus.failed && bus.transfers==bus.fail_transfer && bus.mode==2) {
        consume_prefix(bus.length/2);bus.failed=true;return OLED_BUS_ERROR;
    }
    consume_prefix(bus.length);return OLED_BUS_OK;
}
static void model_abort(void){bus.busy=false;}
static uint32_t model_now(void){return bus.now;}
static const OledHal hal={model_power,model_reset,model_start,model_poll,model_abort,model_now};
static uint8_t golden[8][128];
static int display_trial(unsigned failure,unsigned mode,unsigned sleep_at,unsigned sleep_for,bool wrap,bool slow,bool make_golden) {
    Oled d;memset(&bus,0,sizeof bus);memset(bus.ram,0xa5,sizeof bus.ram);
    bus.now=wrap?0xffffff00U:0;bus.fail_transfer=failure;bus.mode=mode;
    bus.stride=slow?251:1;bus.delay=slow?19:1;bus.poll_advance=slow?17:0;
    oled_init(&d,&hal);
    for(unsigned step=0;step<12000;step++) {
        bool awake=step<sleep_at || step>=sleep_at+sleep_for;
        uint32_t count=step<30?step:12345678;
        bool fault=step>=50 && step<70;
        oled_service(&d,&hal,awake,count,fault,bus.now);bus.now+=bus.stride;
        if(step>sleep_at+sleep_for && step>70 && d.displayed_valid && d.displayed_count==12345678 && !d.displayed_fault && d.state==OLED_READY) {
            CHECK(bus.panel && bus.pump && bus.powered && !bus.reset);
            if(make_golden)memcpy(golden,bus.ram,sizeof golden);
            else CHECK(memcmp(golden,bus.ram,sizeof golden)==0);
            for(unsigned idle=0;idle<30;idle++){unsigned before=bus.transfers;oled_service(&d,&hal,true,12345678,false,bus.now++);CHECK(bus.transfers==before);}
            for(unsigned stop=0;stop<1000 && !oled_is_off(&d);stop++){oled_service(&d,&hal,false,12345678,false,bus.now);bus.now+=bus.stride;}
            CHECK(oled_is_off(&d) && !bus.powered && bus.reset);
            if(failure<=195 && failure)CHECK(bus.failed);
            if(bus.failed)++injected_bus_faults;
            ++oled_cases;return 0;
        }
    }
    CHECK(false);return 1;
}
static int display_interleavings(void) {
    suite="OLED-transfer-faults-and-sleep";case_number=0;
    if(display_trial(0,0,0,0,false,false,true))return 1;
    for(unsigned failure=1;failure<=200;failure++)for(unsigned mode=1;mode<=2;mode++)
    for(unsigned wrap=0;wrap<2;wrap++)for(unsigned slow=0;slow<2;slow++) {
        if(display_trial(failure,mode,0,0,wrap!=0,slow!=0,false))return 1;
        ++case_number;
    }
    const unsigned gaps[]={1,8,31,120};
    for(unsigned phase=0;phase<480;phase++)for(unsigned g=0;g<4;g++)for(unsigned wrap=0;wrap<2;wrap++) {
        if(display_trial(0,0,phase,gaps[g],wrap!=0,false,false))return 1;
        ++case_number;
    }
    return 0;
}

int main(void) {
    if(button_waveforms() || queue_interleavings() || persistence_tears() || recovery_power_cuts() || display_interleavings())return 1;
    printf("{\"analytic_button_waveforms\":%lu,\"queue_schedules_and_capacity_cases\":%lu,\"journal_torn_word_cases\":%lu,\"fault_reset_power_cut_prefixes\":%lu,\"fault_marker_clear_patterns\":%lu,\"oled_fault_sleep_schedules\":%lu,\"oled_bus_faults_actually_injected\":%lu}\n",
           input_cases,queue_schedules,torn_words,recovery_cuts,marker_patterns,oled_cases,injected_bus_faults);
    return 0;
}
