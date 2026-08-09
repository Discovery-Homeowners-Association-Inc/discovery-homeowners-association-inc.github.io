"""Render an SVG street map of Discovery from OpenStreetMap vector data.

Not a tile screenshot: the geometry is drawn directly, so the map carries the
site's own palette via CSS classes (which means it follows dark mode), weighs a
few KB, and makes no request to any third party at runtime.

Data © OpenStreetMap contributors, ODbL.
"""

import json
import math
from pathlib import Path

ROADS = json.load(open("roads.json"))["elements"]

# Streets named for the neighborhood's theme. These are Discovery; everything
# else is context and is drawn muted.
THEME = (
    "Discovery", "Inspiration", "Revelation", "Seekers", "Adventure",
    "Curiosity", "Daring", "Dream", "Eureka", "Foresight", "Fortune",
    "Imagination", "Inovation", "Innovation", "Inquiry", "Challenge",
    "Beacon", "Successful", "Triumphant", "Prosperity", "Venture",
)

# Frame on the themed streets, then add a margin so the neighborhood is not
# jammed against the edge.
lats, lons = [], []
for e in ROADS:
    if e.get("tags", {}).get("name", "").startswith(THEME):
        for p in e.get("geometry", []):
            lats.append(p["lat"]); lons.append(p["lon"])

MARGIN = 0.0016
min_lat, max_lat = min(lats) - MARGIN, max(lats) + MARGIN
min_lon, max_lon = min(lons) - MARGIN, max(lons) + MARGIN


def merc_y(lat):
    return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


Y0, Y1 = merc_y(min_lat), merc_y(max_lat)
WIDTH = 1000.0
HEIGHT = WIDTH * (Y1 - Y0) / math.radians(max_lon - min_lon)


def project(lat, lon):
    x = (lon - min_lon) / (max_lon - min_lon) * WIDTH
    y = HEIGHT - (merc_y(lat) - Y0) / (Y1 - Y0) * HEIGHT
    return x, y


def path_d(geom):
    pts = []
    last = None
    for p in geom:
        x, y = project(p["lat"], p["lon"])
        # Round hard: sub-0.1-unit precision is invisible at any render size
        # and roughly halves the file.
        xy = (round(x, 1), round(y, 1))
        if xy != last:
            pts.append(xy)
            last = xy
    if len(pts) < 2:
        return None
    d = f"M{pts[0][0]} {pts[0][1]}"
    for x, y in pts[1:]:
        d += f"L{x} {y}"
    return d


def visible(geom):
    """Keep a way if any node falls inside the frame."""
    return any(min_lat <= p["lat"] <= max_lat and min_lon <= p["lon"] <= max_lon
               for p in geom)


layers = {"context": [], "path": [], "street": [], "theme": []}
labels = {}

for e in ROADS:
    geom = e.get("geometry", [])
    if not geom or not visible(geom):
        continue
    tags = e.get("tags", {})
    name = tags.get("name", "")
    hw = tags.get("highway")
    d = path_d(geom)
    if not d:
        continue

    if hw == "track":
        continue  # farm tracks outside the neighborhood are noise
    if hw in ("footway", "path", "steps"):
        layer = "path"
    elif name.startswith(THEME):
        layer = "theme"
    elif hw in ("primary", "secondary", "tertiary"):
        layer = "context"
    else:
        layer = "street"
    layers[layer].append(d)

    # Label themed streets once, at the midpoint of their longest segment.
    if name.startswith(THEME) and len(geom) >= 2:
        mid = geom[len(geom) // 2]
        x, y = project(mid["lat"], mid["lon"])
        y -= 7  # sit the label above the line rather than on it
        span = abs(geom[0]["lat"] - geom[-1]["lat"]) + abs(geom[0]["lon"] - geom[-1]["lon"])
        if span < 0.0004:
            continue  # a stub too short to carry a readable label
        if name not in labels or span > labels[name][2]:
            labels[name] = [round(x, 1), round(y, 1), span]

out = []
out.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH:.0f} {HEIGHT:.0f}" '
    f'class="map" role="img" aria-labelledby="map-title map-desc">'
)
out.append('<title id="map-title">Street map of the Discovery neighborhood</title>')
out.append(
    '<desc id="map-desc">The streets of Discovery in Walkersville, Maryland, '
    'highlighted against the surrounding road network. Discovery Boulevard runs '
    'through the centre, with the courts and places branching from it.</desc>'
)
out.append('<rect class="map__ground" width="100%" height="100%"/>')

for cls, key in (("map__context", "context"), ("map__path", "path"),
                 ("map__street", "street"), ("map__theme", "theme")):
    if layers[key]:
        out.append(f'<g class="{cls}" fill="none">')
        for d in layers[key]:
            out.append(f'<path d="{d}"/>')
        out.append("</g>")

out.append('<g class="map__labels">')
for name, (x, y, _span) in sorted(labels.items()):
    short = (name.replace(" Boulevard", " Blvd").replace(" Avenue", " Ave")
                 .replace(" Court", " Ct").replace(" Place", " Pl")
                 .replace(" Lane", " Ln").replace(" Walk", " Wk"))
    out.append(f'<text x="{x}" y="{y}">{short}</text>')
out.append("</g>")
out.append("</svg>")

svg = "\n".join(out)
Path("discovery-map.svg").write_text(svg)
print(f"{WIDTH:.0f}x{HEIGHT:.0f} · {len(svg)/1024:.1f} KB · "
      f"{sum(len(v) for v in layers.values())} ways · {len(labels)} labels")
