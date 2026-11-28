"""Peaceful Vietnamese village (lang que) in Dong Ho style, parallax layers for Flappy chim lac.

Static layers 1600 x 900, tile horizontally. Animated things are sprites in props/, placed by
stage.json 'props' (same prop types as background_giong: anim, sway, smoke, drift, spin).
Ground top = groundY: touching it ends the run.
"""
import json, math, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "background_giong"))
from dongho_lib import *  # noqa
from gen_background_giong import (ridge, poly, poly_line, ink_wide, contour, wrap,  # noqa
                                  bamboo_clump, smoke_puff, cloud, flag)
from PIL import Image

OUT = HERE
PROPS = os.path.join(OUT, "props")
W, H = 1600, 900
GROUND = 820            # top of the dyke road (death line)
WOOD, WOOD_D = "#8A5A36", "#5E3A22"
THATCH = "#C49A52"
SPRITES = {}


# ======================= static layers =======================
def sky():
    band = (f'<path d="M0,470 C400,462 800,478 1200,466 C1400,462 1500,468 {W},470 L{W},{H} L0,{H} Z" fill="#EDD6A6"/>')
    sx, sy, r = 1250, 230, 88
    sun = (ink(f"M{sx-r},{sy} A{r},{r} 0 1 1 {sx+r},{sy} A{r},{r} 0 1 1 {sx-r},{sy} Z", SON, 4)
           + spiral(sx, sy, 40, 1.8, 0, VANG, 3.0) + spiral(sx, sy, 64, 1.0, 180, SON_DARK, 2.2))
    return band + sun


def mountains():
    back = ridge(560, [(150, 230, 230), (520, 180, 200), (900, 260, 250), (1280, 200, 220), (1550, 150, 160)])
    front = ridge(600, [(330, 120, 200), (700, 90, 170), (1080, 140, 220), (1440, 100, 180)])
    out = ink_wide(poly(back), CHAM_LIGHT)
    for dy in (24, 48):
        out += contour(poly_line(back, dy), 2.0, TRANG)
    out += ink_wide(poly(front), "#5B8F6A")
    out += contour(poly_line(front, 20), 2.0, TRANG)
    return out


def dinh(x, base):
    """Communal house (dinh lang): low red-pillared hall under a big curved roof with up-turned corners."""
    out = ink(f"M{x-170},{base} L{x-170},{base-12} L{x+170},{base-12} L{x+170},{base} Z", "#B79A6E", 2.6)
    for i in range(7):
        px = x - 150 + i * 50
        out += ink(f"M{px-6},{base-12} L{px-6},{base-86} L{px+6},{base-86} L{px+6},{base-12} Z", SON, 2.2)
    out += ink(f"M{x-140},{base-86} L{x+140},{base-86} L{x+140},{base-20} L{x-140},{base-20} Z", "#6E4A2C", 0)
    for i in range(6):
        px = x - 125 + i * 50
        out += ink(f"M{px},{base-80} L{px+30},{base-80} L{px+30},{base-24} L{px},{base-24} Z", WOOD_D, 1.6)
    roof = (f"M{x-210},{base-70} C{x-226},{base-84} {x-238},{base-108} {x-232},{base-124} "
            f"C{x-214},{base-108} {x-196},{base-104} {x-170},{base-112} "
            f"L{x-110},{base-186} L{x+110},{base-186} L{x+170},{base-112} "
            f"C{x+196},{base-104} {x+214},{base-108} {x+232},{base-124} "
            f"C{x+238},{base-108} {x+226},{base-84} {x+210},{base-70} Z")
    out += ink(roof, "#8C3A26", 3.4)
    for i in range(14):
        rx = x - 180 + i * 28
        out += line(f"M{rx},{base-78} L{rx+(12 if i < 7 else -12) * 0.6},{base-176}", 1.4, SON_DARK)
    out += ink(f"M{x-120},{base-186} L{x+120},{base-186} L{x+120},{base-198} L{x-120},{base-198} Z", VANG, 2.4)
    out += swirl(x - 128, base - 204, 0.8, 200, sw=2.2) + swirl(x + 128, base - 204, 0.8, -20, sw=2.2)
    out += ink(f"M{x-14},{base-214} A14,14 0 1 1 {x+14},{base-214} A14,14 0 1 1 {x-14},{base-214} Z", SON, 2.2)
    out += spiral(x, base - 214, 8, 1.3, 0, VANG, 1.6)
    return out


def banyan(x, base, s=1.0):
    """Cay da: thick trunk, hanging aerial roots, cloud-like canopy."""
    out = ink(f"M{x-26*s},{base} C{x-20*s},{base-60*s} {x-30*s},{base-120*s} {x-12*s},{base-170*s} "
              f"L{x+16*s},{base-170*s} C{x+30*s},{base-120*s} {x+22*s},{base-60*s} {x+34*s},{base} Z", WOOD, 3)
    for dx in (-60, -36, 40, 70):
        out += line(f"M{x+dx*s},{base-150*s} C{x+dx*s},{base-90*s} {x+(dx+6)*s},{base-40*s} {x+(dx+2)*s},{base}", 2.0, WOOD_D)
    rnd = random.Random(int(x))
    for cx, cy, r in [(-90, -200, 60), (-20, -250, 75), (70, -215, 65), (0, -180, 70), (-60, -160, 50), (90, -160, 45)]:
        rr = r * s
        px, py = x + cx * s, base + cy * s
        d = (f"M{px-rr},{py} C{px-rr},{py-rr*0.8} {px-rr*0.3},{py-rr*1.1} {px},{py-rr} "
             f"C{px+rr*0.5},{py-rr*1.1} {px+rr*1.05},{py-rr*0.6} {px+rr},{py} "
             f"C{px+rr*0.8},{py+rr*0.6} {px-rr*0.8},{py+rr*0.6} {px-rr},{py} Z")
        out += ink(d, LA if rnd.random() < 0.5 else "#2B6B49", 2.8)
        out += swirl(px - rr * 0.2, py - rr * 0.1, 0.55 * s, rnd.uniform(0, 360), sw=1.8, color=TRANG)
    return out


def hut(x, base):
    out = ink(f"M{x-64},{base} L{x-64},{base-62} L{x+64},{base-62} L{x+64},{base} Z", "#CDA46B", 2.8)
    out += ink(f"M{x-22},{base} L{x-22},{base-42} L{x+6},{base-42} L{x+6},{base} Z", INK, 1.8)
    roof = (f"M{x-92},{base-54} C{x-74},{base-82} {x-58},{base-110} {x-46},{base-128} "
            f"L{x+46},{base-128} C{x+58},{base-110} {x+74},{base-82} {x+92},{base-54} Z")
    out += ink(roof, THATCH, 3.0)
    for i in range(8):
        rx = x - 72 + i * 20
        out += line(f"M{rx},{base-60} C{rx+3},{base-84} {rx+7},{base-102} {rx+9},{base-120}", 1.3, SON_DARK)
    return out


VIL_BASE = 700
DINH_X = 820
HUTS = (300, 1280)
BANYAN_X = 560


def village():
    out = ""
    out += wrap(lambda xx: banyan(xx, VIL_BASE, 1.0), BANYAN_X)
    out += wrap(lambda xx: dinh(xx, VIL_BASE), DINH_X)
    for hx in HUTS:
        out += wrap(lambda xx: hut(xx, VIL_BASE), hx)
    # flag pole of the dinh courtyard (flag itself is an animated prop)
    out += ink_wide(f"M-20,{VIL_BASE-4} L0,{VIL_BASE-4} C400,{VIL_BASE-10} 800,{VIL_BASE+2} 1200,{VIL_BASE-8} "
                    f"C1400,{VIL_BASE-12} 1500,{VIL_BASE-2} {W},{VIL_BASE-4} L{W+20},{VIL_BASE-4} "
                    f"L{W+20},{VIL_BASE+40} L-20,{VIL_BASE+40} Z", "#A9884F")
    return out


def fields():
    """Rice paddies with little dykes and a river band."""
    top = 715
    out = ink_wide(f"M-20,{top} L{W+20},{top} L{W+20},{H+20} L-20,{H+20} Z", "#6FA06A", 0)
    # paddy rows
    for k, y in enumerate((728, 742, 758, 776)):
        d = f"M-20,{y}"
        for x in range(0, W + 1, 80):
            d += f" Q{x+40},{y + (3 if (x // 80) % 2 else -3)} {x+80},{y}"
        out += contour(d, 1.6, LA_DARK if k % 2 else "#8DBB7A")
    # dykes between paddies (short vertical strokes, periodic)
    for x in range(40, W, 200):
        out += wrap(lambda xx: line(f"M{xx},{top+4} L{xx-14},{top+80}", 2.4, "#A9884F"), x)
    # river
    out += ink_wide(f"M-20,780 C400,772 800,790 1200,778 C1400,774 1500,780 {W+20},780 L{W+20},812 "
                    f"C1200,818 800,806 400,816 C200,820 100,814 -20,812 Z", CHAM_LIGHT, 3)
    for y in (788, 800):
        d = f"M-20,{y}"
        for x in range(0, W + 1, 50):
            d += f" Q{x+25},{y-4} {x+50},{y}"
        out += contour(d, 1.4, TRANG)
    return out


def ground():
    """Dyke road at the bottom: the bird must not touch it."""
    out = ink_wide(f"M-20,{GROUND} L0,{GROUND} C400,{GROUND-6} 800,{GROUND+4} 1200,{GROUND-4} "
                   f"C1400,{GROUND-6} 1500,{GROUND} {W},{GROUND} L{W+20},{GROUND} L{W+20},{H+20} L-20,{H+20} Z",
                   "#C89B58", 4)
    for k, y in enumerate((GROUND + 22, GROUND + 50)):
        d = f"M-20,{y} L0,{y}"
        for x in range(0, W + 1, 100):
            d += f" Q{x+50},{y + (5 if (x // 100) % 2 else -5)} {x+100},{y}"
        out += contour(d, 2.2, "#8E6633")
    rnd = random.Random(5)
    for i in range(22):
        x = rnd.uniform(0, W)
        y = GROUND + rnd.uniform(-2, 2)
        col = SON if i % 4 == 0 else LA
        out += wrap(lambda xx: line(f"M{xx-8},{y} C{xx-9},{y-10} {xx-12},{y-16} {xx-16},{y-22}", 2.4, col)
                    + line(f"M{xx},{y} C{xx},{y-12} {xx+2},{y-20} {xx+5},{y-26}", 2.6, col)
                    + line(f"M{xx+8},{y} C{xx+9},{y-8} {xx+13},{y-12} {xx+18},{y-16}", 2.2, col), x)
    for i in range(9):   # small yellow daisies
        x = rnd.uniform(0, W)
        y = GROUND - 4
        out += wrap(lambda xx: line(f"M{xx},{y} L{xx+2},{y-18}", 1.8, LA_DARK)
                    + "".join(f'<circle cx="{xx+2+math.cos(a)*5:.1f}" cy="{y-20+math.sin(a)*5:.1f}" r="3.2" '
                              f'fill="{VANG}" stroke="{INK}" stroke-width="1.2"/>' for a in [k * 1.2566 for k in range(5)])
                    + f'<circle cx="{xx+2}" cy="{y-20}" r="2.4" fill="{SON}"/>', x)
    return out


# ======================= animated sprites =======================
def sprite(name, inner, w, h, anchor, scale=2):
    ax, ay = anchor
    write_svg_png(os.path.join(PROPS, name), f'<g transform="translate({ax},{ay})">{inner}</g>', (0, 0, w, h), scale)
    SPRITES[name] = {"png": f"props/{name}.png", "size": [w, h], "anchor": [ax, ay], "pngScale": scale}


def festival_flag(phase, h=170, L=110, Hc=62):
    """Co ngu sac: five-colour festival flag (red, yellow, blue, white, green) with a swallow tail."""
    cols = [SON, VANG, CHAM, TRANG, LA]
    out = line(f"M0,0 L0,{-h-12}", 4.2, WOOD_D)
    out += f'<circle cx="0" cy="{-h-14}" r="5" fill="{VANG}" stroke="{INK}" stroke-width="1.6"/>'
    n = 14
    rows = []
    for j in range(6):
        v = j / 5
        pts = []
        for i in range(n + 1):
            u = i / n
            off = 10 * u * math.sin(2 * math.pi * u * 1.1 - phase)
            pts.append((u * L, -h + Hc * v * (1 - 0.1 * u) + off))
        rows.append(pts)
    for j in range(5):
        a, b = rows[j], rows[j + 1]
        d = "M" + " L".join(f2(p) for p in a) + " L" + " L".join(f2(p) for p in reversed(b)) + " Z"
        out += f'<path d="{d}" fill="{cols[j]}"/>'
    outline = "M" + " L".join(f2(p) for p in rows[0]) + " L" + " L".join(f2(p) for p in reversed(rows[-1])) + " Z"
    out += brush(outline, 2.6, INK, taper=0, var=0.2)
    return out


def kite(k):
    """Dieu sao (flute kite) with a fluttering tail."""
    out = ink("M0,-40 L28,0 L0,30 L-28,0 Z", VANG, 2.6)
    out += line("M0,-40 L0,30 M-28,0 L28,0", 1.6, SON_DARK)
    out += spiral(0, -5, 8, 1.3, 0, SON, 1.6)
    d = "M0,30"
    for i in range(1, 9):
        d += f" Q{(-10 if (i + k) % 2 else 10)},{30 + i * 14 - 7} 0,{30 + i * 14}"
    out += line(d, 2.0, SON)
    for i in range(1, 5):
        y = 30 + i * 28
        out += ink(f"M-6,{y} L6,{y} L0,{y+8} Z", LA if i % 2 else SON, 1.2)
    return out


def buffalo_boy():
    """Small grazing buffalo with a boy on its back (nod to the Muc dong print)."""
    out = ink("M-60,0 C-62,-30 -40,-44 0,-44 C34,-44 54,-34 58,-14 C60,0 50,6 40,6 L-50,6 C-58,6 -60,4 -60,0 Z", INK, 2.4)
    out += line("M-50,-16 C-30,-28 10,-30 40,-20", 1.6, TRANG)
    out += spiral(-36, -18, 8, 1.4, 0, TRANG, 1.5) + spiral(30, -18, 7, 1.4, 180, TRANG, 1.5)
    for lx in (-46, -30, 26, 42):
        out += ink(capsule((lx, 2), (lx + 2, 34), 5, 4), INK, 1.6)
    out += ink("M52,-30 C70,-36 82,-26 84,-12 C86,0 74,6 64,0 C58,-6 54,-18 52,-30 Z", INK, 2.2)
    out += line("M60,-34 C56,-50 68,-56 78,-50 M66,-32 C74,-44 88,-42 90,-34", 2.4, TRANG)
    out += f'<circle cx="74" cy="-20" r="2.4" fill="{TRANG}"/>'
    out += line("M-58,-8 C-70,-4 -74,10 -70,22", 2.0)
    # boy
    out += ink("M-14,-44 C-14,-62 6,-62 6,-44 Z", DA, 2.0)
    out += ink("M-12,-58 A12,12 0 1 1 12,-58 A12,12 0 1 1 -12,-58 Z", DA, 2.0)
    out += ink("M-4,-71 C-6,-78 2,-80 6,-74 Z", INK, 1.2)
    out += line("M2,-60 C4,-62 7,-62 8,-60", 1.2) + f'<circle cx="5" cy="-60" r="1.3" fill="{INK}"/>'
    out += ink("M-16,-48 L8,-48 L10,-40 L-18,-40 Z", SON, 1.6)
    out += line("M6,-52 L34,-66", 2.2, VANG)                # little flute
    return out


def make_sprites():
    os.makedirs(PROPS, exist_ok=True)
    for k in range(6):
        sprite(f"flag5_{k}", festival_flag(2 * math.pi * k / 6), 150, 200, (20, 192))
    sprite("smoke_light", smoke_puff("#9A8C7E"), 120, 90, (60, 50))
    for k in range(2):
        sprite(f"kite_{k}", kite(k), 80, 180, (40, 46))
    sprite("bamboo_0", bamboo_clump(3), 300, 340, (150, 330))
    sprite("bamboo_1", bamboo_clump(9, 0.9), 300, 340, (150, 330))
    for k in range(3):
        sprite(f"cloud_{k}", cloud(k + 4), 220, 110, (110, 55))
    sprite("buffalo", buffalo_boy(), 200, 130, (90, 90))
    sun = ""
    for i in range(12):
        sun += (f'<g transform="rotate({i * 30}) translate(116,0) rotate(90)">'
                + line("M-12,8 C-14,-8 0,-14 8,-8 C12,-3 8,4 3,3", 3, SON) + '</g>')
    sprite("sun_rays", sun, 280, 280, (140, 140))


def props():
    P = [{"layer": "sky", "type": "spin", "sprite": "sun_rays", "x": 1250, "y": 230, "speed": 5}]
    for i, (x, y, v) in enumerate([(200, 150, 8), (700, 110, 5), (1050, 220, 10), (1450, 140, 6)]):
        P.append({"layer": "clouds", "type": "drift", "sprite": f"cloud_{i % 3}", "x": x, "y": y, "vx": -v, "bob": 4})
    P.append({"layer": "clouds", "type": "anim", "frames": ["kite_0", "kite_1"], "fps": 5, "x": 420, "y": 300, "scale": 0.8})
    P.append({"layer": "village", "type": "anim", "frames": [f"flag5_{k}" for k in range(6)], "fps": 8,
              "x": DINH_X + 230, "y": VIL_BASE - 2, "scale": 0.95})
    P.append({"layer": "village", "type": "anim", "frames": [f"flag5_{k}" for k in range(6)], "fps": 7,
              "x": DINH_X - 240, "y": VIL_BASE - 2, "scale": 0.8})
    for hx in HUTS:
        P.append({"layer": "village", "type": "smoke", "x": hx + 30, "y": VIL_BASE - 130, "sprite": "smoke_light",
                  "rate": 1.2, "life": 4.5, "rise": 34, "grow": 1.3, "scale": 0.45})
    for x, sp, s in ((80, "bamboo_0", 0.9), (420, "bamboo_1", 0.85), (1120, "bamboo_0", 0.95), (1480, "bamboo_1", 0.9)):
        P.append({"layer": "village", "type": "sway", "sprite": sp, "x": x, "y": VIL_BASE, "scale": s, "amp": 2.0, "speed": 1.2})
    P.append({"layer": "fields", "type": "sway", "sprite": "buffalo", "x": 1000, "y": 742, "scale": 0.7, "amp": 0.8, "speed": 0.8})
    return P


def write_layer(name, inner, paper=False):
    p = os.path.join(OUT, f"layer_{name}")
    write_svg_png(p, inner, (0, 0, W, H), 1)
    if paper:
        tex = Image.open(os.path.join(OUT, "paper.png")).convert("RGBA")
        bg = Image.new("RGBA", (W, H))
        for x in range(0, W, tex.width):
            for y in range(0, H, tex.height):
                bg.paste(tex, (x, y))
        bg.alpha_composite(Image.open(p + ".png").convert("RGBA"))
        bg.convert("RGB").save(p + ".png")


def main():
    make_paper(os.path.join(OUT, "paper.png"))
    layers = [
        ("sky", sky(), 0.0, True),
        ("clouds", "", 0.05, False),
        ("mountains", mountains(), 0.12, False),
        ("village", village(), 0.3, False),
        ("fields", fields(), 0.6, False),
        ("ground", ground(), 1.0, False),
    ]
    for name, inner, _, paper in layers:
        if inner or paper:
            write_layer(name, inner, paper)
    make_sprites()
    stage = {
        "size": [W, H], "floorY": GROUND, "groundY": GROUND, "tileWidth": W, "paper": "paper.png", "wind": 18,
        "layers": [{"id": n, "png": (f"layer_{n}.png" if (inner or paper) else None), "parallax": p, "front": False}
                   for n, inner, p, paper in layers],
        "sprites": SPRITES,
        "props": props(),
        "note": "same format as background_giong/stage.json. Bamboo columns (fx_flappy) are drawn between "
                "'fields' and 'ground'. Touching groundY ends the run.",
    }
    with open(os.path.join(OUT, "stage.json"), "w") as f:
        json.dump(stage, f, indent=2)
    print("ok", len(SPRITES), "sprites", len(stage["props"]), "props")


if __name__ == "__main__":
    main()
