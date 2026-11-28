"""Shared helpers for the Dong Ho woodblock style (tranh Dong Ho).

Look (from real prints: Ga trong, Muc dong thoi sao):
  - few flat colours from natural pigments: brick red, teal green, ochre,
    ivory, soft pink, charcoal black; no gradients, no translucent shading
  - black lines cut with a brush feel: thick-thin, tapered ends, slightly
    uneven edges (a woodblock filter roughens every edge a little)
  - fine paper grain shows through the colour (subtle, never blotchy)
build() works like puppet_lib.build() with a configurable canvas.
Needs: Pillow, numpy, svgpathtools, rsvg-convert.
"""
import json, math, os, random, subprocess
import numpy as np
from PIL import Image, ImageFilter
from svgpathtools import parse_path

# ---------- palette (closer to real Dong Ho pigments) ----------
PAPER = "#EFE2C2"        # giay diep
PAPER_DARK = "#DCC79C"
OCHRE_PAPER = "#E2B865"  # vang hoe ground (Ga trong print)
INK = "#241A14"          # than la tre
SON = "#A63A25"          # brick red (son)
SON_DARK = "#74261A"
VANG = "#D7A443"         # muted ochre yellow
VANG_LIGHT = "#EACB80"
LA = "#2F7A55"           # teal green (xanh dong)
LA_DARK = "#1E5A3E"
CHAM = "#3E5D72"
CHAM_LIGHT = "#6F8C98"
NAU = "#9A3B25"          # horse brick-brown
NAU_DARK = "#6A2617"
TRANG = "#F4ECD6"        # ivory (diep white)
DA = "#F1D9BD"           # skin
DA_SHADE = "#D9AE8C"
HONG = "#E3998A"
XAM = "#7A7068"
OFF = (0, 0)             # kept for compatibility (no off-register any more)

ROUGH_ID = "dh_rough"


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def angle_deg(p1, p2):
    return math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))


def f2(p):
    return f"{p[0]:.1f},{p[1]:.1f}"


# ---------- brush engine ----------
_seed = [1]


def _noise_fn(rnd):
    """Smooth 1D noise along arc length, roughly in [-1, 1]."""
    comps = [(rnd.uniform(0.02, 0.05), rnd.uniform(0, 6.28)),
             (rnd.uniform(0.06, 0.12), rnd.uniform(0, 6.28))]
    return lambda s: 0.65 * math.sin(s * comps[0][0] + comps[0][1]) + 0.35 * math.sin(s * comps[1][0] + comps[1][1])


def _sample(d, step=2.2):
    """Return list of subpaths, each (points, closed)."""
    path = parse_path(d)
    subs = []
    for sp in path.continuous_subpaths():
        pts = []
        for seg in sp:
            try:
                L = seg.length(error=1e-2)
            except Exception:
                L = abs(seg.end - seg.start)
            n = max(2, int(L / step))
            for i in range(n):
                z = seg.point(i / n)
                pts.append((z.real, z.imag))
        z = sp[-1].end
        pts.append((z.real, z.imag))
        closed = abs(sp[0].start - sp[-1].end) < 0.5
        if len(pts) >= 2:
            subs.append((pts, closed))
    return subs


def brush(d, w=3.0, color=INK, taper=0.22, var=0.28, min_w=0.35):
    """Variable-width brush stroke along an SVG path.
    Drawn as short round-capped segments, each with its own width."""
    _seed[0] += 1
    rnd = random.Random(_seed[0] * 7919)
    out = []
    for pts, closed in _sample(d):
        noise = _noise_fn(rnd)
        acc = [0.0]
        for i in range(1, len(pts)):
            acc.append(acc[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
        L = acc[-1] or 1
        # group segments into short polylines with one width each
        i = 0
        while i < len(pts) - 1:
            j = min(len(pts) - 1, i + 2)
            s = (acc[i] + acc[j]) / 2
            t = s / L
            prof = 1.0
            if not closed and taper > 0:
                e = min(t, 1 - t) / taper
                prof = min_w + (1 - min_w) * (min(1.0, e) ** 0.7)
            ww = max(0.4, w * prof * (1 + var * noise(s)))
            seg = " L".join(f"{p[0]:.1f},{p[1]:.1f}" for p in pts[i:j + 1])
            out.append(f'<path d="M{seg}" stroke-width="{ww:.2f}"/>')
            i = j
    return (f'<g fill="none" stroke="{color}" stroke-linecap="round" stroke-linejoin="round">'
            + "".join(out) + "</g>")


def ink(d, fill, sw=3.4, off=None, extra=""):
    """Flat fill + brush outline (closed outlines keep a thick-thin rhythm)."""
    out = ""
    if fill and fill != "none":
        out += f'<path d="{d}" fill="{fill}" {extra}/>'
    if sw:
        out += brush(d, sw * 1.05, INK, taper=0.08, var=0.3)
    return out


def line(d, sw=2.2, color=INK, extra=""):
    """Open brush line with tapered ends (extra ignored except dash -> plain)."""
    if "dasharray" in extra:
        return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" '
                f'stroke-linecap="round" {extra}/>')
    return brush(d, sw * 1.1, color, taper=0.3, var=0.25)


def flat(d, fill, extra=""):
    return f'<path d="{d}" fill="{fill}" {extra}/>'


def capsule(p1, p2, r1, r2):
    (x1, y1), (x2, y2) = p1, p2
    L = math.hypot(x2 - x1, y2 - y1)
    ux, uy = (x2 - x1) / L, (y2 - y1) / L
    nx, ny = -uy, ux
    A = (x1 + nx * r1, y1 + ny * r1)
    B = (x2 + nx * r2, y2 + ny * r2)
    C = (x2 - nx * r2, y2 - ny * r2)
    D = (x1 - nx * r1, y1 - ny * r1)
    return (f"M{f2(A)} L{f2(B)} A{r2},{r2} 0 0 0 {f2(C)} "
            f"L{f2(D)} A{r1},{r1} 0 0 0 {f2(A)} Z")


def bez(p0, p1, p2, p3, t):
    u = 1 - t
    return (u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
            u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1])


def bez_norm(p0, p1, p2, p3, t, eps=1e-3):
    a = bez(p0, p1, p2, p3, max(0, t - eps))
    b = bez(p0, p1, p2, p3, min(1, t + eps))
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1
    return (-dy / L, dx / L)


def spiral(x, y, r=14, turns=1.6, rot=0, color=TRANG, w=3.0, flip=1):
    """Hand-cut spiral (white decoration on animals, like the buffalo print)."""
    pts = []
    n = int(28 * turns)
    for i in range(n + 1):
        t = i / n
        a = math.radians(rot) + flip * t * turns * 2 * math.pi
        rr = r * (1 - 0.85 * t)
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    d = "M" + " L".join(f2(p) for p in pts)
    return brush(d, w, color, taper=0.35, var=0.2)


def swirl(x, y, s=1.0, rot=0, fill=None, sw=2.0, color=INK):
    """Dong Ho 'may' scroll (cloud / wind curl)."""
    d = ("M-22,6 C-26,-10 -8,-20 4,-12 C14,-6 10,8 0,7 C-7,6 -6,-3 0,-2 "
         "M4,-12 C12,-24 30,-18 28,-6 C27,3 18,4 17,-2")
    return (f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot}) scale({s})">'
            f'{brush(d, sw / max(s, 0.3), color, taper=0.3)}</g>')


def cloud_puff(x, y, s=1.0, fill=TRANG):
    """Dong Ho cloud: lobed outline with inner curls."""
    d = ("M-60,10 C-70,-8 -52,-22 -36,-16 C-32,-34 -8,-38 2,-24 C10,-40 38,-38 42,-18 "
         "C58,-22 72,-6 62,10 C70,22 56,30 44,26 C30,34 -40,34 -50,26 C-64,28 -70,18 -60,10 Z")
    return (f'<g transform="translate({x:.1f},{y:.1f}) scale({s})">'
            f'{ink(d, fill, 3.2)}'
            f'{line("M-30,14 C-34,2 -20,-6 -12,0 C-6,5 -12,12 -17,8", 2.2)}'
            f'{line("M14,12 C10,0 26,-8 34,-1 C39,4 34,11 29,8", 2.2)}</g>')


def flame(x, y, s=1.0, rot=0, outer=SON, inner=VANG, sw=2.6, k=0):
    """Stylised flame tongue, base at (0,0) pointing up. k varies the shape (anim frames)."""
    a = [0, 4, -3, 2][k % 4]
    b = [0, -3, 4, -2][k % 4]
    d = (f"M0,0 C-22,-4 {-26+a},-26 {-14+a},-42 C{-10+a},-50 {-12+b},-60 {-6+b},{-70+a} "
         f"C{-2+b},-58 {6+a},-56 {8+a},-46 C{12+a},-56 {18+b},-58 {20+b},{-66-b} "
         f"C{28+b},-46 {26+a},-20 18,-8 C12,-1 6,0 0,0 Z")
    din = f"M2,-6 C-10,-8 {-12+a},-22 {-4+a},{-32+b} C-2,-26 2,-26 {4+b},-30 C{8+b},-22 12,-14 8,-8 C6,-6 4,-6 2,-6 Z"
    return (f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot}) scale({s})">'
            f'{ink(d, outer, sw / max(s, 0.3))}{ink(din, inner, 1.6 / max(s, 0.3))}</g>')


def dots_row(p1, p2, n, r=2.2, fill=INK):
    out = ""
    for i in range(n):
        c = lerp(p1, p2, (i + 0.5) / n)
        out += f'<circle cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="{r}" fill="{fill}"/>'
    return out


def bell(x, y, r=7):
    d = f"M{x-r},{y} A{r},{r} 0 1 1 {x+r},{y} A{r},{r} 0 1 1 {x-r},{y} Z"
    return (ink(d, VANG, 2.0)
            + line(f"M{x-r*0.55:.1f},{y+r*0.25:.1f} L{x+r*0.55:.1f},{y+r*0.25:.1f}", 1.6)
            + f'<circle cx="{x:.1f}" cy="{y+r*0.55:.1f}" r="{r*0.18:.1f}" fill="{INK}"/>')


def tassel(x, y, s=1.0, color=SON):
    d = "M-5,0 L5,0 L7,8 C10,20 9,30 6,38 L-6,38 C-9,30 -10,20 -7,8 Z"
    return (f'<g transform="translate({x:.1f},{y:.1f}) scale({s})">'
            f'{ink(d, color, 2)}'
            f'{line("M-3,12 L-4,34 M0,12 L0,35 M3,12 L4,34", 1.1)}'
            f'{ink("M-6,-2 L6,-2 L6,6 L-6,6 Z", VANG, 1.8)}</g>')


def leaf(x, y, rot, s=1.0, fill=LA, vein=LA_DARK):
    d = "M0,0 C18,-9 52,-11 80,-1 C52,7 20,9 0,0 Z"
    return (f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.1f}) scale({s})">'
            f'{ink(d, fill, 2.4 / max(s, 0.4))}{line("M6,0 C30,-2 52,-2 72,-1", 1.2 / max(s, 0.4), vein)}</g>')


# ---------- svg / png ----------
def rough_filter(scale=2.2, freq=0.045, region=(-200, -200, 4000, 3000)):
    x, y, w, h = region
    return (f'<filter id="{ROUGH_ID}" filterUnits="userSpaceOnUse" x="{x}" y="{y}" width="{w}" height="{h}">'
            f'<feTurbulence type="fractalNoise" baseFrequency="{freq}" numOctaves="2" seed="7" result="n"/>'
            f'<feDisplacementMap in="SourceGraphic" in2="n" scale="{scale}" '
            f'xChannelSelector="R" yChannelSelector="G"/></filter>')


def svg_doc(inner, vb, rough=True):
    x, y, w, h = vb
    if rough:
        inner = f'<defs>{rough_filter()}</defs><g filter="url(#{ROUGH_ID})">{inner}</g>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}" '
            f'width="{w}" height="{h}">{inner}</svg>')


def render(svg_path, png_path, scale=2):
    subprocess.run(["rsvg-convert", "-z", str(scale), "-o", png_path, svg_path], check=True)


_GRAIN = {}


def _grain_tile(size=256, seed=5):
    if size in _GRAIN:
        return _GRAIN[size]
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, (size, size)).astype(np.float32)
    img = Image.fromarray(((n * 40) + 128).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
    g = (np.asarray(img, np.float32) - 128) / 40
    # vertical paper fibres
    fib = rng.normal(0, 1, (1, size)).astype(np.float32)
    g = g * 0.8 + np.repeat(fib, size, 0) * 0.35
    _GRAIN[size] = g
    return g


def print_texture(png_path, amount=1.0):
    """Woodblock print feel: fine grain in the colours, light speckles in black ink."""
    im = Image.open(png_path).convert("RGBA")
    a = np.asarray(im, np.float32)
    h, w = a.shape[:2]
    g = _grain_tile()
    reps = (h // g.shape[0] + 1, w // g.shape[1] + 1)
    G = np.tile(g, reps)[:h, :w]
    rgb = a[..., :3]
    lum = rgb.mean(-1)
    dark = lum < 70
    rgb *= (1 + 0.035 * amount * G)[..., None]
    speck = (G > 1.55) & dark
    rgb[speck] += 38 * amount
    a[..., :3] = rgb.clip(0, 255)
    Image.fromarray(a.astype(np.uint8)).save(png_path)


def write_svg_png(path_noext, inner, vb, scale=2, rough=True, texture=True):
    with open(path_noext + ".svg", "w") as f:
        f.write(svg_doc(inner, vb, rough))
    render(path_noext + ".svg", path_noext + ".png", scale)
    if texture:
        print_texture(path_noext + ".png")


def circle_shape(c, r):
    return {"type": "circle", "c": list(c), "r": r}


def capsule_shape(a, b, r):
    return {"type": "capsule", "a": list(a), "b": list(b), "r": r}


def _local(shape, pivot):
    out = dict(shape)
    for k in ("c", "a", "b"):
        if k in shape:
            out[k] = [round(shape[k][0] - pivot[0], 2), round(shape[k][1] - pivot[1], 2)]
    return out


def build(out_dir, name, canvas, parts, strings, colliders=None, extra=None, scale=2, pad=6):
    """parts: (id, parent, z, svg, pivot_world, limitDeg|None)
    strings: (id, part, anchor_world, hand, finger, mediapipe_landmark)"""
    W, H = canvas
    colliders = colliders or {}
    parts_dir = os.path.join(out_dir, "parts")
    os.makedirs(parts_dir, exist_ok=True)
    rig_parts = []
    for pid, parent, z, inner, pivot, limits in parts:
        tmp = os.path.join(out_dir, f"_tmp_{pid}")
        write_svg_png(tmp, inner, (0, 0, W, H), scale, texture=False)
        bx0, by0, bx1, by1 = Image.open(tmp + ".png").getbbox()
        x0 = max(0, math.floor(bx0 / scale) - pad)
        y0 = max(0, math.floor(by0 / scale) - pad)
        x1 = min(W, math.ceil(bx1 / scale) + pad)
        y1 = min(H, math.ceil(by1 / scale) + pad)
        vb = (x0, y0, x1 - x0, y1 - y0)
        write_svg_png(os.path.join(parts_dir, pid), inner, vb, scale)
        os.remove(tmp + ".svg"); os.remove(tmp + ".png")
        rig_parts.append({
            "id": pid, "parent": parent, "z": z,
            "svg": f"parts/{pid}.svg", "png": f"parts/{pid}.png",
            "origin": [x0, y0], "size": [vb[2], vb[3]],
            "pivot": [round(pivot[0] - x0, 2), round(pivot[1] - y0, 2)],
            "pivotWorld": [round(pivot[0], 2), round(pivot[1], 2)],
            "limitDeg": list(limits) if limits else None,
            "density": colliders.get(pid, {}).get("density", 1.0),
            "colliders": [_local(s, pivot) for s in colliders.get(pid, {}).get("shapes", [])],
        })
    by_id = {p["id"]: p for p in rig_parts}
    rig = {
        "name": name,
        "units": "design units (1 unit = 2 px in PNG); y down; facing right; colliders relative to part pivot",
        "canvas": [W, H],
        "pngScale": scale,
        "feetY": max(p["origin"][1] + p["size"][1] for p in rig_parts) - pad,
        "parts": rig_parts,
        "strings": [
            {"id": sid, "part": part,
             "anchor": [round(p[0] - by_id[part]["origin"][0], 2),
                        round(p[1] - by_id[part]["origin"][1], 2)],
             "anchorWorld": [round(p[0], 2), round(p[1], 2)],
             "hand": hand, "finger": finger, "mpLandmark": lm}
            for sid, part, p, hand, finger, lm in strings
        ],
    }
    if extra:
        rig.update(extra)
    with open(os.path.join(out_dir, "rig.json"), "w") as f:
        json.dump(rig, f, indent=2)
    full = "".join(p[3] for p in sorted(parts, key=lambda p: p[2]))
    write_svg_png(os.path.join(out_dir, f"{name}_full"), full, (0, 0, W, H), scale)
    return rig


# ---------- giay diep paper ----------
def make_paper(path, size=512, seed=7, base=(239, 226, 194)):
    """Tileable giay diep texture: warm ivory, soft fibres, faint mica sparkle (not blotchy)."""
    rng = np.random.default_rng(seed)
    img = np.ones((size, size, 3), np.float32) * np.array(base, np.float32)
    yy, xx = np.mgrid[0:size, 0:size] / size * 2 * np.pi
    mott = np.zeros((size, size), np.float32)
    for _ in range(6):
        kx, ky = rng.integers(1, 4, 2)
        mott += np.sin(kx * xx + ky * yy + rng.uniform(0, 6.28))
    img -= (mott / 6)[..., None] * 3
    from PIL import ImageDraw
    fib = Image.new("L", (size, size), 0)
    dr = ImageDraw.Draw(fib)
    r = random.Random(seed)
    for _ in range(360):
        x, y = r.uniform(0, size), r.uniform(0, size)
        a = math.pi / 2 + r.uniform(-0.25, 0.25)       # mostly vertical fibres like do-bark paper
        L = r.uniform(10, 40)
        for ox in (-size, 0, size):
            for oy in (-size, 0, size):
                dr.line([(x + ox, y + oy), (x + ox + math.cos(a) * L, y + oy + math.sin(a) * L)],
                        fill=r.randint(15, 40), width=1)
    img -= np.asarray(fib.filter(ImageFilter.GaussianBlur(0.6)), np.float32)[..., None] * 0.3
    img += rng.normal(0, 2.0, (size, size, 1))
    n = 900
    xs, ys = rng.integers(0, size, n), rng.integers(0, size, n)
    img[ys, xs] = np.minimum(255, img[ys, xs] + rng.uniform(8, 18, (n, 1)))
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(path)


def strand(p0, p1, p2, p3, w0, fill, n=26, vein=True, sw=2.4):
    """Long tapered lock / feather along a cubic bezier (tail plumes, crests, mane)."""
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        p = bez(p0, p1, p2, p3, t)
        nx, ny = bez_norm(p0, p1, p2, p3, t)
        w = w0 * (1 - t) ** 0.75 * (0.85 + 0.15 * math.sin(t * math.pi)) + 0.6
        left.append((p[0] + nx * w, p[1] + ny * w))
        right.append((p[0] - nx * w, p[1] - ny * w))
    d = "M" + " L".join(f2(p) for p in left) + " L" + " L".join(f2(p) for p in reversed(right)) + " Z"
    out = ink(d, fill, sw)
    if vein:
        mid = [bez(p0, p1, p2, p3, t / 10) for t in range(1, 9)]
        out += line("M" + " L".join(f2(p) for p in mid), 1.2,
                    INK if fill == TRANG else (TRANG if fill != VANG else SON))
    return out
