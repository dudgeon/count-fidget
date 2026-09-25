#ifndef Q4_JOURNAL_H
#define Q4_JOURNAL_H
#include <stdbool.h>
#include <stdint.h>
#define NV_SLOTS 96U
#define NV_WORDS 8U
#define NV_BASE 0x08080c00UL
#define NV_SIZE (NV_SLOTS*NV_WORDS*4U)
#define NV_FORMAT 0x51443401UL
#define NV_COMMIT 0x434d5434UL
typedef enum { NV_BUSY, NV_OK, NV_ERROR } NvResult;
typedef struct {
    bool (*read)(void *context,unsigned word,uint32_t *value);
    bool (*start)(void *context,unsigned word,uint32_t value,uint32_t now);
    NvResult (*poll)(void *context,uint32_t now);
    void *context;
} NvHal;
typedef struct {
    uint32_t count, sequence;
    bool fault, valid, blank, scan_error;
    unsigned active, destination, step;
    uint32_t record[NV_WORDS];
    uint32_t ticket;
    bool busy, pending, completed, failed;
} Journal;
void journal_load(Journal *j,const NvHal *hal);
bool journal_begin(Journal *j,uint32_t count,bool fault,uint32_t ticket);
void journal_service(Journal *j,const NvHal *hal,uint32_t now);
bool journal_record_valid(const uint32_t record[NV_WORDS]);
uint32_t journal_crc(const uint32_t *words,unsigned count);
#endif
