"""Ve binh Streltsy: original female guard in the style of the Tsardom's Streltsy regiments.

Crimson kaftan with gold frogging, fur-trimmed cap, gold sash, yellow boots, curved saber
in the left hand (viewer's left). Same skeleton and strings as the other puppets, plus:
  braid   chestnut plait over the right shoulder (child of head)
  skirt   long kaftan skirt split at the front (child of torso)
  saber   curved sword in the left hand (child of forearm_L)
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from puppet_lib import *  # noqa

OUT = os.path.dirname(os.path.abspath(__file__))

CRIMSON = "#A31E2B"
CRIMSON_D = "#6E1220"
CRIMSON_L = "#C9404A"
GOLD_C = "#E2B44A"
GOLD_CL = "#F6DA8A"
GOLD_CD = "#A8781A"
GREEN_D = "#2E4A3A"
BOOT = "#D9A62E"
BOOT_D = "#A8781A"
FUR = "#5A3A28"
FUR_L = "#7E5539"
HAIR_C = "#6B3A24"
HAIR_CS = "#4A2616"
SKIN_W = "#F4D3BC"
SKIN_WL = "#FBE6D6"
SKIN_WS = "#D9A98F"
SILVER = "#C9D1DD"
SILVER_L = "#EEF2F7"
SILVER_D = "#8793A8"

NECK = (200, 190)
SHO_L, ELB_L, WRI_L = (160, 224), (130, 304), (116, 386)
HIP_L, KNE_L, ANK_L = (184, 372), (180, 500), (178, 622)
WAIST = (200, 334)
BRAID_PIVOT = (226, 160)
HAND_L = (WRI_L[0] - 1, WRI_L[1] + 10)
GRIP = (HAND_L[0], HAND_L[1] - 2)


def grad(gid, c0, c1, c2=None, horizontal=True):
    x2, y2 = ("1", "0") if horizontal else ("0", "1")
    stops = f'<stop offset="0" stop-color="{c0}"/><stop offset="{0.5 if c2 else 1}" stop-color="{c1}"/>'
    if c2:
        stops += f'<stop offset="1" stop-color="{c2}"/>'
    return f'<linearGradient id="{gid}" x1="0" y1="0" x2="{x2}" y2="{y2}">{stops}</linearGradient>'


def gold_rivet(x, y, r=4.5):
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{GOLD_C}" stroke="{OUTLINE}" stroke-width="2"/>'
            f'<circle cx="{x}" cy="{y}" r="{r * 0.38:.2f}" fill="{CRIMSON_D}"/>')


def fur_band(x0, x1, y0, y1):
    """Sable fur: soft scalloped edges and short strokes."""
    top = " ".join(f"Q{x + 5},{y0 - (5 if (x // 10) % 2 else 1)} {x + 10},{y0}" for x in range(x0, x1, 10))
    bot = " ".join(f"Q{x - 5},{y1 + (5 if (x // 10) % 2 else 1)} {x - 10},{y1}" for x in range(x1, x0, -10))
    strokes = "".join(f'<path d="M{x},{y0 + 4} q2,{(y1 - y0) * 0.4:.1f} 0,{(y1 - y0) - 8}" fill="none" stroke="{FUR_L}" '
                      f'stroke-width="1.6" stroke-linecap="round"/>' for x in range(x0 + 5, x1, 7))
    return (f'<path d="M{x0},{y0} {top} L{x1},{y1} {bot} Z" fill="{FUR}" stroke="{OUTLINE}" stroke-width="2.4"/>'
            + strokes)


# ---------------------------------------------------------------- head
def draw_head():
    hair_back = (f'<path d="M158,120 C146,156 148,196 156,226 C164,232 172,230 178,222 C172,196 172,160 178,128 Z '
                 f'M242,120 C254,156 252,196 244,226 C236,232 228,230 222,222 C228,196 228,160 222,128 Z" '
                 f'fill="{HAIR_C}" stroke="{OUTLINE}" stroke-width="2.4"/>'
                 f'<path d="M162,150 C158,176 160,200 164,218 M238,150 C242,176 240,200 236,218" fill="none" '
                 f'stroke="{HAIR_CS}" stroke-width="1.6"/>')
    neck = (f'<path d="M189,166 L189,198 Q200,204 211,198 L211,166 Z" fill="{SKIN_WS}" '
            f'stroke="{OUTLINE}" stroke-width="2.6"/>')
    face = (f'<radialGradient id="g_face_s" cx="0.45" cy="0.42" r="0.7">'
            f'<stop offset="0" stop-color="{SKIN_WL}"/><stop offset="0.7" stop-color="{SKIN_W}"/>'
            f'<stop offset="1" stop-color="{SKIN_WS}"/></radialGradient>'
            f'<path d="M200,98 C224,98 234,118 233,140 C232,162 218,180 200,184 '
            f'C182,180 168,162 167,140 C166,118 176,98 200,98 Z" fill="url(#g_face_s)" '
            f'stroke="{OUTLINE}" stroke-width="3"/>')
    bangs = (f'<path d="M168,124 C170,108 188,100 200,104 C212,100 230,108 232,124 '
             f'C224,114 212,112 202,118 L200,112 L198,118 C188,112 176,114 168,124 Z" fill="{HAIR_C}" '
             f'stroke="{OUTLINE}" stroke-width="2"/>')
    brows = (f'<path d="M175,128 L193,125 M207,125 L225,128" fill="none" stroke="{HAIR_CS}" '
             f'stroke-width="3" stroke-linecap="round"/>')
    eyes = ""
    for ex in (185, 215):
        eyes += (f'<path d="M{ex-10},142 Q{ex},134 {ex+10},142 Q{ex},147 {ex-10},142 Z" fill="#FFFFFF"/>'
                 f'<circle cx="{ex}" cy="141" r="4.5" fill="#5C7F3E"/>'
                 f'<circle cx="{ex}" cy="141" r="2.1" fill="#1E2A14"/>'
                 f'<circle cx="{ex + 1.5}" cy="139.5" r="1.2" fill="#FFFFFF"/>'
                 f'<path d="M{ex-10},142 Q{ex},132 {ex+10},142" fill="none" stroke="{INK}" stroke-width="2.6" '
                 f'stroke-linecap="round"/>')
    face_detail = (f'<path d="M199,149 q-3,9 1,11 q3,1 5,-1" fill="none" stroke="{SKIN_WS}" stroke-width="1.8" '
                   f'stroke-linecap="round"/>'
                   f'<path d="M191,167 Q200,171 209,167 Q200,174 191,167 Z" fill="#B23A44" stroke="#7E2430" '
                   f'stroke-width="1.2"/>'
                   f'<ellipse cx="177" cy="157" rx="8" ry="4.5" fill="#E58C8C" opacity="0.4"/>'
                   f'<ellipse cx="223" cy="157" rx="8" ry="4.5" fill="#E58C8C" opacity="0.4"/>')
    earrings = (f'<path d="M168,166 l0,6" stroke="{GOLD_C}" stroke-width="1.6"/>'
                f'<circle cx="168" cy="176" r="3.6" fill="{GOLD_C}" stroke="{OUTLINE}" stroke-width="1.2"/>'
                f'<path d="M232,166 l0,6" stroke="{GOLD_C}" stroke-width="1.6"/>'
                f'<circle cx="232" cy="176" r="3.6" fill="{GOLD_C}" stroke="{OUTLINE}" stroke-width="1.2"/>')
    # Streltsy cap: crimson crown, sable fur band, gold finial
    hat = (grad("g_cap", CRIMSON_D, CRIMSON_L, CRIMSON_D)
           + f'<path d="M164,104 C162,72 176,52 200,50 C224,52 238,72 236,104 Z" fill="url(#g_cap)" '
             f'stroke="{OUTLINE}" stroke-width="3"/>'
           + f'<path d="M200,52 L200,100 M182,58 C176,72 174,88 174,102 M218,58 C224,72 226,88 226,102" '
             f'fill="none" stroke="{CRIMSON_D}" stroke-width="1.6"/>'
           + f'<circle cx="200" cy="48" r="6" fill="{GOLD_C}" stroke="{OUTLINE}" stroke-width="2"/>'
           + f'<path d="M200,42 l0,-8" stroke="{GOLD_C}" stroke-width="3" stroke-linecap="round"/>'
           + fur_band(154, 246, 100, 124))
    return (hair_back + neck + face + bangs + brows + eyes + face_detail + earrings + hat
            + gold_rivet(*NECK, 4))


def draw_braid():
    segs = ""
    y, i = 168, 0
    while y < 330:
        x = 230 + (y - 168) * 0.06
        tilt = -28 if i % 2 else 28
        segs += (f'<ellipse cx="{x:.1f}" cy="{y}" rx="12" ry="9" transform="rotate({tilt} {x:.1f} {y})" '
                 f'fill="{HAIR_C}" stroke="{OUTLINE}" stroke-width="2"/>'
                 f'<path d="M{x - 6:.1f},{y - 2} q6,-4 12,0" fill="none" stroke="{HAIR_CS}" stroke-width="1.4" '
                 f'transform="rotate({tilt} {x:.1f} {y})"/>')
        y += 13
        i += 1
    tie = (f'<rect x="228" y="328" width="22" height="10" rx="3" fill="{CRIMSON}" stroke="{OUTLINE}" stroke-width="2"/>'
           f'<path d="M232,338 C228,352 226,362 222,370 M246,338 C248,350 252,360 256,368" fill="none" '
           f'stroke="{CRIMSON}" stroke-width="4" stroke-linecap="round"/>'
           f'<path d="M232,338 C228,354 232,368 240,378 C246,368 248,354 248,338 Z" fill="{HAIR_C}" '
           f'stroke="{OUTLINE}" stroke-width="2"/>')
    return segs + tie + gold_rivet(*BRAID_PIVOT, 3.5)


# ---------------------------------------------------------------- body
def draw_torso():
    body = ("M168,206 C186,199 214,199 232,206 C246,211 252,223 250,237 C248,270 238,300 228,338 "
            "L172,338 C162,300 152,270 150,237 C148,223 154,211 168,206 Z")
    collar = (f'<path d="M184,176 L216,176 L218,206 Q200,212 182,206 Z" fill="{CRIMSON}" stroke="{OUTLINE}" '
              f'stroke-width="2.6"/>'
              f'<path d="M184,182 L216,182 M183,200 Q200,205 217,200" fill="none" stroke="{GOLD_C}" stroke-width="2"/>')
    placket = f'<path d="M200,206 L200,330" stroke="{GOLD_CD}" stroke-width="2"/>'
    frogging = ""
    for i, y in enumerate(range(222, 312, 17)):
        half = 24 - i * 2
        frogging += (f'<path d="M{200 - half},{y} L{200 + half},{y}" stroke="{GOLD_C}" stroke-width="3.2" '
                     f'stroke-linecap="round"/>'
                     f'<path d="M{200 - half},{y} l-5,-4 M{200 - half},{y} l-5,4 M{200 + half},{y} l5,-4 M{200 + half},{y} l5,4" '
                     f'stroke="{GOLD_C}" stroke-width="2" stroke-linecap="round"/>'
                     f'<circle cx="{200 - half}" cy="{y}" r="3.2" fill="{GOLD_CL}" stroke="{OUTLINE}" stroke-width="1.2"/>'
                     f'<circle cx="{200 + half}" cy="{y}" r="3.2" fill="{GOLD_CL}" stroke="{OUTLINE}" stroke-width="1.2"/>')
    sash = (f'<path d="M166,318 Q200,328 234,318 L236,344 Q200,354 164,344 Z" fill="{GOLD_C}" '
            f'stroke="{OUTLINE}" stroke-width="2.6"/>'
            f'<path d="M168,331 Q200,340 232,331" fill="none" stroke="{GOLD_CD}" stroke-width="1.4" stroke-dasharray="4 3"/>'
            f'<path d="M226,340 C232,354 230,368 236,382 L244,380 C240,366 240,352 236,338 Z" fill="{GOLD_C}" '
            f'stroke="{OUTLINE}" stroke-width="2"/>'
            f'<path d="M236,382 l-2,8 M240,381 l0,9 M244,380 l2,8" stroke="{GOLD_CD}" stroke-width="2" stroke-linecap="round"/>')
    return (grad("g_kaftan", CRIMSON_D, CRIMSON_L, CRIMSON_D)
            + f'<path d="{body}" fill="url(#g_kaftan)" stroke="{OUTLINE}" stroke-width="3.2"/>'
            + placket + frogging + sash + collar)


def draw_skirt():
    left = "M174,336 C164,410 148,500 136,566 Q166,576 196,578 L198,420 L200,338 Z"
    right = "M226,336 C236,410 252,500 264,566 Q234,576 204,578 L202,420 L200,338 Z"
    trousers = (f'<path d="M184,420 L216,420 L222,580 L178,580 Z" fill="{GREEN_D}" stroke="{OUTLINE}" stroke-width="2"/>')
    hem = (f'<path d="M136,566 Q166,576 196,578 M204,578 Q234,576 264,566" fill="none" stroke="{GOLD_C}" stroke-width="5"/>'
           f'<path d="M136,566 Q166,576 196,578 M204,578 Q234,576 264,566" fill="none" stroke="{GOLD_CD}" '
           f'stroke-width="1.4" stroke-dasharray="3 4"/>'
           f'<path d="M198,424 L196,578 M202,424 L204,578" fill="none" stroke="{GOLD_C}" stroke-width="3"/>')
    pleats = (f'<path d="M180,350 C172,420 164,500 158,568 M220,350 C228,420 236,500 242,568" fill="none" '
              f'stroke="{CRIMSON_D}" stroke-width="1.8" opacity="0.8"/>')
    return (grad("g_kskirt", CRIMSON_D, CRIMSON, CRIMSON_L)
            + trousers
            + f'<path d="{left}" fill="url(#g_kskirt)" stroke="{OUTLINE}" stroke-width="2.8"/>'
            + f'<path d="{right}" fill="url(#g_kskirt)" stroke="{OUTLINE}" stroke-width="2.8"/>'
            + pleats + hem + gold_rivet(*WAIST, 4))


# ---------------------------------------------------------------- limbs
def draw_upper_arm():
    return (limb("ua_s", SHO_L, ELB_L, 14, 11.5, fill=CRIMSON, shade=CRIMSON_D, stitch=GOLD_CL,
                 pattern=band(SHO_L, ELB_L, 0.2, 13, 7, GOLD_C, CRIMSON_D))
            + gold_rivet(*SHO_L, 4))


def draw_forearm():
    a = angle_deg(ELB_L, WRI_L)
    wrist = (WRI_L[0] + math.cos(math.radians(a)) * 9, WRI_L[1] + math.sin(math.radians(a)) * 9)
    cuff = (f'<path d="{capsule(lerp(ELB_L, WRI_L, 0.72), lerp(ELB_L, WRI_L, 1.0), 13, 12.5)}" fill="{GOLD_C}" '
            f'stroke="{OUTLINE}" stroke-width="2.2"/>'
            f'<path d="{capsule(lerp(ELB_L, WRI_L, 0.76), lerp(ELB_L, WRI_L, 0.96), 8, 7.5)}" fill="none" '
            f'stroke="{GOLD_CD}" stroke-width="1.4" stroke-dasharray="3 3"/>')
    return (hand(wrist, a, thumb_side=-1, s=0.72, fill=SKIN_W, light=SKIN_WL)
            + limb("fa_s", ELB_L, WRI_L, 11.5, 10, fill=CRIMSON, shade=CRIMSON_D, stitch=GOLD_CL)
            + cuff + gold_rivet(*ELB_L, 4))


def boot_foot(ankle):
    x, y = ankle
    d = (f"M{x + 12},{y - 6} C{x + 14},{y + 18} {x + 6},{y + 30} {x - 16},{y + 32} "
         f"C{x - 30},{y + 33} {x - 40},{y + 26} {x - 46},{y + 14} C{x - 38},{y + 18} {x - 30},{y + 14} {x - 12},{y - 6} Z")
    return (f'<path d="{d}" fill="{BOOT}" stroke="{OUTLINE}" stroke-width="2.8"/>'
            f'<path d="M{x + 8},{y + 18} C{x - 4},{y + 26} {x - 22},{y + 26} {x - 36},{y + 18}" fill="none" '
            f'stroke="{BOOT_D}" stroke-width="1.8"/>')


def draw_thigh():
    return (limb("th_s", HIP_L, KNE_L, 18, 15, fill=GREEN_D, shade="#1F3328", stitch="#5E7A68")
            + gold_rivet(*HIP_L, 4))


def draw_shin():
    top = lerp(KNE_L, ANK_L, 0.3)
    boot = (f'<path d="{capsule(top, ANK_L, 16, 14)}" fill="{BOOT}" stroke="{OUTLINE}" stroke-width="2.6"/>'
            f'<path d="{capsule(top, ANK_L, 9, 8)}" fill="none" stroke="{BOOT_D}" stroke-width="1.4"/>'
            + band(KNE_L, ANK_L, 0.3, 16, 8, GOLD_C, CRIMSON))
    return (boot_foot(ANK_L)
            + limb("sh_s", KNE_L, ANK_L, 15, 13, fill=GREEN_D, shade="#1F3328", stitch="#5E7A68")
            + boot + gold_rivet(*KNE_L, 4))


# ---------------------------------------------------------------- saber (left hand)
def draw_saber():
    gx, gy = GRIP
    # curved blade rising from the guard, bending outward like a shashka
    tip = (gx - 46, gy - 290)
    c1, c2 = (gx - 2, gy - 120), (gx - 18, gy - 230)
    back = f"M{gx - 5},{gy - 30} C{c1[0] - 6},{c1[1]} {c2[0] - 8},{c2[1]} {tip[0]},{tip[1]}"
    edge = f"C{c2[0] + 4},{c2[1] + 10} {c1[0] + 8},{c1[1] + 8} {gx + 6},{gy - 30} Z"
    blade = (grad("g_saber", SILVER_D, SILVER_L, SILVER_D)
             + f'<path d="{back} {edge}" fill="url(#g_saber)" stroke="{OUTLINE}" stroke-width="2.2" stroke-linejoin="round"/>'
             + f'<path d="M{gx},{gy - 36} C{c1[0] + 1},{c1[1]} {c2[0] - 3},{c2[1] + 4} {tip[0] + 6},{tip[1] + 14}" '
               f'fill="none" stroke="{SILVER_D}" stroke-width="1.3"/>')
    guard = (f'<path d="M{gx - 16},{gy - 30} Q{gx},{gy - 38} {gx + 16},{gy - 30} L{gx + 14},{gy - 24} '
             f'Q{gx},{gy - 30} {gx - 14},{gy - 24} Z" fill="{GOLD_C}" stroke="{OUTLINE}" stroke-width="2"/>')
    grip = (f'<rect x="{gx - 5}" y="{gy - 26}" width="10" height="44" rx="4" fill="{CRIMSON_D}" '
            f'stroke="{OUTLINE}" stroke-width="2"/>'
            + "".join(f'<path d="M{gx - 5},{y} L{gx + 5},{y + 5}" stroke="{GOLD_C}" stroke-width="1.6"/>'
                      for y in range(gy - 22, gy + 14, 6))
            + f'<circle cx="{gx}" cy="{gy + 22}" r="6.5" fill="{GOLD_C}" stroke="{OUTLINE}" stroke-width="2"/>')
    tassel = (f'<path d="M{gx},{gy + 28} C{gx + 4},{gy + 42} {gx - 4},{gy + 54} {gx + 2},{gy + 66}" fill="none" '
              f'stroke="{CRIMSON}" stroke-width="3"/>'
              f'<path d="M{gx - 5},{gy + 64} L{gx + 9},{gy + 64} L{gx + 12},{gy + 86} L{gx - 8},{gy + 86} Z" '
              f'fill="{CRIMSON}" stroke="{OUTLINE}" stroke-width="1.8"/>'
              + "".join(f'<path d="M{gx - 6 + i * 4},{gy + 70} l0,15" stroke="{CRIMSON_D}" stroke-width="1.2"/>'
                        for i in range(5)))
    return tassel + blade + guard + grip + gold_rivet(*GRIP, 3.2), tip


SABER_SVG, SABER_TIP = draw_saber()

PARTS = [
    ("torso", None, 4, draw_torso(), (200, 280), None),
    ("head", "torso", 11, draw_head(), NECK, (-30, 30)),
    ("braid", "head", 7, draw_braid(), BRAID_PIVOT, (-25, 25)),
    ("skirt", "torso", 5, draw_skirt(), WAIST, (-12, 12)),
    ("thigh_L", "torso", 2, draw_thigh(), HIP_L, (-70, 60)),
    ("shin_L", "thigh_L", 1, draw_shin(), KNE_L, (-10, 120)),
    ("thigh_R", "torso", 2, f'<g {MIRROR}>{draw_thigh()}</g>', mx(HIP_L), (-60, 70)),
    ("shin_R", "thigh_R", 1, f'<g {MIRROR}>{draw_shin()}</g>', mx(KNE_L), (-120, 10)),
    ("upper_arm_L", "torso", 8, draw_upper_arm(), SHO_L, (-150, 60)),
    ("forearm_L", "upper_arm_L", 10, draw_forearm(), ELB_L, (-140, 10)),
    ("upper_arm_R", "torso", 8, f'<g {MIRROR}>{draw_upper_arm()}</g>', mx(SHO_L), (-60, 150)),
    ("forearm_R", "upper_arm_R", 9, f'<g {MIRROR}>{draw_forearm()}</g>', mx(ELB_L), (-10, 140)),
    ("saber", "forearm_L", 6, SABER_SVG, GRIP, (-20, 20)),
]

STRINGS = [
    ("head", "head", (200, 44), "middle", 12),
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
FOOT_L = ((ANK_L[0] + 4, ANK_L[1] + 20), (ANK_L[0] - 40, ANK_L[1] + 22))
ARM_U = [capsule_shape(SHO_L, ELB_L, 12)]
ARM_F = [capsule_shape(ELB_L, HAND_TIP_L, 10)]
LEG_U = [capsule_shape(HIP_L, KNE_L, 16)]
LEG_S = [capsule_shape(KNE_L, ANK_L, 14), capsule_shape(*FOOT_L, 9)]
COLLIDERS = {
    "torso": {"density": 1.0, "shapes": [capsule_shape((200, 236), (200, 318), 40)]},
    "head": {"density": 0.8, "shapes": [circle((200, 142), 38), capsule_shape((168, 84), (232, 84), 30)]},
    "braid": {"density": 0.25, "shapes": [capsule_shape((230, 175), (240, 365), 12)]},
    "skirt": {"density": 0.3, "shapes": [capsule_shape((200, 390), (200, 540), 46)]},
    "saber": {"density": 0.4, "shapes": [capsule_shape((GRIP[0], GRIP[1] - 30), (GRIP[0] - 14, GRIP[1] - 180), 7),
                                          capsule_shape((GRIP[0] - 14, GRIP[1] - 180), SABER_TIP, 6)]},
    "upper_arm_L": {"density": 1.0, "shapes": ARM_U}, "upper_arm_R": {"density": 1.0, "shapes": side(ARM_U)},
    "forearm_L": {"density": 1.0, "shapes": ARM_F}, "forearm_R": {"density": 1.0, "shapes": side(ARM_F)},
    "thigh_L": {"density": 1.0, "shapes": LEG_U}, "thigh_R": {"density": 1.0, "shapes": side(LEG_U)},
    "shin_L": {"density": 1.0, "shapes": LEG_S}, "shin_R": {"density": 1.0, "shapes": side(LEG_S)},
}

if __name__ == "__main__":
    rig = build(OUT, "ve_binh_streltsy", PARTS, STRINGS, COLLIDERS)
    # reuse the stand-alone rig preview page of the winter warrior
    src = open(os.path.join(os.path.dirname(OUT), "chien_binh_tuyet", "gen_chien_binh_tuyet.py")).read()
    page = src.split('PREVIEW = """', 1)[1].split('"""', 1)[0]
    page = page.replace("Chien binh tuyet rig", "Ve binh Streltsy rig").replace("Chiến binh tuyết: test khớp", "Vệ binh Streltsy: test khớp")
    page = page.replace("set('spear', 10*Math.sin(t*3+2.5)); set('cape', 10*Math.sin(t*2-1));", "set('saber', 14*Math.sin(t*3+2.5));")
    open(os.path.join(OUT, "preview.html"), "w").write(page.replace("__RIG__", json.dumps(rig)))
    print("ve_binh_streltsy done")
