// Snow-mountain camp scene: falling snow in two depths, gusts of cold wind (streaks, blown
// snow along the ground, a push on the puppet), pennants waving on the tent poles, a
// flickering campfire with sparks and smoke, glowing tents and a slow aurora.
import { CFG } from "./config";
import type { Stage } from "./assets";
import { drawCloth, pennant, type SceneFx } from "./cloth";

const INK = "#1B2433";
const FLAGS = ["#2F5FA8", "#B8302A", "#2F5FA8"];
const WIND_DIR = 1;   // the cold wind always blows left -> right, so the flags never flip

const rand = (a: number, b: number) => a + Math.random() * (b - a);
const pick = (r: number[]) => rand(r[0], r[1]);

interface Flake { x: number; y: number; r: number; vy: number; sway: number; phase: number }
interface Puff { x: number; y: number; r: number; t: number; life: number; vx: number }
interface Spark { x: number; y: number; vx: number; vy: number; t: number }
interface Gust { x: number; y: number; vx: number; len: number; phase: number }
interface Drift { x: number; y: number; vx: number; vy: number; t: number; r: number }

export class SnowFx implements SceneFx {
  private time = 0;
  private flagPhase = 0;
  private gustSmooth = 0;
  private gustStart = -100;
  private nextGust = 4;
  private far: Flake[] = [];
  private near: Flake[] = [];
  private smoke: Puff[] = [];
  private sparks: Spark[] = [];
  private streaks: Gust[] = [];
  private drifts: Drift[] = [];
  private nextPuff = 0;
  private poles: { x: number; top: number; side: number }[];
  private fire: { x: number; y: number };
  private glows: { x: number; y: number; r: number }[];
  private aurora: { y0: number; y1: number };

  constructor(private stage: Stage) {
    this.poles = stage.meta.poles;
    this.fire = stage.meta.fire;
    this.glows = stage.meta.tentGlows;
    this.aurora = stage.meta.aurora;
    const [w, h] = stage.size;
    const make = (n: number, r: [number, number], vy: [number, number]): Flake[] =>
      Array.from({ length: n }, () => ({
        x: rand(0, w), y: rand(-40, h), r: rand(...r), vy: rand(...vy), sway: rand(0.6, 1.6), phase: rand(0, 6),
      }));
    this.far = make(170, [0.9, 2.0], [22, 45]);
    this.near = make(70, [2.4, 4.6], [60, 110]);
  }

  get gust() {
    const u = (this.time - this.gustStart) / CFG.ambience.gustDuration;
    return u < 0 || u > 1 ? 0 : Math.sin(Math.PI * u) ** 2;
  }

  windAccel() { return this.gust * WIND_DIR * CFG.ambience.windAccel; }

  // ---------------------------------------------------------------- simulation
  update(dt: number) {
    this.time += dt;
    this.gustSmooth += (this.gust - this.gustSmooth) * Math.min(1, dt * 0.8);
    this.flagPhase += 3.2 * dt;
    const [w, h] = this.stage.size;
    const g = this.gust;
    if (this.time >= this.nextGust) this.startGust();

    // snow: gentle sway, carried sideways by the wind
    const wind = WIND_DIR * (12 + 520 * g);
    const move = (fl: Flake[], depth: number) => {
      for (const f of fl) {
        f.y += f.vy * dt * (1 + 0.6 * g);
        f.x += (Math.sin(this.time * f.sway + f.phase) * 14 + wind * depth) * dt;
        if (f.y > h + 10) { f.y = -10; f.x = rand(-100, w); }
        if (f.x > w + 20) f.x -= w + 40;
        if (f.x < -20) f.x += w + 40;
      }
    };
    move(this.far, 0.55);
    move(this.near, 1);

    // snow blown off the ground during a gust
    if (g > 0.25 && Math.random() < dt * 40 * g) {
      this.drifts.push({ x: rand(-60, w * 0.8), y: rand(705, 880), vx: WIND_DIR * rand(380, 620), vy: rand(-60, -10), t: 0, r: rand(1.5, 3.2) });
    }
    for (const d of this.drifts) { d.t += dt; d.x += d.vx * dt; d.y += d.vy * dt; d.vy += 40 * dt; }
    this.drifts = this.drifts.filter((d) => d.t < 2.2 && d.x < w + 40);
    for (const s of this.streaks) s.x += s.vx * dt;
    this.streaks = this.streaks.filter((s) => s.x < w + s.len + 100);

    // campfire: sparks and smoke
    const fx = this.fire.x, fy = this.fire.y;
    if (Math.random() < dt * 9) this.sparks.push({ x: fx + rand(-14, 14), y: fy - 30, vx: rand(-20, 20), vy: rand(-140, -80), t: 0 });
    for (const s of this.sparks) { s.t += dt; s.x += (s.vx + wind * 0.25) * dt; s.y += s.vy * dt; }
    this.sparks = this.sparks.filter((s) => s.t < 1.3);
    this.nextPuff -= dt;
    if (this.nextPuff <= 0) {
      this.nextPuff = rand(0.25, 0.45);
      this.smoke.push({ x: fx + rand(-8, 8), y: fy - 70, r: rand(10, 16), t: 0, life: rand(3.5, 5), vx: rand(-6, 6) });
    }
    for (const p of this.smoke) { p.t += dt; p.y -= 34 * dt; p.x += (p.vx + 14 + wind * 0.3) * dt; p.r += 9 * dt; }
    this.smoke = this.smoke.filter((p) => p.t < p.life);
  }

  onGust?: (seconds: number) => void;

  private startGust() {
    this.onGust?.(CFG.ambience.gustDuration);
    this.gustStart = this.time;
    this.nextGust = this.time + CFG.ambience.gustDuration + pick(CFG.ambience.gustEvery);
    for (let i = 0; i < 6; i++) {
      const len = rand(180, 320);
      this.streaks.push({ x: -len - rand(0, 600), y: rand(260, 820), vx: rand(480, 700), len, phase: rand(0, 6) });
    }
  }

  debugTrigger(kind: string) { if (kind === "gust") this.startGust(); }

  // ---------------------------------------------------------------- drawing
  drawBackground(ctx: CanvasRenderingContext2D) {
    const [w, h] = this.stage.size;
    ctx.drawImage(this.stage.layers.sky, 0, 0, w, h);
    this.drawAurora(ctx);
    ctx.drawImage(this.stage.layers.bg, 0, 0, w, h);
    this.drawTentGlow(ctx);
    this.drawFlakes(ctx, this.far, 0.65);
    this.drawFlags(ctx);
    this.drawFire(ctx);
  }

  drawForeground(ctx: CanvasRenderingContext2D) {
    const [w, h] = this.stage.size;
    this.drawFlakes(ctx, this.near, 0.95);
    ctx.drawImage(this.stage.layers.fg, 0, 0, w, h);
    this.drawWind(ctx);
  }

  private drawFlakes(ctx: CanvasRenderingContext2D, fl: Flake[], alpha: number) {
    ctx.save();
    ctx.fillStyle = `rgba(255,255,255,${alpha})`;
    ctx.beginPath();
    for (const f of fl) { ctx.moveTo(f.x + f.r, f.y); ctx.arc(f.x, f.y, f.r, 0, Math.PI * 2); }
    ctx.fill();
    ctx.restore();
  }

  private drawAurora(ctx: CanvasRenderingContext2D) {
    const { y0, y1 } = this.aurora;
    const w = this.stage.size[0];
    ctx.save();
    ctx.globalCompositeOperation = "lighter";
    const bands = [
      { c: "94,242,194", a: 0.22, base: y0 + 30, amp: 34, k: 0.0042, s: 0.18, hgt: 120, ph: 0 },
      { c: "120,200,255", a: 0.16, base: y0 + 80, amp: 26, k: 0.0055, s: -0.13, hgt: 100, ph: 2.1 },
      { c: "170,130,255", a: 0.10, base: y0 + 10, amp: 22, k: 0.0035, s: 0.1, hgt: 80, ph: 4.0 },
    ];
    for (const b of bands) {
      const top = (x: number) => b.base + b.amp * Math.sin(x * b.k + this.time * b.s + b.ph)
        + 10 * Math.sin(x * b.k * 3.1 - this.time * b.s * 2 + b.ph);
      const grad = ctx.createLinearGradient(0, b.base - b.amp - 10, 0, Math.min(y1, b.base + b.amp + b.hgt));
      grad.addColorStop(0, `rgba(${b.c},0)`);
      grad.addColorStop(0.25, `rgba(${b.c},${b.a})`);
      grad.addColorStop(1, `rgba(${b.c},0)`);
      ctx.fillStyle = grad;
      ctx.beginPath();
      for (let x = 0; x <= w; x += 20) { const y = top(x); if (x) ctx.lineTo(x, y); else ctx.moveTo(x, y); }
      for (let x = w; x >= 0; x -= 20) ctx.lineTo(x, top(x) + b.hgt * (0.7 + 0.3 * Math.sin(x * 0.01 + this.time * 0.3)));
      ctx.closePath();
      ctx.fill();
    }
    ctx.restore();
  }

  private flicker(seed: number) {
    const t = this.time;
    return 0.85 + 0.08 * Math.sin(t * 11 + seed) + 0.05 * Math.sin(t * 17.3 + seed * 2) + 0.03 * Math.sin(t * 29 + seed);
  }

  private drawTentGlow(ctx: CanvasRenderingContext2D) {
    ctx.save();
    ctx.globalCompositeOperation = "lighter";
    this.glows.forEach((g, i) => {
      const r = g.r * (1.6 + 0.15 * this.flicker(i * 3));
      const grad = ctx.createRadialGradient(g.x, g.y, 0, g.x, g.y, r);
      grad.addColorStop(0, `rgba(255,170,80,${0.22 * this.flicker(i)})`);
      grad.addColorStop(1, "rgba(255,170,80,0)");
      ctx.fillStyle = grad;
      ctx.beginPath(); ctx.arc(g.x, g.y, r, 0, Math.PI * 2); ctx.fill();
    });
    ctx.restore();
  }

  private drawFlags(ctx: CanvasRenderingContext2D) {
    this.poles.forEach((pole, i) => {
      const big = i !== 1;
      const L = big ? 120 : 80, h = big ? 42 : 30;
      drawCloth(ctx, {
        px: pole.x, py: pole.top + 6, side: WIND_DIR, L, outline: pennant(L, h), fill: FLAGS[i % FLAGS.length],
        phase: i * 1.9, flagPhase: this.flagPhase, gust: this.gustSmooth, ink: INK,
        after: (map) => {   // white snowflake emblem near the pole
          const [cx, cy] = map(L * 0.3, h / 2);
          this.snowflake(ctx, cx, cy, h * 0.3);
        },
      });
      ctx.fillStyle = "#E2B44A";
      ctx.strokeStyle = INK;
      ctx.lineWidth = 1.6;
      ctx.beginPath(); ctx.arc(pole.x, pole.top, 6, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
    });
  }

  private snowflake(ctx: CanvasRenderingContext2D, x: number, y: number, r: number) {
    ctx.save();
    ctx.strokeStyle = "rgba(255,255,255,0.95)";
    ctx.lineWidth = 2;
    ctx.lineCap = "round";
    ctx.beginPath();
    for (let i = 0; i < 6; i++) {
      const a = (i * Math.PI) / 3 + Math.PI / 6;
      const ex = x + r * Math.cos(a), ey = y + r * Math.sin(a);
      ctx.moveTo(x, y); ctx.lineTo(ex, ey);
      const bx = x + r * 0.6 * Math.cos(a), by = y + r * 0.6 * Math.sin(a);
      for (const s of [-1, 1]) {
        const ba = a + (s * Math.PI) / 4;
        ctx.moveTo(bx, by); ctx.lineTo(bx + r * 0.3 * Math.cos(ba), by + r * 0.3 * Math.sin(ba));
      }
    }
    ctx.stroke();
    ctx.restore();
  }

  private drawFire(ctx: CanvasRenderingContext2D) {
    const { x, y } = this.fire;
    const t = this.time;
    const lean = 10 * this.gustSmooth * WIND_DIR;
    ctx.save();
    // glow on the snow
    ctx.globalCompositeOperation = "lighter";
    const gr = 170 * this.flicker(7);
    const glow = ctx.createRadialGradient(x, y - 20, 0, x, y - 20, gr);
    glow.addColorStop(0, "rgba(255,160,70,0.42)");
    glow.addColorStop(1, "rgba(255,160,70,0)");
    ctx.fillStyle = glow;
    ctx.beginPath(); ctx.arc(x, y - 20, gr, 0, Math.PI * 2); ctx.fill();
    ctx.globalCompositeOperation = "source-over";
    // smoke behind the flames
    for (const p of this.smoke) {
      const a = 0.32 * Math.sin(Math.PI * Math.min(1, p.t / p.life));
      ctx.fillStyle = `rgba(190,202,220,${a.toFixed(3)})`;
      ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2); ctx.fill();
    }
    // flames: three tongues, each with three colour layers
    const tongue = (dx: number, hgt: number, wid: number, seed: number, col: string, outline: boolean) => {
      const hh = hgt * (0.85 + 0.15 * Math.sin(t * 9 + seed) + 0.08 * Math.sin(t * 15.7 + seed * 1.7));
      const sway = 6 * Math.sin(t * 6 + seed) + lean;
      ctx.beginPath();
      ctx.moveTo(x + dx - wid, y - 4);
      ctx.bezierCurveTo(x + dx - wid * 1.1, y - hh * 0.45, x + dx + sway - wid * 0.3, y - hh * 0.75, x + dx + sway, y - hh);
      ctx.bezierCurveTo(x + dx + sway + wid * 0.3, y - hh * 0.75, x + dx + wid * 1.1, y - hh * 0.45, x + dx + wid, y - 4);
      ctx.closePath();
      ctx.fillStyle = col;
      ctx.fill();
      if (outline) { ctx.strokeStyle = "rgba(90,30,10,0.8)"; ctx.lineWidth = 1.6; ctx.stroke(); }
    };
    for (const [dx, hgt, wid, seed] of [[-14, 56, 15, 0.3], [14, 60, 15, 2.2], [0, 82, 20, 4.1]] as const) {
      tongue(dx, hgt, wid, seed, "#E4572E", true);
      tongue(dx, hgt * 0.72, wid * 0.7, seed + 0.5, "#F29E38", false);
      tongue(dx, hgt * 0.45, wid * 0.42, seed + 1, "#FFE08A", false);
    }
    // sparks
    for (const s of this.sparks) {
      ctx.fillStyle = `rgba(255,${180 + Math.round(60 * (1 - s.t))},90,${Math.max(0, 1 - s.t / 1.3).toFixed(3)})`;
      ctx.beginPath(); ctx.arc(s.x, s.y, 2, 0, Math.PI * 2); ctx.fill();
    }
    ctx.restore();
  }

  private drawWind(ctx: CanvasRenderingContext2D) {
    const g = this.gust;
    ctx.save();
    // snow whipped along the ground
    ctx.fillStyle = "rgba(255,255,255,0.85)";
    ctx.beginPath();
    for (const d of this.drifts) { ctx.moveTo(d.x + d.r, d.y); ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2); }
    ctx.fill();
    if (g > 0.02) {
      ctx.strokeStyle = "rgba(214,234,255,1)";
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      ctx.lineWidth = 3;
      for (const s of this.streaks) {
        ctx.globalAlpha = 0.7 * g;
        const tail = s.x - s.len;
        const wav = (u: number) => s.y + 9 * Math.sin(u * 6 + s.phase + this.time * 4);
        ctx.beginPath();
        ctx.moveTo(tail, wav(0));
        for (let i = 1; i <= 12; i++) { const u = i / 12; ctx.lineTo(tail + s.len * u, wav(u)); }
        const hx = s.x, hy = wav(1);
        ctx.quadraticCurveTo(hx + 18, hy - 2, hx + 16, hy - 14);
        ctx.quadraticCurveTo(hx + 12, hy - 24, hx + 2, hy - 18);
        ctx.quadraticCurveTo(hx - 4, hy - 10, hx + 6, hy - 8);
        ctx.stroke();
      }
    }
    ctx.restore();
  }
}
