#include "counter.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef struct { Record *slots; int remaining; } Writer;
static bool write_word(void *p,unsigned slot,unsigned word,uint16_t value) {
    Writer *w=p;
    if (w->remaining==0) return false;
    if(w->remaining>0) --w->remaining;
    w->slots[slot].words[word]=value; return true;
}
static void hold(Counter *c,bool i,bool r,uint32_t start,uint32_t end) {
    for(uint32_t t=start;t<end;t++) counter_sample(c,i,r,t);
}
int main(void) {
    Counter c; counter_init(&c,123,0);
    for(uint32_t t=1;t<8;t++) counter_sample(&c,t%2,0,t);
    hold(&c,1,0,8,100); assert(c.count==124);
    hold(&c,1,0,100,40000); assert(c.count==124 && !c.awake);
    hold(&c,0,0,40000,40010); assert(c.count==124);
    hold(&c,1,0,40010,40020); assert(c.count==125 && c.awake);
    hold(&c,0,0,40020,40030); hold(&c,1,1,40030,40040); assert(c.count==0);
    hold(&c,0,1,40040,40050); hold(&c,1,1,40050,40060); assert(c.count==0);
    counter_init(&c,COUNTER_MAX,0); hold(&c,1,0,0,10); assert(c.count==COUNTER_MAX && c.overflow);
    counter_init(&c,0,0xFFFFFFF0UL);
    for (uint32_t n=0;n<40;n++) counter_sample(&c,1,0,0xFFFFFFF0UL+n);
    assert(c.count==1 && c.awake);
    counter_sample(&c,1,0,(uint32_t)(0xFFFFFFF0UL+SLEEP_MS+20)); assert(!c.awake);
    puts("PASS: bounce, held-key no-repeat/sleep, wake click, reset priority, overflow, timer wrap");
    Record slots[2]; memset(slots,0xFF,sizeof slots);
    uint32_t count,seq;unsigned s;assert(!journal_load(slots,&count,&seq,&s));
    Writer w={slots,-1};assert(journal_save(slots,41,write_word,&w));
    assert(journal_load(slots,&count,&seq,&s) && count==41);
    Record before[2];memcpy(before,slots,sizeof slots);
    for(int cut=0;cut<=9;cut++) {
        memcpy(slots,before,sizeof slots);w.remaining=cut;
        bool saved=journal_save(slots,42,write_word,&w);
        assert(journal_load(slots,&count,&seq,&s));
        assert(count==(saved?42U:41U));
    }
    memcpy(slots,before,sizeof slots);w.remaining=-1;
    assert(journal_save(slots,42,write_word,&w));
    assert(journal_load(slots,&count,&seq,&s));
    slots[s].words[4]^=1;assert(journal_load(slots,&count,&seq,&s) && count==41);
    for(unsigned k=0;k<100000;k++) {assert(journal_save(slots,k,write_word,&w));}
    assert(journal_load(slots,&count,&seq,&s) && count==99999);
    puts("PASS: blank memory, all 10 power-cut boundaries, CRC fallback, 100000 journal commits");
    puts("Host simulation only: target electrical, LCD, interrupt and brownout tests remain.");
}
