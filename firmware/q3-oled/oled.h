#ifndef Q3_OLED_H
#define Q3_OLED_H
#include <stdbool.h>
#include <stdint.h>

#define OLED_ADDRESS 0x3cU /* SA0 low; confirm the exact bonded glass on hardware. */
#define OLED_TX_MAX 32U
#define OLED_CHUNK 16U
#define OLED_BUS_TIMEOUT_MS 20U
/* Nominal milliseconds: margin for +3.5% REFO and integer-tick phase. */
#define OLED_GUARD_100_MS 105U
#define OLED_STABLE_20_MS 23U

typedef enum { OLED_BUS_BUSY, OLED_BUS_OK, OLED_BUS_ERROR } OledBusResult;
/* start copies bytes before returning; poll and all callbacks never wait.
 * reset(true) asserts RES# LOW. power controls VBAT only; VDD stays supplied. */
typedef struct {
    void (*power)(bool enabled);
    void (*reset)(bool asserted);
    bool (*start)(const uint8_t *bytes, uint8_t length, uint32_t now);
    OledBusResult (*poll)(uint32_t now);
    void (*abort)(void);
    uint32_t (*now)(void); /* Fresh clock read after completion/pin changes. */
} OledHal;
typedef enum {
    OLED_OFF, OLED_RESET_WAIT, OLED_RESET_RELEASE, OLED_INIT,
    OLED_CLEAR_BEGIN, OLED_ADDRESS_CHUNK, OLED_DATA_CHUNK, OLED_NEXT_CHUNK,
    OLED_POWER_WAIT, OLED_PUMP_ON, OLED_DISPLAY_ON, OLED_VISIBLE_WAIT,
    OLED_READY, OLED_RENDER_DIGIT, OLED_STOP_DISPLAY, OLED_STOP_PUMP, OLED_STOP_WAIT,
    OLED_FAULT_WAIT, OLED_RETRY_WAIT
} OledState;
typedef struct {
    OledState state;
    uint32_t deadline, powered_at, frame_count, displayed_count;
    uint32_t errors;
    uint32_t remaining;
    bool pending, clearing, displayed_valid, frame_fault, displayed_fault;
    uint8_t page, column;
    uint8_t glyphs[8], digit_index;
} Oled;
void oled_init(Oled *display, const OledHal *hal);
/* Count must be the last successfully committed journal value. */
void oled_service(Oled *display, const OledHal *hal, bool awake,
                  uint32_t committed_count, bool input_fault, uint32_t now);
bool oled_is_off(const Oled *display);
/* Stateless page renderer: no framebuffer, eight digits, visible MAX at limit. */
uint8_t oled_pixel_byte(uint32_t count, uint8_t page, uint8_t column);
uint8_t oled_status_byte(uint32_t count, bool input_fault, uint8_t page, uint8_t column);
#endif
