#ifndef Q4_APP_H
#define Q4_APP_H
#include "input.h"
#include "journal.h"
typedef struct {
    Counter counter;
    InputState input;
    Journal journal;
    bool storage_failed;
    uint32_t failed_revision;
} App;
void app_init(App *a,const NvHal *hal,uint32_t now);
void app_input(App *a,InputResult result,const InputSample *sample);
void app_service(App *a,const NvHal *hal,uint32_t now,bool power_good);
bool app_fault(const App *a);
bool app_settled(const App *a);
/* An idle fault is not a persistence acknowledgement. Backend quiescence and
 * display/ADC/input shutdown must additionally be checked by the target. */
bool app_can_idle(const App *a);
void app_storage_error(App *a);
#endif
