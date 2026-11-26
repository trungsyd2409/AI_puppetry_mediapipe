"""Chu Teu (Vietnamese water puppet), cut into 10 rig parts."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from puppet_lib import *  # noqa

OUT = os.path.dirname(os.path.abspath(__file__))

NECK = (200, 188)
SHO_L, ELB_L, WRI_L = (141, 214), (104, 298), (89, 376)
HIP_L, KNE_L, ANK_L = (172, 392), (163, 510), (159, 622)


def foot(ankle):
    x, y = ankle
    d = (f"M{x+13},{y-6} C{x+16},{y+18} {x+8},{y+30} {x-18},{y+32} "
         f"C{x-40},{y+33} {x-46},{y+20} {x-34},{y+12} "
         f"C{x-22},{y+5} {x-12},{y+2} {x-12},{y-8} Z")
    toes = "".join(
        f'<path d="M{x-40+i*7},{y+22} q2,6 6,8" fill="none" stroke="{OUTLINE}" stroke-width="1.6"/>'
        for i in range(3))
    return (f'<path d="{d}" fill="{SKIN}" stroke="{OUTLINE}" stroke-width="3.2"/>'
            f'<path d="M{x+4},{y+6} C{x+2},{y+18} {x-10},{y+24} {x-24},{y+24}" fill="none" '
            f'stroke="{GOLD_LIGHT}" stroke-width="1.4" stroke-dasharray="4 3"/>{toes}')


def draw_head():
    cx, cy = 200, 118
    neck = (f'<path d="M181,160 L181,196 Q200,204 219,196 L219,160 Z" fill="{SKIN_SHADE}" '
            f'stroke="{OUTLINE}" stroke-width="3"/>')
    ears = "".join(
        f'<ellipse cx="{x}" cy="124" rx="11" ry="17" fill="{SKIN}" stroke="{OUTLINE}" stroke-width="3"/>'
        f'<path d="M{x + (4 if x < 200 else -4)},116 q{-5 if x < 200 else 5},8 0,16" fill="none" '
        f'stroke="{SKIN_SHADE}" stroke-width="2.2"/>'
        for x in (142, 258))
    face = (f'<radialGradient id="g_face" cx="0.45" cy="0.4" r="0.65">'
            f'<stop offset="0" stop-color="{SKIN_LIGHT}"/><stop offset="0.65" stop-color="{SKIN}"/>'
            f'<stop offset="1" stop-color="{SKIN_SHADE}"/></radialGradient>'
            f'<path d="M{cx},{cy-64} C{cx+40},{cy-64} {cx+60},{cy-34} {cx+59},{cy+2} '
            f'C{cx+58},{cy+40} {cx+34},{cy+62} {cx},{cy+62} C{cx-34},{cy+62} {cx-58},{cy+40} '
            f'{cx-59},{cy+2} C{cx-60},{cy-34} {cx-40},{cy-64} {cx},{cy-64} Z" '
            f'fill="url(#g_face)" stroke="{OUTLINE}" stroke-width="3.5"/>')
    tuft = (f'<path d="M200,66 C172,62 170,34 196,22 C201,19 206,15 208,10 '
            f'C214,22 230,36 224,52 C220,62 210,67 200,66 Z" fill="{INK}" '
            f'stroke="{OUTLINE}" stroke-width="2.5"/>'
            f'<path d="M190,58 C186,46 194,34 204,26 M200,60 C198,48 204,38 212,30 '
            f'M210,58 C212,48 216,42 220,40" fill="none" stroke="{GOLD}" stroke-width="1.5" '
            f'stroke-linecap="round"/>')
    brows = (f'<path d="M163,96 Q176,86 190,94" fill="none" stroke="{INK}" stroke-width="4.5" '
             f'stroke-linecap="round"/>'
             f'<path d="M210,94 Q224,86 237,96" fill="none" stroke="{INK}" stroke-width="4.5" '
             f'stroke-linecap="round"/>')
    eyes = (f'<path d="M165,113 Q177,101 189,113" fill="none" stroke="{INK}" stroke-width="4" '
            f'stroke-linecap="round"/>'
            f'<path d="M211,113 Q223,101 235,113" fill="none" stroke="{INK}" stroke-width="4" '
            f'stroke-linecap="round"/>'
            f'<path d="M163,118 q-4,4 -9,3 M237,118 q4,4 9,3" fill="none" stroke="{SKIN_SHADE}" '
            f'stroke-width="2" stroke-linecap="round"/>')
    cheeks = (f'<ellipse cx="160" cy="136" rx="12" ry="8" fill="{RED}" opacity="0.45"/>'
              f'<ellipse cx="240" cy="136" rx="12" ry="8" fill="{RED}" opacity="0.45"/>')
    nose = (f'<path d="M194,121 Q190,132 200,133 Q210,132 206,121" fill="{SKIN_SHADE}" '
            f'opacity="0.7" stroke="{OUTLINE}" stroke-width="2"/>')
    mouth = (f'<path d="M168,143 Q200,186 232,143 Q200,154 168,143 Z" fill="{RED_DARK}" '
             f'stroke="{OUTLINE}" stroke-width="3" stroke-linejoin="round"/>'
             f'<path d="M176,148 Q200,155 224,148 L222,153 Q200,159 178,153 Z" fill="#FFF4DE"/>'
             f'<ellipse cx="200" cy="168" rx="13" ry="6" fill="{RED}"/>'
             f'<path d="M164,140 q3,4 7,4 M236,140 q-3,4 -7,4" fill="none" stroke="{OUTLINE}" '
             f'stroke-width="2.4" stroke-linecap="round"/>')
    chin = f'<path d="M188,176 Q200,182 212,176" fill="none" stroke="{SKIN_SHADE}" stroke-width="2"/>'
    return (neck + ears + face + tuft + brows + eyes + cheeks + nose + mouth + chin
            + cloud(200, 74, 0.8, 0, GOLD, 1.6) + rivet(*NECK))


def draw_torso():
    body = ("M152,190 C170,183 230,183 248,190 C268,196 276,208 272,228 "
            "C290,262 294,320 272,356 L128,356 C106,320 110,262 128,228 "
            "C124,208 132,196 152,190 Z")
    grad = (f'<radialGradient id="g_body" cx="0.5" cy="0.62" r="0.6">'
            f'<stop offset="0" stop-color="{SKIN_LIGHT}"/><stop offset="0.55" stop-color="{SKIN}"/>'
            f'<stop offset="1" stop-color="{SKIN_SHADE}"/></radialGradient>')
    chest = (f'<path d="M160,236 Q176,250 194,240 M206,240 Q224,250 240,236" fill="none" '
             f'stroke="{SKIN_SHADE}" stroke-width="2.6" stroke-linecap="round"/>'
             f'<circle cx="176" cy="246" r="2.6" fill="{SKIN_SHADE}"/>'
             f'<circle cx="224" cy="246" r="2.6" fill="{SKIN_SHADE}"/>')
    belly = (f'<path d="M140,300 Q200,256 260,300" fill="none" stroke="{SKIN_SHADE}" '
             f'stroke-width="2" opacity="0.6"/>'
             f'<path d="M194,318 q6,8 12,0" fill="none" stroke="{OUTLINE}" stroke-width="2.6" '
             f'stroke-linecap="round"/><circle cx="200" cy="318" r="1.8" fill="{OUTLINE}"/>')
    necklace = (f'<path d="M168,194 Q200,226 232,194" fill="none" stroke="{GOLD}" stroke-width="2.4"/>'
                f'<path d="M168,194 Q200,226 232,194" fill="none" stroke="{OUTLINE}" '
                f'stroke-width="0.8" stroke-dasharray="1 3"/>'
                f'<path d="M200,212 l8,10 l-8,10 l-8,-10 Z" fill="{RED}" stroke="{OUTLINE}" stroke-width="2"/>'
                f'<circle cx="200" cy="222" r="2.4" fill="{GOLD_LIGHT}"/>')
    shorts = (f'<path d="M126,352 L274,352 C280,376 278,398 266,414 L246,416 Q200,398 154,416 '
              f'L134,414 C122,398 120,376 126,352 Z" fill="{RED}" stroke="{OUTLINE}" stroke-width="3.5"/>'
              f'<path d="M150,404 Q200,388 250,404" fill="none" stroke="{GOLD_LIGHT}" '
              f'stroke-width="1.4" stroke-dasharray="4 3"/>')
    waist = (f'<path d="M124,346 Q200,336 276,346 L278,370 Q200,360 122,370 Z" fill="{GOLD}" '
             f'stroke="{OUTLINE}" stroke-width="3"/>'
             + "".join(f'<circle cx="{x}" cy="{357 - 0.0012*(x-200)**2:.1f}" r="2.6" fill="{RED_DARK}"/>'
                       for x in range(136, 268, 12)))
    flap = (f'<path d="M178,362 L222,362 L230,454 Q200,466 170,454 Z" fill="{RED_DARK}" '
            f'stroke="{OUTLINE}" stroke-width="3.2"/>'
            f'<path d="M182,370 L218,370 L224,448 Q200,457 176,448 Z" fill="none" '
            f'stroke="{GOLD}" stroke-width="1.6"/>'
            + cloud(200, 396, 1.0, 0) + cloud(200, 426, 0.85, 180)
            + f'<path d="M180,454 l4,10 M190,458 l2,10 M200,459 l0,10 M210,458 l-2,10 M220,454 l-4,10" '
              f'stroke="{GOLD}" stroke-width="2" stroke-linecap="round"/>')
    knot = (f'<ellipse cx="184" cy="358" rx="13" ry="8" fill="{RED}" stroke="{OUTLINE}" stroke-width="2.5"/>'
            f'<ellipse cx="216" cy="358" rx="13" ry="8" fill="{RED}" stroke="{OUTLINE}" stroke-width="2.5"/>'
            f'<circle cx="200" cy="358" r="7" fill="{GOLD}" stroke="{OUTLINE}" stroke-width="2.5"/>')
    side_cloud = cloud(150, 290, 0.9, -20, SKIN_SHADE, 1.6) + cloud(250, 290, 0.9, 200, SKIN_SHADE, 1.6)
    return (grad + f'<path d="{body}" fill="url(#g_body)" stroke="{OUTLINE}" stroke-width="3.5"/>'
            + chest + belly + side_cloud + necklace + shorts + waist + flap + knot)


def draw_upper_arm():
    pat = band(SHO_L, ELB_L, 0.28, 18, 8) + dots(SHO_L, ELB_L, 3, 1.8, 0.5, 0.78)
    return limb("ua", SHO_L, ELB_L, 21, 16, pattern=pat) + rivet(*SHO_L)


def draw_forearm():
    a = angle_deg(ELB_L, WRI_L)
    pat = band(ELB_L, WRI_L, 0.86, 13, 9) + band(ELB_L, WRI_L, 0.74, 13, 5)
    return (limb("fa", ELB_L, WRI_L, 16, 12, pattern=pat)
            + hand((WRI_L[0] + math.cos(math.radians(a)) * 12, WRI_L[1] + math.sin(math.radians(a)) * 12),
                   a, thumb_side=-1)
            + rivet(*ELB_L))


def draw_thigh():
    return limb("th", HIP_L, KNE_L, 27, 19, pattern=dots(HIP_L, KNE_L, 4, 2.0, 0.35, 0.8)) + rivet(*HIP_L)


def draw_shin():
    pat = band(KNE_L, ANK_L, 0.88, 14, 8) + dots(KNE_L, ANK_L, 3, 1.7, 0.3, 0.65)
    return foot(ANK_L) + limb("sh", KNE_L, ANK_L, 19, 14, pattern=pat) + rivet(*KNE_L)


PARTS = [
    ("torso", None, 3, draw_torso(), (200, 300), None),
    ("head", "torso", 6, draw_head(), NECK, (-35, 35)),
    ("thigh_L", "torso", 1, draw_thigh(), HIP_L, (-70, 60)),
    ("shin_L", "thigh_L", 0, draw_shin(), KNE_L, (-10, 120)),
    ("thigh_R", "torso", 1, f'<g {MIRROR}>{draw_thigh()}</g>', mx(HIP_L), (-60, 70)),
    ("shin_R", "thigh_R", 0, f'<g {MIRROR}>{draw_shin()}</g>', mx(KNE_L), (-120, 10)),
    ("upper_arm_L", "torso", 4, draw_upper_arm(), SHO_L, (-150, 60)),
    ("forearm_L", "upper_arm_L", 5, draw_forearm(), ELB_L, (-140, 10)),
    ("upper_arm_R", "torso", 4, f'<g {MIRROR}>{draw_upper_arm()}</g>', mx(SHO_L), (-60, 150)),
    ("forearm_R", "upper_arm_R", 5, f'<g {MIRROR}>{draw_forearm()}</g>', mx(ELB_L), (-10, 140)),
]

STRINGS = [
    ("head", "head", (200, 14), "middle", 12),
    ("hand_L", "forearm_L", lerp(ELB_L, WRI_L, 1.28), "index", 8),
    ("hand_R", "forearm_R", mx(lerp(ELB_L, WRI_L, 1.28)), "ring", 16),
    ("knee_L", "shin_L", KNE_L, "thumb", 4),
    ("knee_R", "shin_R", mx(KNE_L), "pinky", 20),
]

if __name__ == "__main__":
    build(OUT, "teu", PARTS, STRINGS)
    print("teu done")
