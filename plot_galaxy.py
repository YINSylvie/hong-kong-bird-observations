# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "numpy", "pillow"]
# ///

"""Turn HKO 2024 best-track data into an artistic cyclone galaxy poster.

Run with:
    uv run plot_galaxy.py

No arguments and no internet connection are required.  Put HKO2024BST.csv in
data/ beside this script's repository.  The original attached path is used as a
fallback on the author's computer.  Output: out/hko2024_cyclone_galaxy.png.
"""

from __future__ import annotations

import csv
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


HERE = Path(__file__).resolve().parent
CSV_CANDIDATES = (
    HERE / "data" / "HKO2024BST.csv",
    HERE / "HKO2024BST.csv",
    Path(r"G:\polyu\SD5913\数据可视化\HKO2024BST.csv"),
)
OUT_DIR = HERE / "out"

PAPER = "#05090B"
INK = "#E8F7F3"
MUTED = "#75918E"
GRID = "#18312F"
COLORS = {
    "TD": "#62D9E8",
    "TS": "#48AEE8",
    "STS": "#7772F2",
    "T": "#C95CE4",
    "ST": "#F05A9D",
    "SuperT": "#FFB347",
}
INTENSITY_ORDER = ("TD", "TS", "STS", "T", "ST", "SuperT")


def locate_csv() -> Path:
    """Locate the cached raw dataset without using command-line arguments."""
    for candidate in CSV_CANDIDATES:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("Place HKO2024BST.csv in data/ and run the script again.")


def load_storms(path: Path) -> list[dict]:
    """Read the multilingual CSV and summarise observations by HKO track code."""
    grouped: dict[str, list[dict]] = defaultdict(list)
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for _ in range(3):
            next(handle)
        reader = csv.reader(handle)
        next(reader)
        for row in reader:  # marker: explicit loop over the source numbers
            grouped[row[11]].append(
                {
                    "name": row[0] if row[0] != "nameless" else f"UNNAMED-{row[11]}",
                    "time": datetime(int(row[1]), int(row[2]), int(row[3]), int(row[4])),
                    "intensity": row[5],
                    "lat": int(row[6]) / 100,
                    "lon": int(row[7]) / 100,
                    "pressure": int(row[8]),
                    "wind": int(row[9]),
                }
            )

    storms = []
    for code, observations in grouped.items():
        observations.sort(key=lambda item: item["time"])
        peak = max(observations, key=lambda item: item["wind"])
        storms.append(
            {
                "code": code,
                "name": observations[0]["name"],
                "start": observations[0]["time"],
                "end": observations[-1]["time"],
                "start_lon": observations[0]["lon"],
                "peak_wind": peak["wind"],
                "peak_pressure": min(item["pressure"] for item in observations),
                "peak_intensity": peak["intensity"],
                "records": len(observations),
            }
        )
    return sorted(storms, key=lambda storm: storm["start"])


def particle_cloud(
    ax,
    x: float,
    y: float,
    radius: float,
    count: int,
    color: str,
    seed: int,
) -> None:
    """Draw a deterministic luminous particle halo for one cyclone."""
    rng = np.random.default_rng(seed)
    theta = rng.uniform(0, math.tau, count)
    # A dense core plus a ring-like shell, inspired by storm circulation.
    shell = rng.random(count) < 0.68
    radial = np.empty(count)
    radial[shell] = np.clip(rng.normal(0.73, 0.16, shell.sum()), 0.12, 1.18)
    radial[~shell] = np.sqrt(rng.random((~shell).sum())) * 0.68
    jitter_x = np.cos(theta) * radial * radius
    jitter_y = np.sin(theta) * radial * radius
    sizes = rng.uniform(0.35, 1.9, count)
    ax.scatter(x + jitter_x, y + jitter_y, s=sizes, c=color, alpha=0.48,
               linewidths=0, zorder=6)
    # Crisp inner ring: a second layer gives the luminous, screen-printed feel.
    ring_theta = np.linspace(0, math.tau, max(36, count // 7), endpoint=False)
    ring_noise = rng.normal(1.0, 0.035, len(ring_theta))
    ax.scatter(x + np.cos(ring_theta) * radius * 0.43 * ring_noise,
               y + np.sin(ring_theta) * radius * 0.43 * ring_noise,
               s=0.9, c=INK, alpha=0.48, linewidths=0, zorder=7)


def storm_position(storm: dict) -> tuple[float, float, float]:
    """Map start date to angle and starting longitude to orbital distance."""
    year_start = datetime(2024, 1, 1)
    day = (storm["start"] - year_start).total_seconds() / 86400
    angle = -math.pi / 2 + day / 366 * math.tau
    longitude_fraction = (storm["start_lon"] - 104.0) / (179.5 - 104.0)
    orbit = 0.43 + np.clip(longitude_fraction, 0, 1) * 0.39
    return math.cos(angle) * orbit, math.sin(angle) * orbit, angle


def draw_poster(storms: list[dict], output_path: Path) -> None:
    """Compose the complete data-driven cyclone galaxy poster."""
    fig = plt.figure(figsize=(12, 16), dpi=150, facecolor=PAPER)
    ax = fig.add_axes([0.055, 0.19, 0.89, 0.69], facecolor=PAPER)
    ax.set_xlim(-1.14, 1.14)
    ax.set_ylim(-1.18, 1.18)
    ax.set_aspect("equal")
    ax.axis("off")

    # Deterministic background dust is decorative and deliberately very quiet.
    rng = np.random.default_rng(5913)
    dust_x = rng.uniform(-1.12, 1.12, 620)
    dust_y = rng.uniform(-1.15, 1.15, 620)
    ax.scatter(dust_x, dust_y, s=rng.uniform(0.08, 0.65, 620), c="#7AD8CB",
               alpha=0.12, linewidths=0, zorder=0)

    # Calendar and longitude orbits form the structural scaffold.
    for radius in (0.43, 0.56, 0.69, 0.82):
        ax.add_patch(plt.Circle((0, 0), radius, fill=False, color=GRID,
                                linewidth=0.72, linestyle=(0, (2, 6)), zorder=1))

    year_start = datetime(2024, 1, 1)
    for month in range(1, 13):
        moment = datetime(2024, month, 1)
        day = (moment - year_start).total_seconds() / 86400
        angle = -math.pi / 2 + day / 366 * math.tau
        x1, y1 = math.cos(angle) * 0.37, math.sin(angle) * 0.37
        x2, y2 = math.cos(angle) * 0.91, math.sin(angle) * 0.91
        ax.plot([x1, x2], [y1, y2], color=GRID, linewidth=0.65,
                linestyle=(0, (1, 7)), zorder=1)
        lx, ly = math.cos(angle) * 0.96, math.sin(angle) * 0.96
        ax.text(lx, ly, moment.strftime("%b").upper(), color=MUTED, fontsize=7,
                ha="center", va="center", family="monospace", zorder=10)

    # Central season core.
    ax.add_patch(plt.Circle((0, 0), 0.29, color="#071716", ec="#2D6660", lw=0.8, zorder=2))
    for radius, alpha in ((0.25, 0.25), (0.19, 0.34), (0.12, 0.46)):
        ax.add_patch(plt.Circle((0, 0), radius, fill=False, color="#50D1BF",
                                linewidth=0.7, alpha=alpha, zorder=3))
    ax.text(0, 0.035, "2024", color=INK, fontsize=24, fontweight="bold",
            ha="center", va="center", family="monospace", zorder=10)
    ax.text(0, -0.038, "29 CYCLONE TRACKS", color="#72BFB4", fontsize=7.5,
            ha="center", va="center", family="monospace", zorder=10)
    ax.text(0, -0.078, "652 OBSERVATIONS", color=MUTED, fontsize=6.5,
            ha="center", va="center", family="monospace", zorder=10)

    strongest_names = {storm["name"] for storm in sorted(
        storms, key=lambda item: item["peak_wind"], reverse=True
    )[:9]}

    for storm_index, storm in enumerate(storms):  # marker: loop over visualised data
        x, y, angle = storm_position(storm)
        radius = 0.020 + math.sqrt(storm["peak_wind"]) * 0.0092
        color = COLORS.get(storm["peak_intensity"], COLORS["TD"])
        particle_count = 65 + storm["records"] * 20

        # Dotted umbilical line connects date/longitude position to the season core.
        start_radius = 0.30
        end_radius = math.hypot(x, y) - radius * 0.72
        dots = max(6, int((end_radius - start_radius) * 55))
        line_r = np.linspace(start_radius, end_radius, dots)
        ax.scatter(np.cos(angle) * line_r, np.sin(angle) * line_r,
                   s=0.75, c=INK, alpha=0.43, linewidths=0, zorder=2)

        particle_cloud(ax, x, y, radius, particle_count, color,
                       seed=5913 + int(storm["code"]))
        ax.add_patch(plt.Circle((x, y), radius, fill=False, ec=color,
                                lw=0.65, alpha=0.72, zorder=8))

        if storm["name"] in strongest_names:
            label_radius = math.hypot(x, y) + radius + 0.035
            label_x, label_y = math.cos(angle) * label_radius, math.sin(angle) * label_radius
            align = "left" if math.cos(angle) >= 0 else "right"
            ax.text(label_x, label_y, f"{storm['name']}  {storm['peak_wind']} kt",
                    color=INK, fontsize=6.3, fontweight="bold", family="monospace",
                    ha=align, va="center", zorder=11)

    fig.text(0.07, 0.955, "STORMS IN ORBIT", color=INK, fontsize=31,
             fontweight="bold", family="sans-serif")
    fig.text(0.07, 0.925, "2024 WESTERN NORTH PACIFIC CYCLONE FIELD", color="#5DE0CE",
             fontsize=11, fontweight="bold", family="monospace")
    fig.text(0.07, 0.899,
             "angle = formation date   ·   orbit = starting longitude   ·   area = peak wind\n"
             "particle density = observations   ·   colour = peak intensity",
             color=MUTED, fontsize=8.2, family="monospace", linespacing=1.6)

    # Intensity legend.
    legend_y = 0.145
    fig.text(0.07, legend_y + 0.055, "PEAK INTENSITY", color=INK, fontsize=8.5,
             fontweight="bold", family="monospace")
    for index, intensity in enumerate(INTENSITY_ORDER):
        x = 0.07 + index * 0.093
        fig.add_artist(plt.Circle((x, legend_y + 0.025), 0.0065,
                                  transform=fig.transFigure, color=COLORS[intensity]))
        fig.text(x + 0.012, legend_y + 0.021, intensity.upper(), color=MUTED,
                 fontsize=6.5, family="monospace")

    # Mini-chart: strongest storms occupy the high-wind, low-pressure corner.
    inset = fig.add_axes([0.61, 0.045, 0.32, 0.14], facecolor=PAPER)
    for storm in storms:
        inset.scatter(storm["peak_wind"], storm["peak_pressure"],
                      s=12 + storm["records"] * 0.8,
                      color=COLORS.get(storm["peak_intensity"], COLORS["TD"]),
                      alpha=0.78, linewidths=0)
    inset.set_xlim(20, 130)
    inset.set_ylim(1010, 905)
    inset.set_title("WIND ↑  /  PRESSURE ↓", loc="left", color=INK,
                    fontsize=7.5, fontweight="bold", family="monospace", pad=8)
    inset.set_xlabel("PEAK WIND · KNOTS", color=MUTED, fontsize=6, family="monospace")
    inset.set_ylabel("MIN PRESSURE · HPA", color=MUTED, fontsize=6, family="monospace")
    inset.grid(color=GRID, linewidth=0.5, linestyle=(0, (2, 5)))
    inset.tick_params(colors=MUTED, labelsize=5.5, length=0)
    for spine in inset.spines.values():
        spine.set_color(GRID)
        spine.set_linewidth(0.65)

    fig.text(0.07, 0.035,
             "HKO 2024 BEST TRACK DATA (POST ANALYSIS)  ·  STATIC POSTER  ·  DETERMINISTIC PARTICLES",
             color="#466D68", fontsize=6.4, family="monospace")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, facecolor=PAPER, bbox_inches="tight", pad_inches=0.16)
    plt.close(fig)


def main() -> None:
    storms = load_storms(locate_csv())
    output = OUT_DIR / "hko2024_cyclone_galaxy.png"
    draw_poster(storms, output)
    print(f"Created: {output}")
    print(f"Storms: {len(storms)}")


if __name__ == "__main__":
    main()
