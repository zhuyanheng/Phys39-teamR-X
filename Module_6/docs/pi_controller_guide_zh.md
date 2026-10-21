# Module 6 实物 P／PI 控制器

## 启动

双击 [run_pi_control.command](../run_pi_control.command)，或从项目根目录运行：

```bash
./Module_6/run_pi_control.command
```

这是连接 Arduino 的实物控制器，与 `run_gui.command` 的数学模拟器不同。
使用项目根目录 `.venv` 中已有的 PySide6、pyqtgraph、pyserial。
窗口打开时不连接串口，不开始控制。没有新固件需要自动上传。

只查看界面且不连接硬件：

```bash
./Module_6/run_pi_control.command --preview
```

## 通电前给老师检查的代码

- [pi_controller.py](../python/pi_controller.py)：`step()` 计算误差、实际测量间隔、积分、P／I 项及限幅。
- [pi_tec_control_gui.py](../python/pi_tec_control_gui.py)：串口发送、开始／停止、积分清零、测量超时和 CSV 记录。
- 使用 [Module 6 Arduino sketch](../arduino/p_only_tec/p_only_tec.ino)，从 Module 5 原样复制，与 Module 4 同一份源码。保留 1000 次 ADC 平均、原有串口格式和独立温度关断。确认实际上传的版本与此一致。

控制方程：

```text
e = setpoint - measured_temperature
dt = current_accepted_Arduino_time - previous_accepted_Arduino_time
proposed_q = q + e*dt
uP = Kp*e
proposed_u = uP + Ki*proposed_q
if proposed_u is above the positive limit and e > 0: freeze q
if proposed_u is below the negative limit and e < 0: freeze q
otherwise: accept proposed_q
uI = Ki*q
requested_u = uP + uI
clamped_u = clamp(requested_u, -PWM_limit, +PWM_limit)
sent_u = round(clamped_u)
```

每次开始时 q=0，第一条接受的测量 dt=0；后续使用实际 Arduino 时间差。
不根据 GUI 刷新频率或模拟器的 dt 累积误差。P 模式强制 I 项为零。
条件积分允许与饱和方向相反的误差消除已有积分。

## 实验操作顺序

1. 按课程要求，让老师检查控制计算、独立 Arduino 温度保护、PWM 限幅和拟用增益范围；本程序未在真实 TEC 上验证。
2. 关闭 Arduino Serial Monitor 和其他占用同一串口的 GUI。
3. 选择 Arduino 串口，点击 **Connect (PWM 0)**。等待新温度、`Safety: OK` 和固件报告的 PWM=0。
4. 选择 **P** 或 **PI**，填写目标温度、Kp、Ki、PWM limit，保持 anti-windup 勾选。
5. 点击 **Start P / PI**。它重新请求 PWM=0、清零积分，然后等下一条测量计算输出。默认 Kp=2、Ki=0.01 只是输入初值，不是已批准的实物增益。
6. 运行期间增益、模式、输出限制被锁定。修改目标温度后，点 **Apply setpoint step** 才生效，用来记录同一次运行的升温／降温阶跃；此操作保留积分记忆。
7. 换增益或控制模式前，点 **STOP — PWM 0**；确认固件报告 PWM=0，再修改并重新开始。
8. **Zero integral + STOP** 会先停止、请求输出归零，再清零积分。它不会在带输出时悄悄重置积分。
9. 出现错误方向、界面冻结、异常持续饱和或振荡增长时停止并按课堂硬件关断流程处理。

软件默认对称 PWM 上限为 255（按用户要求解除原先的 45 限幅），即 Arduino
8 位 PWM 的完整范围；带符号命令范围为 -255 至 +255。温度、串口超时和
anti-windup 保护保持启用。六组保留运行使用同一个 PWM 上限；之前上限为 45
的记录不能直接当作相同输出条件下的对照。

## 记录和显示

数据自动保存到 `Module_6/data/physical/module_06_pi_日期_时间.csv`，每次串口连接创建一份。
同一 CSV 内用 `run_id` 区分控制运行；`start`、`stop`、`setpoint_step` 等事件保留设置变化。
图上显示温度和设定值、带符号 PWM、P／I 项、误差，窗口保留最近 180 秒，CSV 保留全部测量。

关键列：`dt_s`、`integral_error_C_s`、`p_term_pwm`、`i_term_pwm`、
`requested_signed_pwm`、`clamped_signed_pwm`、`sent_signed_pwm`、
`reported_signed_pwm`、`saturated`、`integration_blocked`。

同一行的固件 PWM 是测量时已在执行的命令；`sent_signed_pwm` 是 Python 收到该测量后
发出的下一条命令。两者存在串口／采样延迟，不应直接视为同一时刻的实际输出。
新命令只有在随后固件报告中才能得到反馈确认。历史积压测量会保存，但不会逐条重放输出。

测量超时超过 2 秒、重复／倒退的 Arduino 时间、非有限或超出 10–45 °C 的温度、
非 OK 安全状态、串口异常或记录失败都会停止控制并尝试请求 PWM=0。
串口断开或 Python 冻结时，不能保证零命令能到达 Arduino；既有独立硬件保护仍然必要。

## 已验证与未验证

无硬件测试覆盖 P／PI 算法、真实时间差、双向饱和、防积分饱和与反向解饱和、
目标阶跃、清零／停止、串口异常、部分写入、测量超时、Arduino 时间重置、积压数据和日志失败。
测试使用假的串口，不会操作真实装置。运行方式：

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python Module_6/python/test_pi_control.py
```

真实 Arduino 通信、符号方向、保护关断和 PI 动态仍需在老师监督下验证。
