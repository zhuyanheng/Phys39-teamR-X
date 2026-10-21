# Analysis scripts

## Recompute the current A3 evidence

Run from the repository root with the existing analysis environment. On a new checkout, follow the [environment setup](../../README.md#首次配置环境) first:

```bash
.venv/bin/python Module_6/python/analysis/analyze_retained_experiments.py
.venv/bin/python Module_6/python/analysis/prepare_a3_evidence.py
```

- analyze_model_baseline.py: optional historical Module 4/5 baseline (not the current A3 P source); outputs to data/model_baseline/ and figures/model_baseline/ within Module_6.
- model_baseline_analysis.ipynb: executed notebook companion; the first cell locates the repository root.
- analyze_retained_experiments.py: current Module 6-only P/PI analysis; outputs to data/experiment_analysis/, figures/experiment_analysis/ and the dated document.
- prepare_a3_evidence.py: six standardized simulations and report assets; outputs to data/a3/ and figures/a3/.
- build_a3_report.py: rebuilds docs/a3_feedback_model.md and output/pdf/A3_Huang_Zhu.pdf from evidence and text in the script. Markdown-only edits are not imported by this builder.
- file_naming.py: shared naming helpers; numerical case IDs stay stable.

The numerical scripts use the repository environment (NumPy, Matplotlib). Current A3 P inputs are exclusively the 21 October Module 6 files; retained PI inputs are from 19 October. The optional historical baseline script is not a prerequisite when its calibration summaries are already present.

## Build the PDF

The builder needs ReportLab, Pillow and pypdf in the Python environment used to run it. For example, if using the repository environment:

```bash
.venv/bin/python -m pip install reportlab pillow pypdf
.venv/bin/python Module_6/python/analysis/build_a3_report.py
```

The current PDF was generated with the Codex bundled Python containing those packages. The builder currently uses macOS Arial font files under `/System/Library/Fonts/Supplemental`; a different platform requires a suitable font path in the script.

Outputs are [A3 Markdown](../../docs/a3_feedback_model.md) and [A3 PDF](../../output/pdf/A3_Huang_Zhu.pdf). Report paragraphs are authored in `build_a3_report.py`; rebuilding overwrites the generated Markdown, so Markdown-only edits are not automatically retained. The numerical scripts do not alter raw measurements, and none of these analysis scripts opens a serial port.

## Validation and history

- [Current raw-data selection and rename hashes](../../docs/new_p_data_selection_2026-10-21.json)
- [Current calculation and PDF checks](../../data/a3/new_p_validation.json)
- [Superseded report](../../archive/2026-10-21_pre_new_p/README.md)

Simulation source settings and input hashes are in `Module_6/data/a3/provenance.json`. Model-generated CSVs are not physical measurements.
