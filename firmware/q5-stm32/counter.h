#ifndef CLICK_COUNTER_H
#define CLICK_COUNTER_H
#include <stdbool.h>
#include <stdint.h>
#define COUNTER_MAX 99999999UL
#define DEBOUNCE_MS 8U
#define SLEEP_MS 30000UL
/* Count reset is deliberate: hold the reset key for RESET_HOLD_MS, then
 * release it. The display shows RST once armed. Holding longer than
 * RESET_ABANDON_MS (a key trapped in a pocket) or pressing COUNT at any point
 * during the hold cancels it. An MCU reset during the hold (USB DFU entry)
 * never zeroes the count because nothing is committed before release. */
#define RESET_HOLD_MS 2000UL
#define RESET_ABANDON_MS 10000UL
#define COUNTER_EVENT_INCREMENT 1U
#define COUNTER_EVENT_RESET 2U
#define COUNTER_EVENT_SATURATED 4U
typedef struct { bool stable, candidate; uint32_t since; } Debouncer;
typedef struct {
    uint32_t count, last_activity, reset_pressed_at;
    bool awake, overflow, dirty;
    bool reset_holding, reset_cancelled, reset_armed;
    Debouncer increment, reset;
} Counter;
/* Keys already held at initialization are stable, not new presses. */
void counter_init(Counter *c, uint32_t saved, uint32_t now, bool increment_held, bool reset_held);
/* Call at 1 ms intervals while debouncing; raw values true = pressed.
 * The target must wake on BOTH press and release edges, and re-arm before
 * sleeping. A held key does not repeat or prevent inactivity sleep.
 * Returns COUNTER_EVENT_* flags for this sample. Increment always wins over
 * a simultaneous or pending count reset. */
unsigned counter_sample(Counter *c, bool increment, bool reset, uint32_t now);
/* Power-on key press that switched the board on (Q5 soft power latch). */
unsigned counter_wake_press(Counter *c, uint32_t now);
#endif
