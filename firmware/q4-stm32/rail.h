#ifndef Q4_RAIL_H
#define Q4_RAIL_H
#include <stdbool.h>
#include <stdint.h>
#define RAIL_ON_MV 3080U
#define RAIL_OFF_MV 3070U
#define RAIL_STALE_MS 30U
typedef struct {uint32_t sampled_at;uint16_t millivolts;uint8_t rising_samples;bool valid,enabled;} Rail;
void rail_sample(Rail*r,uint16_t calibration,uint16_t raw,uint32_t now);
void rail_invalid(Rail*r);
bool rail_display_allowed(const Rail*r,uint32_t now);
#endif
