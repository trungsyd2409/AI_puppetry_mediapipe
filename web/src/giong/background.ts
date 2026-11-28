// Parallax layers + animated props (flags, fire, smoke, bamboo, grass, clouds, crows, sun, catapults).
// Each prop scrolls with its layer; the props keep animating when the horse stands still.
import { drawSprite, type GStage, type PropDef, type Sprite } from "./data";

const TILE = 1600;

interface Puff { age: number; dx: number; rot: number; spin: number }
interface Ember { age: number; x: number; vy: number; ph: number }
interface Bird { x: number; y: number; vx: number; s: number; ph: number }
interface Stone { age: number }

interface PropRT {
  def: PropDef; seed: number; acc: number;
  puffs: Puff[]; embers: Ember[]; birds: Bird[]; stones: Stone[]; lastU: number;
}

const num = (v: number | [number, number] | undefined, d: number) => (Array.isArray(v) ? v[0] : v ?? d);
const rand = (a: number, b: number) => a + Math.random() * (b - a);

export class Background {
  private props = new Map<string, PropRT[]>();

  constructor(private stage: GStage, private fx: Record<string, Sprite>) {
    for (const def of stage.props) {
      const rt: PropRT = { def, seed: (def.x * 0.017) % 6.28, acc: 0, puffs: [], embers: [], birds: [], stones: [], lastU: 0 };
      if (def.type === "flock") {
        const ys = def.y as [number, number], vxs = def.vx as [number, number], ss = def.scale as [number, number];
        rt.birds = Array.from({ length: def.count ?? 4 }, (_, i) => ({
          x: 200 + i * 330 + Math.random() * 120, y: rand(ys[0], ys[1]), vx: rand(vxs[0], vxs[1]),
          s: rand(ss[0], ss[1]), ph: Math.random() * 3,
        }));
      }
      const list = this.props.get(def.layer) ?? [];
      list.push(rt);
      this.props.set(def.layer, list);
    }
  }

  update(dt: number, t: number) {
    for (const list of this.props.values()) for (const p of list) {
      const d = p.def;
      if (d.type === "smoke") {
        p.acc += dt * (d.rate ?? 2);
        while (p.acc > 1) { p.acc -= 1; p.puffs.push({ age: 0, dx: (Math.random() - 0.5) * 14, rot: Math.random() * 6, spin: (Math.random() - 0.5) * 0.4 }); }
        for (const q of p.puffs) q.age += dt;
        p.puffs = p.puffs.filter((q) => q.age < (d.life ?? 5));
        if (d.embers && Math.random() < dt * 6) p.embers.push({ age: 0, x: (Math.random() - 0.5) * 40, vy: 30 + Math.random() * 40, ph: Math.random() * 6 });
        for (const e of p.embers) e.age += dt;
        p.embers = p.embers.filter((e) => e.age < 2.2);
      } else if (d.type === "catapult") {
        const u = ((t + p.seed) % (d.period ?? 4.5)) / (d.period ?? 4.5);
        if (p.lastU < 0.66 && u >= 0.66) p.stones.push({ age: 0 });
        p.lastU = u;
        for (const s of p.stones) s.age += dt;
        p.stones = p.stones.filter((s) => s.age < 2.4);
      } else if (d.type === "flock") {
        const ys = d.y as [number, number];
        for (const b of p.birds) { b.x += b.vx * dt; if (b.x < -120) { b.x = 1720; b.y = rand(ys[0], ys[1]); } }
      }
    }
  }

  drawBack(ctx: CanvasRenderingContext2D, scroll: number, t: number) {
    for (const l of this.stage.layers) if (!l.front) this.drawLayer(ctx, l, scroll, t);
  }

  drawFront(ctx: CanvasRenderingContext2D, scroll: number, t: number) {
    for (const l of this.stage.layers) if (l.front) this.drawLayer(ctx, l, scroll, t);
  }

  /** Draw only the named layers (in stage order), with their props. */
  drawIds(ctx: CanvasRenderingContext2D, scroll: number, t: number, ids: string[]) {
    for (const l of this.stage.layers) if (ids.includes(l.id)) this.drawLayer(ctx, l, scroll, t);
  }

  private drawLayer(ctx: CanvasRenderingContext2D, l: GStage["layers"][number], scroll: number, t: number) {
    const off = -scroll * l.parallax;
    if (l.img) {
      const x = -((scroll * l.parallax) % TILE);
      ctx.drawImage(l.img, x, 0);
      if (l.parallax) ctx.drawImage(l.img, x + TILE, 0);
    }
    for (const p of this.props.get(l.id) ?? []) this.drawProp(ctx, p, off, t);
  }

  private sp(k: string | undefined) { return k ? this.stage.sprites[k] : undefined; }

  private drawProp(ctx: CanvasRenderingContext2D, p: PropRT, off: number, t: number) {
    const d = p.def;
    const y = num(d.y, 0), s = num(d.scale, 1);
    if (d.type === "flock") {
      for (const b of p.birds) drawSprite(ctx, this.sp(d.frames![Math.floor(t * (d.fps ?? 7) + b.ph * 3) % 3]), b.x, b.y + Math.sin(t * 2 + b.ph) * 8, b.s);
      return;
    }
    if (d.type === "spin") { drawSprite(ctx, this.sp(d.sprite), d.x, y, s, (t * (d.speed ?? 6) * Math.PI) / 180); return; }
    let x0 = d.x + off;
    if (d.type === "drift") x0 += num(d.vx, -8) * t;
    const x = ((x0 % TILE) + TILE) % TILE;
    const each = (margin: number, fn: (xx: number) => void) => { fn(x); if (x < margin) fn(x + TILE); if (x > TILE - margin) fn(x - TILE); };

    switch (d.type) {
      case "anim": {
        const fr = d.frames!;
        const k = fr[Math.floor(t * (d.fps ?? 8) + p.seed * 3) % fr.length];
        each(200, (xx) => drawSprite(ctx, this.sp(k), xx, y, s));
        break;
      }
      case "sway": {
        const sp = d.speed ?? 1.5, amp = d.amp ?? 2;
        const a = ((amp * Math.sin(t * sp + p.seed) + amp * 0.6 * Math.sin(t * sp * 2.3 + p.seed * 2)) * Math.PI) / 180;
        each(260, (xx) => drawSprite(ctx, this.sp(d.sprite), xx, y, s, a));
        break;
      }
      case "drift":
        each(200, (xx) => drawSprite(ctx, this.sp(d.sprite), xx, y + Math.sin(t * 0.6 + p.seed) * (d.bob ?? 4), s));
        break;
      case "smoke":
        each(300, (xx) => this.drawSmoke(ctx, p, xx, y, s));
        break;
      case "catapult":
        each(200, (xx) => this.drawCatapult(ctx, p, xx, y, s, t));
        break;
    }
  }

  private drawSmoke(ctx: CanvasRenderingContext2D, p: PropRT, x: number, y: number, s: number) {
    const d = p.def, life = d.life ?? 5, wind = this.stage.wind;
    for (const e of p.embers) {
      ctx.fillStyle = e.age < 1.2 ? "#D7A443" : "#A63A25";
      ctx.globalAlpha = 1 - e.age / 2.2;
      ctx.fillRect(x + e.x + Math.sin(e.age * 3 + e.ph) * 10 + wind * e.age * 0.8, y + 30 - e.vy * e.age, 4, 4);
    }
    ctx.globalAlpha = 1;
    for (const q of p.puffs) {
      const k = q.age / life;
      const sc = s * (0.45 + (d.grow ?? 1.6) * k);
      const px = x + q.dx + wind * q.age * 0.9 + Math.sin(q.age * 1.3 + q.rot) * 6;
      const py = y - (d.rise ?? 45) * q.age;
      drawSprite(ctx, this.sp(d.sprite), px, py, sc, q.rot + q.spin * q.age, Math.min(1, q.age * 3) * (1 - k * k));
    }
  }

  private drawCatapult(ctx: CanvasRenderingContext2D, p: PropRT, x: number, y: number, s: number, t: number) {
    const period = p.def.period ?? 4.5;
    const u = ((t + p.seed) % period) / period;
    let ang: number;   // unmirrored: cup rests down-left, swings over to the right
    if (u < 0.55) ang = -0.42;
    else if (u < 0.66) { const v = (u - 0.55) / 0.11; ang = -0.42 + 2.3 * v * v; }
    else if (u < 0.75) ang = 1.88 - 0.12 * Math.sin(((u - 0.66) / 0.09) * Math.PI);
    else { const v = (u - 0.75) / 0.25; ang = 1.88 - 2.3 * (v * v * (3 - 2 * v)); }
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(-1, 1);          // mirrored so it throws toward the hero on the left
    drawSprite(ctx, this.fx.catapult_base, 0, 0, s);
    drawSprite(ctx, this.fx.catapult_arm, 0, -73 * s, s, ang);
    ctx.restore();
    for (const st of p.stones) {
      const a = st.age;
      const sx = x - 60 * s - 260 * a, sy = y - 170 * s - 230 * a + 120 * a * a;
      drawSprite(ctx, this.fx["trail_" + (Math.floor(t * 14) % 3)], sx, sy, 0.38, Math.atan2(-230 + 240 * a, -260) + Math.PI);
      drawSprite(ctx, this.fx.shell, sx, sy, 0.38, t * 5);
    }
  }
}
