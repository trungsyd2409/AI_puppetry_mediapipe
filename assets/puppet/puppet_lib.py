"""Shared drawing helpers + export pipeline for cut-out puppets.

Every puppet is drawn in a 400 x 720 design space, rest pose, y down,
"_L" = viewer's left. build() renders each part, auto-crops it and writes
parts/<id>.svg|png, rig.json, <name>_full.svg|png into the puppet folder.
"""
import json, math, os, subprocess
from PIL import Image

W, H = 400, 720
SCALE = 2   # PNG pixels per design unit
PAD = 4     # crop padding (design units)

# shared palette: lacquer + gold leaf + dark ink
OUTLINE = "#2A140A"
INK = "#1C0F08"
SKIN = "#E7A247"
SKIN_LIGHT = "#F6CF82"
SKIN_SHADE = "#B86A26"
RED = "#A82219"
RED_DARK = "#6A120D"
GOLD = "#E2B44A"
GOLD_LIGHT = "#F8DE8C"

MIRROR = f'transform="translate({W},0) scale(-1,1)"'


def mx(p):
    return (W - p[0], p[1])


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def angle_deg(p1, p2):
    return math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))


def capsule(p1, p2, r1, r2):
    (x1, y1), (x2, y2) = p1, p2
    L = math.hypot(x2 - x1, y2 - y1)
    ux, uy = (x2 - x1) / L, (y2 - y1) / L
    nx, ny = -uy, ux
    A = (x1 + nx * r1, y1 + ny * r1)
    B = (x2 + nx * r2, y2 + ny * r2)
    C = (x2 - nx * r2, y2 - ny * r2)
    D = (x1 - nx * r1, y1 - ny * r1)
    f = lambda p: f"{p[0]:.2f},{p[1]:.2f}"
    return (f"M{f(A)} L{f(B)} A{r2},{r2} 0 0 0 {f(C)} "
            f"L{f(D)} A{r1},{r1} 0 0 0 {f(A)} Z")


def band(p1, p2, t, r, width=7, fill=GOLD, line=RED_DARK):
    c = lerp(p1, p2, t)
    a = angle_deg(p1, p2)
    return (f'<g transform="translate({c[0]:.2f},{c[1]:.2f}) rotate({a:.2f})">'
            f'<rect x="{-width/2}" y="{-r-1}" width="{width}" height="{2*r+2}" rx="2" '
            f'fill="{fill}" stroke="{OUTLINE}" stroke-width="2"/>'
            f'<line x1="0" y1="{-r+2}" x2="0" y2="{r-2}" stroke="{line}" '
            f'stroke-width="1.6" stroke-dasharray="2 2.5"/></g>')


def dots(p1, p2, n, r=2.0, t0=0.2, t1=0.8, fill=INK, ring=GOLD):
    out = []
    for i in range(n):
        c = lerp(p1, p2, t0 + (t1 - t0) * (i / max(1, n - 1)))
        out.append(f'<circle cx="{c[0]:.2f}" cy="{c[1]:.2f}" r="{r}" fill="{fill}" '
                   f'stroke="{ring}" stroke-width="1"/>')
    return "".join(out)


def cloud(x, y, s=1.0, rot=0, color=GOLD, w=1.8):
    """Small 'van may' cloud swirl."""
    return (f'<path transform="translate({x},{y}) rotate({rot}) scale({s})" '
            f'd="M-11,5 C-13,-5 -3,-10 4,-6 C10,-2 7,6 1,5 C-3,4 -2,-1 1,-1 '
            f'M4,-6 C8,-12 16,-9 15,-3 C14,2 9,2 9,-1" '
            f'fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>')


def lotus(x, y, s=1.0, fill=GOLD, line=OUTLINE, w=1.4):
    """Small stylised lotus flower."""
    return (f'<g transform="translate({x},{y}) scale({s})" fill="{fill}" stroke="{line}" '
            f'stroke-width="{w}" stroke-linejoin="round">'
            f'<path d="M0,6 C-14,2 -16,-8 -12,-14 C-6,-8 -3,-2 0,6 Z"/>'
            f'<path d="M0,6 C14,2 16,-8 12,-14 C6,-8 3,-2 0,6 Z"/>'
            f'<path d="M0,6 C-7,-2 -6,-12 0,-20 C6,-12 7,-2 0,6 Z"/>'
            f'<path d="M-16,8 Q0,14 16,8" fill="none"/></g>')


def rivet(x, y, r=5):
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{GOLD}" stroke="{OUTLINE}" stroke-width="2"/>'
            f'<circle cx="{x}" cy="{y}" r="{r*0.36:.2f}" fill="{OUTLINE}"/>')


def limb(pid, p1, p2, r1, r2, fill=SKIN, shade=SKIN_SHADE, stitch=GOLD_LIGHT, pattern=""):
    """Tapered limb: fill, side shading, dashed stitch, ink outline."""
    body = capsule(p1, p2, r1, r2)
    inner = capsule(p1, p2, max(r1 - 6, 3), max(r2 - 6, 3))
    a = math.radians(angle_deg(p1, p2) + 90)
    off = (math.cos(a) * r1 * 0.75, math.sin(a) * r1 * 0.75)
    shade_path = capsule((p1[0] + off[0], p1[1] + off[1]),
                         (p2[0] + off[0] * r2 / r1, p2[1] + off[1] * r2 / r1),
                         r1 * 0.55, r2 * 0.55)
    return (f'<clipPath id="clip_{pid}"><path d="{body}"/></clipPath>'
            f'<path d="{body}" fill="{fill}"/>'
            f'<path d="{shade_path}" fill="{shade}" opacity="0.55" clip-path="url(#clip_{pid})"/>'
            f'<path d="{inner}" fill="none" stroke="{stitch}" stroke-width="1.4" '
            f'stroke-dasharray="4 3" opacity="0.9"/>'
            f'{pattern}'
            f'<path d="{body}" fill="none" stroke="{OUTLINE}" stroke-width="3.5"/>')


def hand(wrist, direction_deg, thumb_side=1, s=1.0, fill=SKIN, light=SKIN_LIGHT):
    """Open hand; local +x points away from the wrist."""
    fingers = ""
    for i, y in enumerate([-8.5, -3, 2.5, 8]):
        ln = [19, 24, 23, 18][i]
        fingers += (f'<path d="{capsule((8, y), (8 + ln, y * 1.3), 4.8, 4.2)}" '
                    f'fill="{fill}" stroke="{OUTLINE}" stroke-width="2.6"/>')
    ty = 12 * thumb_side
    thumb = (f'<path d="{capsule((0, ty * 0.6), (13, ty * 1.75), 5.4, 4.6)}" '
             f'fill="{fill}" stroke="{OUTLINE}" stroke-width="2.6"/>')
    palm = (f'<ellipse cx="5" cy="0" rx="16" ry="15" fill="{fill}" '
            f'stroke="{OUTLINE}" stroke-width="3"/>'
            f'<ellipse cx="6" cy="0" rx="6" ry="7" fill="{light}" opacity="0.6"/>')
    return (f'<g transform="translate({wrist[0]:.2f},{wrist[1]:.2f}) rotate({direction_deg:.2f}) scale({s})">'
            f'{fingers}{thumb}{palm}</g>')


def svg_doc(inner, vb):
    x, y, w, h = vb
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}" '
            f'width="{w}" height="{h}">{inner}</svg>')


def render(svg_path, png_path, scale=SCALE):
    subprocess.run(["rsvg-convert", "-z", str(scale), "-o", png_path, svg_path], check=True)


def circle(c, r):
    return {"type": "circle", "c": list(c), "r": r}


def capsule_shape(a, b, r):
    return {"type": "capsule", "a": list(a), "b": list(b), "r": r}


def _local_shape(shape, pivot):
    """World design coords -> coords relative to the part pivot."""
    out = dict(shape)
    for k in ("c", "a", "b"):
        if k in shape:
            out[k] = [round(shape[k][0] - pivot[0], 2), round(shape[k][1] - pivot[1], 2)]
    return out


def build(out_dir, name, parts, strings, colliders=None):
    """parts: (id, parent, z, svg, pivot_world, limitDeg|None)
    strings: (id, part, anchor_world, finger, mediapipe_landmark)
    colliders: {part_id: {"density": float, "shapes": [circle()/capsule_shape() in world design coords]}}"""
    colliders = colliders or {}
    parts_dir = os.path.join(out_dir, "parts")
    os.makedirs(parts_dir, exist_ok=True)
    rig_parts = []
    for pid, parent, z, inner, pivot, limits in parts:
        tmp_svg = os.path.join(out_dir, f"_tmp_{pid}.svg")
        tmp_png = os.path.join(out_dir, f"_tmp_{pid}.png")
        with open(tmp_svg, "w") as f:
            f.write(svg_doc(inner, (0, 0, W, H)))
        render(tmp_svg, tmp_png)
        bx0, by0, bx1, by1 = Image.open(tmp_png).getbbox()
        x0 = max(0, math.floor(bx0 / SCALE) - PAD)
        y0 = max(0, math.floor(by0 / SCALE) - PAD)
        x1 = min(W, math.ceil(bx1 / SCALE) + PAD)
        y1 = min(H, math.ceil(by1 / SCALE) + PAD)
        vb = (x0, y0, x1 - x0, y1 - y0)
        with open(os.path.join(parts_dir, f"{pid}.svg"), "w") as f:
            f.write(svg_doc(inner, vb))
        render(os.path.join(parts_dir, f"{pid}.svg"), os.path.join(parts_dir, f"{pid}.png"))
        os.remove(tmp_svg); os.remove(tmp_png)
        rig_parts.append({
            "id": pid, "parent": parent, "z": z,
            "svg": f"parts/{pid}.svg", "png": f"parts/{pid}.png",
            "origin": [x0, y0], "size": [vb[2], vb[3]],
            "pivot": [round(pivot[0] - x0, 2), round(pivot[1] - y0, 2)],
            "pivotWorld": [round(pivot[0], 2), round(pivot[1], 2)],
            "limitDeg": list(limits) if limits else None,
            "density": colliders.get(pid, {}).get("density", 1.0),
            "colliders": [_local_shape(sh, pivot) for sh in colliders.get(pid, {}).get("shapes", [])],
        })
    by_id = {p["id"]: p for p in rig_parts}
    rig = {
        "name": name,
        "units": "design units (1 unit = 2 px in PNG); y points down; _L = viewer's left; colliders are relative to the part pivot",
        "canvas": [W, H],
        "pngScale": SCALE,
        "feetY": max(p["origin"][1] + p["size"][1] for p in rig_parts) - PAD,
        "parts": rig_parts,
        "strings": [
            {"id": sid, "part": part,
             "anchor": [round(p[0] - by_id[part]["origin"][0], 2),
                        round(p[1] - by_id[part]["origin"][1], 2)],
             "anchorWorld": [round(p[0], 2), round(p[1], 2)],
             "finger": finger, "mpLandmark": lm}
            for sid, part, p, finger, lm in strings
        ],
    }
    with open(os.path.join(out_dir, "rig.json"), "w") as f:
        json.dump(rig, f, indent=2)
    full = "".join(p[3] for p in sorted(parts, key=lambda p: p[2]))
    full_svg = os.path.join(out_dir, f"{name}_full.svg")
    with open(full_svg, "w") as f:
        f.write(svg_doc(full, (0, 0, W, H)))
    render(full_svg, os.path.join(out_dir, f"{name}_full.png"))
    return rig
