// Fire-stone shells thrown from the enemy side (right), explosions, sparks and hoof dust.
import type { Pt } from "../config";
import { drawSprite, type Sprite } from "./data";
import { G } from "./gcfg";
import { clamp, segDist } from "./mat";
import type { HitShape } from "./rider";

interface Shell { x: number; y: number; vx: number; vy: number; spin: number; high: boolean }
interface Boom { x: number; y: number; age: number; spark: boolean; scale: number }
interface Dust { x: number; y: number; vx: number; vy: number; age: number; life: number; k: number; rot: number; s: number }

export interface ShellEvent { kind: "block" | "stomp" | "hit" | "ground"; x: number; y: number; part: string; vx: number; vy: number }

export class Shells {
  shells: Shell[] = [];
  private booms: Boom[] = [];
  private dust: Dust[] = [];
  private nextShot = 1.5;
  private lastHigh = false;

  constructor(private fx: Record<string, Sprite>, private floorY: number) {}

  clear() { this.shells = []; this.nextShot = 1.8; }

  /** difficulty 0..1 */
  private fire(diff: number, force?: boolean) {
    // alternate mostly, with some repeats so it is not fully predictable
    const high = force ?? (Math.random() < 0.3 ? this.lastHigh : !this.lastHigh);
    this.lastHigh = high;
    const tgt = high ? G.shell.high : G.shell.low;
    const T = G.shell.flight[0] + (G.shell.flight[1] - G.shell.flight[0]) * diff;
    const x0 = 1700, y0 = 380 + Math.random() * 160;
    const tx = tgt.x + (Math.random() - 0.5) * 30, ty = tgt.y + (Math.random() - 0.5) * 30;
    const g = G.shell.gravity;
    this.shells.push({ x: x0, y: y0, vx: (tx - x0) / T, vy: (ty - y0 - 0.5 * g * T * T) / T, spin: Math.random() * 6, high });
  }

  spawn(type: "high" | "low") { this.fire(0.3, type === "high"); }

  /** Move shells and test them against the rider. Returns what happened this frame. */
  update(dt: number, playing: boolean, playTime: number, shapes: HitShape[] | null): ShellEvent[] {
    const ev: ShellEvent[] = [];
    if (playing) {
      const diff = clamp(playTime / G.shell.rampTime, 0, 1);
      this.nextShot -= dt;
      if (this.nextShot <= 0) {
        this.fire(diff);
        const iv = G.shell.interval[0] + (G.shell.interval[1] - G.shell.interval[0]) * diff;
        this.nextShot = iv * (0.8 + Math.random() * 0.4);
      }
    }
    const R = G.shell.radius;
    for (let i = this.shells.length - 1; i >= 0; i--) {
      const s = this.shells[i];
      s.vy += G.shell.gravity * dt;
      s.x += s.vx * dt; s.y += s.vy * dt; s.spin += dt * 6;
      let hit: ShellEvent | null = null;
      if (shapes) {
        // bamboo and stomping hooves are checked first: they protect the rider
        const order = [...shapes].sort((a, b) => rank(a.kind) - rank(b.kind));
        for (const h of order) {
          if (segDist(s, h.a, h.b) <= h.r + R) {
            hit = { kind: h.kind === "bamboo" ? "block" : h.kind === "stomp" ? "stomp" : "hit", x: s.x, y: s.y, part: h.part, vx: s.vx, vy: s.vy };
            break;
          }
        }
      }
      if (!hit && s.y > this.floorY - 10) hit = { kind: "ground", x: s.x, y: this.floorY - 10, part: "", vx: s.vx, vy: s.vy };
      if (!hit && s.x < -200) { this.shells.splice(i, 1); continue; }
      if (hit) {
        this.shells.splice(i, 1);
        this.booms.push({ x: hit.x, y: hit.y, age: 0, spark: hit.kind === "block" || hit.kind === "stomp", scale: hit.kind === "hit" ? 1.1 : 0.85 });
        ev.push(hit);
      }
    }
    for (const b of this.booms) b.age += dt;
    this.booms = this.booms.filter((b) => b.age < 0.6);
    for (const d of this.dust) { d.age += dt; d.x += d.vx * dt; d.y += d.vy * dt; d.vy += 30 * dt; d.vx *= 0.97; }
    this.dust = this.dust.filter((d) => d.age < d.life);
    return ev;
  }

  /** Hoof strike: a few small puffs that drift back with the ground and fade. */
  kickDust(p: Pt, groundSpeed: number, n = 2) {
    for (let i = 0; i < n; i++) {
      this.dust.push({ x: p.x + (Math.random() - 0.5) * 16, y: this.floorY - 4 - Math.random() * 6,
        vx: -groundSpeed * 0.75 - 20 - Math.random() * 40, vy: -25 - Math.random() * 35,
        age: 0, life: 0.55 + Math.random() * 0.35, k: Math.floor(Math.random() * 2), rot: (Math.random() - 0.5) * 0.6, s: 0.55 + Math.random() * 0.3 });
    }
  }

  /** Big smoke burst (respawn). */
  burst(p: Pt) { this.booms.push({ x: p.x, y: p.y, age: 0.36, spark: false, scale: 1.7 }); }

  drawDust(ctx: CanvasRenderingContext2D) {
    for (const d of this.dust) {
      const u = d.age / d.life;
      drawSprite(ctx, this.fx[`dust_puff_${d.k}`], d.x, d.y, d.s * (0.7 + u * 0.9), d.rot + u * 0.4, (1 - u) * Math.min(1, d.age * 8));
    }
  }

  draw(ctx: CanvasRenderingContext2D, t: number) {
    for (const s of this.shells) {
      const ang = Math.atan2(s.vy, s.vx) + Math.PI;
      drawSprite(ctx, this.fx["trail_" + (Math.floor(t * 14) % 3)], s.x, s.y, G.shell.scale, ang);
      drawSprite(ctx, this.fx.shell, s.x, s.y, G.shell.scale, s.spin);
    }
    for (const b of this.booms) {
      const u = b.age / 0.6;
      if (b.spark && u < 0.35) drawSprite(ctx, this.fx.spark, b.x, b.y, 1.1 + u, u * 2);
      drawSprite(ctx, this.fx["explode_" + Math.min(4, Math.floor(u * 5))], b.x, b.y, b.scale, 0, 1 - Math.max(0, u - 0.8) * 5);
    }
  }
}

const rank = (k: string) => (k === "bamboo" ? 0 : k === "stomp" ? 1 : 2);
