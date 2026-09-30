"""Build the two-page A2 PDF from the team's existing ten selected temperatures.

The manufacturer values are taken from the 27 C hot-side column of the Laird
CP14-127-045 data sheet and filled in. Outputs the Module 4 submission PDF.
Earlier drafts can be recovered from Git history if needed.
"""

import csv
import io
import re
from pathlib import Path

from PIL import Image as PILImage, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    Flowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data/module_04/steady_state.csv"
OUTPUT = ROOT / "Module_4/A2_Huang_Zhu.pdf"
HEAT = colors.HexColor("#C62828")
COOL = colors.HexColor("#1565C0")
MATH_FONT = "/System/Library/Fonts/Supplemental/STIXGeneral.otf"


def fit(points):
    mx = sum(x for x, _ in points) / len(points)
    my = sum(y for _, y in points) / len(points)
    slope = sum((x - mx) * (y - my) for x, y in points) / sum(
        (x - mx) ** 2 for x, _ in points
    )
    return slope, my - slope * mx


class TemperatureChart(Flowable):
    def __init__(self, heat_points, cool_points):
        super().__init__()
        self.width = 526
        self.height = 245
        self.heat_points = heat_points
        self.cool_points = cool_points

    def draw(self):
        c = self.canv
        left, bottom, width, height = 49, 41, 445, 177
        xmin, xmax, ymin, ymax = -100, 50, 8, 48

        def px(x):
            return left + (x - xmin) * width / (xmax - xmin)

        def py(y):
            return bottom + (y - ymin) * height / (ymax - ymin)

        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(self.width / 2, 231, "Steady temperature vs signed PWM")
        c.setLineWidth(0.45)
        c.setStrokeColor(colors.HexColor("#D8DEE5"))
        for x in (-100, -75, -50, -25, 0, 25, 50):
            c.line(px(x), bottom, px(x), bottom + height)
            c.setFont("Helvetica", 7)
            c.setFillColor(colors.black)
            c.drawCentredString(px(x), 28, str(x))
        for y in (10, 20, 30, 40):
            c.line(left, py(y), left + width, py(y))
            c.setFont("Helvetica", 7)
            c.setFillColor(colors.black)
            c.drawRightString(left - 5, py(y) - 2, str(y))
        c.setStrokeColor(colors.HexColor("#46505B"))
        c.rect(left, bottom, width, height, fill=0, stroke=1)
        c.setFont("Helvetica", 8)
        c.drawCentredString(left + width / 2, 13, "Signed PWM count  (COOL < 0; HEAT > 0)")
        c.saveState()
        c.translate(13, bottom + height / 2)
        c.rotate(90)
        c.drawCentredString(0, 0, "Temperature (deg C)")
        c.restoreState()
        for points, color in ((self.cool_points, COOL), (self.heat_points, HEAT)):
            m, b = fit(points)
            x1, x2 = min(x for x, _ in points), max(x for x, _ in points)
            c.setStrokeColor(color)
            c.setLineWidth(1.65)
            c.setDash(4, 2.5)
            c.line(px(x1), py(m * x1 + b), px(x2), py(m * x2 + b))
            c.setDash()
            for x, y in points:
                c.setFillColor(color)
                c.circle(px(x), py(y), 2.9, fill=1, stroke=0)
        c.setFont("Helvetica", 7.5)
        c.setFillColor(HEAT)
        c.drawString(65, 202, "HEAT")
        c.setFillColor(COOL)
        c.drawString(106, 202, "COOL")
        c.setFillColor(colors.black)
        c.drawString(147, 202, "dashed = fit")


class MathFormula(Flowable):
    """Render real math glyphs and scripts at high resolution, then embed in PDF."""

    def __init__(self, expression):
        super().__init__()
        scale = 4
        base = ImageFont.truetype(MATH_FONT, 12 * scale)
        script = ImageFont.truetype(MATH_FONT, 8 * scale)
        integral = ImageFont.truetype(MATH_FONT, 19 * scale)
        canvas = PILImage.new("RGBA", (2800, 140), (255, 255, 255, 0))
        draw = ImageDraw.Draw(canvas)
        x, baseline, index = 0.0, 82, 0

        def put(value, font, y):
            nonlocal x
            draw.text((x, y), value, font=font, fill="black", anchor="ls")
            x += draw.textlength(value, font=font)

        while index < len(expression):
            if expression.startswith("∫_{", index):
                match = re.match(r"∫_\{([^}]*)\}\^\{([^}]*)\}", expression[index:])
                if match is None:
                    raise ValueError(f"Invalid integral notation: {expression}")
                left = x
                put("∫", integral, baseline + 3)
                # STIX's integral overhangs its advance width. Put the limits
                # outside the actual glyph bounds so neither is hidden by it.
                limit_x = left + 46
                draw.text((limit_x, baseline + 33), match.group(1), font=script,
                          fill="black", anchor="ls")
                draw.text((limit_x, baseline - 31), match.group(2), font=script,
                          fill="black", anchor="ls")
                x = max(x, limit_x + max(draw.textlength(match.group(1), font=script),
                                         draw.textlength(match.group(2), font=script))) + 12
                index += len(match.group(0))
            elif expression.startswith("_{", index) or expression.startswith("^{", index):
                match = re.match(r"([_\^])\{([^}]*)\}", expression[index:])
                if match is None:
                    raise ValueError(f"Invalid math script: {expression}")
                put(match.group(2), script, baseline + (16 if match.group(1) == "_" else -24))
                index += len(match.group(0))
            else:
                stop = index + 1
                while stop < len(expression) and not any(
                    expression.startswith(marker, stop) for marker in ("∫_{", "_{", "^{")
                ):
                    stop += 1
                put(expression[index:stop], base, baseline)
                index = stop

        visible = canvas.getbbox()
        if visible is None:
            raise ValueError("Empty formula")
        canvas = canvas.crop((0, max(0, visible[1] - 5), min(2800, visible[2] + 5),
                              min(140, visible[3] + 5)))
        stream = io.BytesIO()
        canvas.save(stream, format="PNG")
        stream.seek(0)
        self.reader = ImageReader(stream)
        natural_width = canvas.width / scale
        natural_height = canvas.height / scale
        factor = min(1.0, 500 / natural_width)
        self.image_width = natural_width * factor
        self.image_height = natural_height * factor
        self.width = self.image_width + 2
        self.height = max(18, self.image_height + 3)

    def draw(self):
        self.canv.drawImage(self.reader, 0, (self.height - self.image_height) / 2,
                            width=self.image_width, height=self.image_height, mask="auto")


def math_pair(left, right):
    row = Table([[MathFormula(left), MathFormula(right)]], colWidths=[263, 263])
    row.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return row


def page_number(canvas, doc):
    canvas.setFillColor(colors.white)
    canvas.rect(0, 0, letter[0], letter[1], fill=1, stroke=0)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#6B7280"))
    canvas.drawString(42, 26, "Phys 39  |  Module 4  |  A2")
    canvas.drawRightString(letter[0] - 42, 26, f"{doc.page} / 2")


def main():
    with SOURCE.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    heat = sorted((int(r["pwm"]), float(r["steady_temperature_C"]))
                  for r in rows if r["direction"] == "HEAT")
    cool = sorted((-int(r["pwm"]), float(r["steady_temperature_C"]))
                  for r in rows if r["direction"] == "COOL")
    if len(heat) != 5 or len(cool) != 5:
        raise ValueError("The A2 graph requires five HEAT and five COOL values")
    mh, _ = fit(heat)
    mc, _ = fit(cool)
    ratio = mh / mc
    joule_peltier = (ratio - 1) / (ratio + 1)

    # Laird CP14-127-045, 27 C hot-side column (official data sheet).
    R_M = 1.50        # ohms, module resistance
    I_MAX = 8.6       # amps, I @ Delta T_max
    QC_MAX = 71.3     # watts, Qcmax at Delta T = 0
    DT_MAX = 70.5     # deg C, Delta Tmax at Qc = 0
    qj_max = 0.5 * I_MAX ** 2 * R_M
    qp_max = QC_MAX + qj_max
    r_laird = (qp_max + qj_max) / (qp_max - qj_max)

    styles = getSampleStyleSheet()
    title = ParagraphStyle("A2Title", parent=styles["Title"], fontName="Helvetica-Bold",
                           fontSize=17, leading=20, spaceAfter=3)
    subtitle = ParagraphStyle("A2Subtitle", parent=styles["Normal"], alignment=TA_CENTER,
                              fontSize=9, leading=12, textColor=colors.HexColor("#4B5563"),
                              spaceAfter=9)
    section = ParagraphStyle("A2Section", parent=styles["Heading2"], fontName="Helvetica-Bold",
                             fontSize=10.7, leading=13, spaceBefore=7, spaceAfter=4,
                             textColor=colors.HexColor("#17324F"))
    body = ParagraphStyle("A2Body", parent=styles["BodyText"], fontName="Helvetica",
                          fontSize=9.8, leading=14.0, spaceAfter=7)
    small = ParagraphStyle("A2Small", parent=body, fontSize=8.2, leading=11.2,
                           textColor=colors.HexColor("#4B5563"))
    cell = ParagraphStyle("A2Cell", parent=body, fontSize=7.8, leading=10.2, spaceAfter=0)

    story = [
        Paragraph("A2: TEC Heating and Cooling Analysis", title),
        Paragraph("Ricky Huang and Xavier Zhu  |  Phys 39  |  Module 4", subtitle),
        TemperatureChart(heat, cool),
        Paragraph("Figure 1. Five selected PWM magnitudes per direction; the two 0-PWM points overlap at 23.44 deg C. Steady temperatures are the means of the final approximately 20 s after the trace ceased sustained directional drift and fluctuated within a local band. Fits cover HEAT 0-45 and COOL -96-0 signed PWM counts.", small),
    ]

    slope_table = Table([
        ["HEAT slope", "COOL slope", "Measured ratio", "Inferred Joule/Peltier"],
        [f"{mh:.4f} deg C/count", f"{mc:.4f} deg C/count", f"{ratio:.4f}", f"{joule_peltier:.4f}"],
    ], colWidths=[131.5] * 4)
    slope_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF0F7")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story += [slope_table,
              Paragraph("PWM averaging and steady-state energy balance", section),
              Paragraph("During one PWM period, the signed on-state current flows for fraction D of the period and is zero otherwise. Here D is the magnitude of signed PWM divided by 255. Evaluating the two period integrals gives:", body),
              math_pair("⟨I⟩ = (1/τ) ∫_{0}^{τ} I(t) dt = [I(Dτ) + 0(1-D)τ]/τ = DI",
                        "⟨I^{2}⟩ = (1/τ) ∫_{0}^{τ} I(t)^{2} dt = [I^{2}(Dτ)]/τ = DI^{2}"),
              MathFormula("⟨I^{2}⟩ - ⟨I⟩^{2} = D(1-D)I^{2}"),
              Paragraph("The last expression is nonzero for duty cycles strictly between zero and one. Using the square of the mean current instead of the mean squared current would incorrectly make Joule heating quadratic in duty. The measured branches are approximately linear.", body),
              Paragraph("Let signed duty equal signed PWM divided by 255. The reduced heat balance counts TEC conduction and other passive leaks once in the effective conductance:", body),
              math_pair("C dT/dt = Q_{TEC} - G(T-T_{0});   Q_{TEC} = dQ_{P} + |d|Q_{J}",
                        "dT/dt = 0:   G(T-T_{0}) = Q_{TEC}"),
              Paragraph("The Peltier term reverses between heating and cooling; the Joule term does not. Solving both branches and differentiating with respect to signed PWM gives:", body),
              math_pair("T_{h}-T_{0}=d(Q_{P}+Q_{J})/G;   T_{c}-T_{0}=d(Q_{P}-Q_{J})/G",
                        "m_{h}=(Q_{P}+Q_{J})/(255G);   m_{c}=(Q_{P}-Q_{J})/(255G)"),
              MathFormula(f"r=m_{{h}}/m_{{c}};   Q_{{J}}/Q_{{P}}=(r-1)/(r+1)={joule_peltier:.4f}"),
              PageBreak(),
              Paragraph("Manufacturer comparison and interpretation", title),
              Paragraph("Laird CP14-127-045  |  hot-side temperature 27 deg C", subtitle),
              Paragraph("Manufacturer specifications", section),
              Paragraph("Values located in the 27 deg C hot-side table of the Laird CP14-127-045 data sheet. The condition and meaning of each value are shown below.", body),
    ]

    sheet_table = Table([
        ["Specification", "Meaning and operating condition", "Value"],
        [MathFormula("R_{M}"), "Module electrical resistance at 27 deg C hot side", f"{R_M:.2f} ohm"],
        [MathFormula("I_{max}"), "Maximum specified current (I at Delta T_max) at 27 deg C hot side", f"{I_MAX:.1f} A"],
        [MathFormula("Q_{c,max}"), "Maximum cold-side pumping at Delta T = 0", f"{QC_MAX:.1f} W"],
        [MathFormula("ΔT_{max}"), "Maximum no-load face temperature difference (at Qc = 0)", f"{DT_MAX:.1f} deg C"],
    ], colWidths=[104, 318, 104])
    sheet_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF0F7")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))
    story += [sheet_table,
              Spacer(1, 5),
              Paragraph("Source: Laird, <i>CP14-127-045 Thermoelectric Cooler</i>, 27 deg C hot-side specifications: https://sethfraden.github.io/Phys39F26-course/references/laird-tec-cp14-127-045.pdf", small),
              Paragraph("Maximum-current calculation", section),
              Paragraph("At zero face-temperature difference, passive TEC conduction vanishes. The symmetric model assigns half the total Joule heat to the object face:", body),
              math_pair(f"Q_{{J,max}}=(1/2)(I_{{max}})^{{2}}R_{{M}}={qj_max:.2f} W",
                        f"Q_{{P,max}}=Q_{{c,max}}+Q_{{J,max}}={qp_max:.2f} W"),
              MathFormula(f"r_{{Laird,max}}=1+(I_{{max}})^{{2}}R_{{M}}/Q_{{c,max}}={r_laird:.3f}"),
              Paragraph("Comparison", section),
              Paragraph(f"The measured ratio is {ratio:.4f} versus the manufacturer's maximum-current prediction of {r_laird:.3f}, about {ratio / r_laird:.2f} times larger. Full PWM duty means the H-bridge is continuously on, not that the current equals I_max; the actual current depends on the supply settings (12 V, 10 A limit), H-bridge and wiring drops, and module resistance. Because the symmetric model predicts r approaching 1 below I_max, the larger measured ratio reflects its idealizations (equal half-Joule split, single symmetric conductance) plus PWM versus DC, finite face temperature difference, changing properties, and one-slope fits over slightly curved data.", body),
              Paragraph("Passive conduction", section),
              Paragraph("When the block is hotter than room temperature, passive heat flows out; when colder, it flows in. The passive-conductance term therefore opposes both excursions. If that conductance is approximately symmetric, it reduces both responses but does not by itself explain why the HEAT slope magnitude exceeds the COOL slope magnitude. Reversing current reverses Peltier transport, whereas Joule heating keeps the same sign.", body),
              Paragraph("Conclusion", section),
              Paragraph("Our open-loop measurements show an approximately linear steady-temperature response to PWM in each direction, with a larger heating susceptibility than cooling susceptibility. The fitted slope ratio is 3.50. Under the simplified near-room-temperature energy balance, that ratio corresponds to object-face Joule heating about 0.56 times the full-on Peltier heat rate. This is a model-based inference, not a direct measurement of either heat flow. Peltier transport reverses with current, while Joule heating keeps the same sign, so their effects add during heating and partly offset during cooling. Passive conduction carries heat away from a hot block and toward a cold one, opposing both departures. The measured slope ratio exceeds the manufacturer's maximum-current prediction (2.56), reflecting the symmetric model's simplifications.", body),
    ]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=letter, leftMargin=42,
                            rightMargin=42, topMargin=38, bottomMargin=42)
    doc.build(story, onFirstPage=page_number, onLaterPages=page_number)
    print(OUTPUT)


if __name__ == "__main__":
    main()
