# Analysis scripts

Run from the repository root in order:

```bash
.venv/bin/python Module_6/python/analysis/analyze_model_baseline.py
.venv/bin/python Module_6/python/analysis/analyze_retained_experiments.py
.venv/bin/python Module_6/python/analysis/prepare_a3_evidence.py
```

- analyze_model_baseline.py: Module 4/5 calibration and one-lump work; outputs to data/model_baseline/ and figures/model_baseline/ within Module_6.
- model_baseline_analysis.ipynb: executed notebook companion; the first cell locates the repository root.
- analyze_retained_experiments.py: physical P/PI analysis; outputs to data/experiment_analysis/, figures/experiment_analysis/ and the dated document.
- prepare_a3_evidence.py: six standardized simulations and report assets; outputs to data/a3/ and figures/a3/.
- build_a3_report.py: rebuilds docs/a3_feedback_model.md and output/pdf/A3_Huang_Zhu.pdf from evidence and text in the script. Markdown-only edits are not imported by this builder.
- file_naming.py: shared naming helpers; numerical case IDs stay stable.

The first three scripts use the repository environment (NumPy, Matplotlib). The PDF builder needs ReportLab, Pillow and pypdf; the current PDF uses Codex bundled Python. These scripts never open a serial port. Rebuilding replaces derived outputs, not raw measurements.
