#ifndef Q4_INPUT_H
#define Q4_INPUT_H
#include "counter.h"
#include <stdbool.h>
#include <stdint.h>
#define INPUT_QUEUE_SIZE 256U
#define INPUT_INCREMENT 1U
#define INPUT_RESET 2U
typedef struct { uint32_t time; uint8_t raw; } InputSample;
typedef enum { INPUT_EMPTY, INPUT_SAMPLE, INPUT_GAP } InputResult;
/* One ISR producer, one foreground consumer. Call take with interrupts masked.
 * 255 usable samples; overflow is explicit, never silently overwrite history. */
typedef struct {
    volatile InputSample samples[INPUT_QUEUE_SIZE];
    volatile InputSample latest;
    volatile uint8_t head, tail, gap;
    volatile uint16_t dropped;
} InputQueue;
typedef struct { bool fault, reset_requested; uint32_t revision; } InputState;
void input_push(InputQueue *q,uint8_t raw,uint32_t time);
InputResult input_take(InputQueue *q,InputSample *sample);
void input_apply(InputState *s,Counter *c,InputResult result,const InputSample *sample);
#endif
