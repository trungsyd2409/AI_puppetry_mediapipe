"""Paper-cut / shadow-puppet style for the Luom game.

Look: flat pieces of hand-cut do paper and coarse fabric, earthy lacquer palette (vang dat, nau,
xanh reu, xanh luc sam, nga, do son), each piece with a light cut rim on the lit side, a darker rim
on the other, heavy grain and fibres, and a soft drop shadow so the layers read like a miniature
paper stage. Joints are round discs held by bronze rivets.
Builds on dongho_lib (brush, capsule, build, write_svg_png).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
from dongho_lib import brush, capsule, lerp, f2, bez, bez_norm  # noqa: F401

# ---------- palette (son mai / lua) ----------
SON = "#A33A27"          # do son
SON_D = "#7A2819"
SON_L = "#C2573A"
NAU = "#7B4A2A"          # nau (ao canh nau)
NAU_D = "#5A321B"
NAU_L = "#9A6539"
VANG = "#B8893A"         # vang dat
VANG_D = "#8E6527"
VANG_L = "#D7AE5A"
REU = "#6E7039"          # xanh reu
REU_D = "#50522A"
REU_L = "#8C8C4C"
LUC = "#2F4A3B"          # xanh luc sam
LUC_D = "#20352A"
LUC_L = "#4B6650"
NGA = "#E6D4AA"          # nga
NGA_D = "#C9B482"
INK = "#2A1C14"          # dark sepia (hair, eyes)
SKIN = "#E2B985"
SKIN_D = "#C4935E"
BLUSH = "#D47A5C"
BRONZE = "#A07B3A"
BRONZE_D = "#6E5122"
BRONZE_L = "#D2AE62"
EARTH = "#A9773F"
EARTH_D = "#7C5228"
SMOKE = "#8F8577"
IRON = "#4E4A42"         # enemy planes, bombs
IRON_D = "#35322C"
IRON_L = "#6E685C"

WEAVE_DEFS = (
    '<pattern id="weave" width="3.2" height="3.2" patternUnits="userSpaceOnUse">'
    '<path d="M0,0.8 H3.2 M0,2.4 H3.2" stroke="#000" stroke-opacity="0.09" stroke-width="0.7"/>'
    '<path d="M0.8,0 V3.2 M2.4,0 V3.2" stroke="#FFF" stroke-opacity="0.07" stroke-width="0.6"/>'
    '</pattern>')


def defs():
    return f"<defs>{WEAVE_DEFS}</defs>"


def mix(a, b, t):
    pa = [int(a.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    pb = [int(b.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    return "#%02X%02X%02X" % tuple(int(x + (y - x) * t) for x, y in zip(pa, pb))


def darker(hex_col, k=0.78):
    h = hex_col.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02X%02X%02X" % (int(r * k), int(g * k), int(b * k))


def lighter(hex_col, t=0.25):
    return mix(hex_col, "#F4E6C4", t)


# ---------- drawing helpers ----------
def cut(d, fill, edge=None, w=0.9, cloth=False):
    """A flat piece of cut paper / cloth. cloth=True adds a fine weave."""
    out = f'<path d="{d}" fill="{fill}"/>'
    if cloth:
        out += f'<path d="{d}" fill="url(#weave)"/>'
    if w:
        out += brush(d, w, edge or darker(fill, 0.72), taper=0, var=0.2)
    return out


def incise(d, w=1.4, base=NAU, depth=0.7):
    """A line pressed / cut into the paper: dark groove with a light lip below-right."""
    return (f'<g transform="translate({depth},{depth})">{brush(d, w * 0.8, lighter(base, 0.45), taper=0.35, var=0.2)}</g>'
            + brush(d, w, darker(base, 0.6), taper=0.35, var=0.2))


def thin(d, w=1.2, color=INK):
    return brush(d, w, color, taper=0.3, var=0.2)


def facet(pts, fill):
    """One flat facet of a fold (no edge line, the fold reads from the colour step)."""
    return f'<path d="M{" L".join(f2(p) for p in pts)} Z" fill="{fill}"/>'


def rivet(x, y, r=3.6):
    """Bronze rivet holding a joint."""
    return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r + 1.1:.1f}" fill="{BRONZE_D}"/>'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{BRONZE}"/>'
            f'<circle cx="{x - r * 0.3:.1f}" cy="{y - r * 0.32:.1f}" r="{r * 0.38:.1f}" fill="{BRONZE_L}"/>')


def disc(x, y, r, fill, ring=True):
    """Round joint disc at the top of a limb piece, with an incised ring and a rivet."""
    out = f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}"/>'
    out += brush(f"M{x - r:.1f},{y:.1f} A{r:.1f},{r:.1f} 0 1 1 {x + r:.1f},{y:.1f} A{r:.1f},{r:.1f} 0 1 1 {x - r:.1f},{y:.1f} Z",
                 0.9, darker(fill, 0.7), taper=0, var=0.15)
    if ring:
        rr = r * 0.66
        out += incise(f"M{x - rr:.1f},{y:.1f} A{rr:.1f},{rr:.1f} 0 1 1 {x + rr:.1f},{y:.1f} A{rr:.1f},{rr:.1f} 0 1 1 {x - rr:.1f},{y:.1f}",
                      1.0, fill, 0.5)
    out += rivet(x, y, max(2.6, r * 0.3))
    return out


def punch_row(p1, p2, n, r=1.6, fill=None, shape="dot"):
    """Row of punched holes / little cut-outs along a line (shadow-puppet perforation)."""
    out = ""
    for i in range(n):
        t = (i + 0.5) / n
        x, y = lerp(p1, p2, t)
        if shape == "dot":
            out += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}"/>'
        else:   # small diamond
            out += f'<path d="M{x:.1f},{y - r * 1.4:.1f} L{x + r:.1f},{y:.1f} L{x:.1f},{y + r * 1.4:.1f} L{x - r:.1f},{y:.1f} Z" fill="{fill}"/>'
    return out


def spiral_d(cx, cy, r, turns=1.75, a0=0.0, flip=1, n=40):
    """Archimedean spiral path from outside in (cloud / wave / flame curls)."""
    pts = []
    for i in range(n + 1):
        t = i / n
        a = a0 + flip * t * turns * 2 * math.pi
        rr = r * (1 - t * 0.85)
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    return "M" + " L".join(f2(p) for p in pts)


def star_d(cx, cy, r, k=0.42, n=5, rot=-90):
    pts = []
    for i in range(2 * n):
        a = math.radians(rot) + i * math.pi / n
        rr = r if i % 2 == 0 else r * k
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    return "M" + " L".join(f2(p) for p in pts) + " Z"


def circle_d(x, y, r):
    return f"M{x - r:.1f},{y:.1f} A{r:.1f},{r:.1f} 0 1 1 {x + r:.1f},{y:.1f} A{r:.1f},{r:.1f} 0 1 1 {x - r:.1f},{y:.1f} Z"


# ---------- folk motifs ----------
def scroll_cloud(s=1.0, fill=NGA, seed=1, lobes=None):
    """May cuon: a band of round lobes ending in curls, incised spirals inside (origin = centre)."""
    rnd = random.Random(seed)
    lobes = lobes or [(-62, 6, 22), (-34, -12, 28), (0, -20, 32), (34, -10, 27), (62, 6, 21), (-20, 12, 22), (22, 12, 22)]
    body = ""
    inner = ""
    for (x, y, r) in lobes:
        x, y, r = x * s, y * s, r * s
        body += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}"/>'
    # flat underside
    body += f'<path d="M{-80 * s:.1f},{14 * s:.1f} C{-60 * s:.1f},{30 * s:.1f} {60 * s:.1f},{30 * s:.1f} {80 * s:.1f},{14 * s:.1f} L{70 * s:.1f},{26 * s:.1f} L{-70 * s:.1f},{26 * s:.1f} Z" fill="{fill}"/>'
    # the two curling tails
    for side in (-1, 1):
        cx, cy = side * 84 * s, 4 * s
        body += f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{12 * s:.1f}" fill="{fill}"/>'
        inner += incise(spiral_d(cx, cy, 10 * s, 1.6, math.pi if side > 0 else 0, side), 1.3, fill, 0.6)
    for (x, y, r) in lobes[:5]:
        x, y, r = x * s, y * s, r * s
        inner += incise(spiral_d(x + rnd.uniform(-2, 2), y + r * 0.1, r * 0.62, 1.35, math.pi * 0.9, 1), 1.2, fill, 0.6)
    return body + inner


def flame_tongue(x, y, L, a_deg, w, fill, curl=1):
    """One curling flame tongue (for the sun / explosions)."""
    a = math.radians(a_deg)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    tip = (x + ux * L + nx * L * 0.25 * curl, y + uy * L + ny * L * 0.25 * curl)
    p1 = (x + nx * w, y + ny * w)
    p2 = (x - nx * w, y - ny * w)
    c1 = (x + ux * L * 0.5 + nx * w * 1.3, y + uy * L * 0.5 + ny * w * 1.3)
    c2 = (x + ux * L * 0.6 - nx * w * 0.2, y + uy * L * 0.6 - ny * w * 0.2)
    d = (f"M{f2(p1)} Q{f2(c1)} {f2(tip)} Q{f2(c2)} {f2(p2)} Z")
    return f'<path d="{d}" fill="{fill}"/>'


def drum_sun(R=100, rays=14, outer=SON, mid=VANG, core=VANG_L, flames=True, ring_col=NAU):
    """Bronze-drum sun: a many-pointed star in a disc, rings of dots and zigzags, flame curls outside."""
    out = ""
    if flames:
        for i in range(rays * 2):
            a = i * 360 / (rays * 2)
            r0 = R * 0.92
            x, y = math.cos(math.radians(a)) * r0, math.sin(math.radians(a)) * r0
            out += flame_tongue(x, y, R * (0.42 if i % 2 == 0 else 0.3), a, R * 0.09, outer, 1)
        for i in range(rays * 2):
            a = i * 360 / (rays * 2) + 6
            x, y = math.cos(math.radians(a)) * R * 0.98, math.sin(math.radians(a)) * R * 0.98
            out += incise(spiral_d(x * 1.12, y * 1.12, R * 0.07, 1.4, math.radians(a), 1), 1.0, outer, 0.5)
    out += f'<circle r="{R:.1f}" fill="{mid}"/>'
    out += f'<circle r="{R * 0.86:.1f}" fill="{ring_col}"/>'
    # ring of dots
    for i in range(36):
        a = math.radians(i * 10)
        out += f'<circle cx="{math.cos(a) * R * 0.93:.1f}" cy="{math.sin(a) * R * 0.93:.1f}" r="{R * 0.025:.1f}" fill="{darker(mid, 0.6)}"/>'
    out += f'<circle r="{R * 0.8:.1f}" fill="{mid}"/>'
    # zigzag ring
    zz = []
    for i in range(49):
        a = math.radians(i * 7.5)
        rr = R * (0.74 if i % 2 else 0.66)
        zz.append((math.cos(a) * rr, math.sin(a) * rr))
    out += incise("M" + " L".join(f2(p) for p in zz), 1.3, mid, 0.6)
    out += f'<circle r="{R * 0.6:.1f}" fill="{core}"/>'
    out += f'<path d="{star_d(0, 0, R * 0.56, 0.3, rays)}" fill="{outer}"/>'
    out += f'<circle r="{R * 0.16:.1f}" fill="{core}"/>'
    out += incise(circle_d(0, 0, R * 0.11), 1.0, core, 0.5)
    return out


def wave_band(x0, x1, y, h, fill, line_col=None, rows=2, period=60, seed=3):
    """Song nuoc: rows of scallops with concentric arcs and a few curling crests (tiles if x1-x0 % period == 0)."""
    out = ""
    line_col = line_col or fill
    for r in range(rows):
        yy = y + r * h * 0.55
        off = (period / 2) * (r % 2)
        x = x0 - period + off
        while x < x1 + period:
            cx = x + period / 2
            R = period / 2
            d = f"M{x:.1f},{yy + h:.1f} A{R:.1f},{R:.1f} 0 0 1 {x + period:.1f},{yy + h:.1f} Z"
            out += f'<path d="{d}" fill="{fill if r % 2 == 0 else darker(fill, 0.9)}"/>'
            for k in (0.72, 0.46):
                rr = R * k
                out += incise(f"M{cx - rr:.1f},{yy + h:.1f} A{rr:.1f},{rr:.1f} 0 0 1 {cx + rr:.1f},{yy + h:.1f}", 1.1, line_col, 0.5)
            x += period
    return out


def wave_crest(x, y, s=1.0, fill=NGA, flip=1):
    """A single curling wave crest (for the stage front / water)."""
    f = flip
    d = (f"M{x - 40 * s * f:.1f},{y:.1f} C{x - 30 * s * f:.1f},{y - 30 * s:.1f} {x + 10 * s * f:.1f},{y - 44 * s:.1f} {x + 30 * s * f:.1f},{y - 26 * s:.1f} "
         f"C{x + 40 * s * f:.1f},{y - 16 * s:.1f} {x + 34 * s * f:.1f},{y - 2 * s:.1f} {x + 22 * s * f:.1f},{y - 6 * s:.1f} "
         f"C{x + 14 * s * f:.1f},{y - 10 * s:.1f} {x + 12 * s * f:.1f},{y - 20 * s:.1f} {x + 20 * s * f:.1f},{y - 22 * s:.1f} "
         f"C{x + 6 * s * f:.1f},{y - 28 * s:.1f} {x - 16 * s * f:.1f},{y - 16 * s:.1f} {x - 14 * s * f:.1f},{y:.1f} Z")
    return f'<path d="{d}" fill="{fill}"/>' + incise(spiral_d(x + 22 * s * f, y - 16 * s, 7 * s, 1.3, 0, f), 1.0, fill, 0.5)


# ---------- texture post-processing ----------
def pnoise(h, w, seed, sigma):
    """Periodic gaussian-filtered noise with unit std (tiles in x and y)."""
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, (h, w)).astype(np.float32)
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    g = np.exp(-2 * (np.pi ** 2) * (sigma ** 2) * (fx ** 2 + fy ** 2))
    out = np.real(np.fft.ifft2(np.fft.fft2(n) * g)).astype(np.float32)
    return out / (out.std() + 1e-6)


def fblur(a, sigma):
    """Periodic gaussian blur via FFT."""
    h, w = a.shape
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    g = np.exp(-2 * (np.pi ** 2) * (sigma ** 2) * (fx ** 2 + fy ** 2))
    return np.real(np.fft.ifft2(np.fft.fft2(a) * g)).astype(np.float32)


def fibres(h, w, seed, count, length=(8, 30), vertical=0.5):
    """Map of do-paper fibres in [-1, 1] (light and dark), wrapped in x."""
    r = random.Random(seed)
    im = Image.new("L", (w, h), 128)
    dr = ImageDraw.Draw(im)
    for _ in range(count):
        x, y = r.uniform(0, w), r.uniform(0, h)
        a = (math.pi / 2 if r.random() < vertical else 0) + r.uniform(-0.6, 0.6)
        L = r.uniform(*length)
        v = 128 + r.choice((-1, 1)) * r.randint(30, 70)
        pts = [(x, y)]
        for k in range(4):
            a += r.uniform(-0.35, 0.35)
            x, y = x + math.cos(a) * L / 4, y + math.sin(a) * L / 4
            pts.append((x, y))
        for ox in (-w, 0, w):
            dr.line([(px + ox, py) for px, py in pts], fill=v, width=1)
    return (np.asarray(im, np.float32) - 128) / 70


def _grain(h, w, seed, scale):
    g = pnoise(h, w, seed, 0.6 * scale) * 0.55
    g += pnoise(h, w, seed + 1, 2.2 * scale) * 0.45
    g += pnoise(h, w, seed + 2, 14 * scale) * 0.55          # mottling
    g += fibres(h, w, seed + 3, int(h * w / (260 * scale * scale)), (6 * scale, 26 * scale)) * 0.6
    return g


def _shift(a, dy, dx):
    out = np.zeros_like(a)
    h, w = a.shape
    ys = slice(max(dy, 0), h + min(dy, 0))
    yd = slice(max(-dy, 0), h + min(-dy, 0))
    xs = slice(max(dx, 0), w + min(dx, 0))
    xd = slice(max(-dx, 0), w + min(-dx, 0))
    out[ys, xs] = a[yd, xd]
    return out


def paper_cut(png_path, scale=2, seed=3, shadow=(4, 6, 4.0, 0.5), grain=1.0, rim=1.0, tile=False):
    """Hand-cut do paper look.

    grain : coarse grain + mottling + fibres in the colour
    rim   : light cut edge on the upper-left, darker edge lower-right, thin dark paper edge
    shadow: (dx, dy, blur, alpha) in design units, warm dark brown; None = no shadow
    tile  : horizontally tileable (background layers): x shift of the rim/shadow is dropped
    """
    im = Image.open(png_path).convert("RGBA")
    a = np.asarray(im, np.float32)
    h, w = a.shape[:2]
    alpha = a[..., 3] / 255
    rgb = a[..., :3]
    g = _grain(h, w, seed, scale)
    lum = rgb.mean(-1, keepdims=True)
    rgb = rgb * (1 + 0.075 * grain * g[..., None]) + 4 * grain * g[..., None] * (lum < 90)
    # cut rims
    s = max(1, int(round(1.6 * scale)))
    sx = 0 if tile else s
    light = np.clip(alpha - _shift(alpha, s, sx), 0, 1)
    dark = np.clip(alpha - _shift(alpha, -s, -sx), 0, 1)
    edge = np.clip(alpha - np.minimum(alpha, _shift(alpha, 1, 0) * _shift(alpha, -1, 0)
                                      * _shift(alpha, 0, 1) * _shift(alpha, 0, -1)), 0, 1)
    rgb = rgb + (np.array([246, 232, 200], np.float32) - rgb) * (0.38 * rim * light)[..., None]
    rgb = rgb * (1 - 0.32 * rim * dark)[..., None]
    rgb = rgb * (1 - 0.35 * rim * edge)[..., None]
    a[..., :3] = rgb.clip(0, 255)
    out = Image.fromarray(a.astype(np.uint8))
    if shadow:
        dx, dy, blur, sa = shadow
        dx = 0 if tile else dx
        m = np.pad(alpha, ((int(blur * scale * 3) + 2, int(blur * scale * 3) + 2), (0, 0)))
        m = _shift(m, int(dy * scale), int(dx * scale))
        m = fblur(m, blur * scale)
        pad = int(blur * scale * 3) + 2
        m = np.clip(m[pad:pad + h], 0, 1) * sa
        sh = np.zeros((h, w, 4), np.float32)
        sh[..., 0], sh[..., 1], sh[..., 2] = 34, 20, 12
        sh[..., 3] = m * 255
        base = Image.fromarray(sh.astype(np.uint8))
        base.alpha_composite(out)
        out = base
    out.save(png_path)


def card_texture(png_path):
    """Character / sprite pieces (2x PNG)."""
    paper_cut(png_path, scale=2, shadow=(3.5, 5, 3.5, 0.5))


def sprite_texture(png_path, shadow=True):
    paper_cut(png_path, scale=2, shadow=(3, 4.5, 3, 0.45) if shadow else None)


def layer_texture(png_path, seed=5, shadow_alpha=0.55):
    """Full-width background layer at 1x, tileable; casts a shadow down on the layer behind it."""
    paper_cut(png_path, scale=1, seed=seed, shadow=(0, -9, 7, shadow_alpha), tile=True, grain=1.15)


def make_do_paper(path, size=512, seed=21):
    """Tileable do paper for multiplying over the whole stage (very light, fibres + mottling)."""
    g = pnoise(size, size, seed, 0.8) * 0.4 + pnoise(size, size, seed + 1, 20) * 0.7
    g += fibres(size, size, seed + 2, 700, (10, 50)) * 0.7
    base = np.array([238, 226, 200], np.float32)
    img = base[None, None, :] * (1 + 0.035 * g[..., None])
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(path)
