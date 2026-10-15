# /// script
# dependencies = ["matplotlib"]
# ///
"""Fig. 9.1 and Exhibit 9A on one A4 sheet, at notebook size.

Captions are printed underneath, so they do not have to be copied by
hand. Print at 100 percent, not "fit to page", then cut and paste into
the notebook.

Run on the laptop, from this folder:  uv run printsheet.py
"""

import csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

A4 = (8.27, 11.69)
FIG_W, FIG_H = 4.7, 3.3
INK, MUTED, BLUE, ORANGE = "#0b0b0b", "#52514e", "#2a78d6", "#eb6834"

CAPTIONS = [
    ("Fig. 9.1. Stop logic of avoid.py, should_stop(), rev d22b77d.\n"
     "Checked once per control loop, about every 82 ms. DRIVING holds the\n"
     "target speed with the Lab 7 PID. Any reading at or under 30 cm, or\n"
     "above 2.6 V (too close to measure), moves it to STOPPED, which is\n"
     "latched until the run ends. The e-stop button is separate and cuts\n"
     "the motor driver in hardware from either state."),
    ("Exhibit 9A. One stop, loop by loop. Floor test, step 4, last run,\n"
     "15 Oct 2026, avoid.py 80 rpm, stop at 30 cm, data in avoid_80_30.csv.\n"
     "Duty drops to 0 in the first loop that reads 30 cm or less (bold).\n"
     "The wheels coast to 0 in 0.38 s while the sensor sees the wall close\n"
     "from 29.5 to 26.3 cm. rpm is measured over the loop before each row."),
]


def box(ax, x, y, title, lines, colour):
    ax.add_patch(FancyBboxPatch((x - 1.6, y - 0.9), 3.2, 1.8,
                                boxstyle="round,pad=0.05,rounding_size=0.25",
                                facecolor="white", edgecolor=colour,
                                linewidth=1.4))
    ax.text(x, y + 0.35, title, ha="center", va="center", fontsize=9,
            fontweight="bold", color=colour)
    ax.text(x, y - 0.3, lines, ha="center", va="center", fontsize=7,
            color=INK, linespacing=1.4)


def arrow(ax, start, end, style="arc3", colour=INK):
    ax.add_patch(FancyArrowPatch(start, end, connectionstyle=style,
                                 arrowstyle="-|>", mutation_scale=10,
                                 linewidth=1.0, color=colour))


def state_machine(ax):
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis("off")

    box(ax, 2.4, 3.6, "DRIVING", "PID holds\nthe target speed", BLUE)
    box(ax, 7.6, 3.6, "STOPPED", "duty 0\nlatched", ORANGE)

    # start arrow
    arrow(ax, (2.4, 6.3), (2.4, 4.55))
    ax.text(2.55, 5.7, "start", fontsize=7, color=MUTED, va="center")

    # DRIVING to STOPPED
    arrow(ax, (4.05, 3.9), (5.95, 3.9))
    ax.text(5.0, 4.45, "cm <= 30\nor V > 2.6", ha="center", va="bottom",
            fontsize=7, color=INK, linespacing=1.3)

    # self loops
    arrow(ax, (1.7, 2.65), (3.1, 2.65), "arc3,rad=1.6")
    ax.text(2.4, 0.85, "cm > 30, or nothing\nin range", ha="center",
            va="center", fontsize=7, color=INK, linespacing=1.3)
    arrow(ax, (6.9, 2.65), (8.3, 2.65), "arc3,rad=1.6")
    ax.text(7.6, 0.85, "always", ha="center", va="center", fontsize=7,
            color=INK)


def exhibit(ax):
    with open("exhibit9a.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    head = ["t s", "volts", "cm", "stopped", "left rpm", "left duty",
            "right rpm", "right duty"]
    keys = ["t", "volts", "cm", "stopped", "left_rpm", "left_duty",
            "right_rpm", "right_duty"]
    cells = [[r[k] for k in keys] for r in rows]
    ax.axis("off")
    table = ax.table(cellText=cells, colLabels=head, loc="upper center",
                     cellLoc="center", colLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(7)
    table.scale(1, 1.15)
    first_stop = next(i for i, r in enumerate(rows) if r["stopped"] == "1")
    for (row, _), cell in table.get_celld().items():
        cell.set_edgecolor("#c9c8c3")
        cell.set_linewidth(0.5)
        if row == 0:
            cell.set_text_props(fontweight="bold", color=INK)
            cell.set_facecolor("#efeee9")
        elif row - 1 == first_stop:
            cell.set_text_props(fontweight="bold")


fig = plt.figure(figsize=A4, dpi=300)
left = (A4[0] - FIG_W) / 2 / A4[0]
width = FIG_W / A4[0]
height = FIG_H / A4[1]

for i, (draw, caption) in enumerate(zip((state_machine, exhibit), CAPTIONS)):
    bottom = 1 - (0.06 + (i + 1) * height + i * 0.16)
    ax = fig.add_axes([left, bottom, width, height])
    draw(ax)
    fig.text(left, bottom - 0.015, caption, fontsize=7.5, color=INK,
             va="top", ha="left", linespacing=1.5)

fig.text(left, 0.975, "CPSY Lab 9 figures, cut along the edges",
         fontsize=7, color=MUTED, va="top")
fig.savefig("lab9-print-sheet.pdf")
fig.savefig("lab9-print-sheet-preview.png", dpi=110)
print("wrote lab9-print-sheet.pdf")
