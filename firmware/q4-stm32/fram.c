#include "fram.h"
#include <string.h>
static bool exchange(Fram*f,const uint8_t*t,uint8_t*r,unsigned n){if(!f->ready||f->asleep)return false;if(f->bus.exchange(f->bus.context,t,r,n))return true;f->cache_valid=false;f->ready=false;return false;}
static bool status(Fram*f,uint8_t*s){uint8_t tx[2]={5,0},rx[2];if(!exchange(f,tx,rx,2))return false;*s=rx[1];return !(*s&0x71U);}
bool fram_init(Fram*f,const FramBus*bus){
    memset(f,0,sizeof(*f));f->bus=*bus;f->ready=true;
    uint8_t tx=4,rx,s,idtx[10]={0x9f},id[10];
    if(!exchange(f,&tx,&rx,1)||!status(f,&s)||(s&0x0eU)||!exchange(f,idtx,id,10)){f->ready=false;return false;}
    for(unsigned i=1;i<=6;i++)if(id[i]!=0x7f){f->ready=false;return false;}
    /* FM25V02A family/density/subcode; allow documented die revision field. */
    if(id[7]!=0xc2||id[8]!=0x22||(id[9]&0xc7U)){f->ready=false;return false;}
    return true;
}
static bool read_word(void*ctx,unsigned word,uint32_t*value){
    Fram*f=ctx;if(word>=NV_SLOTS*NV_WORDS||f->pending)return false;
    unsigned record=word/NV_WORDS;
    if(!f->cache_valid||record!=f->cached_record){
        uint8_t tx[3+NV_WORDS*4]={3},rx[sizeof tx];unsigned address=record*NV_WORDS*4;
        tx[1]=(uint8_t)(address>>8);tx[2]=(uint8_t)address;
        if(!exchange(f,tx,rx,sizeof tx))return false;
        for(unsigned i=0;i<NV_WORDS;i++)f->cache[i]=(uint32_t)rx[3+i*4]|((uint32_t)rx[4+i*4]<<8)|((uint32_t)rx[5+i*4]<<16)|((uint32_t)rx[6+i*4]<<24);
        f->cached_record=record;f->cache_valid=true;
    }
    *value=f->cache[word%NV_WORDS];return true;
}
static bool start_word(void*ctx,unsigned word,uint32_t value,uint32_t now){
    (void)now;Fram*f=ctx;if(word>=NV_SLOTS*NV_WORDS||f->pending)return false;
    uint8_t enable=6,discard,s;f->cache_valid=false;
    if(!status(f,&s)||(s&0x0cU)||!exchange(f,&enable,&discard,1)||!status(f,&s)||!(s&2U))return false;
    unsigned address=word*4;uint8_t tx[7]={2,(uint8_t)(address>>8),(uint8_t)address,(uint8_t)value,(uint8_t)(value>>8),(uint8_t)(value>>16),(uint8_t)(value>>24)},rx[7];
    if(!exchange(f,tx,rx,sizeof tx))return false;
    f->pending=true;return true;
}
static NvResult complete(void*ctx,uint32_t now){(void)now;Fram*f=ctx;if(!f->pending)return NV_ERROR;f->pending=false;uint8_t s;return status(f,&s)&&!(s&0x0eU)?NV_OK:NV_ERROR;}
NvHal fram_storage(Fram*f){NvHal h={read_word,start_word,complete,f};return h;}

bool fram_available(const Fram*f){return f->ready&&!f->asleep;}
bool fram_sleep(Fram*f){
    if(f->pending||!f->ready)return false;
    if(f->asleep)return true;
    uint8_t command=0xb9,discard;
    if(!exchange(f,&command,&discard,1))return false;
    f->cache_valid=false;f->asleep=true;f->waking=false;return true;
}
bool fram_wake(Fram*f,uint32_t now){
    if(!f->ready)return false;
    if(!f->asleep)return true;
    if(!f->waking){
        /* First falling CS wakes the FM25V02A; this byte is ignored in sleep.
         *2ms also covers tick phase and HSI tolerance against400us maximum. */
        uint8_t ignored=0x03,discard;
        if(!f->bus.exchange(f->bus.context,&ignored,&discard,1)){f->cache_valid=false;f->ready=false;return false;}
        f->wake_at=now;f->waking=true;return false;
    }
    if((uint32_t)(now-f->wake_at)<2U)return false;
    f->asleep=false;f->waking=false;return true;
}
