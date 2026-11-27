"""Chien binh tuyet: original winter-warrior puppet inspired by the Russian folk Snow Maiden.

Same skeleton and string layout as the other puppets, plus swinging parts:
  braid   thick white plait over the shoulder (child of head)
  cape    navy cape behind the body (child of torso)
  skirt   white/blue ball-gown skirt (child of torso)
  spear   silver spear held in the right hand (child of forearm_R)

Used by the web app's default "snow" scene.
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from puppet_lib import *  # noqa

OUT = os.path.dirname(os.path.abspath(__file__))

WHITE = "#F7F9FC"
WHITE_SH = "#D3DDEB"
BLUE = "#3A6FB8"
BLUE_D = "#1E3A6E"
BLUE_L = "#9CC3EB"
SILVER = "#C9D1DD"
SILVER_L = "#EEF2F7"
SILVER_D = "#8793A8"
SKIN = "#F6D9C6"
SKIN_L = "#FCEBDF"
SKIN_SH = "#DDB39C"
HAIR = "#F3F5F9"
HAIR_SH = "#BFC9DA"

NECK = (200, 190)
SHO_L, ELB_L, WRI_L = (160, 224), (130, 304), (116, 386)
HIP_L, KNE_L, ANK_L = (184, 372), (180, 500), (178, 622)
WAIST = (200, 334)
BRAID_PIVOT = (174, 160)
CAPE_PIVOT = (200, 210)
SPEAR_X = 288
GRIP = (SPEAR_X, 398)


def snowflake(x, y, r, color=BLUE_L, w=1.6, rot=0):
    arms = ""
    for i in range(6):
        a = math.radians(rot + i * 60)
        ex, ey = x + r * math.cos(a), y + r * math.sin(a)
        arms += f"M{x},{y} L{ex:.2f},{ey:.2f} "
        for t, b in ((0.55, 0.32), (0.8, 0.22)):
            bx, by = x + r * t * math.cos(a), y + r * t * math.sin(a)
            for s in (-1, 1):
                ba = a + s * math.radians(45)
                arms += f"M{bx:.2f},{by:.2f} L{bx + r * b * math.cos(ba):.2f},{by + r * b * math.sin(ba):.2f} "
    return (f'<path d="{arms}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>'
            f'<circle cx="{x}" cy="{y}" r="{max(1.2, r * 0.12):.2f}" fill="{color}"/>')


def silver_rivet(x, y, r=4.5):
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{SILVER}" stroke="{OUTLINE}" stroke-width="2"/>'
            f'<circle cx="{x}" cy="{y}" r="{r * 0.38:.2f}" fill="{BLUE_D}"/>')


def rhombus_band(y, x0, x1, size=7, color=BLUE, curve=0.0):
    """Russian folk embroidery: a chain of small diamonds along a (slightly curved) line."""
    out = ""
    n = int((x1 - x0) / (size * 2.2))
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / max(1, n)
        yy = y + curve * ((x - 200) / 100) ** 2
        out += (f'<path d="M{x:.1f},{yy - size:.1f} L{x + size * 0.7:.1f},{yy:.1f} L{x:.1f},{yy + size:.1f} '
                f'L{x - size * 0.7:.1f},{yy:.1f} Z" fill="none" stroke="{color}" stroke-width="1.5"/>'
                f'<circle cx="{x:.1f}" cy="{yy:.1f}" r="1.4" fill="{color}"/>')
    return out


def grad(gid, c0, c1, c2=None, horizontal=True):
    x2, y2 = ("1", "0") if horizontal else ("0", "1")
    stops = f'<stop offset="0" stop-color="{c0}"/><stop offset="{0.5 if c2 else 1}" stop-color="{c1}"/>'
    if c2:
        stops += f'<stop offset="1" stop-color="{c2}"/>'
    return f'<linearGradient id="{gid}" x1="0" y1="0" x2="{x2}" y2="{y2}">{stops}</linearGradient>'


# ---------------------------------------------------------------- head
def draw_head():
    hair_back = (f'<path d="M156,118 C142,160 146,208 152,240 C158,246 168,244 176,236 C168,204 168,162 176,128 Z '
                 f'M244,118 C258,160 254,208 248,240 C242,246 232,244 224,236 C232,204 232,162 224,128 Z" fill="{HAIR}" '
                 f'stroke="{OUTLINE}" stroke-width="2.4"/>'
                 f'<path d="M160,150 C156,180 158,206 164,226 M240,150 C244,180 242,206 236,226" fill="none" '
                 f'stroke="{HAIR_SH}" stroke-width="1.6"/>')
    neck = (f'<path d="M189,166 L189,198 Q200,204 211,198 L211,166 Z" fill="{SKIN_SH}" '
            f'stroke="{OUTLINE}" stroke-width="2.6"/>')
    face = (f'<radialGradient id="g_face_w" cx="0.45" cy="0.42" r="0.7">'
            f'<stop offset="0" stop-color="{SKIN_L}"/><stop offset="0.7" stop-color="{SKIN}"/>'
            f'<stop offset="1" stop-color="{SKIN_SH}"/></radialGradient>'
            f'<path d="M200,98 C224,98 234,118 233,140 C232,162 218,180 200,184 '
            f'C182,180 168,162 167,140 C166,118 176,98 200,98 Z" fill="url(#g_face_w)" '
            f'stroke="{OUTLINE}" stroke-width="3"/>')
    bangs = (f'<path d="M168,122 C174,104 196,98 214,102 C226,106 234,116 234,128 '
             f'C226,118 214,114 204,120 C196,112 182,112 168,122 Z" fill="{HAIR}" stroke="{OUTLINE}" '
             f'stroke-width="2"/>'
             f'<path d="M182,112 C190,110 198,112 204,118 M212,110 C220,112 226,116 230,122" fill="none" '
             f'stroke="{HAIR_SH}" stroke-width="1.4"/>')
    brows = (f'<path d="M176,130 Q184,125 193,128 M207,128 Q216,125 224,130" fill="none" stroke="#9AA3B5" '
             f'stroke-width="2.2" stroke-linecap="round"/>')
    eyes = ""
    for ex in (185, 215):
        eyes += (f'<path d="M{ex-10},143 Q{ex},134 {ex+10},143 Q{ex},148 {ex-10},143 Z" fill="#FFFFFF"/>'
                 f'<circle cx="{ex}" cy="142" r="4.6" fill="#5E9BD6"/>'
                 f'<circle cx="{ex}" cy="142" r="2.2" fill="{BLUE_D}"/>'
                 f'<circle cx="{ex + 1.5}" cy="140.5" r="1.2" fill="#FFFFFF"/>'
                 f'<path d="M{ex-10},143 Q{ex},133 {ex+10},143" fill="none" stroke="{INK}" stroke-width="2.4" '
                 f'stroke-linecap="round"/>')
    face_detail = (f'<path d="M199,150 q-3,9 1,11 q3,1 5,-1" fill="none" stroke="{SKIN_SH}" stroke-width="1.8" '
                   f'stroke-linecap="round"/>'
                   f'<path d="M192,168 Q200,173 208,168 Q200,171 192,168 Z" fill="#C8707A" stroke="#9E4F5A" '
                   f'stroke-width="1.2"/>'
                   f'<ellipse cx="177" cy="158" rx="8" ry="4.5" fill="#E9A0A8" opacity="0.35"/>'
                   f'<ellipse cx="223" cy="158" rx="8" ry="4.5" fill="#E9A0A8" opacity="0.35"/>')
    # Russian winter fur hat (kubanka) with a snowflake badge
    hat = (grad("g_hat", BLUE_D, BLUE, BLUE_D)
           + f'<path d="M160,110 L162,70 C166,50 234,50 238,70 L240,110 Z" fill="url(#g_hat)" '
             f'stroke="{OUTLINE}" stroke-width="3"/>'
           + f'<path d="M168,64 C186,58 214,58 232,64" fill="none" stroke="{SILVER}" stroke-width="2"/>'
           + rhombus_band(72, 172, 228, 5, SILVER_L)
           + f'<circle cx="200" cy="50" r="5" fill="{SILVER}" stroke="{OUTLINE}" stroke-width="2"/>'
           + f'<path d="M152,104 '
           + " ".join(f"Q{x + 6},{96 if (x // 12) % 2 else 100} {x + 12},104" for x in range(152, 248, 12))
           + f' L248,122 '
           + " ".join(f"Q{x - 6},{130 if (x // 12) % 2 else 126} {x - 12},122" for x in range(248, 152, -12))
           + f' Z" fill="{WHITE}" stroke="{OUTLINE}" stroke-width="2.6"/>'
           + "".join(f'<path d="M{x},108 q3,6 0,12" fill="none" stroke="{WHITE_SH}" stroke-width="1.4"/>'
                     for x in range(160, 244, 9))
           + f'<circle cx="200" cy="86" r="15" fill="{BLUE_D}" stroke="{SILVER}" stroke-width="2.4"/>'
           + snowflake(200, 86, 11, SILVER_L, 1.6))
    earrings = (f'<path d="M168,166 l0,8" stroke="{SILVER}" stroke-width="1.6"/>'
                + snowflake(168, 178, 5, SILVER_L, 1.2)
                + f'<path d="M232,166 l0,8" stroke="{SILVER}" stroke-width="1.6"/>'
                + snowflake(232, 178, 5, SILVER_L, 1.2))
    return (hair_back + neck + face + bangs + brows + eyes + face_detail + earrings + hat
            + silver_rivet(*NECK, 4))


def draw_braid():
    segs = ""
    y, i = 168, 0
    while y < 330:
        x = 170 - (y - 168) * 0.06
        tilt = 28 if i % 2 else -28
        segs += (f'<ellipse cx="{x:.1f}" cy="{y}" rx="13" ry="9" transform="rotate({tilt} {x:.1f} {y})" '
                 f'fill="{HAIR}" stroke="{OUTLINE}" stroke-width="2"/>'
                 f'<path d="M{x - 7:.1f},{y - 2} q7,-4 14,0" fill="none" stroke="{HAIR_SH}" stroke-width="1.4" '
                 f'transform="rotate({tilt} {x:.1f} {y})"/>')
        y += 13
        i += 1
    tie = (f'<rect x="153" y="330" width="22" height="10" rx="3" fill="{BLUE}" stroke="{OUTLINE}" stroke-width="2"/>'
           f'<path d="M158,340 C152,354 150,364 146,372 M170,340 C172,352 176,362 180,370" fill="none" '
           f'stroke="{BLUE}" stroke-width="4" stroke-linecap="round"/>'
           f'<path d="M156,340 C152,356 156,370 164,380 C170,370 172,356 172,340 Z" fill="{HAIR}" '
           f'stroke="{OUTLINE}" stroke-width="2"/>')
    return segs + tie + silver_rivet(*BRAID_PIVOT, 3.5)


# ---------------------------------------------------------------- body
def draw_cape():
    d = "M156,206 C190,198 210,198 244,206 C262,320 282,460 298,598 Q200,622 102,598 C118,460 138,320 156,206 Z"
    return (grad("g_cape", BLUE_D, "#2B4E8C", BLUE_D)
            + f'<path d="{d}" fill="url(#g_cape)" stroke="{OUTLINE}" stroke-width="3"/>'
            + f'<path d="M110,590 Q200,612 290,590" fill="none" stroke="{SILVER}" stroke-width="3"/>'
            + rhombus_band(600, 116, 284, 6, BLUE_L, 1.4)
            + snowflake(132, 520, 12, BLUE_L, 1.4) + snowflake(268, 520, 12, BLUE_L, 1.4))


def draw_torso():
    body = ("M168,206 C186,199 214,199 232,206 C246,211 252,223 250,237 C248,270 238,300 228,338 "
            "L172,338 C162,300 152,270 150,237 C148,223 154,211 168,206 Z")
    collar = (f'<path d="M184,176 L216,176 L218,206 Q200,212 182,206 Z" fill="{BLUE}" stroke="{OUTLINE}" '
              f'stroke-width="2.6"/>'
              f'<path d="M184,182 L216,182" stroke="{SILVER_L}" stroke-width="1.6"/>'
              + snowflake(200, 196, 6, SILVER_L, 1.3))
    plate = ("M170,214 Q200,206 230,214 L234,262 Q218,300 200,308 Q182,300 166,262 Z")
    breastplate = (grad("g_plate", SILVER_D, SILVER_L, SILVER_D)
                   + f'<path d="{plate}" fill="url(#g_plate)" stroke="{OUTLINE}" stroke-width="2.8"/>'
                   + f'<path d="M200,212 L200,304 M176,224 Q200,216 224,224" fill="none" stroke="{SILVER_D}" '
                     f'stroke-width="1.4"/>'
                   + f'<circle cx="200" cy="254" r="17" fill="{BLUE_D}" stroke="{SILVER}" stroke-width="2"/>'
                   + snowflake(200, 254, 13, BLUE_L, 1.6)
                   + "".join(silver_rivet(x, y, 2.6) for x, y in ((176, 226), (224, 226), (184, 284), (216, 284))))
    belt = (f'<path d="M168,320 Q200,330 232,320 L234,342 Q200,352 166,342 Z" fill="{BLUE}" '
            f'stroke="{OUTLINE}" stroke-width="2.6"/>'
            f'<circle cx="200" cy="334" r="9" fill="{SILVER}" stroke="{OUTLINE}" stroke-width="2"/>'
            + snowflake(200, 334, 6, BLUE_D, 1.2))
    return (grad("g_body_w", WHITE_SH, WHITE, WHITE_SH)
            + f'<path d="{body}" fill="url(#g_body_w)" stroke="{OUTLINE}" stroke-width="3.2"/>'
            + f'<path d="M156,240 Q200,232 244,240" fill="none" stroke="{BLUE_L}" stroke-width="1.4" '
              f'stroke-dasharray="4 3"/>'
            + breastplate + belt + collar)


def draw_skirt():
    full = "M172,334 C158,420 120,560 106,642 Q200,670 294,642 C280,560 242,420 228,334 Z"
    left = "M172,334 C158,420 120,560 106,642 Q140,654 170,658 C176,560 186,430 194,338 Z"
    right = "M228,334 C242,420 280,560 294,642 Q260,654 230,658 C224,560 214,430 206,338 Z"
    under_flakes = (snowflake(200, 430, 13) + snowflake(200, 520, 18) + snowflake(186, 600, 10)
                    + snowflake(214, 606, 10) + snowflake(200, 380, 8))
    over_flakes = "".join(snowflake(x, y, r, WHITE, 1.3) for x, y, r in
                          ((168, 430, 8), (150, 520, 11), (136, 600, 9), (232, 430, 8), (250, 520, 11), (264, 600, 9)))
    return (grad("g_under", WHITE_SH, WHITE, WHITE_SH)
            + grad("g_over", BLUE_D, BLUE, BLUE_L)
            + f'<path d="{full}" fill="url(#g_under)" stroke="{OUTLINE}" stroke-width="3"/>'
            + under_flakes
            + rhombus_band(648, 150, 250, 6, BLUE, 1.0)
            + f'<path d="{left}" fill="url(#g_over)" stroke="{OUTLINE}" stroke-width="2.8"/>'
            + f'<path d="{right}" fill="url(#g_over)" stroke="{OUTLINE}" stroke-width="2.8"/>'
            + f'<path d="M194,338 C186,430 176,560 170,658 M206,338 C214,430 224,560 230,658" fill="none" '
              f'stroke="{SILVER}" stroke-width="2.6"/>'
            + over_flakes
            + f'<path d="M108,640 Q140,652 170,656 M230,656 Q260,652 292,640" fill="none" stroke="{SILVER_L}" '
              f'stroke-width="2.4"/>'
            + silver_rivet(*WAIST, 4))


# ---------------------------------------------------------------- limbs
def draw_upper_arm():
    pauldron = "".join(
        f'<path d="M{SHO_L[0] - 22 + k * 3},{SHO_L[1] - 4 + k * 9} Q{SHO_L[0] - 2},{SHO_L[1] - 22 + k * 9} '
        f'{SHO_L[0] + 18 - k * 2},{SHO_L[1] - 6 + k * 9} L{SHO_L[0] + 14 - k * 2},{SHO_L[1] + 4 + k * 9} '
        f'Q{SHO_L[0] - 2},{SHO_L[1] - 8 + k * 9} {SHO_L[0] - 18 + k * 3},{SHO_L[1] + 6 + k * 9} Z" '
        f'fill="{SILVER if k % 2 == 0 else SILVER_L}" stroke="{OUTLINE}" stroke-width="2.2"/>'
        for k in range(3))
    return (limb("ua_w", SHO_L, ELB_L, 14, 11, fill=WHITE, shade=WHITE_SH, stitch=BLUE_L,
                 pattern=band(SHO_L, ELB_L, 0.82, 11, 6, BLUE, BLUE_L))
            + pauldron + silver_rivet(*SHO_L, 4))


def draw_forearm():
    a = angle_deg(ELB_L, WRI_L)
    wrist = (WRI_L[0] + math.cos(math.radians(a)) * 9, WRI_L[1] + math.sin(math.radians(a)) * 9)
    p0, p1 = lerp(ELB_L, WRI_L, 0.3), lerp(ELB_L, WRI_L, 0.95)
    bracer = (f'<path d="{capsule(p0, p1, 13, 11.5)}" fill="{SILVER}" stroke="{OUTLINE}" stroke-width="2.4"/>'
              f'<path d="{capsule(p0, p1, 8, 7)}" fill="none" stroke="{SILVER_L}" stroke-width="1.4"/>')
    gem = lerp(ELB_L, WRI_L, 0.62)
    return (hand(wrist, a, thumb_side=-1, s=0.72, fill=SKIN, light=SKIN_L)
            + limb("fa_w", ELB_L, WRI_L, 11, 9.5, fill=WHITE, shade=WHITE_SH, stitch=BLUE_L)
            + bracer
            + f'<path d="M{gem[0]},{gem[1] - 7} l5,7 l-5,7 l-5,-7 Z" fill="{BLUE}" stroke="{OUTLINE}" stroke-width="1.6"/>'
            + silver_rivet(*ELB_L, 4))


def boot_foot(ankle):
    x, y = ankle
    d = (f"M{x + 12},{y - 4} C{x + 14},{y + 18} {x + 6},{y + 30} {x - 16},{y + 32} "
         f"C{x - 34},{y + 33} {x - 42},{y + 26} {x - 40},{y + 20} C{x - 26},{y + 16} {x - 14},{y + 10} {x - 12},{y - 4} Z")
    return (f'<path d="{d}" fill="{BLUE_D}" stroke="{OUTLINE}" stroke-width="2.8"/>'
            f'<path d="M{x - 40},{y + 20} C{x - 32},{y + 18} {x - 26},{y + 22} {x - 24},{y + 30}" fill="{SILVER}" '
            f'stroke="{OUTLINE}" stroke-width="1.6"/>')


def draw_thigh():
    return (limb("th_w", HIP_L, KNE_L, 18, 15, fill=WHITE, shade=WHITE_SH, stitch=BLUE_L)
            + silver_rivet(*HIP_L, 4))


def draw_shin():
    knee_guard = (f'<ellipse cx="{KNE_L[0]}" cy="{KNE_L[1] + 6}" rx="17" ry="13" fill="{SILVER}" '
                  f'stroke="{OUTLINE}" stroke-width="2.2"/>' + snowflake(KNE_L[0], KNE_L[1] + 6, 7, BLUE_D, 1.2))
    return (boot_foot(ANK_L)
            + limb("sh_w", KNE_L, ANK_L, 15, 13, fill=BLUE_D, shade="#142A52", stitch=BLUE_L,
                   pattern=band(KNE_L, ANK_L, 0.9, 13, 6, SILVER, BLUE))
            + knee_guard + silver_rivet(*KNE_L, 4))


# ---------------------------------------------------------------- spear
def draw_spear():
    x = SPEAR_X
    shaft = (grad("g_shaft", SILVER_D, SILVER_L, SILVER_D)
             + f'<rect x="{x - 4.5}" y="76" width="9" height="572" rx="4" fill="url(#g_shaft)" '
               f'stroke="{OUTLINE}" stroke-width="2.2"/>'
             + "".join(f'<path d="M{x - 4.5},{y} L{x + 4.5},{y + 7}" stroke="{BLUE}" stroke-width="3"/>'
                       for y in range(356, 446, 8))
             + f'<path d="M{x - 7},648 L{x + 7},648 L{x},672 Z" fill="{SILVER}" stroke="{OUTLINE}" stroke-width="2"/>')
    blade = (grad("g_blade", SILVER_D, SILVER_L, SILVER_D)
             + f'<path d="M{x},4 C{x + 14},26 {x + 16},48 {x},76 C{x - 16},48 {x - 14},26 {x},4 Z" '
               f'fill="url(#g_blade)" stroke="{OUTLINE}" stroke-width="2.4"/>'
             + f'<path d="M{x},10 L{x},72" stroke="{SILVER_D}" stroke-width="1.4"/>')
    guard = (f'<circle cx="{x}" cy="84" r="12" fill="{BLUE_D}" stroke="{SILVER}" stroke-width="2.4"/>'
             + snowflake(x, 84, 16, SILVER_L, 2.2, rot=90)
             + f'<circle cx="{x}" cy="84" r="4" fill="{BLUE_L}" stroke="{OUTLINE}" stroke-width="1.4"/>')
    tassel = (f'<path d="M{x - 2},96 C{x - 14},112 {x - 10},128 {x - 20},146" fill="none" stroke="{BLUE}" '
              f'stroke-width="5" stroke-linecap="round"/>'
              f'<path d="M{x + 2},96 C{x + 10},116 {x + 4},132 {x + 10},150" fill="none" stroke="{BLUE_L}" '
              f'stroke-width="4" stroke-linecap="round"/>'
              f'<circle cx="{x - 20}" cy="148" r="5" fill="{WHITE}" stroke="{OUTLINE}" stroke-width="1.6"/>')
    return shaft + tassel + guard + blade + silver_rivet(*GRIP, 3.5)


PARTS = [
    # id, parent, z, svg, pivot, limitDeg
    ("torso", None, 4, draw_torso(), (200, 280), None),
    ("head", "torso", 11, draw_head(), NECK, (-30, 30)),
    ("braid", "head", 7, draw_braid(), BRAID_PIVOT, (-25, 25)),
    ("cape", "torso", 0, draw_cape(), CAPE_PIVOT, (-18, 18)),
    ("skirt", "torso", 5, draw_skirt(), WAIST, (-12, 12)),
    ("thigh_L", "torso", 2, draw_thigh(), HIP_L, (-70, 60)),
    ("shin_L", "thigh_L", 1, draw_shin(), KNE_L, (-10, 120)),
    ("thigh_R", "torso", 2, f'<g {MIRROR}>{draw_thigh()}</g>', mx(HIP_L), (-60, 70)),
    ("shin_R", "thigh_R", 1, f'<g {MIRROR}>{draw_shin()}</g>', mx(KNE_L), (-120, 10)),
    ("upper_arm_L", "torso", 8, draw_upper_arm(), SHO_L, (-150, 60)),
    ("forearm_L", "upper_arm_L", 9, draw_forearm(), ELB_L, (-140, 10)),
    ("upper_arm_R", "torso", 8, f'<g {MIRROR}>{draw_upper_arm()}</g>', mx(SHO_L), (-60, 150)),
    ("forearm_R", "upper_arm_R", 10, f'<g {MIRROR}>{draw_forearm()}</g>', mx(ELB_L), (-10, 140)),
    ("spear", "forearm_R", 6, draw_spear(), GRIP, (-15, 15)),
]

STRINGS = [
    ("head", "head", (200, 50), "middle", 12),
    ("hand_L", "forearm_L", lerp(ELB_L, WRI_L, 1.22), "index", 8),
    ("hand_R", "forearm_R", mx(lerp(ELB_L, WRI_L, 1.22)), "ring", 16),
    ("knee_L", "shin_L", KNE_L, "thumb", 4),
    ("knee_R", "shin_R", mx(KNE_L), "pinky", 20),
]


def side(shapes_L):
    out = []
    for sh in shapes_L:
        m = dict(sh)
        for k in ("c", "a", "b"):
            if k in sh:
                m[k] = list(mx(sh[k]))
        out.append(m)
    return out


HAND_TIP_L = lerp(ELB_L, WRI_L, 1.3)
FOOT_L = ((ANK_L[0] + 4, ANK_L[1] + 20), (ANK_L[0] - 30, ANK_L[1] + 26))
ARM_U = [capsule_shape(SHO_L, ELB_L, 12)]
ARM_F = [capsule_shape(ELB_L, HAND_TIP_L, 10)]
LEG_U = [capsule_shape(HIP_L, KNE_L, 16)]
LEG_S = [capsule_shape(KNE_L, ANK_L, 14), capsule_shape(*FOOT_L, 9)]
COLLIDERS = {
    "torso": {"density": 1.0, "shapes": [capsule_shape((200, 236), (200, 318), 40)]},
    "head": {"density": 0.8, "shapes": [circle((200, 142), 38), capsule_shape((166, 88), (234, 88), 24)]},
    "braid": {"density": 0.25, "shapes": [capsule_shape((170, 175), (160, 365), 12)]},
    "cape": {"density": 0.2, "shapes": [capsule_shape((200, 260), (200, 520), 48), capsule_shape((136, 570), (264, 570), 30)]},
    "skirt": {"density": 0.3, "shapes": [capsule_shape((200, 410), (200, 560), 62), capsule_shape((136, 612), (264, 612), 30)]},
    "spear": {"density": 0.5, "shapes": [capsule_shape((SPEAR_X, 20), (SPEAR_X, 664), 7)]},
    "upper_arm_L": {"density": 1.0, "shapes": ARM_U}, "upper_arm_R": {"density": 1.0, "shapes": side(ARM_U)},
    "forearm_L": {"density": 1.0, "shapes": ARM_F}, "forearm_R": {"density": 1.0, "shapes": side(ARM_F)},
    "thigh_L": {"density": 1.0, "shapes": LEG_U}, "thigh_R": {"density": 1.0, "shapes": side(LEG_U)},
    "shin_L": {"density": 1.0, "shapes": LEG_S}, "shin_R": {"density": 1.0, "shapes": side(LEG_S)},
}


PREVIEW = """<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Chien binh tuyet rig</title>
<style>
  body { margin:0; font:14px system-ui,sans-serif; background:#1c2433; color:#1e2a3a; display:flex; flex-wrap:wrap;
         gap:16px; padding:16px; justify-content:center; align-items:flex-start; }
  canvas { background:radial-gradient(circle at 50% 35%, #f3f6fb, #d7e2ef 70%); border-radius:8px; max-width:100%; height:auto; }
  .panel { background:#eef3f9; border-radius:8px; padding:12px 14px; width:320px; max-width:100%; }
  label { display:grid; grid-template-columns:100px 1fr 44px; gap:6px; align-items:center; margin:4px 0; }
  button { border:1px solid #1e3a6e; background:#fff; border-radius:6px; padding:6px 10px; cursor:pointer; margin:0 6px 8px 0; }
  button.on { background:#1e3a6e; color:#fff; }
</style></head><body>
<canvas id="cv" width="800" height="1440"></canvas>
<div class="panel"><b>Chiến binh tuyết: test khớp</b><div style="margin-top:8px">
<button id="sway">Lắc lư</button><button id="piv">Pivot</button><button id="reset">Reset</button></div>
<div id="sl"></div></div>
<script>
const RIG = __RIG__;
const cv = document.getElementById('cv'), ctx = cv.getContext('2d'), S = RIG.pngScale;
const P = Object.fromEntries(RIG.parts.map(p => [p.id, {...p, angle: 0, img: new Image()}]));
let n = 0, sway = false, piv = false, t0 = 0;
for (const p of Object.values(P)) { p.img.onload = () => { if (++n === RIG.parts.length) draw(); }; p.img.src = p.png; }
function M(p) {
  let m = p.parent ? M(P[p.parent]).translate(p.origin[0] - P[p.parent].origin[0], p.origin[1] - P[p.parent].origin[1])
                   : new DOMMatrix().translate(p.origin[0], p.origin[1]);
  return m.translate(p.pivot[0], p.pivot[1]).rotate(p.angle).translate(-p.pivot[0], -p.pivot[1]);
}
function draw() {
  ctx.setTransform(1,0,0,1,0,0); ctx.clearRect(0,0,cv.width,cv.height);
  const base = new DOMMatrix().scale(S, S);
  for (const p of Object.values(P).sort((a,b) => a.z - b.z)) { ctx.setTransform(base.multiply(M(p))); ctx.drawImage(p.img, 0, 0, p.size[0], p.size[1]); }
  if (piv) for (const p of Object.values(P)) { const q = base.multiply(M(p)).transformPoint(new DOMPoint(...p.pivot));
    ctx.setTransform(1,0,0,1,0,0); ctx.strokeStyle = '#e11d48'; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(q.x, q.y, 9, 0, 7); ctx.stroke(); }
}
const sl = document.getElementById('sl');
for (const p of Object.values(P)) { if (!p.limitDeg) continue;
  const l = document.createElement('label');
  l.innerHTML = `<span>${p.id}</span><input type=range min=${p.limitDeg[0]} max=${p.limitDeg[1]} value=0><span>0°</span>`;
  const [, i, v] = l.children; i.oninput = () => { p.angle = +i.value; v.textContent = i.value + '°'; draw(); }; p.ui = [i, v]; sl.appendChild(l); }
const set = (id, a) => { const p = P[id]; p.angle = Math.max(p.limitDeg[0], Math.min(p.limitDeg[1], a)); p.ui[0].value = p.angle; p.ui[1].textContent = Math.round(p.angle) + '°'; };
function loop() { if (!sway) return; const t = (performance.now() - t0) / 1000;
  set('head', 12*Math.sin(t*2)); set('braid', -14*Math.sin(t*2-0.6)); set('upper_arm_L', -60+45*Math.sin(t*3));
  set('forearm_L', -50+35*Math.sin(t*3+1)); set('upper_arm_R', 40-30*Math.sin(t*3+2)); set('forearm_R', 40-30*Math.sin(t*3+3));
  set('spear', 10*Math.sin(t*3+2.5)); set('cape', 10*Math.sin(t*2-1)); set('skirt', 6*Math.sin(t*3-0.8));
  set('thigh_L', 15*Math.sin(t*3)); set('shin_L', 25+25*Math.sin(t*3+1)); set('thigh_R', 15*Math.sin(t*3+Math.PI)); set('shin_R', -25-25*Math.sin(t*3+1));
  draw(); requestAnimationFrame(loop); }
document.getElementById('sway').onclick = e => { sway = !sway; e.target.classList.toggle('on', sway); if (sway) { t0 = performance.now(); loop(); } };
document.getElementById('piv').onclick = e => { piv = !piv; e.target.classList.toggle('on', piv); draw(); };
document.getElementById('reset').onclick = () => { for (const p of Object.values(P)) if (p.limitDeg) set(p.id, 0); draw(); };
window.__pose = o => { for (const k in o) set(k, o[k]); draw(); };
</script></body></html>"""

if __name__ == "__main__":
    rig = build(OUT, "chien_binh_tuyet", PARTS, STRINGS, COLLIDERS)
    open(os.path.join(OUT, "preview.html"), "w").write(PREVIEW.replace("__RIG__", json.dumps(rig)))
    print("chien_binh_tuyet done")
