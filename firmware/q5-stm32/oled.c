#include "oled.h"
#include "counter.h"
#include <string.h>

/* HS96L01W4S03 module sheet pp15-16: 128x64 SSD1315 per module mechanical drawing.
 * Separate transport classification byte is never transmitted over SPI.
 * Contrast0x10 reduces brightness; it is not a qualified current limit. */
static const uint8_t initialization[] = {
    0x00, 0xae, 0x8d, 0x10, 0xa8, 0x3f, 0xd3, 0x00,
    0xa1, 0xc8, 0xa6, 0x40, 0xa4, 0x81, 0x10, 0xd9, 0xf1,
    0xd5, 0x80, 0xda, 0x12, 0x20, 0x02, 0xdb, 0x30
};
static const uint8_t digits[10][5] = {
    {0x3e,0x51,0x49,0x45,0x3e}, {0x00,0x42,0x7f,0x40,0x00},
    {0x42,0x61,0x51,0x49,0x46}, {0x21,0x41,0x45,0x4b,0x31},
    {0x18,0x14,0x12,0x7f,0x10}, {0x27,0x45,0x45,0x45,0x39},
    {0x3c,0x4a,0x49,0x49,0x30}, {0x01,0x71,0x09,0x05,0x03},
    {0x36,0x49,0x49,0x49,0x36}, {0x06,0x49,0x49,0x29,0x1e}
};
/* Three 3x5 letters with one blank column between them, at y=58..62. */
static const uint8_t labels[OLED_LABEL_COUNT][11] = {
    [OLED_LABEL_ERR]={0x1f,0x15,0x11,0, 0x1f,0x05,0x1a,0, 0x1f,0x05,0x1a},
    [OLED_LABEL_MAX]={0x1f,0x02,0x1f,0, 0x1e,0x05,0x1e,0, 0x1b,0x04,0x1b},
    [OLED_LABEL_RST]={0x1f,0x05,0x1a,0, 0x17,0x15,0x1d,0, 0x01,0x1f,0x01},
    [OLED_LABEL_LO] ={0x1f,0x10,0x10,0, 0x0e,0x11,0x0e,0, 0x00,0x00,0x00},
    [OLED_LABEL_CHG]={0x0e,0x11,0x11,0, 0x1f,0x04,0x1f,0, 0x0e,0x11,0x1d},
    [OLED_LABEL_BAT]={0x1f,0x15,0x0a,0, 0x1e,0x05,0x1e,0, 0x01,0x1f,0x01},
    [OLED_LABEL_OPT]={0x0e,0x11,0x0e,0, 0x1f,0x05,0x02,0, 0x01,0x1f,0x01},
};
#define ICON_X 106U
#define ICON_WIDTH 20U
static uint8_t icon_byte(uint8_t bars,uint8_t column) {
    if(bars==OLED_BARS_HIDDEN || column<ICON_X || column>=ICON_X+ICON_WIDTH) return 0;
    unsigned x=column-ICON_X;
    if(x==0 || x==17) return 0x7e;           /* end walls, y=1..6 */
    if(x==18 || x==19) return 0x18;          /* terminal nub */
    unsigned bar=(x-2U)/4U, offset=(x-2U)%4U;
    bool filled=x>=2 && x<=16 && offset<3 && bar<bars;
    return filled?0x7e:0x42;                 /* 4 bars of 3 columns inside a border */
}
/* Page bits covered by digit source row r (pixel rows 8+6r .. 13+6r). */
static uint8_t row_mask(uint8_t page,unsigned r) {
    int a=(int)(8U+6U*r)-(int)(page*8U),b=a+6;
    if(a<0)a=0;
    if(b>8)b=8;
    if(a>=b)return 0;
    return (uint8_t)(((1U<<b)-1U)&~((1U<<a)-1U));
}
static uint8_t glyph_byte(const uint8_t glyphs[8],uint8_t label,uint8_t bars,uint8_t page,uint8_t column) {
    uint8_t result=0;
    if(page>=8 || column>=128) return 0;
    /* 96px-wide eight-digit field. Each source dot is2x6 pixels, with
     * y=8..49 for digits; the five-pixel status label sits at y=58..62.
     * No division: this runs for every transmitted byte. */
    if(column>=16 && column<112 && page>=1 && page<=6) {
        unsigned cell=0, x=column-16U;
        while(x>=12U){x-=12U;++cell;}
        if(x<10 && glyphs[cell]<10) {
            uint8_t shape=digits[glyphs[cell]][x>>1];
            for(unsigned r=0;r<7;r++) if(shape&(1U<<r)) result|=row_mask(page,r);
        }
    }
    if(label && label<OLED_LABEL_COUNT && page==7 && column>=58 && column<69)
        result=(uint8_t)(labels[label][column-58U]<<2);
    if(page==0) result|=icon_byte(bars,column);
    return result;
}
static void glyphs_for(const OledView *v,uint8_t glyphs[8]) {
    uint32_t value=v->count>COUNTER_MAX?COUNTER_MAX:v->count;
    for(unsigned i=8;i>0;i--){glyphs[i-1]=(!v->hide_digits && (value || i==8))?(uint8_t)(value%10U):10;value/=10U;}
}
uint8_t oled_frame_byte(const OledView *v,uint8_t page,uint8_t column) {
    uint8_t glyphs[8];glyphs_for(v,glyphs);
    return glyph_byte(glyphs,v->label,v->bars,page,column);
}
uint8_t oled_pixel_byte(uint32_t count,uint8_t page,uint8_t column) {
    OledView v={count,OLED_LABEL_NONE,OLED_BARS_HIDDEN,false};
    return oled_frame_byte(&v,page,column);
}
static void region_geometry(uint8_t r,uint8_t *x0,uint8_t *width,uint8_t *first,uint8_t *last) {
    if(r<8){*x0=(uint8_t)(16U+12U*r);*width=10;*first=1;*last=6;}
    else if(r==OLED_REGION_LABEL){*x0=58;*width=11;*first=7;*last=7;}
    else if(r==OLED_REGION_ICON){*x0=ICON_X;*width=ICON_WIDTH;*first=0;*last=0;}
    else {*x0=0;*width=128;*first=0;*last=7;}
}
static bool reached(uint32_t now, uint32_t deadline) {
    return (int32_t)(now-deadline)>=0;
}
static void fail(Oled *d,const OledHal *h) {
    h->abort();h->reset(true);
    d->pending=false;d->shown_valid=false;d->panel_on=false;++d->errors;
    /* Reset disables panel output/pump. Preserve a discharge guard even if
     * a stuck bus prevents the normal AE/8D10 shutdown commands. */
    d->state=OLED_FAULT_WAIT;d->deadline=h->now()+OLED_OFF_GUARD_MS;
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
static bool next_region(Oled *d) {
    while(d->dirty) {
        uint8_t r=0;while(!(d->dirty&(1U<<r)))++r;
        d->dirty&=(uint16_t)~(1U<<r);
        uint8_t x0,w,first,last;region_geometry(r,&x0,&w,&first,&last);
        d->region=r;d->page=first;d->column=x0;return true;
    }
    return false;
}
static void begin_frame(Oled *d) {
    /* Only changed digit cells, label and icon are sent; a first frame after
     * power-up rewrites all GDDRAM, replacing a separate clear pass. */
    uint16_t dirty=0;
    if(!d->shown_valid) dirty=1U<<OLED_REGION_FULL;
    else {
        for(unsigned i=0;i<8;i++) if(d->glyphs[i]!=d->shown_glyphs[i]) dirty|=(uint16_t)(1U<<i);
        if(d->frame.label!=d->shown.label) dirty|=1U<<OLED_REGION_LABEL;
        if(d->frame.bars!=d->shown.bars) dirty|=1U<<OLED_REGION_ICON;
    }
    d->dirty=dirty;
    if(next_region(d)) d->state=OLED_ADDRESS_CHUNK;
    else {d->shown=d->frame;memcpy(d->shown_glyphs,d->glyphs,8);d->shown_valid=true;d->state=OLED_READY;}
}
static bool same_view(const OledView *a,const OledView *b) {
    return a->count==b->count && a->label==b->label && a->bars==b->bars && a->hide_digits==b->hide_digits;
}
void oled_service(Oled *d,const OledHal *h,bool wanted,bool rail_ok,const OledView *view,uint32_t now) {
    uint8_t packet[OLED_TX_MAX];
    if(d->pending) {
        OledBusResult r=h->poll(now);
        if(r==OLED_BUS_BUSY) return;
        if(r==OLED_BUS_ERROR){fail(d,h);return;}
        d->pending=false;
        /* Start the off guard after acknowledged completion, not at START. */
        if(d->state==OLED_STOP_WAIT) d->deadline=h->now()+OLED_OFF_GUARD_MS;
    }
    if(rail_ok)d->rail_dropped=false;
    else if(d->state>=OLED_INIT && d->state<OLED_STOP_DISPLAY)d->rail_dropped=true;
    bool awake=wanted && !d->rail_dropped;
    if(!awake && d->state>OLED_OFF && d->state<OLED_STOP_DISPLAY) {
        /* Before the pump command, holding RES# low is a complete shutdown;
         * afterwards use the SSD1315 AEh / 8Dh 10h / tOFF order. */
        if(d->panel_on) d->state=OLED_STOP_DISPLAY;
        else {h->reset(true);d->deadline=h->now()+OLED_OFF_GUARD_MS;d->state=OLED_STOP_WAIT;}
    }
    switch(d->state) {
    case OLED_OFF:
        if(awake) {
            h->reset(true);h->power(true);
            d->deadline=h->now()+OLED_RESET_HOLD_MS;d->state=OLED_RESET_WAIT;
        }
        break;
    case OLED_RESET_WAIT:
        /* RES# stays low until both the supply-stable interval and a valid
         * rail measurement are available. */
        if(reached(now,d->deadline) && rail_ok){d->deadline=now+2U;d->state=OLED_RESET_RELEASE;}
        break;
    case OLED_RESET_RELEASE:
        if(reached(now,d->deadline)){h->reset(false);d->deadline=h->now()+2U;d->state=OLED_INIT;}
        break;
    case OLED_INIT:
        if(reached(now,d->deadline)) {
            d->shown_valid=false;d->frame=*view;glyphs_for(view,d->glyphs);
            if(send(d,h,initialization,sizeof(initialization),OLED_INIT,now)){
                d->dirty=1U<<OLED_REGION_FULL;(void)next_region(d);d->state=OLED_ADDRESS_CHUNK;
            }
        }
        break;
    case OLED_ADDRESS_CHUNK:
        packet[0]=0;packet[1]=(uint8_t)(0xb0U+d->page);
        packet[2]=(uint8_t)(d->column&15U);packet[3]=(uint8_t)(0x10U+(d->column>>4));
        (void)send(d,h,packet,4,OLED_DATA_CHUNK,now);
        break;
    case OLED_DATA_CHUNK: {
        uint8_t x0,w,first,last;region_geometry(d->region,&x0,&w,&first,&last);
        unsigned end=(unsigned)x0+w,n=end-d->column;if(n>OLED_CHUNK)n=OLED_CHUNK;
        packet[0]=0x40;
        for(unsigned i=0;i<n;i++) packet[i+1]=glyph_byte(d->glyphs,d->frame.label,d->frame.bars,d->page,(uint8_t)(d->column+i));
        if(send(d,h,packet,(uint8_t)(n+1U),OLED_NEXT_CHUNK,now))d->column=(uint8_t)(d->column+n);
        break;
    }
    case OLED_NEXT_CHUNK: {
        uint8_t x0,w,first,last;region_geometry(d->region,&x0,&w,&first,&last);
        if(d->column>=x0+w){d->column=x0;++d->page;}
        if(d->page<=last){d->state=OLED_ADDRESS_CHUNK;break;}
        if(next_region(d)){d->state=OLED_ADDRESS_CHUNK;break;}
        d->shown=d->frame;memcpy(d->shown_glyphs,d->glyphs,8);d->shown_valid=true;
        d->state=d->panel_on?OLED_READY:OLED_PUMP_ON;
        break;
    }
    case OLED_PUMP_ON:
        /* SSD1315 section 6.9.2: after reset, 8Dh then AFh; SEG/COM turn on
         * about 100ms later with the complete first frame already in GDDRAM. */
        packet[0]=0;packet[1]=0x8d;packet[2]=0x14;
        if(send(d,h,packet,3,OLED_DISPLAY_ON,now))d->panel_on=true; /* pump may now be running */
        break;
    case OLED_DISPLAY_ON:
        packet[0]=0;packet[1]=0xaf;
        (void)send(d,h,packet,2,OLED_READY,now);
        break;
    case OLED_READY:
        if(!d->shown_valid || !same_view(&d->shown,view)) {
            d->frame=*view;d->remaining=view->count>COUNTER_MAX?COUNTER_MAX:view->count;
            d->digit_index=8;d->state=OLED_RENDER_DIGIT;
        }
        break;
    case OLED_RENDER_DIGIT:
        /* One 32-bit division per foreground step; never convert a whole
         * framebuffer in a single button-sampling interval. */
        --d->digit_index;
        d->glyphs[d->digit_index]=(!d->frame.hide_digits && (d->remaining || d->digit_index==7)) ?
            (uint8_t)(d->remaining%10U):10;
        d->remaining/=10U;
        if(d->digit_index==0)begin_frame(d);
        break;
    case OLED_STOP_DISPLAY:
        packet[0]=0;packet[1]=0xae;
        (void)send(d,h,packet,2,OLED_STOP_PUMP,now);
        break;
    case OLED_STOP_PUMP:
        packet[0]=0;packet[1]=0x8d;packet[2]=0x10;
        if(send(d,h,packet,3,OLED_STOP_WAIT,now))d->panel_on=false;
        /* The completion path starts the tOFF guard after acknowledgement. */
        break;
    case OLED_STOP_WAIT:
        if(reached(now,d->deadline)) {
            h->reset(true);h->power(false);d->shown_valid=false;d->panel_on=false;d->state=OLED_OFF;
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
