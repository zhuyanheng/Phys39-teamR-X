# Module 7：铝棒仪器、阶跃响应与稳态肋片

Module 7 把 Module 6 的"一两个温度"模型换成有空间分布的 `T(x, t)`。
三个部分共用一条"预测 → 测量 → 比较 → 判断"的模型检验链：

**要开始动手，先看 [实验日执行清单（S16 → S17 runbook）](../docs/module_notes/module_07_lab_day_runbook_2026-10-26.md)**：
它按依赖顺序排出"先做什么"，本文件是背景与要求汇总。

| 部分 | 核心问题 | 做什么 | 评估 |
|---|---|---|---|
| Part I 热传输基础 | 本构律 + 能量守恒怎么给出温度方程？ | 解释 Fourier 定律、推一维热方程、建立 Biot 判据 | A4 第 1 部分、C5 口试 |
| Part II 有限/无限杆理论 | 轴向导热 + 侧面散热 + 端部条件给出什么稳态剖面？ | 推有限长解、半无限极限、两个模型有效性检验 | A4 第 2–4 部分 |
| Part III 实验 | 这些假设和预测是否描述我们的铝棒？ | 六通道交叉标定、测阶跃响应、测稳态剖面、拟合与残差 | C5、形成性记录、C6 证据 |

三个部分的模型是层层递进的，不是三个独立模型：

- Part I：有 `∂T/∂t`，**无**侧向散热；
- Part II：**无** `∂T/∂t`（稳态），**有**侧向散热；
- Part III：两者都保留 → `ρcA ∂θ/∂t = kA ∂²θ/∂x² − hPθ`。

## 0. 现在的时间线（最紧急）

| 时间 | 事情 |
|---|---|
| S16 周一 10/26（**今天**） | 课上：复习有限杆理论、比较 finite/semi-infinite、算 `Bi⊥`、建传感器地图并标定、开始 baseline 与阶跃测量 |
| S17 周三 10/28 | 课上：完成同步阶跃响应 + 稳态剖面；做 finite 与 semi-infinite 拟合 |
| **周三 10/28 09:05** | **A4 提交**（个人，10 分，Moodle `A4_Lastname.pdf` + 仓库 `docs/assessments/a4_finite_length_biot.md`） |
| **周三 10/28 11:55** | **C5 Moodle receipt** 截止，必须引用已 push 的采集代码与证据 commit |
| 周三 10/28 课上 | C5 现场演示（传感器地图 + 标定 + 同步采集 + baseline/阶跃数据 + 不确定性） |

关键判断：**A4 完全不需要实验数据**（用课程给定的杆参数和传感器位置即可），所以它可以在等器材/等标定时并行完成。C5 才依赖硬件和标定。

## 1. 核心公式速查

记 `θ(x, t) = T(x, t) − T∞`，`T∞` 为远离装置处的室温（不是 TEC 附近读数）。

**通用控制方程（Part III 完整形式）**

```text
ρcA ∂θ/∂t = kA ∂²θ/∂x² − hPθ
∂θ/∂t = α ∂²θ/∂x² − νθ,   α = k/(ρc),   ν = hP/(ρcA)
```

**稳态肋片方程（Part II）**

```text
d²θ/dx² − m²θ = 0,   m² = hP/(kA) = ν/α,   1/m = 衰减长度
```

**有限长 + 绝热端解（Lienhard 4.41）**

```text
Θ(x) = θ(x)/θ(0) = cosh[m(L − x)] / cosh(mL)
Θ_tip = 1/cosh(mL)
```

**半无限极限（4.50）**：`Θ∞(x) = e^(−mx)`，`mL ≫ 1` 时成立。

**有限端误差（A4 第 3 部分的判据）**

```text
ε_T(x) = |Θ_finite(x) − Θ∞(x)| / |Θ_finite(x)|      起始判据 ε_T < 5%
```

**横向 Biot 数（A4 第 4 部分，管半径）**

```text
Bi⊥ = h(A/P)/k = hR/(2k) = (mR/2)² = (md/4)² ≪ 1
```

**平行 Biot 数（长度方向）**

```text
Bi∥ = hPL²/(kA) = (mL)²
```

**边界条件**：`x = 0` 是 Dirichlet（杆热敏电阻 1 实测 `T(0,t)`），`x = L` 是 Neumann 绝热（`dT/dx = 0`）；若端部对流则变 Robin。

**重要概念区别**：`Bi⊥` 检验"每个截面能否用一个温度"（半径方向）；`mL` 与 `ε_T(x)` 检验"远端能否忽略"（长度方向）。**两个结论必须分开写**，不能合并成一句"近似一维"。

**为什么稳态实验分不开 k 和 h**：拟合只得到 `m² = hP/(kA)` 一个组合量。Module 8 的 Ångström 周期实验提供第二个独立测量，才能分开 `k` 与 `h`。


## 2. A4：Finite-Rod Model And Validity Checks（个人，10 分）

- 类型：个人，10 分；截止 **周三 10/28 09:05**。
- Moodle 文件：`A4_Lastname.pdf`；仓库文件：`docs/assessments/a4_finite_length_biot.md`。
- 交一份 PDF + 仓库文件，首页写：姓名、作业号、日期、仓库 URL、**精确 Git commit hash**。
- 全程要写单位与量纲检查。

四个部分（与评分一一对应）：

| 部分 | 内容 | 分值 |
|---|---|---|
| Part 1 | 用 Fourier 定律做 **Lienhard Problem 1.3**（Part I 布置）：展示定律如何得到每个结果、带单位、指出物理上不合理的结果 | 1 |
| Part 2 | 从能量守恒 + Fourier 定律 + Newton 冷却律出发，推稳态肋片方程；按 Lienhard §4.5 推出有限长绝热端解；说明两个边界条件的物理含义 | 3 |
| Part 3 | 用 **Problem 4.12** 取半无限极限；用 **Example 4.8** 与 **Problem 4.20** 量化端部边界条件的近似；对每个课程杆传感器算 `mL` 与 `ε_T(x)`；结论必须写明依赖的传感器位置与误差判据 | 3 |
| Part 4 | 算课程杆的 `Bi⊥`，**单独**给出"每个截面能否用一个温度"的结论（不与 Part 3 的长度结论合并）；再答散热器 vs 航天器辐射器的应用题：哪个能用 Newton 冷却律、太空为何无对流、用什么辐射定律替代（Stefan–Boltzmann `q″ = εσ(T_s⁴ − T_sur⁴)`） | 2 |
| 整体 | 完整、量纲检查、条理清楚、引用精确 Git checkpoint | 1 |

阅读路线：Lienhard 第 1 章选读（能量守恒、热阻、热容、lumped model）+ §4.5 教材 pp. 163–173（要跟着推导走，不只看结论）。

## 3. C5：Rod Instrument And Data-Acquisition Chain（团队）

周三 10/28 课上演示，receipt 11:55 AM 前交，引用已 push 的 commit。要展示：

- 已标定/交叉校核的杆热敏电阻；
- 有记录的传感器坐标与接线；
- 六通道同步记录；
- baseline 与初始阶跃响应数据；
- 文件含时间戳、单位、通道标签、实验备注；
- 每个成员能讲清测量链和**一个主导不确定度**。

## 4. 实验流程（Part 1 → 2 → 3）

**Part 1 传感器地图与交叉标定**

1. 杆材料 6061-T6 铝；量直径 `d`、总长、以及从第一个热敏孔到杆尖的分析长度 `L`；算 `A`、`P`（SI）。
2. 给 6 个热敏电阻命名并固定通道：`A0` = TEC base，`A1`–`A5` = rod 1–5。
3. 同温标定：6 个探头一起放进温水（`20–60 °C`）里缓慢降温 ≥ 60 s，搅拌保持均匀，只浸防水端、接头保持干燥。
4. 以 `tec_C` 为参考，逐通道拟合 `T_TEC = a_i + b_i T_i`，修正 `T_i,corrected = a_i + b_i T_i`。
5. 检查 `ΔT_i = T_i,corrected − T_TEC` 对 `T_TEC`：起始判据是修正后平均差 < `0.2 °C` 且无 > `0.2 °C` 的残余趋势。
6. 原始数据永不覆盖；修正系数单独存文件，分析时再套用。
7. 把 rod 1 装进第一个孔并定义该孔为 `x = 0`；量其余 4 个位置和杆尖（`x = L`），记录每个位置与 `L` 的不确定度；画/拍传感器标签、通道、坐标方向、位置图。

**Part 2 选位置 + 阶跃响应**

1. 先用 `T_set = 45 °C` 做稳态试探（更快但温差小；更高温差大但更慢、漏热多；**不得超过 55 °C**）。
2. 在孔位间移动其余 4 个探头，用 `ln θ` vs `x` 选点：最远点要满足 `0 < θ₅ ≤ θ₁/e`，点要散布在 semilog 图上，不能挤在一端，也不能落进噪声/室温漂移里。
3. 定好位置后不动，记录每个位置与不确定度。
4. 先 `20 °C` 全杆平衡，记录室温与 6 通道，确认通道差异在标定判据内。
5. 用 PI 做 `20 → 45 °C` **非振荡**阶跃，连续记录到满足稳态判据。
6. 所有温度画在同一时间轴，解释为什么越远的探头响应越晚、幅度越小。
7. 保存**指令** TEC 温度、**实测** TEC 温度、以及 **rod 1 实测 `T(0,t)`**（模型边界条件用 rod 1，不是 TEC 指令/热电偶）。

**Part 3 稳态肋片剖面**

1. 开跑前先记录预测的剖面形状和稳态判据（起始判据：所有探头 `|dT_i/dt| < 0.02 °C/min` 持续 ≥ 10 min）。
2. 直接用上面 `20 → 45 °C` 阶跃的最后稳态段，**不需要另做一次加热**。
3. 判据满足后取一段合理区间平均（起始建议 5 min）。
4. 画 `θ` vs `x`（带误差棒），**同时**拟合 finite（cosh）与 semi-infinite（指数），画两套残差，报告 `m`（1/m）与不确定度、`1/m`（m）。
5. 报告忽略有限端后 `m` 变了多少，并与拟合不确定度比较。
6. 讨论传感器位置误差、室温漂移、接触不良、以及端部边界条件的实测证据。
7. 与预测记录对照：哪些假设被支持、哪个模型更合适、剩下什么无法解释的偏差。

## 5. 六通道软件扩展（保留 Module 6 作为可工作的 checkpoint）

**规则**：Module 6 的 Arduino sketch 和 Python GUI **原样不动**，另外复制出 Module 7 版本再改。TEC base 热敏电阻仍然是唯一的反馈与安全传感器；5 个杆通道只做测量，不进入 PI 控制律。

分四个阶段，每阶段跑通再做下一个：

**Stage 1 — Arduino 六通道采集（已实现）**

文件：`Module_7/arduino/module_07_rod_controller/module_07_rod_controller.ino`（Module 6 sketch 的拷贝；命令协议、H 桥引脚、上电 PWM=0、60 °C 软件上限、`!isfinite` 停机逻辑全部保持不变）。

- 通道：`A0` = TEC base（**唯一** PI 反馈与安全输入），`A1`–`A5` = rod 1–5。
- 采样预算：TEC 每周期 1000 次 ADC 平均（与 Module 6 相同），杆通道各 100 次。理由：AVR 一次 `analogRead` 约 112 µs，6 通道各 1000 次要 ~670 ms，会破坏 500 ms 周期并给控制加相位滞后；当前一次完整扫描约 168 ms。
- 杆通道读数落在 `-20…90 °C` 之外就发 `nan` 且不计入 `rod_ok`，但**不**触发执行器停机——松动的杆探头不能中断 40 min 的稳态运行；TEC 通道仍按原规则停机。
- 每周期只发**一条**完整记录，字段顺序固定：

```text
#DATA,time_s,tec_C,rod1_C,rod2_C,rod3_C,rod4_C,rod5_C,pwm,heat_cool,heat_pwm,cool_pwm,limit_C,safety,rod_ok
DATA,12.50,23.41,23.38,23.36,23.34,23.31,23.29,120,1,120,0,60.00,OK,5
```

- 启动时打印 `#firmware`、`#channels`、`#pins`、`#DATA,...` 四条表头；所有表头/诊断行以 `#` 开头，只有以 `DATA,` 开头的行是数据。`heat_pwm`/`cool_pwm` 是固件自报的输出（不能替代对引脚的实测），`limit_C` 是软件上限的现场证据。
- `setpoint_C` 不属于固件（它是 PI 目标），由 Python 追加到 CSV。
- 编译验证（2026-10-26）：`arduino-cli compile --fqbn arduino:avr:uno` → 7844 B flash (24%)、545 B RAM (26%)。

**Stage 2 — Python 显示与原始数据记录（已实现）**

文件：`Module_7/python/module_07_rod_acquisition_gui.py`（Module 6 GUI 的拷贝）+ `Module_7/python/rod_protocol.py`（Qt-free 解析器）+ `Module_7/run_rod_acquisition.command`。

- `PIController` 直接从 `Module_6/python/` 导入，**不复制**控制律——与 Module 6 复用 Module 5 `parse_measurement` 是同一做法，控制算术只有一份实现。
- 解析器与固件表头由 `Module_7/python/test_rod_protocol.py` 交叉校验（19 个测试，`python3 Module_7/python/test_rod_protocol.py`，无需 Qt/串口/Arduino）。
- CSV：`Module_7/data/raw/module_07_rod_<时间戳>.csv`。前 14 个测量列与 `DATA` 行**同名同序**（`time_s, tec_C, rod1_C, rod2_C, rod3_C, rod4_C, rod5_C, pwm, heat_cool, heat_pwm, cool_pwm, limit_C, safety, rod_ok`，由 `rod_protocol.py` 生成，手改列名会让测试失败），其后追加控制列（`setpoint_C`、`error_C`、`p_term_pwm`、`i_term_pwm`、`sent_signed_pwm`…），所以一行 CSV 仍然能解释当时的执行器命令。
- 4 张图：6 通道温度 + 设定值（TEC 加粗、每通道固定颜色）、signed PWM、P/I 项、误差。默认窗口 900 s，可勾 `Show whole run`——杆的响应是几十分钟量级，Module 6 的 180 s 窗口不够用。
- 坏行跳过不崩并计数（`rows ok/bad`）；`#` 开头的行不计为坏行；`'x'` 模式打开文件，绝不覆盖；每行 flush。
- `Mark event` 按钮把带说明的事件写进 CSV（稳态判定、移动探头、标定开始等）。
- 端到端验证（2026-10-26，`QT_QPA_PLATFORM=offscreen` + 假串口）：表头/坏行被忽略、20 行 CSV 落盘（含 `connect`/`stop`/`operator_mark` 事件行）、25→45 °C 阶跃发出 `SET PWM … DIR HEAT`、杆通道 `nan` **不**停机、`SHUTDOWN` 与 TEC 46 °C 都会停机——均已通过。

运行方式（需要项目 `.venv`，已按 `requirements.txt` 装好 `PySide6`/`pyqtgraph`/`pyserial`）：

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # 只需一次
Module_7/run_rod_acquisition.command --preview   # 不碰串口，检查界面
Module_7/run_rod_acquisition.command             # 实测：选端口 → Connect (PWM 0) → Start P / PI
```

上机第一次通电的每一步见 [Step 1 现场操作单](../docs/module_notes/module_07_step1_integration_check.md)（接线图、每个温度对应的期望电压、逐通道指纹表、故障注入、排查表）。

**Stage 3 — 相对标定分析（独立脚本）**

```bash
.venv/bin/python Module_7/python/analysis/module_07_calibration.py \
    Module_7/data/raw/module_07_rod_20261026_141500_123456.csv      # 不给文件则取 raw/ 里最新的一份
```

- 只读原始 CSV（`raw/` 里的文件字节不变，有测试守着），逐杆通道拟合 `T_TEC = a_i + b_i T_i`，默认只用 `event=measurement` 且 `tec_C`/该杆通道都有限的 240 行级别样本。
- 画 `T_i` vs `T_TEC`（含 identity 线与拟合线）和修正后残差 `(a_i + b_i T_i) − T_TEC` vs `T_TEC`，图写到 `figures/calibration/<raw 文件名>_fit.png`。
- 输出标定表到 `data/calibration/module_07_calibration_<raw 文件名>.csv`：通道、`a_i`、`b_i`、点数、温度范围、残差均值/标准差/最大绝对值、`before`（未修正前平均偏差）、三项判据与总判定。
- 另存"原始列 + `rod1_corrected_C`…`rod5_corrected_C`"到 `data/calibration/<raw 文件名>_corrected.csv`，原始列不改；`nan` 在修正列里仍是 `nan`。
- 判据（与 runbook 一致，可用 `--criterion-*` 改）：`|残差均值| ≤ 0.2 °C`、`残差曲率 ≤ 0.2 °C`、`max|残差| ≤ 0.2 °C`。任一通道不达标时退出码为 2，并提示重做浸泡。
- **判据的正确读法**：拟合带截距，所以残差均值按构造恒为 0（它只是"截距解对了"的自检）；残差的**直线倾斜**也被 `b` 吃掉，所以"趋势"用**曲率**（中间半段均值 − 两端四分之一均值）来量；真正判别探头滞后/失去接触的是 `max|残差|` 与曲率两项。
- 参考本身是未标定的 A0 探头（β=4540 K 标称值，β 差 1 % ≈ 0.6 °C），所以它做的是**相对一致性**标定，不是绝对精度标定——这一点必须写进报告。

**Stage 4 — 标定前集成检查**

- 单独加热一个探头，确认只有它对应的 Arduino 与 Python 通道变化；
- 核对"一条 DATA 行 = 一组显示值 = 一行 CSV"；
- 拔掉一个杆探头，确认故障可见且**不破坏** TEC base 的安全停机；
- 重启两程序，确认 PWM 从 0 开始且新建数据文件；
- 把 sketch/GUI/标定脚本文件名与 commit hash 写进传感器地图。

## 6. 预测记录（开加热前必须先写下来）

必须记录的内容：

1. 各探头响应先后顺序；
2. 响应幅度随距离如何变化；
3. 稳态剖面定性形状；
4. 测量区间是否应看到有限端。

下面是**用课程给定几何 + 文献量级做的粗估**，用来先形成预期；拿到实测 `d`、`L`、位置和 `m` 后必须替换。

假设：6061-T6 `k ≈ 167 W/(m·K)`，`d = 12.7 mm`，自然对流 `h = 5–10 W/(m²·K)`，`L = 0.30 m`（**待实测**）。

| `h` (W/m²K) | `m` (1/m) | `1/m` (m) | `mL` | `Θ_tip` | `Bi⊥` |
|---|---|---|---|---|---|
| 5 | 3.07 | 0.326 | 0.92 | 0.69 | 9.5×10⁻⁵ |
| 7 | 3.63 | 0.275 | 1.09 | 0.60 | 1.3×10⁻⁴ |
| 10 | 4.34 | 0.230 | 1.30 | 0.51 | 1.9×10⁻⁴ |

对应有限端误差 `ε_T(x)`（同一假设下）：

| `x` (m) | 0.05 | 0.10 | 0.15 | 0.20 | 0.25 |
|---|---|---|---|---|---|
| `ε_T` (h=5) | 4.7% | 10% | 17% | 25% | 33% |
| `ε_T` (h=7) | 4.3% | 9.8% | 17% | 25% | 34% |
| `ε_T` (h=10) | 3.6% | 8.7% | 16% | 24% | 35% |

由此得到两个**可检验**的预判：

- `Bi⊥ ~ 10⁻⁴ ≪ 1`：一维径向近似几乎肯定成立（`k` 大、`d` 小）。
- `mL ~ 1`，杆尖仍有基温的 50–70%：**半无限近似在 `x ≳ 5 cm` 就不满足 5% 判据**，A4 第 3 部分应保留有限长 cosh 解，并明确写出"结论依赖传感器位置与判据"。这与 Lienhard 的经验阈值（温度用 `mL ≳ 5`、基热流用 `mL ≳ 3`）一致地指向"有限端不可忽略"。

## 7. 目录与命名约定

沿用 Module 4–6 的仓库习惯（小写+下划线，小数点写 `p`），并满足课程要求的证据文件路径：

```text
Module_7/
├── README.md                                     本文件
├── run_rod_acquisition.command                   Stage 2 启动脚本（可加 --preview）
├── arduino/
│   └── module_07_rod_controller/
│       └── module_07_rod_controller.ino          Stage 1（Module 6 sketch 的拷贝）
├── python/
│   ├── module_07_rod_acquisition_gui.py          Stage 2（Module 6 GUI 的拷贝）
│   ├── rod_protocol.py                           串口格式与解析（Qt-free，可单测）
│   ├── test_rod_protocol.py                      19 个无硬件测试
│   ├── test_module_07_calibration.py             24 个无硬件测试（合成六通道数据）
│   └── analysis/
│       ├── module_07_calibration.py              Stage 3 交叉标定（标准库即可；图需 matplotlib）
│       └── module_07_stationary_fin_fit.py       Part 3 finite/semi-infinite 拟合（待写）
├── data/
│   ├── raw/                                      原始 CSV（永不覆盖）
│   ├── calibration/                              标定系数表 + 修正数据 CSV（Stage 3 写入）
│   ├── processed/                                拟合结果（Part 3 建）
│   └── README.md                                 数据目录规则
├── figures/                                      Part 1–3 的图（脚本运行时生成）
├── docs/
│   └── README.md                                 文档索引
```

课程额外要求的证据文件（放 `docs/module_notes/`，与 Module 1–5 的笔记一致）：

- `docs/module_notes/module_07_rod_instrument.md` — 传感器地图、标定记录、几何、baseline/阶跃、运行元数据
- `docs/module_notes/module_07_stationary_fin.md` — 形成性稳态肋片分析（C6 与最终展示的证据）
- `docs/assessments/a4_finite_length_biot.md` — A4 的四部分正文

## 8. 行动清单（按优先级）

**P0 — 今天/明天必须完成（A4 不依赖数据）**

- [ ] 读 Lienhard §4.5（pp. 163–173）+ 跟着 `fin-design-derivation` 走完 (4.27)–(4.51)
- [ ] Lienhard Problem 1.3（A4 Part 1）
- [ ] 稳态肋片方程 + 绝热端 cosh 解两边界条件推导（A4 Part 2）
- [ ] Problem 4.12 / Example 4.8 / Problem 4.20 + 逐传感器 `mL`、`ε_T(x)`（A4 Part 3）
- [ ] `Bi⊥` 计算 + 半径结论 + 散热器/辐射器应用题（A4 Part 4）
- [ ] 写成 `docs/assessments/a4_finite_length_biot.md` 并导出 `A4_Lastname.pdf`，首页写 commit hash

**P1 — S16 课上**

- [ ] 量 `d`、总长、`L`、孔位并记录不确定度
- [ ] 六探头同温标定（≥ 60 s）
- [ ] Stage 1 + Stage 2 改好并做 Stage 4 集成检查
- [ ] baseline 与首次阶跃数据落盘

**P2 — S17 课上 + 截止前**

- [ ] 定 5 个杆探头位置（`θ₅ ≤ θ₁/e`）
- [ ] 完成 `20 → 45 °C` 阶跃到稳态
- [ ] finite/semi-infinite 双拟合 + 残差
- [ ] 写 `module_07_rod_instrument.md`、`module_07_stationary_fin.md`
- [ ] C5 演示 + 11:55 前交 receipt（引用已 push 的 commit）

**建议分工（两人）**：A4 的四部分各自独立完成（个人作业），但可以互相校对量纲与边界条件；S16/S17 现场一人管硬件与标定、一人管软件与数据落盘，交换复核。

## 9. 参考链接

- [Module 7 Part I：Thermal Transport Foundations](https://sethfraden.github.io/Phys39F26-course/labs/theory-bridge-chapter-1/)
- [Module 7 Part II：Finite And Infinite Rod Theory (fin-design-derivation)](https://sethfraden.github.io/Phys39F26-course/labs/fin-design-derivation/)
- [Module 7 Part III：Rod Instrument, Step Response, And Stationary Fin](https://sethfraden.github.io/Phys39F26-course/labs/lab-08/)
- [TEC + finite-rod 模拟器](https://sethfraden.github.io/Phys39F26-course/simulators/tec-rod-control/)
- [Lienhard & Lienhard, A Heat Transfer Textbook](https://sethfraden.github.io/Phys39F26-course/references/lienhard-heat-transfer-v6.pdf)

## 模拟器要点（S16 之前可先玩）

- 杆被分成 24–100 个有限差分单元，`0.01 s` 子步长推进；控制器每 `0.1 s` 更新。
- 端部**零热流**；驱动端接一个动态 TEC（冷面 `T_c`、热面 `T_h`、`C_c = 12 J/K`、`C_h = 180 J/K`、`S = 0.0513 V/K`、`R = 1.861 Ω`、`K_TEC = 0.560 W/K`、`R_hs = 0.55 K/W`、12 V）。
- 热敏电阻有 2 s 一阶响应；PWM 限幅 ±100%。
- 高增益练习：探针放 `x = 0`、纯 P，`Kp = 8 → 80 → 800`，找出"单调 → 衰减振荡 → 持续振荡"的转变点，并观察 PWM 是否大部分时间顶在限幅（bang-bang）。
- 固定 `Kp = 800`，把探针沿杆后移：振荡**变慢**（反馈用到了更旧、更弱的信号）。
- 这个振荡来自 TEC 双态执行器 + 分布扩散 + 传感器 + 采样累积的相位滞后，**一维 one-lump P 模型给不出来**——这是 Module 7 相较 Module 6 的关键新增物理。

