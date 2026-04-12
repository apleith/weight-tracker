"""Generate a dark-themed weight dashboard PNG and set it as Windows wallpaper."""

import ctypes
import json
from datetime import date, timedelta
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure

from .model import (
    START_DATE, START_WEIGHT, GOAL_WEIGHT,
    expected_weight, day_number, compute_stats,
)

# -- Color palette (dark theme) --
BG = "#0d1117"
SURFACE = "#161b22"
BORDER = "#30363d"
TEXT = "#e6edf3"
TEXT_DIM = "#8b949e"
ACCENT = "#58a6ff"       # expected curve
ACTUAL = "#3fb950"       # actual data points
AHEAD = "#3fb950"        # ahead of schedule
BEHIND = "#f85149"       # behind schedule
GRID = "#21262d"
MILESTONE = "#f0883e"


def generate_wallpaper(
    entries: list[dict],
    output_path: str | Path,
    width: int = 2560,
    height: int = 1440,
    dpi: int = 150,
    breakpoints=None,
):
    """Render the dashboard PNG."""
    stats = compute_stats(entries, breakpoints)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig_w = width / dpi
    fig_h = height / dpi
    fig = Figure(figsize=(fig_w, fig_h), dpi=dpi, facecolor=BG)

    # Layout: top row = KPI cards, bottom = chart
    # Using gridspec for precise control
    gs = fig.add_gridspec(
        nrows=2, ncols=1,
        height_ratios=[1, 3],
        left=0.06, right=0.94, top=0.92, bottom=0.08,
        hspace=0.15,
    )

    # -- KPI strip (top) --
    ax_kpi = fig.add_subplot(gs[0])
    ax_kpi.set_facecolor(BG)
    ax_kpi.axis("off")

    kpis = [
        ("CURRENT", f"{stats['current_weight']:.1f}", "lbs"),
        ("LOST", f"{stats['total_lost']:.1f}", f"lbs ({stats['pct_lost']}%)"),
        ("EXPECTED", f"{stats['expected_today']:.1f}", "lbs today"),
        ("DEVIATION", f"{stats['deviation']:+.1f}", "lbs"),
        ("RATE", f"{stats['recent_weekly_rate']:.1f}", "lbs/week"),
        ("DAY", f"{stats['day_number']}", f"of 525"),
    ]

    n = len(kpis)
    for i, (label, value, unit) in enumerate(kpis):
        x = (i + 0.5) / n
        # Value color: deviation gets ahead/behind coloring
        v_color = TEXT
        if label == "DEVIATION":
            v_color = AHEAD if stats["deviation"] <= 0 else BEHIND

        ax_kpi.text(x, 0.75, label, transform=ax_kpi.transAxes,
                    ha="center", va="center", fontsize=9, color=TEXT_DIM,
                    fontweight="bold", fontfamily="monospace")
        ax_kpi.text(x, 0.40, value, transform=ax_kpi.transAxes,
                    ha="center", va="center", fontsize=22, color=v_color,
                    fontweight="bold", fontfamily="monospace")
        ax_kpi.text(x, 0.10, unit, transform=ax_kpi.transAxes,
                    ha="center", va="center", fontsize=9, color=TEXT_DIM,
                    fontfamily="monospace")

    # -- Weight chart (bottom) --
    ax = fig.add_subplot(gs[1])
    ax.set_facecolor(SURFACE)
    for spine in ax.spines.values():
        spine.set_color(BORDER)

    # Expected curve
    total_days = 525
    curve_dates = [START_DATE + timedelta(days=d) for d in range(total_days + 1)]
    curve_weights = [expected_weight(d, breakpoints) for d in range(total_days + 1)]
    ax.plot(curve_dates, curve_weights, color=ACCENT, linewidth=2,
            label="Expected", alpha=0.7, linestyle="--")

    # Fill between start and expected
    ax.fill_between(curve_dates, curve_weights, START_WEIGHT,
                    color=ACCENT, alpha=0.03)

    # Actual data
    if entries:
        actual_dates = [e["date"] for e in entries]
        actual_weights = [e["weight"] for e in entries]
        ax.plot(actual_dates, actual_weights, color=ACTUAL, linewidth=2.5,
                marker="o", markersize=6, label="Actual", zorder=5)

        # Highlight latest point
        ax.scatter([actual_dates[-1]], [actual_weights[-1]],
                   color=ACTUAL, s=120, zorder=6, edgecolors="white", linewidth=1.5)

    # Goal line
    ax.axhline(y=GOAL_WEIGHT, color=MILESTONE, linewidth=1, linestyle=":",
               alpha=0.5, label=f"Goal: {GOAL_WEIGHT}")

    # Milestones
    milestones = [
        (600, "600"),
        (500, "500"),
        (400, "400"),
        (300, "300"),
    ]
    for mw, mlabel in milestones:
        if mw < START_WEIGHT:
            ax.axhline(y=mw, color=GRID, linewidth=0.5, linestyle=":")

    # Styling
    ax.set_ylabel("Weight (lbs)", color=TEXT_DIM, fontsize=11, fontfamily="monospace")
    ax.set_xlabel("", color=TEXT_DIM)
    ax.tick_params(colors=TEXT_DIM, labelsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.grid(True, color=GRID, linewidth=0.5, alpha=0.5)
    ax.set_ylim(GOAL_WEIGHT - 20, START_WEIGHT + 10)
    ax.set_xlim(START_DATE, START_DATE + timedelta(days=total_days + 14))

    legend = ax.legend(loc="upper right", fontsize=9,
                       facecolor=SURFACE, edgecolor=BORDER,
                       labelcolor=TEXT_DIM)

    # Title
    fig.text(0.06, 0.96, "WEIGHT TRACKER", fontsize=16, color=TEXT,
             fontweight="bold", fontfamily="monospace")
    fig.text(0.06, 0.935, f"660 → {GOAL_WEIGHT}  |  Started {START_DATE.strftime('%b %d, %Y')}",
             fontsize=9, color=TEXT_DIM, fontfamily="monospace")

    fig.savefig(output_path, facecolor=BG, edgecolor="none")
    plt.close(fig)
    return output_path


def set_wallpaper(image_path: str | Path):
    """Set the Windows desktop wallpaper to the given image."""
    path = str(Path(image_path).resolve())
    SPI_SETDESKWALLPAPER = 0x0014
    SPIF_UPDATEINIFILE = 0x01
    SPIF_SENDCHANGE = 0x02
    ctypes.windll.user32.SystemParametersInfoW(
        SPI_SETDESKWALLPAPER, 0, path,
        SPIF_UPDATEINIFILE | SPIF_SENDCHANGE,
    )
