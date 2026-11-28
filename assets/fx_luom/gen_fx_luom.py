"""Hazards, items and UI for the Luom runner, as paper-cut pieces (same look as the puppet).

  plane_0/1     enemy propeller plane flying left (2 propeller frames), iron-grey paper, rivets
  bomb          falling bomb (points down)
  explode_0..3  paper-cut blast: curling flame tongues, then scroll-cloud smoke
  crater        bomb crater left on the path (jump over it)
  bullet        tracer flying left at head height (duck under it)
  sheaf, stump, fence   things on the field edge to jump over
  letter        folded triangle letter to pick up (into the satchel)
  heart, heart_empty    health (10)
  note_0/1      whistle notes floating from Luom's lips
  dust          dust puff from his bare feet
  curtain_panel, curtain_top   stage curtain: red lacquer cloth, gold drum-sun and wave borders
fx.json: size, anchor, pngScale per sprite, plus a collision box for the hazards.
"""
import json, math, os, random, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from dongho_lib import write_svg_png, brush, capsule, lerp, f2  # noqa
from paper_lib import *  # noqa

OUT = os.path.dirname(os.path.abspath(__file__))
MANIFEST = {}


def save(name, inner, w, h, anchor, scale=2, shadow=True, box=None):
    write_svg_png(os.path.join(OUT, name), f'{defs()}<g transform="translate({anchor[0]},{anchor[1]})">{inner}</g>', (0, 0, w, h), scale,
                  texture=lambda p: sprite_texture(p, shadow))
    MANIFEST[name] = {"png": f"{name}.png", "size": [w, h], "anchor": list(anchor), "pngScale": scale}
    if box:
        MANIFEST[name]["box"] = box          # [x0, y0, x1, y1] relative to the anchor (design units)


# ---------------- enemy plane + bomb ----------------
def plane(k):
    out = cut("M70,-16 L100,-50 L116,-50 L112,-10 Z", IRON_D, w=0.6)                     # tail fin
    out += incise("M86,-24 L106,-46", 1.0, IRON_D, 0.5)
    body = "M-116,-2 C-108,-18 -60,-22 20,-20 C70,-18 104,-14 120,-6 L124,4 C100,10 60,14 0,14 C-60,14 -104,10 -116,-2 Z"
    out += cut(body, IRON)
    out += facet([(-110, -6), (-60, -18), (20, -18), (110, -10), (118, -4), (20, -8), (-60, -6)], IRON_L)   # lit top
    out += cut("M-58,-18 C-50,-34 -20,-36 -6,-20 Z", mix(IRON_L, NGA, 0.3), w=0.6)         # canopy
    out += incise("M-40,-20 L-34,-32 M-24,-20 L-22,-34", 0.9, IRON_L, 0.4)
    for x in (-90, -40, 10, 60):                                                          # panel seams
        out += incise(f"M{x},-16 L{x + 2},12", 1.0, IRON, 0.5)
    out += punch_row((-100, 4), (110, 2), 22, 1.2, IRON_D)                                # rivets
    out += cut("M84,2 L116,-2 L118,10 L88,12 Z", IRON_D, w=0.6)                           # tail plane
    out += cut("M-44,2 L40,4 L30,28 L-54,26 Z", IRON_D, w=0.6)                            # wing
    out += incise("M-40,14 L34,16", 1.0, IRON_D, 0.5)
    out += disc(-6, 14, 7, IRON_L)
    out += cut("M-124,-6 L-112,-8 L-112,8 L-124,6 Z", BRONZE_D, w=0.5)                    # nose cone
    if k == 0:
        out += cut("M-128,-34 L-122,-34 L-124,34 L-130,34 Z", mix(IRON_D, NGA, 0.2), w=0.5)
    else:
        out += f'<ellipse cx="-126" cy="0" rx="5" ry="34" fill="{NGA}" opacity="0.35"/>'
        out += cut("M-132,-6 L-120,-6 L-122,6 L-130,6 Z", mix(IRON_D, NGA, 0.2), w=0.5)
    out += rivet(-124, 0, 3)
    return out


def bomb():
    out = cut("M-12,-36 L12,-36 L8,-22 L-8,-22 Z", IRON_D, w=0.6)                          # fins
    out += cut("M-16,-46 L-4,-28 L-12,-26 Z M16,-46 L4,-28 L12,-26 Z", IRON_D, w=0.6)
    body = "M-14,-24 C-16,-6 -14,20 0,44 C14,20 16,-6 14,-24 C8,-28 -8,-28 -14,-24 Z"
    out += cut(body, IRON)
    out += facet([(-10, -22), (-4, -24), (-4, 30), (-10, 10)], IRON_L)
    out += cut("M-15,-6 L15,-6 L15,2 L-15,2 Z", SON_D, w=0.5)                              # band
    out += punch_row((-12, -2), (12, -2), 5, 1.0, darker(SON_D, 0.6))
    return out


def explosion(k):
    """0: flash, 1: big flames, 2: flames + smoke, 3: smoke clouds."""
    rnd = random.Random(10 + k)
    out = ""
    if k < 3:
        n = [10, 14, 12][k]
        R = [44, 70, 60][k]
        for i in range(n):
            a = -90 + (i - n / 2) * (180 / n) * 1.6 + rnd.uniform(-8, 8)
            out += flame_tongue(0, 0, R * rnd.uniform(0.8, 1.25), a, R * 0.24, SON, 1 if i % 2 else -1)
        for i in range(n - 3):
            a = -90 + (i - (n - 3) / 2) * (150 / n) * 1.6 + rnd.uniform(-8, 8)
            out += flame_tongue(0, 4, R * rnd.uniform(0.5, 0.8), a, R * 0.18, VANG, 1 if i % 2 else -1)
        out += f'<circle cx="0" cy="4" r="{R * 0.36:.1f}" fill="{VANG_L}"/>'
        out += incise(spiral_d(0, 4, R * 0.26, 1.6), 1.2, VANG_L, 0.6)
        for i in range(5):
            a = math.radians(-160 + i * 35)
            out += incise(spiral_d(math.cos(a) * R * 0.7, math.sin(a) * R * 0.7 + 4, R * 0.12, 1.4, a, 1), 1.0, SON, 0.5)
    if k >= 2:
        col = mix(SMOKE, NAU_D, 0.25)
        sc = 0.7 if k == 2 else 0.95
        out = f'<g transform="translate(0,{-50 if k == 2 else -30}) scale({sc})">{scroll_cloud(1.0, col, 5 + k)}</g>' + out
        if k == 3:
            out += f'<g transform="translate(-30,16) scale(0.55)">{scroll_cloud(1.0, mix(col, NGA, 0.2), 9)}</g>'
            out += f'<g transform="translate(40,20) scale(0.45)">{scroll_cloud(1.0, mix(col, NGA, 0.1), 11)}</g>'
    # paper debris
    if k in (1, 2):
        for i in range(6):
            x, y = rnd.uniform(-90, 90), rnd.uniform(-110, -20)
            out += f'<path d="M{x:.0f},{y:.0f} l8,-3 l-2,8 Z" fill="{EARTH_D}"/>'
    return out


def crater():
    out = cut("M-96,4 C-80,-14 -40,-16 0,-14 C40,-16 80,-14 96,4 C70,16 -70,16 -96,4 Z", EARTH_D)
    out += cut("M-74,2 C-50,-8 50,-8 74,2 C50,10 -50,10 -74,2 Z", darker(EARTH_D, 0.55), w=0.5)
    out += incise("M-60,-6 C-30,-12 30,-12 60,-6", 1.0, EARTH_D, 0.5)
    for x in (-90, -62, -30, 30, 64, 88):                                                  # clods
        out += cut(f"M{x - 8},-8 C{x - 6},-18 {x + 6},-18 {x + 8},-8 Z", EARTH, w=0.5)
    return out


def bullet():
    out = f'<path d="M0,-3 L70,-1.5 L74,0 L70,1.5 L0,3 Z" fill="{VANG_L}" opacity="0.55"/>'   # streak
    out += cut("M-8,0 C-6,-6 6,-7 18,-5 L18,5 C6,7 -6,6 -8,0 Z", BRONZE)
    out += facet([(-6, -2), (16, -4), (16, -1), (-4, 0)], BRONZE_L)
    out += cut("M18,-5 L24,-6 L24,6 L18,5 Z", BRONZE_D, w=0.4)
    out += flame_tongue(24, 0, 26, 0, 4.5, SON, 1)
    return out


def sheaf():
    out = ""
    for i in range(9):                                                                     # stalks
        x = -18 + i * 4.5
        out += cut(f"M{x - 2},0 L{x + 2},0 L{x + 1 + (i - 4) * 2},-70 L{x - 3 + (i - 4) * 2},-70 Z",
                   VANG_D if i % 2 else VANG, w=0)
    sys.path.insert(0, os.path.join(ROOT, "background_luom"))
    from gen_background_luom import rice_ear
    for i in range(7):                                                                     # drooping heads
        x0 = (i - 3) * 5.5
        flip = -1 if i < 3 else 1
        ear = rice_ear(0, 0, 1.25, VANG_D, VANG_L)
        out += f'<g transform="translate({x0 + (i - 3) * 2},-66) scale({flip},1) rotate({-10 + abs(i - 3) * 8})">{ear}</g>'
    out += cut("M-22,-44 L22,-44 L22,-34 L-22,-34 Z", NAU, w=0.5)                          # straw band
    out += incise("M-20,-39 L20,-39", 0.9, NAU, 0.4)
    out += incise("M-10,-30 L-11,-4 M0,-30 L0,-4 M10,-30 L11,-4", 0.9, VANG, 0.4)
    return out


def stump():
    out = cut("M-34,0 C-40,-4 -30,-10 -28,-14 L-26,-48 L26,-48 L28,-14 C30,-10 40,-4 34,0 Z", NAU)
    out += cut("M-26,-48 C-26,-58 26,-58 26,-48 C26,-40 -26,-40 -26,-48 Z", NAU_L)       # cut top
    for r in (18, 11, 5):
        out += incise(f"M{-r},-48 C{-r},{-48 - r * 0.38:.1f} {r},{-48 - r * 0.38:.1f} {r},-48 C{r},{-48 + r * 0.32:.1f} {-r},{-48 + r * 0.32:.1f} {-r},-48",
                      0.9, NAU_L, 0.4)
    out += incise("M-14,-38 C-16,-26 -12,-14 -16,-4 M6,-40 C8,-28 4,-16 8,-6", 1.1, NAU, 0.5)
    out += cut("M24,-34 C34,-44 44,-46 50,-42 C44,-40 36,-36 26,-28 Z", REU, w=0.5)          # sprout
    return out


def fence():
    """A section of fallen bamboo fence: two rails, slanted slats, rope ties."""
    out = ""
    for i in range(9):
        x = -78 + i * 19
        out += cut(f"M{x - 3},0 L{x + 3},0 L{x + 14},-50 L{x + 8},-50 Z", mix(VANG_D, NAU, 0.4) if i % 2 else VANG_D, w=0.5)
        for y in (-14, -30, -44):
            out += f'<path d="M{x + 1 + (-y) * 0.22:.1f},{y} l6,0" stroke="{lighter(VANG_D, 0.3)}" stroke-width="1"/>'
    for y, x0 in ((-14, -82), (-36, -76)):
        out += cut(f"M{x0},{y - 4} L{x0 + 170},{y - 8} L{x0 + 170},{y} L{x0},{y + 4} Z", VANG, w=0.5)
        for i in range(6):
            x = x0 + 12 + i * 30
            out += f'<circle cx="{x}" cy="{y - 2 - i * 0.2:.1f}" r="2.6" fill="{NAU}"/>'
    return out


def letter():
    """Folded triangle letter (thu gap tam giac) with a little red seal."""
    out = cut("M-32,16 L32,16 L0,-22 Z", NGA)
    out += facet([(-32, 16), (0, -22), (-6, 4)], NGA_D)
    out += facet([(32, 16), (0, -22), (6, 4)], lighter(NGA, 0.3))
    out += facet([(-32, 16), (32, 16), (0, 2)], mix(NGA, NGA_D, 0.4))
    out += incise("M-32,16 L0,2 L32,16", 1.0, NGA, 0.5)
    out += incise("M0,-22 L0,2", 0.9, NGA, 0.5)
    out += thin("M-18,11 L-6,7 M6,7 L18,11", 0.8, NAU)
    out += f'<circle cx="0" cy="4" r="5.5" fill="{SON}"/>' + f'<path d="{star_d(0, 4.4, 3.6)}" fill="{VANG_L}"/>'
    return out


def heart(full=True):
    d = "M0,16 C-14,6 -22,-2 -22,-8 C-22,-16 -14,-20 -8,-18 C-4,-17 -1,-14 0,-11 C1,-14 4,-17 8,-18 C14,-20 22,-16 22,-8 C22,-2 14,6 0,16 Z"
    if full:
        out = cut(d, SON)
        out += f'<path d="M-14,-10 C-14,-14 -10,-16 -7,-14" stroke="{SON_L}" stroke-width="2.4" fill="none" stroke-linecap="round"/>'
        out += incise("M0,10 C-8,4 -14,-2 -15,-7", 0.8, SON, 0.4)
    else:
        out = cut(d, mix(NAU_D, NGA, 0.15))
        out += incise("M0,10 C-8,4 -14,-2 -15,-7", 0.8, NAU_D, 0.4)
    return out


def note(k):
    if k == 0:
        out = cut("M-4,-28 L0,-28 L0,4 C0,12 -12,14 -14,8 C-16,2 -8,-2 -4,0 Z", NGA)
        out += cut("M0,-28 C8,-24 14,-18 12,-10 C10,-16 6,-18 0,-20 Z", NGA)
    else:
        out = cut("M-12,-24 L12,-30 L12,0 C12,8 2,10 0,4 C-2,-2 6,-4 8,-2 L8,-22 L-8,-18 L-8,6 C-8,14 -18,16 -20,10 C-22,4 -14,0 -12,2 Z", NGA)
    return out


def dust():
    return scroll_cloud(0.38, mix(NGA_D, EARTH, 0.3), 7, [(-34, 4, 16), (-10, -8, 20), (16, -2, 18), (34, 6, 14), (0, 8, 16)])


CW, CH = 820, 900


def curtain_panel():
    """Red lacquer cloth with folds, a gold border of rice ears on the inner edge, a wave hem."""
    out = cut(f"M0,0 L{CW},0 L{CW},{CH} L0,{CH} Z", SON, w=0, cloth=True)
    for i in range(9):
        x = 40 + i * 86
        out += f'<path d="M{x + 14},0 C{x + 28},300 {x + 6},600 {x + 20},{CH} L{x + 44},{CH} C{x + 30},600 {x + 50},300 {x + 36},0 Z" fill="{SON_D}"/>'
        out += f'<path d="M{x + 36},0 C{x + 50},300 {x + 30},600 {x + 44},{CH} L{x + 48},{CH} C{x + 34},600 {x + 54},300 {x + 40},0 Z" fill="{SON_L}" opacity="0.6"/>'
    # inner border: gold band with drum-sun medallions
    out += cut(f"M{CW - 70},0 L{CW},0 L{CW},{CH} L{CW - 70},{CH} Z", VANG_D, w=0, cloth=True)
    out += cut(f"M{CW - 62},0 L{CW - 8},0 L{CW - 8},{CH} L{CW - 62},{CH} Z", NAU_D, w=0)
    for j in range(9):
        y = 50 + j * 100
        out += f'<g transform="translate({CW - 35},{y})">{drum_sun(20, 10, SON, VANG, VANG_L, False, NAU)}</g>'
        out += incise(f"M{CW - 35},{y + 26} L{CW - 35},{y + 74}", 1.2, NAU_D, 0.5)
    # hem: wave band
    out += cut(f"M0,{CH - 110} L{CW},{CH - 110} L{CW},{CH} L0,{CH} Z", NAU_D, w=0)
    out += cut(f"M0,{CH - 110} L{CW},{CH - 110} L{CW},{CH - 100} L0,{CH - 100} Z", VANG_D, w=0)
    out += wave_band(0, CW, CH - 96, 40, LUC, LUC_L, rows=2, period=64)
    for i in range(11):
        out += wave_crest(30 + i * 78, CH - 98, 0.8, NGA_D, 1)
    return out


def curtain_top():
    W2, H2 = 1600, 190
    d = f"M0,0 L{W2},0 L{W2},130 "
    for i in range(20, 0, -1):
        x0, x1 = W2 * i / 20, W2 * (i - 1) / 20
        d += f"Q{(x0 + x1) / 2:.1f},176 {x1:.1f},130 "
    d += "Z"
    out = cut(d, SON_D, w=0, cloth=True)
    out += cut(f"M0,0 L{W2},0 L{W2},30 L0,30 Z", NAU_D, w=0)
    out += cut(f"M0,30 L{W2},30 L{W2},38 L0,38 Z", VANG_D, w=0)
    out += punch_row((0, 34), (W2, 34), 200, 1.3, NAU_D)
    for i in range(20):
        x = W2 * (i + 0.5) / 20
        out += incise(f"M{x - 30:.1f},136 Q{x:.1f},166 {x + 30:.1f},136", 1.1, SON_D, 0.5)
        out += f'<g transform="translate({x:.1f},150)">{drum_sun(8, 8, VANG, VANG_L, NGA, False, VANG_D)}</g>'
    # plaque for the score, flanked by scroll clouds and small suns
    px, py, pw, ph = 800, 92, 340, 70
    out += cut(f"M{px - pw / 2},{py - ph / 2} L{px + pw / 2},{py - ph / 2} L{px + pw / 2},{py + ph / 2} L{px - pw / 2},{py + ph / 2} Z", NGA)
    out += incise(f"M{px - pw / 2 + 8},{py - ph / 2 + 8} L{px + pw / 2 - 8},{py - ph / 2 + 8} L{px + pw / 2 - 8},{py + ph / 2 - 8} L{px - pw / 2 + 8},{py + ph / 2 - 8} Z", 1.2, NGA, 0.6)
    for s in (-1, 1):
        out += f'<g transform="translate({px + s * (pw / 2 + 60)},{py}) scale({s},1)">{scroll_cloud(0.55, NGA_D, 3)}</g>'
        out += f'<g transform="translate({px + s * (pw / 2 + 150)},{py})">{drum_sun(22, 12, SON, VANG, VANG_L, True, NAU)}</g>'
    return out


def main():
    for k in range(2):
        save(f"plane_{k}", plane(k), 290, 110, (145, 55), box=[-120, -22, 124, 26])
    save("bomb", bomb(), 60, 100, (30, 52), box=[-14, -30, 14, 40])
    for k in range(4):
        save(f"explode_{k}", explosion(k), 220, 200, (110, 120))
    save("crater", crater(), 200, 50, (100, 30), box=[-60, -12, 60, 10])
    save("bullet", bullet(), 90, 24, (12, 12), box=[-8, -5, 60, 5])
    save("sheaf", sheaf(), 80, 124, (40, 118), box=[-24, -110, 24, 0])
    save("stump", stump(), 120, 76, (60, 70), box=[-34, -56, 34, 0])
    save("fence", fence(), 190, 70, (95, 62), box=[-80, -50, 84, 0])
    save("letter", letter(), 70, 54, (35, 26), box=[-30, -20, 30, 22])
    save("heart", heart(True), 52, 44, (26, 22))
    save("heart_empty", heart(False), 52, 44, (26, 22))
    for k in range(2):
        save(f"note_{k}", note(k), 50, 48, (22, 34))
    save("dust", dust(), 90, 50, (45, 30), shadow=False)
    write_svg_png(os.path.join(OUT, "curtain_panel"), defs() + curtain_panel(), (0, 0, CW, CH), 1,
                  texture=lambda p: paper_cut(p, scale=1, shadow=None, tile=True))
    MANIFEST["curtain_panel"] = {"png": "curtain_panel.png", "size": [CW, CH], "anchor": [0, 0], "pngScale": 1}
    write_svg_png(os.path.join(OUT, "curtain_top"), defs() + curtain_top(), (0, 0, 1600, 190), 1,
                  texture=lambda p: paper_cut(p, scale=1, shadow=(0, 6, 5, 0.5), tile=True))
    MANIFEST["curtain_top"] = {"png": "curtain_top.png", "size": [1600, 190], "anchor": [0, 0], "pngScale": 1, "plaque": [800, 92]}
    with open(os.path.join(OUT, "fx.json"), "w") as f:
        json.dump(MANIFEST, f, indent=2)
    print(len(MANIFEST), "sprites")


if __name__ == "__main__":
    main()
