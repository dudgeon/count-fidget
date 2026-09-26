#ifndef Q5_BATTERY_H
#define Q5_BATTERY_H
#include <stdbool.h>
#include <stdint.h>
/* Battery gauge and storage protection from the switched SYS_LOAD divider.
 * On battery SYS_LOAD is the protected cell (less the charger BATFET and U7
 * drops); with valid USB the charger regulates SYS to 4.5V +/-2%. With the
 * 2.06% worst-case estimate error (VREFINT budget plus 0.1% divider), a full
 * cell (4.221V max) reads <=4.308V and USB SYS (>=4.41V) reads >=4.319V, so
 * BATTERY_USB_MV sits between them. STAT1 or STAT2 low (charging or fault)
 * independently proves an adapter; H/H at 4.3V is harmless either way.
 * Thresholds are loaded-cell voltages for a LIR2032 at ~1-2 mA; they are
 * engineering choices to be confirmed on the qualified cell. */
#define BATTERY_USB_MV 4313U
#define BATTERY_BAR4_MV 3950U
#define BATTERY_BAR3_MV 3800U
#define BATTERY_BAR2_MV 3700U
#define BATTERY_BAR1_MV 3550U  /* below: LO label (roughly the last 10-15%) */
#define BATTERY_CUTOFF_MV 3350U /* below: save and power off, leaving a storage reserve */
#define BATTERY_HYSTERESIS_MV 30U
#define BATTERY_FILTER_SAMPLES 4U
#define BATTERY_CUTOFF_SAMPLES 6U
typedef enum { CHARGE_UNKNOWN, CHARGE_NONE, CHARGE_ACTIVE, CHARGE_IDLE, CHARGE_FAULT } ChargeState;
typedef struct {
    uint32_t sum; uint16_t history[BATTERY_FILTER_SAMPLES]; uint8_t filled, next;
    uint16_t millivolts; uint8_t bars, low_count; bool valid, usb, low, cutoff;
    ChargeState charge;
} Battery;
void battery_reset(Battery *b);
/* sys_mv: SYS_LOAD millivolts from the calibrated ADC. stat1/stat2: true = pin HIGH. */
void battery_sample(Battery *b, uint16_t sys_mv, bool stat1, bool stat2);
#endif
