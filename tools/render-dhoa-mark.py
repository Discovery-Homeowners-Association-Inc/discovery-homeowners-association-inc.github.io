"""Generate assets/brand/dhoa-mark.svg — the association's emblem.

Measured from the artwork the association publishes on its own website, a clean
467x470 rendering, rather than from the fax-quality letterhead scan an earlier
version of this script used. The two differ in ways that matter:

  * the frame is SQUARE, not portrait
  * the sun is an ARCH — a rounded-top shape standing on the ridge — not a disc
  * the ridge is a solid grey band between two outlines, not a stipple
  * the fruit are ELLIPSES, about 1.3x wider than tall, not circles

How the numbers were obtained, all from the 467x470 original:

  * fruit centroids — eroded the black-only bitmap with a disc until the trunk
    and the outlines vanished and only the fruit survived, then took
    connected-component centroids. Fourteen, in four staggered columns.
  * ridge band — column scans recording black runs and grey runs separately, so
    the two outlines could be told apart from the fill between them. The band
    is a wedge: about 14 units thick at the left, 6 at the right.
  * sun — row scans. It reads as one span at the top and splits into two legs
    below, which is an arch, not a disc.
  * trunk — row scans of its width, which grows from 1.3 units near the crown
    to 11.6 at the flared base.

Run:  python3 tools/render-dhoa-mark.py
"""

from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets/brand/dhoa-mark.svg"

S = 100 / 467                      # the original is 467 px wide
HEIGHT = round(470 * S, 2)


def p(x, y):
    return round(x * S, 2), round(y * S, 2)


# ── Measured control points, in original pixels ────────────────────────────

RIDGE_TOP = [(0, 197), (30, 184), (70, 168), (110, 153), (150, 139),
             (190, 126), (230, 117), (252, 114), (310, 131), (350, 142),
             (390, 154), (430, 167), (467, 179)]

RIDGE_BOTTOM = [(0, 266), (30, 250), (70, 234), (110, 218), (150, 203),
                (190, 192), (230, 188), (270, 187), (310, 182), (350, 179),
                (390, 184), (430, 194), (467, 205)]

# On the left the band's lower outline *is* the hillside. On the right the band
# narrows and this second line carries on down to the corner.
HILL_RIGHT = [(266, 188), (310, 205), (350, 220), (390, 234), (430, 247),
              (467, 259)]

FRUIT = [(204.9, 230.6), (274.4, 243.2), (159.9, 257.4), (205.2, 280.7),
         (319.5, 266.5), (272.8, 290.7), (159.7, 308.6), (318.2, 314.0),
         (205.0, 332.0), (272.6, 341.9), (318.0, 365.2), (158.3, 356.1),
         (203.7, 379.4), (272.8, 391.9)]
FRUIT_RX, FRUIT_RY = 23, 17.5

# Down the stem: (y, centre x, width). The first two rows are the crown, which
# leans right and tapers to a point — in the original this is continuous with
# the trunk, so it is modelled here rather than drawn as a separate flick.
TRUNK = [(193, 256, 1.5), (203, 250, 4), (215, 244, 6), (240, 240, 8),
         (280, 239, 12), (320, 240, 18), (360, 242, 25), (400, 239, 31),
         (430, 236, 42), (462, 236, 54)]

# The sun is a flared arch, not a loop: row scans show its outer span growing
# from 42 px at the crown to 66 px where it meets the ridge, so the legs splay.
# Centre-line control points, from those scans.
SUN = [(211, 122), (210, 102), (222, 88), (242, 88), (262, 88), (270, 102), (270, 122)]
SUN_STROKE = 9
BORDER = 18


def _catmull(pts):
    ext = [pts[0]] + pts + [pts[-1]]
    d = ""
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        c1 = (round(p1[0] + (p2[0] - p0[0]) / 6, 2), round(p1[1] + (p2[1] - p0[1]) / 6, 2))
        c2 = (round(p2[0] - (p3[0] - p1[0]) / 6, 2), round(p2[1] - (p3[1] - p1[1]) / 6, 2))
        d += f" C{c1[0]} {c1[1]}, {c2[0]} {c2[1]}, {p2[0]} {p2[1]}"
    return d


def path_through(points):
    """A smooth path through surveyed points — these are curves, not arcs."""
    pts = [p(*q) for q in points]
    return f"M{pts[0][0]} {pts[0][1]}" + _catmull(pts)


def band_fill():
    """The grey wedge: along the top edge, back along the bottom."""
    bottom = [p(*q) for q in reversed(RIDGE_BOTTOM)]
    return (path_through(RIDGE_TOP)
            + f" L{bottom[0][0]} {bottom[0][1]}"
            + _catmull(bottom) + " Z")


def trunk_shape():
    """A tapered trunk: down the left side, back up the right."""
    left = [p(cx - w / 2, y) for y, cx, w in TRUNK]
    right = [p(cx + w / 2, y) for y, cx, w in reversed(TRUNK)]
    d = f"M{left[0][0]} {left[0][1]}"
    for x, y in left[1:] + right:
        d += f" L{x} {y}"
    return d + " Z"


def sun_arch():
    """Up the left leg, over the crown, down the right — legs splaying out."""
    q = [p(*c) for c in SUN]
    return (f"M{q[0][0]} {q[0][1]} "
            f"C{q[1][0]} {q[1][1]}, {q[2][0]} {q[2][1]}, {q[3][0]} {q[3][1]} "
            f"C{q[4][0]} {q[4][1]}, {q[5][0]} {q[5][1]}, {q[6][0]} {q[6][1]}")


border = round(BORDER * S, 2)
inset = round(border / 2, 2)
frx, fry = round(FRUIT_RX * S, 2), round(FRUIT_RY * S, 2)

fruit = "\n".join(
    f'      <ellipse cx="{p(cx, cy)[0]}" cy="{p(cx, cy)[1]}" rx="{frx}" ry="{fry}"/>'
    for cx, cy in FRUIT)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 {HEIGHT}" class="mark"
     role="img" aria-label="Discovery Homeowners Association">
  <!--
    GENERATED by tools/render-dhoa-mark.py — edit that, not this file.

    The association's emblem: an arched sun at the crest of a ploughed ridge, a
    nearer hillside, and an orchard tree of fourteen fruit. Apt for a
    neighborhood laid out over a farm in 1972.

    Measured from the association's own 467x470 artwork. Drawn with currentColor
    so it inherits its surroundings and works in light and dark themes; the
    ridge fill is the same colour held back to 35% opacity, which reproduces the
    grey of the original against any background.
  -->
  <defs>
    <clipPath id="mark-interior">
      <rect x="{border}" y="{border}" width="{round(100 - 2 * border, 2)}"
            height="{round(HEIGHT - 2 * border, 2)}"/>
    </clipPath>
  </defs>

  <g clip-path="url(#mark-interior)">
    <!-- The ploughed ridge: a grey wedge, thick at the left, thin at the right. -->
    <path class="mark__band" d="{band_fill()}" fill="currentColor" opacity="0.35"/>

    <!-- Its two outlines. On the left the lower one is the hillside itself. -->
    <path class="mark__ridge" d="{path_through(RIDGE_TOP)}"
          fill="none" stroke="currentColor" stroke-width="1.9"
          stroke-linecap="round" stroke-linejoin="round"/>
    <path class="mark__ridge" d="{path_through(RIDGE_BOTTOM)}"
          fill="none" stroke="currentColor" stroke-width="1.9"
          stroke-linecap="round" stroke-linejoin="round"/>

    <!-- Where the band narrows, the near hillside carries on to the corner. -->
    <path class="mark__hill" d="{path_through(HILL_RIGHT)}"
          fill="none" stroke="currentColor" stroke-width="1.9"
          stroke-linecap="round" stroke-linejoin="round"/>

    <!-- The sun: an arch standing on the ridge. -->
    <path class="mark__sun" d="{sun_arch()}"
          fill="none" stroke="currentColor" stroke-width="{round(SUN_STROKE * S, 2)}"
          stroke-linejoin="round"/>

    <!-- The tree: a tapered trunk flaring into the ground. -->
    <path class="mark__trunk" d="{trunk_shape()}" fill="currentColor"/>

    <!-- Fourteen fruit, in four staggered columns. -->
    <g class="mark__fruit" fill="currentColor">
{fruit}
    </g>
  </g>

  <!-- Frame last, so it sits cleanly over anything reaching the edge. -->
  <rect class="mark__frame" x="{inset}" y="{inset}"
        width="{round(100 - border, 2)}" height="{round(HEIGHT - border, 2)}"
        fill="none" stroke="currentColor" stroke-width="{border}"/>
</svg>
'''

OUT.write_text(svg)
print(f"{OUT.name}: {len(svg)/1024:.1f} KB, {len(FRUIT)} fruit, viewBox 100 x {HEIGHT}")
