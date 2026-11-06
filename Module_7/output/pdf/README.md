# A4 PDF version verification

`A4_Zhu.pdf` is the submission artifact. Its first-page hash identifies **source
and calculation inputs only**. It does not claim that the source-only commit
already contains the generated PDF.

`A4_Zhu_build.json` records the source checkpoint, all seven rendering-input
hashes and the generated PDF SHA-256. `A4_Zhu_release.json` separately records
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

To recover this precise PDF, use the `pdf_commit` and `pdf_path` in the release
receipt with `git show <pdf_commit>:<pdf_path>`. Checking out that PDF commit
also provides the same PDF bytes. A checkout of the source-only commit is for
rebuilding the manuscript/calculations and can still contain an older PDF.

For a future revision:

1. Edit the Markdown/calculations/builder as needed, regenerate the figure with
   `a4_theory_checks.py`, and commit those inputs to obtain source commit H.
2. Run `build_a4_pdf.py --prepare`, then `--render --source-ref H` using a Python
   runtime with ReportLab. Review the rendered PDF pages.
3. Commit only the reviewed PDF and build record to obtain PDF commit K.
4. Run `build_a4_pdf.py --record-release --pdf-commit K`, verify the release,
   then commit the new release receipt and push the revision.

Never try to write K inside the PDF that K itself commits: changing those bytes
would require a different commit. The first page and the independent receipt
are complementary provenance records.
