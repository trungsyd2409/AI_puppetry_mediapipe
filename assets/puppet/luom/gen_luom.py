"""Luom, the little liaison boy, as a paper-cut shadow puppet (3/4 view, running to the right).

Naive folk look: big round head, small chubby body, round cheeks, happy dot eyes.
Folded ca lo cap with a yellow star on red, ao vat xeo (cross-collar brown shirt), dark green
shorts, red scarf, little satchel, bare feet. Every joint is a round disc with a bronze rivet:
neck, shoulders, elbows, hips, knees, ankles.
Canvas 400 x 510 design units, feet on y = 478.
Strings: middle finger -> top of the cap, index finger -> shoulder.
"""
import math, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from dongho_lib import build, capsule, lerp, circle_shape, capsule_shape  # noqa
from paper_lib import *  # noqa

OUT = os.path.dirname(os.path.abspath(__file__))
W, H = 400, 510
GROUND = 478

HEAD_C = (208, 150)
NECK = (200, 228)
SHO_N, ELB_N, WRI_N = (206, 252), (218, 298), (224, 340)
SHO_F, ELB_F, WRI_F = (178, 250), (162, 296), (154, 338)
HIP_N, KNEE_N, ANK_N = (214, 338), (218, 390), (214, 440)
HIP_F, KNEE_F, ANK_F = (184, 338), (188, 390), (184, 440)
STRAP_END = (152, 312)
SCARF_ROOT = (178, 240)
FAR = 0.8


def k(col, far):
    return darker(col, FAR) if far else col


# ---------------- head ----------------
def head():
    out = defs()
    out += cut(capsule((198, 200), NECK, 15, 14), SKIN_D, w=0)                      # neck
    out += disc(*NECK, 13, SKIN_D, ring=False)
    face = ("M136,152 C134,104 168,78 210,78 C254,78 282,106 282,148 C283,170 276,190 262,204 "
            "C246,220 226,226 206,225 C168,224 138,198 136,152 Z")
    out += cut(face, SKIN)
    # hair: back of the head down to the nape, sideburn, fringe under the cap
    hair = ("M138,152 C132,112 160,84 206,80 C248,78 278,98 282,126 C272,120 262,122 256,128 "
            "C250,118 238,118 232,126 C226,116 212,116 206,126 C200,118 190,118 184,126 "
            "C178,136 176,148 176,158 C172,172 164,182 156,190 C150,194 144,196 140,197 C136,184 136,168 138,152 Z")
    out += cut(hair, INK, w=0.6)
    for i in range(4):
        out += incise(f"M{150 + i * 8},{110 + i * 2} C{146 + i * 8},{130 + i * 4} {148 + i * 7},{160} {146 + i * 5},{184 - i * 4}",
                      0.9, INK, 0.5)
    for x in (196, 220, 246, 268):
        out += incise(f"M{x - 6},{104} C{x - 2},{112} {x + 2},{116} {x + 4},{120}", 0.8, INK, 0.4)
    # ear
    out += cut("M168,146 C154,140 148,156 152,168 C156,180 170,182 176,172 Z", SKIN_D)
    out += incise("M164,154 C158,158 158,166 164,172", 1.0, SKIN_D, 0.5)
    # cheeks
    out += f'<circle cx="206" cy="182" r="15" fill="{BLUSH}" opacity="0.55"/>'
    out += f'<circle cx="270" cy="178" r="9" fill="{BLUSH}" opacity="0.5"/>'
    # eyes: happy dots with a highlight, short arched brows
    for (x, y, rx, ry) in ((218, 150, 5.2, 6.6), (256, 148, 4.4, 6.0)):
        out += f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{INK}"/>'
        out += f'<circle cx="{x + 1.6}" cy="{y - 2.2}" r="{rx * 0.36:.1f}" fill="{NGA}"/>'
    out += thin("M208,132 C214,128 222,128 228,131", 1.6, INK)
    out += thin("M248,130 C253,127 260,127 265,130", 1.4, INK)
    # little nose and an open, happy mouth
    out += incise("M270,160 C275,164 275,170 269,172", 1.1, SKIN, 0.5)
    mouth = "M228,184 C236,186 252,186 262,180 C260,194 250,202 242,202 C234,202 228,194 228,184 Z"
    out += cut(mouth, "#6E2418", w=0.6)
    out += f'<path d="M234,196 C238,192 248,192 254,195 C250,201 240,202 234,196 Z" fill="#C25B48"/>'
    # ---- ca lo: folded garrison cap, tilted, crisp facets ----
    cap = '<g transform="translate(2,16) rotate(-11 208 82)">'
    top_l, ridge_l, dip, ridge_r, top_r = (144, 104), (152, 66), (204, 72), (256, 58), (274, 98)
    body = [(140, 108), ridge_l, (178, 60), dip, (236, 54), ridge_r, (270, 70), top_r]
    cap += facet(body + [(206, 104)], REU)
    cap += f'<path d="M{" L".join(f2(p) for p in body)} L206,104 Z" fill="url(#weave)"/>'
    cap += facet([ridge_l, (178, 60), dip, (236, 54), ridge_r, (254, 64), (204, 78), (156, 72)], REU_L)   # top crease
    band = [(140, 108), (146, 86), (206, 82), (272, 76), (274, 98), (206, 104)]
    cap += facet(band, REU_D)                                                                    # turned-up band
    cap += f'<path d="M{" L".join(f2(p) for p in band)} Z" fill="url(#weave)"/>'
    cap += facet([(146, 86), (206, 82), (272, 76), (270, 80), (206, 87), (147, 91)], lighter(REU_D, 0.3))   # fold lip
    cap += facet([(258, 77), (272, 76), (274, 98), (262, 99)], darker(REU_D, 0.8))              # front fold
    cap += incise("M206,82 L206,104", 1.0, REU_D, 0.5)
    cap += incise("M156,72 L204,78 L254,64", 1.0, REU, 0.5)
    cap += brush("M140,108 L146,86 L152,66 L178,60 L204,72 L236,54 L256,58 L270,70 L274,98 L206,104 Z", 0.9,
                 darker(REU, 0.65), taper=0, var=0.2)
    # badge: yellow star on red
    cap += f'<circle cx="240" cy="90" r="10.5" fill="{SON_D}"/><circle cx="240" cy="90" r="9" fill="{SON}"/>'
    cap += f'<path d="{star_d(240, 90.5, 7.4)}" fill="{VANG_L}"/>'
    cap += '</g>'
    out += cap
    return out


# ---------------- torso, scarf, satchel ----------------
def torso():
    out = defs()
    # shorts seat (under the shirt hem)
    out += cut("M168,318 L232,318 C238,330 238,346 234,356 L166,356 C162,344 162,330 168,318 Z", LUC, cloth=True)
    # chubby shirt
    shirt = ("M170,240 C182,230 216,230 230,240 C246,256 252,290 248,322 C247,332 244,340 240,346 "
             "L162,346 C156,336 152,326 152,312 C150,282 156,256 170,240 Z")
    out += cut(shirt, NAU, cloth=True)
    # vat xeo: the front flap crossing from the collar down to the right side seam
    flap = "M196,236 C210,232 224,234 232,242 C246,258 250,284 248,304 C232,298 214,276 196,236 Z"
    out += cut(flap, NAU_L, cloth=True)
    out += incise("M196,236 C214,276 232,298 248,304", 1.4, NAU, 0.7)
    for (x, y) in ((206, 252), (220, 274), (236, 292)):                                         # knot buttons
        out += f'<circle cx="{x}" cy="{y}" r="3.4" fill="{NGA_D}"/><circle cx="{x - 0.8}" cy="{y - 0.8}" r="1.4" fill="{NGA}"/>'
        out += thin(f"M{x + 3},{y} l6,2", 1.2, NGA_D)
    # folds
    out += incise("M166,262 C172,278 172,296 166,312", 1.2, NAU, 0.6)
    out += incise("M180,300 C196,306 214,310 232,312", 1.1, NAU, 0.6)
    out += incise("M188,318 C204,324 222,326 240,322", 1.0, NAU, 0.6)
    # hem band with punched dots (shadow-puppet perforation)
    out += cut("M158,334 C190,342 220,342 244,336 L240,346 L162,346 Z", NAU_D, cloth=True, w=0.5)
    out += punch_row((166, 341), (238, 341), 12, 1.5, darker(NAU_D, 0.55))
    # satchel strap across the chest (near shoulder -> far hip)
    out += cut("M214,238 L224,242 L162,322 L152,316 Z", NAU_D, w=0.6)
    out += punch_row((216, 244), (160, 316), 9, 1.1, VANG)
    # red scarf: band and knot under the chin
    out += cut("M176,236 C192,230 214,230 230,238 L228,248 C212,242 194,242 178,246 Z", SON)
    out += cut("M226,240 L246,246 L242,262 L222,256 Z", SON_D)
    out += cut("M236,258 L258,288 L242,292 Z", SON)
    out += cut("M228,260 L232,296 L218,288 Z", SON_D)
    out += incise("M240,264 L250,282", 0.9, SON, 0.5)
    return out


def scarf_tail():
    """Two scarf ends flying back from the nape (sways with the wind)."""
    x, y = SCARF_ROOT
    out = cut(f"M{x},{y} C{x - 22},{y - 10} {x - 46},{y - 20} {x - 74},{y - 16} L{x - 64},{y - 8} L{x - 76},{y - 2} "
              f"C{x - 52},{y + 4} {x - 28},{y + 8} {x},{y + 8} Z", SON)
    out += incise(f"M{x - 8},{y + 2} C{x - 30},{y - 4} {x - 50},{y - 8} {x - 66},{y - 8}", 0.9, SON, 0.5)
    out += cut(f"M{x},{y + 6} C{x - 20},{y + 12} {x - 40},{y + 20} {x - 64},{y + 30} L{x - 52},{y + 34} "
               f"C{x - 36},{y + 22} {x - 20},{y + 16} {x},{y + 14} Z", SON_D)
    return out


def satchel():
    x, y = STRAP_END
    out = defs()
    bag = f"M{x - 28},{y - 4} L{x + 24},{y - 4} C{x + 28},{y + 20} {x + 28},{y + 40} {x + 24},{y + 50} L{x - 28},{y + 50} C{x - 32},{y + 40} {x - 32},{y + 20} {x - 28},{y - 4} Z"
    flap = f"M{x - 28},{y - 4} L{x + 24},{y - 4} L{x + 22},{y + 24} C{x + 6},{y + 32} {x - 10},{y + 32} {x - 26},{y + 24} Z"
    out += cut(bag, VANG, cloth=True)
    out += cut(flap, VANG_L, cloth=True)
    out += incise(f"M{x - 24},{y + 2} L{x + 20},{y + 2}", 1.0, VANG_L, 0.5)
    out += punch_row((x - 22, y + 20), (x + 18, y + 20), 8, 1.2, VANG_D)
    out += incise(spiral_d(x - 2, y + 10, 6, 1.3), 1.0, VANG_L, 0.5)
    out += f'<circle cx="{x - 2}" cy="{y + 27}" r="3.6" fill="{BRONZE}"/>'
    # a letter peeking out
    out += cut(f"M{x + 6},{y - 16} L{x + 24},{y - 10} L{x + 20},{y + 0} L{x + 2},{y - 6} Z", NGA)
    out += thin(f"M{x + 6},{y - 12} L{x + 14},{y - 6} L{x + 22},{y - 10}", 0.8, NGA_D)
    out += rivet(x, y - 4, 3.0)
    return out


# ---------------- limbs ----------------
def thigh(hip, knee, far):
    out = defs()
    hem = lerp(hip, knee, 0.62)
    out += cut(capsule(lerp(hip, knee, 0.5), knee, 15, 13), k(SKIN, far))
    leg = (f"M{hip[0] - 20},{hip[1] - 6} L{hip[0] + 20},{hip[1] - 6} L{hem[0] + 22},{hem[1] + 4} "
           f"C{hem[0] + 8},{hem[1] + 9} {hem[0] - 8},{hem[1] + 9} {hem[0] - 22},{hem[1] + 4} Z")
    out += cut(leg, k(LUC, far), cloth=True)
    out += incise(f"M{hem[0] - 20},{hem[1] - 2} C{hem[0] - 6},{hem[1] + 3} {hem[0] + 8},{hem[1] + 3} {hem[0] + 20},{hem[1] - 2}",
                  1.0, k(LUC, far), 0.5)
    out += incise(f"M{hip[0] + 6},{hip[1] + 10} C{hip[0] + 10},{hip[1] + 22} {hip[0] + 10},{hip[1] + 30} {hip[0] + 8},{hip[1] + 38}",
                  1.0, k(LUC, far), 0.5)
    out += disc(*hip, 17, k(LUC_L, far))
    return out


def shin(knee, ank, far):
    out = cut(capsule(knee, ank, 13, 10.5), k(SKIN, far))
    out += incise(f"M{knee[0] + 4},{knee[1] + 14} C{knee[0] + 8},{knee[1] + 30} {knee[0] + 6},{knee[1] + 46} {ank[0] + 4},{ank[1] - 12}",
                  0.9, k(SKIN, far), 0.5)
    out += disc(*knee, 12.5, k(SKIN_D, far))
    return out


def foot(ank, far):
    x, y = ank
    sole = GROUND - 1
    d = (f"M{x - 10},{y - 4} C{x - 14},{y + 12} {x - 16},{sole - 6} {x - 8},{sole} "
         f"L{x + 26},{sole} C{x + 36},{sole} {x + 38},{sole - 12} {x + 28},{sole - 16} "
         f"C{x + 18},{sole - 19} {x + 10},{y + 8} {x + 9},{y - 4} Z")
    out = cut(d, k(SKIN, far))
    for i in range(3):                                                                           # toes
        out += incise(f"M{x + 24 + i * 4},{sole - 1} l1,-5", 0.8, k(SKIN, far), 0.4)
    out += disc(x, y, 10, k(SKIN_D, far))
    return out


def upper_arm(sho, elb, far):
    out = defs()
    out += cut(capsule(sho, elb, 15, 12), k(NAU, far), cloth=True)
    m = lerp(sho, elb, 0.55)
    out += incise(f"M{m[0] - 9:.1f},{m[1] - 2:.1f} C{m[0] - 3:.1f},{m[1] + 3:.1f} {m[0] + 4:.1f},{m[1] + 3:.1f} {m[0] + 10:.1f},{m[1] - 1:.1f}",
                  1.0, k(NAU, far), 0.5)
    out += disc(*sho, 15, k(NAU_L, far))
    return out


def fore_arm(elb, wri, far):
    out = defs()
    x, y = wri
    out += cut(capsule(elb, wri, 10, 8.5), k(SKIN, far))
    hand = f"M{x - 10},{y - 4} C{x - 12},{y + 10} {x - 4},{y + 18} {x + 4},{y + 17} C{x + 13},{y + 16} {x + 14},{y + 4} {x + 10},{y - 6} Z"
    out += cut(hand, k(SKIN, far))
    out += cut(f"M{x + 8},{y - 2} C{x + 16},{y - 2} {x + 18},{y + 6} {x + 12},{y + 8} Z", k(SKIN_D, far), w=0.5)   # thumb
    out += cut(capsule(elb, lerp(elb, wri, 0.26), 13, 12.5), k(NAU, far), cloth=True)          # rolled sleeve
    c = lerp(elb, wri, 0.26)
    out += incise(f"M{c[0] - 12:.1f},{c[1]:.1f} L{c[0] + 12:.1f},{c[1] + 1:.1f}", 1.0, k(NAU, far), 0.5)
    out += disc(*elb, 12, k(NAU_L, far))
    return out


def main():
    parts = [
        # id, parent, z, svg, pivot, limitDeg
        ("scarf", "torso", 0, scarf_tail(), SCARF_ROOT, (-30, 30)),
        ("arm_far_upper", "torso", 1, upper_arm(SHO_F, ELB_F, True), SHO_F, (-120, 120)),
        ("arm_far_fore", "arm_far_upper", 1, fore_arm(ELB_F, WRI_F, True), ELB_F, (-10, 140)),
        ("leg_far_thigh", "torso", 2, thigh(HIP_F, KNEE_F, True), HIP_F, (-100, 60)),
        ("leg_far_shin", "leg_far_thigh", 2, shin(KNEE_F, ANK_F, True), KNEE_F, (-10, 130)),
        ("leg_far_foot", "leg_far_shin", 2, foot(ANK_F, True), ANK_F, (-40, 40)),
        ("satchel", "torso", 3, satchel(), STRAP_END, (-40, 40)),
        ("torso", None, 4, torso(), (200, 290), None),
        ("leg_near_thigh", "torso", 5, thigh(HIP_N, KNEE_N, False), HIP_N, (-100, 60)),
        ("leg_near_shin", "leg_near_thigh", 5, shin(KNEE_N, ANK_N, False), KNEE_N, (-10, 130)),
        ("leg_near_foot", "leg_near_shin", 5, foot(ANK_N, False), ANK_N, (-40, 40)),
        ("head", "torso", 6, head(), NECK, (-30, 30)),
        ("arm_near_upper", "torso", 7, upper_arm(SHO_N, ELB_N, False), SHO_N, (-120, 120)),
        ("arm_near_fore", "arm_near_upper", 7, fore_arm(ELB_N, WRI_N, False), ELB_N, (-10, 140)),
    ]
    strings = [
        ("head", "head", (208, 62), "right", "middle", 12),
        ("shoulder", "torso", (200, 244), "right", "index", 8),
    ]
    colliders = {
        "head": {"density": 0.6, "shapes": [circle_shape(HEAD_C, 70)]},
        "torso": {"density": 1.0, "shapes": [capsule_shape((200, 256), (200, 326), 40)]},
        "leg_near_thigh": {"density": 0.5, "shapes": [capsule_shape(HIP_N, KNEE_N, 14)]},
        "leg_near_shin": {"density": 0.4, "shapes": [capsule_shape(KNEE_N, ANK_N, 11)]},
        "leg_far_thigh": {"density": 0.5, "shapes": [capsule_shape(HIP_F, KNEE_F, 14)]},
        "leg_far_shin": {"density": 0.4, "shapes": [capsule_shape(KNEE_F, ANK_F, 11)]},
        "leg_near_foot": {"density": 0.3, "shapes": [capsule_shape(ANK_N, (ANK_N[0] + 24, GROUND - 7), 8)]},
        "leg_far_foot": {"density": 0.3, "shapes": [capsule_shape(ANK_F, (ANK_F[0] + 24, GROUND - 7), 8)]},
    }
    extra = {"groundY": GROUND, "headCenter": list(HEAD_C),
             "hips": [list(HIP_N), list(HIP_F)], "ankles": [list(ANK_N), list(ANK_F)]}
    rig = build(OUT, "luom", (W, H), parts, strings, colliders, extra, pad=16, texture=card_texture, rough=True)
    print("parts:", [p["id"] for p in rig["parts"]], "feetY", rig["feetY"])


if __name__ == "__main__":
    main()
