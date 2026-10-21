# Module 6 数据索引

| 文件夹 | 内容 | 生成脚本 |
|---|---|---|
| [physical/](physical/README.md) | 10月19日三组原始实物 PI CSV | 实物 GUI；按 CSV 内 run_id 筛选 |
| experiment_analysis/ | step_metrics.csv、analysis_results.json：实测指标和输入 SHA256 | analyze_retained_experiments.py |
| model_baseline/ | 标定、时间常数、P droop、one-lump 模拟 | analyze_model_baseline.py |
| a3/ | 标准化 two-lump CSV、稳定性、步长和报告验证 | prepare_a3_evidence.py、build_a3_report.py |

## model_baseline

- susceptibility.csv、time_constants.csv：Module 4 暂定标定及端点敏感性，不是置信区间。
- p_droop_comparison.csv、open_loop_comparison.csv：Module 4 / 5 与模型比较。
- sim_one_lump_p.csv、sim_one_lump_pi_overdamped.csv、sim_one_lump_pi_underdamped.csv：数学模拟，不是实物数据。
- simulation_metrics.csv、windup_comparison.csv、numerical_checks.csv：模拟指标与检查。
- analysis_results.json：精确设置、来源和校验。H=1 是归一化，不是独立实测值。

## a3

- sim_two_lump_p_kp_*.csv、sim_two_lump_pi_kp_20_ki_*.csv：新计算的标准化模型数据，不是从截图提取的轨迹。
- simulation_step_metrics.csv：升降温指标。
- shared_model.json、stability.json：共同参数、阻尼、临界增益与 PI 稳定性。
- timestep_checks.csv：0.05 / 0.025秒比较。
- provenance.json：来源 SHA256；pdf_build_check.json、validation_note.txt：验证记录。

Module 5 的 P 原始数据仍在 `../../Module_5/data/`，本模块只读取。
