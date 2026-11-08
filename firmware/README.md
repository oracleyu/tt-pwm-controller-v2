# MCU 控制示例

`pwm_spi.c/.h` 是不依赖 MCU 厂商的 C11 驱动。调用方实现三项回调：完整 5 字节 SPI 事务、微秒计时和微秒延时；具体协议和时序约束见根目录 PROTOCOL.md。单调用者使用，外部需要串行化并发调用。

- `pwm_read()`：读回状态与已生效配置；检查 C2 ID 和保留位。
- `pwm_clear_errors()`：清除错误并再次读回确认。
- `pwm_configure()`：等待队列空，写完整配置，再等待 generation 翻转，核验全部配置；divider 参数为 1..256。
- 返回值区分参数错误、传输失败、协议错误、设备错误和超时。超时参数小于 2^31 µs，计时器允许 32 位回绕。

`arduino_pwm_demo/` 是 SPI 100 kHz、Mode 0 的适配示例，包含相同的 C 驱动副本。修改 MCU 的 CS GPIO 和默认 SPI 引脚设置；Arduino 示例要求 ASIC clk 至少 4 MHz，推荐 10 MHz。此文件夹可作为 Arduino sketch 打开。它不负责选择 Tiny Tapeout 项目或生成系统时钟，必须先在演示板设置这些功能。

主机已用 C11 严格警告及 AddressSanitizer/UndefinedBehaviorSanitizer 编译并执行 `test_driver.c`，覆盖帧生成、读回校验、错误、超时及计时器回绕。该测试使用模拟 SPI 回调；没有连接实际 MCU、板卡，也没有使用具体开发板 SDK 编译 Arduino 示例。硬件适配和上板结果必须另行记录。

从工程根目录执行 `make firmware-test` 可复跑主机测试。
