"""Parallax war background (Thanh Giong era) in Dong Ho woodblock style.

Static layers: 1600 x 900, tile horizontally (draw at x and x + 1600).
Animated things are separate sprites in props/ and placed by stage.json
'props' (each prop belongs to a layer and scrolls with it):
  anim   : frame list played at fps (flags, fires)
  sway   : one sprite rotated around its anchor (bamboo, grass)
  smoke  : emitter, spawns puffs that rise, grow, drift with the wind and fade
  drift  : moves on its own (clouds) and wraps
  flock  : crows flying across the sky, 3 flap frames
  spin   : slow rotation (sun rays)
  catapult: base + arm that swings and throws a far stone
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dongho_lib import *  # noqa
from PIL import Image

OUT = os.path.dirname(os.path.abspath(__file__))
PROPS = os.path.join(OUT, "props")
W, H = 1600, 900
FLOOR = 780
SMOKE = "#4C433C"
SMOKE_LIGHT = "#948779"
WOOD, WOOD_D = "#8A5A36", "#5E3A22"
THATCH = "#C49A52"
EARTH = "#C89B58"
EARTH_D = "#8E6633"
SPRITES = {}


def wrap(fn, x, *a, **k):
    return "".join(fn(x + o, *a, **k) for o in (-W, 0, W))


def ink_wide(d, fill, sw=3.6):
    """Full-width shapes: very even outline so the tile edges match."""
    out = f'<path d="{d}" fill="{fill}"/>'
    if sw:
        out += brush(d, sw, INK, taper=0, var=0.06)
    return out


def contour(d, sw, color):
    return brush(d, sw, color, taper=0, var=0.08)


def ridge(base, peaks, step=8):
    pts = []
    for x in range(0, W + step, step):
        h = 0
        for px, ph, pw in peaks:
            for o in (-W, 0, W):
                dd = abs(x - (px + o)) / pw
                if dd < 1:
                    h = max(h, ph * (0.5 + 0.5 * math.cos(dd * math.pi)) ** 0.8)
        pts.append((x, base - h))
    return pts


def poly(pts, bottom=H):
    return (f"M-20,{pts[0][1]:.1f} L" + " L".join(f2(p) for p in pts)
            + f" L{W+20},{pts[-1][1]:.1f} L{W+20},{bottom+20} L-20,{bottom+20} Z")


def poly_line(pts, dy):
    return f"M-20,{pts[0][1]+dy:.1f} L" + " L".join(f"{p[0]:.1f},{p[1] + dy:.1f}" for p in pts) + \
        f" L{W+20},{pts[-1][1]+dy:.1f}"


# ======================= STATIC LAYERS =======================
def sky():
    # flat warm bands near the horizon (no gradients in a woodblock print)
    band = (f'<path d="M0,430 C400,420 800,440 1200,424 C1400,418 1500,428 {W},430 L{W},{H} L0,{H} Z" '
            f'fill="#EBCB95"/>'
            f'<path d="M0,520 C400,512 800,530 1200,514 C1400,508 1500,518 {W},520 L{W},{H} L0,{H} Z" '
            f'fill="#E5B98A"/>')
    sx, sy, r = 1180, 250, 100
    sun = (ink(f"M{sx-r},{sy} A{r},{r} 0 1 1 {sx+r},{sy} A{r},{r} 0 1 1 {sx-r},{sy} Z", SON, 4)
           + spiral(sx, sy, 46, 1.8, 0, VANG, 3.2) + spiral(sx, sy, 72, 1.0, 180, SON_DARK, 2.4))
    return band + sun


def mountains():
    back = ridge(560, [(80, 300, 220), (420, 240, 200), (760, 330, 240), (1100, 250, 190),
                       (1400, 310, 230)])
    front = ridge(610, [(250, 180, 200), (600, 140, 170), (950, 200, 230), (1300, 160, 180),
                        (1560, 120, 150)])
    out = ink_wide(poly(back), CHAM_LIGHT)
    for dy in (24, 50):
        out += contour(poly_line(back, dy), 2.0, TRANG)
    out += ink_wide(poly(front), LA)
    for dy in (20, 42):
        out += contour(poly_line(front, dy), 2.0, TRANG)
    rnd = random.Random(3)
    for _ in range(34):
        i = rnd.randrange(len(front))
        x, y = front[i]
        out += ink(f"M{x},{y+4} L{x-7},{y+20} L{x+7},{y+20} Z", LA_DARK, 1.4)
    return out


def fortress(x):
    y = 640
    out = ""
    for i in range(28):
        lx = x - 260 + i * 19
        top = y - 70 - (i % 3) * 6
        out += ink(f"M{lx},{y+20} L{lx},{top+8} L{lx+8},{top} L{lx+16},{top+8} L{lx+16},{y+20} Z",
                   WOOD, 2.2)
    out += line(f"M{x-262},{y-28} L{x+272},{y-28}", 3, WOOD_D)
    for tx in (x - 250, x + 250):
        out += ink(f"M{tx-34},{y+20} L{tx-26},{y-150} L{tx+26},{y-150} L{tx+34},{y+20} Z", WOOD, 3)
        out += line(f"M{tx-30},{y-60} L{tx+30},{y-110} M{tx+30},{y-60} L{tx-30},{y-110}", 2.2)
        out += ink(f"M{tx-50},{y-150} L{tx},{y-200} L{tx+50},{y-150} Z", SON_DARK, 3)
    out += ink(f"M{x-60},{y+20} L{x-60},{y-90} Q{x},{y-130} {x+60},{y-90} L{x+60},{y+20} Z", WOOD_D, 3)
    out += line(f"M{x},{y-112} L{x},{y+20} M{x-60},{y-40} L{x+60},{y-40}", 2.2)
    return out


CAMP_FORT = 980
CAMP_TENTS = (180, 320, 1450)


def tent(xx):
    return (ink(f"M{xx-50},660 C{xx-30},630 {xx-12},600 {xx},590 C{xx+12},600 {xx+30},630 {xx+50},660 Z",
                VANG_LIGHT, 2.8)
            + line(f"M{xx},592 L{xx},660 M{xx-6},604 C{xx-12},620 {xx-18},640 {xx-24},660", 1.8))


def camp():
    out = ink_wide(f"M-20,655 L0,655 C400,645 800,662 1200,650 C1400,646 1500,652 {W},655 "
                   f"L{W+20},655 L{W+20},{H+20} L-20,{H+20} Z", "#D2AE70", 0)
    out += wrap(fortress, CAMP_FORT)
    for tx in CAMP_TENTS:
        out += wrap(tent, tx)
    return out


def hut(x, base):
    out = ink(f"M{x-70},{base} L{x-70},{base-70} L{x+70},{base-70} L{x+70},{base} Z", "#CDA46B", 3)
    out += ink(f"M{x-25},{base} L{x-25},{base-45} L{x+5},{base-45} L{x+5},{base} Z", INK, 2)
    roof = (f"M{x-100},{base-60} C{x-80},{base-90} {x-62},{base-120} {x-50},{base-140} "
            f"L{x+50},{base-140} C{x+62},{base-120} {x+80},{base-90} {x+100},{base-60} Z")
    out += ink(roof, THATCH, 3.2)
    for i in range(9):
        rx = x - 80 + i * 20
        out += line(f"M{rx},{base-66} C{rx+3},{base-90} {rx+7},{base-110} {rx+10},{base-130}", 1.4, SON_DARK)
    out += line(f"M{x-48},{base-140} L{x+48},{base-140}", 4, SON_DARK)
    return out


VILLAGE_BASE = 720
HUTS = (360, 1050)


def village():
    out = ""
    for hx in HUTS:
        out += wrap(lambda xx: hut(xx, VILLAGE_BASE), hx)
    out += ink_wide(f"M-20,{VILLAGE_BASE-4} L0,{VILLAGE_BASE-4} C300,{VILLAGE_BASE-12} 600,{VILLAGE_BASE+2} "
                    f"900,{VILLAGE_BASE-8} C1200,{VILLAGE_BASE-16} 1400,{VILLAGE_BASE} {W},{VILLAGE_BASE-4} "
                    f"L{W+20},{VILLAGE_BASE-4} L{W+20},{VILLAGE_BASE+60} L-20,{VILLAGE_BASE+60} Z", "#A77E48")
    out += contour(f"M-20,{VILLAGE_BASE+14} C400,{VILLAGE_BASE+8} 800,{VILLAGE_BASE+20} {W+20},{VILLAGE_BASE+12}",
                   1.8, VANG_LIGHT)
    return out


def ground():
    out = ink_wide(f"M-20,{FLOOR-40} L0,{FLOOR-40} C400,{FLOOR-46} 800,{FLOOR-34} 1200,{FLOOR-44} "
                   f"C1400,{FLOOR-48} 1500,{FLOOR-40} {W},{FLOOR-40} L{W+20},{FLOOR-40} L{W+20},{H+20} L-20,{H+20} Z",
                   EARTH, 4)
    for k, y in enumerate((FLOOR - 8, FLOOR + 32, FLOOR + 72, FLOOR + 106)):
        d = f"M-20,{y} L0,{y}"
        for x in range(0, W + 1, 100):
            d += f" Q{x+50},{y + (6 if (x//100) % 2 else -6)} {x+100},{y}"
        out += contour(d, 2.2 if k else 2.6, EARTH_D)
    rnd = random.Random(11)
    for _ in range(12):
        x = rnd.uniform(0, W)
        y = rnd.uniform(FLOOR + 15, H - 30)
        rx = rnd.uniform(10, 20)
        out += wrap(lambda xx: ink(f"M{xx-rx},{y} C{xx-rx},{y-rx} {xx+rx},{y-rx} {xx+rx},{y} "
                                   f"C{xx+rx*0.6},{y+6} {xx-rx*0.6},{y+6} {xx-rx},{y} Z", XAM, 2.2), x)
    # small grass along the road edge: green and red blades like the buffalo print
    for i in range(18):
        x = rnd.uniform(0, W)
        y = FLOOR - 38 + rnd.uniform(-3, 3)
        col = SON if i % 3 == 0 else LA
        out += wrap(lambda xx: line(f"M{xx-8},{y} C{xx-9},{y-10} {xx-12},{y-18} {xx-16},{y-24}", 2.6, col)
                    + line(f"M{xx},{y} C{xx},{y-12} {xx+2},{y-22} {xx+5},{y-30}", 2.8, col)
                    + line(f"M{xx+8},{y} C{xx+9},{y-8} {xx+13},{y-14} {xx+18},{y-18}", 2.4, col), x)
    for _ in range(5):
        x = rnd.uniform(0, W)
        y = rnd.uniform(FLOOR + 10, H - 40)
        a = rnd.uniform(-60, -20)
        out += wrap(lambda xx: f'<g transform="translate({xx:.1f},{y:.1f}) rotate({a:.1f})">'
                    + line("M0,0 L60,0", 3.2, WOOD_D)
                    + ink("M60,-6 L76,0 L60,6 Z", XAM, 1.8)
                    + ink("M0,-6 L-12,-10 L-8,0 L-12,10 L0,6 Z", TRANG, 1.4) + '</g>', x)
    return out


def foreground():
    return wrap(lambda xx: f'<g transform="translate({xx},{H-10}) rotate(-70)">'
                + line("M0,0 L170,0", 6, WOOD_D)
                + ink("M170,-10 L210,0 L170,10 Z", XAM, 2.2)
                + ink("M150,-8 L162,-8 L162,8 L150,8 Z", SON, 1.6) + '</g>', 760)


# ======================= ANIMATED SPRITES =======================
def sprite(name, inner, w, h, anchor, scale=2):
    """inner drawn with the anchor at (0,0)."""
    ax, ay = anchor
    write_svg_png(os.path.join(PROPS, name), f'<g transform="translate({ax},{ay})">{inner}</g>',
                  (0, 0, w, h), scale)
    SPRITES[name] = {"png": f"props/{name}.png", "size": [w, h], "anchor": [ax, ay], "pngScale": scale}


def flag(phase, col, emblem_col, h=120, L=86, Hc=46):
    """Swallow-tail war banner on a pole, base at (0,0). phase in [0, 2pi)."""
    top, bot = [], []
    n = 14
    for i in range(n + 1):
        u = i / n
        off = 9 * u * math.sin(2 * math.pi * u * 1.1 - phase)
        x = u * L * (1 - 0.05 * abs(math.sin(phase)))
        top.append((x, -h + off))
        bot.append((x, -h + Hc * (1 - 0.12 * u) + off))
    tail = (top[-1][0] - 16, (top[-1][1] + bot[-1][1]) / 2)
    d = ("M" + " L".join(f2(p) for p in top) + f" L{f2(tail)} L"
         + " L".join(f2(p) for p in reversed(bot)) + " Z")
    em_u = 0.42
    em_off = 9 * em_u * math.sin(2 * math.pi * em_u * 1.1 - phase)
    ex, ey = em_u * L, -h + Hc / 2 + em_off
    emblem = (ink(f"M{ex-10:.1f},{ey:.1f} A10,10 0 1 1 {ex+10:.1f},{ey:.1f} A10,10 0 1 1 {ex-10:.1f},{ey:.1f} Z",
                  emblem_col, 1.8)
              + spiral(ex, ey, 6, 1.2, 0, INK if emblem_col != INK else TRANG, 1.4))
    trim = line("M" + " L".join(f2((p[0], p[1] + 5)) for p in top[1:-2]), 1.4, VANG)
    pole = (line(f"M0,0 L0,{-h-10}", 4, WOOD_D)
            + f'<circle cx="0" cy="{-h-12}" r="4" fill="{VANG}" stroke="{INK}" stroke-width="1.6"/>')
    return pole + ink(d, col, 2.6) + trim + emblem


def fire_cluster(k):
    return (flame(-22, 0, 0.62, -8, k=k) + flame(20, 0, 0.55, 10, k=(k + 2))
            + flame(0, 0, 0.85, 0, k=(k + 1)))


def smoke_puff(col):
    d = ("M-40,4 C-46,-22 -16,-38 0,-26 C14,-42 46,-30 42,-6 C54,6 40,24 22,18 "
         "C10,30 -14,28 -22,18 C-40,24 -50,14 -40,4 Z")
    return (ink(d, col, 2.6) + line("M-18,2 C-20,-12 -4,-16 0,-6 C2,0 -4,3 -8,0", 2.0, PAPER)
            + line("M14,-8 C12,-20 26,-22 28,-12", 1.8, PAPER))


def crow(k):
    body = ink("M-16,0 C-10,-8 10,-8 20,-2 L30,-4 L22,2 C12,8 -8,8 -16,0 Z", INK, 1.4)
    wings = [
        "M-4,-4 C-10,-22 -22,-34 -34,-38 C-26,-24 -18,-12 4,-2 Z",
        "M-4,-4 C-14,-10 -28,-12 -40,-8 C-28,-2 -16,2 4,-2 Z",
        "M-4,-2 C-12,8 -22,18 -32,22 C-24,10 -14,2 4,0 Z",
    ][k]
    return ink(wings, INK, 1.4) + body + f'<circle cx="16" cy="-3" r="1.4" fill="{TRANG}"/>'


def bamboo_clump(seed, s=1.0):
    rnd = random.Random(seed)
    out = ""
    stalks = []
    for i in range(7):
        bx = (i - 3) * 14 * s
        lean = (i - 3) * 9 * s + rnd.uniform(-6, 6)
        top = -rnd.uniform(220, 300) * s
        stalks.append((bx, lean, top))
        d = f"M{bx:.1f},0 Q{bx+lean*0.3:.1f},{top/2:.1f} {bx+lean:.1f},{top:.1f}"
        out += brush(d, 7 * s, INK, taper=0.25, var=0.1) + brush(d, 3.6 * s, LA, taper=0.3, var=0.1)
        for k in range(1, 5):
            t = k / 5
            px = bx + lean * 0.3 * 2 * t * (1 - t) + lean * t * t
            py = top * t
            out += line(f"M{px-4*s:.1f},{py:.1f} L{px+4*s:.1f},{py:.1f}", 1.4, INK)
    for j in range(10):
        bx, lean, top = stalks[j % 7]
        lx = bx + lean + rnd.uniform(-60, 60) * s
        ly = top * rnd.uniform(0.55, 1.0)
        for k in range(5):
            a = rnd.uniform(-170, -10)
            out += leaf(lx, ly, a, 0.55 * s, LA if k % 2 else LA_DARK, LA_DARK if k % 2 else LA)
    return out


def grass_tuft(seed, cols):
    rnd = random.Random(seed)
    out = ""
    for i in range(9):
        a = -90 + (i - 4) * 13 + rnd.uniform(-5, 5)
        L = rnd.uniform(70, 130)
        ex, ey = math.cos(math.radians(a)) * L, math.sin(math.radians(a)) * L
        bend = rnd.uniform(-14, 14)
        d = f"M-6,0 Q{ex*0.4+bend:.1f},{ey*0.6:.1f} {ex:.1f},{ey:.1f} Q{ex*0.4+8+bend:.1f},{ey*0.6:.1f} 6,0 Z"
        out += ink(d, cols[i % len(cols)], 2.2)
    return out


def cloud(seed):
    rnd = random.Random(seed)
    s = rnd.uniform(0.9, 1.3)
    return cloud_puff(0, 0, s) + swirl(-70 * s, 18 * s, 0.6, 0, sw=2.0)


def sun_rays():
    out = ""
    for i in range(12):
        a = i * 30
        out += (f'<g transform="rotate({a}) translate(128,0) rotate(90)">'
                + line("M-12,8 C-14,-8 0,-14 8,-8 C12,-3 8,4 3,3", 3, SON) + '</g>')
    return out


def make_sprites():
    os.makedirs(PROPS, exist_ok=True)
    F = 6
    for k in range(F):
        ph = 2 * math.pi * k / F
        sprite(f"flag_black_{k}", flag(ph, INK, SON), 130, 150, (20, 140))
        sprite(f"flag_red_{k}", flag(ph, SON, VANG), 130, 150, (20, 140))
    for k in range(4):
        sprite(f"fire_{k}", fire_cluster(k), 120, 100, (60, 92))
    sprite("smoke_dark", smoke_puff(SMOKE), 120, 90, (60, 50))
    sprite("smoke_light", smoke_puff(SMOKE_LIGHT), 120, 90, (60, 50))
    for k in range(3):
        sprite(f"crow_{k}", crow(k), 90, 80, (45, 42))
    sprite("bamboo_0", bamboo_clump(1), 300, 340, (150, 330))
    sprite("bamboo_1", bamboo_clump(5, 0.9), 300, 340, (150, 330))
    sprite("grass_0", grass_tuft(2, [LA_DARK, LA]), 260, 150, (130, 140))
    sprite("grass_1", grass_tuft(4, [LA, SON, LA_DARK]), 260, 150, (130, 140))
    for k in range(3):
        sprite(f"cloud_{k}", cloud(k + 1), 220, 110, (110, 55))
    sprite("sun_rays", sun_rays(), 300, 300, (150, 150))


# ======================= stage =======================
def props():
    P = []
    flags_b = [f"flag_black_{k}" for k in range(6)]
    flags_r = [f"flag_red_{k}" for k in range(6)]
    fires = [f"fire_{k}" for k in range(4)]
    P.append({"layer": "sky", "type": "spin", "sprite": "sun_rays", "x": 1180, "y": 250, "speed": 6})
    for i, (x, y, v) in enumerate([(160, 130, 9), (640, 90, 6), (980, 200, 11), (1420, 120, 7)]):
        P.append({"layer": "clouds", "type": "drift", "sprite": f"cloud_{i % 3}", "x": x, "y": y, "vx": -v,
                  "bob": 4})
    P.append({"layer": "sky", "type": "flock", "frames": ["crow_0", "crow_1", "crow_2"], "count": 5,
              "y": [120, 260], "vx": [-70, -40], "fps": 7, "scale": [0.5, 0.8]})
    fx = CAMP_FORT
    for tx, fr in ((fx - 250, flags_b), (fx + 250, flags_r)):
        P.append({"layer": "camp", "type": "anim", "frames": fr, "fps": 8, "x": tx, "y": 444, "scale": 0.8})
    P.append({"layer": "camp", "type": "anim", "frames": flags_r, "fps": 9, "x": fx - 120, "y": 600, "scale": 1.0})
    P.append({"layer": "camp", "type": "anim", "frames": flags_b, "fps": 7, "x": fx + 130, "y": 600, "scale": 1.0})
    for t in CAMP_TENTS:
        P.append({"layer": "camp", "type": "anim", "frames": flags_b, "fps": 8, "x": t, "y": 592, "scale": 0.55})
    for x, s in ((fx - 160, 0.6), (fx + 60, 0.75), (fx + 190, 0.55)):
        P.append({"layer": "camp", "type": "anim", "frames": fires, "fps": 10, "x": x, "y": 574, "scale": s})
    P.append({"layer": "camp", "type": "smoke", "x": fx + 60, "y": 540, "sprite": "smoke_dark",
              "rate": 2.2, "life": 5, "rise": 46, "grow": 1.6, "scale": 0.7})
    P.append({"layer": "camp", "type": "smoke", "x": 250, "y": 600, "sprite": "smoke_light",
              "rate": 1.6, "life": 5, "rise": 40, "grow": 1.5, "scale": 0.55})
    for x in (560, 1330):
        P.append({"layer": "camp", "type": "catapult", "x": x, "y": 628, "scale": 0.55, "period": 4.5})
    for x, sp, s in ((120, "bamboo_0", 1.0), (640, "bamboo_1", 0.95), (770, "bamboo_0", 1.08),
                     (1300, "bamboo_1", 1.0)):
        P.append({"layer": "village", "type": "sway", "sprite": sp, "x": x, "y": VILLAGE_BASE, "scale": s,
                  "amp": 2.2, "speed": 1.3})
    P.append({"layer": "village", "type": "anim", "frames": fires, "fps": 11, "x": 350, "y": VILLAGE_BASE - 126,
              "scale": 1.2})
    P.append({"layer": "village", "type": "smoke", "x": 360, "y": VILLAGE_BASE - 170, "sprite": "smoke_dark",
              "rate": 2.6, "life": 4.5, "rise": 60, "grow": 1.8, "scale": 0.8, "embers": True})
    for x, sp in ((90, "grass_0"), (520, "grass_1"), (980, "grass_0"), (1360, "grass_1")):
        P.append({"layer": "fg", "type": "sway", "sprite": sp, "x": x, "y": H + 6, "scale": 1.0,
                  "amp": 4, "speed": 2.0})
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
    for f in os.listdir(OUT):
        if f.startswith("layer_"):
            os.remove(os.path.join(OUT, f))
    make_paper(os.path.join(OUT, "paper.png"))
    layers = [
        ("sky", sky(), 0.0, True),
        ("clouds", "", 0.04, False),
        ("mountains", mountains(), 0.12, False),
        ("camp", camp(), 0.25, False),
        ("village", village(), 0.5, False),
        ("ground", ground(), 1.0, False),
        ("fg", foreground(), 1.35, False),
    ]
    for name, inner, _, paper in layers:
        if inner or paper:
            write_layer(name, inner, paper)
    make_sprites()
    stage = {
        "size": [W, H],
        "floorY": FLOOR,
        "tileWidth": W,
        "paper": "paper.png",
        "wind": 22,
        "layers": [{"id": n, "png": (f"layer_{n}.png" if (inner or paper) else None), "parallax": p,
                    "front": n == "fg"} for n, inner, p, paper in layers],
        "sprites": SPRITES,
        "props": props(),
        "note": "draw back to front; layer x = -(scroll * parallax) mod 1600, drawn twice; props scroll "
                "with their layer; fg goes over the puppet. Horse runs -> scroll grows; front legs up -> "
                "scroll stops (props keep animating).",
    }
    with open(os.path.join(OUT, "stage.json"), "w") as f:
        json.dump(stage, f, indent=2)
    print("layers ok,", len(SPRITES), "sprites,", len(stage["props"]), "props")


if __name__ == "__main__":
    main()
