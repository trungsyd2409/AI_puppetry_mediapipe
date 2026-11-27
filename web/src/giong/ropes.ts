// One hand = one role (left hand: bamboo, right hand: front legs) with two strings (index, middle).
// DETACHED -> (hand seen N frames) -> GROW (strings grow from the fingertips) -> ATTACHED.
// When the strings reach the puppet their length is fixed for good: they never stretch and never sag,
// so the anchor follows the fingertip both ways. Hand gone for loseAfter s -> strings are cut.
import type { Pt } from "../config";
import { PointFilter } from "../filter";
import { CFG } from "../config";
import type { Control } from "../puppet";
import { G } from "./gcfg";
import { dist, lerpPt, smoothstep } from "./mat";
import type { Rope } from "./rider";

export type RoleState = "DETACHED" | "GROW" | "ATTACHED";
const SLOTS = [1, 2];   // tips[] index: 1 = index finger, 2 = middle finger

export class HandRole {
  state: RoleState = "DETACHED";
  stateTime = 0;
  attachedTime = 0;
  tips: Pt[] = [{ x: 0, y: 0 }, { x: 0, y: 0 }];
  lens = [0, 0];
  private seen = 0;
  private lastSeen = -Infinity;
  private lastSample = 0;
  private filters = SLOTS.map(() => new PointFilter(CFG.euro.minCutoff, CFG.euro.beta, CFG.euro.dCutoff));
  private cutAt = -Infinity;
  private dropped: Pt[] = [];

  /** sag = the strings only pull (leg strings); otherwise they also push and stay straight. */
  constructor(readonly name: "bamboo" | "legs", readonly color: string, readonly sag = false) {}

  /** Seconds the hand has been continuously visible (used to start the game). */
  presentTime = 0;

  onHand(c: Control | null, now: number, allow = true) {
    if (!allow && this.state !== "DETACHED") this.cut(now);
    if (c) {
      const dt = this.lastSample ? Math.max(1e-3, (now - this.lastSample) / 1000) : 1 / 30;
      this.lastSample = now;
      SLOTS.forEach((s, i) => (this.tips[i] = this.filters[i].filter(c.tips[s], dt)));
      this.lastSeen = now;
      this.seen++;
      if (allow && this.state === "DETACHED" && this.seen >= G.attachFrames) this.set("GROW");
    } else {
      this.seen = 0;
      if (this.state !== "DETACHED" && (now - this.lastSeen) / 1000 > G.loseAfter) this.cut(now);
    }
  }

  private set(s: RoleState) { this.state = s; this.stateTime = 0; }

  cut(now: number) {
    if (this.state === "DETACHED") return;
    this.dropped = this.tips.map((p) => ({ ...p }));
    this.cutAt = now;
    this.set("DETACHED");
    this.attachedTime = 0;
    this.filters.forEach((f) => f.reset());
    this.lastSample = 0;
  }

  update(dt: number, anchors: Pt[], now: number) {
    this.stateTime += dt;
    this.presentTime = (now - this.lastSeen) / 1000 < G.loseAfter ? this.presentTime + dt : 0;
    if (this.state === "GROW" && this.stateTime >= G.growTime) {
      this.lens = anchors.map((a, i) => dist(a, this.tips[i]));
      this.set("ATTACHED");
    }
    this.attachedTime = this.state === "ATTACHED" ? this.attachedTime + dt : 0;
  }

  /** Ropes that act on the puppet (only once attached). */
  ropes(): (Rope | null)[] {
    return this.state === "ATTACHED" ? this.tips.map((F, i) => ({ F, L: this.lens[i] })) : [null, null];
  }

  get attached() { return this.state === "ATTACHED"; }

  draw(ctx: CanvasRenderingContext2D, anchors: Pt[], now: number) {
    ctx.save();
    ctx.lineCap = "round";
    if (this.state === "DETACHED") {
      const age = (now - this.cutAt) / 1000;
      const alpha = 1 - age / 1.2;
      if (alpha > 0) anchors.forEach((a, i) => {
        const from = this.dropped[i] ?? a;
        const top = lerpPt(from, { x: a.x + 20 * Math.sin(i * 2.1), y: a.y - 50 }, smoothstep(0, 0.6, age));
        const ctrl = { x: (a.x + top.x) / 2 + 25 * Math.sin(age * 6 + i), y: Math.max(a.y, top.y) + 24 };
        ctx.globalAlpha = alpha;
        cord(ctx, top, ctrl, a, this.color);
      });
    } else {
      const grow = this.state === "GROW" ? smoothstep(0, 1, this.stateTime / G.growTime) : 1;
      anchors.forEach((a, i) => {
        const tip = this.tips[i];
        const end = lerpPt(tip, a, grow);
        const mid = lerpPt(tip, end, 0.5);
        if (this.sag && grow >= 1) {   // slack string hangs; taut string is straight
          const d = dist(tip, a), L = this.lens[i];
          mid.y += Math.sqrt(Math.max(0, L * L - d * d)) * 0.5;
        }
        cord(ctx, tip, mid, end, this.color);
        ctx.fillStyle = this.color;
        ctx.beginPath(); ctx.arc(tip.x, tip.y, 7, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = "#241A14"; ctx.lineWidth = 2; ctx.stroke();
        if (grow >= 1) {
          ctx.fillStyle = "#D7A443";
          ctx.beginPath(); ctx.arc(a.x, a.y, 5, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
        }
      });
    }
    ctx.restore();
  }
}

/** A thick hemp cord: dark outline, light core, coloured thread along it. */
function cord(ctx: CanvasRenderingContext2D, a: Pt, c: Pt, b: Pt, color: string) {
  const path = () => { ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.quadraticCurveTo(c.x, c.y, b.x, b.y); ctx.stroke(); };
  ctx.strokeStyle = "#241A14"; ctx.lineWidth = G.rope.width; path();
  ctx.strokeStyle = "#EAD9AE"; ctx.lineWidth = G.rope.core; path();
  ctx.strokeStyle = color; ctx.lineWidth = 1.2; ctx.setLineDash([6, 8]); path(); ctx.setLineDash([]);
}
