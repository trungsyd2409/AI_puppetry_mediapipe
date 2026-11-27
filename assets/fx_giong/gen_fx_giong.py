"""Gameplay sprites in Dong Ho style: fire-stone shell, flame trail, explosion,
spark (bamboo block), hoof dust, catapult (may ban da), UI (life, score plaque).

Each sprite is drawn centred in its own box; PNG at 2x. fx.json lists files,
sizes (design units) and the anchor point.
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dongho_lib import *  # noqa

OUT = os.path.dirname(os.path.abspath(__file__))
MANIFEST = {}


def save(name, inner, w, h, anchor=None, scale=2):
    """inner is drawn with (0,0) at the box centre."""
    write_svg_png(os.path.join(OUT, name), f'<g transform="translate({w/2},{h/2})">{inner}</g>',
                  (0, 0, w, h), scale)
    MANIFEST[name] = {"png": f"{name}.png", "size": [w, h],
                      "anchor": list(anchor) if anchor else [w / 2, h / 2], "pngScale": scale}


# ---------- shell: stone ball wrapped in fire ----------
def shell():
    r = 26
    ball = ink(f"M{-r},0 A{r},{r} 0 1 1 {r},0 A{r},{r} 0 1 1 {-r},0 Z", "#7D736A", 3.4)
    cracks = line("M-14,-8 L-4,-2 L-8,8 M6,-16 L10,-4 L20,0 M-2,14 L8,10", 2)
    rim = line(f"M{-r+6},-10 A{r-6},{r-6} 0 0 1 4,{-r+6}", 3, "#A89C8E")
    band = ink("M-24,6 C-10,14 10,14 24,6 L22,12 C10,20 -10,20 -22,12 Z", SON, 2)
    return ball + rim + cracks + band


def trail(frame):
    """Flame trail pointing +x (behind a shell flying to -x)."""
    rnd = random.Random(frame * 13 + 5)
    out = ""
    for i, (x, s) in enumerate([(30, 0.55), (-22, 0.75), (-75, 0.95)]):
        y = rnd.uniform(-6, 6)
        out += flame(x, y, s * rnd.uniform(0.9, 1.1), 90 + rnd.uniform(-8, 8))
    return out


# ---------- explosion (5 frames) ----------
def petal_ring(n, r0, r1, col, rot=0, sw=3):
    out = ""
    for i in range(n):
        a = math.radians(rot + i * 360 / n)
        b = math.radians(rot + (i + 0.5) * 360 / n)
        c = math.radians(rot + (i - 0.5) * 360 / n)
        tip = (math.cos(a) * r1, math.sin(a) * r1)
        l = (math.cos(c) * r0, math.sin(c) * r0)
        rr = (math.cos(b) * r0, math.sin(b) * r0)
        mid = (math.cos(a) * (r0 + r1) / 2, math.sin(a) * (r0 + r1) / 2)
        k = r1 * 0.78 / r0
        out += ink(f"M{f2(l)} Q{l[0]*k:.1f},{l[1]*k:.1f} {f2(tip)} Q{rr[0]*k:.1f},{rr[1]*k:.1f} {f2(rr)} Z",
                   col, sw)
    return out


def explosion(k):
    out = ""
    if k == 0:
        out += petal_ring(8, 14, 46, VANG, 0)
        out += f'<circle r="20" fill="{TRANG}" stroke="{INK}" stroke-width="3"/>'
    elif k == 1:
        out += petal_ring(10, 30, 92, SON, 10)
        out += petal_ring(10, 22, 62, VANG, 28)
        out += f'<circle r="26" fill="{TRANG}" stroke="{INK}" stroke-width="3"/>'
    elif k == 2:
        out += petal_ring(12, 50, 120, SON_DARK, 0)
        out += petal_ring(12, 40, 96, SON, 15)
        out += petal_ring(12, 30, 66, VANG, 30)
        out += f'<circle r="34" fill="{TRANG}" stroke="{INK}" stroke-width="3"/>'
        for a in range(0, 360, 60):
            x, y = math.cos(math.radians(a)) * 40, math.sin(math.radians(a)) * 40
            out += swirl(x, y, 0.9, a)
    elif k == 3:
        for a, d, s in [(0, 50, 1.0), (70, 56, 0.9), (140, 46, 1.1), (210, 54, 0.95), (290, 50, 1.0)]:
            x, y = math.cos(math.radians(a)) * d, math.sin(math.radians(a)) * d
            out += f'<g transform="translate({x:.1f},{y:.1f}) scale({s})">' + ink(
                "M-36,0 C-40,-26 -8,-36 6,-22 C24,-36 46,-18 36,4 C40,24 12,32 0,22 C-16,34 -40,22 -36,0 Z",
                "#4A403A", 3) + line("M-14,2 C-16,-10 0,-14 4,-4 C6,2 0,4 -3,1", 2.2, PAPER) + '</g>'
        out += petal_ring(8, 16, 44, SON, 0) + f'<circle r="16" fill="{VANG}" stroke="{INK}" stroke-width="2.6"/>'
        rnd = random.Random(3)
        for _ in range(10):
            a = rnd.uniform(0, 2 * math.pi); d = rnd.uniform(90, 125)
            out += f'<circle cx="{math.cos(a)*d:.1f}" cy="{math.sin(a)*d:.1f}" r="4" fill="{VANG}" stroke="{INK}" stroke-width="1.6"/>'
    else:
        for a, d, s in [(20, 70, 0.9), (110, 62, 0.8), (200, 74, 0.85), (300, 66, 0.75)]:
            x, y = math.cos(math.radians(a)) * d, math.sin(math.radians(a)) * d - 20
            out += f'<g transform="translate({x:.1f},{y:.1f}) scale({s})" opacity="0.8">' + ink(
                "M-36,0 C-40,-26 -8,-36 6,-22 C24,-36 46,-18 36,4 C40,24 12,32 0,22 C-16,34 -40,22 -36,0 Z",
                "#8A7E72", 2.6) + line("M-14,2 C-16,-10 0,-14 4,-4", 2, PAPER) + '</g>'
    return out


# ---------- spark when bamboo blocks ----------
def spark():
    out = ""
    for i in range(8):
        a = i * 45
        L = 54 if i % 2 == 0 else 34
        out += (f'<g transform="rotate({a})">'
                + ink(f"M0,-6 L{L},0 L0,6 Z", VANG if i % 2 == 0 else TRANG, 2.4) + '</g>')
    return out + f'<circle r="12" fill="{TRANG}" stroke="{INK}" stroke-width="2.4"/>'


# ---------- hoof dust (3 frames) ----------
def dust(k):
    out = ""
    for j, (x, y, r) in enumerate([(-34, 0, 16), (-10, -8, 20), (18, -2, 17), (40, 4, 12)]):
        rr = r * (0.7 + 0.35 * k)
        x2 = x * (1 + 0.35 * k)
        out += (f'<g transform="translate({x2:.1f},{y - 6*k:.1f})" opacity="{1 - 0.25*k:.2f}">'
                + ink(f"M{-rr:.1f},0 C{-rr:.1f},{-rr*1.1:.1f} {rr:.1f},{-rr*1.1:.1f} {rr:.1f},0 "
                      f"C{rr*0.6:.1f},{rr*0.4:.1f} {-rr*0.6:.1f},{rr*0.4:.1f} {-rr:.1f},0 Z", "#D8B57E", 2.4)
                + line(f"M{-rr*0.4:.1f},{-rr*0.2:.1f} C{-rr*0.4:.1f},{-rr*0.6:.1f} {rr*0.2:.1f},{-rr*0.6:.1f} "
                       f"{rr*0.1:.1f},{-rr*0.3:.1f}", 1.8, "#8C6430") + '</g>')
    return out


# ---------- catapult (may ban da), two parts so the arm can swing ----------
def catapult_base():
    wood, wood_d = "#8C5A34", "#5E3A22"
    out = ink("M-110,40 L110,40 L100,56 L-100,56 Z", wood_d, 3)
    for x in (-80, 80):
        out += ink(f"M{x-20},70 A20,20 0 1 1 {x+20},70 A20,20 0 1 1 {x-20},70 Z", wood, 3)
        out += line(f"M{x-14},70 L{x+14},70 M{x},56 L{x},84", 2.2)
    out += ink("M-60,40 L-14,-70 L-2,-70 L-40,40 Z", wood, 3)
    out += ink("M60,40 L14,-70 L2,-70 L40,40 Z", wood, 3)
    out += ink("M-26,-80 L26,-80 L26,-66 L-26,-66 Z", wood_d, 2.6)
    out += line("M-40,0 L40,0", 4, wood_d)
    # enemy banner on the frame
    out += line("M90,40 L90,-60", 3.4) + ink("M90,-60 L140,-52 L126,-38 L144,-24 L90,-20 Z", INK, 2.6)
    return out


def catapult_arm():
    """Pivot at (0,0); arm rests pointing back-left (+x is the throw side)."""
    out = ink(capsule((-150, 0), (40, 0), 8, 10), "#7A4A2A", 3)
    out += ink("M-178,-22 C-190,0 -178,22 -150,22 C-140,10 -140,-10 -150,-22 Z", "#5E3A22", 3)  # cup
    out += ink("M30,-30 L80,-30 L80,30 L30,30 Z", XAM, 3)  # counterweight
    out += line("M40,-20 L70,20 M70,-20 L40,20", 2)
    out += f'<circle r="9" fill="{VANG}" stroke="{INK}" stroke-width="2.6"/>'
    return out


# ---------- UI ----------
def life_icon():
    """Small bamboo shoot + bell = one life."""
    out = ink("M-8,26 L8,26 L6,-14 L-6,-14 Z", LA, 2.6)
    out += line("M-7,6 L7,6 M-6,-6 L6,-6", 2, LA_DARK)
    out += f'<g transform="translate(4,-16) rotate(-40) scale(0.4)">{ink("M0,0 C18,-8 52,-10 78,-2 C52,6 20,8 0,0 Z", LA, 3)}</g>'
    out += f'<g transform="translate(-4,-14) rotate(-140) scale(0.32)">{ink("M0,0 C18,-8 52,-10 78,-2 C52,6 20,8 0,0 Z", LA_DARK, 3)}</g>'
    return out + bell(0, 30, 8)


def life_lost():
    return f'<g opacity="0.35">{life_icon()}</g>'


def score_plaque():
    """Red lacquer plaque with gold border, room for text in the middle."""
    d = "M-150,-34 L150,-34 L170,0 L150,34 L-150,34 L-170,0 Z"
    out = ink(d, SON, 3.6)
    out += line("M-140,-24 L140,-24 L156,0 L140,24 L-140,24 L-156,0 Z", 2, VANG, 'stroke-dasharray="6 4"')
    for x in (-160, 160):
        out += swirl(x * 1.08, 0, 0.7, 0 if x > 0 else 180)
    return out


def main():
    save("shell", shell(), 64, 64)
    for k in range(3):
        save(f"trail_{k}", trail(k), 160, 80, (5, 40))
    for k in range(5):
        save(f"explode_{k}", explosion(k), 280, 280)
    save("spark", spark(), 130, 130)
    for k in range(3):
        save(f"dust_{k}", dust(k), 190, 80, (95, 55))
    save("catapult_base", catapult_base(), 300, 200, (150, 100))
    save("catapult_arm", f'<g transform="translate(55,0)">{catapult_arm()}</g>', 300, 80, (205, 40))
    save("life", life_icon(), 40, 84)
    save("life_lost", life_lost(), 40, 84)
    save("score_plaque", score_plaque(), 360, 80)
    with open(os.path.join(OUT, "fx.json"), "w") as f:
        json.dump(MANIFEST, f, indent=2)
    print(len(MANIFEST), "sprites")


if __name__ == "__main__":
    main()
