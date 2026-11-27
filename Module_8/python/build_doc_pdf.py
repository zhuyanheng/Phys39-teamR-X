"""Print a self-contained HTML document to PDF with headless Chrome.

The Module_8 docs are hand-authored HTML with an ``@page`` A4 rule and no
external scripts (same pattern as ``f1_study_guide.html`` and
``f1_variables_table.html``), so Chrome's print-to-pdf is the whole pipeline.

Usage
-----
    .venv/bin/python Module_8/python/build_doc_pdf.py \
        Module_8/docs/f1_derivation_kappa_nu.html \
        Module_8/output/pdf/F1_derivation_kappa_nu_Huang.pdf
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

ROOT = pathlib.Path(__file__).resolve().parents[2]


def build(html: pathlib.Path, pdf: pathlib.Path) -> pathlib.Path:
    html = html.resolve()
    pdf = pdf.resolve()
    if not html.is_file():
        raise FileNotFoundError(html)
    pdf.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        CHROME,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf}",
        "--virtual-time-budget=8000",
        html.as_uri(),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if not pdf.is_file() or pdf.stat().st_size == 0:
        raise RuntimeError(
            "chrome did not write a pdf\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return pdf


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    pdf = build(ROOT / argv[1], ROOT / argv[2])
    print(f"{pdf}  ({pdf.stat().st_size / 1024:.0f} kB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
