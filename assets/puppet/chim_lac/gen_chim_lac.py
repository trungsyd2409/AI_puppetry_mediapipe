"""Chim lac (Dong Son bird) in Dong Ho woodblock style, cut into 4 rig parts.

Facing right. Canvas 640 x 420 design units. Wings are drawn raised (mid up-stroke) and
rotate around the shoulders.
Strings (one hand): index -> near wing, middle -> far wing.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from dongho_lib import *  # noqa

OUT = os.path.dirname(os.path.abspath(__file__))
W, H = 640, 420

SHO_N = (330, 196)      # near wing shoulder
SHO_F = (350, 186)      # far wing shoulder
TAIL_ROOT = (236, 214)
HEAD = (452, 140)


# ---------------- wings ----------------
def wing_geom(sho, rot=0.0, scale=1.0):
    """Leading-edge bezier of a raised wing, rotated around the shoulder."""
    base = [(0, 0), (-8, -60), (-40, -112), (-112, -150)]
    c, s = math.cos(rot), math.sin(rot)
    return [(sho[0] + (x * c - y * s) * scale, sho[1] + (x * s + y * c) * scale) for x, y in base]


def wing(sho, cols, covert, rot=0.0, scale=1.0, dots=TRANG):
    p0, p1, p2, p3 = wing_geom(sho, rot, scale)
    out = ""
    # flight feathers hang from the leading edge, sweeping back (left) and down
    N = 9
    back = (-math.cos(0.42 - rot), math.sin(0.42 - rot) * 0.9 + 0.25)
    for i in range(N, -1, -1):
        t = 0.1 + 0.9 * i / N
        a = bez(p0, p1, p2, p3, t)
        L = (34 + 72 * t ** 1.3) * scale
        tip = (a[0] + back[0] * L, a[1] + back[1] * L)
        c1 = (a[0] + back[0] * L * 0.3, a[1] + back[1] * L * 0.3 - 4)
        c2 = (a[0] + back[0] * L * 0.75, a[1] + back[1] * L * 0.75 + 3)
        out += strand(a, c1, c2, tip, 10 * scale, cols[i % len(cols)], 14)
    # outer primaries beyond the wing tip
    for k, (dx, dy, col) in enumerate([(-58, -6, cols[0]), (-50, 12, cols[1]), (-40, 28, cols[2 % len(cols)])]):
        a = p3
        tip = (a[0] + dx * scale, a[1] + dy * scale)
        out += strand(a, lerp(a, tip, 0.35), lerp(a, tip, 0.7), tip, 9 * scale, col, 12)
    # covert band along the leading edge
    edge = [bez(p0, p1, p2, p3, i / 16) for i in range(17)]
    inner = []
    for i, p in enumerate(edge):
        t = i / 16
        nx, ny = bez_norm(p0, p1, p2, p3, max(0.001, min(0.999, t)))
        if nx > 0:
            nx, ny = -nx, -ny               # toward the back of the wing
        w = (44 - 26 * t) * scale
        inner.append((p[0] + nx * w, p[1] + ny * w))
    # scalloped inner edge: rounded covert feather tips
    ri = list(reversed(inner))
    d = "M" + " L".join(f2(p) for p in edge) + " L" + f2(ri[0])
    for i in range(1, len(ri)):
        a, b = ri[i - 1], ri[i]
        m = lerp(a, b, 0.5)
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        bulge = 5 * scale
        # bulge toward the feathers (away from the leading edge)
        cx, cy = m[0] - dy / L * bulge * -1, m[1] + dx / L * bulge * -1
        d += f" Q{cx:.1f},{cy:.1f} {f2(b)}"
    d += " Z"
    out += ink(d, covert, 3.0)
    for i in range(3, 15, 3):
        q = lerp(edge[i], inner[i], 0.45)
        out += spiral(q[0], q[1], 6.5 * scale, 1.3, i * 30, dots, 1.7)
    for i in range(2, 16, 3):
        q = lerp(edge[i], inner[i], 0.82)
        out += f'<circle cx="{q[0]:.1f}" cy="{q[1]:.1f}" r="{2.4*scale:.1f}" fill="{dots}"/>'
    out += spiral(*lerp(edge[1], inner[1], 0.5), 10 * scale, 1.5, 0, dots, 2.0)
    return out


# ---------------- body / head / tail ----------------
def tail():
    out = ""
    specs = [
        ((240, 206), (190, 190), (130, 150), (48, 136), 12, LA),
        ((240, 210), (180, 206), (110, 196), (30, 200), 12, TRANG),
        ((240, 216), (184, 228), (120, 252), (44, 262), 12, SON),
        ((240, 220), (196, 244), (150, 282), (96, 304), 10, TRANG),
        ((240, 204), (204, 178), (166, 140), (110, 112), 9, SON),
    ]
    for p0, p1, p2, p3, w, c in specs:
        out += strand(p0, p1, p2, p3, w, c, 28)
    out += ink("M226,204 L246,200 L248,226 L228,228 Z", SON_DARK, 2.0)
    return out


def body():
    # one outline for body + neck (no seam where the neck joins)
    torso = ("M230,215 C250,180 320,166 366,172 C388,160 406,140 428,126 "
             "C450,114 474,124 474,146 C474,166 458,178 440,182 "
             "C420,188 410,204 412,222 C400,248 340,258 290,252 C254,247 232,234 230,215 Z")
    belly = ("M258,236 C290,250 350,252 396,232 C390,246 350,258 300,256 C276,254 262,248 258,236 Z")
    out = ""
    # tucked legs trailing back under the belly
    for dx, col in ((0, VANG), (14, VANG_LIGHT)):
        out += ink(capsule((318 + dx, 246), (280 + dx, 282), 4.5, 3.5), col, 2.0)
        out += line(f"M{278+dx},282 l-10,4 M{278+dx},282 l-8,-4 M{278+dx},282 l-12,0", 1.6)
    out += ink(torso, SON, 3.6)
    out += f'<path d="{belly}" fill="{TRANG}"/>' + line("M262,238 C300,252 350,252 394,234", 1.6)
    # scale feathers on the back: rows of small arcs, like the rooster print
    for r, (y0, n, x0) in enumerate([(196, 6, 262), (212, 7, 252), (228, 6, 262)]):
        for i in range(n):
            x = x0 + i * 20 + (10 if r % 2 else 0)
            y = y0 + (i % 2) * 2
            out += line(f"M{x-8},{y} C{x-8},{y+10} {x+8},{y+10} {x+8},{y}", 1.8,
                        TRANG if (i + r) % 2 else VANG_LIGHT)
    out += spiral(392, 204, 10, 1.5, 200, TRANG, 2.2)
    # neck rings (lac birds on bronze drums have banded necks)
    for i, t in enumerate((0.35, 0.55, 0.75)):
        a = lerp((382, 176), (440, 128), t)
        out += line(f"M{a[0]-9:.1f},{a[1]-6:.1f} C{a[0]-2:.1f},{a[1]+4:.1f} {a[0]+8:.1f},{a[1]+6:.1f} {a[0]+14:.1f},{a[1]+2:.1f}",
                    2.2, VANG if i % 2 == 0 else TRANG)
    return out


def head():
    hx, hy = HEAD
    out = ""
    # crest: three long feathers sweeping back
    for p3, col, w in [((372, 62), SON, 7), ((392, 54), LA, 6), ((414, 60), TRANG, 5)]:
        out += strand((hx - 6, hy - 18), (hx - 20, hy - 46), (p3[0] + 30, p3[1] + 12), p3, w, col, 18)
    # long beak, upper ochre, lower ivory
    out += ink(f"M{hx+14},{hy-10} C{hx+50},{hy-8} {hx+96},{hy+2} {hx+136},{hy+12} "
               f"C{hx+96},{hy+10} {hx+52},{hy+8} {hx+16},{hy+6} Z", VANG, 2.4)
    out += ink(f"M{hx+16},{hy+6} C{hx+52},{hy+8} {hx+92},{hy+11} {hx+130},{hy+13} "
               f"C{hx+92},{hy+18} {hx+50},{hy+18} {hx+14},{hy+14} Z", TRANG, 2.0)
    out += ink(f"M{hx-22},{hy} A22,22 0 1 1 {hx+22},{hy} A22,22 0 1 1 {hx-22},{hy} Z", SON, 3.0)
    out += line(f"M{hx-14},{hy+10} C{hx-6},{hy+18} {hx+8},{hy+18} {hx+16},{hy+8}", 1.8, TRANG)
    # Dong Ho animal eye: ivory almond, black pupil, red-brown lid line
    ex, ey = hx + 4, hy - 4
    out += ink(f"M{ex-8},{ey} C{ex-4},{ey-7} {ex+6},{ey-7} {ex+9},{ey} C{ex+5},{ey+5} {ex-4},{ey+5} {ex-8},{ey} Z", TRANG, 1.6)
    out += f'<circle cx="{ex+1.5}" cy="{ey-0.5}" r="3.4" fill="{INK}"/>'
    out += line(f"M{ex-10},{ey-4} C{ex-4},{ey-11} {ex+6},{ey-11} {ex+12},{ey-3}", 1.8, VANG)
    return out


def main():
    near_cols = [LA, TRANG, SON]
    far_cols = [LA_DARK, VANG_LIGHT, SON_DARK]
    parts = [
        ("tail", "body", 1, tail(), TAIL_ROOT, (-25, 25)),
        ("wing_far", "body", 2, wing(SHO_F, far_cols, SON_DARK, rot=0.12, scale=0.95, dots=VANG_LIGHT), SHO_F, (-70, 60)),
        ("body", None, 3, body() + head(), (330, 210), None),
        ("wing_near", "body", 4, wing(SHO_N, near_cols, SON, rot=0.0, scale=1.0), SHO_N, (-70, 60)),
    ]
    near_edge = wing_geom(SHO_N, 0.0, 1.0)
    far_edge = wing_geom(SHO_F, 0.12, 0.95)
    a_near = bez(*near_edge, 0.62)
    a_far = bez(*far_edge, 0.62)
    strings = [
        ("wing_near", "wing_near", a_near, "right", "index", 8),
        ("wing_far", "wing_far", a_far, "right", "middle", 12),
    ]
    colliders = {
        "body": {"density": 1.0, "shapes": [capsule_shape((250, 214), (400, 206), 34),
                                            circle_shape(HEAD, 24),
                                            capsule_shape((470, 140), (575, 150), 6)]},
        "tail": {"density": 0.3, "shapes": [capsule_shape((236, 212), (120, 200), 18)]},
        "wing_near": {"density": 0.3, "shapes": [capsule_shape(SHO_N, near_edge[3], 16)]},
        "wing_far": {"density": 0.3, "shapes": [capsule_shape(SHO_F, far_edge[3], 15)]},
    }
    extra = {"head": list(HEAD), "beakTip": [588, 152], "shoulders": {"near": list(SHO_N), "far": list(SHO_F)}}
    rig = build(OUT, "chim_lac", (W, H), parts, strings, colliders, extra)
    print("parts:", [p["id"] for p in rig["parts"]])


if __name__ == "__main__":
    main()
