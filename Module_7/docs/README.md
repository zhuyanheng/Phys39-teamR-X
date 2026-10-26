# Module 7 文档索引

`Module_7/` 内部只放**这个模块自己的**产物；课程要求的证据笔记按仓库惯例统一放在仓库根的
`docs/`（与 Module 1–6 一致），不在这里重复。

## 本目录

| 文件 | 内容 |
| --- | --- |
| `README.md`（本文件） | Module 7 的文档索引：哪些文档在仓库根 `docs/`、图与数据从哪来 |
| `../README.md` | Module 7 实验设计、六个部件、预测记录、软件扩展方案 |

## 仓库根 `docs/` 中与 Module 7 相关的证据

| 文件 | 内容 | 状态 |
| --- | --- | --- |
| `docs/module_notes/module_07_lab_day_runbook_2026-10-26.md` | 实验日步骤：软件 → 几何 → 标定 → 阶跃 → 稳态 | 已有 |
| `docs/module_notes/module_07_rod_instrument.md` | 传感器地图、标定记录、几何、baseline/阶跃、运行元数据 | 待写（做完 Part 2 后填） |
| `docs/module_notes/module_07_stationary_fin.md` | 形成性稳态肋片分析 | 待写（Part 3 之后） |
| `docs/assessments/a4_finite_length_biot.md` | A4 四部分正文 | 已有 |

## 图

`Module_7/figures/` 由分析脚本写入，文件名与报告里的图号一一对应：

- `part_01_sensor_map.png` — 杆几何、孔位、探头编号
- `part_02_step_response.png` — 6 通道阶跃响应（含标定后修正曲线）
- `part_03_stationary_profile.png` — 稳态剖面 + finite/semi-infinite 拟合与残差

图里出现的数字必须能在 `Module_7/data/processed/` 的拟合结果里找到，反之亦然。
