"""Water-puppet stage (thuy dinh) background, 1600 x 900.

Outputs:
  stage_bg.svg|png        everything behind the puppets (flags and waves are animated by the web app)
  stage_fg_water.svg|png  semi-transparent water band in front of the puppets
  stage_fg_lotus.svg|png  lotus clusters in front of everything
  stage_fg.svg|png        water + waves + lotus in one static image (used by assets/preview.html)
  stage_bg_static.png     bg with static flags and waves (used by assets/preview.html)
  stage.json              floor line, flag poles, water line, props for the web app
"""
import json, math, os, random, subprocess

OUT = os.path.dirname(os.path.abspath(__file__))
W, H = 1600, 900
FLOOR_Y = 760
random.seed(7)

INK = "#2A140A"
LACQUER = "#8E1B14"
LACQUER_D = "#5E0F0B"
GOLD = "#E2B44A"
GOLD_L = "#F6DA8A"
TILE = "#4E2A1C"
BAMBOO = "#3C5A32"
WATER = "#24504C"
WATER_D = "#163533"


def svg(inner, w=W, h=H):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
            f'{inner}</svg>')


def cloud(x, y, s=1.0, rot=0, color=GOLD, w=1.8, op=1):
    return (f'<path transform="translate({x},{y}) rotate({rot}) scale({s})" opacity="{op}" '
            f'd="M-11,5 C-13,-5 -3,-10 4,-6 C10,-2 7,6 1,5 C-3,4 -2,-1 1,-1 '
            f'M4,-6 C8,-12 16,-9 15,-3 C14,2 9,2 9,-1" '
            f'fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>')


# ---------------------------------------------------------------- sky
def sky():
    return (
        '<defs>'
        '<linearGradient id="g_sky" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#D9B77A"/><stop offset="0.45" stop-color="#F1DDB0"/>'
        '<stop offset="0.8" stop-color="#EBCB92"/><stop offset="1" stop-color="#D7A866"/></linearGradient>'
        '<radialGradient id="g_moon_glow"><stop offset="0" stop-color="#FFF4CF" stop-opacity="0.9"/>'
        '<stop offset="1" stop-color="#FFF4CF" stop-opacity="0"/></radialGradient>'
        '<radialGradient id="g_moon" cx="0.4" cy="0.4"><stop offset="0" stop-color="#FFF6D6"/>'
        '<stop offset="1" stop-color="#EBCB7E"/></radialGradient>'
        '<filter id="f_paper" x="0" y="0" width="1" height="1">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="3"/>'
        '<feColorMatrix values="0 0 0 0 0.35  0 0 0 0 0.22  0 0 0 0 0.10  0 0 0 0.9 -0.35"/></filter>'
        '<radialGradient id="g_vig" cx="0.5" cy="0.45" r="0.75">'
        '<stop offset="0.6" stop-color="#3A1E0C" stop-opacity="0"/>'
        '<stop offset="1" stop-color="#3A1E0C" stop-opacity="0.55"/></radialGradient>'
        '</defs>'
        f'<rect width="{W}" height="{H}" fill="url(#g_sky)"/>'
        '<circle cx="1250" cy="170" r="230" fill="url(#g_moon_glow)"/>'
        '<circle cx="1250" cy="170" r="92" fill="url(#g_moon)" stroke="#C9A055" stroke-width="2"/>'
        '<path d="M1210,150 q20,-12 40,0 M1238,196 q16,8 30,-2" fill="none" stroke="#D9B566" '
        'stroke-width="5" stroke-linecap="round" opacity="0.6"/>'
        + cloud(1120, 210, 3.2, 0, "#B98E4A", 1.2, 0.7) + cloud(1380, 130, 2.6, 180, "#B98E4A", 1.2, 0.7)
        + cloud(560, 80, 2.2, 190, "#B98E4A", 1.2, 0.45)
    )


def mountains():
    def layer(peaks, base, fill, op):
        paths = ""
        for x, h, w in peaks:
            paths += (f'<path d="M{x-w},{base} C{x-w*0.9},{base-h*0.7} {x-w*0.55},{base-h*1.08} {x},{base-h} '
                      f'C{x+w*0.55},{base-h*1.08} {x+w*0.9},{base-h*0.7} {x+w},{base} Z"/>')
        return f'<g fill="{fill}" opacity="{op}">{paths}</g>'
    far = [(60, 170, 90), (190, 240, 80), (300, 150, 90), (470, 210, 70), (620, 160, 100),
           (980, 180, 90), (1100, 250, 70), (1230, 160, 100), (1420, 230, 80), (1560, 170, 90)]
    near = [(110, 200, 110), (360, 150, 120), (1300, 170, 120), (1500, 220, 110)]
    return layer(far, 600, "#8E7B5C", 0.35) + layer(near, 640, "#5E4E38", 0.45)


def cranes():
    def crane(x, y, s, flip=1):
        return (f'<g transform="translate({x},{y}) scale({s * flip},{s})" fill="{INK}" opacity="0.75">'
                f'<path d="M0,0 C10,-14 26,-22 40,-18 C28,-12 20,-4 16,2 C30,0 44,4 56,12 '
                f'C40,10 26,10 14,8 L-4,10 C-14,8 -26,2 -34,-4 L-30,-6 C-20,-2 -10,0 0,0 Z"/>'
                f'<path d="M-34,-4 L-44,-8" stroke="{INK}" stroke-width="2"/></g>')
    return crane(330, 120, 0.9) + crane(400, 92, 0.7) + crane(262, 150, 0.6)


def bamboo(x0, flip=1):
    out = ""
    for i, (dx, top, w) in enumerate([(0, 40, 16), (46, 110, 13), (-38, 170, 11), (82, 220, 10)]):
        x = x0 + dx * flip
        lean = random.uniform(-14, 14)
        seg = ""
        y = FLOOR_Y + 40
        while y > top:
            y2 = max(top, y - random.uniform(55, 80))
            xa, xb = x + lean * (1 - y / H), x + lean * (1 - y2 / H)
            seg += (f'<path d="M{xa-w/2:.1f},{y} L{xb-w/2:.1f},{y2+3} L{xb+w/2:.1f},{y2+3} L{xa+w/2:.1f},{y} Z" '
                    f'fill="{BAMBOO}"/><rect x="{xb-w/2-2:.1f}" y="{y2:.1f}" width="{w+4}" height="4" rx="2" '
                    f'fill="#24391F"/>')
            if random.random() < 0.55:
                ang = random.choice([-1, 1]) * random.uniform(20, 60)
                for k in range(3):
                    seg += (f'<path transform="translate({xb:.1f},{y2:.1f}) rotate({ang + k*18 - 18:.1f})" '
                            f'd="M0,0 C14,-6 40,-4 62,2 C40,6 14,6 0,0 Z" fill="{BAMBOO}"/>')
            y = y2
        out += f'<g opacity="{0.9 - i*0.12:.2f}">{seg}</g>'
    return out


# ---------------------------------------------------------------- thuy dinh
def pavilion():
    o = ""
    # stilts + deck
    for x in range(260, 1360, 90):
        o += f'<rect x="{x}" y="{FLOOR_Y+20}" width="16" height="70" fill="#3D2416"/>'
    # back wall of the stage
    o += f'<rect x="300" y="320" width="1000" height="{FLOOR_Y-320}" fill="#3B160F"/>'
    # side bays: lacquer walls with round lattice windows
    for cx in (430, 1170):
        o += (f'<rect x="318" y="330" width="224" height="{FLOOR_Y-330}" fill="{LACQUER_D}" '
              f'transform="translate({cx-430},0)"/>'
              f'<circle cx="{cx}" cy="545" r="70" fill="#2A0E0A" stroke="{GOLD}" stroke-width="6"/>'
              f'<g stroke="{GOLD}" stroke-width="3" opacity="0.85">'
              + "".join(f'<line x1="{cx-70}" y1="{545+k}" x2="{cx+70}" y2="{545+k}"/>'
                        f'<line x1="{cx+k}" y1="475" x2="{cx+k}" y2="615"/>' for k in range(-60, 61, 20))
              + f'</g><circle cx="{cx}" cy="545" r="70" fill="none" stroke="{INK}" stroke-width="3"/>'
              f'<circle cx="{cx}" cy="545" r="22" fill="{LACQUER}" stroke="{GOLD}" stroke-width="4"/>'
              + cloud(cx, 545, 1.2, 0, GOLD, 2)
              + f'<rect x="{cx-100}" y="640" width="200" height="100" rx="6" fill="none" stroke="{GOLD}" '
                f'stroke-width="3" opacity="0.7"/>'
              + cloud(cx - 40, 690, 2, 0, GOLD, 1.4, 0.8) + cloud(cx + 40, 690, 2, 180, GOLD, 1.4, 0.8))
    # bamboo curtain (manh tre) behind the centre stage
    o += f'<rect x="560" y="330" width="480" height="300" fill="#C9A15A"/>'
    o += "".join(f'<line x1="{x}" y1="330" x2="{x}" y2="630" stroke="#9C7639" stroke-width="2"/>'
                 for x in range(566, 1040, 9))
    o += "".join(f'<line x1="560" y1="{y}" x2="1040" y2="{y}" stroke="#6E4E22" stroke-width="2.5"/>'
                 for y in (380, 450, 520, 590))
    o += (f'<path d="M560,630 ' + " ".join(f'L{x},{630 + (12 if (x//20)%2 else 0)}' for x in range(560, 1041, 20))
          + f' L1040,630 Z" fill="#9C7639"/>'
          f'<rect x="560" y="330" width="480" height="300" fill="none" stroke="{INK}" stroke-width="4"/>')
    # curtain valance with lotus scallops
    o += (f'<path d="M560,330 ' + " ".join(f'Q{x+30},{372} {x+60},330' for x in range(560, 1040, 60))
          + f' Z" fill="{LACQUER}" stroke="{GOLD}" stroke-width="3"/>')
    # stage floor
    o += (f'<rect x="230" y="{FLOOR_Y}" width="1140" height="30" fill="#6B3A20" stroke="{INK}" stroke-width="3"/>'
          f'<rect x="230" y="{FLOOR_Y}" width="1140" height="7" fill="{GOLD}" opacity="0.8"/>'
          + "".join(f'<line x1="{x}" y1="{FLOOR_Y+8}" x2="{x}" y2="{FLOOR_Y+30}" stroke="{INK}" '
                    f'stroke-width="1.5" opacity="0.6"/>' for x in range(260, 1370, 40)))
    # pillars
    for x in (300, 560, 1040, 1300):
        o += (f'<rect x="{x-17}" y="300" width="34" height="{FLOOR_Y-300}" fill="{LACQUER}" '
              f'stroke="{INK}" stroke-width="3"/>'
              f'<rect x="{x-9}" y="300" width="6" height="{FLOOR_Y-300}" fill="#B8382C" opacity="0.6"/>'
              f'<rect x="{x-22}" y="{FLOOR_Y-22}" width="44" height="22" fill="{GOLD}" stroke="{INK}" stroke-width="3"/>'
              f'<rect x="{x-22}" y="318" width="44" height="16" fill="{GOLD}" stroke="{INK}" stroke-width="3"/>')
        if x in (300, 1300):  # couplet boards
            o += (f'<rect x="{x-12}" y="380" width="24" height="300" rx="4" fill="#2A0E0A" stroke="{GOLD}" stroke-width="2.5"/>'
                  + "".join(f'<circle cx="{x}" cy="{y}" r="5" fill="{GOLD}"/>' for y in range(405, 670, 38)))
    # main beam + name board
    o += (f'<rect x="250" y="296" width="1100" height="30" fill="{LACQUER}" stroke="{INK}" stroke-width="3"/>'
          + "".join(cloud(x, 311, 1.0, 0 if (x//80) % 2 else 180, GOLD, 1.8) for x in range(300, 1320, 80))
)
    # lower roof with upturned corners (dau dao)
    lower = ("M180,236 C210,268 250,292 330,298 L1270,298 C1350,292 1390,268 1420,236 "
             "C1400,244 1370,246 1340,240 C1250,214 1160,196 1080,190 L520,190 "
             "C440,196 350,214 260,240 C230,246 200,244 180,236 Z")
    o += (f'<clipPath id="clip_roof1"><path d="{lower}"/></clipPath>'
          f'<path d="{lower}" fill="{TILE}"/>'
          f'<g clip-path="url(#clip_roof1)" stroke="#6E3E28" stroke-width="3">'
          + "".join(f'<line x1="{x}" y1="180" x2="{x + (x-800)*0.08:.0f}" y2="300"/>' for x in range(190, 1420, 18))
          + f'</g><path d="M180,236 C210,268 250,292 330,298 L1270,298 C1350,292 1390,268 1420,236" '
          f'fill="none" stroke="{GOLD}" stroke-width="6"/>'
          f'<path d="{lower}" fill="none" stroke="{INK}" stroke-width="3.5"/>')
    # frieze between the roofs
    o += (f'<rect x="500" y="150" width="600" height="42" fill="{LACQUER}" stroke="{INK}" stroke-width="3"/>'
          + "".join(f'<circle cx="{x}" cy="171" r="9" fill="none" stroke="{GOLD}" stroke-width="2.5"/>'
                    for x in range(530, 1080, 45)))
    # upper roof
    upper = ("M430,170 C460,160 500,146 560,140 L1040,140 C1100,146 1140,160 1170,170 "
             "C1150,172 1130,170 1110,166 C1040,120 960,98 900,94 L700,94 "
             "C640,98 560,120 490,166 C470,170 450,172 430,170 Z")
    o += (f'<clipPath id="clip_roof2"><path d="{upper}"/></clipPath>'
          f'<path d="{upper}" fill="{TILE}"/>'
          f'<g clip-path="url(#clip_roof2)" stroke="#6E3E28" stroke-width="3">'
          + "".join(f'<line x1="{x}" y1="90" x2="{x + (x-800)*0.15:.0f}" y2="172"/>' for x in range(430, 1180, 16))
          + f'</g><path d="M430,170 C460,160 500,146 560,140 L1040,140 C1100,146 1140,160 1170,170" '
          f'fill="none" stroke="{GOLD}" stroke-width="5"/>'
          f'<path d="{upper}" fill="none" stroke="{INK}" stroke-width="3.5"/>')
    # ridge: two dragons facing the pearl (luong long chau nguyet), stylised
    o += (f'<rect x="690" y="84" width="220" height="14" rx="4" fill="{LACQUER}" stroke="{INK}" stroke-width="3"/>'
          f'<circle cx="800" cy="62" r="16" fill="{GOLD}" stroke="{INK}" stroke-width="3"/>'
          + "".join(f'<path d="M800,62 l{math.cos(a)*30:.1f},{math.sin(a)*30:.1f}" stroke="{GOLD}" stroke-width="3"/>'
                    for a in [i * math.pi / 6 for i in range(-6, 1)])
          + f'<circle cx="800" cy="62" r="16" fill="{GOLD}" stroke="{INK}" stroke-width="3"/>')
    for s in (-1, 1):
        x = 800 + s * 120
        o += (f'<path transform="translate({x},80) scale({s},1)" d="M0,8 C10,-20 40,-30 60,-12 '
              f'C70,-4 66,10 56,8 C48,6 50,-4 56,-4 C46,-18 22,-12 18,8 Z" fill="{GOLD}" '
              f'stroke="{INK}" stroke-width="2.5"/>')
    # curled roof tips
    for x, y, s in ((180, 236, 1), (1420, 236, -1), (430, 170, 1), (1170, 170, -1)):
        o += (f'<path transform="translate({x},{y}) scale({s},1)" d="M0,0 C-6,-24 6,-46 24,-44 '
              f'C38,-42 38,-24 26,-22 C16,-20 16,-32 24,-32" fill="none" stroke="{GOLD}" '
              f'stroke-width="7" stroke-linecap="round"/>'
              f'<path transform="translate({x},{y}) scale({s},1)" d="M0,0 C-6,-24 6,-46 24,-44 '
              f'C38,-42 38,-24 26,-22 C16,-20 16,-32 24,-32" fill="none" stroke="{INK}" '
              f'stroke-width="2" stroke-linecap="round"/>')
    # name board (hoanh phi)
    o += (f'<rect x="660" y="246" width="280" height="74" rx="8" fill="#2A0E0A" stroke="{GOLD}" stroke-width="5"/>'
          f'<rect x="670" y="256" width="260" height="54" rx="5" fill="none" stroke="{GOLD}" stroke-width="1.5"/>'
          f'<text x="800" y="296" text-anchor="middle" font-family="Georgia, \'Times New Roman\', \'DejaVu Serif\', serif" '
          f'font-size="34" font-weight="bold" letter-spacing="4" fill="{GOLD_L}">THỦY ĐÌNH</text>')
    # lanterns
    for x in (430, 1170):
        o += (f'<line x1="{x}" y1="326" x2="{x}" y2="340" stroke="{INK}" stroke-width="2"/>'
              f'<rect x="{x-12}" y="338" width="24" height="8" fill="{GOLD}" stroke="{INK}" stroke-width="2"/>'
              f'<ellipse cx="{x}" cy="376" rx="30" ry="32" fill="#C0281C" stroke="{INK}" stroke-width="3"/>'
              f'<path d="M{x-14},348 Q{x-24},376 {x-14},404 M{x},344 L{x},408 M{x+14},348 Q{x+24},376 {x+14},404" '
              f'fill="none" stroke="#7E140D" stroke-width="2"/>'
              f'<rect x="{x-12}" y="404" width="24" height="8" fill="{GOLD}" stroke="{INK}" stroke-width="2"/>'
              f'<path d="M{x-6},412 l-2,26 M{x},412 l0,30 M{x+6},412 l2,26" stroke="{GOLD}" stroke-width="2.5"/>')
    return o


POLES = [(150, 1), (1450, -1)]   # (x, side the flags fly to)
POLE_TOP = 166


def pole(x):
    return (f'<rect x="{x-5}" y="{POLE_TOP+4}" width="10" height="{H-POLE_TOP-4}" fill="#5A3A22" '
            f'stroke="{INK}" stroke-width="2"/>'
            f'<circle cx="{x}" cy="{POLE_TOP}" r="9" fill="{GOLD}" stroke="{INK}" stroke-width="2"/>')


def flags(x, side):
    """Swallow-tail festival pennants (co duoi nheo) on a pole standing in the water."""
    colors = ["#C0281C", "#E2B44A", "#2F6FA8", "#3E8A4A", "#8A3FA0"]
    o = pole(x)
    for i, c in enumerate(colors):
        y = 190 + i * 34
        L = 110 - i * 8
        o += (f'<path transform="translate({x},{y}) scale({side},1)" '
              f'd="M0,0 C{L*0.4},-6 {L*0.7},6 {L},2 L{L*0.8},14 L{L},26 C{L*0.7},22 {L*0.4},32 0,28 Z" '
              f'fill="{c}" stroke="{INK}" stroke-width="2"/>')
    return o


def water(y0, fg=False, waves=True):
    o = ""
    if not fg:
        o += (f'<linearGradient id="g_water" x1="0" y1="0" x2="0" y2="1">'
              f'<stop offset="0" stop-color="{WATER}"/><stop offset="1" stop-color="{WATER_D}"/></linearGradient>'
              f'<rect x="0" y="{y0}" width="{W}" height="{H-y0}" fill="url(#g_water)"/>')
        # pavilion reflection
        for x in (300, 560, 1040, 1300):
            o += f'<rect x="{x-14}" y="{y0+4}" width="28" height="70" fill="{LACQUER}" opacity="0.25"/>'
    rows = range(y0 + 10, H + 10, 22) if waves else []
    for j, y in enumerate(rows):
        off = (j % 2) * 40
        waves = "".join(f'M{x},{y} q20,-12 40,0 q-12,-4 -18,2' for x in range(-40 + off, W + 40, 80))
        o += f'<path d="{waves}" fill="none" stroke="#9CC3B4" stroke-width="2" opacity="{0.55 if fg else 0.35}"/>'
    return o


def lotus_cluster(x, y, s=1.0, flip=1):
    leaf = lambda cx, cy, r: (f'<ellipse cx="{cx}" cy="{cy}" rx="{r}" ry="{r*0.35}" fill="#3E6B3A" '
                              f'stroke="{INK}" stroke-width="2.5"/>'
                              f'<path d="M{cx},{cy} l{-r*0.9:.0f},{-r*0.05:.0f} M{cx},{cy} l{r*0.9:.0f},{-r*0.05:.0f} '
                              f'M{cx},{cy} l0,{-r*0.3:.0f}" stroke="#2A4A27" stroke-width="2"/>')
    flower = lambda cx, cy, k: (
        f'<g transform="translate({cx},{cy}) scale({k})" stroke="{INK}" stroke-width="2" stroke-linejoin="round">'
        f'<path d="M0,0 C-30,-6 -36,-30 -28,-44 C-14,-30 -6,-14 0,0 Z" fill="#E68FA0"/>'
        f'<path d="M0,0 C30,-6 36,-30 28,-44 C14,-30 6,-14 0,0 Z" fill="#E68FA0"/>'
        f'<path d="M0,0 C-16,-14 -14,-40 0,-56 C14,-40 16,-14 0,0 Z" fill="#F4B6C0"/>'
        f'<path d="M-12,-30 C-8,-38 -4,-42 0,-46 M12,-30 C8,-38 4,-42 0,-46" fill="none" stroke="#C25A70"/>'
        f'</g>')
    stem = lambda x1, y1, x2, y2: f'<path d="M{x1},{y1} Q{(x1+x2)/2+10},{(y1+y2)/2} {x2},{y2}" stroke="#2A4A27" stroke-width="4" fill="none"/>'
    return (f'<g transform="translate({x},{y}) scale({s*flip},{s})">'
            + stem(0, 60, -10, -40) + stem(60, 60, 70, -10)
            + leaf(-30, 40, 70) + leaf(90, 60, 60) + leaf(10, 80, 80)
            + flower(-10, -40, 1.0) + flower(70, -10, 0.7)
            + f'<path d="M140,70 C138,30 150,0 160,-30 M150,70 C152,40 166,20 176,0" stroke="#5E7A3A" '
              f'stroke-width="3" fill="none"/>'
            + f'</g>')


paper = (f'<rect width="{W}" height="{H}" filter="url(#f_paper)" opacity="0.35"/>'
         f'<rect width="{W}" height="{H}" fill="url(#g_vig)"/>')
scene = sky() + mountains() + cranes() + bamboo(70) + bamboo(1530, -1)
bg = scene + water(FLOOR_Y + 30, waves=False) + pavilion() + "".join(pole(x) for x, _ in POLES) + paper
bg_static = scene + water(FLOOR_Y + 30) + pavilion() + "".join(flags(x, sd) for x, sd in POLES) + paper
FG_WATER_Y = 815
fg_water = (f'<linearGradient id="g_fgw" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{WATER}" stop-opacity="0"/>'
            f'<stop offset="0.35" stop-color="{WATER}" stop-opacity="0.85"/>'
            f'<stop offset="1" stop-color="{WATER_D}"/></linearGradient>'
            f'<rect x="0" y="{FG_WATER_Y}" width="{W}" height="{H-FG_WATER_Y}" fill="url(#g_fgw)"/>')
fg_lotus = (lotus_cluster(70, 800, 1.0) + lotus_cluster(1530, 800, 1.0, -1)
            + lotus_cluster(330, 860, 0.6) + lotus_cluster(1270, 860, 0.6, -1))
fg = fg_water + water(830, fg=True) + fg_lotus

for name, inner in (("stage_bg", bg), ("stage_bg_static", bg_static), ("stage_fg", fg),
                    ("stage_fg_water", fg_water), ("stage_fg_lotus", fg_lotus)):
    p = os.path.join(OUT, f"{name}.svg")
    open(p, "w").write(svg(inner))
    subprocess.run(["rsvg-convert", "-o", os.path.join(OUT, f"{name}.png"), p], check=True)
os.remove(os.path.join(OUT, "stage_bg_static.svg"))

json.dump({
    "size": [W, H],
    "floorY": FLOOR_Y,
    "stageX": [330, 1270],
    "puppetHeight": 420,
    "layers": {"bg": "stage_bg.png", "fg": "stage_fg.png",
               "fgWater": "stage_fg_water.png", "fgLotus": "stage_fg_lotus.png"},
    "poles": [{"x": x, "top": POLE_TOP, "side": sd} for x, sd in POLES],
    "water": {"surfaceY": FLOOR_Y + 30, "frontY": 830},
    "props": {"fish": "props/fish.png", "crane": ["props/crane_0.png", "props/crane_1.png", "props/crane_2.png"],
              "leaf": "props/leaf.png", "scale": 2},
    "note": "web order: bg, back waves, flags, birds, puppets, fish, fgWater, front waves, fgLotus, wind",
}, open(os.path.join(OUT, "stage.json"), "w"), indent=2)
print("background done")
