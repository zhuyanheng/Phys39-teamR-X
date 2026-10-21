# Module 6 Arduino 程序

[p_only_tec.ino](p_only_tec/p_only_tec.ino) 从 Module 5 原样复制，与 Module 4 的
`arudino/part_1/part_1.ino` 逐字节一致，未修改控制或保护逻辑。

虽然历史文件名是 `p_only_tec`，它也适用于 Module 6 的 PI 实验：
P／PI 计算在 Python 中执行，Arduino 负责测温、接收串口 PWM／方向命令和独立温度关断。

用 Arduino IDE 打开 `p_only_tec/p_only_tec.ino`，选择实际 Arduino Uno 和串口。
文件夹与 `.ino` 同名，符合 Arduino IDE 的 sketch 目录要求。
如果板上已经运行同一版本，不必仅因为复制文件而重新上传。

原有设置：9600 baud、1000 次 ADC 电压平均、约 500 ms 报告间隔、
D9 HEAT／D10 COOL、60 °C 独立软件温度关断及无效传感器关断。
实际上传版本、接线与保护仍需现场核对；本次只复制源码，未上传或操作硬件。
