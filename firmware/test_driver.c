/* Host tests exercise framing, verification, error handling and timer wrap. */
#include "pwm_spi.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef struct {
    uint8_t l,r,d,flags,queued[4];uint32_t us;
    unsigned remaining;bool stuck,bad_id,bad_readback,fail;
} mock;
static bool xfer(void *p,const uint8_t t[5],uint8_t r[5]) {
    mock *m=p;if(m->fail)return false;m->us+=404;
    if(m->remaining && !m->stuck && --m->remaining==0) {
        m->l=m->queued[0];m->r=m->queued[1];m->d=m->queued[2];
        m->flags=(m->flags&16)^16;m->flags|=m->queued[3]&1;
        if(m->bad_readback)m->l^=1;
    }
    r[0]=m->bad_id?0:0xc2;r[1]=m->flags;r[2]=m->l;r[3]=m->r;r[4]=m->d;
    if(t[0]==0xa1) {
        memcpy(m->queued,t+1,4);m->remaining=3;m->flags|=2;
    } else if(t[0]==0xc0)m->flags&=(uint8_t)~12u;
    else assert(t[0]==0);
    return true;
}
static uint32_t now(void *p){return ((mock*)p)->us;}
static void delay(void*p,uint32_t n){((mock*)p)->us+=n;}
int main(void) {
    mock m={.d=1};pwm_io io={&m,xfer,now,delay};pwm_status s;
    assert(pwm_read(&io,&s)==0 && s.divider==2 && !s.enabled);
    assert(pwm_configure(&io,64,192,2,true,10000)==0);
    assert(pwm_read(&io,&s)==0 && s.left==64 && s.right==192 && s.enabled);
    m.us=0xfffffff0u;
    assert(pwm_configure(&io,0,255,256,false,10000)==0);
    assert(pwm_configure(&io,0,0,0,true,10000)==PWM_ERR_ARGUMENT);
    assert(pwm_configure(&io,0,0,257,true,10000)==PWM_ERR_ARGUMENT);
    assert(pwm_configure(&io,0,0,1,true,0)==PWM_ERR_ARGUMENT);
    m.flags|=4;assert(pwm_configure(&io,1,2,1,true,10000)==PWM_ERR_DEVICE);
    assert(pwm_clear_errors(&io)==0);
    m.bad_id=true;assert(pwm_read(&io,&s)==PWM_ERR_PROTOCOL);m.bad_id=false;
    m.fail=true;assert(pwm_read(&io,&s)==PWM_ERR_TRANSPORT);m.fail=false;
    m.stuck=true;assert(pwm_configure(&io,1,2,1,true,2000)==PWM_ERR_TIMEOUT);
    m.stuck=false;m.remaining=0;m.flags=0;m.bad_readback=true;
    assert(pwm_configure(&io,1,2,1,true,10000)==PWM_ERR_PROTOCOL);
    puts("PASS: driver framing/readback/errors/timeout/32-bit timer wrap");
}
