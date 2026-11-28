# Module 8 documentation index

| File | Purpose |
| --- | --- |
| `../README.md` | Module structure, programs, status, output locations and deadlines |
| `theory_and_analysis.md` | Periodic derivation, offline fitting/viewer, reproduction and uncertainty limits |
| `f1_derivation_kappa_nu.html` | Why the rod balance is divided by rho*c*A: slice energy balance → kappa = k/(rho c) and nu = hP/(rho c A) → s² = (nu + i omega)/kappa → kappa = omega/(2qq'); prints to `../output/pdf/F1_derivation_kappa_nu_Huang.pdf` |
| `q10_steady_state_derivation.html` | Q10: why a steady state cannot give k. Sets d(theta)/dt = 0 → single number m (so only h/k is observable), shows steady state is the omega→0 limit where the phase observable vanishes, and quantifies the room-reference sensitivity; prints to `../output/pdf/Q10_steady_state_derivation_Huang.pdf` |
| `serial_protocol.md` | Commands, schema, events, timing and safety state |
| `transport_and_model_note_2026-11-18.md` | k/h conversion with sourced constants, conditioning and drift systematics, mean-profile cross-route, measured actuator response, remaining measurements |
| `verification.json` | Current software verification and build results |
| `source_manifest.json` | Original copied files and their source SHA-256 hashes |
| `../../docs/module_notes/module_08_angstrom.md` | Current setup and experimental evidence status |
| `../../docs/module_notes/module_08_lab_day_runbook_2026-11-04.md` | Ordered trials and acceptance gates |
| `../../docs/module_notes/module_08_modeling_app.md` | Implemented offline analysis and remaining experimental requirements |

Course evidence remains in repository-root `docs/`, consistent with Modules 1–7.

## Rebuilding the printed notes

The HTML files are self-contained (A4 `@page` rule, no external scripts). Figures and the PDF are regenerated from the repository root with:

```sh
.venv/bin/python Module_8/python/derivation_figures.py
.venv/bin/python Module_8/python/build_doc_pdf.py \
    Module_8/docs/f1_derivation_kappa_nu.html \
    Module_8/output/pdf/F1_derivation_kappa_nu_Huang.pdf
```

`build_doc_pdf.py` prints any self-contained HTML to PDF with headless Chrome; the same command works for `f1_study_guide.html`, `f1_oral_answers.html`, `f1_variables_table.html` and `q10_steady_state_derivation.html`.

The Q10 note draws its own three figures (degeneracy line, room-reference sensitivity, d.c. limit) with a separate script:

```sh
.venv/bin/python Module_8/python/q10_figures.py
```
