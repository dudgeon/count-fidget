#ifndef CLICK_COUNTER_H
#define CLICK_COUNTER_H
#include <stdbool.h>
#include <stdint.h>
#define COUNTER_MAX 99999999UL
#define DEBOUNCE_MS 8U
#define SLEEP_MS 30000UL
typedef struct { bool stable, candidate; uint32_t since; } Debouncer;
typedef struct {
    uint32_t count, last_activity;
    bool awake, overflow, dirty;
    Debouncer increment, reset;
} Counter;
void counter_init(Counter *c, uint32_t saved, uint32_t now);
/* Call at 1 ms intervals while debouncing; raw values true = pressed.
 * The target must wake on BOTH press and release edges, and re-arm before
 * sleeping. A held key does not repeat or prevent inactivity sleep. */
void counter_sample(Counter *c, bool increment, bool reset, uint32_t now);
#endif
