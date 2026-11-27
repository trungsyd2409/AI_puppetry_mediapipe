"""Snow-mountain camp at night, 1600 x 900, same flat ink style as the other assets.

Outputs (drawn by the web app in this order):
  stage_sky.png    night sky and stars (the moon and the aurora are animated on top of it)
  stage_bg.png     mountains, pine forest, camp tents, campfire stones, snowy ground
  (puppet)
  stage_fg.png     snow drifts and big pines in front of the puppet
  stage.json       floor line, flag poles on the tents, campfire, tent glows
"""
import json, math, os, random, subprocess

OUT = os.path.dirname(os.path.abspath(__file__))
W, H = 1600, 900
FLOOR_Y = 760
random.seed(11)

INK = "#1B2433"
SNOW = "#F4F8FC"
SNOW_SH = "#C9D9EB"
SNOW_SH2 = "#A7BED8"
MT_FAR = "#8EA9CB"
MT_MID = "#5E80AB"
PINE = "#21404A"
PINE_D = "#162D35"
TENT = "#C7BCA3"
TENT_SH = "#9B8F76"
TENT_D = "#6B604B"
WOOD = "#5A3A22"
WOOD_D = "#3B2414"
STONE = "#7C8796"
GOLD = "#E2B44A"


def svg(inner):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
            f'{inner}</svg>')


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def pts(ps):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in ps)


# ---------------------------------------------------------------- sky
def sky():
    stars = "".join(
        f'<circle cx="{random.uniform(0, W):.0f}" cy="{random.uniform(60, 430):.0f}" '
        f'r="{random.choice([0.8, 1.1, 1.4, 1.9]):.1f}" fill="#FFFFFF" opacity="{random.uniform(0.35, 0.95):.2f}"/>'
        for _ in range(170))
    sparkle = "".join(
        f'<path d="M{x},{y - 7} L{x + 1.6},{y - 1.6} L{x + 7},{y} L{x + 1.6},{y + 1.6} L{x},{y + 7} '
        f'L{x - 1.6},{y + 1.6} L{x - 7},{y} L{x - 1.6},{y - 1.6} Z" fill="#FFFFFF" opacity="0.85"/>'
        for x, y in ((210, 150), (620, 120), (980, 200), (1480, 300), (420, 330)))
    return (
        '<defs><linearGradient id="g_sky" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#101C36"/><stop offset="0.45" stop-color="#22406E"/>'
        '<stop offset="0.75" stop-color="#5B7FAE"/><stop offset="1" stop-color="#A9C2DE"/></linearGradient>'
        '<radialGradient id="g_moonglow"><stop offset="0" stop-color="#E8F2FF" stop-opacity="0.75"/>'
        '<stop offset="1" stop-color="#E8F2FF" stop-opacity="0"/></radialGradient>'
        '<radialGradient id="g_moon" cx="0.4" cy="0.4"><stop offset="0" stop-color="#FFFFFF"/>'
        '<stop offset="1" stop-color="#CFDDEE"/></radialGradient></defs>'
        f'<rect width="{W}" height="{H}" fill="url(#g_sky)"/>' + stars + sparkle
        # the moon itself is drawn (and animated) by the web app, see stage.json "moon"
    )


# ---------------------------------------------------------------- mountains
def mountain(x, base, h, w, fill, shade_op=0.22):
    A, B, C, D, E = (x - w, base), (x - 0.38 * w, base - 0.66 * h), (x, base - h), (x + 0.3 * w, base - 0.7 * h), (x + w, base)
    body = f'<polygon points="{pts([A, B, C, D, E])}" fill="{fill}" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>'
    shade = f'<polygon points="{pts([C, D, E, (x + 0.08 * w, base)])}" fill="{INK}" opacity="{shade_op}"/>'
    L, R = lerp(C, B, 0.75), lerp(C, D, 0.85)
    teeth = []
    for i in range(1, 7):
        t = i / 7
        px, py = L[0] + (R[0] - L[0]) * t, L[1] + (R[1] - L[1]) * t
        teeth.append((px, py + (18 if i % 2 else -2) * h / 300))
    cap = f'<polygon points="{pts([C, L] + teeth + [R])}" fill="{SNOW}" stroke="{INK}" stroke-width="1.6" stroke-linejoin="round"/>'
    cap_shade = f'<polygon points="{pts([C, R, teeth[-1], (x + 0.04 * w, base - 0.82 * h)])}" fill="{SNOW_SH}" opacity="0.9"/>'
    ridge = (f'<path d="M{C[0]},{C[1]} L{x + 0.04 * w:.1f},{base - 0.82 * h:.1f} L{x - 0.06 * w:.1f},{base - 0.6 * h:.1f}" '
             f'fill="none" stroke="{INK}" stroke-width="1.2" opacity="0.4"/>')
    return body + shade + cap + cap_shade + ridge


def ranges():
    far = [(90, 300, 200), (360, 380, 230), (640, 300, 200), (900, 410, 250), (1180, 330, 220), (1460, 380, 230), (1650, 300, 200)]
    mid = [(-20, 230, 200), (260, 260, 220), (560, 210, 200), (1040, 250, 230), (1330, 220, 210), (1600, 260, 220)]
    out = '<g opacity="0.85">' + "".join(mountain(x, 680, h + 80, w, MT_FAR, 0.15) for x, h, w in far) + "</g>"
    out += "".join(mountain(x, 705, h + 45, w, MT_MID, 0.25) for x, h, w in mid)
    return out


# ---------------------------------------------------------------- pines
def pine(x, base, h, color=PINE, snow=True, op=1.0):
    w = h * 0.42
    tiers = ""
    for i in range(4):
        top = base - h + i * h * 0.2
        bot = base - h * 0.62 + i * h * 0.17
        tw = w * (0.45 + i * 0.2)
        tiers += (f'<polygon points="{x},{top:.1f} {x + tw:.1f},{bot:.1f} {x - tw:.1f},{bot:.1f}" fill="{color}" '
                  f'stroke="{INK}" stroke-width="1.4" stroke-linejoin="round"/>')
        if snow:
            sx = tw * 0.75
            tiers += (f'<path d="M{x - sx:.1f},{bot - 3:.1f} Q{x - sx * 0.5:.1f},{bot - 9:.1f} {x:.1f},{bot - 5:.1f} '
                      f'Q{x + sx * 0.5:.1f},{bot - 9:.1f} {x + sx:.1f},{bot - 3:.1f} Q{x:.1f},{bot + 3:.1f} {x - sx:.1f},{bot - 3:.1f} Z" '
                      f'fill="{SNOW}" stroke="{INK}" stroke-width="1"/>')
    trunk = f'<rect x="{x - h * 0.03:.1f}" y="{base - h * 0.1:.1f}" width="{h * 0.06:.1f}" height="{h * 0.12:.1f}" fill="{WOOD_D}"/>'
    return f'<g opacity="{op}">{trunk}{tiers}</g>'


def forest():
    out = ""
    hills = (f'<path d="M0,690 C200,650 380,668 560,676 C760,686 900,650 1100,662 C1300,672 1440,646 1600,664 '
             f'L1600,760 L0,760 Z" fill="{SNOW_SH}" stroke="{INK}" stroke-width="1.6"/>')
    out += hills
    for i in range(46):
        x = random.uniform(-20, W + 20)
        if 640 < x < 960 and random.random() < 0.6:
            continue
        base = 690 + random.uniform(-14, 6)
        out += pine(x, base, random.uniform(60, 110), PINE_D, True, 0.85)
    for i in range(22):
        x = random.choice([random.uniform(-20, 520), random.uniform(1080, W + 20)])
        out += pine(x, 712 + random.uniform(-6, 6), random.uniform(100, 150), PINE, True)
    return out


# ---------------------------------------------------------------- ground + camp
def ground():
    return ('<linearGradient id="g_ground" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{SNOW}"/><stop offset="1" stop-color="{SNOW_SH}"/></linearGradient>'
            f'<path d="M0,712 C240,700 420,722 640,716 C860,710 1040,724 1240,714 C1400,706 1520,716 1600,712 '
            f'L1600,{H} L0,{H} Z" fill="url(#g_ground)" stroke="{INK}" stroke-width="1.8"/>'
            + "".join(f'<path d="M{x},{y} q{l / 2},-6 {l},0" fill="none" stroke="{SNOW_SH2}" stroke-width="2" opacity="0.7"/>'
                      for x, y, l in ((120, 780, 90), (420, 800, 120), (760, 790, 140), (1080, 806, 110),
                                      (1380, 788, 120), (260, 840, 100), (980, 850, 130))))


TENTS = [  # (x, base, width, height, pole height)
    (300, 752, 300, 210, 110),
    (980, 724, 150, 110, 70),
    (1360, 756, 280, 200, 105),
]


def tent(x, base, w, h, pole):
    apex = (x, base - h)
    L, R = (x - w / 2, base), (x + w / 2, base)
    door_top = (x, base - h * 0.72)
    dl, dr = (x - w * 0.16, base), (x + w * 0.16, base)
    gid = f"g_door_{x}"
    body = (f'<polygon points="{pts([apex, R, L])}" fill="{TENT}" stroke="{INK}" stroke-width="2.6" stroke-linejoin="round"/>'
            f'<polygon points="{pts([apex, R, (x + w * 0.05, base)])}" fill="{TENT_SH}" opacity="0.55"/>')
    seams = "".join(
        f'<path d="M{apex[0]},{apex[1]} L{x + w / 2 * t:.1f},{base}" stroke="{TENT_D}" stroke-width="1.2" opacity="0.6"/>'
        for t in (-0.66, -0.33, 0.33, 0.66))
    door = (f'<radialGradient id="{gid}" cx="0.5" cy="0.85" r="0.8"><stop offset="0" stop-color="#FFD27A"/>'
            f'<stop offset="0.6" stop-color="#E0873A"/><stop offset="1" stop-color="#6B2E14"/></radialGradient>'
            f'<polygon points="{pts([door_top, dr, dl])}" fill="url(#{gid})" stroke="{INK}" stroke-width="2"/>')
    flaps = (f'<path d="M{door_top[0]},{door_top[1]} Q{x - w * 0.12},{base - h * 0.3} {x - w * 0.24},{base} '
             f'L{dl[0]},{base} Z" fill="{TENT_SH}" stroke="{INK}" stroke-width="1.8"/>'
             f'<path d="M{door_top[0]},{door_top[1]} Q{x + w * 0.12},{base - h * 0.3} {x + w * 0.24},{base} '
             f'L{dr[0]},{base} Z" fill="{TENT_SH}" stroke="{INK}" stroke-width="1.8"/>')
    snow_cap = (f'<path d="M{apex[0]},{apex[1] - 3} L{x + w * 0.2},{base - h * 0.62} '
                + " ".join(f"L{x + w * (0.2 - 0.08 * i):.1f},{base - h * (0.62 if i % 2 else 0.68):.1f}" for i in range(1, 6))
                + f' Z" fill="{SNOW}" stroke="{INK}" stroke-width="1.4"/>')
    ropes = (f'<path d="M{apex[0]},{apex[1]} L{x - w * 0.82},{base + 4} M{apex[0]},{apex[1]} L{x + w * 0.82},{base + 4}" '
             f'stroke="{TENT_D}" stroke-width="1.4" opacity="0.8"/>'
             f'<rect x="{x - w * 0.82 - 2}" y="{base - 6}" width="4" height="12" fill="{WOOD_D}"/>'
             f'<rect x="{x + w * 0.82 - 2}" y="{base - 6}" width="4" height="12" fill="{WOOD_D}"/>')
    pole_top = apex[1] - pole
    pole_svg = (f'<rect x="{x - 3.5}" y="{pole_top}" width="7" height="{pole + 6}" fill="{WOOD}" stroke="{INK}" stroke-width="1.6"/>'
                f'<circle cx="{x}" cy="{pole_top}" r="6" fill="{GOLD}" stroke="{INK}" stroke-width="1.6"/>')
    drift = (f'<path d="M{L[0] - 20},{base + 4} Q{L[0] + 30},{base - 16} {x - w * 0.2},{base + 2} Z '
             f'M{x + w * 0.2},{base + 2} Q{R[0] - 30},{base - 14} {R[0] + 20},{base + 4} Z" fill="{SNOW}" '
             f'stroke="{INK}" stroke-width="1.4"/>')
    return ropes + pole_svg + body + seams + door + flaps + snow_cap + drift, (x, pole_top), (x, base - h * 0.25, w * 0.35)


def campfire(x, y):
    stones = "".join(
        f'<ellipse cx="{x + 46 * math.cos(a):.1f}" cy="{y + 12 * math.sin(a):.1f}" rx="13" ry="8" fill="{STONE}" '
        f'stroke="{INK}" stroke-width="1.6"/>'
        for a in [i * math.pi / 5 for i in range(10)] if math.sin(a) > -0.2)
    logs = (f'<rect x="{x - 40}" y="{y - 8}" width="80" height="13" rx="6" fill="{WOOD}" stroke="{INK}" stroke-width="1.8" '
            f'transform="rotate(-18 {x} {y})"/>'
            f'<rect x="{x - 40}" y="{y - 8}" width="80" height="13" rx="6" fill="{WOOD}" stroke="{INK}" stroke-width="1.8" '
            f'transform="rotate(18 {x} {y})"/>'
            f'<ellipse cx="{x}" cy="{y + 2}" rx="26" ry="7" fill="#2B1A10" opacity="0.6"/>')
    seat = (f'<rect x="{x + 70}" y="{y - 6}" width="96" height="22" rx="10" fill="{WOOD}" stroke="{INK}" stroke-width="1.8"/>'
            f'<ellipse cx="{x + 166}" cy="{y + 5}" rx="6" ry="10" fill="#8A5A34" stroke="{INK}" stroke-width="1.4"/>'
            f'<path d="M{x + 74},{y - 6} Q{x + 118},{y - 16} {x + 162},{y - 6}" fill="{SNOW}" stroke="{INK}" stroke-width="1.2"/>')
    return stones + logs + seat


def crates(x, y):
    out = ""
    for dx, dy, s in ((0, 0, 46), (50, 0, 40), (22, -42, 40)):
        cx, cy = x + dx, y + dy - s
        out += (f'<rect x="{cx}" y="{cy}" width="{s}" height="{s}" fill="#8A5A34" stroke="{INK}" stroke-width="1.8"/>'
                f'<path d="M{cx},{cy} L{cx + s},{cy + s} M{cx + s},{cy} L{cx},{cy + s}" stroke="{WOOD_D}" stroke-width="1.4"/>'
                f'<path d="M{cx - 2},{cy + 2} Q{cx + s / 2},{cy - 9} {cx + s + 2},{cy + 2} Z" fill="{SNOW}" stroke="{INK}" stroke-width="1.2"/>')
    return out


def foreground():
    drifts = (f'<path d="M0,846 C120,812 260,826 360,850 C460,872 520,880 600,{H} L0,{H} Z '
              f'M1000,{H} C1080,872 1180,846 1300,836 C1420,826 1520,820 1600,834 L1600,{H} Z" fill="{SNOW}" '
              f'stroke="{INK}" stroke-width="1.8"/>'
              f'<path d="M30,866 q60,-16 140,-6 M1200,870 q90,-20 190,-14" fill="none" stroke="{SNOW_SH2}" stroke-width="2.4"/>')
    pines = pine(46, 880, 360, PINE) + pine(1560, 884, 380, PINE) + pine(150, 900, 230, PINE_D) + pine(1460, 904, 240, PINE_D)
    return pines + drifts


camp = ""
poles, glows = [], []
for t in TENTS:
    s, p, g = tent(*t)
    camp += s
    poles.append({"x": p[0], "top": p[1], "side": 1})
    glows.append({"x": g[0], "y": g[1], "r": g[2]})
FIRE = (1130, 768)

bg = ranges() + forest() + ground() + crates(470, 762) + camp + campfire(*FIRE)
layers = {"stage_sky": sky(), "stage_bg": bg, "stage_fg": foreground()}
for name, inner in layers.items():
    p = os.path.join(OUT, f"{name}.svg")
    open(p, "w").write(svg(inner))
    subprocess.run(["rsvg-convert", "-o", os.path.join(OUT, f"{name}.png"), p], check=True)

json.dump({
    "scene": "snow",
    "size": [W, H],
    "floorY": FLOOR_Y,
    "stageX": [330, 1270],
    "puppetHeight": 470,
    "layers": {"sky": "stage_sky.png", "bg": "stage_bg.png", "fg": "stage_fg.png"},
    "props": {},
    "poles": poles,
    "fire": {"x": FIRE[0], "y": FIRE[1] - 6},
    "tentGlows": glows,
    "aurora": {"y0": 110, "y1": 330},
    "moon": {"x": 1260, "y": 190, "r": 78},
    "note": "web order: sky, moon, aurora, bg, far snow, flags, fire, puppet, near snow, fg, wind",
}, open(os.path.join(OUT, "stage.json"), "w"), indent=2)
print("snow background done")
