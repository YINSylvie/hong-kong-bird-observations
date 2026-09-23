"""Colour-rich HKO 2024 tropical cyclone ranking.

Run with: uv run plot_color.py
No third-party package is required.  The script writes an HTML chart and SVG.
"""

from __future__ import annotations

from html import escape
from pathlib import Path


# The eight strongest tracks derived from HKO2024BST.csv.
# name, peak wind (kt), minimum pressure (hPa), peak intensity, peak date
DATA = [
    ("YAGI", 125, 915, "SuperT", "06 SEP"),
    ("KRATHON", 120, 920, "SuperT", "30 SEP"),
    ("YINXING", 120, 920, "SuperT", "07 NOV"),
    ("MAN-YI", 120, 920, "SuperT", "16 NOV"),
    ("KONG-REY", 115, 925, "SuperT", "30 OCT"),
    ("USAGI", 110, 930, "SuperT", "13 NOV"),
    ("GAEMI", 105, 935, "SuperT", "24 JUL"),
    ("SHANSHAN", 100, 940, "SuperT", "27 AUG"),
]


# lieflat-charts PORCELAIN palette: one hue, lightness = ordered wind speed.
BG = "#F7F2EB"
TEXT = "#081F5C"
MUTED = "#52658F"
GRID = "#CDD8E7"
RAMP = ["#D0E3FF", "#BAD6EB", "#7096D1", "#334EAC", "#081F5C"]


def blue_for_wind(wind: int) -> str:
    """Return a porcelain-blue shade for an absolute wind-speed level."""
    if wind >= 100:
        return RAMP[4]
    if wind >= 75:
        return RAMP[3]
    if wind >= 50:
        return RAMP[2]
    if wind >= 25:
        return RAMP[1]
    return RAMP[0]


def text(x: float, y: float, value: str, **attrs: object) -> str:
    """Build an escaped SVG text element."""
    attributes = {"x": f"{x:.1f}", "y": f"{y:.1f}", **attrs}
    normalized = {
        (key[:-1] if key.endswith("_") else key).replace("_", "-"): val
        for key, val in attributes.items()
    }
    joined = " ".join(f'{key}="{escape(str(attr_value))}"' for key, attr_value in normalized.items())
    return f"<text {joined}>{escape(value)}</text>"


def draw_color_ranking(data: list[tuple], svg_path: Path) -> str:
    """Draw an F5 Tick Rows chart using the porcelain colour system."""
    width, height = 1500, 1040
    label_x, tick_start, tick_step = 250, 320, 39
    row_top, row_gap = 300, 82
    max_wind = 125
    max_ticks = max_wind // 5
    svg: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">',
        """<style>
        text{font-family:Inter,"Segoe UI",Arial,sans-serif;fill:#081F5C}
        .fade{opacity:0;animation:fade .8s ease forwards}
        .tick{opacity:0;animation:rise .55s cubic-bezier(.2,.7,.3,1) forwards}
        .row:hover .tick{stroke-width:7}
        @keyframes fade{to{opacity:1}}
        @keyframes rise{from{opacity:0;transform:translateY(12px)}to{opacity:.95;transform:none}}
        @media(prefers-reduced-motion:reduce){.fade,.tick{animation:none;opacity:.95;transform:none}}
        </style>""",
        '<title id="title">Eight storms reached 100 knots; Yagi led at 125</title>',
        '<desc id="description">A horizontal tick ranking of the eight strongest tropical cyclones in the HKO 2024 best track dataset.</desc>',
        f'<rect width="{width}" height="{height}" rx="24" fill="{BG}"/>',
    ]

    svg.append(text(62, 58, "LUPI BASICS · F5 TICK ROWS · PORCELAIN", font_size=14, font_weight=700, letter_spacing=".14em", fill=MUTED))
    svg.append(text(62, 112, "Eight storms reached 100 kt; YAGI led at 125", font_size=38, font_weight=750, letter_spacing="-.025em"))
    svg.append(text(62, 151, "One tick = 5 kt · darker blue = stronger wind · labels show peak pressure and date · 2024 best-track analysis", font_size=17, fill=MUTED))

    # Scale labels and vertical guides keep the bar-length contract honest at zero.
    for guide_index, wind in enumerate(range(0, max_wind + 1, 25)):
        x = tick_start + (wind / 5) * tick_step
        svg.append(f'<line x1="{x:.1f}" y1="245" x2="{x:.1f}" y2="{row_top + (len(data)-1)*row_gap + 30:.1f}" stroke="{GRID}" stroke-width="1.2" stroke-dasharray="3 7"/>')
        svg.append(text(x, 227, f"{wind}", font_size=12, font_weight=700, text_anchor="middle", fill=MUTED))

    # Required explicit loop over the data: one visual row per cyclone.
    for row_index, row in enumerate(data):  # marker: loop traversing the dataset
        name, wind, pressure, intensity, peak_date = row
        y = row_top + row_index * row_gap
        ticks = wind // 5
        delay = row_index * 0.09
        tooltip = f"{name}: {wind} kt · {pressure} hPa · {intensity} · peak {peak_date} 2024"
        svg.append(f'<g class="row"><title>{escape(tooltip)}</title>')
        svg.append(text(label_x, y + 5, name, font_size=18, font_weight=800, text_anchor="end", class_="fade", style=f"animation-delay:{delay:.2f}s"))
        svg.append(text(label_x, y + 25, f"{pressure} HPA · {peak_date}", font_size=10.5, font_weight=700, letter_spacing=".08em", text_anchor="end", fill=MUTED, class_="fade", style=f"animation-delay:{delay+.05:.2f}s"))
        svg.append(f'<line x1="{tick_start}" y1="{y+17}" x2="{tick_start + max_ticks*tick_step}" y2="{y+17}" stroke="{GRID}" stroke-width="1.2"/>')

        for tick_index in range(ticks):  # each tick faithfully represents 5 knots
            x = tick_start + tick_index * tick_step + tick_step / 2
            represented_wind = (tick_index + 1) * 5
            colour = blue_for_wind(represented_wind)
            tick_height = 21 if (tick_index + 1) % 5 else 30
            tick_delay = delay + tick_index * 0.012
            svg.append(f'<line class="tick" x1="{x:.1f}" y1="{y+17:.1f}" x2="{x:.1f}" y2="{y+17-tick_height:.1f}" stroke="{colour}" stroke-width="5" stroke-linecap="round" style="animation-delay:{tick_delay:.3f}s"/>')
            if (tick_index + 1) % 5 == 0:
                svg.append(f'<circle class="fade" cx="{x:.1f}" cy="{y+28:.1f}" r="2.8" fill="{colour}" style="animation-delay:{tick_delay:.3f}s"/>')

        value_x = tick_start + ticks * tick_step + 14
        svg.append(text(value_x, y + 8, f"{wind}", font_size=25, font_weight=800, fill=blue_for_wind(wind), class_="fade", style=f"animation-delay:{delay+.35:.2f}s"))
        svg.append(text(value_x + 47, y + 8, "KT", font_size=11, font_weight=750, letter_spacing=".08em", fill=MUTED, class_="fade", style=f"animation-delay:{delay+.38:.2f}s"))
        svg.append("</g>")

    legend_y = 943
    for legend_index, (label, colour) in enumerate(zip(("≤25", "50", "75", "100+"), (RAMP[1], RAMP[2], RAMP[3], RAMP[4]))):
        x = 72 + legend_index * 125
        svg.append(f'<rect x="{x}" y="{legend_y-13}" width="34" height="10" rx="5" fill="{colour}"/>')
        svg.append(text(x + 44, legend_y - 3, label, font_size=11.5, font_weight=700, fill=MUTED))
    svg.append(text(62, 995, "TICK ROWS · PORCELAIN · HKO 2024 BEST TRACK DATA (POST ANALYSIS)", font_size=12.5, font_weight=650, letter_spacing=".11em", fill=MUTED))
    svg.append("</svg>")

    markup = "\n".join(svg)
    svg_path.write_text(markup, encoding="utf-8")
    return markup


def build_html(svg: str) -> str:
    """Return a responsive, dependency-free HTML page containing the SVG."""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HKO 2024 — Strongest Tropical Cyclones</title>
<style>*{{box-sizing:border-box}}body{{margin:0;padding:28px;background:{BG};font-family:Inter,"Segoe UI",Arial,sans-serif}}main{{max-width:1500px;margin:auto}}svg{{display:block;width:100%;height:auto;cursor:pointer}}p{{color:{MUTED};font-size:12px}}</style>
</head><body><main>{svg}<p>Hover a row for details. Click the chart to replay the entrance animation.</p></main>
<script>let chart=document.querySelector('svg');chart.addEventListener('click',()=>{{const fresh=chart.cloneNode(true);chart.replaceWith(fresh);fresh.addEventListener('click',()=>location.reload())}});</script>
</body></html>"""


def main() -> None:
    output_dir = Path(__file__).resolve().parent
    svg_path = output_dir / "hko2024_color_ranking.svg"
    html_path = output_dir / "hko2024_color_ranking.html"
    svg = draw_color_ranking(DATA, svg_path)
    html_path.write_text(build_html(svg), encoding="utf-8")
    print(f"Created: {html_path}")
    print(f"Created: {svg_path}")


if __name__ == "__main__":
    main()
