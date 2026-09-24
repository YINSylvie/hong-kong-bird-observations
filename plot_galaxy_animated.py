# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "numpy", "pillow"]
# ///

"""Animated companion to plot_galaxy.py.

Run with: uv run plot_galaxy_animated.py

No arguments or internet connection are required. Put HKO2024BST.csv in data/.
Outputs are written to out/hko2024_cyclone_galaxy.webp and .png.
"""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter


HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
CSV_CANDIDATES = (
    HERE / "data" / "HKO2024BST.csv",
    HERE / "HKO2024BST.csv",
    Path(r"G:\polyu\SD5913\数据可视化\HKO2024BST.csv"),
)

BG = "#05090B"
INK = "#E8F7F3"
MUTED = "#75918E"
GRID = "#18312F"
COLORS = {
    "TD": "#62D9E8", "TS": "#48AEE8", "STS": "#7772F2",
    "T": "#C95CE4", "ST": "#F05A9D", "SuperT": "#FFB347",
}
ORDER = ("TD", "TS", "STS", "T", "ST", "SuperT")
FPS = 12
FRAMES = 144


def locate_csv() -> Path:
    """Find the cached raw CSV without command-line input."""
    for path in CSV_CANDIDATES:
        if path.is_file():
            return path
    raise FileNotFoundError("Place HKO2024BST.csv inside data/ and run again.")


def load_storms(path: Path) -> list[dict]:
    """Parse the HKO file and create one summary dictionary per track."""
    grouped: dict[str, list[dict]] = defaultdict(list)
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for _ in range(3):
            next(handle)
        rows = csv.reader(handle)
        next(rows)
        for row in rows:  # marker: loop over the source data
            grouped[row[11]].append({
                "name": row[0] if row[0] != "nameless" else f"UNNAMED-{row[11]}",
                "time": datetime(int(row[1]), int(row[2]), int(row[3]), int(row[4])),
                "lon": int(row[7]) / 100,
                "pressure": int(row[8]),
                "wind": int(row[9]),
                "intensity": row[5],
            })

    storms = []
    for code, observations in grouped.items():
        observations.sort(key=lambda item: item["time"])
        peak = max(observations, key=lambda item: item["wind"])
        storms.append({
            "code": code,
            "name": observations[0]["name"],
            "start": observations[0]["time"],
            "start_lon": observations[0]["lon"],
            "wind": peak["wind"],
            "pressure": min(item["pressure"] for item in observations),
            "intensity": peak["intensity"],
            "records": len(observations),
        })
    return sorted(storms, key=lambda item: item["start"])


def storm_position(storm: dict) -> tuple[float, float, float]:
    """Map formation date to angle and starting longitude to orbit radius."""
    day = (storm["start"] - datetime(2024, 1, 1)).total_seconds() / 86400
    angle = -math.pi / 2 + day / 366 * math.tau
    longitude_fraction = np.clip((storm["start_lon"] - 104) / 75.5, 0, 1)
    orbit = 0.43 + longitude_fraction * 0.39
    return math.cos(angle) * orbit, math.sin(angle) * orbit, angle


def make_cloud(count: int, seed: int) -> np.ndarray:
    """Create deterministic unit-circle particles with a core and shell."""
    rng = np.random.default_rng(seed)
    theta = rng.uniform(0, math.tau, count)
    shell = rng.random(count) < 0.68
    radius = np.empty(count)
    radius[shell] = np.clip(rng.normal(0.73, 0.16, shell.sum()), 0.12, 1.18)
    radius[~shell] = np.sqrt(rng.random((~shell).sum())) * 0.68
    return np.column_stack((np.cos(theta) * radius, np.sin(theta) * radius))


def ease_out(value: float) -> float:
    """Fast-in, slow-out bloom used when a storm first appears."""
    value = float(np.clip(value, 0, 1))
    return 1 - (1 - value) ** 4


def build_animation(storms: list[dict]):
    """Build the poster and return its figure and frame-update function."""
    fig = plt.figure(figsize=(7.2, 10.1), dpi=110, facecolor=BG)
    ax = fig.add_axes([0.045, 0.18, 0.91, 0.69], facecolor=BG)
    ax.set_xlim(-1.14, 1.14)
    ax.set_ylim(-1.18, 1.18)
    ax.set_aspect("equal")
    ax.axis("off")

    rng = np.random.default_rng(5913)
    ax.scatter(rng.uniform(-1.12, 1.12, 420), rng.uniform(-1.15, 1.15, 420),
               s=rng.uniform(0.08, 0.5, 420), c="#7AD8CB", alpha=0.10,
               linewidths=0, zorder=0)
    for radius in (0.43, 0.56, 0.69, 0.82):
        ax.add_patch(plt.Circle((0, 0), radius, fill=False, color=GRID,
                                linewidth=0.65, linestyle=(0, (2, 6))))

    year_start = datetime(2024, 1, 1)
    for month in range(1, 13):
        moment = datetime(2024, month, 1)
        day = (moment - year_start).total_seconds() / 86400
        angle = -math.pi / 2 + day / 366 * math.tau
        ax.plot([math.cos(angle) * 0.37, math.cos(angle) * 0.91],
                [math.sin(angle) * 0.37, math.sin(angle) * 0.91],
                color=GRID, lw=0.55, linestyle=(0, (1, 7)), zorder=1)
        ax.text(math.cos(angle) * 0.96, math.sin(angle) * 0.96,
                moment.strftime("%b").upper(), color=MUTED, fontsize=5.6,
                ha="center", va="center", family="monospace")

    pulse_rings = []
    ax.add_patch(plt.Circle((0, 0), 0.29, color="#071716", ec="#2D6660", lw=0.8))
    for radius, alpha in ((0.25, .25), (0.19, .34), (0.12, .46)):
        ring = plt.Circle((0, 0), radius, fill=False, color="#50D1BF",
                          lw=0.65, alpha=alpha, zorder=3)
        ax.add_patch(ring)
        pulse_rings.append((ring, radius, alpha))
    ax.text(0, 0.032, "2024", color=INK, fontsize=20, fontweight="bold",
            ha="center", family="monospace")
    count_text = ax.text(0, -0.038, "0 / 29 TRACKS", color="#72BFB4",
                         fontsize=6.5, ha="center", family="monospace")
    date_text = fig.text(0.07, 0.895, "", color=MUTED, fontsize=7.4,
                         family="monospace")

    fig.text(0.07, 0.957, "STORMS IN MOTION", color=INK, fontsize=25,
             fontweight="bold")
    fig.text(0.07, 0.925, "2024 WESTERN NORTH PACIFIC CYCLONE FIELD",
             color="#5DE0CE", fontsize=8.5, fontweight="bold", family="monospace")
    fig.text(0.07, 0.070,
             "angle = formation date  ·  orbit = starting longitude  ·  area = peak wind\n"
             "particles = observations  ·  colour = peak intensity",
             color=MUTED, fontsize=6.2, family="monospace", linespacing=1.5)

    # Static legend.
    fig.text(0.07, 0.145, "PEAK INTENSITY", color=INK, fontsize=7,
             fontweight="bold", family="monospace")
    for index, intensity in enumerate(ORDER):
        x = 0.07 + index * 0.137
        fig.add_artist(plt.Circle((x, 0.120), 0.007, transform=fig.transFigure,
                                  color=COLORS[intensity]))
        fig.text(x + 0.014, 0.116, intensity.upper(), color=MUTED,
                 fontsize=5.3, family="monospace")
    fig.text(0.07, 0.027, "HKO 2024 BEST TRACK DATA · 144 FRAMES · 12 FPS",
             color="#466D68", fontsize=5.4, family="monospace")

    strongest = {item["name"] for item in sorted(
        storms, key=lambda item: item["wind"], reverse=True
    )[:9]}
    artists = []

    for storm_index, storm in enumerate(storms):  # marker: loop over visualised storms
        x, y, angle = storm_position(storm)
        radius = 0.020 + math.sqrt(storm["wind"]) * 0.0092
        count = 55 + storm["records"] * 14
        cloud = make_cloud(count, 5913 + int(storm["code"]))
        sizes = np.linspace(0.35, 1.5, count)
        scatter = ax.scatter(np.full(count, x), np.full(count, y), s=sizes,
                             c=COLORS.get(storm["intensity"], COLORS["TD"]),
                             alpha=0, linewidths=0, zorder=6)
        outline = plt.Circle((x, y), 0, fill=False,
                             ec=COLORS.get(storm["intensity"], COLORS["TD"]),
                             lw=0.65, alpha=0, zorder=8)
        ax.add_patch(outline)
        connector, = ax.plot([], [], color=INK, lw=0, marker=".", markersize=1.2,
                             alpha=0, zorder=2)
        label = ax.text(x, y, "", color=INK, fontsize=5.2, fontweight="bold",
                        family="monospace", alpha=0, zorder=10)
        artists.append({
            "storm": storm, "x": x, "y": y, "angle": angle,
            "radius": radius, "cloud": cloud, "scatter": scatter,
            "outline": outline, "connector": connector, "label": label,
            "labelled": storm["name"] in strongest, "spin": -1 if storm_index % 2 else 1,
        })

    first_day = min(storm["start"] for storm in storms)
    # Leave one week after the final genesis date so the last storm can fully bloom.
    last_day = max(storm["start"] for storm in storms) + timedelta(days=7)
    span_seconds = (last_day - first_day).total_seconds()

    def update(frame_index: int):
        """Animate chronological blooming, rotation and central breathing."""
        fraction = frame_index / (FRAMES - 1)
        current = first_day.timestamp() + fraction * span_seconds
        current_date = datetime.fromtimestamp(current)
        visible_count = 0

        for storm_index, item in enumerate(artists):  # marker: animation data loop
            storm = item["storm"]
            age_days = (current_date - storm["start"]).total_seconds() / 86400
            progress = ease_out(age_days / 7.0)
            if age_days < 0:
                progress = 0
            if progress > 0:
                visible_count += 1
            breathing = 1 + 0.035 * math.sin(frame_index * 0.16 + storm_index)
            scale = item["radius"] * progress * breathing
            rotation = item["spin"] * frame_index * 0.006
            c, s = math.cos(rotation), math.sin(rotation)
            cloud = item["cloud"]
            rotated = np.column_stack((cloud[:, 0] * c - cloud[:, 1] * s,
                                       cloud[:, 0] * s + cloud[:, 1] * c))
            item["scatter"].set_offsets(rotated * scale + (item["x"], item["y"]))
            item["scatter"].set_alpha(0.48 * progress)
            item["outline"].set_radius(scale)
            item["outline"].set_alpha(0.72 * progress)

            orbit = math.hypot(item["x"], item["y"])
            end_radius = max(0.30, orbit - scale * 0.72)
            line_r = np.linspace(0.30, end_radius, max(3, int((end_radius - .30) * 44)))
            item["connector"].set_data(np.cos(item["angle"]) * line_r,
                                        np.sin(item["angle"]) * line_r)
            item["connector"].set_alpha(0.38 * progress)

            if item["labelled"] and progress > 0.75:
                label_radius = orbit + scale + 0.025
                lx = math.cos(item["angle"]) * label_radius
                ly = math.sin(item["angle"]) * label_radius
                item["label"].set_position((lx, ly))
                item["label"].set_text(f"{storm['name']}  {storm['wind']} kt")
                item["label"].set_ha("left" if math.cos(item["angle"]) >= 0 else "right")
                item["label"].set_alpha(min(1, (progress - .75) * 4))
            else:
                item["label"].set_alpha(0)

        for ring_index, (ring, base_radius, base_alpha) in enumerate(pulse_rings):
            pulse = 1 + 0.025 * math.sin(frame_index * 0.12 + ring_index * 1.7)
            ring.set_radius(base_radius * pulse)
            ring.set_alpha(base_alpha + 0.08 * math.sin(frame_index * 0.12 + ring_index))
        count_text.set_text(f"{visible_count} / 29 TRACKS")
        date_text.set_text(f"SEASON CLOCK  ·  {current_date:%d %B 2024}")
        return [count_text, date_text] + [item["scatter"] for item in artists]

    return fig, update


def main() -> None:
    storms = load_storms(locate_csv())
    OUT.mkdir(parents=True, exist_ok=True)
    fig, update = build_animation(storms)
    animation = FuncAnimation(fig, update, frames=FRAMES, interval=1000 / FPS, blit=False)
    webp_path = OUT / "hko2024_cyclone_galaxy.webp"
    animation.save(webp_path, writer=PillowWriter(fps=FPS), dpi=110)
    update(FRAMES - 1)
    png_path = OUT / "hko2024_cyclone_galaxy_final.png"
    fig.savefig(png_path, dpi=180, facecolor=BG, bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    print(f"Created: {webp_path}")
    print(f"Created: {png_path}")
    print(f"Frames: {FRAMES} at {FPS} fps")


if __name__ == "__main__":
    main()
