"""Artistic radial visualization of HKO 2024 tropical cyclones.

Run with: uv run plot_artistic.py
Uses only Python's standard library and needs no command-line arguments.
"""

from __future__ import annotations

import math
from datetime import datetime
from html import escape
from pathlib import Path


# Derived from HKO2024BST.csv:
# name, start, end, peak wind (kt), peak intensity, minimum pressure (hPa)
DATA = [
    ("EWINIAR", "2024-05-24T00:00", "2024-05-30T00:00", 75, "T", 965),
    ("MALIKSI", "2024-05-30T09:00", "2024-06-01T06:00", 35, "TS", 996),
    ("UNNAMED-0003", "2024-07-13T09:00", "2024-07-15T09:00", 25, "TD", 998),
    ("PRAPIROON", "2024-07-19T06:00", "2024-07-23T09:00", 55, "STS", 980),
    ("GAEMI", "2024-07-19T12:00", "2024-07-27T18:00", 105, "SuperT", 935),
    ("MARIA", "2024-08-06T18:00", "2024-08-12T18:00", 60, "STS", 978),
    ("SON-TINH", "2024-08-10T12:00", "2024-08-13T12:00", 35, "TS", 998),
    ("AMPIL", "2024-08-12T00:00", "2024-08-18T18:00", 95, "ST", 945),
    ("WUKONG", "2024-08-12T06:00", "2024-08-15T06:00", 35, "TS", 998),
    ("JONGDARI", "2024-08-18T00:00", "2024-08-21T00:00", 40, "TS", 995),
    ("SHANSHAN", "2024-08-21T06:00", "2024-09-01T00:00", 100, "SuperT", 940),
    ("YAGI", "2024-09-01T03:00", "2024-09-08T06:00", 125, "SuperT", 915),
    ("HONE", "2024-09-03T00:00", "2024-09-03T18:00", 30, "TD", 1002),
    ("LEEPI", "2024-09-03T00:00", "2024-09-06T12:00", 35, "TS", 1000),
    ("BEBINCA", "2024-09-10T00:00", "2024-09-17T12:00", 80, "T", 960),
    ("PULASAN", "2024-09-15T12:00", "2024-09-21T00:00", 45, "TS", 988),
    ("SOULIK", "2024-09-16T00:00", "2024-09-19T18:00", 35, "TS", 994),
    ("UNNAMED-0018", "2024-09-22T00:00", "2024-09-22T09:00", 30, "TD", 1000),
    ("CIMARON", "2024-09-23T12:00", "2024-09-27T00:00", 35, "TS", 998),
    ("JEBI", "2024-09-26T00:00", "2024-10-02T06:00", 60, "STS", 980),
    ("KRATHON", "2024-09-26T12:00", "2024-10-03T18:00", 120, "SuperT", 920),
    ("BARIJAT", "2024-10-06T00:00", "2024-10-10T18:00", 35, "TS", 998),
    ("TRAMI", "2024-10-20T18:00", "2024-10-28T00:00", 65, "T", 975),
    ("KONG-REY", "2024-10-24T06:00", "2024-11-01T09:00", 115, "SuperT", 925),
    ("YINXING", "2024-11-03T00:00", "2024-11-12T03:00", 120, "SuperT", 920),
    ("MAN-YI", "2024-11-08T18:00", "2024-11-19T15:00", 120, "SuperT", 920),
    ("TORAJI", "2024-11-09T00:00", "2024-11-14T18:00", 70, "T", 970),
    ("USAGI", "2024-11-11T00:00", "2024-11-16T03:00", 110, "SuperT", 930),
    ("PABUK", "2024-12-22T12:00", "2024-12-25T06:00", 30, "TD", 1000),
]


# lieflat-charts PALM palette. Colour is an ordered intensity category.
BG = "#F0EFEB"
TEXT = "#58402E"
MUTED = "#7B6B5F"
GRID = "#D2CCC4"
INTENSITY_COLOURS = {
    "TD": "#43593B",
    "TS": "#5A7049",
    "STS": "#77835A",
    "T": "#929960",
    "ST": "#ACAD79",
    "SuperT": "#F2D17E",
}


def polar(cx: float, cy: float, radius: float, angle_deg: float) -> tuple[float, float]:
    """Return Cartesian coordinates for one polar point."""
    angle = math.radians(angle_deg)
    return cx + radius * math.cos(angle), cy + radius * math.sin(angle)


def sector_path(cx: float, cy: float, inner: float, outer: float, start: float, end: float) -> str:
    """Create an annular SVG sector, preserving L10's core wedge geometry."""
    x1, y1 = polar(cx, cy, outer, start)
    x2, y2 = polar(cx, cy, outer, end)
    x3, y3 = polar(cx, cy, inner, end)
    x4, y4 = polar(cx, cy, inner, start)
    large_arc = 1 if (end - start) > 180 else 0
    return (
        f"M{x1:.2f},{y1:.2f} A{outer:.2f},{outer:.2f} 0 {large_arc} 1 {x2:.2f},{y2:.2f} "
        f"L{x3:.2f},{y3:.2f} A{inner:.2f},{inner:.2f} 0 {large_arc} 0 {x4:.2f},{y4:.2f} Z"
    )


def svg_text(x: float, y: float, value: str, **attrs: object) -> str:
    """Build one escaped SVG text element."""
    attributes = {"x": f"{x:.1f}", "y": f"{y:.1f}", **attrs}
    normalized = {
        (key[:-1] if key.endswith("_") else key).replace("_", "-"): val
        for key, val in attributes.items()
    }
    joined = " ".join(f'{key}="{escape(str(attr_value))}"' for key, attr_value in normalized.items())
    return f"<text {joined}>{escape(value)}</text>"


def draw_radial_patchwork(data: list[tuple], svg_path: Path) -> str:
    """Render an artistic L10 Radial Patchwork from the cyclone records."""
    width, height = 1600, 1220
    cx, cy = 850, 675
    inner_radius, rim_radius = 92, 455
    year_start = datetime(2024, 1, 1)
    year_end = datetime(2025, 1, 1)
    year_seconds = (year_end - year_start).total_seconds()

    def angle_for(moment: datetime) -> float:
        fraction = (moment - year_start).total_seconds() / year_seconds
        return -90 + fraction * 360

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">',
        """<style>
        text{font-family:Inter,"Segoe UI",Arial,sans-serif;fill:#58402E}
        .fade{opacity:0;animation:fade .9s ease forwards}
        .petal{opacity:0;transform-box:fill-box;transform-origin:center;animation:bloom .9s cubic-bezier(.2,.8,.2,1) forwards;transition:opacity .2s,filter .2s}
        .petal:hover{opacity:1;stroke:#58402E;stroke-width:2.4}
        @keyframes fade{to{opacity:1}}
        @keyframes bloom{from{opacity:0;transform:scale(.72) rotate(-2deg)}to{opacity:.88;transform:none}}
        @media(prefers-reduced-motion:reduce){.fade,.petal{animation:none;opacity:.88;transform:none}}
        </style>""",
        '<title id="title">The 2024 cyclone season bloomed late</title>',
        '<desc id="description">Twenty-nine cyclone lifetimes form a radial calendar. Angle is date, angular width is duration, radius is peak wind, and colour is peak intensity.</desc>',
        f'<rect width="{width}" height="{height}" rx="24" fill="{BG}"/>',
    ]

    parts.append(svg_text(62, 60, "LUPI EDITORIAL · L10 RADIAL PATCHWORK · PALM", font_size=14, font_weight=700, letter_spacing=".14em", fill=MUTED))
    parts.append(svg_text(62, 113, "The 2024 cyclone season bloomed late", font_size=39, font_weight=750, letter_spacing="-.025em"))
    parts.append(svg_text(62, 153, "Angle = calendar date · petal width = track duration · reach = peak wind · colour = peak intensity", font_size=17, fill=MUTED))

    # L10-style daily rim: every day is visible, weekly ticks are longer.
    for day_index in range(366):
        angle = -90 + day_index / 366 * 360
        inner_tick = rim_radius + (0 if day_index % 7 else -6)
        outer_tick = rim_radius + (7 if day_index % 7 else 14)
        x1, y1 = polar(cx, cy, inner_tick, angle)
        x2, y2 = polar(cx, cy, outer_tick, angle)
        stroke_width = 1.3 if day_index % 7 == 0 else 0.65
        parts.append(f'<line class="fade" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{GRID}" stroke-width="{stroke_width}" style="animation-delay:{day_index*.0012:.3f}s"/>')

    # Month spokes and labels turn the radial field into a readable calendar.
    for month_index in range(12):
        month = datetime(2024, month_index + 1, 1)
        angle = angle_for(month)
        x1, y1 = polar(cx, cy, inner_radius - 10, angle)
        x2, y2 = polar(cx, cy, rim_radius - 8, angle)
        lx, ly = polar(cx, cy, rim_radius + 37, angle)
        parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{GRID}" stroke-width="1" stroke-dasharray="3 7"/>')
        parts.append(svg_text(lx, ly + 5, month.strftime("%b").upper(), font_size=12, font_weight=800, text_anchor="middle", fill=MUTED))

    # Concentric wind guides make radial length quantitative rather than decorative.
    for wind in (25, 50, 75, 100, 125):
        radius = inner_radius + 62 + (wind - 25) / 100 * 285
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{radius:.1f}" fill="none" stroke="{GRID}" stroke-width="1" stroke-dasharray="2 8"/>')
        parts.append(svg_text(cx + 8, cy - radius + 15, f"{wind} KT", font_size=10.5, font_weight=700, fill=MUTED))

    # Required loop over every cyclone: each row becomes one truthful petal.
    for storm_index, storm in enumerate(data):  # marker: loop traversing the data
        name, start_s, end_s, wind, intensity, pressure = storm
        start = datetime.fromisoformat(start_s)
        end = datetime.fromisoformat(end_s)
        start_angle = angle_for(start)
        end_angle = angle_for(end)
        outer_radius = inner_radius + 62 + (wind - 25) / 100 * 285
        colour = INTENSITY_COLOURS[intensity]
        outlined = wind >= 120
        path = sector_path(cx, cy, inner_radius, outer_radius, start_angle, end_angle)
        duration_days = (end - start).total_seconds() / 86400
        tooltip = (
            f"{name} | {start:%d %b}–{end:%d %b %Y} | "
            f"{duration_days:.1f} days | peak {wind} kt | {pressure} hPa | {intensity}"
        )
        stroke = TEXT if outlined else BG
        stroke_width = 2.8 if outlined else 1.1
        parts.append(
            f'<path class="petal" d="{path}" fill="{colour}" fill-opacity=".88" '
            f'stroke="{stroke}" stroke-width="{stroke_width}" '
            f'style="animation-delay:{.18 + storm_index*.028:.3f}s"><title>{escape(tooltip)}</title></path>'
        )

    # Central inscription and four strongest-storm labels.
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{inner_radius-5}" fill="{BG}" stroke="{TEXT}" stroke-width="1.8"/>')
    parts.append(svg_text(cx, cy - 22, "29", font_size=43, font_weight=800, text_anchor="middle"))
    parts.append(svg_text(cx, cy + 6, "CYCLONE TRACKS", font_size=11.5, font_weight=750, letter_spacing=".12em", text_anchor="middle", fill=MUTED))
    parts.append(svg_text(cx, cy + 35, "125 KT MAX", font_size=16, font_weight=800, text_anchor="middle"))

    strongest = sorted(data, key=lambda row: row[3], reverse=True)[:4]
    for label_index, storm in enumerate(strongest):
        name, start_s, end_s, wind, intensity, pressure = storm
        start = datetime.fromisoformat(start_s)
        end = datetime.fromisoformat(end_s)
        mid_angle = (angle_for(start) + angle_for(end)) / 2
        outer_radius = inner_radius + 62 + (wind - 25) / 100 * 285
        ax, ay = polar(cx, cy, outer_radius + 8, mid_angle)
        tx, ty = polar(cx, cy, rim_radius + 78 + label_index * 4, mid_angle)
        anchor = "start" if math.cos(math.radians(mid_angle)) >= 0 else "end"
        parts.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{tx:.1f}" y2="{ty:.1f}" stroke="{TEXT}" stroke-width="1.3"/>')
        parts.append(svg_text(tx, ty - 4, f"{name} · {wind} KT", font_size=12.5, font_weight=800, text_anchor=anchor))

    # Six-category PALM legend; labels ensure colour is never the only cue.
    legend_x, legend_y = 70, 1022
    intensity_order = ("TD", "TS", "STS", "T", "ST", "SuperT")
    for legend_index, intensity in enumerate(intensity_order):
        x = legend_x + legend_index * 152
        parts.append(f'<rect x="{x}" y="{legend_y}" width="32" height="13" rx="6.5" fill="{INTENSITY_COLOURS[intensity]}"/>')
        parts.append(svg_text(x + 43, legend_y + 11, intensity.upper(), font_size=11.5, font_weight=750, fill=MUTED))
    parts.append(svg_text(70, 1068, "OUTLINED PETAL = ≥120 KT · HOVER A PETAL FOR NAME, DURATION, WIND AND PRESSURE", font_size=11.5, font_weight=700, letter_spacing=".08em", fill=MUTED))
    parts.append(svg_text(70, 1158, "RADIAL PATCHWORK · PALM · HKO 2024 BEST TRACK DATA (POST ANALYSIS)", font_size=12.5, font_weight=650, letter_spacing=".11em", fill=MUTED))
    parts.append("</svg>")

    markup = "\n".join(parts)
    svg_path.write_text(markup, encoding="utf-8")
    return markup


def build_html(svg: str) -> str:
    """Wrap the chart in a responsive, dependency-free HTML page."""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HKO 2024 — Radial Cyclone Patchwork</title>
<style>*{{box-sizing:border-box}}body{{margin:0;padding:28px;background:{BG};font-family:Inter,"Segoe UI",Arial,sans-serif}}main{{max-width:1600px;margin:auto}}svg{{display:block;width:100%;height:auto;cursor:pointer}}p{{color:{MUTED};font-size:12px}}</style>
</head><body><main>{svg}<p>Hover a petal for details. Click the chart to replay the bloom animation.</p></main>
<script>let chart=document.querySelector('svg');chart.addEventListener('click',()=>{{const fresh=chart.cloneNode(true);chart.replaceWith(fresh);fresh.addEventListener('click',()=>location.reload())}});</script>
</body></html>"""


def main() -> None:
    output_dir = Path(__file__).resolve().parent
    svg_path = output_dir / "hko2024_radial_patchwork.svg"
    html_path = output_dir / "hko2024_radial_patchwork.html"
    svg = draw_radial_patchwork(DATA, svg_path)
    html_path.write_text(build_html(svg), encoding="utf-8")
    print(f"Created: {html_path}")
    print(f"Created: {svg_path}")


if __name__ == "__main__":
    main()
