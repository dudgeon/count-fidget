#ifndef LCD_DE188_H
#define LCD_DE188_H
#include <stdint.h>
/* 16 segment-line nibbles, COM1..4 mapped to bits 0..3.
 * Lines correspond to glass pins 2..9,12..19, wired to MCU L8..L19 and L24..L27.
 * commons: glass 20,1,11,10 -> MCU L0,L1,L2,L3.
 * This encoder does not generate the required AC/bias waveform. */
void lcd_de188_encode(uint32_t count, uint8_t lines[16]);
#endif
