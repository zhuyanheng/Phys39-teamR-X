"""Build the two-page A2 PDF from the team's existing ten selected temperatures.

The manufacturer values are intentionally blank until the students locate them
in the 27 C hot-side data-sheet table, as the assignment requires.
"""

import csv
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Flowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data/module_04/steady_state.csv"
OUTPUT = ROOT / "output/pdf/A2_Huang_Zhu.pdf"
HEAT = colors.HexColor("#C62828")
COOL = colors.HexColor("#1565C0")


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
              Paragraph("During one period, on-state current I flows for D times the period and zero current for the rest, where D=|u|/255. Direct integration gives &lt;I&gt;=DI and &lt;I<super>2</super>&gt;=DI<super>2</super>. In general &lt;I<super>2</super>&gt; is not &lt;I&gt;<super>2</super>=D<super>2</super>I<super>2</super>; the difference is D(1-D)I<super>2</super>. Consequently, for fixed on-state current, both Peltier transport and Joule heating scale linearly with PWM duty, consistent with the nearly linear measured branches.", body),
              Paragraph("Let d=u/255 be signed duty and let Q<sub>P</sub> and Q<sub>J</sub> be positive full-on Peltier and object-face Joule heat rates. The reduced balance is C dT/dt = Q<sub>TEC</sub> - G(T-T<sub>0</sub>), with Q<sub>TEC</sub>=dQ<sub>P</sub>+|d|Q<sub>J</sub>. TEC conduction and other passive leaks are included once in G. At steady state the individual heat flows sum to zero: G(T-T<sub>0</sub>)=Q<sub>TEC</sub>.", body),
              Paragraph("Thus T<sub>h</sub>-T<sub>0</sub>=d(Q<sub>P</sub>+Q<sub>J</sub>)/G and T<sub>c</sub>-T<sub>0</sub>=d(Q<sub>P</sub>-Q<sub>J</sub>)/G. Both signed-PWM slopes are positive: m<sub>h</sub>=(Q<sub>P</sub>+Q<sub>J</sub>)/(255G), m<sub>c</sub>=(Q<sub>P</sub>-Q<sub>J</sub>)/(255G). Their ratio gives Q<sub>J</sub>/Q<sub>P</sub>=(r-1)/(r+1)=" + f"{joule_peltier:.4f}." , body),
              PageBreak(),
              Paragraph("Manufacturer comparison and interpretation", title),
              Paragraph("Laird CP14-127-045  |  hot-side temperature 27 deg C", subtitle),
              Paragraph("Manufacturer specifications", section),
              Paragraph("Enter the values located in the 27 deg C hot-side table of the Laird CP14-127-045 data sheet. The condition and meaning of each value are shown below.", body),
    ]

    sheet_table = Table([
        ["Specification", "Meaning and operating condition", "Value"],
        [Paragraph("R<sub>M</sub>", cell), "Module electrical resistance at 27 deg C hot side", "________ ohm"],
        [Paragraph("I<sub>max</sub>", cell), "Maximum specified current at 27 deg C hot side", "________ A"],
        [Paragraph("Q<sub>c,max</sub>", cell), "Maximum cold-side pumping at Delta T = 0", "________ W"],
        [Paragraph("Delta T<sub>max</sub>", cell), "Maximum no-load face temperature difference", "________ deg C"],
    ], colWidths=[104, 318, 104])
    sheet_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF0F7")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))
    story += [sheet_table,
              Spacer(1, 5),
              Paragraph("Source: Laird, <i>CP14-127-045 Thermoelectric Cooler</i>, 27 deg C hot-side specifications: https://sethfraden.github.io/Phys39F26-course/references/laird-tec-cp14-127-045.pdf", small),
              Paragraph("Maximum-current calculation", section),
              Paragraph("At Delta T=0, passive TEC conduction vanishes. In the symmetric model, the object face receives half the total Joule heat. Therefore Q<sub>J,max</sub>=0.5 I<sub>max</sub><super>2</super> R<sub>M</sub> = __________ W; Q<sub>P,max</sub>=Q<sub>c,max</sub>+Q<sub>J,max</sub> = __________ W; and r<sub>Laird,max</sub>=(Q<sub>P,max</sub>+Q<sub>J,max</sub>)/(Q<sub>P,max</sub>-Q<sub>J,max</sub>) = 1+I<sub>max</sub><super>2</super>R<sub>M</sub>/Q<sub>c,max</sub> = __________.", body),
              Paragraph("Comparison", section),
              Paragraph(f"The measured ratio is {ratio:.4f}; the manufacturer's maximum-current prediction is __________. Their difference is __________. Full PWM duty means continuously applying the H-bridge drive, not necessarily I=I<sub>max</sub>. Actual current depends on the supply settings, H-bridge and wiring drops, and module resistance. PWM rather than steady DC, finite face temperature difference, temperature-dependent properties, other passive paths, and fitting slightly curved data with one slope can also affect the comparison.", body),
              Paragraph("Passive conduction", section),
              Paragraph("When the block is hotter than room temperature, passive heat flows out; when colder, it flows in. The term -G(T-T<sub>0</sub>) therefore opposes both excursions. If G is approximately symmetric, conduction reduces both responses but does not by itself explain why the HEAT slope magnitude exceeds the COOL slope magnitude. Reversing current reverses Peltier transport, whereas Joule heating keeps the same sign.", body),
              Paragraph("Conclusion", section),
              Paragraph("Our open-loop measurements show an approximately linear steady-temperature response to PWM in each direction, with a larger heating susceptibility than cooling susceptibility. The fitted slope ratio is 3.50. Under the simplified near-room-temperature energy balance, that ratio corresponds to object-face Joule heating about 0.56 times the full-on Peltier heat rate. This is a model-based inference, not a direct measurement of either heat flow. Peltier transport reverses with current, while Joule heating keeps the same sign, so their effects add during heating and partly offset during cooling. Passive conduction carries heat away from a hot block and toward a cold one, opposing both departures. Manufacturer maximum-current values describe a different operating condition from our PWM-driven apparatus and should be compared on that basis.", body),
    ]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=letter, leftMargin=42,
                            rightMargin=42, topMargin=38, bottomMargin=42)
    doc.build(story, onFirstPage=page_number, onLaterPages=page_number)
    print(OUTPUT)


if __name__ == "__main__":
    main()
