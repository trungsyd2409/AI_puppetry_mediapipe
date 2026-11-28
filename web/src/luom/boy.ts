// Luom, a paper-cut marionette on two strings: index finger -> shoulder, middle finger -> top of the cap.
//
// Height works like a real marionette. The strings never stretch, they only pull; gravity pulls the
// body down; the legs are weak, so his height is set by the strings:
//   hand at the height it had when the strings attached -> he stands and runs
//   hand lower (past a small dead zone)                 -> the strings let him sink: he crouches (duck)
//   hand higher                                         -> the strings lift him off the path
//   hand flicked up fast                                -> he keeps flying up after the hand stops (jump)
// Without strings (hand lost) his legs carry him and he keeps running, but cannot jump or duck.
// `e` = elevation in stage px: > 0 feet above the path, < 0 crouched (how far the cap came down).
import type { Pt } from "../config";
import { type M, apply, clamp, mul, rotAt, smoothstep } from "../giong/mat";
import type { Rope } from "../giong/rider";
import type { LuomRig } from "./data";
import { L } from "./lcfg";

export interface Circle { c: Pt; r: number }
type Angles = Record<string, number>;

const mix = (a: number, b: number, t: number) => a + (b - a) * t;

export class Boy {
  readonly k = L.scale;
  x = L.x;
  e = 0;
  ve = 0;
  ph = 0;
  run = 0;                    // 0 idle .. 1 running
  stepHz = L.stepHz;
  keyDuck = false;
  hitAt = -99;
  deadAt = -99;
  dead = false;
  landed = 0;                 // > 0 for a moment after landing (dust)
  M: Record<string, M> = {};
  ropes: (Rope | null)[] = [null, null];   // [index -> shoulder, middle -> head]

  private parts;
  private byId;
  private hip: Pt;
  private order: number[];    // rig string index for [index finger, middle finger]
  private base: number[] = [];          // stand anchor y per string (stage px)
  private drop: number[][] = [];        // anchor drop per string for crouch u = 0, 0.05 .. 1
  crouchMax = 1;
  private t = 0;
  private lastFloor = 0;
  private floorV = 0;

  constructor(readonly rig: LuomRig, readonly ground: number) {
    this.parts = [...rig.parts].sort((a, b) => a.z - b.z);
    this.byId = Object.fromEntries(rig.parts.map((p) => [p.id, p]));
    this.hip = { x: (rig.hips[0][0] + rig.hips[1][0]) / 2, y: rig.hips[0][1] };
    this.order = ["index", "middle"].map((f) => rig.strings.findIndex((s) => s.finger === f));
    // crouch tables: how far each anchor comes down as he crouches (standing still)
    const N = 20;
    for (let si = 0; si < rig.strings.length; si++) this.drop.push([]);
    for (let i = 0; i <= N; i++) {
      const M = this.build(this.angles(i / N, 0, 0, 0, 0), 0, 0, 0);
      rig.strings.forEach((s, si) => {
        const y = apply(M[s.part], s.anchorWorld[0], s.anchorWorld[1]).y;
        if (i === 0) this.base[si] = y;
        this.drop[si].push(y - this.base[si]);
      });
    }
    this.crouchMax = this.drop[this.order[1]][N];
    this.reset();
  }

  reset() {
    this.e = 0; this.ve = 0; this.run = 0; this.dead = false; this.hitAt = -99; this.deadAt = -99;
    this.ropes = [null, null]; this.keyDuck = false; this.lastFloor = 0; this.floorV = 0;
    this.pose();
  }

  // ------------------------------------------------------------------ pose
  private angles(u: number, air: number, run: number, ph: number, t: number): Angles {
    const r = run * (1 - u * 0.55) * (1 - air);
    const idle = (1 - run) * (1 - air);
    const a: Angles = {};
    const g = (gv: number, av: number) => mix(gv, av, air);
    a.leg_near_thigh = g(r * 0.8 * Math.sin(ph) - u * 1.6, -1.15);
    a.leg_far_thigh = g(r * 0.8 * Math.sin(ph + Math.PI) - u * 1.35, -0.45);
    a.leg_near_shin = g(r * 1.1 * Math.max(0, Math.cos(ph)) + 0.08 * run + u * 2.45, 1.6);
    a.leg_far_shin = g(r * 1.1 * Math.max(0, Math.cos(ph + Math.PI)) + 0.08 * run + u * 2.2, 1.15);
    const lean = 0.03 + 0.08 * run + u * 0.8 - air * 0.05;
    a.leg_near_foot = g(-(lean + a.leg_near_thigh + a.leg_near_shin) * 0.85, 0.35);
    a.leg_far_foot = g(-(lean + a.leg_far_thigh + a.leg_far_shin) * 0.85, 0.3);
    a.arm_near_upper = g(-0.75 * r * Math.sin(ph) - u * 0.7 + idle * 0.05 * Math.sin(t * 2), -2.0);
    a.arm_far_upper = g(-0.75 * r * Math.sin(ph + Math.PI) - u * 0.5 - idle * 0.05 * Math.sin(t * 2), -1.5);
    a.arm_near_fore = g(-1.0 * run - 0.25 * idle, -0.3);
    a.arm_far_fore = g(-1.0 * run - 0.25 * idle, -0.3);
    a.head = -0.04 + 0.05 * r * Math.sin(ph * 2) - u * 0.15 + idle * 0.03 * Math.sin(t * 1.7);
    a.scarf = 0.14 * Math.sin(t * 9) * (0.4 + 0.6 * run) + 0.1 * run;
    a.satchel = 0.2 * r * Math.sin(ph * 2) - air * 0.35;
    a._lean = lean;
    return a;
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
    // lowest point: soles, knees, and when falling the head, torso and hands
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
    return make(this.ground - low - lift);
  }

  private tripAmount(): number {
    const s = this.t - this.hitAt;
    if (s < 0 || s > L.tripTime) return 0;
    if (s < 0.3) return smoothstep(0, 0.3, s);
    if (s < 0.7) return 1;
    return 1 - smoothstep(0.7, L.tripTime, s);
  }

  get tripping() { return this.tripAmount() > 0 || (this.t - this.hitAt) < L.tripTime; }
  get invulnerable() { return this.t - this.hitAt < L.invuln || this.dead; }

  pose() {
    const u = clamp(-this.e / this.crouchMax, 0, 1);
    const air = smoothstep(6, 50, this.e);
    let trip = this.tripAmount(), lie = 0;
    if (this.dead) { const s = this.t - this.deadAt; trip = smoothstep(0, 0.35, s); lie = smoothstep(0.25, 0.8, s); }
    const a = this.angles(u * (1 - trip), air * (1 - trip), this.run * (1 - trip), this.ph, this.t);
    if (trip > 0) {   // stumble forward: arms out, legs kick back
      a.arm_near_upper = mix(a.arm_near_upper, -2.4, trip); a.arm_far_upper = mix(a.arm_far_upper, -2.0, trip);
      a.arm_near_fore = mix(a.arm_near_fore, -0.2, trip); a.arm_far_fore = mix(a.arm_far_fore, -0.2, trip);
      a.leg_near_thigh = mix(a.leg_near_thigh, 0.5, trip); a.leg_far_thigh = mix(a.leg_far_thigh, 0.2, trip);
      a.leg_near_shin = mix(a.leg_near_shin, 1.2, trip); a.leg_far_shin = mix(a.leg_far_shin, 0.9, trip);
      a.head = mix(a.head, -0.45, trip);
    }
    const fall = trip * 1.15 + lie * 0.4;
    this.M = this.build(a, Math.max(0, this.e), fall, lie);
  }

  // ------------------------------------------------------------------ physics
  /** Lowest elevation the strings allow (they only pull). */
  private floor(): number {
    let req = -Infinity, any = false;
    this.ropes.forEach((r, i) => {
      if (!r) return;
      any = true;
      const si = this.order[i], s = this.rig.strings[si];
      const ax = apply(this.M[s.part], s.anchorWorld[0], s.anchorWorld[1]).x;
      const dx = ax - r.F.x;
      const v = Math.abs(dx) < r.L ? Math.sqrt(r.L * r.L - dx * dx) : 0;
      const lowest = r.F.y + v;                  // the anchor cannot hang lower than this
      const d = lowest - this.base[si] - L.deadZone;   // > 0: room to sink, < 0: lifted
      let e: number;
      if (d <= -L.deadZone) e = -d - L.deadZone;
      else if (d <= 0) e = 0;
      else {
        const tb = this.drop[si], n = tb.length - 1;
        let u = 1;
        for (let j = 1; j <= n; j++) if (tb[j] >= d) { u = (j - 1 + (d - tb[j - 1]) / Math.max(1e-6, tb[j] - tb[j - 1])) / n; break; }
        e = -u * this.crouchMax;
      }
      req = Math.max(req, e);
    });
    if (!any) return this.keyDuck ? -this.crouchMax : 0;
    return this.keyDuck ? Math.min(req, -this.crouchMax) : req;
  }

  keyJump() { if (!this.dead && !this.tripping && this.e <= this.floor() + 2) this.ve = L.keyJump; }

  update(dt: number, t: number) {
    this.t = t;
    this.ph += dt * this.stepHz * Math.PI * this.run;
    if (this.landed > 0) this.landed -= dt;
    if (this.dead || this.tripping) {
      this.e = Math.max(0, this.e - 900 * dt); this.ve = 0;
    } else {
      const fl = this.floor();
      const vf = dt > 0 ? (fl - this.lastFloor) / dt : 0;
      this.floorV += (vf - this.floorV) * Math.min(1, dt * 20);
      this.lastFloor = fl;
      const prev = this.e, wasAir = prev > 20, taut = prev <= fl + 3;
      this.ve -= L.gravity * dt;
      this.e += this.ve * dt;
      if (this.e < fl) this.e = fl;
      // a quick flick of the hand throws him up: he keeps rising after the hand stops
      if (taut && this.floorV > L.flickMin) this.ve = Math.max(this.ve, this.floorV * L.flickBoost);
      if (this.e < -this.crouchMax) this.e = -this.crouchMax;
      if (this.e <= fl + 0.01 && !(taut && this.floorV > L.flickMin)) this.ve = (this.e - prev) / dt;
      this.ve = Math.min(L.maxRise, this.ve);
      if (wasAir && this.e < 4) this.landed = 0.2;
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
