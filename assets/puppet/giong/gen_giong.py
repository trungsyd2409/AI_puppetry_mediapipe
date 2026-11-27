"""Cau be cuoi ngua cam tre (Dong Ho style), one rig: horse + boy + bamboo.

Facing right (runs to the right). Canvas 720 x 640 design units, hooves on y=600.
Strings:
  left hand  index -> bamboo top (leafy) end, middle -> bamboo bottom end
  right hand index  -> near front leg (below knee), middle -> far front leg
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from dongho_lib import *  # noqa

OUT = os.path.dirname(os.path.abspath(__file__))
W, H = 720, 660
DY = 80  # everything is drawn, then shifted down so the bamboo tip fits
GROUND = 560
BOY_S = 1.3   # boy drawn at base size, scaled up around the hip

# ---------------- horse joints ----------------
NECK_BASE = (428, 300)
TAIL_ROOT = (196, 298)
FN = dict(sh=(446, 356), kn=(456, 452), fe=(452, 530))   # front near
FF = dict(sh=(416, 354), kn=(420, 452), fe=(412, 530))   # front far
HN = dict(sh=(242, 352), kn=(216, 452), fe=(230, 530))   # hind near (hock)
HF = dict(sh=(272, 352), kn=(250, 452), fe=(262, 530))   # hind far

# ---------------- boy joints ----------------
HIP = (328, 270)
NECK = (334, 196)
SHO_N, ELB_N, WRI_N = (352, 208), (364, 246), (384, 196)
SHO_F, ELB_F, WRI_F = (314, 210), (300, 248), (334, 240)
KNEE, ANKLE = (378, 292), (372, 352)


def S(p):
    return (HIP[0] + (p[0] - HIP[0]) * BOY_S, HIP[1] + (p[1] - HIP[1]) * BOY_S)


def boy_g(svg):
    return (f'<g transform="translate({HIP[0]},{HIP[1]}) scale({BOY_S}) '
            f'translate({-HIP[0]},{-HIP[1]})">{svg}</g>')


# bamboo: bottom end A -> leafy top end B, passing through the near grip
_dir = (352 / 463.4, -302 / 463.4)
BAM_LEN = 500
_g = S((384, 196))
BAM_A = (_g[0] - _dir[0] * BAM_LEN * 0.46, _g[1] - _dir[1] * BAM_LEN * 0.46)
BAM_B = (_g[0] + _dir[0] * BAM_LEN * 0.54, _g[1] + _dir[1] * BAM_LEN * 0.54)


def bam_at(t):
    return lerp(BAM_A, BAM_B, t)


# =============== HORSE ===============
def strand(p0, p1, p2, p3, w0, fill, n=26, vein=True):
    """Long tapered lock (tail / mane), like the rooster's tail feathers."""
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        p = bez(p0, p1, p2, p3, t)
        nx, ny = bez_norm(p0, p1, p2, p3, t)
        w = w0 * (1 - t) ** 0.75 * (0.85 + 0.15 * math.sin(t * math.pi)) + 0.6
        left.append((p[0] + nx * w, p[1] + ny * w))
        right.append((p[0] - nx * w, p[1] - ny * w))
    d = "M" + " L".join(f2(p) for p in left) + " L" + " L".join(f2(p) for p in reversed(right)) + " Z"
    out = ink(d, fill, 2.4)
    if vein:
        mid = [bez(p0, p1, p2, p3, t / 10) for t in range(1, 9)]
        out += line("M" + " L".join(f2(p) for p in mid), 1.2,
                    INK if fill == TRANG else (TRANG if fill != VANG else SON))
    return out


LOCK_COLS = [LA, TRANG, SON]


def horse_body():
    body = ("M190,320 C188,284 222,266 262,274 C302,282 362,290 404,278 "
            "C440,268 474,298 478,336 C481,366 464,388 440,393 "
            "C390,404 300,410 246,400 C206,394 190,360 190,320 Z")
    deco = (line("M212,368 C238,392 318,400 380,397 C420,395 448,388 462,370", 2.6, TRANG)
            + line("M448,294 C464,308 471,326 470,348", 2.4, TRANG)
            + line("M206,312 C210,296 224,286 244,284", 2.4, TRANG)
            + spiral(440, 345, 15, 1.6, 200, TRANG, 2.8)
            + spiral(230, 330, 19, 1.7, 0, TRANG, 3.0, -1)
            + line("M250,352 C258,360 270,362 280,358 M252,368 C262,376 276,378 286,372", 1.8, TRANG))
    # saddle cloth: red border band, green field, ivory scroll pattern, red tassels
    cloth = ("M276,280 C300,286 360,290 394,284 C400,320 398,360 390,394 "
             "C350,404 310,404 282,398 C274,360 272,320 276,280 Z")
    field = ("M288,296 C310,300 356,302 382,298 C386,328 384,360 378,384 "
             "C350,390 316,390 294,386 C288,358 286,326 288,296 Z")
    motif = (ink("M334,318 L352,340 L334,362 L316,340 Z", SON, 2.2)
             + f'<circle cx="334" cy="340" r="5" fill="{TRANG}" stroke="{INK}" stroke-width="1.6"/>'
             + swirl(306, 372, 0.55, 0, sw=2.0, color=TRANG) + swirl(362, 372, 0.55, 180, sw=2.0, color=TRANG)
             + swirl(306, 312, 0.5, 0, sw=2.0, color=TRANG) + swirl(364, 312, 0.5, 180, sw=2.0, color=TRANG))
    fringe = "".join(tassel(290 + i * 33, 398 + (2 if i % 2 else 0), 0.7) for i in range(4))
    saddle = ("M290,272 C300,262 312,268 318,276 C330,282 344,282 356,276 "
              "C364,266 380,262 388,272 C384,290 372,296 340,296 C306,296 292,290 290,272 Z")
    breast = "M392,302 C420,312 450,328 474,332 L476,344 C450,342 420,328 390,318 Z"
    crupper = "M282,292 C256,288 226,290 204,302 L206,312 C228,300 256,300 282,302 Z"
    bells = "".join(bell(*lerp((404, 318), (468, 346), t), 6.5) for t in (0.1, 0.4, 0.7, 1.0))
    return (ink(body, NAU, 3.8) + deco
            + ink(crupper, SON, 2.2) + dots_row((212, 304), (276, 297), 6, 1.8, VANG)
            + ink(cloth, SON, 3.2) + ink(field, LA, 2.0) + motif + fringe
            + ink(breast, SON, 2.2) + bells
            + ink(saddle, SON, 3.0) + line("M300,281 C320,289 356,289 380,279", 1.8, VANG))


def mane():
    """Feather-like locks along the neck crest, cycling green / ivory / red."""
    p0, p1, p2, p3 = (502, 150), (470, 168), (420, 214), (400, 284)
    out = ""
    N = 11
    for i in range(N, -1, -1):
        t = i / N
        p = bez(p0, p1, p2, p3, t)
        nx, ny = bez_norm(p0, p1, p2, p3, t)
        if nx > 0 or ny > 0:
            nx, ny = -nx, -ny
        # direction: outward, swept back toward the withers
        a = math.atan2(ny, nx) - 0.55
        L = 46 + 10 * math.sin(t * math.pi)
        dx, dy = math.cos(a), math.sin(a)
        base = (p[0] - nx * 6, p[1] - ny * 6)
        tip = (base[0] + dx * L, base[1] + dy * L)
        c1 = (base[0] + dx * L * 0.35 - dy * 8, base[1] + dy * L * 0.35 + dx * 8)
        c2 = (base[0] + dx * L * 0.75 + dy * 6, base[1] + dy * L * 0.75 - dx * 6)
        out += strand(base, c1, c2, tip, 11, LOCK_COLS[i % 3], 14)
    return out


def horse_neck_head():
    neck = ("M392,286 C406,238 448,190 494,158 C510,146 526,150 534,166 "
            "C550,192 572,220 590,242 C598,256 590,270 575,270 "
            "C561,270 550,264 540,254 C528,244 512,244 498,252 "
            "C482,266 472,296 470,338 C450,344 418,330 392,286 Z")
    ear_far = ink("M512,158 L522,124 L534,160 Z", NAU_DARK, 2.4)
    ear = (ink("M495,162 C494,146 498,128 501,116 C510,128 520,146 522,156 Z", NAU, 2.6)
           + line("M502,152 C502,142 503,134 504,128", 1.6, HONG))
    deco = (line("M486,262 C478,284 474,308 474,332", 2.4, TRANG)
            + spiral(512, 228, 11, 1.5, 160, TRANG, 2.4)
            + line("M552,224 C562,236 572,246 580,252", 1.8, TRANG))
    eye = (ink("M521,188 C528,179 545,178 552,190 C545,197 530,198 521,188 Z", TRANG, 2.0)
           + f'<circle cx="537" cy="188" r="5.2" fill="{INK}"/>'
           + f'<circle cx="535.5" cy="186.5" r="1.4" fill="{TRANG}"/>'
           + line("M518,184 C526,175 540,173 551,181", 3.0, SON)
           + line("M516,175 C526,166 540,164 549,169", 1.7))
    nose = spiral(579, 249, 6, 1.3, 220, INK, 2.0) + line("M577,264 C566,262 556,258 548,252", 2.0)
    bridle = (ink(capsule((548, 210), (580, 238), 4.5, 4.5), SON, 1.8)
              + ink(capsule((522, 160), (544, 232), 4, 4), SON, 1.8)
              + dots_row((548, 210), (580, 238), 4, 1.5, VANG) + dots_row((522, 160), (544, 232), 5, 1.5, VANG)
              + ink("M535,214 A9,9 0 1 1 553,214 A9,9 0 1 1 535,214 Z", SON, 2.0)
              + tassel(544, 222, 0.7))
    forelock = (strand((514, 152), (526, 156), (532, 166), (534, 182), 6, LA, 10, False)
                + strand((520, 150), (534, 154), (542, 164), (546, 176), 5, SON, 10, False))
    collar = (ink("M410,262 C430,272 456,284 478,286 L478,300 C452,298 428,288 404,276 Z", SON, 2.4)
              + "".join(bell(*lerp((414, 280), (474, 302), t), 7) for t in (0.0, 0.33, 0.66, 1.0)))
    return (ear_far + ink(neck, NAU, 3.8) + deco + mane() + ear + forelock
            + eye + nose + bridle + collar)


def horse_tail():
    out = ink("M190,288 L210,288 L210,306 L190,306 Z", SON, 2)
    specs = [
        ((200, 300), (170, 300), (150, 360), (132, 470), 12, LA),
        ((200, 302), (176, 312), (166, 380), (156, 488), 12, TRANG),
        ((200, 304), (186, 330), (184, 400), (180, 494), 11, SON),
        ((200, 300), (164, 296), (132, 340), (112, 432), 10, TRANG),
        ((202, 306), (196, 340), (200, 410), (204, 476), 9, LA),
    ]
    for p0, p1, p2, p3, w, c in specs:
        out += strand(p0, p1, p2, p3, w, c)
    return out


def hoof(fe, far=False):
    x, y = fe
    d = f"M{x-14},{y+4} L{x+14},{y+4} L{x+18},{GROUND} L{x-16},{GROUND} Z"
    tuft = (f"M{x-16},{y+8} C{x-24},{y-2} {x-18},{y-16} {x-10},{y-18} "
            f"C{x-6},{y-8} {x},{y-12} {x+4},{y-20} C{x+8},{y-10} {x+14},{y-14} {x+18},{y-14} "
            f"C{x+22},{y-2} {x+20},{y+6} {x+16},{y+8} Z")
    return (ink(d, INK, 3) + ink(tuft, VANG_LIGHT if far else TRANG, 2.2)
            + line(f"M{x-8},{y-2} C{x-10},{y+2} {x-8},{y+5} {x-5},{y+5} "
                   f"M{x+6},{y-4} C{x+4},{y} {x+6},{y+4} {x+9},{y+4}", 1.3))


def _inner_edge(p1, p2, r1, r2, side=1, inset=6):
    """White contour line inside a limb, along one edge."""
    L = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    nx, ny = -(p2[1] - p1[1]) / L * side, (p2[0] - p1[0]) / L * side
    a = (p1[0] + nx * (r1 - inset), p1[1] + ny * (r1 - inset))
    b = (p2[0] + nx * (r2 - inset * 0.6), p2[1] + ny * (r2 - inset * 0.6))
    a = lerp(a, b, 0.12)
    return line(f"M{f2(a)} L{f2(b)}", 2.0, TRANG)


def leg_upper(L, far, front):
    col = NAU_DARK if far else NAU
    r1 = 30 if front else 38
    out = ink(capsule(L["sh"], L["kn"], r1, 13), col, 3.4)
    if not far:
        out += _inner_edge(L["sh"], L["kn"], r1, 13, -1 if front else 1)
        k = L["kn"]
        out += spiral(k[0], k[1] - 6, 6, 1.3, 90, TRANG, 1.8)
    return out


def leg_lower(L, far):
    col = NAU_DARK if far else NAU
    out = ink(capsule(L["kn"], L["fe"], 13, 10), col, 3.2)
    if not far:
        out += _inner_edge(L["kn"], L["fe"], 13, 10, -1)
    return out + hoof(L["fe"], far)


# =============== BOY ===============
def boy_torso():
    body = ("M302,276 C292,248 296,216 312,202 C324,192 346,192 360,202 "
            "C374,218 374,250 364,278 Z")
    yem_out = "M311,204 L360,204 L371,258 C352,283 318,283 299,258 Z"
    yem_in = "M318,212 L353,212 L362,255 C346,272 324,272 308,255 Z"
    motif = (spiral(335, 236, 9, 1.4, 0, TRANG, 2.0)
             + line("M326,252 C330,258 340,258 344,252", 1.8, TRANG))
    straps = line("M315,205 L325,194 M357,205 L347,194", 2.6)
    shorts = ink("M298,268 C318,284 352,284 370,268 L368,292 C346,302 320,302 300,292 Z", LA, 2.8)
    sash = (ink("M298,262 C320,272 352,272 370,262 L371,274 C350,284 318,284 297,274 Z", VANG, 2.4)
            + strand((300, 270), (286, 280), (272, 296), (258, 318), 6, VANG, 12, False)
            + strand((304, 274), (296, 290), (292, 304), (290, 324), 5, SON, 12, False))
    return ink(body, DA, 3) + shorts + ink(yem_out, LA, 3) + ink(yem_in, SON, 1.6) + motif + straps + sash


def boy_head():
    cx, cy = 340, 150
    neck = ink("M327,182 L327,200 L346,200 L346,182 Z", DA, 2.4)
    face = (f"M{cx},{cy-44} C{cx+30},{cy-46} {cx+48},{cy-24} {cx+46},{cy+4} "
            f"C{cx+44},{cy+30} {cx+26},{cy+44} {cx+2},{cy+44} "
            f"C{cx-26},{cy+44} {cx-44},{cy+28} {cx-44},{cy} "
            f"C{cx-44},{cy-26} {cx-28},{cy-44} {cx},{cy-44} Z")
    ear = (ink(f"M{cx-38},{cy-6} C{cx-54},{cy-12} {cx-56},{cy+14} {cx-38},{cy+14} Z", DA, 2.4)
           + line(f"M{cx-43},{cy-1} C{cx-48},{cy+2} {cx-47},{cy+8} {cx-42},{cy+8}", 1.3))
    # Dong Ho kid hair: small tuft on the crown + a lock behind the ear
    tuft = ink(f"M{cx+2},{cy-42} C{cx-4},{cy-52} {cx+2},{cy-62} {cx+12},{cy-66} "
               f"C{cx+12},{cy-58} {cx+20},{cy-54} {cx+26},{cy-56} "
               f"C{cx+24},{cy-46} {cx+14},{cy-40} {cx+2},{cy-42} Z", INK, 1.6)
    tuft += line(f"M{cx+6},{cy-46} C{cx+8},{cy-52} {cx+12},{cy-56} {cx+16},{cy-58}", 1.0, XAM)
    lock = ink(f"M{cx-40},{cy-18} C{cx-50},{cy-24} {cx-54},{cy-36} {cx-46},{cy-44} "
               f"C{cx-44},{cy-34} {cx-38},{cy-30} {cx-32},{cy-30} Z", INK, 1.6)
    # soft brush features: long thin brows, narrow eyes with the pupil tucked under the lid
    brows = (line(f"M{cx+2},{cy-13} C{cx+10},{cy-20} {cx+20},{cy-20} {cx+27},{cy-15}", 1.7)
             + line(f"M{cx+32},{cy-14} C{cx+36},{cy-18} {cx+41},{cy-18} {cx+45},{cy-13}", 1.5))
    eyes = (line(f"M{cx+7},{cy-2} C{cx+11},{cy-8} {cx+21},{cy-8} {cx+26},{cy-3}", 2.2)
            + f'<ellipse cx="{cx+17.5}" cy="{cy-3.6}" rx="3.2" ry="2.8" fill="{INK}"/>'
            + line(f"M{cx+10},{cy+1} C{cx+14},{cy+2} {cx+20},{cy+2} {cx+24},{cy}", 0.9, DA_SHADE)
            + line(f"M{cx+33},{cy-3} C{cx+36},{cy-7} {cx+41},{cy-7} {cx+44},{cy-3}", 1.9)
            + f'<ellipse cx="{cx+39}" cy="{cy-4}" rx="2.4" ry="2.3" fill="{INK}"/>')
    nose = line(f"M{cx+38},{cy+3} C{cx+43},{cy+9} {cx+41},{cy+13} {cx+35},{cy+13}", 1.5)
    cheek = f'<ellipse cx="{cx+12}" cy="{cy+15}" rx="7" ry="5" fill="{HONG}"/>'
    mouth = (ink(f"M{cx+22},{cy+24} C{cx+26},{cy+29} {cx+33},{cy+28} {cx+36},{cy+23} "
                 f"C{cx+31},{cy+25} {cx+26},{cy+25} {cx+22},{cy+24} Z", SON, 1.2))
    chin = line(f"M{cx-4},{cy+38} C{cx+4},{cy+41} {cx+12},{cy+41} {cx+20},{cy+38}", 1.2, DA_SHADE)
    return neck + ear + ink(face, DA, 2.8) + lock + tuft + brows + eyes + nose + cheek + mouth + chin


def fist(c, s=1.0):
    x, y = c
    d = (f"M{x-11},{y-8} C{x-6},{y-14} {x+8},{y-14} {x+12},{y-6} "
         f"C{x+15},{y+2} {x+12},{y+12} {x+2},{y+13} C{x-8},{y+14} {x-14},{y+6} {x-11},{y-8} Z")
    return (ink(d, DA, 2.4)
            + line(f"M{x-5},{y-4} C{x},{y-6} {x+5},{y-5} {x+8},{y-3} "
                   f"M{x-5},{y+3} C{x},{y+1} {x+5},{y+2} {x+8},{y+4}", 1.1))


def arm_upper(sho, elb, far):
    return ink(capsule(sho, elb, 11, 9), DA_SHADE if far else DA, 2.6)


def arm_fore(elb, wri, far):
    band = ink(capsule(lerp(elb, wri, 0.72), lerp(elb, wri, 0.86), 9, 9), VANG, 1.8)
    return ink(capsule(elb, wri, 9, 8), DA_SHADE if far else DA, 2.6) + band + fist(wri)


def boy_thigh():
    return (ink(capsule(HIP, KNEE, 17, 13), LA, 2.8)
            + line(f"M{HIP[0]+4},{HIP[1]+11} C{(HIP[0]+KNEE[0])/2},{HIP[1]+18} "
                   f"{KNEE[0]-12},{KNEE[1]+8} {KNEE[0]-4},{KNEE[1]+9}", 1.6, TRANG))


def boy_shin():
    x, y = ANKLE
    foot = (f"M{x-10},{y-6} C{x-10},{y+6} {x-4},{y+12} {x+10},{y+12} "
            f"C{x+24},{y+12} {x+28},{y+4} {x+18},{y-2} C{x+10},{y-6} {x+4},{y-8} {x-10},{y-6} Z")
    anklet = ink(capsule((x - 11, y - 10), (x + 11, y - 12), 4, 4), SON, 1.8)
    toes = line(f"M{x+16},{y+3} C{x+19},{y+5} {x+21},{y+7} {x+22},{y+9}", 1.0)
    return ink(capsule(KNEE, ANKLE, 12, 9), DA, 2.6) + ink(foot, DA, 2.4) + anklet + toes


# =============== BAMBOO ===============
def bamboo():
    A, B = BAM_A, BAM_B
    L = math.hypot(B[0] - A[0], B[1] - A[1])
    ang = angle_deg(A, B)
    stalk = capsule((0, 0), (L, 0), 10, 7)
    hl = line(f"M10,-4 L{L*0.45:.1f},-3.5 M{L*0.52:.1f},-3.5 L{L-16:.1f},-2.5", 1.6, VANG_LIGHT)
    nodes = ""
    n = 8
    for i in range(1, n):
        x = L * i / n
        r = 10 - 3 * i / n
        nodes += line(f"M{x-2:.1f},{-r:.1f} C{x+1:.1f},{-r/2:.1f} {x+1:.1f},{r/2:.1f} {x-2:.1f},{r:.1f}", 2.6)
        nodes += line(f"M{x+3:.1f},{-r+2:.1f} L{x+3:.1f},{r-2:.1f}", 1.4, LA_DARK)
    leaves = ""
    for x, rot, s, c in [(L - 4, -24, 0.95, LA), (L - 6, 14, 0.85, LA_DARK), (L - 30, -62, 0.8, LA_DARK),
                         (L - 34, 44, 0.75, LA), (L * 0.62, -50, 0.6, LA), (L * 0.62, 36, 0.55, LA_DARK)]:
        leaves += leaf(x, 0, rot, s, c, LA_DARK if c == LA else LA)
    twig = line(f"M{L*0.62:.1f},0 l-6,-10 M{L*0.62:.1f},0 l-6,10", 1.6)
    return (f'<g transform="translate({A[0]:.2f},{A[1]:.2f}) rotate({ang:.2f})">'
            f'{ink(stalk, LA, 3.0)}{hl}{nodes}{twig}{leaves}</g>')


# =============== build ===============
def main():
    # far arm grips bamboo behind; near fist drawn over bamboo
    parts = [
        # id, parent, z, svg, pivot, limitDeg
        ("tail", "body", 1, horse_tail(), TAIL_ROOT, (-35, 45)),
        ("hind_far_upper", "body", 2, leg_upper(HF, True, False), HF["sh"], (-45, 55)),
        ("hind_far_lower", "hind_far_upper", 2, leg_lower(HF, True), HF["kn"], (-10, 100)),
        ("front_far_upper", "body", 2, leg_upper(FF, True, True), FF["sh"], (-70, 60)),
        ("front_far_lower", "front_far_upper", 2, leg_lower(FF, True), FF["kn"], (-120, 10)),
        ("body", None, 4, horse_body(), (330, 330), None),
        ("hind_near_upper", "body", 5, leg_upper(HN, False, False), HN["sh"], (-45, 55)),
        ("hind_near_lower", "hind_near_upper", 5, leg_lower(HN, False), HN["kn"], (-10, 100)),
        ("front_near_upper", "body", 5, leg_upper(FN, False, True), FN["sh"], (-70, 60)),
        ("front_near_lower", "front_near_upper", 5, leg_lower(FN, False), FN["kn"], (-120, 10)),
        ("neck", "body", 6, horse_neck_head(), NECK_BASE, (-30, 25)),
        ("boy_arm_far_upper", "boy_torso", 7, boy_g(arm_upper(SHO_F, ELB_F, True)), S(SHO_F), (-120, 120)),
        ("boy_arm_far_fore", "boy_arm_far_upper", 7, boy_g(arm_fore(ELB_F, WRI_F, True)), S(ELB_F), (-150, 20)),
        ("boy_torso", "body", 8, boy_g(boy_torso()), S(HIP), (-25, 25)),
        ("boy_head", "boy_torso", 9, boy_g(boy_head()), S(NECK), (-30, 30)),
        ("boy_thigh", "boy_torso", 10, boy_g(boy_thigh()), S(HIP), (-30, 30)),
        ("boy_shin", "boy_thigh", 10, boy_g(boy_shin()), S(KNEE), (-20, 60)),
        ("bamboo", "boy_arm_near_fore", 11, bamboo(), S(WRI_N), None),
        ("boy_arm_near_upper", "boy_torso", 12, boy_g(arm_upper(SHO_N, ELB_N, False)), S(SHO_N), (-120, 120)),
        ("boy_arm_near_fore", "boy_arm_near_upper", 12, boy_g(arm_fore(ELB_N, WRI_N, False)), S(ELB_N), (-150, 20)),
    ]
    sh = lambda p: (p[0], p[1] + DY)
    parts = [(i, par, z, f'<g transform="translate(0,{DY})">{svg}</g>', sh(pv), lim)
             for i, par, z, svg, pv, lim in parts]
    kn_off = 22  # string anchor a bit below the knee
    strings = [
        ("bamboo_top", "bamboo", bam_at(0.97), "left", "index", 8),
        ("bamboo_bottom", "bamboo", bam_at(0.03), "left", "middle", 12),
        ("front_near", "front_near_lower", (FN["kn"][0], FN["kn"][1] + kn_off), "right", "index", 8),
        ("front_far", "front_far_lower", (FF["kn"][0], FF["kn"][1] + kn_off), "right", "middle", 12),
    ]
    strings = [(a, b, sh(p), c, d, e) for a, b, p, c, d, e in strings]
    colliders = {
        "body": {"density": 2.0, "shapes": [capsule_shape((222, 330), (450, 336), 58)]},
        "neck": {"density": 1.0, "shapes": [capsule_shape((440, 290), (500, 190), 26),
                                            capsule_shape((510, 190), (575, 250), 20)]},
        "front_near_lower": {"density": 1.0, "shapes": [capsule_shape(FN["kn"], (FN["fe"][0], GROUND - 8), 12)]},
        "front_far_lower": {"density": 1.0, "shapes": [capsule_shape(FF["kn"], (FF["fe"][0], GROUND - 8), 12)]},
        "hind_near_lower": {"density": 1.0, "shapes": [capsule_shape(HN["kn"], (HN["fe"][0], GROUND - 8), 12)]},
        "hind_far_lower": {"density": 1.0, "shapes": [capsule_shape(HF["kn"], (HF["fe"][0], GROUND - 8), 12)]},
        "boy_torso": {"density": 0.8, "shapes": [capsule_shape(S((334, 266)), S((336, 212)), 38)]},
        "boy_head": {"density": 0.6, "shapes": [circle_shape(S((342, 150)), 56)]},
        "bamboo": {"density": 0.4, "shapes": [capsule_shape(bam_at(0.02), bam_at(0.98), 9)]},
    }
    for c in colliders.values():
        for shp in c["shapes"]:
            for k in ("c", "a", "b"):
                if k in shp:
                    shp[k] = [shp[k][0], shp[k][1] + DY]
    extra = {
        "groundY": GROUND + DY,
        "gripNear": list(sh(S(WRI_N))), "gripFar": list(sh(S(WRI_F))),
        "bambooEnds": [list(sh(BAM_A)), list(sh(BAM_B))],
        "runLegs": ["front_near", "front_far", "hind_near", "hind_far"],
        "tailRoot": list(sh(TAIL_ROOT)),
    }
    rig = build(OUT, "giong", (W, H), parts, strings, colliders, extra)
    print("parts:", len(rig["parts"]), "feetY", rig["feetY"])


if __name__ == "__main__":
    main()
