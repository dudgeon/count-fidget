#include "input.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static void drain(InputQueue *q,InputState *s,Counter *c) {
    InputSample sample;InputResult result;
    while((result=input_take(q,&sample))!=INPUT_EMPTY)input_apply(s,c,result,&sample);
}
static void samples(InputQueue *q,uint32_t start,unsigned count,uint8_t raw) {
    for(unsigned i=0;i<count;i++)input_push(q,raw,start+i);
}
static uint16_t marker;
static unsigned marker_writes;
static bool reject_write;
static uint16_t read_marker(void *p){(void)p;return marker;}
static bool write_marker(void *p,uint16_t value) {
    (void)p;++marker_writes;if(reject_write)return false;marker=value;return true;
}
int main(void) {
    InputQueue q={0};InputState s={0};Counter c;counter_init(&c,88888889,0);
    /* The old foreground-only sample at0 and9ms misses this reset entirely.
     * Timer samples taken while a slow journal/render blocks foreground do not. */
    Counter old=c;counter_sample(&old,false,false,0);counter_sample(&old,false,false,9);
    samples(&q,0,9,INPUT_RESET);input_push(&q,0,9);drain(&q,&s,&c);
    assert(old.count==88888889 && c.count==0 && c.dirty && !s.fault);
    puts("PASS: timestamped ISR samples preserve an entire reset pulse during a9ms foreground stall");

    counter_init(&c,0,0);memset(&q,0,sizeof q);memset(&s,0,sizeof s);
    for(unsigned cycle=0;cycle<1000;cycle++) {
        uint32_t t=cycle*24U;
        samples(&q,t,11,INPUT_INCREMENT);samples(&q,t+11,13,0);
        drain(&q,&s,&c);
    }
    assert(c.count==1000 && !s.fault && q.dropped==0);
    /* Simultaneous qualified reset has priority over increment. */
    samples(&q,24000,9,INPUT_INCREMENT|INPUT_RESET);drain(&q,&s,&c);assert(c.count==0);
    puts("PASS:1000 delayed foreground batches across ring wraps, release and simultaneous reset priority");

    memset(&q,0,sizeof q);memset(&s,0,sizeof s);counter_init(&c,15,0);
    samples(&q,0,INPUT_QUEUE_SIZE+20,INPUT_INCREMENT);drain(&q,&s,&c);
    assert(s.fault && q.dropped==21 && c.count==15);
    marker=INPUT_FAULT_CLEAR;marker_writes=0;reject_write=true;
    input_persist_fault(&s,read_marker,write_marker,0);assert(s.fault && marker==INPUT_FAULT_CLEAR);
    reject_write=false;input_persist_fault(&s,read_marker,write_marker,0);
    assert(marker==INPUT_FAULT_MARKER);
    /* Reboot interprets all nonblank markers as uncertain, never as clear. */
    InputState reboot={marker!=INPUT_FAULT_CLEAR,false};assert(reboot.fault);
    samples(&q,100,20,0);samples(&q,120,12,INPUT_INCREMENT);drain(&q,&s,&c);
    assert(c.count==15 && s.fault); /* increments frozen after history loss */
    samples(&q,140,9,INPUT_RESET);drain(&q,&s,&c);
    assert(c.count==0 && c.dirty && s.reset_requested);
    input_after_commit(&s,&c,15,write_marker,0);assert(marker==INPUT_FAULT_MARKER && s.fault);
    c.dirty=false;input_after_commit(&s,&c,15,write_marker,0);assert(s.fault);
    reject_write=true;input_after_commit(&s,&c,0,write_marker,0);
    assert(s.fault && marker==INPUT_FAULT_MARKER); /* successful count0 commit, failedclear */
    reject_write=false;input_after_commit(&s,&c,0,write_marker,0);
    assert(!s.fault && !s.reset_requested && marker==INPUT_FAULT_CLEAR);
    puts("PASS: explicit overflow, frozen increments, durable fault ordering, failed write/clear retry and reset recovery");

    memset(&q,0,sizeof q);memset(&s,0,sizeof s);counter_init(&c,0,0xfffffff8UL);
    samples(&q,0xfffffff8UL,10,INPUT_INCREMENT);drain(&q,&s,&c);assert(c.count==1);
    /* Wake captures the first held level; timer samples establish debounce;
     * release before LPM4 is queued instead of being silently discarded. */
    samples(&q,2,12,INPUT_INCREMENT);drain(&q,&s,&c);assert(c.count==1);
    samples(&q,14,10,0);drain(&q,&s,&c);assert(!c.increment.stable);
    samples(&q,24,10,INPUT_INCREMENT);drain(&q,&s,&c);assert(c.count==2);
    for(unsigned n=0;n<70000;n++)input_push(&q,0,n);
    assert(q.dropped==65535U);drain(&q,&s,&c);assert(s.fault);
    puts("PASS: timestamp wrap, first/held/released wake input and saturating overflow diagnostics");

    memset(&q,0,sizeof q);counter_init(&c,15,0);s.fault=true;s.reset_requested=false;
    samples(&q,0,9,INPUT_INCREMENT|INPUT_RESET);drain(&q,&s,&c);
    assert(c.count==0 && s.reset_requested);c.dirty=false;marker=INPUT_FAULT_MARKER;
    input_after_commit(&s,&c,0,write_marker,0);assert(!s.fault);
    samples(&q,9,12,INPUT_INCREMENT);drain(&q,&s,&c);assert(c.count==0);
    samples(&q,21,10,0);samples(&q,31,10,INPUT_INCREMENT);drain(&q,&s,&c);assert(c.count==1);
    puts("PASS: holding increment through fault-reset recovery produces no synthetic new press");
}
