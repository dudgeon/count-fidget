/* Deterministic adversarial harness linked to the actual production modules.
 * Models storage completion/tears and input schedules; it is not MCU emulation. */
#include "app.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef struct {
    uint32_t words[NV_SLOTS*NV_WORDS],value,started;
    unsigned address,latency,starts,reads;
    bool pending,fail_start,fail_poll,fail_read,corrupt;
} Memory;
static bool rd(void *ctx,unsigned a,uint32_t *v){Memory*m=ctx;++m->reads;if(a>=NV_SLOTS*NV_WORDS||m->pending||m->fail_read)return false;*v=m->words[a];return true;}
static bool start(void *ctx,unsigned a,uint32_t v,uint32_t t){Memory*m=ctx;if(m->pending||m->fail_start)return false;assert(a<NV_SLOTS*NV_WORDS);m->address=a;m->value=v;m->started=t;m->pending=true;++m->starts;return true;}
static NvResult poll(void*ctx,uint32_t t){Memory*m=ctx;assert(m->pending);if((uint32_t)(t-m->started)<m->latency)return NV_BUSY;m->pending=false;if(m->fail_poll)return NV_ERROR;m->words[m->address]=m->corrupt?m->value^1U:m->value;return NV_OK;}
static NvHal hal(Memory*m){NvHal h={rd,start,poll,m};return h;}
#ifndef TEAR_STEP
#define TEAR_STEP 1U
#endif
static unsigned long tears,waves,queue_schedules,corruptions,interleavings,fault_idles;
static void finish(Journal*j,Memory*m,uint32_t *t){NvHal h=hal(m);for(unsigned i=0;j->busy&&i<10000;i++)journal_service(j,&h,(*t)++);assert(!j->busy&&!j->failed);}
static void save(Journal*j,Memory*m,uint32_t count,bool fault,uint32_t*t){assert(journal_begin(j,count,fault,0));finish(j,m,t);}
static void record(uint32_t*r,uint32_t seq,uint32_t count,bool fault){r[0]=NV_FORMAT;r[1]=seq;r[2]=count;r[3]=fault;r[4]=~seq;r[5]=~count;r[6]=journal_crc(r,6);r[7]=NV_COMMIT;}
static void journal_tears(void){
    /* Destination contains an older VALID record. A tear of invalidation must
     * not let a partially overwritten destination supersede the active slot. */
    Memory base={0};base.latency=8;record(base.words,100,12345,false);record(base.words+NV_WORDS,4,987,true);
    NvHal bh=hal(&base);Journal j;journal_load(&j,&bh);assert(j.valid&&j.count==12345&&!j.fault);
    assert(journal_begin(&j,12346,false,9));uint32_t t=0;
    for(unsigned stage=0;stage<NV_WORDS+1;stage++) {
        while(!j.pending)journal_service(&j,&bh,t++);
        assert(base.pending);Memory snapshot=base;uint32_t before=base.words[base.address],after=base.value;
        for(unsigned orientation=0;orientation<2;orientation++)for(uint32_t partial=0;partial<65536;partial+=TEAR_STEP) {
            Memory cut=snapshot;cut.pending=false;
            cut.words[cut.address]=orientation?(before&0xffffU)|(partial<<16):(before&0xffff0000UL)|partial;
            NvHal ch=hal(&cut);Journal reboot;journal_load(&reboot,&ch);
            assert(reboot.valid&&!reboot.fault&&(reboot.count==12345||reboot.count==12346));
            if(reboot.count==12346)assert(stage==NV_WORDS&&cut.words[cut.address]==after);
            ++tears;
        }
        do{journal_service(&j,&bh,t++);}while(j.pending);
    }
    assert(j.completed&&j.count==12346);
    /* Every single-bit corruption in latest record must fall back to prior. */
    for(unsigned word=0;word<NV_WORDS;word++)for(unsigned bit=0;bit<32;bit++) {
        Memory cut=base;cut.words[NV_WORDS+word]^=1UL<<bit;NvHal ch=hal(&cut);Journal reboot;journal_load(&reboot,&ch);
        assert(reboot.valid&&reboot.count==12345&&!reboot.fault);++corruptions;
    }
    /* Blank, damaged-only, duplicate/ambiguous serials and read failure. */
    Memory bad={0};NvHal h=hal(&bad);Journal x;journal_load(&x,&h);assert(x.blank&&!x.valid&&x.fault);
    bad.words[0]=1;journal_load(&x,&h);assert(!x.valid&&x.fault&&!x.blank);
    memset(&bad,0,sizeof bad);record(bad.words,7,1,false);record(bad.words+NV_WORDS,7,2,false);journal_load(&x,&h);assert(x.fault&&x.scan_error);
    record(bad.words+NV_WORDS,7+0x80000000UL,2,false);journal_load(&x,&h);assert(x.fault&&x.scan_error);
    bad.fail_read=true;journal_load(&x,&h);assert(x.fault&&x.scan_error);
    /* Ring overwrite and sequence wrap; old slot stays available until commit. */
    memset(&bad,0,sizeof bad);bad.latency=8;record(bad.words,0xfffffff0UL,0,false);journal_load(&x,&h);t=0xfffff000UL;
    for(unsigned i=1;i<=NV_SLOTS*4;i++){save(&x,&bad,i,false,&t);Journal reboot;journal_load(&reboot,&h);assert(reboot.count==i&&!reboot.fault&&reboot.sequence==(uint32_t)(0xfffffff0UL+i));}
}
static void sample(App*a,uint8_t raw,uint32_t t){InputSample s={t,raw};app_input(a,INPUT_SAMPLE,&s);}
static void app_finish(App*a,Memory*m,uint32_t*t){NvHal h=hal(m);for(unsigned i=0;i<20000;i++){app_service(a,&h,(*t)++,true);if(app_settled(a)&&!a->storage_failed)return;}assert(!"app failed to settle");}
static void behavior(void){
    /* Analytic clean pulse oracle across debounce boundaries and wrap. */
    for(unsigned offset=0;offset<17;offset++)for(unsigned high=1;high<=32;high++)for(unsigned stall=1;stall<=13;stall++){
        Counter c;uint32_t t=0xfffffff0UL+offset;counter_init(&c,17,t);InputQueue q={0};InputState state={0};
        for(unsigned tick=0;tick<90;tick++){
            uint8_t raw=tick>=4&&tick<4+high?INPUT_INCREMENT:0;input_push(&q,raw,t+tick);
            if(tick%stall==0||tick==89){InputSample s;InputResult r;while((r=input_take(&q,&s))!=INPUT_EMPTY)input_apply(&state,&c,r,&s);}
        }
        assert(!state.fault&&c.count==17+(high>=9));++waves;
    }
    Counter c;counter_init(&c,COUNTER_MAX-1,0);for(unsigned i=0;i<31000;i++)counter_sample(&c,true,false,i);
    assert(c.count==COUNTER_MAX&&!c.awake&&!c.overflow);
    for(unsigned i=31000;i<31010;i++)counter_sample(&c,false,false,i);
    for(unsigned i=31010;i<31020;i++)counter_sample(&c,true,false,i);
    assert(c.count==COUNTER_MAX&&c.overflow&&c.awake);
    counter_init(&c,5,0);counter_sample(&c,false,false,30001);assert(!c.awake);
    for(unsigned i=30002;i<30020;i++)counter_sample(&c,true,false,i);assert(c.count==6&&c.awake);
    for(unsigned i=30020;i<40000;i++)counter_sample(&c,true,false,i);assert(c.count==6);
    for(unsigned i=40000;i<40010;i++)counter_sample(&c,true,true,i);assert(c.count==0);
    /* Actual queue + app while every EEPROM word takes worst-case8ms. */
    for(unsigned latency=0;latency<=8;latency++)for(unsigned stride=1;stride<INPUT_QUEUE_SIZE;stride++) {
        Memory m={0};m.latency=latency;record(m.words,0,0,false);NvHal h=hal(&m);App a;app_init(&a,&h,0);InputQueue q={0};uint32_t t=0;
        for(;t<1600;t++) {
            input_push(&q,(t%40)<20?INPUT_INCREMENT:0,t);
            if(t%stride==0)for(unsigned n=0;n<INPUT_QUEUE_SIZE;n++){InputSample s;InputResult r=input_take(&q,&s);if(r==INPUT_EMPTY)break;app_input(&a,r,&s);}
            app_service(&a,&h,t,true);
        }
        InputSample s;InputResult r;while((r=input_take(&q,&s))!=INPUT_EMPTY)app_input(&a,r,&s);
        app_finish(&a,&m,&t);assert(a.counter.count==40&&a.journal.count==40&&!app_fault(&a));++queue_schedules;
    }
}
static void fault_recovery(void){
    /* Cut any stage of an in-flight clean reset, then inject a second gap.
     * The first reset transaction may never clear that later uncertainty. */
    for(unsigned stop=0;stop<200;stop++) {
        Memory m={0};m.latency=8;record(m.words,7,55,true);NvHal h=hal(&m);App a;app_init(&a,&h,0);uint32_t t=0;
        for(;t<10;t++)sample(&a,INPUT_INCREMENT|INPUT_RESET,t);
        assert(a.input.reset_requested&&a.counter.count==0&&app_fault(&a));
        for(unsigned n=0;n<stop;n++)app_service(&a,&h,t++,true);
        InputSample gap={t,INPUT_INCREMENT};app_input(&a,INPUT_GAP,&gap);
        for(unsigned n=0;n<1000;n++){sample(&a,INPUT_INCREMENT,t);app_service(&a,&h,t++,true);}
        assert(app_fault(&a)&&a.counter.count==0&&a.journal.fault);
        for(unsigned n=0;n<10;n++)sample(&a,INPUT_INCREMENT|INPUT_RESET,t++);
        app_finish(&a,&m,&t);assert(!app_fault(&a)&&a.journal.count==0);
        for(unsigned n=0;n<20;n++)sample(&a,INPUT_INCREMENT,t++);
        assert(a.counter.count==0); /* held INC must not synthesize after recovery */
        for(unsigned n=0;n<10;n++)sample(&a,0,t++);
        for(unsigned n=0;n<10;n++)sample(&a,INPUT_INCREMENT,t++);
        assert(a.counter.count==1);++interleavings;
    }
    for(unsigned failure=0;failure<3;failure++){
        Memory m={0};m.latency=8;record(m.words,0,0,false);NvHal h=hal(&m);App a;app_init(&a,&h,0);uint32_t t=0;app_finish(&a,&m,&t);
        m.fail_start=failure==0;m.fail_poll=failure==1;m.corrupt=failure==2;
        for(unsigned n=0;n<10;n++)sample(&a,INPUT_INCREMENT,t++);
        for(unsigned n=0;n<200;n++)app_service(&a,&h,t++,true);
        assert(a.storage_failed&&app_fault(&a));unsigned starts=m.starts;
        for(unsigned n=0;n<100;n++)app_service(&a,&h,t++,true);assert(m.starts==starts);
        m.fail_start=m.fail_poll=m.corrupt=false;
        for(unsigned n=0;n<10;n++)sample(&a,INPUT_RESET,t++);
        app_finish(&a,&m,&t);assert(!app_fault(&a)&&a.journal.count==0);
    }
    /* Overflow counts never wrap, and exact255 capacity is not a false gap. */
    for(unsigned n=INPUT_QUEUE_SIZE-1;n<INPUT_QUEUE_SIZE+67;n++) {InputQueue q={0};for(unsigned i=0;i<n;i++)input_push(&q,0,i);InputSample s;InputResult r=input_take(&q,&s);assert(r==(n==INPUT_QUEUE_SIZE-1?INPUT_SAMPLE:INPUT_GAP));}
    InputQueue q={0};for(unsigned n=0;n<70000;n++)input_push(&q,0,n);assert(q.dropped==65535);
}
static void fault_idle(void){
    /* A permanent read/start/poll/readback failure cannot acknowledge an
     * unsaved count, but must permit fault-idle after inactivity. Retry only
     * follows a NEW reset press; INC wake and held reset remain faulted. */
    for(unsigned fault=0;fault<4;fault++)for(unsigned wrap=0;wrap<2;wrap++){
        Memory m={0};record(m.words,3,77,false);m.fail_read=fault==0;
        NvHal h=hal(&m);App a;uint32_t base=wrap?0xfffffff0UL:0,t=base;
        app_init(&a,&h,t);
        m.fail_start=fault==1;m.fail_poll=fault==2;m.corrupt=fault==3;
        if(fault)for(unsigned i=0;i<10;i++)sample(&a,INPUT_INCREMENT,t++);
        for(unsigned i=0;i<60000;i++){sample(&a,0,t);app_service(&a,&h,t++,true);}
        assert(!a.counter.awake && !a.journal.busy && a.storage_failed && app_fault(&a));
        assert(!app_settled(&a) && app_can_idle(&a));
        uint32_t count=a.counter.count,saved=a.journal.count;unsigned starts=m.starts;
        for(unsigned i=0;i<20;i++){sample(&a,INPUT_INCREMENT,t);app_service(&a,&h,t++,true);}
        assert(a.counter.awake && app_fault(&a) && a.counter.count==count && a.journal.count==saved && m.starts==starts);
        for(unsigned i=0;i<10;i++){sample(&a,0,t);app_service(&a,&h,t++,true);}
        for(unsigned i=0;i<1000;i++){sample(&a,INPUT_RESET,t);app_service(&a,&h,t++,true);}
        assert(app_fault(&a) && a.storage_failed && !a.input.reset_requested);
        unsigned held_starts=m.starts;
        for(unsigned i=0;i<60000;i++){sample(&a,INPUT_RESET,t);app_service(&a,&h,t++,true);}
        assert(m.starts==held_starts && !a.counter.awake && app_can_idle(&a) && !app_settled(&a));
        m.fail_read=m.fail_start=m.fail_poll=m.corrupt=false;
        for(unsigned i=0;i<10;i++)sample(&a,0,t++);
        for(unsigned i=0;i<10;i++)sample(&a,INPUT_RESET,t++);
        assert(a.input.reset_requested && !a.storage_failed && app_fault(&a) && !app_can_idle(&a));
        app_finish(&a,&m,&t);assert(app_settled(&a) && app_can_idle(&a) && !app_fault(&a) && a.journal.count==0);
        ++fault_idles;
    }
    /* An ordinary outstanding write may never pass via the fault-idle path. */
    Memory m={0};record(m.words,1,4,false);NvHal h=hal(&m);App a;app_init(&a,&h,0);
    for(uint32_t t=0;t<10;t++)sample(&a,INPUT_INCREMENT,t);
    assert(!app_settled(&a) && !app_can_idle(&a));app_service(&a,&h,10,true);
    assert(a.journal.busy && !app_can_idle(&a));
}
int main(void){journal_tears();behavior();fault_recovery();fault_idle();printf("{\"torn_word_reboots\":%lu,\"single_bit_corruptions\":%lu,\"button_waveforms\":%lu,\"queue_storage_schedules\":%lu,\"recovery_interleavings\":%lu,\"fault_idle_recovery_scenarios\":%lu,\"hardware_executed\":false}\n",tears,corruptions,waves,queue_schedules,interleavings,fault_idles);return 0;}
