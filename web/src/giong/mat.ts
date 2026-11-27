// 2D affine matrices in canvas order [a, b, c, d, e, f]: x' = a x + c y + e, y' = b x + d y + f.
import type { Pt } from "../config";

export type M = [number, number, number, number, number, number];

export const I: M = [1, 0, 0, 1, 0, 0];

export const mul = (m: M, n: M): M => [
  m[0] * n[0] + m[2] * n[1], m[1] * n[0] + m[3] * n[1],
  m[0] * n[2] + m[2] * n[3], m[1] * n[2] + m[3] * n[3],
  m[0] * n[4] + m[2] * n[5] + m[4], m[1] * n[4] + m[3] * n[5] + m[5],
];

/** Rotation by `a` around (px, py). */
export function rotAt(a: number, px: number, py: number): M {
  const c = Math.cos(a), s = Math.sin(a);
  return [c, s, -s, c, px - c * px + s * py, py - s * px - c * py];
}

export const translate = (x: number, y: number): M => [1, 0, 0, 1, x, y];

export const apply = (m: M, x: number, y: number): Pt => ({ x: m[0] * x + m[2] * y + m[4], y: m[1] * x + m[3] * y + m[5] });

export const angleOf = (m: M) => Math.atan2(m[1], m[0]);

/** Absolute matrix: design point `pd` lands on stage point `ps`, rotated by `a`, uniform scale `k`. */
export function place(ps: Pt, a: number, k: number, pd: Pt): M {
  const c = Math.cos(a) * k, s = Math.sin(a) * k;
  return [c, s, -s, c, ps.x - (c * pd.x - s * pd.y), ps.y - (s * pd.x + c * pd.y)];
}

export const dist = (a: Pt, b: Pt) => Math.hypot(a.x - b.x, a.y - b.y);
export const lerpPt = (a: Pt, b: Pt, t: number): Pt => ({ x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t });
export const clamp = (v: number, a: number, b: number) => Math.min(b, Math.max(a, v));
export const smoothstep = (a: number, b: number, v: number) => { const t = clamp((v - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };

/** Distance from p to segment ab. */
export function segDist(p: Pt, a: Pt, b: Pt): number {
  const dx = b.x - a.x, dy = b.y - a.y;
  const L2 = dx * dx + dy * dy || 1;
  const t = clamp(((p.x - a.x) * dx + (p.y - a.y) * dy) / L2, 0, 1);
  return Math.hypot(p.x - (a.x + dx * t), p.y - (a.y + dy * t));
}
