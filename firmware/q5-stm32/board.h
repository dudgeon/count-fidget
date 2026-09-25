#ifndef Q5_BOARD_H
#define Q5_BOARD_H
/* Q5 pin contract, separate from every Q3/Q4 assignment.
 * Firmware/build manifest and native model must agree before release. */
#define CORE_HZ 4000000UL
#define BOARD_INC_PIN 0U         /* PA0, active LOW: Q5 NMOS mirrors the SYS-referenced COUNT/power key */
#define BOARD_COUNT_RESET_PIN 1U /* PA1, active HIGH; shared key drives BOOT0. */
#define BOARD_VBAT_ADC_PIN 4U    /* PA4 / ADC_IN4: SYS_LOAD through 150k/150k 0.1% divider */
#define BOARD_VBAT_ADC_CHANNEL 4U
#define BOARD_STAT1_PIN 5U       /* PA5: BQ25185 STAT1 open drain, internal pull-up while awake */
#define BOARD_STAT2_PIN 6U       /* PA6: BQ25185 STAT2 open drain, internal pull-up while awake */
#define BOARD_PWR_HOLD_PIN 2U    /* PB2: HIGH keeps U7 (system load switch) on through D3 */
#define BOARD_OLED_RESET_PIN 0U  /* PB0, push-pull only while module powered; external pull-down */
#define BOARD_OLED_ENABLE_PIN 1U /* PB1, active high, external pull-down */
#define BOARD_SPI_CS_PIN 12U     /* PB12 GPIO */
#define BOARD_SPI_SCK_PIN 13U    /* PB13 AF0 */
#define BOARD_SPI_DC_PIN 14U     /* PB14 GPIO */
#define BOARD_SPI_MOSI_PIN 15U   /* PB15 AF0 */
#define BOARD_BOR_REQUIRED 0xCU  /* raw BOR_LEV 0xC = RM0376 "BOR LEVEL 5" = VBOR4, falling 2.68..2.85V */
/* Option-byte USER half-word (FLASH_OPTR[31:16]) the application provisions:
 * nBOOT1=1, BFB2=0, nRST_STDBY=1, nRST_STOP=1, WDG_SW=1, BOR_LEV=0xC. */
#define BOARD_OPTR_USER 0x807CU
#endif
