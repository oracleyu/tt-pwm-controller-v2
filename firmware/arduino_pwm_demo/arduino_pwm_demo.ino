// SPDX-License-Identifier: Apache-2.0
// Use a 3.3 V MCU and an already-selected Tiny Tapeout project.
// The demo board must supply an independent running ASIC clk (e.g. 10 MHz).
#include <SPI.h>
#include "pwm_spi.h"
constexpr int CS_PIN=10; // MCU GPIO number; change for your board.
static bool transfer_frame(void *,const uint8_t tx[5],uint8_t rx[5]) {
    SPI.beginTransaction(SPISettings(100000,MSBFIRST,SPI_MODE0));
    digitalWrite(CS_PIN,LOW);delayMicroseconds(2);
    for (unsigned i=0;i<5;i++) rx[i]=SPI.transfer(tx[i]);
    delayMicroseconds(2);digitalWrite(CS_PIN,HIGH);delayMicroseconds(2);
    SPI.endTransaction();return true;
}
static uint32_t now_us(void *) { return micros(); }
static void wait_us(void *,uint32_t n) { delayMicroseconds(n); }
static const pwm_io io={nullptr,transfer_frame,now_us,wait_us};
void setup() {
    pinMode(CS_PIN,OUTPUT);digitalWrite(CS_PIN,HIGH);SPI.begin();Serial.begin(115200);
    delay(20);
    int rc=pwm_clear_errors(&io);
    if (rc==PWM_OK) rc=pwm_configure(&io,64,192,2,true,500000);
    Serial.print("PWM init result: ");Serial.println(rc);
    // At 10 MHz clk: divider 2 => 19,531.25 Hz; duties 25% / 75%.
}
void loop() {
    pwm_status s;int rc=pwm_read(&io,&s);
    Serial.print("status=");Serial.print(rc);
    if (rc==PWM_OK) {
        Serial.print(" left=");Serial.print(s.left);
        Serial.print(" right=");Serial.print(s.right);
        Serial.print(" divider=");Serial.print(s.divider);
        Serial.print(" pending=");Serial.println(s.pending);
    } else Serial.println();
    delay(1000);
}
