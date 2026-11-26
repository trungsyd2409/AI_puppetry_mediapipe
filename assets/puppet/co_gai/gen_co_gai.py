"""Co gai: female puppet in ao dai and non la, cut into 13 rig parts.

Extra parts compared with Teu (same skeleton otherwise):
  hair        long hair behind the back (child of head, swings)
  flap_front  front panel of the ao dai (child of torso, swings)
  flap_back   back panel of the ao dai  (child of torso, swings)
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from puppet_lib import *  # noqa

OUT = os.path.dirname(os.path.abspath(__file__))

SKIN_F = "#F0BA6E"
SKIN_F_LIGHT = "#FBDDA2"
SKIN_F_SHADE = "#C98A3E"
AO = "#1D6A64"         # jade ao dai
AO_LIGHT = "#3E9A8E"
AO_SHADE = "#10423E"
QUAN = "#F5ECDB"       # white silk trousers
QUAN_SHADE = "#CDBE9E"
NON = "#E9C878"        # palm-leaf hat
NON_SHADE = "#B48E45"
NON_LINE = "#8A6A2E"

NECK = (200, 232)
HAIR_PIVOT = (200, 168)
WAIST = (200, 334)
SHO_L, ELB_L, WRI_L = (161, 250), (136, 324), (122, 398)
HIP_L, KNE_L, ANK_L = (182, 352), (178, 482), (176, 612)


# ---------------------------------------------------------------- head + hat
def draw_head():
    neck = (f'<path d="M189,196 L189,238 Q200,244 211,238 L211,196 Z" fill="{SKIN_F_SHADE}" '
            f'stroke="{OUTLINE}" stroke-width="3"/>')
    hair_frame = (f'<path d="M160,150 C150,180 152,214 160,230 L172,228 C166,206 166,178 172,150 Z '
                  f'M240,150 C250,180 248,214 240,230 L228,228 C234,206 234,178 228,150 Z" '
                  f'fill="{INK}" stroke="{OUTLINE}" stroke-width="2"/>')
    face = (f'<radialGradient id="g_face_f" cx="0.45" cy="0.42" r="0.7">'
            f'<stop offset="0" stop-color="{SKIN_F_LIGHT}"/><stop offset="0.7" stop-color="{SKIN_F}"/>'
            f'<stop offset="1" stop-color="{SKIN_F_SHADE}"/></radialGradient>'
            f'<path d="M200,124 C226,124 238,146 237,170 C236,194 220,214 200,218 '
            f'C180,214 164,194 163,170 C162,146 174,124 200,124 Z" fill="url(#g_face_f)" '
            f'stroke="{OUTLINE}" stroke-width="3.2"/>')
    bangs = (f'<path d="M166,150 C172,138 190,134 200,140 C210,134 228,138 234,150 '
             f'C226,146 214,146 206,152 C204,148 196,148 194,152 C186,146 174,146 166,150 Z" '
             f'fill="{INK}"/>')
    brows = (f'<path d="M176,158 Q184,152 193,156 M207,156 Q216,152 224,158" fill="none" '
             f'stroke="{INK}" stroke-width="2.4" stroke-linecap="round"/>')
    eyes = ""
    for ex, s in ((184, -1), (216, 1)):
        eyes += (f'<path d="M{ex-10},170 Q{ex},161 {ex+10},170 Q{ex},175 {ex-10},170 Z" fill="#FFF7E6"/>'
                 f'<circle cx="{ex}" cy="168.5" r="4.6" fill="{INK}"/>'
                 f'<circle cx="{ex+1.5}" cy="167" r="1.3" fill="#FFF7E6"/>'
                 f'<path d="M{ex-10},170 Q{ex},160 {ex+10},170" fill="none" stroke="{INK}" '
                 f'stroke-width="2.6" stroke-linecap="round"/>'
                 f'<path d="M{ex + 10*s},170 l{4*s},-3" stroke="{INK}" stroke-width="2" stroke-linecap="round"/>')
    cheeks = (f'<ellipse cx="176" cy="188" rx="9" ry="5.5" fill="{RED}" opacity="0.35"/>'
              f'<ellipse cx="224" cy="188" rx="9" ry="5.5" fill="{RED}" opacity="0.35"/>')
    nose = (f'<path d="M199,176 q-3,9 1,11 q3,1 5,-1" fill="none" stroke="{SKIN_F_SHADE}" '
            f'stroke-width="2" stroke-linecap="round"/>')
    lips = (f'<path d="M190,198 Q195,193 200,196 Q205,193 210,198 Q200,206 190,198 Z" fill="{RED}" '
            f'stroke="{RED_DARK}" stroke-width="1.4"/>'
            f'<path d="M191,198 Q200,200 209,198" fill="none" stroke="{RED_DARK}" stroke-width="1.2"/>')
    earrings = (f'<circle cx="163" cy="196" r="4" fill="{GOLD}" stroke="{OUTLINE}" stroke-width="1.5"/>'
                f'<circle cx="237" cy="196" r="4" fill="{GOLD}" stroke="{OUTLINE}" stroke-width="1.5"/>')
    # non la: cone with leaf ribs, gold rim, red strap
    ribs = "".join(
        f'<path d="M200,44 L{x},{132 + 0.0009*(x-200)**2*-1 + 10:.1f}" stroke="{NON_LINE}" '
        f'stroke-width="1.2" opacity="0.7"/>'
        for x in range(104, 300, 14))
    rings = "".join(
        f'<path d="M{200 - k*108},{44 + k*90} Q200,{44 + k*90 + k*22} {200 + k*108},{44 + k*90}" '
        f'fill="none" stroke="{NON_LINE}" stroke-width="1" opacity="0.55"/>'
        for k in (0.25, 0.45, 0.65, 0.85))
    hat = (f'<linearGradient id="g_non" x1="0" y1="0" x2="1" y2="0">'
           f'<stop offset="0" stop-color="{NON_SHADE}"/><stop offset="0.45" stop-color="{NON}"/>'
           f'<stop offset="0.6" stop-color="#F6DE9C"/><stop offset="1" stop-color="{NON_SHADE}"/></linearGradient>'
           f'<clipPath id="clip_non"><path d="M200,40 L90,132 Q200,158 310,132 Z"/></clipPath>'
           f'<path d="M200,40 L90,132 Q200,158 310,132 Z" fill="url(#g_non)"/>'
           f'<g clip-path="url(#clip_non)">{ribs}{rings}</g>'
           f'<path d="M90,132 Q200,158 310,132" fill="none" stroke="{GOLD}" stroke-width="4"/>'
           f'<path d="M200,40 L90,132 Q200,158 310,132 Z" fill="none" stroke="{OUTLINE}" '
           f'stroke-width="3.2" stroke-linejoin="round"/>'
           + lotus(200, 112, 0.9, RED, OUTLINE, 1.2)
           + f'<circle cx="200" cy="42" r="3.5" fill="{GOLD}" stroke="{OUTLINE}" stroke-width="1.5"/>')
    strap = (f'<path d="M158,143 Q166,200 200,222 Q234,200 242,143" fill="none" stroke="{RED}" '
             f'stroke-width="3.2" stroke-linecap="round"/>'
             f'<path d="M158,143 Q166,200 200,222 Q234,200 242,143" fill="none" stroke="{OUTLINE}" '
             f'stroke-width="0.8" stroke-dasharray="2 4"/>')
    return (neck + hair_frame + face + bangs + brows + eyes + cheeks + nose + lips + earrings
            + strap + hat + rivet(*NECK, 4.5))


def draw_hair():
    d = ("M164,150 C146,200 150,260 152,300 C148,330 140,360 146,392 "
         "Q170,380 182,398 Q200,384 218,398 Q230,380 254,392 "
         "C260,360 252,330 248,300 C250,260 254,200 236,150 Z")
    strands = (f'<path d="M160,200 C156,260 158,320 152,380 M240,200 C244,260 242,320 248,380 '
               f'M172,220 C170,290 172,340 168,386 M228,220 C230,290 228,340 232,386" '
               f'fill="none" stroke="#3B2A1E" stroke-width="1.6" stroke-linecap="round"/>')
    clip = (f'<rect x="186" y="186" width="28" height="9" rx="3" fill="{GOLD}" '
            f'stroke="{OUTLINE}" stroke-width="1.6"/>')
    return f'<path d="{d}" fill="{INK}" stroke="{OUTLINE}" stroke-width="2.5"/>' + strands + clip


# ---------------------------------------------------------------- ao dai
def ao_grad(gid):
    return (f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="0">'
            f'<stop offset="0" stop-color="{AO_SHADE}"/><stop offset="0.35" stop-color="{AO}"/>'
            f'<stop offset="0.55" stop-color="{AO_LIGHT}"/><stop offset="1" stop-color="{AO_SHADE}"/>'
            f'</linearGradient>')


def draw_torso():
    body = ("M170,238 C186,232 214,232 230,238 C246,242 254,252 252,268 "
            "C250,292 244,308 232,328 C236,338 240,346 242,354 L158,354 "
            "C160,346 164,338 168,328 C156,308 150,292 148,268 C146,252 154,242 170,238 Z")
    collar = (f'<path d="M184,222 L216,222 L218,242 Q200,248 182,242 Z" fill="{AO}" '
              f'stroke="{OUTLINE}" stroke-width="2.6"/>'
              f'<path d="M185,227 L215,227" stroke="{GOLD}" stroke-width="2"/>')
    opening = (f'<path d="M214,242 C226,248 240,252 251,266" fill="none" stroke="{GOLD}" stroke-width="2.6"/>'
               + "".join(f'<circle cx="{x}" cy="{y}" r="2.8" fill="{GOLD_LIGHT}" stroke="{OUTLINE}" '
                         f'stroke-width="1.2"/>' for x, y in ((220, 245), (232, 250), (244, 258))))
    bust = (f'<path d="M168,286 Q182,298 196,288 M204,288 Q218,298 232,286" fill="none" '
            f'stroke="{AO_SHADE}" stroke-width="2.2" stroke-linecap="round" opacity="0.8"/>')
    deco = (lotus(178, 272, 0.75) + cloud(222, 306, 0.8, 10) + cloud(176, 318, 0.7, 190)
            + f'<path d="M166,328 Q200,338 234,328" fill="none" stroke="{GOLD_LIGHT}" '
              f'stroke-width="1.4" stroke-dasharray="4 3"/>')
    # trousers visible at the hips, between the side slits
    hips = (f'<path d="M160,330 L240,330 L246,362 Q200,372 154,362 Z" fill="{QUAN}" '
            f'stroke="{OUTLINE}" stroke-width="2.8"/>')
    return (ao_grad("g_ao_t") + hips
            + f'<path d="{body}" fill="url(#g_ao_t)" stroke="{OUTLINE}" stroke-width="3.4"/>'
            + bust + deco + opening + collar)


def draw_flap_front():
    d = "M172,326 L228,326 C234,420 240,520 242,604 Q200,622 158,604 C160,520 166,420 172,326 Z"
    inner = "M178,336 L222,336 C228,424 233,520 234,596 Q200,610 166,596 C167,520 172,424 178,336 Z"
    return (ao_grad("g_ao_f")
            + f'<path d="{d}" fill="url(#g_ao_f)" stroke="{OUTLINE}" stroke-width="3.2"/>'
            + f'<path d="{inner}" fill="none" stroke="{GOLD}" stroke-width="1.6"/>'
            + lotus(200, 540, 1.5) + lotus(200, 470, 0.9, GOLD_LIGHT)
            + cloud(186, 410, 0.8, 0) + cloud(214, 430, 0.8, 180) + cloud(200, 382, 0.7, 0)
            + "".join(f'<circle cx="{x}" cy="{604 + 0.0045*(x-200)**2*-1 + 8:.1f}" r="2.2" '
                      f'fill="{GOLD_LIGHT}"/>' for x in range(168, 236, 9))
            + rivet(*WAIST, 4.5))


def draw_flap_back():
    d = "M166,326 L234,326 C248,430 258,520 266,594 Q200,616 134,594 C142,520 152,430 166,326 Z"
    return (f'<path d="{d}" fill="{AO_SHADE}" stroke="{OUTLINE}" stroke-width="3.2"/>'
            f'<path d="M142,586 Q200,606 258,586" fill="none" stroke="{GOLD}" stroke-width="2"/>'
            + cloud(150, 560, 0.8, 0, GOLD, 1.5) + cloud(250, 560, 0.8, 180, GOLD, 1.5))


# ---------------------------------------------------------------- limbs
def draw_upper_arm():
    pat = cloud(*lerp(SHO_L, ELB_L, 0.55), 0.6, 60, GOLD, 1.5)
    return (limb("ua", SHO_L, ELB_L, 15, 12, fill=AO, shade=AO_SHADE, stitch=GOLD, pattern=pat)
            + rivet(*SHO_L, 4.5))


def draw_forearm():
    a = angle_deg(ELB_L, WRI_L)
    wrist = (WRI_L[0] + math.cos(math.radians(a)) * 9, WRI_L[1] + math.sin(math.radians(a)) * 9)
    pat = band(ELB_L, WRI_L, 0.9, 11, 7)
    bracelet = band(ELB_L, WRI_L, 1.04, 8, 4, GOLD_LIGHT, GOLD)
    return (hand(wrist, a, thumb_side=-1, s=0.72, fill=SKIN_F, light=SKIN_F_LIGHT)
            + limb("fa", ELB_L, WRI_L, 12, 10, fill=AO, shade=AO_SHADE, stitch=GOLD, pattern=pat)
            + bracelet + rivet(*ELB_L, 4.5))


def foot(ankle):
    x, y = ankle
    d = (f"M{x+11},{y+4} C{x+13},{y+24} {x+4},{y+32} {x-16},{y+33} "
         f"C{x-34},{y+34} {x-38},{y+24} {x-30},{y+18} C{x-22},{y+12} {x-12},{y+8} {x-10},{y+2} Z")
    return (f'<path d="{d}" fill="{RED}" stroke="{OUTLINE}" stroke-width="3"/>'
            f'<path d="M{x+4},{y+16} C{x},{y+24} {x-12},{y+27} {x-26},{y+25}" fill="none" '
            f'stroke="{GOLD}" stroke-width="1.8"/>'
            + lotus(x - 20, y + 22, 0.32, GOLD, OUTLINE, 1))


def draw_thigh():
    return (limb("th", HIP_L, KNE_L, 20, 17, fill=QUAN, shade=QUAN_SHADE, stitch=QUAN_SHADE)
            + rivet(*HIP_L, 4.5))


def draw_shin():
    end = (ANK_L[0], ANK_L[1] + 4)
    folds = (f'<path d="M{KNE_L[0]-6},{KNE_L[1]+40} q-4,30 -8,60 M{KNE_L[0]+8},{KNE_L[1]+50} '
             f'q2,26 6,50" fill="none" stroke="{QUAN_SHADE}" stroke-width="2" stroke-linecap="round"/>')
    return (foot(ANK_L)
            + limb("sh", KNE_L, end, 17, 22, fill=QUAN, shade=QUAN_SHADE, stitch=QUAN_SHADE, pattern=folds)
            + rivet(*KNE_L, 4.5))


PARTS = [
    # id, parent, z, svg, pivot, limitDeg
    ("torso", None, 4, draw_torso(), (200, 290), None),
    ("head", "torso", 8, draw_head(), NECK, (-30, 30)),
    ("hair", "head", 1, draw_hair(), HAIR_PIVOT, (-15, 15)),
    ("flap_back", "torso", 0, draw_flap_back(), WAIST, (-20, 20)),
    ("flap_front", "torso", 5, draw_flap_front(), WAIST, (-20, 20)),
    ("thigh_L", "torso", 3, draw_thigh(), HIP_L, (-70, 60)),
    ("shin_L", "thigh_L", 2, draw_shin(), KNE_L, (-10, 120)),
    ("thigh_R", "torso", 3, f'<g {MIRROR}>{draw_thigh()}</g>', mx(HIP_L), (-60, 70)),
    ("shin_R", "thigh_R", 2, f'<g {MIRROR}>{draw_shin()}</g>', mx(KNE_L), (-120, 10)),
    ("upper_arm_L", "torso", 6, draw_upper_arm(), SHO_L, (-150, 60)),
    ("forearm_L", "upper_arm_L", 7, draw_forearm(), ELB_L, (-140, 10)),
    ("upper_arm_R", "torso", 6, f'<g {MIRROR}>{draw_upper_arm()}</g>', mx(SHO_L), (-60, 150)),
    ("forearm_R", "upper_arm_R", 7, f'<g {MIRROR}>{draw_forearm()}</g>', mx(ELB_L), (-10, 140)),
]

STRINGS = [
    ("head", "head", (200, 40), "middle", 12),
    ("hand_L", "forearm_L", lerp(ELB_L, WRI_L, 1.22), "index", 8),
    ("hand_R", "forearm_R", mx(lerp(ELB_L, WRI_L, 1.22)), "ring", 16),
    ("knee_L", "shin_L", KNE_L, "thumb", 4),
    ("knee_R", "shin_R", mx(KNE_L), "pinky", 20),
]

if __name__ == "__main__":
    build(OUT, "co_gai", PARTS, STRINGS)
    print("co_gai done")
