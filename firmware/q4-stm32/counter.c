#include "counter.h"
#include <string.h>
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
