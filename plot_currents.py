# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "pillow"]
# ///

"""Animated HKO 2024 cyclone tracks in the visual language of currents.webp.

Run with: uv run plot_currents_style.py

The CSV should be beside this file as HKO2024BST.csv.  On the author's machine
the original attached-file path is also tried automatically.  No command-line
arguments are needed.  Outputs: hko2024_currents.png and .webp.
"""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap, Normalize


PAPER = "#faf8f4"
INK = "#1d1d1b"
WATER = "#2a6f7f"
FAST = "#d6591d"
RAMP = [WATER, "#8fb3a3", "#e9a23b", FAST]
HERE = Path(__file__).resolve().parent
LOCAL_CSV = HERE / "HKO2024BST.csv"
ATTACHED_CSV = Path(r"G:\polyu\SD5913\数据可视化\HKO2024BST.csv")


def find_csv() -> Path:
    """Find the dataset without requiring a command-line argument."""
    for candidate in (LOCAL_CSV, ATTACHED_CSV):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "Place HKO2024BST.csv beside plot_currents_style.py, then run it again."
    )


def load_tracks(path: Path) -> dict[str, list[dict]]:
    """Read the HKO CSV and return time-sorted observations by HKO track code."""
    tracks: dict[str, list[dict]] = defaultdict(list)
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for _ in range(3):
            next(handle)
        reader = csv.reader(handle)
        next(reader)  # multilingual header
        for row in reader:  # marker: explicit loop traversing the source data
            when = datetime(int(row[1]), int(row[2]), int(row[3]), int(row[4]))
            name = row[0] if row[0] != "nameless" else f"UNNAMED-{row[11]}"
            tracks[row[11]].append(
                {
                    "name": name,
                    "time": when,
                    "lat": int(row[6]) / 100,
                    "lon": int(row[7]) / 100,
                    "pressure": int(row[8]),
                    "wind": int(row[9]),
                }
            )
    for observations in tracks.values():
        observations.sort(key=lambda item: item["time"])
    return dict(tracks)


def movement_vector(first: dict, second: dict) -> tuple[float, float]:
    """Turn two geographic observations into an east/north movement vector."""
    mean_latitude = math.radians((first["lat"] + second["lat"]) / 2)
    east = (second["lon"] - first["lon"]) * math.cos(mean_latitude)
    north = second["lat"] - first["lat"]
    length = math.hypot(east, north) or 1.0
    return east / length, north / length


def setup_axes(ax) -> None:
    """Apply the paper-map treatment shared by every animation frame."""
    ax.set_facecolor(PAPER)
    ax.set_xlim(101, 182)
    ax.set_ylim(6, 48)
    ax.set_aspect(1.35)
    ax.set_xticks(range(110, 181, 10))
    ax.set_yticks(range(10, 50, 10))
    ax.grid(color="#d9d4cc", linewidth=0.65, linestyle=(0, (2, 6)), alpha=0.85)
    ax.tick_params(colors="#77736d", labelsize=8, length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xlabel("LONGITUDE °E", fontsize=8, color="#77736d", labelpad=8, family="monospace")
    ax.set_ylabel("LATITUDE °N", fontsize=8, color="#77736d", labelpad=8, family="monospace")


def draw_frame(ax, tracks: dict[str, list[dict]], cutoff: datetime, cmap, norm) -> None:
    """Draw all cyclone motion observed up to one animation timestamp."""
    ax.clear()
    setup_axes(ax)
    visible_points = 0
    strongest = None

    for track_code, observations in tracks.items():  # marker: loop over cyclone tracks
        visible = [point for point in observations if point["time"] <= cutoff]
        if not visible:
            continue
        visible_points += len(visible)
        if strongest is None or max(point["wind"] for point in visible) > strongest["wind"]:
            strongest = max(visible, key=lambda point: point["wind"])

        if len(visible) > 1:
            segments = [
                [(a["lon"], a["lat"]), (b["lon"], b["lat"])]
                for a, b in zip(visible, visible[1:])
            ]
            speeds = [b["wind"] for b in visible[1:]]
            widths = [0.45 + speed / 34 for speed in speeds]
            colors = [cmap(norm(speed)) for speed in speeds]
            ax.add_collection(
                LineCollection(segments, colors=colors, linewidths=widths, alpha=0.82, zorder=3)
            )

            # Direction arrows mirror the reference: equal length, speed as colour/weight.
            for segment_index, (a, b) in enumerate(zip(visible, visible[1:])):
                if segment_index % 2:
                    continue
                east, north = movement_vector(a, b)
                speed = b["wind"]
                ax.arrow(
                    a["lon"], a["lat"], east * 0.82, north * 0.82,
                    width=0.035 + speed / 3300,
                    head_width=0.34 + speed / 500,
                    head_length=0.40 + speed / 440,
                    length_includes_head=True,
                    color=cmap(norm(speed)), alpha=0.95, zorder=4,
                )

        latest = visible[-1]
        ax.scatter(
            latest["lon"], latest["lat"], s=12 + latest["wind"] * 0.55,
            c=[cmap(norm(latest["wind"]))], edgecolors=PAPER,
            linewidths=0.7, zorder=6,
        )

    ax.text(
        0.018, 0.975, f"{cutoff:%Y-%m-%d %H:%M UTC}",
        transform=ax.transAxes, va="top", ha="left", fontsize=14,
        family="monospace", color=INK,
        bbox=dict(boxstyle="round,pad=0.35", fc=PAPER, ec="none", alpha=0.92),
    )
    detail = f"29 HKO tracks · {visible_points} observations"
    if strongest:
        detail += f" · strongest so far: {strongest['name']} {strongest['wind']} kt"
    ax.text(0.02, 0.925, detail, transform=ax.transAxes, fontsize=8.5,
            color="#5d5a55", family="monospace", va="top")
    ax.text(0.99, 0.012, "HKO 2024 BEST TRACK DATA · arrow = motion · colour/weight = wind",
            transform=ax.transAxes, va="bottom", ha="right", fontsize=7,
            color="#68645e", family="monospace")


def main() -> None:
    """Create a still PNG and an animated WebP with no command-line options."""
    tracks = load_tracks(find_csv())
    timeline = sorted({point["time"] for track in tracks.values() for point in track})
    # Keep the film compact: approximately one frame per 18 hours, plus the final state.
    frames = timeline[::3]
    if frames[-1] != timeline[-1]:
        frames.append(timeline[-1])

    cmap = LinearSegmentedColormap.from_list("cyclone-current", RAMP)
    norm = Normalize(vmin=20, vmax=125)
    fig, ax = plt.subplots(figsize=(12, 7.4), dpi=90)
    fig.patch.set_facecolor(PAPER)
    fig.subplots_adjust(left=0.055, right=0.985, top=0.985, bottom=0.07)

    draw_frame(ax, tracks, frames[-1], cmap, norm)
    png_path = HERE / "hko2024_currents.png"
    fig.savefig(png_path, dpi=130, facecolor=PAPER)

    def animate(frame_index: int):
        draw_frame(ax, tracks, frames[frame_index], cmap, norm)
        return (ax,)

    animation = FuncAnimation(fig, animate, frames=len(frames), interval=1000 / 12, blit=False)
    webp_path = HERE / "hko2024_currents.webp"
    animation.save(webp_path, writer=PillowWriter(fps=12), dpi=90)
    plt.close(fig)
    print(f"Created: {png_path}")
    print(f"Created: {webp_path} ({len(frames)} frames)")


if __name__ == "__main__":
    main()
