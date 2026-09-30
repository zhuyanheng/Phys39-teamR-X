# Module 4 上课操作清单（2026-09-28；已按教授新版要求更新）

**打开本页后从第 0 步开始。** 本页是今天现场的打勾清单；[十行数据表](module_04_open_loop_tec.md)是正式测量记录，[新版 A2 分析草稿](../assessments/a2_open_loop_tec.md)在实验后填写，**仓库草稿不是课程要求的提交物**。老师已看过之前的 Part 1 演示；这里仍要做**通电前复核**，但不要求擅自重做 20/30/60 °C 安全实验。课程要求所有物理运行和安全测试在课堂进行，测量温度保持 **10–45 °C**；不要故意加热到 60 °C。

> **硬停条件：** 温度向错误方向变化、接近 10/45 °C 边界、显示/串口停止更新、电源电流异常上升、TEC/H-bridge/散热器异常发热或有气味时，立即在 GUI 输入 `0` 并确认固件输出为 `0/0`，关闭执行器电源，通知老师。若 GUI/串口失灵，**不要等软件响应，直接关闭执行器电源**。不要让通电装置无人看守，也不要触摸带电端子或高温部件。

## 0. 到实验台后，先打开这些东西（此时执行器电源必须 OFF）

- [ ] 在 VS Code 打开此仓库和本页；同时打开[十行数据表](module_04_open_loop_tec.md)。请 agent 从此页开始，现场每做完一步才勾选，并在表中记录数值/文件名。日期、操作者、老师：________。
- [ ] 确认 TEC 执行器电源开关在 **OFF**、输出未使能；Arduino 只由 USB 连接电脑。不要为了“先看有没有反应”给 TEC 通电。
- [ ] 确认准备使用的是 [Module 4 Arduino sketch](../../Module_4/arudino/part_1/part_1.ino) 和 [Module 4 Python GUI](../../Module_4/python/part_5_tec_control_gui.py)，不是 Module 3 旧控制程序。当前源码参数为：固件上限 `60 °C`（原 10–45 °C 固件限制已移除）、热方向 `D9`、冷方向 `D10`、串口 `9600`；课程测量范围仍需单独遵守。实际上传版本/commit：________。

## 1. 断电状态核对线路；老师批准前不要通电

本组 Module 3 **实物记录**对应以下连接；这是一张**核对图，不是让你带电重新接线**。如现场标签/实物与它不一致，停下让老师确认，不要猜。所有电源→桥→TEC/热开关的高电流线都是 **18 AWG 绞合铜线**；热开关使用已压接的两个 female spade 端子。

```text
高电流电源 V+ ──18 AWG──> H-bridge B+
高电流电源 V− ──18 AWG──> H-bridge B−

H-bridge M+ ──18 AWG──> 热开关 ──18 AWG──> TEC+
H-bridge M− ──18 AWG─────────────────────> TEC−
                 （热开关必须与 TEC 串联）

Arduino 5 V ──> H-bridge VCC、R_EN、L_EN（两个 enable 保持 HIGH）
Arduino GND ──> H-bridge 逻辑 GND（共地）
Arduino D9 ──> H-bridge RPWM（本组 HEAT）
Arduino D10 ──> H-bridge LPWM（本组 COOL）

热敏电阻分压：Arduino 5 V ──> 100 kΩ 固定电阻 ──> A0
                                          A0 ──> 100 kΩ NTC ──> GND
```

TEC **不能直接接到 Arduino D9/D10**；这两个针脚只给 H-bridge 逻辑信号。热开关必须能在软件失效时独立断开 TEC 电流。先前两张旧示意图把热开关画在 TEC 的另一侧，还画成断开状态；它们与以上实物记录的位置不一致，已从工作目录移除，**不能当作已核实的接线证据**。在工作记录中按老师确认的实物留下接线信息，供后续模块使用；**新版 A2 不再要求放接线图**。热交换器/水泵与风扇须按老师批准的供电方式接好，并且在给 TEC 非零 PWM 前实际运行。

- [ ] 看实物标签逐根核对 `V+→B+`、`V−→B−`、`M+→热开关→TEC+`、`TEC−→M−`；检查所有高电流线为 18 AWG、极性正确、无松动/裸露短路。若热开关实际装在 TEC 另一侧，只要**仍严格串联**，先记录真实路径并请老师确认，不要为了匹配文字自行改线。现场真实路径：________。
- [ ] 在**电源断开**时，用万用表确认常闭热开关两端导通；轻拉检查两个 spade 压接牢固。记录读数/老师确认：________。不要带电做连续性测量。
- [ ] 核对 Arduino `5 V/GND/D9/D10/A0` 与桥的 `VCC/GND/R_EN/L_EN/RPWM/LPWM`、分压器和 TEC 的物理接点；两方向 PWM 输入不得同时主动输出。检查热交换器的供电连接，但暂不使 TEC 运行。
- [ ] 在实验本画出**真实的完整高电流路径**，并给老师看图和实物，请其检查线径、极性、热开关串联与导通、压接和电源电流限制。老师批准人/时间：________。**未勾选这一项，不进入第 3 步通电。**

## 2. Arduino + GUI 零功率开机检查（执行器电源仍 OFF）

- [ ] 在 Arduino IDE 打开 `Module_4/arudino/part_1/part_1.ino`，选 **Arduino Uno** 和实际串口，先 Verify 再 Upload；不要改回临时 20/30 °C 版本。上传成功后关闭 Serial Monitor/Plotter，避免占用串口。Arduino 端口：________。
- [x] 在 GUI 文件顶部核对 `SERIAL_PORT` 是否等于实际端口（仓库当前为 `/dev/cu.usbmodem101`）；只有端口变了才改此项。于仓库根目录运行 `.venv/bin/python Module_4/python/part_5_tec_control_gui.py`；若明天不是同一台电脑，先确认相应 Python 环境已经安装 `requirements.txt`。GUI 启动时会发 `PWM 0`，并在 `Module_4/data/` 建立新的带时间戳 CSV。**本次新 CSV：`Module_4/data/module_04_tec_20260928_095700_881845.csv`。**
- [x] 旧版本启动记录：约每 0.5 秒更新温度与 Arduino time；初始约 `23.80 °C`、`Safety OK`、PWM `0/0`，当时 CSV 报告阈值 `60/10/45`。这是旧运行证据，不能证明新上传的 60 °C-only 固件已生效。
- [ ] 对新版本重新核对 GUI/新 CSV 的 `Safety=OK`、`Heat PWM=0`、`Cool PWM=0`、`Limit (C)=60.00`，并确认新 CSV 不再有 `low_limit_C` / `operating_high_C` 两列；记新文件名：________。
- [ ] 给老师看[既有 Part 1 安全证据](../../Module_4/part_1_safety_check.md)：20 °C 断电演示、恢复 60 °C、30 °C 现场演示。只有老师要求时才在断开 TEC 电源的条件下重做；不可故意加热到 60 °C。固件串口的 `0/0` 是软件报告，不等于已用仪表测到 D9/D10 为零。

## 3. 老师批准后，谨慎通电并选 Part 2 的十个 PWM 值

- [x] 先确认 GUI 仍是 `PWM 0`、温度可信、老师已批准**本次 Module 4**电源电压与电流限制。把实际设置写入[工作记录](module_04_open_loop_tec.md#settings-to-write-down-before-the-first-new-run)：电压 **12** V；限流 **10** A（原始设定，记录一次即可，老师表示无需逐步记录）。
- [ ] 按老师批准的方式开启电源；保持 GUI `PWM 0`，先确认热交换器的泵/风扇确实运行、供电电流正常，然后才允许非零 TEC PWM。电源显示电流（PWM 0）：________ A。
- [ ] GUI 操作：先确保 `PWM command=0`；点方向按钮使其显示红色 `HEAT`；在右侧 PWM 数字框输入**老师认可的低值**（例如 10 只作为历史低 PWM 探索起点，绝非课程指定或保证安全的值），按 Enter/移开焦点使设置生效。看温度是否升高、红色 PWM 曲线及电源电流；记录值与现象：________。然后输入 `0`，确认固件输出 `0/0`。
- [ ] 在 PWM 0 时点方向按钮切到蓝色 `COOL`（程序切换方向时也会自动归零，但仍要亲眼确认）；用老师认可的低值短测。看温度是否下降、蓝色 PWM 曲线及电源电流；记录值与现象：________。然后回 `0`。若方向不符，立即停机请老师检查接线/标定。
- [x] 操作者已完成 HEAT/COOL 最大档位探索，选定 `Hmax=45`（报告约 45 ± 0.3 °C；原始 HEAT-45 片段 45.31–45.45 °C）及 `Cmax=96`（报告约 10 °C；原始 COOL-96 片段 9.83–10.17 °C）。操作者接受边界附近的小幅波动；此处只确认档位选择，不替老师确认课程 10–45 °C 范围的解释。
- [x] 已计算并写入十行表的准确整数档位：HEAT `[0, 11, 23, 34, 45]`（0.5 档取 23）；COOL `[0, 24, 48, 72, 96]`。各方向四个非零值互异。
- [x] 操作者现确认现场判稳规则：温度停止持续单向变化、只在一个区间内波动；加热看不再持续升高，制冷看不再持续下降。已测档位取末约 20 s 的平均温度；未规定固定波动幅度或斜率阈值，也未声称老师另行确认过定量阈值。

## 4. Part 3：正式收集 H0–H4、C0–C4

每一行都按同一套动作走：① 在 PWM 0 或上一设置下选方向，**先记录改变 PWM 前**的 start T 与 Arduino time；② 把 PWM 设为上一步确定的准确整数，记下命令生效时的 Arduino time；③ 观察温度曲线及程序状态；④ 温度不再持续单向变化、仅在区间内波动时，记录末约 20 s 窗口的起止 `time_s`、均值、等待秒数、备注与 CSV 文件名；⑤ 打开 CSV 核实该窗口的方向、PWM、温度和固件输出后给该行打勾。电流不是这张稳态数据表的必填量。

- [x] `H0`：HEAT 方向、PWM 0 基线已记录；末约 20 s 均值 **23.44 °C**，窗口 5.10–24.82 s。CSV 从已接近常温时开始，先前等待时间未记录；见[表格 H0](module_04_open_loop_tec.md#ten-formal-measurements--fill-only-from-new-supervised-runs)。
- [x] `H1`：HEAT PWM 11，[表格 H1](module_04_open_loop_tec.md#ten-formal-measurements--fill-only-from-new-supervised-runs)已记录 218.12–237.97 s，均值 28.31 °C。
- [x] `H2`：HEAT PWM 23，[表格 H2](module_04_open_loop_tec.md#ten-formal-measurements--fill-only-from-new-supervised-runs)已记录 402.29–422.14 s，均值 34.62 °C。文件起始有 3 行 PWM 233，已标记为稳态窗口之外的异常，不删原始记录。
- [x] `H3`：HEAT PWM 34，[表格 H3](module_04_open_loop_tec.md#ten-formal-measurements--fill-only-from-new-supervised-runs)已记录 519.31–539.16 s，均值 40.42 °C。
- [x] `H4`：操作者决定采用最大档位探索 CSV 中 HEAT 45 的末约 20 s 均值 **45.37 °C**；40/40 行高于课程 45 °C 上界。原始曲线和范围例外说明均保留，老师 2026-09-28 已接受；见[表格 H4](module_04_open_loop_tec.md#ten-formal-measurements--fill-only-from-new-supervised-runs)。
- [x] `C0`：COOL 方向、PWM 0 基线已记录；末约 20 s 均值 **23.44 °C**，窗口 2.08–21.78 s。回温过程不在这份 CSV 内，实际回温等待时间未记录；见[表格 C0](module_04_open_loop_tec.md#ten-formal-measurements--fill-only-from-new-supervised-runs)。
- [x] `C1`：COOL PWM 24，[表格 C1](module_04_open_loop_tec.md#ten-formal-measurements--fill-only-from-new-supervised-runs)已记录 408.97–428.82 s，均值 20.44 °C。
- [x] `C2`：COOL PWM 48，[表格 C2](module_04_open_loop_tec.md#ten-formal-measurements--fill-only-from-new-supervised-runs)已记录 358.90–378.75 s，均值 16.99 °C。
- [x] `C3`：COOL PWM 72，[表格 C3](module_04_open_loop_tec.md#ten-formal-measurements--fill-only-from-new-supervised-runs)已记录 336.72–356.57 s，均值 13.40 °C。
- [x] `C4`：操作者决定采用最大档位探索 CSV 中 COOL 96 的末约 20 s 均值 **9.99 °C**；40 行中有 21 行低于课程 10 °C 下界。原始曲线和范围例外说明均保留，老师 2026-09-28 已接受；见[表格 C4](module_04_open_loop_tec.md#ten-formal-measurements--fill-only-from-new-supervised-runs)。

**课程的测量范围仍为 10–45 °C。** 被 safety shutdown 截断、方向/PWM 与记录不符或未达到稳态的区间不能当正式点。H4/C4 是操作者明确决定采用的超范围例外，老师 2026-09-28 已接受、无需补测；在分析或提交材料中仍应如实说明它们超出 10–45 °C 范围。

## 5. 离开实验台之前（不要把核对留到回家）

- [ ] GUI 输入 `0`，确认最新串口/CSV 行的 HEAT 与 COOL 固件输出均为 `0`；然后关闭执行器电源，确认热交换器按老师要求收尾，最后退出 GUI。不要在非零 PWM 时直接拔 USB 作为正常停机方法。
- [ ] 打开明天新生成的 CSV，确认文件并非只有表头；核对十行表每一行都有实际数值、等待时间、原始文件名和稳态时间窗口。确认 HEAT/COOL 各有至少一段时间曲线。缺点或异常现在就请老师决定是否现场重测。
- [ ] 给老师展示记录/原始文件、实际电源电压与限流、接线和两方向结果；记下老师要求的改动：________。将选定的正式原始文件整理到 [`data/module_04/`](../../data/module_04/)；保留旧探索/安全 CSV 的身份说明，不把它们混作正式点。

## 6. 下课后 A2（新版截止：周一 2026-10-05 18:00）

教授新版预计 S8 课外工作共约 **1 小时 30 分钟**：准备表格/安全边界 30 分钟、作图和斜率 15 分钟、热量平衡分析 30 分钟、检查提交 15 分钟。若需要补测，留待下一次有老师监督的机会，不在家自行运行装置。

- [ ] 用真实数据补齐 [`steady_state.csv` 格式说明](../../data/module_04/README.md)与十行工作表；运行[已更新的作图脚本](../../Module_4/python/plot_a2.py)，检查 HEAT/COOL 时间曲线和**负 PWM=COOL、正 PWM=HEAT** 的主图。对两侧各自选定的近似线性区间画拟合线，标出范围、斜率单位与实际稳态判据。
- [ ] 求两侧斜率 `m_h`、`m_c`（°C/PWM count）和 `r=m_h/|m_c|`，注明拟合所用 PWM 范围与曲率。完成 PWM 周期平均电流证明：`⟨I⟩=DI`、`⟨I²⟩=DI²`，注意后者**不是**`(DI)²`。
- [ ] 用课程给的稳态能量平衡推导 `r` 与 Peltier/Joule 热率之比；热传导项已经并入有效 `G`，不要重复计算。详见[新版 A2 分析草稿](../assessments/a2_open_loop_tec.md)。
- [ ] **先自己查看**课程指定的 Laird CP14-127-045 数据表，在热端 27 °C 一栏找 `R_M`、`I_max`、`Q_c,max`（ΔT=0）、`ΔT_max`，抄单位和适用条件。然后算厂家最大电流条件下的 Joule/Peltier 热率与预测斜率比；不要把 `D=1` 当成实验装置一定达到 `I_max`。
- [ ] 将实测比值和厂家最大电流预测比较，解释差异、室温上下被动传热方向，以及为什么近似对称的被动传导本身不能解释两侧斜率大小不同。写约 100–150 个英文词的结论。
- [ ] 整理**1–2 页 PDF**：只放新版要求的图（含拟合线）、斜率与比值、推导、注明条件的 Laird 数值与计算、比较/传导解释和结论；不要重复 C2/C3 接线图、装置描述、安全演示或代码文档。按 `A2_Lastname_Lastname.pdf` 命名，**两名队员各自上传同一份 PDF**。新版不要求为 A2 新建仓库文档或 Git checkpoint，但课堂原始数据与代码必须保留。

## 给 VS Code agent 的现场指令（可直接复制）

> 请先读 `docs/module_notes/module_04_lab_day_runbook_2026-09-28.md` 和 `docs/module_notes/module_04_open_loop_tec.md`。一次只推进当前未完成步骤：能从最新 CSV/代码核实的项目由你核实，接线、电源读数、老师批准和装置状态必须由我现场确认。每完成一项，写入数值与来源，再在本清单打勾，并告诉我下一步具体要按哪个按钮/看哪个读数。不得自行接线、通电、提高 PWM、修改安全阈值或让装置无人值守；出现异常先让我关执行器电源并通知老师。旧 CSV 只作探索/安全记录，不得填入正式稳态表。

参考：[课程 Module 4](https://sethfraden.github.io/Phys39F26-course/labs/lab-04/) · [课程硬件页](https://sethfraden.github.io/Phys39F26-course/hardware/) · [本组 Module 3 接线记录](module_03_tec_gui.md)。
