#include "counter.h"
#include <string.h>
/* Returns +1 on a debounced press edge, -1 on a debounced release edge. */
static int update(Debouncer *b, bool raw, uint32_t now) {
    if (raw != b->candidate) { b->candidate = raw; b->since = now; }
    if (b->stable != b->candidate && (uint32_t)(now-b->since) >= DEBOUNCE_MS) {
        b->stable = b->candidate;
        return b->stable ? 1 : -1;
    }
    return 0;
}
void counter_init(Counter *c, uint32_t saved, uint32_t now, bool inc, bool rst) {
    memset(c,0,sizeof(*c));
    c->count = saved <= COUNTER_MAX ? saved : 0;
    c->awake = true; c->last_activity = now;
    c->increment.since = c->reset.since = now;
    c->increment.stable = c->increment.candidate = inc;
    c->reset.stable = c->reset.candidate = rst;
    /* A reset key already down at boot has no observed press edge: it can
     * never arm, so its eventual release is ignored. */
}
static unsigned increment(Counter *c) {
    c->dirty = true;
    if (c->count < COUNTER_MAX) { ++c->count; return COUNTER_EVENT_INCREMENT; }
    c->overflow = true; return COUNTER_EVENT_SATURATED;
}
unsigned counter_wake_press(Counter *c, uint32_t now) {
    c->awake = true; c->last_activity = now;
    return increment(c);
}
unsigned counter_sample(Counter *c, bool inc, bool rst, uint32_t now) {
    unsigned events = 0;
    int ie = update(&c->increment,inc,now), re = update(&c->reset,rst,now);
    if (ie || re) { c->awake = true; c->last_activity = now; }
    if (re > 0) {
        c->reset_holding = true; c->reset_armed = false;
        c->reset_pressed_at = now; c->reset_cancelled = c->increment.stable;
    }
    /* Increment wins: any COUNT press or hold during the reset hold cancels it. */
    if (ie > 0) events |= increment(c);
    if (c->reset_holding && c->increment.stable) { c->reset_cancelled = true; c->reset_armed = false; }
    if (c->reset_holding && !c->reset_cancelled) {
        uint32_t held = now - c->reset_pressed_at;
        if (held > RESET_ABANDON_MS) { c->reset_cancelled = true; c->reset_armed = false; }
        else if (held >= RESET_HOLD_MS && !c->reset_armed) {
            c->reset_armed = true; c->last_activity = now; /* keep the RST prompt visible */
        }
    }
    if (re < 0) {
        if (c->reset_holding && c->reset_armed && !c->reset_cancelled) {
            c->count = 0; c->overflow = false; c->dirty = true; events |= COUNTER_EVENT_RESET;
        }
        c->reset_holding = c->reset_armed = c->reset_cancelled = false;
    }
    if ((uint32_t)(now-c->last_activity) >= SLEEP_MS) c->awake = false;
    return events;
}
