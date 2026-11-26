"""Animated-prop sprites for the stage, same lacquer + ink style as the puppets.

  props/fish.png       carp (ca chep, Dong Ho style) facing right, for jumps out of the pond
  props/crane_0..2.png crane (hac) in flight, wings up / level / down, facing right (170 x 130)
  props/leaf.png       bamboo leaf blown by the wind

PNGs are rendered at 2x (stage.json props.scale).
"""
import os, subprocess

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "props")
os.makedirs(OUT, exist_ok=True)

INK = "#2A140A"
GOLD = "#E2B44A"
GOLD_L = "#F6DA8A"
RED = "#B8301C"
RED_D = "#7A1A0E"


def save(name, w, h, inner):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
           f'{inner}</svg>')
    p = os.path.join(OUT, f"{name}.svg")
    open(p, "w").write(svg)
    subprocess.run(["rsvg-convert", "-z", "2", "-o", os.path.join(OUT, f"{name}.png"), p], check=True)
    os.remove(p)


def cloud(x, y, s, rot=0, color=GOLD, w=1.4):
    return (f'<path transform="translate({x},{y}) rotate({rot}) scale({s})" '
            f'd="M-11,5 C-13,-5 -3,-10 4,-6 C10,-2 7,6 1,5 C-3,4 -2,-1 1,-1 '
            f'M4,-6 C8,-12 16,-9 15,-3 C14,2 9,2 9,-1" fill="none" stroke="{color}" '
            f'stroke-width="{w}" stroke-linecap="round"/>')


# ---------------------------------------------------------------- carp (200 x 110)
def fish():
    body = ("M40,58 C50,30 96,22 134,31 C154,36 168,45 176,56 C168,67 154,75 134,80 "
            "C96,89 50,84 40,58 Z")
    tail = ("M44,54 C32,42 18,28 6,14 C12,32 18,46 26,58 C18,70 12,84 6,102 "
            "C18,88 32,74 44,64 Z")
    dorsal = "M78,30 C84,10 112,6 128,30 C112,24 96,24 78,30 Z"
    pect = "M118,78 C122,92 136,98 146,96 C140,88 132,82 124,76 Z"
    belly_fin = "M76,82 C78,94 90,100 100,98 C94,92 88,86 84,82 Z"
    scales = "".join(
        f'<path d="M{x},{y} q6,-7 12,0" fill="none" stroke="{GOLD_L}" stroke-width="1.4" opacity="0.85"/>'
        for row, y in enumerate(range(42, 80, 9)) for x in range(58 + (row % 2) * 6, 140, 12))
    rays = lambda d: f'<path d="{d}" fill="none" stroke="{GOLD}" stroke-width="1.2" stroke-linecap="round"/>'
    return (
        f'<linearGradient id="g_fish" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{RED}"/><stop offset="0.55" stop-color="#D9622A"/>'
        f'<stop offset="1" stop-color="#F2B75A"/></linearGradient>'
        f'<clipPath id="c_fish"><path d="{body}"/></clipPath>'
        f'<path d="{tail}" fill="{RED}" stroke="{INK}" stroke-width="2.4" stroke-linejoin="round"/>'
        + rays("M40,56 C30,44 20,32 12,22 M40,62 C30,74 20,86 12,96 M42,58 C32,58 24,58 16,58")
        + f'<path d="{dorsal}" fill="{RED_D}" stroke="{INK}" stroke-width="2.2"/>'
        + rays("M88,28 C92,18 100,14 106,14 M100,26 C104,18 112,16 118,18")
        + f'<path d="{belly_fin}" fill="{RED}" stroke="{INK}" stroke-width="2"/>'
        + f'<path d="{body}" fill="url(#g_fish)"/>'
        + f'<g clip-path="url(#c_fish)">{scales}'
        + f'<path d="M50,64 C90,72 140,70 176,58 L176,90 L40,90 Z" fill="#F7D68A" opacity="0.45"/></g>'
        + cloud(92, 56, 0.9, 0, GOLD_L, 1.3)
        + f'<path d="M150,40 C144,50 144,64 150,72" fill="none" stroke="{RED_D}" stroke-width="2"/>'
        + f'<path d="{body}" fill="none" stroke="{INK}" stroke-width="2.6"/>'
        + f'<path d="{pect}" fill="{RED}" stroke="{INK}" stroke-width="2"/>'
        + f'<circle cx="160" cy="50" r="5" fill="#FFF4DE" stroke="{INK}" stroke-width="1.6"/>'
        + f'<circle cx="161" cy="50" r="2.4" fill="{INK}"/>'
        + f'<path d="M174,58 C182,62 188,68 190,78 M172,60 C178,66 180,72 180,80" fill="none" '
          f'stroke="{INK}" stroke-width="1.6" stroke-linecap="round"/>'
    )


# ---------------------------------------------------------------- crane (170 x 130)
def crane(lift):
    """lift: wing tip offset from the body line (negative = wings up)."""
    cx, cy = 80, 65
    body = (f"M{cx-34},{cy+2} C{cx-20},{cy-8} {cx+18},{cy-9} {cx+30},{cy-3} "
            f"C{cx+20},{cy+8} {cx-16},{cy+9} {cx-34},{cy+2} Z")
    neck = (f'<path d="M{cx+26},{cy-3} C{cx+44},{cy-8} {cx+60},{cy-10} {cx+70},{cy-10}" fill="none" '
            f'stroke="{INK}" stroke-width="5" stroke-linecap="round"/>')
    head = (f'<ellipse cx="{cx+72}" cy="{cy-10}" rx="6" ry="4.5" fill="{INK}"/>'
            f'<circle cx="{cx+71}" cy="{cy-14}" r="2.4" fill="#C0281C"/>'
            f'<path d="M{cx+77},{cy-10} L{cx+90},{cy-8}" stroke="{INK}" stroke-width="2.6" stroke-linecap="round"/>')
    legs = (f'<path d="M{cx-30},{cy+3} L{cx-62},{cy+8} M{cx-28},{cy+5} L{cx-60},{cy+12}" stroke="{INK}" '
            f'stroke-width="2.2" stroke-linecap="round"/>')

    def wing(sx, k, op):
        ty = cy + lift * k
        F, B, T = (sx + 12, cy), (sx - 26, cy + 1), (sx - 10, ty)
        d = (f"M{F[0]},{F[1]} C{sx+16},{cy + (ty-cy)*0.45} {sx+6},{cy + (ty-cy)*0.95} {T[0]},{T[1]} ")
        # primary feathers along the trailing edge
        for i, t in enumerate((0.18, 0.36, 0.54, 0.72)):
            bx, by = T[0] + (B[0]-T[0])*t, T[1] + (B[1]-T[1])*t
            d += f"L{bx-9:.1f},{by + (2 if lift < 0 else -2):.1f} L{bx:.1f},{by:.1f} "
        d += f"L{B[0]},{B[1]} Z"
        return f'<path d="{d}" fill="{INK}" opacity="{op}" stroke="{INK}" stroke-width="1" stroke-linejoin="round"/>'

    return (f'<g opacity="0.8">' + wing(cx + 8, 0.8, 0.55) + legs
            + f'<path d="{body}" fill="{INK}"/>' + neck + head + wing(cx - 2, 1.0, 1.0) + '</g>')


# ---------------------------------------------------------------- bamboo leaf (72 x 18)
def leaf():
    return ('<path d="M2,9 C18,1 48,0 70,8 C48,15 18,17 2,9 Z" fill="#4F7A3E" stroke="#2A140A" stroke-width="1.6"/>'
            '<path d="M4,9 C24,8 46,8 68,8" fill="none" stroke="#2F4A27" stroke-width="1.2"/>'
            '<path d="M2,9 L-4,10" stroke="#2A140A" stroke-width="1.6" stroke-linecap="round"/>')


save("fish", 200, 110, fish())
for i, lift in enumerate((-52, -3, 44)):
    save(f"crane_{i}", 170, 130, crane(lift))
save("leaf", 72, 18, leaf())
print("props done")
