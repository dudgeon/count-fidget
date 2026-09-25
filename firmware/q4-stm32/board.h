#ifndef Q4_BOARD_H
#define Q4_BOARD_H
/* Provisional Q4 pin contract, separate from every Q3 pin assignment.
 * Firmware/build manifest and native model must agree before release. */
#define CORE_HZ 4000000UL
#define BOARD_INC_PIN 0U       /* PA0 */
#define BOARD_COUNT_RESET_PIN 1U /* PA1, active HIGH; shared key drives BOOT0. */
#define BOARD_OLED_RESET_PIN 0U /* PB0, push-pull only while module powered; external pull-down */
#define BOARD_OLED_ENABLE_PIN 1U /* PB1, active high, external pull-down */
#define BOARD_CELL_ADC_PIN 4U  /* PA4 / ADC_IN4 */
#define BOARD_PRE_ADC_PIN 5U   /* PA5 / ADC_IN5 */
#define BOARD_BYPASS_PIN 6U    /* PA6, active high, external pull-down */
#define BOARD_I2C_SCL_PIN 6U   /* PB6 AF1 */
#define BOARD_I2C_SDA_PIN 7U   /* PB7 AF1 */
#define BOARD_SPI_CS_PIN 12U   /* PB12 GPIO */
#define BOARD_SPI_SCK_PIN 13U  /* PB13 AF0 */
#define BOARD_SPI_DC_PIN 14U   /* PB14 GPIO */
#define BOARD_SPI_MOSI_PIN 15U /* PB15 AF0 */
#define BOARD_DISPLAY_SPI 1   /* HS96L01W4S03, seven-pin SPI module. */
#ifndef BOARD_STORAGE_FRAM
#define BOARD_STORAGE_FRAM 1 /* Separate SPI1; EEPROM remains alternate build. */
#endif
#define BOARD_BOR_REQUIRED 0xCU /* DS10689 BOR4, falling2.68..2.85V */
#endif
