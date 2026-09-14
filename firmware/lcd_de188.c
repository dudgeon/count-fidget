#include "lcd_de188.h"
#include <string.h>
/* Seven-segment bit order a,b,c,d,e,f,g. Drawing: DE188 Rev4 p3. */
static const uint8_t digits[10]={0x3F,0x06,0x5B,0x4F,0x66,0x6D,0x7D,0x07,0x7F,0x6F};
static uint8_t acb(uint8_t d){return ((d>>0)&1U)|(((d>>2)&1U)<<1)|(((d>>1)&1U)<<2);}
static uint8_t fegd(uint8_t d){return ((d>>5)&1U)|(((d>>4)&1U)<<1)|(((d>>6)&1U)<<2)|(((d>>3)&1U)<<3);}
void lcd_de188_encode(uint32_t count,uint8_t lines[16]) {
    memset(lines,0,16);
    for(unsigned pos=0;pos<8;pos++) {
        uint8_t d=digits[count%10U];count/=10U;
        /* pos0 is the rightmost digit (glass digit 1). */
        if(pos<4) {lines[8+2*pos]=acb(d);lines[9+2*pos]=fegd(d);}
        else {unsigned i=2*(7-pos);lines[i]=fegd(d);lines[i+1]=acb(d);}
        if(count==0) break;
    }
}
