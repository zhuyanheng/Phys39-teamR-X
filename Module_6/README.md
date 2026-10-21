# Module 6：P / PI 温度控制与热模型

## 常用入口

- [A3 最终 PDF](output/pdf/A3_Huang_Zhu.pdf)
- [A3 可编辑英文报告](docs/a3_feedback_model.md)
- [实验数据分析](docs/experiment_analysis_2026-10-19.md)
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
├── docs/                            报告、方法、实验记录、整理清单
└── output/pdf/                      A3_Huang_Zhu.pdf
```

`.venv/` 是模拟器本地 Python / Tk 环境，不是提交数据，不要移动。Module 4、5 原始数据仍在原文件夹，本模块会读取。

## 命名约定

常规文件用小写与下划线；小数点写成 `p`，例如 `0p25` 表示0.25。

- 实测图：`exp_pi_kp_20_ki_0p2.png`。
- 模拟图与数据：`sim_two_lump_pi_kp_20_ki_0p2.png/.csv`。
- GUI 截图由目录表明模型：`figures/gui/two_lump/p_kp_100.png`。
- 已归档实物 CSV 写明增益并保留原时间戳。新采集仍按连接时间命名，因为一次连接可能包含多组设置；以 CSV 内参数和 `run_id` 为准。
- 老师程序保留 `Lab_6_7_modeling_tec_v3.py` 原名；Arduino sketch 保持同名目录与 `.ino`；最终 PDF 保留课程要求的姓名格式。
- 改名前后路径与原始 SHA256 见[整理清单](docs/file_organization_2026-10-21.json)。原始实物 CSV、截图内容不因整理改变。

## 启动和复算

从项目根目录执行，也可双击两个启动文件：

```bash
./Module_6/run_gui.command
./Module_6/run_pi_control.command
```

模拟器使用 `Module_6/.venv`，实物界面与分析使用项目根目录 `.venv`。老师程序保留启动兼容修补；本次整理未改变数学方程、增益或保护逻辑。固件见[arduino/README.md](arduino/README.md)。

```bash
.venv/bin/python Module_6/python/analysis/analyze_model_baseline.py
.venv/bin/python Module_6/python/analysis/analyze_retained_experiments.py
.venv/bin/python Module_6/python/analysis/prepare_a3_evidence.py
```

最后用装有 ReportLab、Pillow、pypdf 的 Python 运行 `Module_6/python/analysis/build_a3_report.py`，更新 PDF 和 Markdown。详见[脚本说明](python/analysis/README.md)。这些分析脚本不连接硬件。

## 当前状态与限制

A3 包含问题1–5、六组实测图和六组标准化模拟图。历史 P 缺少降温，高增益实物250与模拟100不同，PI 的 Kp=20 与历史稳定 P 示例4也不匹配；这些限制已写入报告，不能声称严格满足完整匹配协议。

标定仍是暂定结果；基础模型 H=1 是任意归一化，A3 常数则以假设电压、电阻推导，二者不应混用。提交前仍需团队审阅、GitHub checkpoint 和 Moodle 上传；本次整理未代为提交。
