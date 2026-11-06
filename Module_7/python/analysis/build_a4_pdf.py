"""Build the A4 PDF from its reviewed Markdown source.

1. .venv/bin/python Module_7/python/analysis/build_a4_pdf.py --prepare
2. Commit the manuscript, calculations, figure and builder to obtain source H.
3. A Python with reportlab and Pillow: build_a4_pdf.py --render --source-ref H
4. Review and commit the PDF/build record to obtain artifact commit K.
5. build_a4_pdf.py --record-release --pdf-commit K, then commit that receipt.
6. build_a4_pdf.py --verify-release

Preparation renders mathematical notation with matplotlib; rendering uses
ReportLab. Neither step alters the paper source or experimental raw files.
"""
import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "docs/assessments/a4_finite_length_biot.md"
BUILD = ROOT / "Module_7/output/a4_build"
PDF = ROOT / "Module_7/output/pdf/A4_Zhu.pdf"
BUILD_RECORD = PDF.parent / "A4_Zhu_build.json"
RELEASE_RECORD = PDF.parent / "A4_Zhu_release.json"
SOURCE_INPUTS = (
    "docs/assessments/a4_finite_length_biot.md",
    "Module_7/python/analysis/build_a4_pdf.py",
    "Module_7/python/analysis/a4_theory_checks.py",
    "Module_7/figures/a4/a4_finite_length_prediction.png",
    "Module_7/data/processed/a4_predictions/a4_numeric_checks.json",
    "Module_7/data/processed/a4_predictions/a4_sensor_predictions.csv",
    "Module_7/data/processed/a4_predictions/a4_problem_1_3.csv",
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_bytes(commit, path):
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)


def resolve_commit(ref):
    return subprocess.check_output(
        ["git", "rev-parse", "--verify", ref + "^{commit}"], cwd=ROOT, text=True).strip()


def check_source(commit, hashes=None):
    """Require every PDF-generating input to match its cited source commit."""
    hashes = hashes or {name: digest(ROOT / name) for name in SOURCE_INPUTS}
    if set(hashes) != set(SOURCE_INPUTS):
        raise ValueError("Source-input manifest is incomplete")
    for name, expected in hashes.items():
        historical = hashlib.sha256(git_bytes(commit, name)).hexdigest()
        if historical != expected or digest(ROOT / name) != expected:
            raise ValueError(f"Source/checkpoint mismatch: {name}; commit inputs before rendering")
    return hashes


def inline(text):
    """Escape ordinary text, then render the manuscript's explicit inline notation."""
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"\^([+-]?\d+)", r"<super>\1</super>", text)
    for name, label in (("Bi_parallel", "Bi<sub>parallel</sub>"),
                        ("Bi_perp", "Bi<sub>perp</sub>"),
                        ("Theta_tip", "Theta<sub>tip</sub>")):
        text = text.replace(name, label)
    text = re.sub(r"(?<!\w)\$?h_L\$?(?!\w)", "h<sub>L</sub>", text)
    return re.sub(r"`([^`]+)`", r'<font name="Courier" size="8">\1</font>', text)


def verify_release(record=None):
    """Check the delivered bytes both locally and at the exact artifact commit."""
    record = record or json.loads(RELEASE_RECORD.read_text())
    build = json.loads(BUILD_RECORD.read_text())
    commit = resolve_commit(record["pdf_commit"])
    if record["source_checkpoint"] != build["git_source_checkpoint"]:
        raise ValueError("Release/source checkpoint mismatch")
    check_source(record["source_checkpoint"], build["source_input_sha256"])
    pdf_relative = str(PDF.relative_to(ROOT))
    expected = record["pdf_sha256"]
    if digest(PDF) != expected or hashlib.sha256(git_bytes(commit, pdf_relative)).hexdigest() != expected:
        raise ValueError("PDF bytes do not match the artifact commit/SHA-256")
    if build["pdf_sha256"] != expected or build["source_sha256"] != digest(SOURCE):
        raise ValueError("Build record checksum mismatch")
    if git_bytes(commit, str(BUILD_RECORD.relative_to(ROOT))) != BUILD_RECORD.read_bytes():
        raise ValueError("Build record differs from its artifact commit")
    subprocess.run(["git", "merge-base", "--is-ancestor", record["source_checkpoint"], commit],
                   cwd=ROOT, check=True)
    return record


def record_release(pdf_commit):
    build = json.loads(BUILD_RECORD.read_text())
    record = {"source_checkpoint": build["git_source_checkpoint"],
              "pdf_commit": resolve_commit(pdf_commit),
              "pdf_path": str(PDF.relative_to(ROOT)), "pdf_sha256": digest(PDF),
              "source_path": str(SOURCE.relative_to(ROOT)), "source_sha256": digest(SOURCE),
              "build_record": str(BUILD_RECORD.relative_to(ROOT)),
              "versioning": "The PDF cites its source-only checkpoint; this separate receipt identifies the exact committed PDF without a self-referential commit hash."}
    verify_release(record)
    RELEASE_RECORD.write_text(json.dumps(record, indent=2) + "\n")
    print(RELEASE_RECORD)


def prepare():
    os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/module7-matplotlib")
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.font_manager import FontProperties
    from matplotlib.mathtext import math_to_image
    from PIL import Image
    BUILD.mkdir(parents=True, exist_ok=True)
    manifest = {"source_sha256": digest(SOURCE), "equations": {}}
    equations = re.findall(r"^\$\$(.*?)\$\$$", SOURCE.read_text(), flags=re.M)
    for index, equation in enumerate(equations):
        target = BUILD / f"equation_{index:02d}.png"
        math_to_image("$" + equation + "$", str(target), dpi=220,
                      prop=FontProperties(size=12), format="png", color="#172a3a")
        width, height = Image.open(target).size
        manifest["equations"][equation] = {
            "file": target.name, "width_pt": width * 72 / 220,
            "height_pt": height * 72 / 220}
    (BUILD / "equations.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Prepared {len(equations)} mathematical displays")


def render(source_ref=None):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph,
                                   Preformatted, SimpleDocTemplate, Spacer,
                                   Table, TableStyle)
    manifest = json.loads((BUILD / "equations.json").read_text())
    assert manifest["source_sha256"] == digest(SOURCE), "Prepare equations after source edits"
    fonts = next((ROOT / ".venv/lib").glob("python*/site-packages/matplotlib/mpl-data/fonts/ttf"))
    for name, file in [("Body", "DejaVuSerif.ttf"), ("Body-Bold", "DejaVuSerif-Bold.ttf"),
                       ("Body-Italic", "DejaVuSerif-Italic.ttf"),
                       ("UI", "DejaVuSans.ttf"), ("UI-Bold", "DejaVuSans-Bold.ttf")]:
        pdfmetrics.registerFont(TTFont(name, str(fonts / file)))
    pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold", italic="Body-Italic", boldItalic="Body-Bold")
    pdfmetrics.registerFontFamily("UI", normal="UI", bold="UI-Bold", italic="UI", boldItalic="UI-Bold")
    styles = getSampleStyleSheet()
    body = ParagraphStyle("A4Body", fontName="Body", fontSize=9.2, leading=12.2,
                          textColor=colors.HexColor("#172a3a"), spaceAfter=5)
    h1 = ParagraphStyle("A4Title", parent=body, fontName="UI-Bold", fontSize=21,
                        leading=25, spaceAfter=12)
    h2 = ParagraphStyle("A4Section", parent=body, fontName="UI-Bold", fontSize=14,
                        leading=18, spaceBefore=10, spaceAfter=10, keepWithNext=True)
    h3 = ParagraphStyle("A4Subsection", parent=body, fontName="UI-Bold", fontSize=11,
                        leading=15, spaceBefore=8, spaceAfter=7, keepWithNext=True)
    small = ParagraphStyle("A4Small", parent=body, fontName="UI", fontSize=7.3,
                           leading=10, spaceAfter=6)
    cell = ParagraphStyle("A4Cell", parent=body, fontSize=8.0, leading=10.6, spaceAfter=0)
    header = ParagraphStyle("A4Header", parent=cell, fontName="UI-Bold", textColor=colors.white)
    mono = ParagraphStyle("A4Mono", parent=body, fontName="Courier", fontSize=7.2,
                          leading=10, spaceBefore=3, spaceAfter=8)

    commit = resolve_commit(source_ref or "HEAD")
    source_hashes = check_source(commit)
    git_caption = "Source/calculation checkpoint (source only): " + commit
    pdf_styles = {"# ": h1, "## ": h2, "### ": h3}
    story, i = [], 0
    lines = SOURCE.read_text().splitlines()
    while i < len(lines):
        text = lines[i].strip()
        if not text:
            i += 1
            continue
        if text == "<!-- pagebreak -->":
            story.append(PageBreak()); i += 1; continue
        if text.startswith("```"):
            code = []; i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i]); i += 1
            story.append(Preformatted("\n".join(code), mono)); i += 1; continue
        if text.startswith("$$") and text.endswith("$$"):
            equation = manifest["equations"][text[2:-2]]
            width, height = equation["width_pt"], equation["height_pt"]
            scale = min(1, 516 / width)
            image = Image(str(BUILD / equation["file"]), width=width*scale, height=height*scale)
            image.hAlign = "CENTER"
            story.extend([Spacer(1, 4), image, Spacer(1, 9)])
            i += 1; continue
        if text.startswith("!["):
            match = re.match(r"!\[.*?\]\((.*?)\)", text)
            path = (SOURCE.parent / match.group(1)).resolve()
            from PIL import Image as PILImage
            width, height = PILImage.open(path).size
            story.append(Image(str(path), width=516, height=516*height/width)); i += 1; continue
        if text.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                row = [part.strip() for part in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", x) for x in row): rows.append(row)
                i += 1
            columns = len(rows[0])
            widths = {3: [151, 145, 220], 4: [211, 100, 100, 105],
                      6: [89, 66, 90, 90, 90, 91]}.get(columns, [516/columns]*columns)
            if columns == 6 and rows[0][0].startswith("k,"):
                widths = [92, 77, 77, 77, 98, 95]
            data = [[Paragraph(inline(value), header if rowno == 0 else cell)
                     for value in row] for rowno, row in enumerate(rows)]
            table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#23445c")),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#f1f5f8"), colors.white]),
                ("VALIGN", (0,0), (-1,-1), "TOP"),
                ("LEFTPADDING", (0,0), (-1,-1), 6), ("RIGHTPADDING", (0,0), (-1,-1), 6),
                ("TOPPADDING", (0,0), (-1,-1), 3), ("BOTTOMPADDING", (0,0), (-1,-1), 3),
                ("LINEBELOW", (0,-1), (-1,-1), .5, colors.HexColor("#cbd6df")),
            ]))
            story.extend([table, Spacer(1, 10)]); continue
        heading = next((prefix for prefix in ("### ", "## ", "# ") if text.startswith(prefix)), None)
        if heading:
            story.append(Paragraph(inline(text[len(heading):]), pdf_styles[heading])); i += 1
            if heading == "# ":
                story.append(Paragraph(inline(git_caption), small))
                story.append(Paragraph("Exact PDF commit and SHA-256: see A4_Zhu_release.json in Module_7/output/pdf/.", small))
                story.append(Paragraph("Provisional theory | Measured diameter 12.77 mm; vernier caliper, precision 0.01 mm", small))
            continue
        paragraph = [text]; i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", "|", "$$", "<!--", "```", "![")):
            paragraph.append(lines[i].strip()); i += 1
        joined = " ".join(paragraph)
        story.append(Paragraph(inline(joined), small if joined.startswith("https://") else body))

    PDF.parent.mkdir(parents=True, exist_ok=True)
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#ccd6de"))
        canvas.line(48, 37, 564, 37)
        canvas.setFillColor(colors.HexColor("#536775"))
        canvas.setFont("UI", 7)
        canvas.drawString(48, 24, "Yanheng Zhu | A4 | Provisional theory, measured geometry")
        canvas.drawRightString(564, 24, str(doc.page))
        canvas.restoreState()
    doc = SimpleDocTemplate(str(PDF), pagesize=letter, rightMargin=48, leftMargin=48,
                            topMargin=42, bottomMargin=49, title="A4 - Finite-Rod Model and Validity Checks",
                            author="Yanheng Zhu", pageCompression=1)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    record = {"author": "Yanheng Zhu", "source": str(SOURCE.relative_to(ROOT)),
              "source_sha256": digest(SOURCE), "git_source_checkpoint": commit,
              "git_base_checkpoint": commit, "source_committed": True,
              "source_input_sha256": source_hashes,
              "pdf_artifact_commit_record": str(RELEASE_RECORD.relative_to(ROOT)),
              "checkpoint_scope": "source and calculation inputs only; exact PDF commit is in the separate release record",
              "diameter_status": "measured", "diameter_m": 0.01277,
              "diameter_method": "vernier caliper", "instrument_precision_mm": 0.01,
              "due_at": "2026-11-09T09:05:00-05:00", "pdf_sha256": digest(PDF)}
    BUILD_RECORD.write_text(json.dumps(record, indent=2) + "\n")
    print(PDF)
    print(git_caption)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--source-ref", help="Committed source/calculation inputs, normally the source-only commit H")
    parser.add_argument("--record-release", action="store_true")
    parser.add_argument("--pdf-commit", help="Commit K that contains these exact PDF/build-record bytes")
    parser.add_argument("--verify-release", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        prepare()
    if args.render:
        render(args.source_ref)
    if args.record_release:
        if not args.pdf_commit:parser.error("--record-release requires --pdf-commit")
        record_release(args.pdf_commit)
    if args.verify_release:
        record = verify_release()
        print("Verified source checkpoint, exact committed PDF, build record and SHA-256:", record["pdf_commit"])
    if not (args.prepare or args.render or args.record_release or args.verify_release):
        parser.error("Select --prepare, --render, --record-release or --verify-release")
