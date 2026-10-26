# Module 7 实验日 runbook（S16 2026-10-26 → S17 2026-10-28）

**按依赖顺序执行，不按钟点执行。** 第 1 步是唯一"卡住后面全部工作"的一步：没有六通道采集链，课堂时间就采不到 `T(x,t)`，C5 也就没有可演示的数据。计划与公式汇总见 [Module 7 README](../../Module_7/README.md)，A4 脚手架见 [a4_finite_length_biot.md](../assessments/a4_finite_length_biot.md)。

> **Stop condition（安全）：** 温度朝错误方向变化、接近课程工作区间 10 °C / 45 °C 边界（本轮实验区间 20–45 °C，稳态试探不得超过 55 °C）、显示或串口冻结、电源电流异常升高、TEC / H 桥 / 散热器异常发烫或有异味时，在 GUI 输入 `0`，确认固件输出 `0/0`，关闭执行器电源，并告知老师。GUI 或串口失效时应直接切断执行器电源，不要等软件。运行时不要无人看管，不要触碰带电端子或高温部件。

## 0. 为什么是这个顺序

| 步骤 | 依赖 | 阻塞了什么 | 能否课后补 |
|---|---|---|---|
| 1 六通道测量链 | 只依赖代码（TEC 断电也能测） | 标定、阶跃、C5 全部 | 能，但会浪费课堂时间 |
| 2 几何 + 传感器地图 | 卡尺 / 尺子 | A4 Part 3/4、`mL`、`ε_T` | 能，但 C5 要现场展示 |
| 3 交叉标定 | 六通道链 + 温水 | 剖面梯度的有效性 | **不能**（探头装进 TEC/杆后无法再同温浸泡） |
| 4 阶跃响应 | 标定 + 位置选定 | Part 3 稳态剖面、C5 | **不能**（需要 20 °C 全杆初态） |
| 5 A4 Part 2 推导 | 只需教材 | A4 6/10 分 | 课后做，但截止 10/28 09:05 |
| 6 A4 Part 3/4 + 选点 | 第 2、4 步 | A4 5/10 分 | 课后做 |

**一句话**：先花 2–3 小时把软件做通（第 1 步），再用课堂时间做"过期作废"的标定与阶跃（第 3、4 步），推导型作业（第 5、6 步）放在晚上并行。

## 1. 先做：六通道测量链（TEC 断电状态下即可验证）

- [ ] 清点探头：确认有 **6 个**可用热敏电阻，其中至少 5 个能装进杆孔、TEC base 用的那个能固定。不够就先焊线 + 热缩管绝缘，标签 `TEC`、`1`–`5` 贴牢并保持到学期末。
- [x] 复制而非修改 Module 6（2026-10-26 完成）：`Module_6/arduino/p_only_tec/p_only_tec.ino` → `Module_7/arduino/module_07_rod_controller/module_07_rod_controller.ino`；`Module_6/python/pi_tec_control_gui.py` → `Module_7/python/module_07_rod_acquisition_gui.py`。**Module 6 的两个文件保持原样**，作为可工作的 checkpoint。
- [x] 通道映射：`A0` = TEC base，`A1`–`A5` = rod 1–5。`A0` 仍是唯一的 PI 反馈与软件温度上限来源；5 个杆通道只测量，不进入控制律。
- [x] 采样预算：TEC 1000 次/周期（同 Module 6），杆通道 100 次/周期（一次 `analogRead` ≈ 112 µs，全扫 ≈ 168 ms < 500 ms 周期）。
- [x] 串口记录格式（启动时打印 `#firmware`/`#channels`/`#pins`/`#DATA,...` 表头，之后每周期只发一条 `DATA` 行，其他行一律以 `#` 开头）：

```text
#DATA,time_s,tec_C,rod1_C,rod2_C,rod3_C,rod4_C,rod5_C,pwm,heat_cool,heat_pwm,cool_pwm,limit_C,safety,rod_ok
DATA,12.50,23.41,23.38,23.36,23.34,23.31,23.29,120,1,120,0,60.00,OK,5
```

- [x] Python 侧只解析完整 `DATA` 行（`Module_7/python/rod_protocol.py`）；坏行/表头/应答跳过不崩；界面显示 `rows ok/bad` 计数；6 条曲线固定颜色且 TEC 加粗。
- [x] CSV 测量列与 `DATA` 行同名同序，**存原始读数**，不写修正值；文件名带时间戳，`'x'` 模式打开绝不覆盖；每行 flush。
- [x] 静态验证：`arduino-cli compile --fqbn arduino:avr:uno` 通过（7844 B flash / 545 B RAM）；`python3 Module_7/python/test_rod_protocol.py` 19 个测试全通过（含"解析器字段名 = 固件表头"交叉检查）。
- [ ] 集成检查（TEC 断电）：逐个用手指加热一个探头，确认**只有**它对应的 Arduino 列与 Python 曲线变化；核对"一条 `DATA` 行 = 一组显示值 = 一行 CSV"；确认上电 PWM 从 0 开始并能响应零功率命令；拔掉一个杆探头，确认只有该列变 `nan`、`rod_ok` 下降，而 TEC 安全停机仍然正常。
- [ ] 打开 Serial Monitor 测试后**先关闭**再开 Python GUI（同一串口只能一个程序占用）。
- [ ] 此时就 commit 一次，记下 hash：C5 receipt 必须引用已 push 的采集代码与证据 commit。

## 2. 紧接着：几何与传感器地图（约 15 min，无需通电）

- [ ] 记录材料 `6061-T6 铝`；量直径 `d`、杆总体物理长度、以及**从第一个热敏孔到杆尖**的分析长度 `L`，各自带不确定度。标称 `d = 12.7 mm`，必须实测。
- [ ] 算 `A = πR²`、`P = πd`、`A/P = R/2`（SI 单位，写进记录）。
- [ ] 把 rod 1 装进第一个孔，定义该孔为 `x = 0`（它**不是**杆的物理端点，也**不是** TEC 里那个热敏电阻）；量其余 4 个位置与杆尖 `x = L`，记录每个位置不确定度。
- [ ] 画/拍一张图：永久标签、Arduino 通道、坐标正方向、实测位置。存 `Module_7/figures/part_01_sensor_map.png`。
- [ ] 第一次算预测值：用实测 `d`、`L` 和 `h = 5–10 W/(m²·K)`、`k ≈ 167 W/(m·K)` 更新 `m`、`1/m`、`mL`、`Θ_tip`、`Bi⊥` 和逐传感器 `ε_T(x)`，写进 [runbook 末节的预测记录](#8-预测记录开加热前必须写完)。

## 3. 课堂 S16：交叉标定（一次性，过期作废）

必须在探头**永久装入 TEC base 和杆之前**完成，否则无法让 6 个探头同温。

- [ ] 按 Step 1 的接线与采样率，把 6 个探头一起放进盛温水的 Styrofoam 杯，覆盖约 `20 °C < T < 60 °C`；只浸防水端，接头保持干燥，探头不碰杯壁/杯底。
- [ ] 轻微持续搅拌，让 6 个探头经历**同一条**降温曲线；同时记录所有通道 ≥ 60 s。
- [ ] 以 `tec_C` 为参考，逐杆通道拟合 `T_TEC = a_i + b_i T_i`；画 `T_i` vs `T_TEC`（含 identity 线与拟合线）。
- [ ] 画修正残差 `(a_i + b_i T_i) − T_TEC` vs `T_TEC`；**先写判据再评估**：起始判据是修正后平均差 < 0.2 °C 且整段无 > 0.2 °C 的残余趋势。若噪声水平明显不同，改写判据并说明理由。
- [ ] 保存标定表（通道、`a_i`、`b_i`、点数、温度范围、残差均值/标准差/最大绝对值）到 `Module_7/data/calibration/`；原始 CSV 保持不动。
- [ ] 结论：通道差异是否小于实测的杆内温差？若否，先修硬件/接线，不要开始剖面测量。

## 4. 课堂 S16 后半：baseline + `20 → 45 °C` 阶跃（最长的一个环节，尽早开跑）

杆的时间常数是几十分钟量级，开始太晚就采不到稳态。

- [ ] 稳态试探：`T_set = 45 °C`（不得超 55 °C），移动其余 4 个探头在孔位间试，用 `ln θ` vs `x` 选点。要求：最远点 `0 < θ₅ ≤ θ₁/e`、点散布在 semilog 图上不挤在一端、不落在噪声/室温漂移里。
- [ ] 位置确定后**不再改动**，逐个记录位置与不确定度（补进传感器地图）。
- [ ] 全杆回到 `T_set = 20 °C` 平衡，记录室温（远离装置处测得）与 6 通道；确认杆通道之间差异在标定判据内。这段就是 baseline。
- [ ] 用 PI 做 `20 → 45 °C` **非振荡**阶跃，连续记录到满足稳态判据。同时保存：指令 TEC 温度、实测 TEC 温度、**rod 1 实测 `T(0,t)`**（模型边界条件用 rod 1）。
- [ ] 稳态判据（先写后测）：所有探头 `|dT_i/dt| < 0.02 °C/min` 持续 ≥ 10 min。
- [ ] 中途记录观察：哪个探头先响应、幅度如何随距离衰减。用来对照第 8 节的预测。

## 5. 今晚：A4 Part 2 推导（6/10 分的核心，不能再拖）

A4 的 6 分在 Part 2（3 分，推导）+ Part 3（3 分，误差评估），都是纯理论，不依赖今天的任何数据。

- [ ] 读 Lienhard §4.5，教材 pp. 163–173，对着 [fin-design-derivation](https://sethfraden.github.io/Phys39F26-course/labs/fin-design-derivation/) 走 (4.28) → (4.30) → (4.31b) → (4.41)。
- [ ] 切片能量平衡（每个符号带单位）：

```text
−kA (dT/dx)|_{x+δx} + kA (dT/dx)|_x + hP δx (T − T∞) = 0        [W]
δx → 0  ⇒  d²θ/dx² − m²θ = 0,    m² = hP/(kA)                     [1/m², m in 1/m]
θ(0) = θ₀ (Dirichlet)；dθ/dx|_{x=L} = 0 (Neumann, 绝热端)
⇒  Θ(x) = cosh[m(L − x)] / cosh(mL),   Θ_tip = 1/cosh(mL)
```

- [ ] 写清两个边界条件的物理含义：基温由 rod 1 实测给出（不是理想热源，也不是 TEC 指令）；绝热端表示端面无净热流。
- [ ] Part 1：Lienhard Problem 1.3，逐式给单位并指出物理上不合理的结果。
- [ ] 全部写进 [a4_finite_length_biot.md](../assessments/a4_finite_length_biot.md)，边写边打勾。

## 6. 周二：A4 Part 3/4 + 选点分析 + C5 排练

- [ ] Part 3：Problem 4.12 取半无限极限；Example 4.8 / Problem 4.20 做端部近似；用**实测** `L` 与位置算 `mL` 和逐点 `ε_T(x)`；结论写明依赖哪些位置、什么判据。若 `ε_T > 5%`，保留有限长 cosh 解并这样陈述。
- [ ] Part 4：`Bi⊥ = hR/(2k)` 与自洽式 `(mR/2)²` 各算一次；**单独**给半径结论，不与 Part 3 的长度结论合并；答散热器 / 航天器辐射器应用题（太空无对流，用 `q″ = εσ(T_s⁴ − T_sur⁴)`）。
- [ ] 写 `docs/module_notes/module_07_rod_instrument.md`：传感器地图、标定结果、几何、baseline、阶跃曲线、运行元数据、代码文件名与 commit hash。
- [ ] C5 排练：每人讲清一条测量链环节 + **一个主导不确定度**（候选：传感器位置、接触热阻、室温漂移、标定残余偏差、`m` 的拟合不确定度）。能回答"为什么边界条件用 rod 1 而不是 TEC"和"为什么稳态实验分不开 `k` 与 `h`"。
- [ ] 导出 `A4_Lastname.pdf`，首页写姓名、A4、日期、仓库 URL、**精确 commit hash**（先 commit 再回填）。

## 7. 周三 10/28：两个硬截止

- [ ] **09:05** 前：Moodle 提交 `A4_Lastname.pdf`；确认 `docs/assessments/a4_finite_length_biot.md` 已 push。
- [ ] **11:55** 前：Moodle 交 C5 Team Checkoff receipt，引用已 push 的采集代码与证据 commit。
- [ ] 课上演示 C5：标定后的杆探头、传感器坐标与接线、六通道同步记录、baseline + 初始阶跃数据、含时间戳/单位/标签/备注的文件。

## 8. 预测记录（开加热前必须写完）

先写四句话，再加数字；数字用实测几何重算后替换下表。

1. 响应顺序：`rod1 → rod2 → …`（离 TEC 越远越晚、越小）
2. 幅度衰减：每段距离约按 `e^{−mΔx}` 下降
3. 稳态剖面形状：`cosh[m(L−x)]`，凸向上、在杆尖趋平（`dθ/dx = 0`）
4. 是否会看到有限端：给出 `Θ_tip = 1/cosh(mL)` 的预测值并说明"若 > 0.1 则有限端可见"

课程几何 + 文献量级下的粗估（`k = 167 W/(m·K)`、`d = 12.7 mm`、`L = 0.30 m`），仅用于形成预期：

| `h` (W/m²K) | `m` (1/m) | `1/m` (m) | `mL` | `Θ_tip` | `Bi⊥` |
|---|---|---|---|---|---|
| 5 | 3.07 | 0.33 | 0.92 | 0.69 | 9.5×10⁻⁵ |
| 7 | 3.63 | 0.28 | 1.09 | 0.60 | 1.3×10⁻⁴ |
| 10 | 4.34 | 0.23 | 1.30 | 0.51 | 1.9×10⁻⁴ |

- 预测 A：`Bi⊥ ~ 10⁻⁴ ≪ 1`，一维径向近似成立（`k` 大、`d` 小）。
- 预测 B：`mL ≈ 1`，杆尖仍有基温的 50–70%，半无限近似在 `x ≳ 5 cm` 就超过 5% 误差 → A4 Part 3 应保留有限长解。这也与 Lienhard 的经验阈值（温度需 `mL ≳ 5`）方向一致。

拟合后回来逐条标注"支持 / 不支持 / 无法判断"，并写出剩余无法解释的偏差。

## 9. 提交前总检查

- [ ] Module 6 的 sketch 与 GUI **未被修改**（`git diff` 应为空）。
- [ ] 原始 CSV 未被覆盖；修正只存在于 `*_corrected*` 列/单独文件。
- [ ] 每个图有轴标签与单位；`m` 用 m⁻¹、`1/m` 用 m、`Bi⊥` 与 `ε_T` 无量纲。
- [ ] finite 与 semi-infinite 两套拟合都做了，两套残差都画了，并报告忽略有限端后 `m` 的偏移与拟合不确定度的对比。
- [ ] A4 首页有精确 commit hash；C5 receipt 引用的 hash 与实际 push 一致。

## VS Code agent 指令（现场使用）

> 先读 `docs/module_notes/module_07_lab_day_runbook_2026-10-26.md` 和 `Module_7/README.md`。每次只推进一个未完成的步骤。代码、CSV 列名与串口格式可以直接核对；接线、温度读数、老师批准和装置状态必须由操作者在现场确认。每完成一步就记录数值与证据、勾选该框，并说出下一步的确切操作或读数。不要自行重新接线、给 TEC 通电、提高 PWM、修改安全阈值，也不要让通电运行无人看管。出现异常让操作者切断执行器电源并通知老师。不要把试探性/安全性 CSV 混入正式稳态数据。

References: [Module 7 Part I](https://sethfraden.github.io/Phys39F26-course/labs/theory-bridge-chapter-1/) · [Part II](https://sethfraden.github.io/Phys39F26-course/labs/fin-design-derivation/) · [Part III](https://sethfraden.github.io/Phys39F26-course/labs/lab-08/) · [TEC + rod 模拟器](https://sethfraden.github.io/Phys39F26-course/simulators/tec-rod-control/)

