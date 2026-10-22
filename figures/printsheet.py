# /// script
# dependencies = ["matplotlib"]
# ///
"""Lab 10 figures and exhibit on A4 sheets, at notebook size.

Exhibit 10A, Fig. 10.1, Fig. 10.2 and Fig. 10.3, two per page, each
119 x 84 mm with its caption printed underneath, so nothing has to be
copied by hand. Print at 100 percent, not "fit to page", then cut and
paste into the notebook.

Every number comes from the run logs in the repo root.

Run on the laptop, from this folder:  uv run printsheet.py
"""

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Patch, Rectangle

LOGS = Path(__file__).resolve().parent.parent
A4 = (8.27, 11.69)
FIG_W, FIG_H = 4.7, 3.3
INK, MUTED, RULE = "#0b0b0b", "#52514e", "#c9c8c3"

# the stripes' own colours, so a cell looks like what the sensor saw.
# grey is hatched: it is low contrast on paper and by design has no hue
SEEN = {
    "red": ("#d64545", None),
    "blue": ("#2a78d6", None),
    "green": ("#3a9a5b", None),
    "grey": ("#a9a7a1", "////"),
    "white": ("#ffffff", None),
}
LABEL = {"red": "red", "blue": "blue", "green": "green",
         "grey": "edge (grey)", "white": "white"}

CAPTIONS = {
    "10A": (
        "Exhibit 10A. What the colour sensor reads on each surface. TCS34725,\n"
        "100 ms, gain 4, steps 3 and 4, 20 Oct 2026. Raw counts, then each\n"
        "channel divided by its white reading. Raw blue is never the largest,\n"
        "even on the blue stripe, because the LED is weak in blue. Divided by\n"
        "white, each stripe's own channel is the largest, which is how\n"
        "classify() in colour.py names it. The grey floor reads equal ratios."),
    "10.1": (
        "Fig. 10.1. The steering rule, follow.py steer(), rev f5c0688, following\n"
        "blue at 30 rpm. A cross section of the track as the rover sees it,\n"
        "red on its left. Under each part: left / right wheel rpm. The turn\n"
        "grows with the drift. On blue the inner wheel slows in proportion to\n"
        "green minus red (zero at the centre, read at start). On an edge it\n"
        "runs at half speed or less, on red, green or white it stops."),
    "10.2": (
        "Fig. 10.2. The same straight, 5 to 15 s, under each steering version.\n"
        "One cell per loop, about 85 ms, coloured by what the sensor saw.\n"
        "Steps 8, 10 and 11. Right: times it left blue, and loops with a wheel\n"
        "under 10 rpm. Stopping a wheel at every drift jerks it (23 loops).\n"
        "Soft turns at the edge cut that but it wanders to the edge more often.\n"
        "Proportional steering leaves blue least, never reaches red or green."),
    "10.3": (
        "Fig. 10.3. (a) The figure eight crossing, step 12, 69.0 to 70.4 s. The\n"
        "other strand's green, blue and red pass under the sensor in 1 s. Green\n"
        "turns it left, red right, and the two cancel. The other blue lasts\n"
        "0.2 s, too short to follow. (b) Started the wrong way round, step 13.\n"
        "The turn away from red drives onto white, so the stripe order flips\n"
        "at 2.0 s (dashed line) and it turns back onto blue. Wheel rpm below."),
}


def read_log(name):
    with open(LOGS / name, newline="") as f:
        return list(csv.DictReader(f))


def window(rows, start, end):
    return [r for r in rows if start <= float(r["t"]) <= end]


def strip(ax, rows, y, height=0.8):
    """One cell per loop, from its time to the next loop's time."""
    for a, b in zip(rows, rows[1:] + [None]):
        t0 = float(a["t"])
        t1 = float(b["t"]) if b else t0 + 0.085
        colour, hatch = SEEN[a["seen"]]
        ax.add_patch(Rectangle((t0, y), t1 - t0, height, facecolor=colour,
                               edgecolor=MUTED if hatch else "none",
                               hatch=hatch, linewidth=0))
    ax.add_patch(Rectangle((float(rows[0]["t"]), y),
                           float(rows[-1]["t"]) + 0.085 - float(rows[0]["t"]),
                           height, facecolor="none", edgecolor=RULE,
                           linewidth=0.5))


def legend(ax, keys, **kw):
    handles = [Patch(facecolor=SEEN[k][0], hatch=SEEN[k][1], edgecolor=RULE,
                     linewidth=0.5, label=LABEL[k]) for k in keys]
    ax.legend(handles=handles, frameon=False, fontsize=6.5, ncol=len(keys),
              handlelength=1.2, columnspacing=1.0, **kw)


def recessive(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(RULE)
    ax.tick_params(colors=MUTED, labelsize=6.5, length=2)


def exhibit_10a(ax):
    white = (6640, 5100, 2815, 15100)
    rows = [("white", white), ("red", (3960, 1420, 870, 6150)),
            ("green", (2340, 2630, 980, 6190)),
            ("blue", (760, 580, 585, 1930)),
            ("grey floor", (2080, 1575, 875, 4685))]
    head = ["surface", "R", "G", "B", "clear", "R/W", "G/W", "B/W"]
    cells = []
    for name, (r, g, b, c) in rows:
        ratios = (r / white[0], g / white[1], b / white[2])
        cells.append([name, r, g, b, c] + [f"{x:.2f}" for x in ratios])
    ax.axis("off")
    table = ax.table(cellText=cells, colLabels=head, loc="center",
                     cellLoc="center", colLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(7.5)
    table.scale(1, 1.6)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor(RULE)
        cell.set_linewidth(0.5)
        if row == 0:
            cell.set_text_props(fontweight="bold", color=INK)
            cell.set_facecolor("#efeee9")
        elif 1 <= row <= 4 and col >= 5:
            # bold the largest ratio, the one classify() picks
            ratios = [float(x) for x in cells[row - 1][5:]]
            if row > 1 and ratios[col - 5] == max(ratios):
                cell.set_text_props(fontweight="bold")


def figure_10_1(ax):
    parts = [("white", "white", "30 / 0\nor 0 / 30", "last turn,\nhard"),
             ("red", "red", "30 / 0", "turn right,\nhard"),
             ("grey", "edge", "30 / 15\nor less", "turn right,\nsoft"),
             ("blue", "blue", "30 / 30 x\n(1 - 12 e)", "lean back\nto centre"),
             ("grey", "edge", "15 / 30\nor less", "turn left,\nsoft"),
             ("green", "green", "0 / 30", "turn left,\nhard"),
             ("white", "white", "0 / 30\nor 30 / 0", "last turn,\nhard")]
    widths = [1.0, 1.4, 0.8, 1.6, 0.8, 1.4, 1.0]
    ax.set_xlim(0, sum(widths))
    ax.set_ylim(0, 6)
    ax.axis("off")
    x = 0
    for (key, name, rpm, action), w in zip(parts, widths):
        colour, hatch = SEEN[key]
        ax.add_patch(Rectangle((x, 3.6), w, 1.6, facecolor=colour,
                               hatch=hatch, edgecolor=RULE, linewidth=0.5))
        text_colour = INK if key in ("white", "grey") else "white"
        ax.text(x + w / 2, 4.4, name, ha="center", va="center", fontsize=7,
                color=text_colour, fontweight="bold")
        ax.text(x + w / 2, 2.8, rpm, ha="center", va="center", fontsize=6.5,
                color=INK, linespacing=1.3)
        ax.text(x + w / 2, 1.3, action, ha="center", va="center",
                fontsize=6.5, color=MUTED, linespacing=1.3)
        x += w
    ax.text(0, 5.6, "rover's left", fontsize=6.5, color=MUTED, va="center")
    ax.text(sum(widths), 5.6, "rover's right", fontsize=6.5, color=MUTED,
            va="center", ha="right")
    ax.text(sum(widths) / 2, 0.2, "e = (G/W - R/W) - centre,  "
            "rpm shown left / right", ha="center", fontsize=6.5, color=MUTED)


def figure_10_2(ax):
    runs = [("step 8, stop a wheel", "follow_blue_30_forward_130904.csv"),
            ("step 10, soft at the edge", "follow_blue_30_forward_133206.csv"),
            ("step 11, proportional", "follow_blue_30_forward_133730.csv")]
    for i, (name, log) in enumerate(runs):
        y = 2 - i
        rows = window(read_log(log), 5, 15)
        strip(ax, rows, y + 0.1)
        left_blue = sum(a["seen"] == "blue" and b["seen"] != "blue"
                        for a, b in zip(rows, rows[1:]))
        stopped = sum(min(float(r["left_rpm"]), float(r["right_rpm"])) < 10
                      for r in rows)
        ax.text(4.9, y + 0.5, name, ha="right", va="center", fontsize=6.5,
                color=INK)
        ax.text(15.2, y + 0.5, f"left {left_blue}x\nstop {stopped}",
                ha="left", va="center", fontsize=6.5, color=MUTED,
                linespacing=1.2)
    ax.set_xlim(1.2, 16.6)
    ax.set_ylim(0, 3.5)
    ax.set_yticks([])
    ax.set_xticks(range(5, 16))
    ax.set_xlabel("time in run, s", fontsize=6.5, color=MUTED, labelpad=2)
    recessive(ax)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_bounds(5, 15)
    legend(ax, ["blue", "grey", "green", "red"], loc="upper center",
           bbox_to_anchor=(0.6, 1.02))


def wheels(ax, rows, flip_at=None):
    t = [float(r["t"]) for r in rows]
    ax.plot(t, [float(r["left_rpm"]) for r in rows], color=INK,
            linewidth=1.2, label="left wheel")
    ax.plot(t, [float(r["right_rpm"]) for r in rows], color=MUTED,
            linewidth=1.2, linestyle=(0, (3, 1.5)), label="right wheel")
    ax.set_ylim(0, 50)
    ax.set_yticks([0, 25, 50])
    ax.set_ylabel("rpm", fontsize=6.5, color=MUTED)
    if flip_at is not None:
        ax.axvline(flip_at, color=INK, linewidth=0.8, linestyle=(0, (2, 2)))
    recessive(ax)


def figure_10_3(fig, box):
    left, bottom, width, height = box
    half = (width - 0.06) / 2
    panels = [("a", "follow_blue_30_forward_134607.csv", 69.0, 70.4, None),
              ("b", "follow_blue_30_forward_135546.csv", 1.4, 3.4, None)]
    for i, (tag, log, start, end, _) in enumerate(panels):
        rows = window(read_log(log), start, end)
        flip_at = next((float(r["t"]) for r in rows if r.get("flips") == "1"),
                       None)
        x = left + i * (half + 0.06)
        top = fig.add_axes([x, bottom + height * 0.62, half, height * 0.2])
        strip(top, rows, 0)
        top.set_xlim(start, end + 0.085)
        top.set_ylim(0, 0.8)
        top.axis("off")
        if flip_at is not None:
            top.axvline(flip_at, color=INK, linewidth=0.8,
                        linestyle=(0, (2, 2)))
            top.text(flip_at + 0.05, 1.05, "FLIP", ha="left", fontsize=6.5,
                     color=INK)
        top.text(start, 1.05, f"({tag})", fontsize=7, color=INK,
                 fontweight="bold")
        low = fig.add_axes([x, bottom + height * 0.1, half, height * 0.45])
        wheels(low, rows, flip_at)
        low.set_xlim(start, end + 0.085)
        low.set_xlabel("time in run, s", fontsize=6.5, color=MUTED)
        if i == 0:
            low.legend(frameon=False, fontsize=6.5, loc="upper left",
                       handlelength=2)
    key = fig.add_axes([left, bottom + height * 0.88, width, height * 0.1])
    key.axis("off")
    legend(key, ["blue", "grey", "green", "red", "white"], loc="center")


def page(pdf, items, title):
    fig = plt.figure(figsize=A4, dpi=300)
    left = (A4[0] - FIG_W) / 2 / A4[0]
    width = FIG_W / A4[0]
    height = FIG_H / A4[1]
    for i, (key, draw) in enumerate(items):
        bottom = 1 - (0.06 + (i + 1) * height + i * 0.16)
        if draw is figure_10_3:
            draw(fig, (left, bottom, width, height))
        elif draw is figure_10_2:
            # room inside the cut line for the time axis label
            draw(fig.add_axes([left, bottom + 0.03, width, height - 0.035]))
        else:
            draw(fig.add_axes([left, bottom, width, height]))
        fig.add_artist(Rectangle((left, bottom), width, height,
                                 transform=fig.transFigure, facecolor="none",
                                 edgecolor=RULE, linewidth=0.4,
                                 linestyle=(0, (4, 3))))
        fig.text(left, bottom - 0.015, CAPTIONS[key], fontsize=7.5,
                 color=INK, va="top", ha="left", linespacing=1.5)
    fig.text(left, 0.975, title, fontsize=7, color=MUTED, va="top")
    pdf.savefig(fig)
    return fig


with PdfPages("lab10-print-sheet.pdf") as pdf:
    first = page(pdf, [("10A", exhibit_10a), ("10.1", figure_10_1)],
                 "CPSY Lab 10 figures, page 1 of 2, cut along the dashed edges")
    first.savefig("lab10-print-sheet-1.png", dpi=110)
    second = page(pdf, [("10.2", figure_10_2), ("10.3", figure_10_3)],
                  "CPSY Lab 10 figures, page 2 of 2, cut along the dashed edges")
    second.savefig("lab10-print-sheet-2.png", dpi=110)
print("wrote lab10-print-sheet.pdf")
