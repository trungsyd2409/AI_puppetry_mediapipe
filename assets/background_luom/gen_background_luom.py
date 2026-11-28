"""Ripe rice fields for Luom as a layered paper-cut folk stage.

Every layer is a sheet of hand-cut do paper with grain, a light cut rim and a soft shadow on the
sheet behind it, like a miniature puppet stage. Motifs from bronze drums and old communal houses:
scroll clouds, rounded mountains with incised contour lines, water waves, a flaming drum sun.

The SKY is painted by code (morning -> afternoon -> dusk, from skyTimes) with the drum sun sprite on
an arc and a vignette; the stage FRAME (wave band + half sun medallion at the bottom, valance at the
top) is fixed and does not scroll. Layers are 1600 x 900 and tile horizontally; groundY = the path.
"""
import json, math, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from dongho_lib import write_svg_png, brush, lerp, f2  # noqa
from paper_lib import *  # noqa

OUT = HERE
PROPS = os.path.join(OUT, "props")
W, H = 1600, 900
GROUND = 770
SPRITES = {}


def wrap(fn, x, *a, **k):
    return "".join(fn(x + o, *a, **k) for o in (-W, 0, W))


def band(top_pts, fill, bottom=H + 20, cloth=False):
    d = f"M-30,{top_pts[0][1]:.1f} L" + " L".join(f2(p) for p in top_pts) + f" L{W + 30},{top_pts[-1][1]:.1f} L{W + 30},{bottom} L-30,{bottom} Z"
    return cut(d, fill, w=0, cloth=cloth)


def wavy(base, amps, step=10):
    """Periodic wavy line: amps = [(amplitude, cycles, phase)]."""
    pts = []
    for x in range(-30, W + 31, step):
        y = base + sum(a * math.sin(2 * math.pi * c * x / W + p) for a, c, p in amps)
        pts.append((x, y))
    return pts


def line_of(pts, dy=0):
    return "M" + " L".join(f"{x:.1f},{y + dy:.1f}" for x, y in pts)


# ======================= motifs =======================
def mountain(x, base, w, h, fill, lines=3, light=True):
    """Rounded folk mountain with incised contour lines and a lighter lit flank."""
    def shape(xx, ww, hh):
        return (f"M{xx - ww / 2:.1f},{base} C{xx - ww * 0.42:.1f},{base - hh * 0.9:.1f} {xx - ww * 0.2:.1f},{base - hh:.1f} {xx:.1f},{base - hh:.1f} "
                f"C{xx + ww * 0.2:.1f},{base - hh:.1f} {xx + ww * 0.42:.1f},{base - hh * 0.9:.1f} {xx + ww / 2:.1f},{base} Z")
    out = f'<path d="{shape(x, w, h)}" fill="{fill}"/>'
    if light:
        out += f'<path d="{shape(x - w * 0.12, w * 0.62, h * 0.9)}" fill="{lighter(fill, 0.12)}"/>'
    for i in range(1, lines + 1):
        t = 1 - i / (lines + 1)
        d = shape(x, w * t, h * t).rsplit(" Z", 1)[0]
        out += incise(d, 1.4, fill, 0.8)
    return out


def rice_ear(x, y, s, col, grain):
    """One drooping ear of ripe rice: a stem and a row of teardrop grains."""
    p0, p1, p2, p3 = (x, y), (x + 2 * s, y - 16 * s), (x + 10 * s, y - 26 * s), (x + 20 * s, y - 14 * s)
    out = brush(f"M{x:.1f},{y:.1f} C{f2(p1)} {f2(p2)} {f2(p3)}", 1.0 * s + 0.4, col, taper=0.3, var=0.1)
    for i in range(6):
        t = 0.45 + i * 0.1
        bx, by = bez(p0, p1, p2, p3, t)
        nx, ny = bez_norm(p0, p1, p2, p3, t)
        a = math.degrees(math.atan2(ny, nx))
        for side in (1, -1):
            cx, cy = bx + nx * side * 2.2 * s, by + ny * side * 2.2 * s
            out += (f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{2.6 * s:.1f}" ry="{1.4 * s:.1f}" '
                    f'transform="rotate({a + 90 + side * 25:.0f} {cx:.1f} {cy:.1f})" fill="{grain}"/>')
    return out


def leaf_spray(x, y, a0, s, fill):
    """A spray of 4-5 slim bamboo leaves fanning from one point."""
    out = ""
    for i in range(5):
        a = math.radians(a0 + (i - 2) * 22)
        L = s * (26 - abs(i - 2) * 3)
        ex, ey = x + math.cos(a) * L, y + math.sin(a) * L
        nx, ny = -math.sin(a) * 3.2 * s, math.cos(a) * 3.2 * s
        mx, my = (x + ex) / 2, (y + ey) / 2
        out += f'<path d="M{x:.1f},{y:.1f} Q{mx + nx:.1f},{my + ny:.1f} {ex:.1f},{ey:.1f} Q{mx - nx:.1f},{my - ny:.1f} {x:.1f},{y:.1f} Z" fill="{fill}"/>'
    return out


def bamboo_clump(x, base, s, fill, dark):
    """Luy tre: tall arching culms with node rings and sprays of slim leaves."""
    out = ""
    rnd = random.Random(int(x * 7 + s * 100))
    culms = []
    for i in range(6):
        lean = (i - 2.5) * 0.16 + rnd.uniform(-0.05, 0.05)
        L = s * rnd.uniform(190, 240)
        p0 = (x + (i - 2.5) * 5 * s, base)
        p3 = (p0[0] + math.sin(lean) * L * 0.9 + lean * 60 * s, base - math.cos(lean) * L)
        p1 = (p0[0] + (p3[0] - p0[0]) * 0.1, base - L * 0.4)
        p2 = (p0[0] + (p3[0] - p0[0]) * 0.55, base - L * 0.85)
        culms.append((p0, p1, p2, p3))
    for (p0, p1, p2, p3) in culms:
        # tapered culm
        left, right = [], []
        for k in range(13):
            t = k / 12
            px, py = bez(p0, p1, p2, p3, t)
            nx, ny = bez_norm(p0, p1, p2, p3, t)
            w = 3.6 * s * (1 - t * 0.75)
            left.append((px + nx * w, py + ny * w)); right.append((px - nx * w, py - ny * w))
        out += f'<path d="M{" L".join(f2(p) for p in left)} L{" L".join(f2(p) for p in reversed(right))} Z" fill="{dark}"/>'
        for t in (0.18, 0.34, 0.5, 0.64, 0.78):
            px, py = bez(p0, p1, p2, p3, t)
            out += f'<path d="M{px - 4 * s:.1f},{py:.1f} L{px + 4 * s:.1f},{py:.1f}" stroke="{lighter(dark, 0.3)}" stroke-width="1.1"/>'
    for (p0, p1, p2, p3) in culms:
        for t in (0.42, 0.58, 0.72, 0.86, 1.0):
            px, py = bez(p0, p1, p2, p3, t)
            side = 1 if (p3[0] > p0[0]) else -1
            a0 = 90 + side * rnd.uniform(-40, -10) if t < 1 else (60 if side > 0 else 120)
            out += leaf_spray(px, py, a0, s * rnd.uniform(0.9, 1.25), fill if rnd.random() < 0.6 else lighter(fill, 0.12))
    return out


def dinh(x, base):
    """Mai dinh: communal-house roof with upturned dragon-tail corners, on wooden pillars."""
    out = ""
    out += cut(f"M{x - 120},{base} L{x - 120},{base - 46} L{x + 120},{base - 46} L{x + 120},{base} Z", NAU, w=0)
    for i in range(-3, 4):
        out += cut(f"M{x + i * 34 - 5},{base} L{x + i * 34 - 5},{base - 46} L{x + i * 34 + 5},{base - 46} L{x + i * 34 + 5},{base} Z", NAU_D, w=0)
    roof = (f"M{x - 196},{base - 70} C{x - 180},{base - 52} {x - 160},{base - 48} {x - 140},{base - 50} "
            f"L{x + 140},{base - 50} C{x + 160},{base - 48} {x + 180},{base - 52} {x + 196},{base - 70} "
            f"C{x + 180},{base - 64} {x + 166},{base - 66} {x + 150},{base - 72} L{x + 96},{base - 134} "
            f"L{x - 96},{base - 134} L{x - 150},{base - 72} C{x - 166},{base - 66} {x - 180},{base - 64} {x - 196},{base - 70} Z")
    out += cut(roof, SON_D, w=0)
    for i in range(1, 6):
        y = base - 50 - i * 14
        hw = 140 - i * 8.5
        out += incise(f"M{x - hw:.1f},{y} L{x + hw:.1f},{y}", 1.2, SON_D, 0.6)
    out += cut(f"M{x - 100},{base - 134} L{x + 100},{base - 134} L{x + 100},{base - 142} L{x - 100},{base - 142} Z", NAU_D, w=0)
    for sx in (-1, 1):
        out += cut(f"M{x + sx * 96},{base - 140} C{x + sx * 112},{base - 156} {x + sx * 128},{base - 156} {x + sx * 126},{base - 140} "
                   f"C{x + sx * 120},{base - 146} {x + sx * 110},{base - 144} {x + sx * 100},{base - 134} Z", NAU_D, w=0)
        out += incise(spiral_d(x + sx * 118, base - 148, 5, 1.3, 0, sx), 0.9, NAU_D, 0.4)
        out += incise(spiral_d(x + sx * 190, base - 74, 6, 1.3, math.pi, -sx), 0.9, SON_D, 0.4)
    out += f'<g transform="translate({x},{base - 150})">{drum_sun(10, 10, SON, VANG, VANG_L, flames=False)}</g>'
    return out


def areca(x, base, h, fill):
    out = cut(f"M{x - 3},{base} C{x - 2},{base - h * 0.5} {x + 2},{base - h * 0.8} {x + 1},{base - h} L{x + 6},{base - h} "
              f"C{x + 7},{base - h * 0.8} {x + 4},{base - h * 0.5} {x + 4},{base} Z", NAU_D, w=0)
    for a in (-170, -135, -100, -70, -35, -5):
        ex = x + 3 + math.cos(math.radians(a)) * 46
        ey = base - h + math.sin(math.radians(a)) * 26 + 20
        out += f'<path d="M{x + 3},{base - h} Q{(x + 3 + ex) / 2:.1f},{base - h - 22} {ex:.1f},{ey:.1f} Q{(x + 3 + ex) / 2:.1f},{base - h - 8} {x + 3},{base - h} Z" fill="{fill}"/>'
    return out


# ======================= layers =======================
def layer_far():
    """Far mountains, hazy into the sky."""
    col = mix(LUC_L, "#C7B488", 0.5)
    out = band(wavy(560, [(6, 2, 0.3)]), col)
    for x, w, h in [(120, 360, 170), (420, 300, 130), (700, 420, 200), (1000, 320, 140), (1280, 380, 180), (1520, 280, 120)]:
        out += wrap(mountain, x, 570, w, h, col, 3)
    return out


def layer_mountains():
    col = mix(LUC_L, "#C7B488", 0.18)
    out = band(wavy(610, [(5, 3, 1.0)]), col)
    for x, w, h in [(240, 300, 150), (560, 240, 110), (860, 280, 130), (1160, 260, 160), (1440, 220, 100)]:
        out += wrap(mountain, x, 620, w, h, col, 2)
    return out


def layer_village():
    base = 660
    out = band(wavy(base - 8, [(4, 4, 0.2)]), REU_D)
    for x, s in [(60, 0.9), (180, 1.1), (330, 0.85), (560, 1.0), (1090, 1.05), (1230, 0.8), (1400, 1.15), (1530, 0.9)]:
        out += wrap(bamboo_clump, x, base, s, LUC if int(x) % 20 else LUC_L, LUC_D)
    for x in (430, 700, 960, 1310):
        out += wrap(areca, x, base - 4, 150 + (x % 3) * 14, LUC)
    out += dinh(820, base - 4)
    return out


def layer_river():
    top = 676
    col = mix(LUC_L, NGA, 0.3)
    out = band(wavy(top, [(3, 2, 0.0)]), col)
    out += wave_band(0, W, top + 2, 18, col, col, rows=2, period=64)
    return out


def layer_field():
    out = ""
    rnd = random.Random(4)
    tops = [698, 724, 748]
    for r, t in enumerate(tops):
        pts = wavy(t, [(4, 3 + r, r * 1.3), (2, 7, r)])
        col = [VANG_D, VANG, mix(VANG, VANG_L, 0.4)][r]
        out += band(pts, col)
        out += incise(line_of(pts, 3), 1.2, col, 0.7)
        s = 1.0 + r * 0.45
        n = int(W / (22 + r * 12))
        for i in range(n):
            x = (i + rnd.uniform(0.1, 0.9)) * W / n
            y = t + 10 + rnd.uniform(0, 10) + r * 2
            out += wrap(rice_ear, x, y, s, darker(col, 0.72), lighter(col, 0.35))
    return out


def layer_path():
    top = wavy(GROUND - 10, [(3, 2, 0.4), (2, 5, 1.0)])
    out = band(top, EARTH)
    out += incise(line_of(top, 4), 1.4, EARTH, 0.7)
    for i, y in enumerate((GROUND + 26, GROUND + 58)):
        out += incise(line_of(wavy(y, [(4, 6 + i * 2, i)])), 1.2, EARTH, 0.6)
    rnd = random.Random(9)
    for _ in range(36):
        x = rnd.uniform(0, W)
        y = rnd.uniform(GROUND + 10, 850)
        if rnd.random() < 0.55:
            r = rnd.uniform(3, 6)
            out += wrap(lambda xx: f'<ellipse cx="{xx:.1f}" cy="{y:.1f}" rx="{r:.1f}" ry="{r * 0.6:.1f}" fill="{lighter(EARTH, 0.2)}"/>', x)
        else:
            out += wrap(lambda xx: incise(f"M{xx:.1f},{y:.1f} q-2,-8 -6,-12 M{xx + 3:.1f},{y:.1f} q1,-9 5,-13", 1.1, EARTH, 0.5), x)
    return out


# ======================= sprites =======================
def sprite(name, inner, w, h, anchor, scale=2, shadow=True):
    ax, ay = anchor
    write_svg_png(os.path.join(PROPS, name), f'{defs()}<g transform="translate({ax},{ay})">{inner}</g>', (0, 0, w, h), scale,
                  texture=lambda p: sprite_texture(p, shadow))
    SPRITES[name] = {"png": f"props/{name}.png", "size": [w, h], "anchor": [ax, ay], "pngScale": scale}


def stork(k):
    """Con co in flight (paper-cut, 3 wing frames)."""
    wing = ["M-6,-4 C-14,-26 -32,-38 -48,-40 C-40,-30 -36,-26 -30,-22 C-24,-12 -14,-6 6,-2 Z",
            "M-6,-4 C-18,-12 -36,-14 -52,-10 C-40,-4 -24,2 6,-2 Z",
            "M-6,-2 C-14,8 -28,20 -42,24 C-30,12 -18,2 6,0 Z"][k]
    body = "M-26,0 C-14,-9 10,-9 22,-5 L44,-3 L22,2 C10,6 -14,6 -26,0 Z"
    out = cut(wing, NGA_D, w=0.6) + cut(body, NGA, w=0.6)
    out += incise("M-2,-3 C6,-1 12,-1 18,-3", 0.8, NGA, 0.4)
    out += thin("M-26,0 L-44,3", 1.6, NAU_D) + f'<circle cx="24" cy="-4" r="1.4" fill="{INK}"/>'
    return out


def cloud(seed):
    rnd = random.Random(seed)
    s = rnd.uniform(0.85, 1.15)
    return scroll_cloud(s, NGA, seed)


def rice_tuft(seed, big=1.0):
    rnd = random.Random(seed)
    out = ""
    for i in range(9):
        a = -90 + (i - 4) * 10 + rnd.uniform(-4, 4)
        L = rnd.uniform(70, 110) * big
        ex, ey = math.cos(math.radians(a)) * L, math.sin(math.radians(a)) * L
        leaf = f"M-3,0 Q{ex * 0.4 - 4:.1f},{ey * 0.6:.1f} {ex:.1f},{ey:.1f} Q{ex * 0.4 + 4:.1f},{ey * 0.6:.1f} 3,0 Z"
        out += f'<path d="{leaf}" fill="{REU if i % 2 else REU_L}"/>'
    for i in range(5):
        a = -90 + (i - 2) * 18 + rnd.uniform(-5, 5)
        L = rnd.uniform(80, 100) * big
        x, y = math.cos(math.radians(a)) * L * 0.6, math.sin(math.radians(a)) * L * 0.6
        out += rice_ear(x, y + 20, 1.6 * big, VANG_D, VANG_L)
    return out


def smoke():
    return scroll_cloud(0.38, mix(NGA_D, SMOKE, 0.5), 5,
                        [(-30, 4, 18), (-8, -10, 22), (16, -4, 20), (34, 6, 16), (0, 10, 18)])


def sun_sprite():
    return drum_sun(70, 14, SON, VANG, VANG_L, True, NAU)


def stage_front():
    """Fixed stage lip at the bottom: lacquer band, rolling wave crests, half drum-sun in the middle."""
    out = ""
    top = 64
    out += cut(f"M0,{top} L{W},{top} L{W},140 L0,140 Z", NAU_D, w=0)
    out += cut(f"M0,{top} L{W},{top} L{W},{top + 8} L0,{top + 8} Z", VANG_D, w=0)
    out += punch_row((0, top + 4), (W, top + 4), 160, 1.4, NAU_D)
    for i in range(22):
        x = i * 76 + 20
        out += wave_crest(x, top + 2, 0.9, LUC_L if i % 2 else LUC, 1 if x < W / 2 else -1)
    out += wave_band(0, W, top + 14, 30, SON_D, SON_D, rows=2, period=56)
    out += f'<g transform="translate({W / 2},{150})">{drum_sun(118, 14, SON, VANG, VANG_L, True, NAU)}</g>'
    out += f'<g transform="translate(110,{top - 6})">{scroll_cloud(0.75, NGA_D, 3)}</g>'
    out += f'<g transform="translate({W - 110},{top - 6}) scale(-1,1)">{scroll_cloud(0.75, NGA_D, 4)}</g>'
    return out


def stage_top():
    """Valance at the top of the stage: lacquer red cloth with scallops, gold bands, tassels."""
    out = cut(f"M0,0 L{W},0 L{W},34 L0,34 Z", SON_D, w=0, cloth=True)
    out += cut(f"M0,26 L{W},26 L{W},34 L0,34 Z", VANG_D, w=0)
    sc = ""
    for i in range(20):
        x = i * 80
        sc += f"M{x},34 Q{x + 40},74 {x + 80},34 Z "
    out += cut(sc, SON, w=0, cloth=True)
    for i in range(20):
        x = i * 80
        out += incise(f"M{x + 10},40 Q{x + 40},64 {x + 70},40", 1.0, SON, 0.5)
        out += f'<g transform="translate({x + 40},50)">{drum_sun(7, 8, VANG, VANG_L, NGA, False, VANG_D)}</g>'
        out += cut(f"M{x - 2},34 L{x + 2},34 L{x + 2},62 L{x - 2},62 Z", VANG_D, w=0)
        out += f'<circle cx="{x}" cy="64" r="4" fill="{VANG}"/>'
        out += cut(f"M{x - 3},66 L{x + 3},66 L{x + 6},84 L{x - 6},84 Z", SON_D, w=0)
        out += incise(f"M{x - 2},70 L{x - 3},83 M{x + 2},70 L{x + 3},83", 0.7, SON_D, 0.3)
    out += punch_row((0, 30), (W, 30), 200, 1.2, SON_D)
    return out


def make_sprites():
    os.makedirs(PROPS, exist_ok=True)
    for k in range(3):
        sprite(f"stork_{k}", stork(k), 110, 80, (55, 42))
    for k in range(3):
        sprite(f"cloud_{k}", cloud(k + 2), 240, 110, (120, 60))
    for k in range(3):
        sprite(f"rice_{k}", rice_tuft(k + 3, 1.0 + 0.15 * k), 240, 160, (120, 150))
    sprite("smoke", smoke(), 110, 70, (55, 38), shadow=False)
    sprite("sun", sun_sprite(), 240, 240, (120, 120))
    write_svg_png(os.path.join(PROPS, "stage_front"), defs() + stage_front(), (0, 0, W, 140), 1,
                  texture=lambda p: paper_cut(p, scale=1, shadow=(0, -6, 6, 0.6), tile=True))
    SPRITES["stage_front"] = {"png": "props/stage_front.png", "size": [W, 140], "anchor": [0, 140], "pngScale": 1}
    write_svg_png(os.path.join(PROPS, "stage_top"), defs() + stage_top(), (0, 0, W, 96), 1,
                  texture=lambda p: paper_cut(p, scale=1, shadow=(0, 6, 5, 0.55), tile=True))
    SPRITES["stage_top"] = {"png": "props/stage_top.png", "size": [W, 96], "anchor": [0, 0], "pngScale": 1}


def props():
    P = []
    for i, (x, y, v) in enumerate([(220, 300, 7), (760, 250, 5), (1180, 330, 9), (1500, 280, 6)]):
        P.append({"layer": "clouds", "type": "drift", "sprite": f"cloud_{i % 3}", "x": x, "y": y, "vx": -v, "bob": 3})
    P.append({"layer": "sky", "type": "flock", "frames": ["stork_0", "stork_1", "stork_2"], "count": 4,
              "y": [260, 420], "vx": [-55, -30], "fps": 5, "scale": [0.45, 0.7]})
    for x in (700, 1300):
        P.append({"layer": "village", "type": "smoke", "x": x, "y": 600, "sprite": "smoke",
                  "rate": 0.8, "life": 5, "rise": 26, "grow": 1.2, "scale": 0.6})
    for i, x in enumerate((60, 380, 700, 1020, 1340)):
        P.append({"layer": "front", "type": "sway", "sprite": f"rice_{i % 3}", "x": x, "y": 860, "scale": 1.0,
                  "amp": 4, "speed": 1.6})
    return P


def write_layer(name, inner, seed):
    p = os.path.join(OUT, f"layer_{name}")
    write_svg_png(p, defs() + inner, (0, 0, W, H), 1, texture=lambda q: layer_texture(q, seed))


def main():
    make_do_paper(os.path.join(OUT, "paper.png"))
    layers = [
        ("sky", "", 0.0),          # painted by code (time of day) + sun sprite
        ("clouds", "", 0.03),
        ("far", layer_far(), 0.06),
        ("mountains", layer_mountains(), 0.12),
        ("village", layer_village(), 0.25),
        ("river", layer_river(), 0.38),
        ("field", layer_field(), 0.55),
        ("path", layer_path(), 1.0),
        ("front", "", 1.3),        # swaying rice tufts in front (props only)
    ]
    for i, (name, inner, _) in enumerate(layers):
        if inner:
            write_layer(name, inner, 10 + i)
    make_sprites()
    stage = {
        "size": [W, H], "floorY": GROUND, "groundY": GROUND, "tileWidth": W, "paper": "paper.png", "wind": 14,
        "layers": [{"id": n, "png": (f"layer_{n}.png" if inner else None), "parallax": p, "front": n == "front"}
                   for n, inner, p in layers],
        "sprites": SPRITES,
        "props": props(),
        "frame": {"bottom": "stage_front", "top": "stage_top"},
        "sun": {"sprite": "sun", "arc": {"x0": 1450, "x1": 150, "yLow": 560, "yHigh": 190}, "scale": 0.8},
        "skyTimes": {
            "morning":   {"top": "#9FA488", "bottom": "#E3CB98", "sun": "#E9C46A", "tint": [255, 246, 226, 0.0]},
            "afternoon": {"top": "#C29150", "bottom": "#E6BE78", "sun": "#E39A3E", "tint": [255, 214, 150, 0.08]},
            "dusk":      {"top": "#4C3843", "bottom": "#B8613C", "sun": "#C9502E", "tint": [120, 60, 50, 0.22]},
        },
        "vignette": {"strength": 0.55, "radius": 0.75, "color": [30, 16, 8]},
        "note": "Draw order: sky gradient -> sun -> layers back to front (props per layer) -> puppet -> front layer -> "
                "stage_front at the bottom (fixed) and stage_top at the top of the visible stage (fixed) -> time tint -> "
                "vignette centred on the puppet -> paper.png multiplied lightly. Hazards/items are in fx_luom.",
    }
    with open(os.path.join(OUT, "stage.json"), "w") as f:
        json.dump(stage, f, indent=2)
    print("ok", len(SPRITES), "sprites", len(stage["props"]), "props")


if __name__ == "__main__":
    main()
