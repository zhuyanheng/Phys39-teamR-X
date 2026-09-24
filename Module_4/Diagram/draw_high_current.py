#!/usr/bin/env python3
"""
High-current TEC (thermoelectric cooler) H-bridge circuit diagrams.

Generates two figures and opens them in a window:

  * heating_high_current.png  ->  Heating Mode: High-Current Path  (red)
  * cooling_high_current.png  ->  Cooling Mode: High-Current Path  (blue)

The high-current path is drawn as a THICK (linewidth=4) coloured line and every
high-current wire is labelled "18 AWG".  The low-voltage Arduino control link is
drawn as a thin grey dashed line and is explicitly marked as NOT being part of
the high-current path.

Run:
    python3 draw_high_current.py
"""

import os

import schemdraw
import schemdraw.elements as elm

# Force the matplotlib backend so we can save PNG files.
schemdraw.use('matplotlib')

AWG = '18 AWG'          # wire-gauge annotation for every high-current wire
LW = 4                  # line width used for the high-current path
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


# --------------------------------------------------------------------------- #
# small drawing helpers
# --------------------------------------------------------------------------- #
def add_text(d, xy, label, fontsize=12, color='black'):
    """Standalone text label, centred at xy."""
    d += elm.Label().at(xy).label(label, fontsize=fontsize, color=color)


def wire(d, p1, p2, color, arrow=True):
    """Thick high-current wire segment from p1 to p2.

    The arrowhead (when enabled) is placed at p2, i.e. the current flows
    from p1 towards p2.
    """
    seg = elm.Line(arrow='->' if arrow else None).at(p1).to(p2)
    seg.color(color).linewidth(LW)
    d += seg
    return seg


def awg(d, xy, fontsize=9):
    """Small '18 AWG' annotation next to a high-current wire."""
    add_text(d, xy, AWG, fontsize=fontsize, color='#444444')


# --------------------------------------------------------------------------- #
# main drawing routine
# --------------------------------------------------------------------------- #
def draw_circuit(mode):
    """Draw one high-current path diagram.

    mode: 'heating' -> red, current: supply+ -> B+ -> M+ -> TEC -> switch -> M- -> B- -> supply-
          'cooling' -> blue, current: supply+ -> B+ -> M- -> switch -> TEC -> M+ -> B- -> supply-
    """
    assert mode in ('heating', 'cooling')

    color = 'red' if mode == 'heating' else 'blue'
    title = f"{'Heating' if mode == 'heating' else 'Cooling'} Mode: High-Current Path"

    d = schemdraw.Drawing(show=False)

    # ---- node coordinates (drawing units) ---------------------------------
    P_top = (2.0, 2.0)      # DC supply "+" terminal
    P_bot = (2.0, -2.0)     # DC supply "-" terminal
    Bp    = (6.0, 2.0)      # H-bridge pin B+
    Bm    = (6.0, -2.0)     # H-bridge pin B-
    Mp    = (9.0, 2.0)      # H-bridge pin M+
    Mm    = (9.0, -2.0)     # H-bridge pin M-
    Rt    = (12.0, 2.0)     # right branch, top of TEC
    Rg1   = (12.0, 1.0)     # right branch, TEC / gap junction
    Rg2   = (12.0, 0.0)     # right branch, gap / switch junction
    Rb    = (12.0, -2.0)    # right branch, bottom of switch

    # ---- title ------------------------------------------------------------
    add_text(d, (7.0, 3.6), title, fontsize=15)

    # ---- DC power supply --------------------------------------------------
    d += elm.SourceV().at(P_bot).to(P_top).linewidth(2)
    add_text(d, (2.0, 2.32), '+', fontsize=13, color=color)          # positive -> B+
    add_text(d, (2.0, -2.32), '-', fontsize=13, color=color)         # negative -> B-
    add_text(d, (0.75, 0.0), '$V_{supply}$', fontsize=12)
    add_text(d, (3.25, 0.0), '$I_{limit}$', fontsize=12)

    # ---- H-bridge module (rectangle with 4 labelled pins) ------------------
    d += (elm.Rect(corner1=(0.0, 0.0), corner2=(3.0, 5.0))
          .at((6.0, -2.5)).theta(0).linewidth(2))
    add_text(d, (7.5, 1.0), 'H-Bridge', fontsize=12)

    for p in (Bp, Bm, Mp, Mm):
        d += elm.Dot().at(p)

    add_text(d, (5.55, 2.15), 'B+', fontsize=11)
    add_text(d, (5.55, -2.15), 'B-', fontsize=11)
    add_text(d, (9.45, 2.15), 'M+', fontsize=11)
    add_text(d, (9.45, -2.15), 'M-', fontsize=11)

    # ---- high-current path -------------------------------------------------
    if mode == 'heating':
        # supply+ -> B+  (top rail)
        wire(d, P_top, Bp, color)
        # B+ -> M+ inside the H-bridge  (top bar)
        wire(d, Bp, Mp, color)
        # M+ -> TEC
        wire(d, Mp, Rt, color)
        # TEC (down through it)
        d += elm.RBox().at(Rt).to(Rg1).color(color).linewidth(3)
        # gap TEC -> switch (current flows down)
        wire(d, Rg1, Rg2, color)
        # Thermal switch (down through it), in series with the TEC
        d += elm.Switch().at(Rg2).to((12.0, -1.0)).color(color).linewidth(3)
        # gap switch -> bottom of branch (current flows down)
        wire(d, (12.0, -1.0), Rb, color)
        # branch bottom -> M-
        wire(d, Rb, Mm, color)
        # M- -> B- inside the H-bridge  (bottom bar)
        wire(d, Mm, Bm, color)
        # B- -> supply-  (bottom rail)
        wire(d, Bm, P_bot, color)
    else:
        # cooling: current through the TEC/switch branch is reversed
        # supply+ -> B+  (top rail)
        wire(d, P_top, Bp, color)
        # B+ -> M- inside the H-bridge  (diagonal)
        wire(d, Bp, Mm, color)
        # M- -> bottom of branch (current flows right, then up)
        wire(d, Mm, Rb, color)
        # gap up into the switch
        wire(d, Rb, (12.0, -1.0), color)
        # Thermal switch (up through it), in series with the TEC
        d += elm.Switch().at((12.0, -1.0)).to(Rg2).color(color).linewidth(3)
        # gap switch -> TEC (current flows up)
        wire(d, Rg2, Rg1, color)
        # TEC (up through it)
        d += elm.RBox().at(Rg1).to(Rt).color(color).linewidth(3)
        # TEC top -> M+
        wire(d, Rt, Mp, color)
        # M+ -> B- inside the H-bridge  (diagonal)
        wire(d, Mp, Bm, color)
        # B- -> supply-  (bottom rail)
        wire(d, Bm, P_bot, color)

    # ---- component labels ---------------------------------------------------
    add_text(d, (12.7, 1.5), 'TEC', fontsize=12)
    add_text(d, (13.6, -0.5), 'Thermal Switch', fontsize=10)

    # ---- "18 AWG" on every high-current wire -------------------------------
    awg(d, (4.0, 2.3))          # top rail
    awg(d, (4.0, -2.3))         # bottom rail
    awg(d, (10.5, 2.3))         # M+ -> TEC
    awg(d, (10.5, -2.3))        # switch -> M-
    awg(d, (12.7, 0.0))         # TEC / switch series branch

    # ---- low-voltage control (thin grey dashed line, de-emphasised) ---------
    # Arduino sits below the H-bridge; only the low-voltage control lines go up.
    d += (elm.Rect(corner1=(0.0, 0.0), corner2=(1.0, 0.6))
          .at((7.0, -3.9)).theta(0).linewidth(1))
    add_text(d, (7.5, -3.6), 'Arduino', fontsize=9)
    d += (elm.Line().at((7.5, -3.3)).to((7.5, -2.5))
          .color('grey').linewidth(1).linestyle('--'))
    add_text(d, (9.7, -3.05), 'Low-voltage control (PWM / DIR / GND),',
             fontsize=8, color='grey')
    add_text(d, (9.7, -3.45), 'not high-current path',
             fontsize=8, color='grey')

    return d


def main():
    for mode in ('heating', 'cooling'):
        d = draw_circuit(mode)
        fname = os.path.join(OUT_DIR, f'{mode}_high_current.png')
        d.save(fname, transparent=False, dpi=150)   # white background
        print(f'Saved {fname}')
        d.draw(show=True)   # open the figure window (no-op in headless env)


if __name__ == '__main__':
    main()

