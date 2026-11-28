// Luom, a paper-cut marionette on two strings: index finger -> shoulder, middle finger -> top of the cap.
// He runs on his own with a skipping gait (chay nhay chan sao). A quick upward flick of the hand makes
// him jump; the faster the flick, the higher, up to 3/5 of the play area. He must land before the next
// jump, and holding the hand up does not keep him in the air. `e` = feet above the path (stage px).
import type { Pt } from "../config";
import { type M, apply, clamp, mul, rotAt, smoothstep } from "../giong/mat";
import type { LuomRig } from "./data";
import { L } from "./lcfg";

export interface Circle { c: Pt; r: number }
type Angles = Record<string, number>;

const mix = (a: number, b: number, t: number) => a + (b - a) * t;
const ease = (t: number) => t * t * (3 - 2 * t);
/** Piecewise smooth curve through keys [[t, v], ...] for t in 0..1. */
function curve(keys: [number, number][], t: number): number {
  for (let i = 1; i < keys.length; i++) {
    if (t <= keys[i][0]) {
      const [t0, v0] = keys[i - 1], [t1, v1] = keys[i];
      return v0 + (v1 - v0) * ease((t - t0) / Math.max(1e-6, t1 - t0));
    }
  }
  return keys[keys.length - 1][1];
}
// one skip, s = 0..1: the "free" leg swings from behind to a high knee and comes down in front;
// the "support" leg lands in front and pushes back. The legs swap roles every skip, so it loops.
const FREE_THIGH: [number, number][] = [[0, 0.55], [0.45, -1.15], [1, -0.2]];
const FREE_SHIN: [number, number][] = [[0, 0.7], [0.4, 1.55], [1, 0.15]];
const SUP_THIGH: [number, number][] = [[0, -0.2], [1, 0.55]];
const SUP_SHIN: [number, number][] = [[0, 0.15], [0.5, 0.3], [1, 0.7]];

export class Boy {
  readonly k = L.scale;
  x = L.x;
  e = 0;
  ve = 0;
  ph = 0;                     // skip phase: one skip per PI
  run = 0;                    // 0 idle .. 1 running
  skipHz = L.skipHz;
  hitAt = -99;
  deadAt = -99;
  dead = false;
  landed = 0;                 // > 0 for a moment after landing (dust)
  jumpAt = -99;
  maxJump = 400;
  M: Record<string, M> = {};

  private parts;
  private byId;
  private hip: Pt;
  private order: number[];    // rig string index for [index finger, middle finger]
  private t = 0;

  constructor(readonly rig: LuomRig, readonly ground: number) {
    this.parts = [...rig.parts].sort((a, b) => a.z - b.z);
    this.byId = Object.fromEntries(rig.parts.map((p) => [p.id, p]));
    this.hip = { x: (rig.hips[0][0] + rig.hips[1][0]) / 2, y: rig.hips[0][1] };
    this.order = ["index", "middle"].map((f) => rig.strings.findIndex((s) => s.finger === f));
    this.reset();
  }

  reset() {
    this.e = 0; this.ve = 0; this.run = 0; this.dead = false; this.hitAt = -99; this.deadAt = -99; this.jumpAt = -99;
    this.pose();
  }

  get grounded() { return this.e <= 0.5 && this.ve <= 0; }

  // ------------------------------------------------------------------ pose
  /** Returns the angles and the hop lift (px) of the skip. */
  private angles(air: number, run: number, ph: number, t: number): [Angles, number] {
    const r = run * (1 - air);
    const idle = (1 - run) * (1 - air);
    const s = (ph % Math.PI) / Math.PI;                       // 0..1 within this skip
    const nearFree = Math.floor(ph / Math.PI) % 2 === 0;      // which leg swings this skip
    const fT = curve(FREE_THIGH, s), fS = curve(FREE_SHIN, s), sT = curve(SUP_THIGH, s), sS = curve(SUP_SHIN, s);
    const [nT, nS, fT2, fS2] = nearFree ? [fT, fS, sT, sS] : [sT, sS, fT, fS];
    const a: Angles = {};
    const g = (gv: number, av: number) => mix(gv, av, air);
    a.leg_near_thigh = g(r * nT, -1.15);
    a.leg_far_thigh = g(r * fT2, -0.45);
    a.leg_near_shin = g(r * nS + idle * 0.04, 1.6);
    a.leg_far_shin = g(r * fS2 + idle * 0.04, 1.15);
    const lean = 0.02 + 0.06 * r;
    a.leg_near_foot = g(-(lean + a.leg_near_thigh + a.leg_near_shin) * 0.8 + r * 0.25 * (nearFree ? Math.sin(s * Math.PI) : 0), 0.35);
    a.leg_far_foot = g(-(lean + a.leg_far_thigh + a.leg_far_shin) * 0.8 + r * 0.25 * (nearFree ? 0 : Math.sin(s * Math.PI)), 0.3);
    // arms swing high and opposite to the knee that comes up, like a happy child
    const swing = Math.sin(ph);                                 // + while the near leg is free
    a.arm_near_upper = g(r * (-0.35 + 0.95 * swing) + idle * 0.05 * Math.sin(t * 2), -2.0);
    a.arm_far_upper = g(r * (-0.35 - 0.95 * swing) - idle * 0.05 * Math.sin(t * 2), -1.5);
    a.arm_near_fore = g(-0.7 * run - 0.25 * idle - r * 0.35 * Math.max(0, -swing), -0.3);
    a.arm_far_fore = g(-0.7 * run - 0.25 * idle - r * 0.35 * Math.max(0, swing), -0.3);
    const hop = r * L.skipHop * Math.sin(Math.PI * clamp((s - 0.15) / 0.85, 0, 1));
    a.head = -0.1 * r + 0.06 * r * Math.sin(ph * 2 + 0.6) + idle * 0.03 * Math.sin(t * 1.7);   // head up, nodding
    a.scarf = 0.14 * Math.sin(t * 9) * (0.4 + 0.6 * run) + 0.12 * run + 0.15 * r * Math.cos(ph * 2);
    a.satchel = -0.25 * r * Math.cos(ph * 2) - air * 0.35;
    a._lean = lean;
    return [a, hop];
  }

  /** Matrices with the lowest point of the body on the path, then raised by `lift`. */
  private build(a: Angles, lift: number, fall: number, lie: number): Record<string, M> {
    const k = this.k, rig = this.rig;
    const make = (dy: number) => {
      let root: M = [k, 0, 0, k, this.x - this.hip.x * k, this.ground - rig.groundY * k + dy];
      root = mul(root, rotAt(a._lean + fall, this.hip.x, this.hip.y));
      const M: Record<string, M> = { torso: root };
      const get = (id: string): M => {
        if (M[id]) return M[id];
        const p = this.byId[id];
        return (M[id] = mul(get(p.parent!), rotAt(a[id] ?? 0, p.pivotWorld[0], p.pivotWorld[1])));
      };
      for (const p of rig.parts) get(p.id);
      return M;
    };
    const M0 = make(0);
    let low = -Infinity;
    for (const [id, an] of [["leg_near_foot", rig.ankles[0]], ["leg_far_foot", rig.ankles[1]]] as const) {
      low = Math.max(low, apply(M0[id], an[0] - 8, rig.groundY).y, apply(M0[id], an[0] + 28, rig.groundY).y);
    }
    if (fall > 0.2 || lie > 0) {
      const hc = rig.headCenter;
      low = Math.max(low, apply(M0.head, hc[0], hc[1]).y + 66 * k);
      low = Math.max(low, apply(M0.torso, 200, 330).y + 36 * k, apply(M0.torso, 200, 250).y + 36 * k);
      low = Math.max(low, apply(M0.arm_near_fore, 230, 352).y, apply(M0.leg_near_thigh, 218, 390).y + 12 * k);
    }
    const dy = this.ground - low - lift;
    // shift the matrices instead of building them again
    for (const id in M0) M0[id] = [M0[id][0], M0[id][1], M0[id][2], M0[id][3], M0[id][4], M0[id][5] + dy];
    return M0;
  }

  private tripAmount(): number {
    const s = this.t - this.hitAt;
    if (s < 0 || s > L.tripTime) return 0;
    if (s < 0.3) return smoothstep(0, 0.3, s);
    if (s < 0.7) return 1;
    return 1 - smoothstep(0.7, L.tripTime, s);
  }

  get tripping() { return this.t - this.hitAt < L.tripTime; }
  get invulnerable() { return this.t - this.hitAt < L.invuln || this.dead; }

  pose() {
    const air = smoothstep(4, 40, this.e);
    let trip = this.tripAmount(), lie = 0;
    if (this.dead) { const s = this.t - this.deadAt; trip = smoothstep(0, 0.35, s); lie = smoothstep(0.25, 0.8, s); }
    const [a, hop] = this.angles(air * (1 - trip), this.run * (1 - trip), this.ph, this.t);
    if (trip > 0) {   // stumble forward: arms out, legs kick back
      a.arm_near_upper = mix(a.arm_near_upper, -2.4, trip); a.arm_far_upper = mix(a.arm_far_upper, -2.0, trip);
      a.arm_near_fore = mix(a.arm_near_fore, -0.2, trip); a.arm_far_fore = mix(a.arm_far_fore, -0.2, trip);
      a.leg_near_thigh = mix(a.leg_near_thigh, 0.5, trip); a.leg_far_thigh = mix(a.leg_far_thigh, 0.2, trip);
      a.leg_near_shin = mix(a.leg_near_shin, 1.2, trip); a.leg_far_shin = mix(a.leg_far_shin, 0.9, trip);
      a.head = mix(a.head, -0.45, trip);
    }
    const fall = trip * 1.15 + lie * 0.4;
    this.M = this.build(a, Math.max(0, this.e) + hop * (1 - air), fall, lie);
  }

  // ------------------------------------------------------------------ physics
  /** Start a jump of `h` px (only from the path). Returns true if he jumped. */
  jump(h: number): boolean {
    if (this.dead || this.tripping || !this.grounded) return false;
    this.ve = Math.sqrt(2 * L.gravity * clamp(h, 0, this.maxJump));
    this.jumpAt = this.t;
    return true;
  }

  /** Right after take-off a faster flick can still raise the jump (never above maxJump). */
  boost(h: number) {
    if (this.t - this.jumpAt > L.boostWindow || this.ve <= 0) return;
    const v = Math.sqrt(2 * L.gravity * Math.max(0, clamp(h, 0, this.maxJump) - this.e));
    if (v > this.ve) this.ve = v;
  }

  update(dt: number, t: number) {
    this.t = t;
    this.ph += dt * this.skipHz * Math.PI * this.run;
    if (this.landed > 0) this.landed -= dt;
    if (this.dead || this.tripping) {
      this.e = Math.max(0, this.e - 900 * dt); this.ve = 0;
    } else if (this.e > 0 || this.ve > 0) {
      this.ve -= L.gravity * dt;
      this.e += this.ve * dt;
      if (this.e > this.maxJump) { this.e = this.maxJump; this.ve = Math.min(this.ve, 0); }
      if (this.e <= 0) { this.e = 0; this.ve = 0; this.landed = 0.2; }
    }
    this.pose();
  }

  // ------------------------------------------------------------------ queries
  /** String anchors in HandRole order: [index -> shoulder, middle -> cap]. */
  anchors(): Pt[] {
    return this.order.map((si) => { const s = this.rig.strings[si]; return apply(this.M[s.part], s.anchorWorld[0], s.anchorWorld[1]); });
  }

  headCircle(): Circle {
    const hc = this.rig.headCenter;
    return { c: apply(this.M.head, hc[0], hc[1]), r: 70 * this.k * 0.85 };
  }

  mouth(): Pt { return apply(this.M.head, 252, 192); }
  feet(): Pt { return { x: this.x + 14, y: this.ground - Math.max(0, this.e) }; }

  /** Collision circles (a little smaller than the paper so near misses feel fair). */
  hitCircles(): Circle[] {
    const out: Circle[] = [], k = this.k * 0.85;
    for (const p of this.rig.parts) {
      const m = this.M[p.id];
      if (!m || !p.colliders.length) continue;
      const px = p.pivotWorld[0], py = p.pivotWorld[1];
      for (const c of p.colliders) {
        if (c.type === "circle") out.push({ c: apply(m, px + c.c[0], py + c.c[1]), r: c.r * k });
        else for (let i = 0; i <= 3; i++) {
          const u = i / 3;
          out.push({ c: apply(m, px + c.a[0] + (c.b[0] - c.a[0]) * u, py + c.a[1] + (c.b[1] - c.a[1]) * u), r: c.r * k });
        }
      }
    }
    return out;
  }

  draw(ctx: CanvasRenderingContext2D) {
    const blink = !this.dead && this.t - this.hitAt < L.invuln && this.t - this.hitAt > L.tripTime * 0.5 && Math.floor(this.t * 12) % 2 === 0;
    ctx.save();
    if (blink) ctx.globalAlpha = 0.45;
    for (const p of this.parts) {
      const m = this.M[p.id];
      ctx.save();
      ctx.transform(m[0], m[1], m[2], m[3], m[4], m[5]);
      ctx.drawImage(p.img, p.origin[0], p.origin[1], p.size[0], p.size[1]);
      ctx.restore();
    }
    ctx.restore();
  }
}
