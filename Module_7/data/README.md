# Module 7 数据目录约定

只放**测量到的东西**，不放推出来的东西。三个子目录互不覆盖：

| 目录 | 内容 | 由谁写 |
| --- | --- | --- |
| `raw/` | GUI 直接落盘的原始 CSV，文件名 `module_07_rod_<YYYYmmdd_HHMMSS_微秒>.csv` | `module_07_rod_acquisition_gui.py`（`'x'` 模式，绝不覆盖） |
| `calibration/` | 交叉标定系数表（`a_i`、`b_i`、温度范围、残差统计）+ 修正后的数据 CSV | `python/analysis/module_07_calibration.py` |
| `processed/` | 稳态剖面、阶跃响应的拟合结果（`m`、`1/m`、`χ²`、判据表） | `python/analysis/module_07_stationary_fin_fit.py` |

规则：

1. **原始列永不改写。** 修正值另存为 `rod1_corrected_C`…`rod5_corrected_C` 新列或新文件，并写明用的是哪一版标定表。
2. `raw/` 里的每个文件都对应一次真实运行；不要手工编辑、合并或"清理"它们。
3. 每个 CSV 的第一行就是列名，前 14 个测量列与固件 `DATA` 行同名同序（见 `Module_7/python/rod_protocol.py`）；`event` 列区分 `measurement`、`start`、`stop`、`setpoint_step`、`operator_mark`、`connect`、`disconnect`。
4. 分析脚本只读 `raw/`，输出只能写到 `calibration/` 或 `processed/`。
5. 提交进 Git 的应当是"能支撑报告结论的那几条"运行（连同 `docs/module_notes/module_07_rod_instrument.md` 里的运行元数据），不是全部原始数据。
