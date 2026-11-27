// The horse + boy + bamboo while alive (not a ragdoll):
//  - gallop is a procedural animation; the ground scrolls under it
//  - the two front legs hang on fixed-length strings from the right hand (they only pull, may sag);
//    lifting both makes the horse rear,
//    and a rearing horse stops galloping
//  - the bamboo is a free rod (position based dynamics) held by two fixed-length strings from the left hand;
//    the boy's two hands always hold it (arm reach constraint + 2-bone IK)
//  - the tail is drawn in thin strips that bend, so it waves softly
import type { Pt } from "../config";
import type { GData, GPart, GRig } from "./data";
import { G } from "./gcfg";
import { type M, angleOf, apply, clamp, dist, lerpPt, mul, place, rotAt, smoothstep } from "./mat";

export interface Rope { F: Pt; L: number }          // fingertip (stage px) and fixed length
export interface RopeInputs { legs: (Rope | null)[]; bamboo: (Rope | null)[] }   // [index, middle]

export type HitKind = "bamboo" | "stomp" | "body";
export interface HitShape { kind: HitKind; part: string; a: Pt; b: Pt; r: number }   // capsule (a == b: circle)

interface LegDef { up: GPart; low: GPart; sh: Pt; kn: Pt; anchor: Pt; hoof: Pt; key: "front_near" | "front_far" }
interface LegRT { th: number; fold: number; lift: number }

const P = (a: [number, number]): Pt => ({ x: a[0], y: a[1] });

export class Rider {
  readonly k = G.puppetScale;
  readonly rig: GRig;
  readonly parts: GPart[];
  readonly byId = new Map<string, GPart>();
  readonly floorY: number;
  private base: M;

  // animation state
  phase = 0;
  run = 1;            // 0..1 gallop strength
  rear = 0;           // 0..1
  private tailA = 0; private tailV = 0;
  private prevBodyAng = 0; private bodyAngV = 0;
  legRT: Record<string, LegRT> = { front_near: { th: 0, fold: 0, lift: 0 }, front_far: { th: 0, fold: 0, lift: 0 } };
  private legs: LegDef[] = [];

  // bamboo rod (stage px): e1 = bottom end, e2 = leafy end
  e1: Pt = { x: 0, y: 0 }; e2: Pt = { x: 0, y: 0 };
  private p1: Pt = { x: 0, y: 0 }; private p2: Pt = { x: 0, y: 0 };
  private bamLen = 0;
  private tNear = 0; private tFar = 0; private tTop = 0; private tBot = 0;
  private gripN = 0; private gripF = 0;   // where the hands hold the rod: always centred on the pole
  private restShift: Pt = { x: 0, y: 0 }; // rest pose slid along the pole so its middle sits in the hands
  private bamA: Pt; private bamB: Pt;

  // arms
  private arms: { up: GPart; fore: GPart; sho: Pt; elb: Pt; wri: Pt; a: number; b: number; bend: number; t: () => number }[] = [];

  /** World matrices of every part (design -> stage px). */
  M: Record<string, M> = {};
  ropes: RopeInputs = { legs: [null, null], bamboo: [null, null] };

  constructor(data: GData) {
    this.rig = data.rig;
    this.parts = [...data.rig.parts].sort((a, b) => a.z - b.z);
    for (const p of this.parts) this.byId.set(p.id, p);
    this.floorY = data.stage.floorY;
    const k = this.k;
    this.base = [k, 0, 0, k, G.horseX - 330 * k, this.floorY - this.rig.groundY * k];

    for (const key of ["front_near", "front_far"] as const) {
      const up = this.byId.get(`${key}_upper`)!, low = this.byId.get(`${key}_lower`)!;
      const st = this.rig.strings.find((s) => s.id === key)!;
      const kn = P(low.pivotWorld);
      this.legs.push({ up, low, key, sh: P(up.pivotWorld), kn, anchor: P(st.anchorWorld), hoof: { x: kn.x - 4, y: this.rig.groundY - 10 } });
    }

    // bamboo geometry in design units
    this.bamA = P(this.rig.bambooEnds[0]); this.bamB = P(this.rig.bambooEnds[1]);
    const ab = { x: this.bamB.x - this.bamA.x, y: this.bamB.y - this.bamA.y };
    const L2 = ab.x * ab.x + ab.y * ab.y;
    const proj = (p: Pt) => ((p.x - this.bamA.x) * ab.x + (p.y - this.bamA.y) * ab.y) / L2;
    this.bamLen = Math.sqrt(L2) * k;
    this.tNear = proj(P(this.rig.gripNear));
    this.tFar = proj(P(this.rig.gripFar));
    // the visible (near) fist always holds the exact midpoint of the pole; the far fist (behind the body)
    // sits the same distance below it as in the drawing. The rest pose is slid so the midpoint is in the fist.
    const shift = this.tNear - 0.5;
    this.restShift = { x: ab.x * shift, y: ab.y * shift };
    this.gripN = 0.5; this.gripF = 0.5 - (this.tNear - this.tFar);
    this.tTop = proj(P(this.rig.strings.find((s) => s.id === "bamboo_top")!.anchorWorld));
    this.tBot = proj(P(this.rig.strings.find((s) => s.id === "bamboo_bottom")!.anchorWorld));

    for (const side of ["near", "far"] as const) {
      const up = this.byId.get(`boy_arm_${side}_upper`)!, fore = this.byId.get(`boy_arm_${side}_fore`)!;
      const sho = P(up.pivotWorld), elb = P(fore.pivotWorld), wri = P(side === "near" ? this.rig.gripNear : this.rig.gripFar);
      const cross = (wri.x - sho.x) * (elb.y - sho.y) - (wri.y - sho.y) * (elb.x - sho.x);
      this.arms.push({ up, fore, sho, elb, wri, a: dist(sho, elb), b: dist(elb, wri), bend: Math.sign(cross) || 1,
        t: side === "near" ? () => this.gripN : () => this.gripF });
    }
    this.reset();
  }

  reset() {
    this.phase = 0; this.run = 1; this.rear = 0; this.tailA = 0.3; this.tailV = 0;
    for (const l of Object.values(this.legRT)) { l.th = 0; l.fold = 0; l.lift = 0; }
    this.ropes = { legs: [null, null], bamboo: [null, null] };
    this.pose(0, 0);
    [this.e1, this.e2] = this.restEnds();
    this.p1 = { ...this.e1 }; this.p2 = { ...this.e2 };
  }

  /** Current gallop speed in stage px/s. */
  get speed() { return G.runSpeed * this.run; }

  // ------------------------------------------------------------------ pose
  private legMatrices(body: M, def: LegDef, th: number, fold: number) {
    const up = mul(body, rotAt(th, def.sh.x, def.sh.y));
    const low = mul(up, rotAt(fold, def.kn.x, def.kn.y));
    return { up, low };
  }

  private static liftFold(th: number) { return clamp(-th * 1.2, 0, 1.6); }

  /** Solve one front leg so its rope (fixed length L, may go slack) is never longer than L.
   *  Slack rope: the leg keeps galloping. Taut rope: the angle that fits, nearest the gallop pose and the
   *  previous angle (no jumps). */
  private solveLeg(body: M, def: LegDef, th0: number, fold0: number, rope: Rope | null, prev: number): LegRT {
    const at = (th: number) => {
      const fold = Math.max(fold0, Rider.liftFold(th));
      return { th, fold, p: apply(this.legMatrices(body, def, th, fold).low, def.anchor.x, def.anchor.y) };
    };
    let best = at(th0);
    if (rope && dist(best.p, rope.F) > rope.L) {
      let bestCost = Infinity;
      for (let th = -1.75; th <= 0.6; th += 0.025) {
        const c = at(th);
        const over = Math.max(0, dist(c.p, rope.F) - rope.L);
        const cost = over * 10 + Math.abs(th - th0) + 0.5 * Math.abs(th - prev);
        if (cost < bestCost) { bestCost = cost; best = c; }
      }
    }
    // hoof height in the body frame -> lift 0..1
    const loc = mul(rotAt(best.th, def.sh.x, def.sh.y), rotAt(best.fold, def.kn.x, def.kn.y));
    const hy = apply(loc, def.hoof.x, def.hoof.y).y;
    return { th: best.th, fold: best.fold, lift: clamp((def.hoof.y - hy) / G.liftFull, 0, 1) };
  }

  /** Compute every part matrix for this frame. */
  pose(t: number, dt: number) {
    const R = this.rig, run = this.run, ph = this.phase, rear = this.rear;
    const ang: Record<string, number> = {};
    const sw = (o: number) => Math.sin(ph + o);
    // hind legs + neck + boy (procedural)
    ang.hind_near_upper = run * 0.45 * sw(Math.PI) + rear * 0.42 * G.rearAngle / 0.5;
    ang.hind_far_upper = run * 0.45 * sw(Math.PI + 0.7) + rear * 0.42 * G.rearAngle / 0.5;
    ang.hind_near_lower = run * -0.8 * Math.max(0, Math.cos(ph + Math.PI)) - rear * 0.1;
    ang.hind_far_lower = run * -0.8 * Math.max(0, Math.cos(ph + Math.PI + 0.7)) - rear * 0.1;
    ang.neck = run * 0.08 * sw(1) - rear * 0.25;
    ang.boy_torso = run * 0.05 * sw(-0.6) + rear * 0.22;
    ang.boy_head = 0.06 * Math.sin(t * 2) - rear * 0.15;
    ang.boy_thigh = -rear * 0.1;
    ang.boy_shin = run * 0.12 * sw(-1) + rear * 0.2;

    const bob = run * -7 * Math.abs(Math.sin(ph));
    const bodyAng = -G.rearAngle * rear + run * 0.025 * sw(0.5);
    const hindHoof = { x: 246, y: R.groundY };
    const body = mul(mul(this.base, [1, 0, 0, 1, 0, bob]), rotAt(bodyAng, hindHoof.x, hindHoof.y));
    if (dt > 0) { this.bodyAngV = (bodyAng - this.prevBodyAng) / dt; this.prevBodyAng = bodyAng; }

    // front legs on ropes
    for (const [i, def] of this.legs.entries()) {
      const off = def.key === "front_near" ? 0 : 0.7;
      const th0 = run * 0.55 * Math.sin(ph + off);
      const fold0 = run * 1.1 * Math.max(0, -Math.cos(ph + off));
      const rt = this.solveLeg(body, def, th0, fold0, this.ropes.legs[i], this.legRT[def.key].th);
      this.legRT[def.key] = rt;
      ang[`${def.key}_upper`] = rt.th;
      ang[`${def.key}_lower`] = rt.fold;
    }

    // tail: damped spring, streams back while galloping and swings when the body tips
    if (dt > 0) {
      const target = 0.32 * run + 0.1 * Math.sin(t * 2.1) - rear * 0.1;
      const acc = 38 * (target - this.tailA) - 6 * this.tailV - this.bodyAngV * 3;
      this.tailV += acc * dt; this.tailA += this.tailV * dt;
    }
    ang.tail = this.tailA;

    const M: Record<string, M> = {};
    const get = (p: GPart): M => {
      if (M[p.id]) return M[p.id];
      const parent = p.parent ? get(this.byId.get(p.parent)!) : body;
      return (M[p.id] = mul(parent, rotAt(ang[p.id] ?? 0, p.pivotWorld[0], p.pivotWorld[1])));
    };
    for (const p of this.parts) if (!p.id.startsWith("boy_arm") && p.id !== "bamboo") get(p);
    this.M = M;
  }

  // ------------------------------------------------------------------ bamboo
  private restEnds() {
    const m = this.M.boy_torso, s = this.restShift;
    return [apply(m, this.bamA.x + s.x, this.bamA.y + s.y), apply(m, this.bamB.x + s.x, this.bamB.y + s.y)];
  }

  private shoulders() { return this.arms.map((a) => apply(this.M.boy_torso, a.sho.x, a.sho.y)); }

  /** Move the point at parameter t on the rod by `d` (rod treated as rigid, weights by lever). */
  private pushRod(t: number, dx: number, dy: number) {
    const w = (1 - t) * (1 - t) + t * t;
    const w1 = (1 - t) / w, w2 = t / w;
    this.e1.x += dx * w1; this.e1.y += dy * w1;
    this.e2.x += dx * w2; this.e2.y += dy * w2;
  }

  /** Point on rod at t must stay within `L` of `F` (exact = true: exactly L, the rope also pushes). */
  private maxDist(t: number, F: Pt, L: number, exact = false) {
    const g = lerpPt(this.e1, this.e2, t);
    const d = dist(g, F);
    if ((!exact && d <= L) || d < 1e-6) return;
    const c = (d - L) / d;
    this.pushRod(t, (F.x - g.x) * c, (F.y - g.y) * c);
  }

  stepBamboo(dt: number, leftAttached: boolean) {
    const B = G.bamboo;
    for (const [e, p] of [[this.e1, this.p1], [this.e2, this.p2]] as const) {
      const vx = (e.x - p.x) * B.damping, vy = (e.y - p.y) * B.damping;
      p.x = e.x; p.y = e.y;
      e.x += vx; e.y += vy + B.gravity * dt * dt;
    }
    const [r1, r2] = this.restEnds();
    const h = leftAttached ? B.holdAttached : B.holdFree;
    this.e1.x += (r1.x - this.e1.x) * h; this.e1.y += (r1.y - this.e1.y) * h;
    this.e2.x += (r2.x - this.e2.x) * h; this.e2.y += (r2.y - this.e2.y) * h;
    const sh = this.shoulders();
    for (let it = 0; it < B.iters; it++) {
      // rigid rod
      const d = dist(this.e1, this.e2) || 1, c = (d - this.bamLen) / d / 2;
      const dx = (this.e2.x - this.e1.x) * c, dy = (this.e2.y - this.e1.y) * c;
      this.e1.x += dx; this.e1.y += dy; this.e2.x -= dx; this.e2.y -= dy;
      // fixed-length strings, exact distance (index -> leafy tip, middle -> base)
      const [ri, rm] = this.ropes.bamboo;
      if (ri) this.maxDist(this.tTop, ri.F, ri.L, true);
      if (rm) this.maxDist(this.tBot, rm.F, rm.L, true);
      // both hands keep hold of it: grips stay within arm reach
      this.arms.forEach((a, i) => this.maxDist(a.t(), sh[i], (a.a + a.b) * this.k * 0.97));
      for (const e of [this.e1, this.e2]) if (e.y > this.floorY - 4) e.y = this.floorY - 4;
      this.keepSides();
    }
    this.keepSides();
    // final hard step: slide the whole pole (length and angle unchanged) so its midpoint is inside the
    // near arm's reach, so the near fist is always drawn exactly on the midpoint
    // (and not closer than the folded arm allows, or the fist could not touch it either)
    const near = this.arms[0], reach = (near.a + near.b) * this.k * 0.97;
    const minR = Math.abs(near.a - near.b) * this.k + 2;
    const mid = lerpPt(this.e1, this.e2, 0.5), d = dist(mid, sh[0]) || 1e-6;
    const want = Math.min(reach, Math.max(minR, d));
    if (want !== d) {
      const c = (d - want) / d, dx = (sh[0].x - mid.x) * c, dy = (sh[0].y - mid.y) * c;
      this.e1.x += dx; this.e1.y += dy; this.e2.x += dx; this.e2.y += dy;
    }
  }

  /** The index-finger end (leafy tip, e2) always stays on the RIGHT of the middle-finger end (base, e1):
   *  the pole may tilt up to G.bamboo.maxTilt from horizontal but never flips over, so the strings never swap. */
  private keepSides() {
    const dx = this.e2.x - this.e1.x, dy = this.e2.y - this.e1.y;
    const ang = Math.atan2(dy, dx), lim = G.bamboo.maxTilt;
    if (Math.abs(ang) <= lim) return;
    const a = ang > 0 ? lim : -lim;   // nearest allowed angle (tip up -> -lim, tip down -> +lim)
    const c = lerpPt(this.e1, this.e2, 0.5), h = this.bamLen / 2;
    this.e1 = { x: c.x - Math.cos(a) * h, y: c.y - Math.sin(a) * h };
    this.e2 = { x: c.x + Math.cos(a) * h, y: c.y + Math.sin(a) * h };
  }

  // ------------------------------------------------------------------ arms + bamboo matrices
  finishPose() {
    const k = this.k;
    const bAng = Math.atan2(this.e2.y - this.e1.y, this.e2.x - this.e1.x) - Math.atan2(this.bamB.y - this.bamA.y, this.bamB.x - this.bamA.x);
    this.M.bamboo = place(this.e1, bAng, k, this.bamA);
    const sh = this.shoulders();
    this.arms.forEach((arm, i) => {
      const S = sh[i], Gp = lerpPt(this.e1, this.e2, arm.t());
      const a = arm.a * k, b = arm.b * k;
      const d = clamp(dist(S, Gp), Math.abs(a - b) + 0.5, a + b - 0.01);
      const base = Math.atan2(Gp.y - S.y, Gp.x - S.x);
      const A = Math.acos(clamp((a * a + d * d - b * b) / (2 * a * d), -1, 1));
      const eA = base + arm.bend * A;
      const E = { x: S.x + Math.cos(eA) * a, y: S.y + Math.sin(eA) * a };
      const restUp = Math.atan2(arm.elb.y - arm.sho.y, arm.elb.x - arm.sho.x);
      const restFore = Math.atan2(arm.wri.y - arm.elb.y, arm.wri.x - arm.elb.x);
      this.M[arm.up.id] = place(S, eA - restUp, k, arm.sho);
      this.M[arm.fore.id] = place(E, Math.atan2(Gp.y - E.y, Gp.x - E.x) - restFore, k, arm.elb);
    });
  }

  // ------------------------------------------------------------------ per frame
  update(dt: number, t: number, legsAttached: boolean) {
    const ln = this.legRT.front_near.lift, lf = this.legRT.front_far.lift;
    const target = legsAttached ? smoothstep(G.rearOn[0], G.rearOn[1], Math.min(ln, lf)) : 0;
    this.rear += (target - this.rear) * Math.min(1, dt * 7);
    const runT = 1 - smoothstep(G.stopRear[0], G.stopRear[1], this.rear);
    this.run += (runT - this.run) * Math.min(1, dt * 5);
    this.phase += dt * G.gallopHz * 2 * Math.PI * Math.max(0.15, this.run) * (this.run > 0.02 ? 1 : 0);
    this.pose(t, dt);
  }

  // ------------------------------------------------------------------ queries
  /** Anchor points (stage px) of the 4 strings: legs[index, middle], bamboo[index, middle]. */
  anchors() {
    const st = (id: string) => this.rig.strings.find((s) => s.id === id)!;
    const leg = (id: string) => { const s = st(id); return apply(this.M[s.part], s.anchorWorld[0], s.anchorWorld[1]); };
    return {
      legs: [leg("front_near"), leg("front_far")],
      bamboo: [lerpPt(this.e1, this.e2, this.tTop), lerpPt(this.e1, this.e2, this.tBot)],   // [index, middle]
    };
  }

  hoofPoints(): Pt[] {
    return this.legs.map((l) => apply(this.M[l.low.id], l.hoof.x, l.hoof.y));
  }

  hindHoofPoints(): Pt[] {
    return ["hind_near_lower", "hind_far_lower"].map((id) => {
      const p = this.byId.get(id)!;
      return apply(this.M[id], p.pivotWorld[0] + 14, this.rig.groundY - 10);
    });
  }

  hitShapes(): HitShape[] {
    const out: HitShape[] = [];
    const k = this.k;
    out.push({ kind: "bamboo", part: "bamboo", a: { ...this.e1 }, b: { ...this.e2 }, r: 10 * k });
    for (const p of this.parts) {
      if (p.id === "bamboo" || !this.M[p.id]) continue;
      const m = this.M[p.id];
      const isFront = p.id === "front_near_lower" || p.id === "front_far_lower";
      const leg = isFront ? this.legRT[p.id.replace("_lower", "")] : null;
      // only a hoof the player lifts (or a rearing horse) stamps shells out; the gallop alone does not
      const pulled = !!this.ropes.legs[0] || !!this.ropes.legs[1];
      const kind: HitKind = leg && (this.rear > 0.35 || (pulled && leg.lift > 0.5)) ? "stomp" : "body";
      for (const c of p.colliders) {
        const px = p.pivotWorld[0], py = p.pivotWorld[1];
        if (c.type === "circle") {
          const q = apply(m, px + c.c[0], py + c.c[1]);
          out.push({ kind, part: p.id, a: q, b: q, r: c.r * k * (kind === "stomp" ? 1.6 : 1) });
        } else {
          out.push({ kind, part: p.id, a: apply(m, px + c.a[0], py + c.a[1]), b: apply(m, px + c.b[0], py + c.b[1]),
            r: c.r * k * (kind === "stomp" ? 1.8 : 1) });
        }
      }
    }
    if (this.rear > 0.4) for (const h of this.hoofPoints()) out.push({ kind: "stomp", part: "hoof", a: h, b: h, r: 34 });
    return out;
  }

  // ------------------------------------------------------------------ draw
  draw(ctx: CanvasRenderingContext2D, t: number) {
    for (const p of this.parts) {
      const m = this.M[p.id];
      if (!m) continue;
      if (p.id === "tail") { this.drawTail(ctx, p, m, t); continue; }
      ctx.save();
      ctx.transform(m[0], m[1], m[2], m[3], m[4], m[5]);
      ctx.drawImage(p.img, p.origin[0], p.origin[1], p.size[0], p.size[1]);
      ctx.restore();
    }
  }

  /** Tail in horizontal strips; each strip shifts sideways by a wave that grows toward the tip. */
  private drawTail(ctx: CanvasRenderingContext2D, p: GPart, m: M, t: number) {
    const [ox, oy] = p.origin, [w, h] = p.size;
    const rootY = this.rig.tailRoot[1];
    const sc = this.rig.pngScale;
    const step = 3;
    ctx.save();
    ctx.transform(m[0], m[1], m[2], m[3], m[4], m[5]);
    for (let yy = 0; yy < h; yy += step) {
      const u = clamp((oy + yy - rootY) / (oy + h - rootY), 0, 1);
      const wave = Math.sin(t * 5.2 - u * 3.4) * (6 + 6 * this.run) + Math.sin(t * 2.3 - u * 2) * 4;
      const stream = -this.run * 26 * u + this.bodyAngV * 10 * u;
      const dx = Math.pow(u, 1.6) * (wave + stream);
      ctx.drawImage(p.img, 0, yy * sc, w * sc, (step + 1) * sc, ox + dx, oy + yy, w, step + 1);
    }
    ctx.restore();
  }

  /** Body rotation now (rad), used by the ragdoll to inherit the pose. */
  bodyAngle() { return angleOf(this.M.body); }
}
