#include "journal.h"
#include "counter.h"
#include <string.h>
/* Reflected CRC-32 (IEEE), four bits per step: identical results to the
 * bitwise form in 64 bytes of table and about a quarter of the boot scan time. */
static const uint32_t crc_nibble[16]={
    0x00000000UL,0x1db71064UL,0x3b6e20c8UL,0x26d930acUL,0x76dc4190UL,0x6b6b51f4UL,0x4db26158UL,0x5005713cUL,
    0xedb88320UL,0xf00f9344UL,0xd6d6a3e8UL,0xcb61b38cUL,0x9b64c2b0UL,0x86d3d2d4UL,0xa00ae278UL,0xbdbdf21cUL};
uint32_t journal_crc(const uint32_t *words,unsigned count) {
    uint32_t crc=0xffffffffUL;
    for(unsigned i=0;i<count;i++)for(unsigned b=0;b<4;b++) {
        crc^=(words[i]>>(b*8))&255U;
        crc=(crc>>4)^crc_nibble[crc&15U];
        crc=(crc>>4)^crc_nibble[crc&15U];
    }
    return ~crc;
}
bool journal_record_valid(const uint32_t r[NV_WORDS]) {
    return r[0]==NV_FORMAT && r[2]<=COUNTER_MAX && r[3]<=1U &&
           r[4]==~r[1] && r[5]==~r[2] && r[6]==journal_crc(r,6) && r[7]==NV_COMMIT;
}
void journal_load(Journal *j,const NvHal *h) {
    memset(j,0,sizeof(*j));j->active=NV_SLOTS-1U;j->blank=true;
    for(unsigned s=0;s<NV_SLOTS;s++) {
        uint32_t r[NV_WORDS];bool readable=true;
        for(unsigned w=0;w<NV_WORDS;w++) {
            if(!h->read(h->context,s*NV_WORDS+w,&r[w])) {
                readable=false;j->scan_error=true;r[w]=0;
            }
            if(r[w])j->blank=false; /* STM32L0 EEPROM erase state is zero. */
        }
        if(!readable || !journal_record_valid(r))continue;
        uint32_t delta=r[1]-j->sequence;
        if(j->valid && ((delta==0 && (r[2]!=j->count || (r[3]!=0)!=j->fault)) ||
                        delta==0x80000000UL))j->scan_error=true;
        if(!j->valid || (delta && delta<0x80000000UL)) {
            j->valid=true;j->active=s;j->sequence=r[1];j->count=r[2];j->fault=r[3]!=0;
        }
    }
    if(j->scan_error || !j->valid)j->fault=true; /* First use requires explicit reset. */
}
bool journal_begin(Journal *j,uint32_t count,bool fault,uint32_t ticket) {
    if(j->busy || count>COUNTER_MAX)return false;
    uint32_t *r=j->record;
    r[0]=NV_FORMAT;r[1]=j->sequence+1U;r[2]=count;r[3]=fault?1U:0U;
    r[4]=~r[1];r[5]=~r[2];r[6]=journal_crc(r,6);r[7]=NV_COMMIT;
    j->destination=(j->active+1U)%NV_SLOTS;j->step=0;j->ticket=ticket;
    j->busy=true;j->pending=false;j->completed=false;j->failed=false;return true;
}
static void fail(Journal *j){j->busy=false;j->pending=false;j->failed=true;}
void journal_service(Journal *j,const NvHal *h,uint32_t now) {
    if(!j->busy)return;
    if(j->pending) {
        NvResult result=h->poll(h->context,now);
        if(result==NV_BUSY)return;
        if(result!=NV_OK){fail(j);return;}
        unsigned w=j->step==0?7U:j->step-1U;
        uint32_t actual;
        if(!h->read(h->context,j->destination*NV_WORDS+w,&actual) ||
           actual!=(j->step==0?0U:j->record[w])){fail(j);return;}
        j->pending=false;
        if(++j->step==NV_WORDS+1U) {
            for(unsigned i=0;i<NV_WORDS;i++) {
                if(!h->read(h->context,j->destination*NV_WORDS+i,&actual) ||
                   actual!=j->record[i]){fail(j);return;}
            }
            /* Commit acknowledgement is after write completion and readback. */
            j->count=j->record[2];j->fault=j->record[3]!=0;j->sequence=j->record[1];
            j->active=j->destination;j->valid=true;j->blank=false;
            j->busy=false;j->completed=true;return;
        }
        return; /* Always yield to input processing between word operations. */
    }
    unsigned w=j->step==0?7U:j->step-1U;
    if(!h->start(h->context,j->destination*NV_WORDS+w,
                 j->step==0?0U:j->record[w],now)){fail(j);return;}
    j->pending=true;
}
