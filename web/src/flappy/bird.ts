// The chim lac puppet. Two fixed-length, always-straight strings hold its wings:
//   index finger -> near wing, middle finger -> far wing.
// Height: the body sits where both strings keep their length with the wings near their flap pose,
// so the bird follows the hand up and down. Wings: each wing angle is solved so its string keeps its
// length (within a few px, which lets the wings keep a small natural flap). Moving one finger
// relative to the other beats that wing.
// No strings (hand lost or crashed): the bird falls.
import type { Pt } from "../config";
import { type M, apply, clamp, dist, mul, place, rotAt } from "../giong/mat";
import type { Rope } from "../giong/rider";
import type { BirdRig } from "./data";
import { F } from "./fcfg";

export type BirdMode = "hover" | "rope" | "fall" | "dead";
export interface Circle { c: Pt; r: number }

const PIV = { x: 330, y: 210 };     // design point placed at (x, y)

export class Bird {
  readonly k = F.birdScale;
  x = F.birdX;
  y = F.hoverY;
  vy = 0;
  pitch = 0;
  spin = 0;
  mode: BirdMode = "hover";
  phase = 0;
  wing = { near: -0.3, far: -0.3 };
  M: Record<string, M> = {};
  ropes: (Rope | null)[] = [null, null];
  private parts;
  private sho: Record<string, Pt> = {};

  constructor(readonly rig: BirdRig) {
    this.parts = [...rig.parts].sort((a, b) => a.z - b.z);
    for (const p of rig.parts) if (p.id.startsWith("wing")) this.sho[p.id] = { x: p.pivotWorld[0], y: p.pivotWorld[1] };
    this.reset();
  }

  reset() {
    this.y = F.hoverY; this.vy = 0; this.pitch = 0; this.spin = 0; this.mode = "hover";
    this.ropes = [null, null];
    this.pose(0, this.wing.near, this.wing.far, 0);
  }

  private flapAngle(off = 0) { return -0.45 + 0.6 * Math.sin(this.phase - off); }

  private root(y: number, pitch: number): M { return place({ x: this.x, y }, pitch, this.k, PIV); }

  private wingM(root: M, id: string, a: number): M { const s = this.sho[id]; return mul(root, rotAt(a, s.x, s.y)); }

  private anchor(root: M, i: number, a: number): Pt {
    const st = this.rig.strings[i];
    return apply(this.wingM(root, st.part, a), st.anchorWorld[0], st.anchorWorld[1]);
  }

  pose(t: number, aN: number, aF: number, pitch: number) {
    const root = this.root(this.y, pitch + this.spin);
    this.M = { body: root, wing_near: this.wingM(root, "wing_near", aN), wing_far: this.wingM(root, "wing_far", aF),
      tail: mul(root, rotAt(0.08 * Math.sin(t * 3) + clamp(-this.vy / 3000, -0.2, 0.2), 236, 214)) };
  }

  update(dt: number, t: number) {
    const flapSpeed = this.mode === "fall" ? 3.2 : this.mode === "dead" ? 0.5 : 1;
    this.phase += dt * F.flapHz * 2 * Math.PI * flapSpeed;
    const prevY = this.y;
    const restA = [this.flapAngle(0), this.flapAngle(0.35)];
    let aN = restA[0], aF = restA[1];

    if (this.mode === "hover") {
      this.y = F.hoverY + Math.sin(t * 2) * 12;
    } else if (this.mode === "rope") {
      // 1) height: where both strings keep their length with the wings in the flap pose
      const root = this.root(this.y, this.pitch);
      let sum = 0, n = 0;
      this.ropes.forEach((r, i) => {
        if (!r) return;
        const A = this.anchor(root, i, restA[i]);
        const dx = A.x - r.F.x;
        const below = Math.abs(dx) < r.L ? Math.sqrt(r.L * r.L - dx * dx) : 0;
        sum += this.y + (r.F.y + below - A.y); n++;
      });
      if (n) {
        const target = sum / n;
        const step = F.maxClimb * dt;
        this.y += clamp(target - this.y, -step, step);
      }
      // 2) each wing: angle that keeps its string length, close to the natural flap and the last angle
      const root2 = this.root(this.y, this.pitch);
      const solved = [this.wing.near, this.wing.far];
      this.ropes.forEach((r, i) => {
        if (!r) { solved[i] = restA[i]; return; }
        let best = solved[i], bestCost = Infinity;
        for (let a = -1.4; a <= 0.75; a += 0.02) {
          const err = Math.abs(dist(this.anchor(root2, i, a), r.F) - r.L);
          const cost = Math.max(0, err - F.wingTolerance) * 10 + Math.abs(a - restA[i]) + 0.5 * Math.abs(a - solved[i]);
          if (cost < bestCost) { bestCost = cost; best = a; }
        }
        solved[i] = best;
      });
      [aN, aF] = solved;
    } else {
      // falling: gravity, wings flailing, nose tips down
      this.vy += F.gravity * dt;
      this.y += this.vy * dt;
      if (this.mode === "dead") this.spin += dt * 2.5;
    }
    if (this.mode !== "fall" && this.mode !== "dead") this.vy = dt > 0 ? (this.y - prevY) / dt : 0;
    const pitchT = this.mode === "dead" ? 0.9 : clamp(this.vy / 700, -0.45, 0.6);
    this.pitch += (pitchT - this.pitch) * Math.min(1, dt * 8);
    this.wing.near = aN; this.wing.far = aF;
    this.pose(t, aN, aF, this.pitch);
  }

  /** String anchor points on the wings (stage px), [index -> near wing, middle -> far wing]. */
  anchors(): Pt[] {
    return this.rig.strings.map((s) => apply(this.M[s.part], s.anchorWorld[0], s.anchorWorld[1]));
  }

  /** Collision circles: body, head and beak (wings and tail are feathers, they do not count). */
  hitCircles(): Circle[] {
    const out: Circle[] = [];
    const body = this.rig.parts.find((p) => p.id === "body")!;
    const m = this.M.body, k = this.k;
    for (const c of body.colliders) {
      const px = body.pivotWorld[0], py = body.pivotWorld[1];
      if (c.type === "circle") out.push({ c: apply(m, px + c.c[0], py + c.c[1]), r: c.r * k });
      else for (let i = 0; i <= 4; i++) {
        const u = i / 4;
        out.push({ c: apply(m, px + c.a[0] + (c.b[0] - c.a[0]) * u, py + c.a[1] + (c.b[1] - c.a[1]) * u), r: c.r * k });
      }
    }
    return out;
  }

  draw(ctx: CanvasRenderingContext2D) {
    for (const p of this.parts) {
      const m = this.M[p.id];
      if (!m) continue;
      ctx.save();
      ctx.transform(m[0], m[1], m[2], m[3], m[4], m[5]);
      ctx.drawImage(p.img, p.origin[0], p.origin[1], p.size[0], p.size[1]);
      ctx.restore();
    }
  }
}
