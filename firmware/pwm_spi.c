/* SPDX-License-Identifier: Apache-2.0 */
#include "pwm_spi.h"
#include <stddef.h>
static int transact(const pwm_io *io, const uint8_t tx[5], uint8_t rx[5]) {
    if (!io || !io->transfer) return PWM_ERR_ARGUMENT;
    if (!io->transfer(io->context,tx,rx)) return PWM_ERR_TRANSPORT;
    if (rx[0]!=0xc2 || (rx[1]&0xe0)) return PWM_ERR_PROTOCOL;
    return PWM_OK;
}
int pwm_read(const pwm_io *io, pwm_status *s) {
    const uint8_t tx[5]={0,0,0,0,0};uint8_t rx[5];
    if (!s) return PWM_ERR_ARGUMENT;
    int rc=transact(io,tx,rx);if (rc) return rc;
    s->enabled=(rx[1]&1)!=0;s->pending=(rx[1]&2)!=0;
    s->frame_error=(rx[1]&4)!=0;s->overrun_error=(rx[1]&8)!=0;
    s->generation=(rx[1]&16)!=0;s->left=rx[2];s->right=rx[3];
    s->divider=(uint16_t)rx[4]+1u;
    return PWM_OK;
}
int pwm_clear_errors(const pwm_io *io) {
    const uint8_t tx[5]={0xc0,0,0,0,0};uint8_t rx[5];
    int rc=transact(io,tx,rx);if (rc) return rc;
    pwm_status s;rc=pwm_read(io,&s);if (rc) return rc;
    return (s.frame_error || s.overrun_error)?PWM_ERR_DEVICE:PWM_OK;
}
int pwm_configure(const pwm_io *io,uint8_t left,uint8_t right,uint16_t divider,
                  bool enable,uint32_t timeout_us) {
    if (!io || !io->now_us || !io->delay_us || divider<1 || divider>256 ||
        timeout_us==0 || timeout_us>0x7fffffffu) return PWM_ERR_ARGUMENT;
    uint32_t start=io->now_us(io->context);pwm_status s;int rc;
    for (;;) {
        rc=pwm_read(io,&s);if (rc) return rc;
        if (s.frame_error || s.overrun_error) return PWM_ERR_DEVICE;
        if (!s.pending) break;
        if ((uint32_t)(io->now_us(io->context)-start)>=timeout_us) return PWM_ERR_TIMEOUT;
        io->delay_us(io->context,10);
    }
    bool generation=s.generation;
    const uint8_t tx[5]={0xa1,left,right,(uint8_t)(divider-1u),(uint8_t)enable};
    uint8_t rx[5];rc=transact(io,tx,rx);if (rc) return rc;
    for (;;) {
        rc=pwm_read(io,&s);if (rc) return rc;
        if (s.frame_error || s.overrun_error) return PWM_ERR_DEVICE;
        if (!s.pending && s.generation!=generation) {
            return (s.left==left && s.right==right && s.divider==divider &&
                    s.enabled==enable)?PWM_OK:PWM_ERR_PROTOCOL;
        }
        if ((uint32_t)(io->now_us(io->context)-start)>=timeout_us) return PWM_ERR_TIMEOUT;
        io->delay_us(io->context,10);
    }
}
