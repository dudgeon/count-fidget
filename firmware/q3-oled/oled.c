#include "oled.h"
#include "counter.h"
#include <string.h>

/* Exact X087 module geometry/scan settings from its Ver A pp14-15; pump
 * commands from SSD1312 Rev1.2 pp25 and command-table pp5/28. The module's
 * sample 8D12 means 7.5 V, so Q3 explicitly selects 9 V using 8D72 later.
 * Contrast 0x10 is a conservative candidate, not a proven current limit. */
static const uint8_t initialization[] = {
    0x00, 0xae, 0x8d, 0x10, 0xa8, 0x1f, 0xad, 0x40,
    0xd3, 0x10, 0xa1, 0xc8, 0xa6, 0x40, 0xa4,
    0x81, 0x10, 0xd9, 0x22, 0xd5, 0x80, 0xda, 0x10,
    0x20, 0x02, 0xdb, 0x30
};
static const uint8_t digits[10][5] = {
    {0x3e,0x51,0x49,0x45,0x3e}, {0x00,0x42,0x7f,0x40,0x00},
    {0x42,0x61,0x51,0x49,0x46}, {0x21,0x41,0x45,0x4b,0x31},
    {0x18,0x14,0x12,0x7f,0x10}, {0x27,0x45,0x45,0x45,0x39},
    {0x3c,0x4a,0x49,0x49,0x30}, {0x01,0x71,0x09,0x05,0x03},
    {0x36,0x49,0x49,0x49,0x36}, {0x06,0x49,0x49,0x29,0x1e}
};
static const uint8_t max_label[11] = {
    0x1f,0x02,0x1f,0, 0x1e,0x05,0x1e,0, 0x1b,0x04,0x1b
};
static const uint8_t err_label[11] = {
    0x1f,0x15,0x11,0, 0x1f,0x05,0x1a,0, 0x1f,0x05,0x1a
};
static uint8_t glyph_byte(const uint8_t glyphs[8],bool maximum,bool fault,uint8_t page,uint8_t column) {
    uint8_t result=0;
    if(page>=4 || column>=128) return 0;
    /* Eight 12-pixel cells at x=16; each 5x7 glyph is 2x3 pixels per dot,
     * using 21 of 32 vertical pixels for readable numerals on small glass. */
    if(column>=16 && column<112) {
        unsigned cell=(column-16U)/12U, x=(column-16U)%12U;
        if(x<10 && glyphs[cell]<10) {
            uint8_t shape=digits[glyphs[cell]][x/2U];
            if(page==0) result=(uint8_t)(((shape&1U)?0x1c:0)|((shape&2U)?0xe0:0));
            if(page==1) result=(uint8_t)(((shape&4U)?7:0)|((shape&8U)?0x38:0)|((shape&16U)?0xc0:0));
            if(page==2) result=(uint8_t)(((shape&16U)?1:0)|((shape&32U)?0x0e:0)|((shape&64U)?0x70:0));
        }
    }
    /* Saturation stays visible after reboot as well as an excess press. */
    if((maximum || fault) && page==3 && column>=58 && column<69)
        result=(uint8_t)((fault?err_label[column-58U]:max_label[column-58U])<<2);
    return result;
}
uint8_t oled_status_byte(uint32_t count,bool fault,uint8_t page,uint8_t column) {
    uint8_t glyphs[8];uint32_t value=count>COUNTER_MAX?COUNTER_MAX:count;
    for(unsigned i=8;i>0;i--){glyphs[i-1]=(value || i==8)?(uint8_t)(value%10U):10;value/=10U;}
    return glyph_byte(glyphs,count>=COUNTER_MAX,fault,page,column);
}
uint8_t oled_pixel_byte(uint32_t count,uint8_t page,uint8_t column) {
    return oled_status_byte(count,false,page,column);
}
static bool reached(uint32_t now, uint32_t deadline) {
    return (int32_t)(now-deadline)>=0;
}
static void fail(Oled *d,const OledHal *h) {
    h->abort();h->reset(true);
    d->pending=false;d->displayed_valid=false;++d->errors;
    /* Reset disables panel output/pump. Preserve a discharge guard even if
     * a stuck bus prevents the normal AE/8D10 shutdown commands. */
    d->state=OLED_FAULT_WAIT;d->deadline=h->now()+OLED_GUARD_100_MS;
}
static bool send(Oled *d,const OledHal *h,const uint8_t *p,uint8_t n,
                 OledState next,uint32_t now) {
    if(!h->start(p,n,now)){fail(d,h);return false;}
    d->pending=true;d->state=next;return true;
}
void oled_init(Oled *d,const OledHal *h) {
    memset(d,0,sizeof(*d));h->abort();h->reset(true);h->power(false);
    d->state=OLED_OFF;
}
bool oled_is_off(const Oled *d) { return d->state==OLED_OFF && !d->pending; }
void oled_service(Oled *d,const OledHal *h,bool awake,uint32_t count,bool input_fault,uint32_t now) {
    uint8_t packet[OLED_TX_MAX];
    if(d->pending) {
        OledBusResult r=h->poll(now);
        if(r==OLED_BUS_BUSY) return;
        if(r==OLED_BUS_ERROR){fail(d,h);return;}
        d->pending=false;
        /* Start these guards after acknowledged completion, not at START.
         * Slow foreground service only extends the physical interval. */
        if(d->state==OLED_STOP_WAIT || d->state==OLED_VISIBLE_WAIT)
            d->deadline=h->now()+OLED_GUARD_100_MS;
    }
    if(!awake && d->state>OLED_OFF && d->state<OLED_STOP_DISPLAY) {
        if(d->state<OLED_INIT) {
            h->reset(true);d->deadline=h->now()+OLED_GUARD_100_MS;d->state=OLED_STOP_WAIT;
        } else d->state=OLED_STOP_DISPLAY;
    }
    switch(d->state) {
    case OLED_OFF:
        if(awake) {
            h->reset(true);h->power(true);d->powered_at=h->now();
            d->deadline=d->powered_at+OLED_STABLE_20_MS;d->state=OLED_RESET_WAIT;
        }
        break;
    case OLED_RESET_WAIT:
        /* VDD and VBAT settle with reset held low, then a separate 2 ms
         * reset interval exceeds the controller's 3 us minimum. */
        if(reached(now,d->deadline)){d->deadline=now+2U;d->state=OLED_RESET_RELEASE;}
        break;
    case OLED_RESET_RELEASE:
        if(reached(now,d->deadline)){h->reset(false);d->deadline=h->now()+2U;d->state=OLED_INIT;}
        break;
    case OLED_INIT:
        if(reached(now,d->deadline))
            (void)send(d,h,initialization,sizeof(initialization),OLED_CLEAR_BEGIN,now);
        break;
    case OLED_CLEAR_BEGIN:
        d->clearing=true;d->page=0;d->column=0;d->state=OLED_ADDRESS_CHUNK;
        break;
    case OLED_ADDRESS_CHUNK:
        packet[0]=0;packet[1]=(uint8_t)(0xb0U+d->page);
        packet[2]=(uint8_t)(d->column&15U);packet[3]=(uint8_t)(0x10U+(d->column>>4));
        (void)send(d,h,packet,4,OLED_DATA_CHUNK,now);
        break;
    case OLED_DATA_CHUNK:
        packet[0]=0x40;
        for(unsigned i=0;i<OLED_CHUNK;i++) packet[i+1]=d->clearing ? 0 :
            glyph_byte(d->glyphs,d->frame_count==COUNTER_MAX,d->frame_fault,d->page,(uint8_t)(d->column+i));
        (void)send(d,h,packet,OLED_CHUNK+1,OLED_NEXT_CHUNK,now);
        break;
    case OLED_NEXT_CHUNK:
        d->column=(uint8_t)(d->column+OLED_CHUNK);
        if(d->column==128){d->column=0;++d->page;}
        if(d->page<(d->clearing ? 8U : 4U)) d->state=OLED_ADDRESS_CHUNK;
        else if(d->clearing) d->state=OLED_POWER_WAIT;
        else {d->displayed_count=d->frame_count;d->displayed_fault=d->frame_fault;d->displayed_valid=true;d->state=OLED_READY;}
        break;
    case OLED_POWER_WAIT:
        if(reached(now,d->powered_at+OLED_GUARD_100_MS)) d->state=OLED_PUMP_ON;
        break;
    case OLED_PUMP_ON:
        packet[0]=0;packet[1]=0x8d;packet[2]=0x72;
        (void)send(d,h,packet,3,OLED_DISPLAY_ON,now);
        break;
    case OLED_DISPLAY_ON:
        packet[0]=0;packet[1]=0xaf;
        (void)send(d,h,packet,2,OLED_VISIBLE_WAIT,now);
        break;
    case OLED_VISIBLE_WAIT:
        if(reached(now,d->deadline)){d->displayed_valid=false;d->state=OLED_READY;}
        break;
    case OLED_READY:
        if(!d->displayed_valid || d->displayed_count!=count || d->displayed_fault!=input_fault) {
            d->frame_count=count;d->frame_fault=input_fault;d->clearing=false;d->page=0;d->column=0;
            d->remaining=count;d->digit_index=8;d->state=OLED_RENDER_DIGIT;
        }
        break;
    case OLED_RENDER_DIGIT:
        /* One 32-bit division per foreground step; never convert a whole
         * framebuffer in a single button-sampling interval. */
        --d->digit_index;
        d->glyphs[d->digit_index]=(d->remaining || d->digit_index==7) ?
            (uint8_t)(d->remaining%10U):10;
        d->remaining/=10U;
        if(d->digit_index==0)d->state=OLED_ADDRESS_CHUNK;
        break;
    case OLED_STOP_DISPLAY:
        packet[0]=0;packet[1]=0xae;
        (void)send(d,h,packet,2,OLED_STOP_PUMP,now);
        break;
    case OLED_STOP_PUMP:
        packet[0]=0;packet[1]=0x8d;packet[2]=0x10;
        (void)send(d,h,packet,3,OLED_STOP_WAIT,now);
        /* The completion path starts a105 nominal ms guard after ACK. */
        break;
    case OLED_STOP_WAIT:
        if(reached(now,d->deadline)) {
            h->reset(true);h->power(false);d->displayed_valid=false;d->state=OLED_OFF;
        }
        break;
    case OLED_FAULT_WAIT:
        if(reached(now,d->deadline)) {
            h->power(false);d->deadline=now+1000U;d->state=awake ? OLED_RETRY_WAIT : OLED_OFF;
        }
        break;
    case OLED_RETRY_WAIT:
        if(!awake || reached(now,d->deadline))d->state=OLED_OFF;
        break;
    }
}
