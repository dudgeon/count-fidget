#ifndef Q4_FRAM_H
#define Q4_FRAM_H
#include "journal.h"
/* One transaction asserts CS, transfers at most35 bytes, then deasserts CS.
 * Failure must leave CS high and abort peripheral; interrupts remain enabled. */
typedef struct {bool (*exchange)(void *context,const uint8_t *tx,uint8_t *rx,unsigned n);void *context;} FramBus;
typedef struct {FramBus bus;uint32_t cache[NV_WORDS];unsigned cached_record;uint32_t wake_at;bool cache_valid,ready,pending,asleep,waking;} Fram;
bool fram_init(Fram *f,const FramBus *bus);
bool fram_sleep(Fram *f);
bool fram_wake(Fram *f,uint32_t now);
bool fram_available(const Fram *f);
NvHal fram_storage(Fram *f);
#endif
