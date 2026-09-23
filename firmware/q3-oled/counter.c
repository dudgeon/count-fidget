#include "counter.h"
#include <string.h>
#define COMMITTED 0xC17CU
#define FORMAT_VERSION 1U
static bool update(Debouncer *b, bool raw, uint32_t now) {
    if (raw != b->candidate) { b->candidate = raw; b->since = now; }
    if (b->stable != b->candidate && (uint32_t)(now-b->since) >= DEBOUNCE_MS) {
        b->stable = b->candidate;
        return b->stable;
    }
    return false;
}
void counter_init(Counter *c, uint32_t saved, uint32_t now) {
    memset(c,0,sizeof(*c));
    c->count = saved <= COUNTER_MAX ? saved : 0;
    c->awake = true; c->last_activity = now;
    c->increment.since = c->reset.since = now;
}
void counter_sample(Counter *c, bool inc, bool rst, uint32_t now) {
    bool ip = update(&c->increment,inc,now), rp = update(&c->reset,rst,now);
    if (rp || ip) {
        c->awake = true; c->last_activity = now;
        /* Reset has priority if both presses qualify together; ignore count
         * while reset is held. A later release never generates a count. */
        if (rp) { c->count = 0; c->overflow = false; c->dirty = true; }
        else if (ip && !c->reset.stable) {
            if (c->count < COUNTER_MAX) { ++c->count; c->dirty = true; }
            else c->overflow = true;
        }
    }
    if ((uint32_t)(now-c->last_activity) >= SLEEP_MS) c->awake = false;
}
static uint16_t crc16(const uint16_t *w) {
    uint16_t crc = 0xFFFF;
    for (unsigned i=0;i<6;i++) {
        for (unsigned b=0;b<2;b++) {
            crc ^= (uint16_t)(((w[i]>>(b*8))&255U)<<8);
            for (unsigned j=0;j<8;j++) crc = (uint16_t)((crc&0x8000U) ? ((uint32_t)crc<<1)^0x1021U : (uint32_t)crc<<1);
        }
    }
    return crc;
}
static uint32_t unpack(const uint16_t *w) { return (uint32_t)w[0] | ((uint32_t)w[1]<<16); }
static bool valid(const Record *r) {
    return r->words[7] == COMMITTED && r->words[0] == FORMAT_VERSION &&
           r->words[1] == 0 && r->words[6] == crc16(r->words) &&
           unpack(&r->words[4]) <= COUNTER_MAX;
}
bool journal_load(const Record slots[2], uint32_t *count, uint32_t *seq, unsigned *slot) {
    bool a=valid(&slots[0]), b=valid(&slots[1]);
    if (!a && !b) { *count=0; *seq=0; *slot=1; return false; }
    unsigned s = a ? 0U : 1U;
    if (a && b) {
        uint32_t delta = unpack(&slots[1].words[2])-unpack(&slots[0].words[2]);
        if (delta != 0 && delta < 0x80000000UL) s=1;
    }
    *count=unpack(&slots[s].words[4]); *seq=unpack(&slots[s].words[2]); *slot=s;
    return true;
}
bool journal_save(Record slots[2], uint32_t count, WriteWord write, void *context) {
    if (count>COUNTER_MAX) return false;
    uint32_t old,seq; unsigned active;
    (void)journal_load(slots,&old,&seq,&active);
    unsigned dest=active^1U; ++seq;
    Record next={{FORMAT_VERSION,0,(uint16_t)seq,(uint16_t)(seq>>16),
                  (uint16_t)count,(uint16_t)(count>>16),0,COMMITTED}};
    next.words[6]=crc16(next.words);
    /* Invalidate target BEFORE touching its payload; commit LAST. Keep the
     * previous slot untouched. Target HAL must use aligned 16-bit volatile
     * FRAM writes, compiler barriers, FRAM write protection and brownout
     * supervision. This portable model does not establish electrical atomicity. */
    if (!write(context,dest,7,0)) return false;
    for (unsigned i=0;i<7;i++) if (!write(context,dest,i,next.words[i])) return false;
    return write(context,dest,7,COMMITTED);
}
