# Module 6：P / PI 温度控制与热模型

## 常用入口

- [A3 最终 PDF](output/pdf/A3_Huang_Zhu.pdf)
- [A3 可编辑英文报告](docs/a3_feedback_model.md)
- [实验数据分析](docs/experiment_analysis_2026-10-21.md)
- [P 三组对照图](figures/experiment_analysis/p_aligned_comparison.png)
- [PI 三组对照图](figures/experiment_analysis/pi_aligned_comparison.png)
- [实物控制程序说明](docs/pi_controller_guide_zh.md)
- [数据说明](data/README.md)、[图片说明](figures/README.md)、[文档索引](docs/README.md)

## 目录结构

```text
Module_6/
├── run_gui.command                  数学模拟器入口
├── run_pi_control.command           实物 P / PI 控制入口
├── arduino/                         Arduino sketch 与说明
├── python/                          老师程序、控制器、测试
│   └── analysis/                    分析、绘图、报告脚本及 notebook
├── data/
│   ├── physical/                    原始实物 CSV
│   ├── experiment_analysis/         实测指标与来源校验
│   ├── model_baseline/              标定、one-lump 基础分析
│   └── a3/                          标准化 two-lump 模拟与验证
├── figures/
│   ├── gui/one_lump/                手动保存的 one-lump 截图
│   ├── gui/two_lump/                手动保存的六组 two-lump 截图
│   ├── model_baseline/              基础分析图
│   ├── experiment_analysis/         实测详细图
│   └── a3/                          报告用图及公式
├── archive/                         被新P数据替代的旧报告与图
├── docs/                            报告、方法、实验记录、整理清单
└── output/pdf/                      A3_Huang_Zhu.pdf
```

`.venv/` 是模拟器本地 Python / Tk 环境，不是提交数据，不要移动。Module 4、5 原始数据仍在原文件夹；当前A3仅使用Module 4标定与本模块六组实测，旧Module 5 P不再作为A3证据。

## 命名约定

常规文件用小写与下划线；小数点写成 `p`，例如 `0p25` 表示0.25。

- 实测图：`exp_pi_kp_20_ki_0p2.png`。
- 模拟图与数据：`sim_two_lump_pi_kp_20_ki_0p2.png/.csv`。
- GUI 截图由目录表明模型：`figures/gui/two_lump/p_kp_100.png`。
- 已归档实物 CSV 写明增益并保留原时间戳。新采集仍按连接时间命名，因为一次连接可能包含多组设置；以 CSV 内参数和 `run_id` 为准。
- 老师程序保留 `Lab_6_7_modeling_tec_v3.py` 原名；Arduino sketch 保持同名目录与 `.ino`；最终 PDF 保留课程要求的姓名格式。
- 改名前后路径与原始 SHA256 见[整理清单](docs/file_organization_2026-10-21.json)。原始实物 CSV、截图内容不因整理改变。
- 10月21日新增 P 的改名与来源校验另见[新 P 数据清单](docs/new_p_data_selection_2026-10-21.json)。

## 首次配置环境

在项目根目录执行。已有可用环境时跳过本节，不必重新创建。`.venv/` 不随 Git 分发，新克隆的仓库需要自行配置环境。

实物控制与分析环境：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt -r Module_6/python/analysis/requirements.txt
```

数学模拟器使用单独环境。以下命令需要已安装、带 Tk 的 Python 3.12；本机验证环境为 Python 3.12 / Tk 9.0.4，系统旧 Tk 8.5 不适用：

```bash
python3.12 -m venv Module_6/.venv
Module_6/.venv/bin/python -m pip install -r Module_6/python/requirements-gui.txt
```

PDF 生成另外需要 ReportLab、Pillow 和 pypdf，见[分析脚本说明](python/analysis/README.md#build-the-pdf)。

## 启动和复算

从项目根目录执行，也可双击两个启动文件：

```bash
./Module_6/run_gui.command
./Module_6/run_pi_control.command
```

模拟器使用 `Module_6/.venv`，实物界面与分析使用项目根目录 `.venv`。老师程序保留启动兼容修补；本次整理未改变数学方程、增益或保护逻辑。固件见[arduino/README.md](arduino/README.md)。

```bash
.venv/bin/python Module_6/python/analysis/analyze_retained_experiments.py
.venv/bin/python Module_6/python/analysis/prepare_a3_evidence.py
```

最后用装有 ReportLab、Pillow、pypdf 的 Python 运行 `Module_6/python/analysis/build_a3_report.py`，更新 PDF 和 Markdown。详见[脚本说明](python/analysis/README.md)。这些分析脚本不连接硬件。`analyze_model_baseline.py` 保留为历史基础分析（其中包括旧 Module 5 P），不必为了更新当前 A3 运行它。

## 当前结果与提交

Module 6 的数据整理、实验分析、六组模拟和 A3 报告已按现有数据完成。当前证据为：

| 模式 | 日期 | 增益 | 目标与 PWM 上限 |
|---|---|---|---|
| P | 2026-10-21 | Kp=0.25、4、100；Ki=0 | 20→30→20°C，255 |
| PI | 2026-10-19 | Kp=20；Ki=0.1、0.2、0.5 | 20→30→20°C，255 |

A3 不再使用 Module 5 P 数据；当前 P 的增益与模拟一致。数据定义、观测时长及模型假设详见报告。基础模型 H=1 是任意归一化，A3 常数以假设电压、电阻推导，二者用途不同。

当前报告在 `output/pdf/A3_Huang_Zhu.pdf`，被替代的旧报告在 [archive/](archive/2026-10-21_pre_new_p/README.md)。GitHub checkpoint 和每位组员的 Moodle 上传单独完成；本说明不声称已提交。
