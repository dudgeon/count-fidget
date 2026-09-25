#ifndef Q5_OLED_H
#define Q5_OLED_H
#include <stdbool.h>
#include <stdint.h>

#define OLED_TX_MAX 32U
#define OLED_CHUNK 31U  /* data bytes per SPI packet: OLED_TX_MAX less the classification byte */
#define OLED_BUS_TIMEOUT_MS 20U
/* U6 slew: TPS22917 tON 3.8us/pF typical x 4.7nF CT = 17.9ms. SSD1315 section
 * 6.9.2 then needs VDD stable for >=20ms before RES# is released. 60ms is
 * more than 3x the typical ramp plus that 20ms; measure the actual module. */
#define OLED_RESET_HOLD_MS 60U
/* SSD1315 power-off: AEh, 8Dh 10h, then typical tOFF=100ms before supply
 * removal. 120ms covers HSI tolerance and tick phase. */
#define OLED_OFF_GUARD_MS 120U

typedef enum { OLED_BUS_BUSY, OLED_BUS_OK, OLED_BUS_ERROR } OledBusResult;
/* start copies bytes before returning; poll and all callbacks never wait.
 * reset(true) asserts RES# LOW. power switches the entire module; target isolates signal pins before OFF. */
typedef struct {
    void (*power)(bool enabled);
    void (*reset)(bool asserted);
    bool (*start)(const uint8_t *bytes, uint8_t length, uint32_t now);
    OledBusResult (*poll)(uint32_t now);
    void (*abort)(void);
    uint32_t (*now)(void); /* Fresh clock read after completion/pin changes. */
} OledHal;
typedef enum { OLED_LABEL_NONE, OLED_LABEL_ERR, OLED_LABEL_MAX, OLED_LABEL_RST,
               OLED_LABEL_LO, OLED_LABEL_CHG, OLED_LABEL_BAT, OLED_LABEL_OPT, OLED_LABEL_COUNT } OledLabel;
#define OLED_BARS_HIDDEN 0xffU
/* What the panel should show. count is the last successfully committed
 * journal value; hide_digits blanks the number (configuration diagnostic). */
typedef struct { uint32_t count; uint8_t label, bars; bool hide_digits; } OledView;
typedef enum {
    OLED_OFF, OLED_RESET_WAIT, OLED_RESET_RELEASE, OLED_INIT,
    OLED_ADDRESS_CHUNK, OLED_DATA_CHUNK, OLED_NEXT_CHUNK,
    OLED_PUMP_ON, OLED_DISPLAY_ON, OLED_READY, OLED_RENDER_DIGIT,
    OLED_STOP_DISPLAY, OLED_STOP_PUMP, OLED_STOP_WAIT,
    OLED_FAULT_WAIT, OLED_RETRY_WAIT
} OledState;
#define OLED_REGION_LABEL 8U
#define OLED_REGION_ICON 9U
#define OLED_REGION_FULL 10U
typedef struct {
    OledState state;
    uint32_t deadline, errors, remaining;
    OledView frame, shown;
    uint16_t dirty;          /* regions still to send in this frame */
    bool pending, shown_valid, panel_on, rail_dropped;
    uint8_t region, page, column;
    uint8_t glyphs[8], shown_glyphs[8], digit_index;
} Oled;
void oled_init(Oled *display, const OledHal *hal);
/* wanted: the module may be powered (board awake, supply good). rail_ok: the
 * measured VLOGIC permits operating the controller. The module may be powered
 * and held in reset before rail_ok (overlapping boot work); initialization,
 * the charge pump and AFh wait for rail_ok. Losing rail_ok while running shuts
 * the panel down and it stays unpowered until rail_ok returns. */
void oled_service(Oled *display, const OledHal *hal, bool wanted, bool rail_ok, const OledView *view, uint32_t now);
bool oled_is_off(const Oled *display);
/* Stateless page renderer: no framebuffer, eight digits, status label, battery icon. */
uint8_t oled_frame_byte(const OledView *view, uint8_t page, uint8_t column);
uint8_t oled_pixel_byte(uint32_t count, uint8_t page, uint8_t column);
#endif
