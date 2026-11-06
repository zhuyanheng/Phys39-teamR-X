# A4 PDF version verification

`A4_Zhu.pdf` is the submission artifact. Its first-page hash identifies **source
and calculation inputs only**. It does not claim that the source-only commit
already contains the generated PDF.

`A4_Zhu_build.json` records the source checkpoint, six manuscript/code/numerical
input hashes, the PNG bytes used during rendering, and the generated PDF SHA-256.
`A4_Zhu_release.json` separately records
the exact commit containing the delivered PDF and build record. The release
receipt is committed afterward, avoiding a self-referential PDF/commit hash.

Verify the working copy and both historical versions from the repository root:

```bash
.venv/bin/python Module_7/python/analysis/build_a4_pdf.py --verify-release
```

The verifier checks the local source/calculation inputs against their cited
commit, checks the delivered PDF bytes against the exact PDF commit, checks the
build-record bytes and all SHA-256 values, and checks that the source commit is
an ancestor of the PDF commit. No experimental data or hardware is accessed.

Re-running the calculation command printed in the PDF also regenerates the PNG.
Its bytes can vary with Matplotlib and font versions even when the numerical
results are unchanged. The PNG is a generated asset, excluded from the six
source-input checks; its build-record checksum describes the image used when
that PDF was rendered, not a requirement on a newly generated working copy.
The exact release figure is preserved inside the committed PDF. Recomputing the
tables and figure must not require changing the receipt or rebuilding the PDF
merely because raster bytes differ. Changed numerical results or code still
fail source verification.

To recover this precise PDF, use the `pdf_commit` and `pdf_path` in the release
receipt with `git show <pdf_commit>:<pdf_path>`. Checking out that PDF commit
also provides the same PDF bytes. A checkout of the source-only commit is for
rebuilding the manuscript/calculations and can still contain an older PDF.

For a future revision:

Install rendering dependencies into the project environment if needed:

```bash
.venv/bin/python -m pip install matplotlib Pillow reportlab
```

1. Edit the Markdown/calculations/builder as needed, regenerate the figure with
   `a4_theory_checks.py`, and commit those inputs to obtain source commit H.
2. Run `build_a4_pdf.py --prepare`, then `--render --source-ref H` using a Python
   runtime with ReportLab and Pillow. Review the rendered PDF pages.
3. Commit only the reviewed PDF and build record to obtain PDF commit K.
4. Run `build_a4_pdf.py --record-release --pdf-commit K`, verify the release,
   then commit the new release receipt. Push when publication is authorized.

Never try to write K inside the PDF that K itself commits: changing those bytes
would require a different commit. The first page and the independent receipt
are complementary provenance records.
