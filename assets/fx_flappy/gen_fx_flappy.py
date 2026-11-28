"""Flappy chim lac sprites in Dong Ho style.

  bamboo_body : bundle of 3 bamboo stalks tied with red cord, tiles vertically (period = BODY_H)
  bamboo_cap  : the open end of a column (cut stalks, cord, sprouting leaves); anchor = where it
                joins the body. Bottom columns use it as is, top columns flip it vertically in code.
  feather_0..2: loose feathers for the crash burst
  impact      : star burst when the bird hits something
fx.json: size, anchor, pngScale per sprite (design units, PNG at 2x).
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dongho_lib import *  # noqa

OUT = os.path.dirname(os.path.abspath(__file__))
MANIFEST = {}
COL_W = 150           # column width (collision width in code)
BODY_H = 240          # vertical tile period
STALKS = [(-46, 25, 0), (0, 27, 27), (46, 24, 53)]   # x, radius, node phase


def save(name, inner, w, h, anchor, scale=2, extra=None):
    """inner drawn with the anchor at (0, 0)."""
    write_svg_png(os.path.join(OUT, name), f'<g transform="translate({anchor[0]},{anchor[1]})">{inner}</g>',
                  (0, 0, w, h), scale)
    MANIFEST[name] = {"png": f"{name}.png", "size": [w, h], "anchor": list(anchor), "pngScale": scale, **(extra or {})}


def stalk(x, r, y0, y1, phase, nodes=True):
    d = f"M{x-r},{y0} L{x-r},{y1} L{x+r},{y1} L{x+r},{y0} Z"
    out = f'<path d="{d}" fill="{LA}"/>'
    out += f'<path d="M{x+r*0.35},{y0} L{x+r*0.35},{y1} L{x+r},{y1} L{x+r},{y0} Z" fill="{LA_DARK}"/>'
    out += brush(f"M{x-r*0.45},{y0} L{x-r*0.45},{y1}", 2.0, VANG_LIGHT, taper=0, var=0.1)
    out += brush(f"M{x-r},{y0} L{x-r},{y1}", 3.6, INK, taper=0, var=0.05)
    out += brush(f"M{x+r},{y0} L{x+r},{y1}", 3.6, INK, taper=0, var=0.05)
    if nodes:
        y = phase - 80
        while y < y1 + 80:
            if y0 - 10 < y < y1 + 10:
                out += line(f"M{x-r+2},{y-2} C{x-r/2},{y+4} {x+r/2},{y+4} {x+r-2},{y-2}", 3.0)
                out += line(f"M{x-r+4},{y+6} C{x-r/2},{y+10} {x+r/2},{y+10} {x+r-4},{y+6}", 1.4, LA_DARK)
                # tiny bud on alternate nodes
                if int((y - phase) / 80) % 2 == 0:
                    out += leaf(x + r - 2, y + 2, -30, 0.28, LA, LA_DARK)
            y += 80
    return out


def cord(y, w=COL_W + 12):
    out = ink(f"M{-w/2},{y-9} C{-w/4},{y-4} {w/4},{y-4} {w/2},{y-9} L{w/2},{y+7} C{w/4},{y+12} {-w/4},{y+12} {-w/2},{y+7} Z",
              SON, 2.8)
    out += dots_row((-w / 2, y + 1), (w / 2, y + 1), 9, 2.2, VANG)
    return out


def bamboo_body():
    out = ""
    # draw beyond the tile and let the viewBox clip, so the outline continues across the seam
    for x, r, ph in STALKS:
        out += stalk(x, r, -20, BODY_H + 20, ph)
    out += cord(BODY_H * 0.5)
    return out


def bamboo_cap():
    """y = 0 joins the body; the open end points up (negative y)."""
    out = ""
    tops = [-70, -96, -60]
    for (x, r, ph), top in zip(STALKS, tops):
        out += stalk(x, r, top, 20, ph + 40, nodes=False)
        # diagonal cut showing the hollow ivory inside
        cut = f"M{x-r},{top+8} C{x-r/2},{top-6} {x+r/2},{top-12} {x+r},{top-10} C{x+r/2},{top+6} {x-r/2},{top+14} {x-r},{top+8} Z"
        out += ink(cut, TRANG, 2.6)
        out += line(f"M{x-r+6},{top+4} C{x},{top-4} {x+r/2},{top-6} {x+r-6},{top-6}", 1.4, VANG)
        out += line(f"M{x-r+2},{top+40} C{x-r/2},{top+46} {x+r/2},{top+46} {x+r-2},{top+40}", 3.0)
    out += cord(-30)
    # leaves sprouting from the top of the bundle
    for x, y, rot, s, c in [(-58, -40, -150, 0.7, LA), (60, -50, -25, 0.75, LA_DARK),
                            (-10, -88, -110, 0.6, LA_DARK), (30, -70, -60, 0.55, LA)]:
        out += leaf(x, y, rot, s, c, LA_DARK if c == LA else LA)
    return out


def feather(k):
    cols = [(LA, TRANG), (SON, TRANG), (TRANG, SON)][k]
    return strand((-34, 4), (-12, -6), (12, -8), (36, -2), 9, cols[0], 16) + \
        line("M-40,6 L-30,4", 2.0, cols[1])


def impact():
    out = ""
    for i in range(10):
        a = i * 36
        L = 58 if i % 2 == 0 else 36
        out += f'<g transform="rotate({a})">' + ink(f"M0,-7 L{L},0 L0,7 Z", VANG if i % 2 == 0 else TRANG, 2.4) + '</g>'
    return out + ink("M-16,0 A16,16 0 1 1 16,0 A16,16 0 1 1 -16,0 Z", TRANG, 2.4) + swirl(0, 0, 0.5, 0, sw=1.6)


def main():
    save("bamboo_body", bamboo_body(), COL_W + 20, BODY_H, (COL_W / 2 + 10, 0), extra={"tileH": BODY_H, "colW": COL_W})
    save("bamboo_cap", bamboo_cap(), COL_W + 80, 140, (COL_W / 2 + 40, 120), extra={"colW": COL_W, "capTop": -100})
    for k in range(3):
        save(f"feather_{k}", feather(k), 90, 34, (45, 17))
    save("impact", impact(), 140, 140, (70, 70))
    with open(os.path.join(OUT, "fx.json"), "w") as f:
        json.dump(MANIFEST, f, indent=2)
    print(len(MANIFEST), "sprites")


if __name__ == "__main__":
    main()
