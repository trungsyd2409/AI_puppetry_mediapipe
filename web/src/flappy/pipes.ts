// Bamboo columns: top and bottom bundles with a fixed gap, moving left at a fixed speed.
import { drawSprite, type Sprite } from "../giong/data";
import type { Circle } from "./bird";
import { F } from "./fcfg";

interface Col { x: number; gy: number; scored: boolean }

const rand = (a: number, b: number) => a + Math.random() * (b - a);

export class Pipes {
  cols: Col[] = [];
  private halfW: number;
  private tile: number;

  constructor(private fx: Record<string, Sprite>, private groundY: number) {
    const body = fx.bamboo_body as Sprite & { colW?: number };
    this.halfW = ((body.colW ?? 150) * F.colScale) / 2;
    this.tile = fx.bamboo_body.size[1] * F.colScale;
    this.reset();
  }

  reset() {
    this.cols = [];
    for (let i = 0; i < 5; i++) this.cols.push({ x: F.firstColumnX + i * F.spacing, gy: rand(...F.gapRange), scored: false });
  }

  /** Move left; returns how many columns the bird passed this frame. */
  update(dt: number, birdX: number): number {
    let passed = 0;
    for (const c of this.cols) {
      c.x -= F.speed * dt;
      if (!c.scored && c.x + this.halfW < birdX) { c.scored = true; passed++; }
    }
    const last = Math.max(...this.cols.map((c) => c.x));
    for (const c of this.cols) if (c.x < -200) { c.x = last + F.spacing; c.gy = rand(...F.gapRange); c.scored = false; }
    return passed;
  }

  hit(circles: Circle[]): boolean {
    for (const c of this.cols) {
      const top = c.gy - F.gap / 2, bot = c.gy + F.gap / 2;
      for (const { c: p, r } of circles) {
        const nx = Math.max(c.x - this.halfW, Math.min(p.x, c.x + this.halfW));
        if (Math.hypot(p.x - nx, p.y - Math.min(p.y, top)) < r) return true;   // top column (y <= top)
        if (Math.hypot(p.x - nx, p.y - Math.max(p.y, bot)) < r) return true;   // bottom column (y >= bot)
      }
    }
    return false;
  }

  draw(ctx: CanvasRenderingContext2D) {
    const s = F.colScale, tile = this.tile;
    for (const c of this.cols) {
      if (c.x < -200 || c.x > 1800) continue;
      const top = c.gy - F.gap / 2, bot = c.gy + F.gap / 2;
      // the cap's open end sits on the gap edge; the body continues from the cap's joint
      for (let y = bot + 100 * s; y < this.groundY + tile; y += tile) drawSprite(ctx, this.fx.bamboo_body, c.x, y, s);
      drawSprite(ctx, this.fx.bamboo_cap, c.x, bot + 100 * s, s);
      ctx.save(); ctx.translate(c.x, top - 100 * s); ctx.scale(1, -1);
      for (let y = 0; y < top + tile; y += tile) drawSprite(ctx, this.fx.bamboo_body, 0, y, s);
      drawSprite(ctx, this.fx.bamboo_cap, 0, 0, s);
      ctx.restore();
    }
  }
}
