#include "fram.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef struct {uint8_t bytes[8192],status;unsigned calls,fail_at,partial,writes;bool stuck_low,stuck_high,ignore_write,asleep;} Chip;
static bool chip_exchange(void*ctx,const uint8_t*tx,uint8_t*rx,unsigned n){
    Chip*c=ctx;assert(n&&n<=35);++c->calls;memset(rx,0,n);
    if(c->stuck_low)return true;if(c->stuck_high){memset(rx,255,n);return true;}
    bool fail=c->fail_at&&c->calls==c->fail_at;
    if(c->asleep){c->asleep=false;return !fail;}
    if(tx[0]==0x9f){assert(n==10);for(unsigned i=1;i<=6;i++)rx[i]=0x7f;rx[7]=0xc2;rx[8]=0x22;rx[9]=8;}
    else if(tx[0]==3){assert(n>=4);unsigned a=(unsigned)tx[1]*256+tx[2];assert(a+n-3<=sizeof c->bytes);for(unsigned i=3;i<n;i++)rx[i]=c->bytes[a+i-3];}
    else if(tx[0]==2){assert(n==7&&(c->status&2));unsigned a=(unsigned)tx[1]*256+tx[2];assert(a+4<=sizeof c->bytes);for(unsigned i=0;i<4;i++)if(!c->ignore_write&&(!fail||i<c->partial))c->bytes[a+i]=tx[i+3];c->status&=~2U;++c->writes;}
    else if(tx[0]==5){assert(n==2);rx[1]=c->status;}
    else if(tx[0]==6){assert(n==1);c->status|=2;}
    else if(tx[0]==0xb9){assert(n==1);c->asleep=true;}
    else if(tx[0]==4){assert(n==1);c->status&=~2U;}
    else assert(!"Unexpected opcode: production may never erase or WRSR");
    return !fail;
}
static NvHal attach(Fram*f,Chip*c){FramBus bus={chip_exchange,c};assert(fram_init(f,&bus));return fram_storage(f);}
static void complete(Journal*j,NvHal*h){for(uint32_t t=0;j->busy&&t<1000;t++)journal_service(j,h,t);assert(!j->busy);}
static void seed(Chip*c){Fram f;NvHal h=attach(&f,c);Journal j;journal_load(&j,&h);assert(!j.valid&&j.fault);assert(journal_begin(&j,99,false,0));complete(&j,&h);assert(j.completed&&j.count==99);}
int main(void){
    Chip original={0};seed(&original);unsigned cases=0;
    /* Every bus transaction during a save can fail, including each byte prefix
     * of the WRITE payload. On reboot only old99 or new100 may be credible. */
    for(unsigned call=1;call<=70;call++)for(unsigned partial=0;partial<=4;partial++){
        Chip c=original;Fram f;NvHal h=attach(&f,&c);Journal j;journal_load(&j,&h);assert(j.count==99&&!j.fault);
        c.fail_at=c.calls+call;c.partial=partial;assert(journal_begin(&j,100,false,0));complete(&j,&h);
        c.fail_at=0;Fram reboot_f;NvHal rh=attach(&reboot_f,&c);Journal reboot;journal_load(&reboot,&rh);
        assert(reboot.valid&&!reboot.fault&&(reboot.count==99||reboot.count==100));
        if(j.completed)assert(reboot.count==100);++cases;
    }
    for(unsigned fault=0;fault<3;fault++){
        Chip c=original;Fram f;NvHal h=attach(&f,&c);Journal j;journal_load(&j,&h);c.stuck_low=fault==0;c.stuck_high=fault==1;c.ignore_write=fault==2;
        assert(journal_begin(&j,100,false,0));complete(&j,&h);assert(j.failed&&!j.completed&&j.count==99);
    }
    Chip c=original;c.status=0x0c;Fram f;FramBus b={chip_exchange,&c};assert(!fram_init(&f,&b));assert(c.status==0x0c); /* do not remove protection */
    c.status=0;c.stuck_high=true;assert(!fram_init(&f,&b));
    c=original;NvHal h=attach(&f,&c);(void)h;
    for(unsigned i=0;i<1000;i++){
        uint32_t t=0xfffffff0UL+i*7U;assert(fram_sleep(&f));assert(c.asleep&&!fram_available(&f));
        assert(!fram_wake(&f,t));assert(!c.asleep&&!fram_available(&f));assert(!fram_wake(&f,t+1));assert(fram_wake(&f,t+2));assert(fram_available(&f));
    }
    /* Sleep/wake transfer failure latches an unavailable interface. No
     * service loop may retry until explicit recovery reinitializes the bus. */
    c=original;h=attach(&f,&c);c.fail_at=c.calls+1;
    assert(!fram_sleep(&f));assert(!f.ready&&!f.pending);
    unsigned stopped_calls=c.calls;
    for(unsigned n=0;n<60000;n++)assert(!fram_sleep(&f)&&!fram_wake(&f,n));
    assert(c.calls==stopped_calls);
    c=original;h=attach(&f,&c);assert(fram_sleep(&f));c.fail_at=c.calls+1;
    assert(!fram_wake(&f,0));assert(!f.ready&&!f.pending);
    stopped_calls=c.calls;
    for(unsigned n=0;n<60000;n++)assert(!fram_wake(&f,n));
    assert(c.calls==stopped_calls);
    c=original;h=attach(&f,&c);assert(fram_available(&f));
    printf("PASS: two permanent sleep/wake failures stop bus retries; explicit reinitialization recovers\n");
    printf("PASS: %u SPI FRAM transaction/byte-prefix failures, stuck MISO0/1, ignored writes, protected-device refusal,1000 sleep/wake guards across wrap; no MCU execution\n",cases);
}
