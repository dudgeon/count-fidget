#include "lcd_de188.h"
#include <assert.h>
#include <stdio.h>
int main(void) {
 uint8_t s[16];
 lcd_de188_encode(0,s);assert(s[8]==7 && s[9]==11);
 for(unsigned i=0;i<16;i++)if(i!=8&&i!=9)assert(s[i]==0);
 lcd_de188_encode(1,s);assert(s[8]==6&&s[9]==0);
 lcd_de188_encode(88888888UL,s);
 for(unsigned i=0;i<8;i+=2)assert(s[i]==15&&s[i+1]==7);
 for(unsigned i=8;i<16;i+=2)assert(s[i]==7&&s[i+1]==15);
 lcd_de188_encode(10000000UL,s);assert(s[0]==0&&s[1]==6);
 puts("PASS: DE188 zero, one, eight/all-digit segment mapping and digit order (host only)");
}
