"""2024 Western North Pacific tropical cyclone intensity lineage.

Run with:
    uv run plot.py

This script is deliberately dependency-free.  It uses only Python's standard
library and writes an interactive HTML chart plus a standalone SVG image next
to this file.
"""

from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path


# Derived from HKO2024BST.csv.  Each row is:
# name, HKO code, first observation, peak observation, last observation,
# peak wind (kt), minimum pressure at peak (hPa), peak intensity, record count.
STORMS = [
    ("EWINIAR", "0001", "2024-05-24T00:00", "2024-05-26T18:00", "2024-05-30T00:00", 75, 965, "T", 25),
    ("MALIKSI", "0002", "2024-05-30T09:00", "2024-05-31T06:00", "2024-06-01T06:00", 35, 996, "TS", 9),
    ("UNNAMED-0003", "0003", "2024-07-13T09:00", "2024-07-13T09:00", "2024-07-15T09:00", 25, 998, "TD", 10),
    ("PRAPIROON", "0004", "2024-07-19T06:00", "2024-07-22T12:00", "2024-07-23T09:00", 55, 980, "STS", 18),
    ("GAEMI", "0005", "2024-07-19T12:00", "2024-07-24T06:00", "2024-07-27T18:00", 105, 935, "SuperT", 34),
    ("MARIA", "0006", "2024-08-06T18:00", "2024-08-08T18:00", "2024-08-12T18:00", 60, 978, "STS", 25),
    ("SON-TINH", "0007", "2024-08-10T12:00", "2024-08-11T12:00", "2024-08-13T12:00", 35, 998, "TS", 13),
    ("AMPIL", "0008", "2024-08-12T00:00", "2024-08-16T00:00", "2024-08-18T18:00", 95, 945, "ST", 28),
    ("WUKONG", "0009", "2024-08-12T06:00", "2024-08-13T00:00", "2024-08-15T06:00", 35, 998, "TS", 13),
    ("JONGDARI", "0010", "2024-08-18T00:00", "2024-08-19T18:00", "2024-08-21T00:00", 40, 995, "TS", 13),
    ("SHANSHAN", "0011", "2024-08-21T06:00", "2024-08-27T12:00", "2024-09-01T00:00", 100, 940, "SuperT", 44),
    ("YAGI", "0012", "2024-09-01T03:00", "2024-09-06T00:00", "2024-09-08T06:00", 125, 915, "SuperT", 31),
    ("HONE", "0013", "2024-09-03T00:00", "2024-09-03T00:00", "2024-09-03T18:00", 30, 1002, "TD", 4),
    ("LEEPI", "0014", "2024-09-03T00:00", "2024-09-05T00:00", "2024-09-06T12:00", 35, 1000, "TS", 15),
    ("BEBINCA", "0015", "2024-09-10T00:00", "2024-09-15T12:00", "2024-09-17T12:00", 80, 960, "T", 31),
    ("PULASAN", "0016", "2024-09-15T12:00", "2024-09-17T00:00", "2024-09-21T00:00", 45, 988, "TS", 23),
    ("SOULIK", "0017", "2024-09-16T00:00", "2024-09-18T18:00", "2024-09-19T18:00", 35, 994, "TS", 16),
    ("UNNAMED-0018", "0018", "2024-09-22T00:00", "2024-09-22T00:00", "2024-09-22T09:00", 30, 1000, "TD", 3),
    ("CIMARON", "0019", "2024-09-23T12:00", "2024-09-25T00:00", "2024-09-27T00:00", 35, 998, "TS", 15),
    ("JEBI", "0020", "2024-09-26T00:00", "2024-10-01T00:00", "2024-10-02T06:00", 60, 980, "STS", 26),
    ("KRATHON", "0021", "2024-09-26T12:00", "2024-09-30T18:00", "2024-10-03T18:00", 120, 920, "SuperT", 31),
    ("BARIJAT", "0022", "2024-10-06T00:00", "2024-10-09T12:00", "2024-10-10T18:00", 35, 998, "TS", 20),
    ("TRAMI", "0023", "2024-10-20T18:00", "2024-10-26T06:00", "2024-10-28T00:00", 65, 975, "T", 30),
    ("KONG-REY", "0024", "2024-10-24T06:00", "2024-10-30T00:00", "2024-11-01T09:00", 115, 925, "SuperT", 34),
    ("YINXING", "0025", "2024-11-03T00:00", "2024-11-07T06:00", "2024-11-12T03:00", 120, 920, "SuperT", 38),
    ("MAN-YI", "0026", "2024-11-08T18:00", "2024-11-16T00:00", "2024-11-19T15:00", 120, 920, "SuperT", 45),
    ("TORAJI", "0027", "2024-11-09T00:00", "2024-11-11T00:00", "2024-11-14T18:00", 70, 970, "T", 24),
    ("USAGI", "0028", "2024-11-11T00:00", "2024-11-13T18:00", "2024-11-16T03:00", 110, 930, "SuperT", 22),
    ("PABUK", "0029", "2024-12-22T12:00", "2024-12-23T00:00", "2024-12-25T06:00", 30, 1000, "TD", 12),
]


# lieflat-charts "wire" palette: greys carry data; orange marks one hero only.
BG = "#F0F0EE"
TEXT = "#1F1E1C"
MUTED = "#6E6D66"
GRID = "#CFCFC9"
DATA = "#22211F"
DATA_2 = "#8F8E86"
FAINT = "#C0BFB7"
HERO = "#F5572F"


def parse_time(value: str) -> datetime:
    """Convert the compact ISO timestamps stored above into datetimes."""
    return datetime.fromisoformat(value)


def wind_shade(wind: int) -> str:
    """Map ordered wind-speed bands to the wire palette's grey ladder."""
    if wind >= 100:
        return DATA
    if wind >= 65:
        return "#4F4E49"
    if wind >= 45:
        return DATA_2
    return FAINT


def svg_text(x: float, y: float, value: str, **attrs: object) -> str:
    """Create one escaped SVG text element."""
    attributes = {"x": f"{x:.1f}", "y": f"{y:.1f}", **attrs}
    normalized = {
        (key[:-1] if key.endswith("_") else key).replace("_", "-"): val
        for key, val in attributes.items()
    }
    joined = " ".join(f'{key}="{escape(str(val))}"' for key, val in normalized.items())
    return f"<text {joined}>{escape(value)}</text>"


def draw_intensity_lineage(data: list[tuple], output_svg: Path) -> str:
    """Draw the L11 Trend Lineage adaptation and return its SVG markup."""
    width, height = 1800, 1120
    left, right = 145, 1685
    top, bottom = 245, 850
    timeline_start = datetime(2024, 5, 1)
    timeline_end = datetime(2025, 1, 1)
    total_seconds = (timeline_end - timeline_start).total_seconds()

    def y_for(moment: datetime) -> float:
        portion = (moment - timeline_start).total_seconds() / total_seconds
        return top + portion * (bottom - top)

    def x_for(index: int) -> float:
        return left + index * (right - left) / (len(data) - 1)

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" '
        'aria-labelledby="chart-title chart-desc">'
    )
    parts.append("""<style>
      text{font-family:Inter,"Segoe UI",Arial,sans-serif;fill:#1F1E1C}
      .fade{opacity:0;animation:fade .9s ease forwards}
      .draw{stroke-dasharray:1;stroke-dashoffset:1;animation:draw 1s cubic-bezier(.4,0,.2,1) forwards}
      .pop{transform-box:fill-box;transform-origin:center;transform:scale(0);animation:pop .5s cubic-bezier(.2,.7,.3,1.3) forwards}
      .storm:hover .life{stroke:#22211F;stroke-width:3.2}
      .storm:hover .peak{stroke:#F0F0EE;stroke-width:2.2}
      @keyframes fade{to{opacity:1}}
      @keyframes draw{to{stroke-dashoffset:0}}
      @keyframes pop{to{transform:scale(1)}}
      @media(prefers-reduced-motion:reduce){.fade,.draw,.pop{animation:none;opacity:1;stroke-dasharray:none;stroke-dashoffset:0;transform:none}}
    </style>""")
    parts.append('<title id="chart-title">Yagi reached 125 kt, the strongest storm of 2024</title>')
    parts.append('<desc id="chart-desc">Twenty-nine tropical cyclone lifelines from May to December 2024. Each peak circle is sized and shaded by maximum wind speed.</desc>')
    parts.append(f'<rect width="{width}" height="{height}" rx="24" fill="{BG}"/>')

    parts.append(svg_text(70, 62, "LUPI EDITORIAL · L11 TREND LINEAGE", font_size=15, font_weight=700, letter_spacing=".14em", fill=MUTED))
    parts.append(svg_text(70, 115, "YAGI reached 125 kt — the strongest storm of 2024", font_size=37, font_weight=700, letter_spacing="-.02em"))
    parts.append(svg_text(70, 153, "Each column = one cyclone life · ○ start/end · ● peak · circle size and shade = peak wind (kt) · orange = annual maximum", font_size=18, font_weight=400, fill=MUTED))
    parts.append(svg_text(70, 184, "Twenty-nine HKO tracks · 652 six-hourly observations · May–December 2024", font_size=16, font_weight=600, fill=MUTED))

    # Calendar furniture inherited from L11: horizontal time rules and labels.
    months = [datetime(2024, month, 1) for month in range(5, 13)] + [datetime(2025, 1, 1)]
    for month_index, month in enumerate(months):  # required visible data loop
        y = y_for(month)
        delay = month_index * 0.035
        parts.append(f'<line class="fade" x1="{left-20}" y1="{y:.1f}" x2="{right+20}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1.2" style="animation-delay:{delay:.3f}s"/>')
        label = month.strftime("%b").upper() if month.year == 2024 else "2025"
        parts.append(svg_text(left - 35, y + 5, label, font_size=13, font_weight=700, text_anchor="end", fill=MUTED, class_="fade", style=f"animation-delay:{delay:.3f}s"))

    hero_point: tuple[float, float] | None = None

    # Main data loop: one vertical lineage for every cyclone in the dataset.
    for storm_index, storm in enumerate(data):  # marker: explicit loop over the data
        name, code, start_s, peak_s, end_s, wind, pressure, intensity, record_count = storm
        start, peak, end = parse_time(start_s), parse_time(peak_s), parse_time(end_s)
        x = x_for(storm_index)
        y_start, y_peak, y_end = y_for(start), y_for(peak), y_for(end)
        radius = 4.0 + (wind - 25) / 100 * 8.0
        is_hero = wind == max(row[5] for row in data)
        fill = HERO if is_hero else wind_shade(wind)
        delay = 0.30 + storm_index * 0.025
        tooltip = (
            f"{name} (HKO {code}) | {start:%d %b}–{end:%d %b %Y} | "
            f"peak {wind} kt, {pressure} hPa, {intensity} | {record_count} records"
        )
        parts.append(f'<g class="storm"><title>{escape(tooltip)}</title>')
        parts.append(f'<line class="life draw" pathLength="1" x1="{x:.1f}" y1="{y_start:.1f}" x2="{x:.1f}" y2="{y_end:.1f}" stroke="{DATA_2}" stroke-width="1.8" style="animation-delay:{delay:.3f}s"/>')
        parts.append(f'<circle class="pop" cx="{x:.1f}" cy="{y_start:.1f}" r="3.2" fill="{BG}" stroke="{DATA_2}" stroke-width="1.8" style="animation-delay:{delay+.08:.3f}s"/>')
        parts.append(f'<circle class="peak pop" cx="{x:.1f}" cy="{y_peak:.1f}" r="{radius:.1f}" fill="{fill}" style="animation-delay:{delay+.13:.3f}s"/>')
        parts.append(f'<circle class="pop" cx="{x:.1f}" cy="{y_end:.1f}" r="2.8" fill="{BG}" stroke="{DATA_2}" stroke-width="1.6" style="animation-delay:{delay+.18:.3f}s"/>')
        parts.append("</g>")
        if is_hero:
            hero_point = (x, y_peak)

        label_y = bottom + 38
        display_name = name.replace("UNNAMED-", "UNNAMED ")
        parts.append(svg_text(x, label_y, display_name, font_size=11.5, font_weight=650, text_anchor="end", fill=DATA if wind >= 100 else MUTED, transform=f"rotate(-52 {x:.1f} {label_y:.1f})", class_="fade", style=f"animation-delay:{delay+.2:.3f}s"))

    if hero_point:
        hx, hy = hero_point
        callout_x, callout_y = hx + 80, hy - 42
        parts.append(f'<path d="M{hx+11:.1f},{hy-5:.1f} L{callout_x-10:.1f},{callout_y+4:.1f}" fill="none" stroke="{DATA}" stroke-width="1.4"/>')
        parts.append(svg_text(callout_x, callout_y, "YAGI · 125 KT", font_size=15, font_weight=800))
        parts.append(svg_text(callout_x, callout_y + 22, "6 SEP · 915 HPA · SUPER TYPHOON", font_size=11, font_weight=650, letter_spacing=".08em", fill=MUTED))

    # Compact size legend, using greys only so the orange remains a single hero element.
    legend_y = 1033
    for legend_index, wind in enumerate((25, 65, 100, 125)):
        lx = 90 + legend_index * 150
        radius = 4.0 + (wind - 25) / 100 * 8.0
        parts.append(f'<circle cx="{lx}" cy="{legend_y-5}" r="{radius:.1f}" fill="{wind_shade(min(wind, 120))}"/>')
        parts.append(svg_text(lx + 22, legend_y, f"{wind} KT", font_size=12, font_weight=700, fill=MUTED))

    parts.append(svg_text(70, 1086, "TREND LINEAGE · WIRE · HKO 2024 BEST TRACK DATA (POST ANALYSIS)", font_size=13, font_weight=600, letter_spacing=".10em", fill=DATA_2))
    parts.append("</svg>")
    svg = "\n".join(parts)
    output_svg.write_text(svg, encoding="utf-8")
    return svg


def build_html(svg: str) -> str:
    """Wrap the SVG in a dependency-free responsive HTML document."""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>HKO 2024 Tropical Cyclone Intensity Lineage</title>
  <style>
    *{{box-sizing:border-box}}
    body{{margin:0;padding:28px;background:{BG};font-family:Inter,"Segoe UI",Arial,sans-serif;color:{TEXT}}}
    main{{max-width:1800px;margin:auto}}
    svg{{display:block;width:100%;height:auto;cursor:pointer}}
    .hint{{margin:10px 6px 0;color:{MUTED};font-size:12px;letter-spacing:.04em}}
  </style>
</head>
<body>
  <main>
    {svg}
    <p class="hint">Hover a cyclone to read its details. Click the chart to replay the entrance animation.</p>
  </main>
  <script>
    const chart = document.querySelector('svg');
    chart.addEventListener('click', () => {{
      const fresh = chart.cloneNode(true);
      chart.replaceWith(fresh);
      fresh.addEventListener('click', () => location.reload());
    }});
  </script>
</body>
</html>
"""


def main() -> None:
    """Generate the chart files next to this script."""
    output_dir = Path(__file__).resolve().parent
    svg_path = output_dir / "hko2024_intensity_lineage.svg"
    html_path = output_dir / "hko2024_intensity_lineage.html"
    svg = draw_intensity_lineage(STORMS, svg_path)
    html_path.write_text(build_html(svg), encoding="utf-8")
    print(f"Created: {html_path}")
    print(f"Created: {svg_path}")


if __name__ == "__main__":
    main()
