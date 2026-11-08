# How it works

V2 has two registered 8-bit PWM outputs, a shared 8-bit phase counter, a programmable 1..256 clock divider, and an oversampled SPI Mode 0 interface. Clocked input synchronizers bring SCK, CS_n and MOSI into the system-clock domain. A valid complete 40-bit write stages the entire configuration in a one-entry shadow buffer, which commits at the old PWM period boundary. Reset asynchronously asserts and synchronously releases; outputs default off. There is no internally generated clock.

Duty is code/256 (0..255/256). PWM frequency is f_clk/(256*N). At a 10 MHz system clock and N=2, PWM frequency is 19,531.25 Hz. Outputs are control signals, not motor power drivers.

# How to test

Select the project, provide a running system clock and reset it. Drive SPI Mode 0, MSB first, exactly five bytes per CS assertion. ui_in[0]=SCK, ui_in[1]=CS_n, ui_in[2]=MOSI, uo_out[2]=MISO. Every frame returns C2, flags, active left, active right, active DIV encoding. READ is 00 00 00 00 00. WRITE is A1 left right DIV flags, where DIV=N-1 and only flags bit0 (enable) is valid. CLEAR_ERRORS is C0 00 00 00 00. Reset defaults are C2 00 00 00 01.

Use a 10 MHz system clock and 100 kHz SPI for the example. Each SPI high/low phase and CS setup/hold/idle gap must be at least eight system-clock cycles. MISO is a dedicated push-pull signal, not tristated.

Send A1 40 C0 01 01, poll until pending clears and generation toggles, and measure 25% and 75% PWM at uo_out[0:1]. A pending configuration must not be overwritten; a second write is rejected with overrun. Malformed frames set a sticky error and do not update the configuration. Full protocol, firmware and bench procedure are included in PROTOCOL.md and WIRING_AND_BRINGUP.md.

# External hardware

A compatible Tiny Tapeout demo board supplies the independent system clock and reset. A 3.3 V MCU supplies SPI, with a common ground. An oscilloscope or logic analyzer measures PWM. Pin names are logical project signals; use the chosen board's connector mapping, and ensure its onboard controller releases lines driven by the external MCU. No physical board or FPGA test has been performed in this local project.
