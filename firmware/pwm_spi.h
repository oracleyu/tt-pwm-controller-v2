/* SPDX-License-Identifier: Apache-2.0 */
#ifndef PWM_SPI_H
#define PWM_SPI_H
#include <stdbool.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
/* transfer must implement exactly 5 bytes, MSB first, SPI mode 0, with CS gaps. */
typedef struct {
    void *context;
    bool (*transfer)(void *, const uint8_t tx[5], uint8_t rx[5]);
    uint32_t (*now_us)(void *);
    void (*delay_us)(void *, uint32_t);
} pwm_io;
typedef struct {
    uint8_t left, right;
    uint16_t divider; /* 1..256, not the encoded wire value */
    bool enabled, pending, frame_error, overrun_error, generation;
} pwm_status;
enum { PWM_OK=0, PWM_ERR_ARGUMENT=-1, PWM_ERR_TRANSPORT=-2,
       PWM_ERR_PROTOCOL=-3, PWM_ERR_DEVICE=-4, PWM_ERR_TIMEOUT=-5 };
int pwm_read(const pwm_io *, pwm_status *);
int pwm_clear_errors(const pwm_io *);
/* Includes waiting for the previous commit and verifies readback + generation. */
int pwm_configure(const pwm_io *, uint8_t left, uint8_t right,
                  uint16_t divider, bool enable, uint32_t timeout_us);
#ifdef __cplusplus
}
#endif
#endif
