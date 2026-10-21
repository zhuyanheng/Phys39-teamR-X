# Module 6 图片索引

| 目录 | 内容 |
|---|---|
| [gui/one_lump/](gui/one_lump/) | 早期手动保存的 one-lump 截图 |
| [gui/two_lump/](gui/two_lump/) | 六组 two-lump GUI 截图 |
| [model_baseline/](model_baseline/) | 编号01–07的历史标定、P droop、one-lump 与 windup 图 |
| [experiment_analysis/](experiment_analysis/) | 当前六组实测温度、PWM、P / I 贡献与误差详细图 |
| [a3/](a3/) | 当前报告六张实测和六张数值模拟曲线图；equations/ 为公式图片 |

p / pi 表示模式，kp / ki 表示增益；0p1表示0.1。exp_表示实测，sim_two_lump_表示数值模拟。GUI截图由目录表明模型。

PNG 用于查看，SVG 用于矢量排版，两者不作为重复文件删除。

当前 P 实测与模拟均为 Kp=0.25、4、100；PI 均为 Kp=20，Ki=0.1、0.2、0.5。旧 Kp=250 实测图只保留在历史归档，不参与当前 A3。

- [当前 P 升降温对照](experiment_analysis/p_aligned_comparison.png)
- [当前 PI 升降温对照](experiment_analysis/pi_aligned_comparison.png)
- [当前高增益 P 报告图](a3/exp_p_kp_100.png)

GUI 截图保存操作时界面，`a3/sim_two_lump_*.png` 是统一时序重新计算的模型曲线，不能混称为同一次记录。
