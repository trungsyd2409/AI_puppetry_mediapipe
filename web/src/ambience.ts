// Living background: waving flags (Vietnamese flag + five-colour swallow-tail pennants),
// drifting waves, carp jumping out of the pond, gusts of wind with cloud streaks and
// bamboo leaves, and cranes flying across. Everything is drawn in stage pixels.
import { CFG } from "./config";
import type { Stage } from "./assets";

const INK = "#2A140A";
const WAVE = "#9CC3B4";
const PENNANTS = ["#C0281C", "#E2B44A", "#2F6FA8", "#3E8A4A", "#8A3FA0"];
const VN_RED = "#D0261C";
const VN_STAR = "#F8D23A";

const rand = (a: number, b: number) => a + Math.random() * (b - a);
const pick = (r: number[]) => rand(r[0], r[1]);

interface Fish { x0: number; dir: number; dist: number; h: number; t: number; dur: number; scale: number; landed: boolean }
interface Ripple { x: number; y: number; t: number; size: number }
interface Drop { x: number; y: number; vx: number; vy: number; t: number }
interface Bird { x: number; y: number; vx: number; phase: number; scale: number }
interface Leaf { x: number; y: number; vx: number; vy: number; rot: number; vr: number; s: number; phase: number }
interface Streak { x: number; y: number; vx: number; len: number; phase: number }

export class Ambience {
  private time = 0;
  private flagPhase = 0;   // accumulated so speed changes never make the cloth jump
  private wavePhase = 0;
  private gustSmooth = 0;  // slowly follows the gust, only widens the flag motion a little
  private gustStart = -100;
  private gustDir = 1;
  private nextGust = pick(CFG.ambience.gustEvery) * 0.5;
  private nextFish = 2;
  private nextBirds = 3;
  private fish: Fish[] = [];
  private ripples: Ripple[] = [];
  private drops: Drop[] = [];
  private birds: Bird[] = [];
  private leaves: Leaf[] = [];
  private streaks: Streak[] = [];

  constructor(private stage: Stage) {}

  /** 0..1 strength of the current gust (smooth bump). */
  get gust() {
    const u = (this.time - this.gustStart) / CFG.ambience.gustDuration;
    return u < 0 || u > 1 ? 0 : Math.sin(Math.PI * u) ** 2;
  }

  /** Horizontal acceleration the wind applies to the puppets (m/s^2). */
  windAccel() { return this.gust * this.gustDir * CFG.ambience.windAccel; }

  // ---------------------------------------------------------------- simulation
  update(dt: number) {
    this.time += dt;
    this.gustSmooth += (this.gust - this.gustSmooth) * Math.min(1, dt * 0.8);
    this.flagPhase += 3.2 * dt;    // constant, calm flutter
    this.wavePhase += 16 * dt;     // px/s drift of the wave rows
    const W = this.stage.size[0];
    const A = CFG.ambience;

    if (this.time >= this.nextGust) this.startGust();
    if (this.time >= this.nextFish) { this.spawnFish(); this.nextFish = this.time + pick(A.fishEvery); }
    if (this.time >= this.nextBirds) { this.spawnBirds(); this.nextBirds = this.time + pick(A.birdsEvery); }

    // fish: parabolic jump, splash on leaving and on landing
    const surf = this.stage.water.frontY + 12;
    for (const f of this.fish) {
      f.t += dt;
      if (!f.landed && f.t >= f.dur) {
        f.landed = true;
        this.splash(f.x0 + f.dir * f.dist, surf, 1.2);
      }
    }
    this.fish = this.fish.filter((f) => f.t < f.dur + 0.1);

    for (const r of this.ripples) r.t += dt;
    this.ripples = this.ripples.filter((r) => r.t < 1.6);
    for (const d of this.drops) { d.t += dt; d.vy += 900 * dt; d.x += d.vx * dt; d.y += d.vy * dt; }
    this.drops = this.drops.filter((d) => d.y < surf + 10 && d.t < 2);

    for (const b of this.birds) { b.x += b.vx * dt; b.phase += dt; }
    this.birds = this.birds.filter((b) => b.x > -250 && b.x < W + 250);

    // wind: streaks and leaves while a gust blows
    const g = this.gust;
    if (g > 0.2 && Math.random() < dt * 5 * g) {
      this.leaves.push({
        x: this.gustDir > 0 ? -40 : W + 40, y: rand(120, 720),
        vx: this.gustDir * rand(260, 420), vy: rand(-40, 40),
        rot: rand(0, Math.PI * 2), vr: rand(-6, 6), s: rand(0.9, 1.4), phase: rand(0, 6),
      });
    }
    for (const l of this.leaves) {
      l.x += l.vx * dt;
      l.y += (l.vy + 50 * Math.sin(this.time * 3 + l.phase)) * dt;
      l.vy += 15 * dt;
      l.rot += l.vr * dt;
    }
    this.leaves = this.leaves.filter((l) => l.x > -100 && l.x < W + 100 && l.y < this.stage.size[1]);
    for (const s of this.streaks) s.x += s.vx * dt;
    this.streaks = this.streaks.filter((s) => s.x > -s.len - 100 && s.x < W + s.len + 100);
  }

  private startGust() {
    this.gustStart = this.time;
    this.gustDir = Math.random() < 0.5 ? -1 : 1;
    this.nextGust = this.time + CFG.ambience.gustDuration + pick(CFG.ambience.gustEvery);
    const W = this.stage.size[0];
    for (let i = 0; i < 5; i++) {
      const len = rand(160, 300);
      this.streaks.push({
        x: this.gustDir > 0 ? -len - rand(0, 500) : W + len + rand(0, 500),
        y: rand(130, 640), vx: this.gustDir * rand(420, 620), len, phase: rand(0, 6),
      });
    }
  }

  private spawnFish() {
    const dir = Math.random() < 0.5 ? -1 : 1;
    const f: Fish = {
      x0: rand(260, 1340), dir, dist: rand(130, 220), h: rand(100, 160),
      t: 0, dur: rand(1.0, 1.3), scale: rand(0.45, 0.65), landed: false,
    };
    this.fish.push(f);
    this.splash(f.x0, this.stage.water.frontY + 12, 0.9);
  }

  private splash(x: number, y: number, k: number) {
    this.ripples.push({ x, y, t: 0, size: k }, { x, y, t: -0.18, size: k * 0.7 });
    const n = Math.round(8 * k);
    for (let i = 0; i < n; i++)
      this.drops.push({ x: x + rand(-12, 12), y, vx: rand(-110, 110) * k, vy: -rand(180, 360) * k, t: 0 });
  }

  private spawnBirds() {
    const dir = Math.random() < 0.5 ? -1 : 1;
    const W = this.stage.size[0];
    const n = 2 + Math.floor(Math.random() * 3);
    const y0 = rand(120, 230), speed = rand(110, 170);
    for (let i = 0; i < n; i++) {
      this.birds.push({
        x: (dir > 0 ? -120 : W + 120) - dir * i * rand(60, 110), y: y0 + i * rand(-25, 30),
        vx: dir * speed, phase: rand(0, 1), scale: rand(0.45, 0.7),
      });
    }
  }

  // ---------------------------------------------------------------- waves
  private drawWaveRows(ctx: CanvasRenderingContext2D, y0: number, y1: number, alpha: number) {
    ctx.save();
    ctx.strokeStyle = WAVE;
    ctx.globalAlpha = alpha;
    ctx.lineWidth = 2;
    ctx.lineCap = "round";
    let j = 0;
    for (let y = y0; y < y1; y += 22, j++) {
      const dirRow = j % 2 ? 1 : -1;
      const off = (((j % 2) * 40 + dirRow * this.wavePhase) % 80 + 80) % 80;
      const bob = Math.sin(this.time * 1.6 + j) * 2;
      ctx.beginPath();
      for (let x = -80 + off; x < this.stage.size[0] + 80; x += 80) {
        const yy = y + bob;
        ctx.moveTo(x, yy);
        ctx.quadraticCurveTo(x + 20, yy - 12, x + 40, yy);
        ctx.quadraticCurveTo(x + 28, yy - 4, x + 22, yy + 2);
      }
      ctx.stroke();
    }
    ctx.restore();
  }

  drawWaterBack(ctx: CanvasRenderingContext2D) {
    this.drawWaveRows(ctx, this.stage.water.surfaceY + 10, this.stage.water.frontY, 0.35);
  }

  drawWaterFront(ctx: CanvasRenderingContext2D) {
    this.drawWaveRows(ctx, this.stage.water.frontY, this.stage.size[1] + 10, 0.55);
    ctx.save();
    for (const r of this.ripples) {
      if (r.t < 0) continue;
      const rad = (12 + 70 * r.t) * r.size;
      ctx.globalAlpha = Math.max(0, 0.8 * (1 - r.t / 1.6));
      ctx.strokeStyle = "#D8EEE4";
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.ellipse(r.x, r.y, rad, rad * 0.22, 0, 0, Math.PI * 2); ctx.stroke();
    }
    ctx.globalAlpha = 1;
    for (const d of this.drops) {
      ctx.fillStyle = "#E4F4EC";
      ctx.strokeStyle = "rgba(42,20,10,0.5)";
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.ellipse(d.x, d.y, 3, 4, Math.atan2(d.vy, d.vx), 0, Math.PI * 2); ctx.fill(); ctx.stroke();
    }
    ctx.restore();
  }

  // ---------------------------------------------------------------- flags
  /** Draw a cloth whose outline is given in local coords (x along the flag), waving from the pole. */
  private cloth(ctx: CanvasRenderingContext2D, px: number, py: number, side: number, L: number,
    outline: [number, number][], fill: string, phase: number, after?: (map: (x: number, y: number) => [number, number], slope: (x: number) => number) => void) {
    const g = this.gustSmooth;
    const amp = 4 + 3 * g;
    const k = (2 * Math.PI) / (L * 0.9);
    const ph = this.flagPhase;
    const wave = (x: number) => amp * (x / L) * Math.sin(k * x - ph + phase);
    const slope = (x: number) => (amp / L) * Math.sin(k * x - ph + phase)
      + amp * (x / L) * k * Math.cos(k * x - ph + phase);
    const droop = (x: number) => (1 - g) * 0.06 * x;   // hangs a little when calm
    const map = (x: number, y: number): [number, number] => [px + side * x, py + y + wave(x) + droop(x)];

    ctx.save();
    ctx.beginPath();
    outline.forEach(([x, y], i) => { const [X, Y] = map(x, y); if (i) ctx.lineTo(X, Y); else ctx.moveTo(X, Y); });
    ctx.closePath();
    ctx.fillStyle = fill;
    ctx.fill();
    // folds: darken where the cloth turns away, lighten where it faces the light
    const [XA] = map(0, 0), [XB] = map(L, 0);
    const shade = ctx.createLinearGradient(XA, 0, XB, 0);
    for (let i = 0; i <= 16; i++) {
      const x = (L * i) / 16, s = slope(x);
      shade.addColorStop(i / 16, s > 0 ? `rgba(40,15,5,${Math.min(0.32, s * 0.9).toFixed(3)})`
        : `rgba(255,240,200,${Math.min(0.28, -s * 0.8).toFixed(3)})`);
    }
    ctx.fillStyle = shade;
    ctx.fill();
    after?.(map, slope);
    ctx.strokeStyle = INK;
    ctx.lineWidth = 2;
    ctx.lineJoin = "round";
    ctx.stroke();
    ctx.restore();
  }

  drawFlags(ctx: CanvasRenderingContext2D) {
    const N = 14;
    for (const [pi, pole] of this.stage.poles.entries()) {
      // Vietnamese national flag on top
      const L = 104, Hh = 68;
      const rect: [number, number][] = [];
      for (let i = 0; i <= N; i++) rect.push([(L * i) / N, 0]);
      for (let i = N; i >= 0; i--) rect.push([(L * i) / N, Hh]);
      this.cloth(ctx, pole.x, pole.top + 8, pole.side, L, rect, VN_RED, pi * 1.7, (map, slope) => {
        const [cx, cy] = map(L * 0.5, Hh * 0.5);
        this.star(ctx, cx, cy, Hh * 0.3, Math.atan(slope(L * 0.5)) * 0.6 * pole.side);
      });
      // five swallow-tail pennants
      PENNANTS.forEach((c, i) => {
        const Lp = 106 - i * 8, h = 26;
        const shape: [number, number][] = [];
        for (let s = 0; s <= N; s++) shape.push([(Lp * s) / N, -3 * Math.sin((Math.PI * s) / N)]);
        shape.push([Lp * 0.8, h / 2]);
        for (let s = N; s >= 0; s--) shape.push([(Lp * s) / N, h + 3 * Math.sin((Math.PI * s) / N)]);
        this.cloth(ctx, pole.x, pole.top + 92 + i * 37, pole.side, Lp, shape, c, pi * 1.7 + (i + 1) * 0.6);
      });
      // pole finial on top of the cloth
      ctx.fillStyle = "#E2B44A";
      ctx.strokeStyle = INK;
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(pole.x, pole.top, 9, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
    }
  }

  private star(ctx: CanvasRenderingContext2D, x: number, y: number, r: number, rot: number) {
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(rot);
    ctx.beginPath();
    for (let i = 0; i < 10; i++) {
      const rad = i % 2 ? r * 0.382 : r;
      const a = -Math.PI / 2 + (i * Math.PI) / 5;
      if (i) ctx.lineTo(rad * Math.cos(a), rad * Math.sin(a)); else ctx.moveTo(rad * Math.cos(a), rad * Math.sin(a));
    }
    ctx.closePath();
    ctx.fillStyle = VN_STAR;
    ctx.fill();
    ctx.restore();
  }

  // ---------------------------------------------------------------- creatures
  drawBirds(ctx: CanvasRenderingContext2D) {
    const frames = this.stage.props.crane, sc = this.stage.props.scale;
    const seq = [0, 1, 2, 1];
    for (const b of this.birds) {
      const img = frames[seq[Math.floor((b.phase * 6) % 4)]];
      const w = (img.width / sc) * b.scale, h = (img.height / sc) * b.scale;
      ctx.save();
      ctx.translate(b.x, b.y + Math.sin(b.phase * 3) * 5);
      if (b.vx < 0) ctx.scale(-1, 1);
      ctx.drawImage(img, -w / 2, -h / 2, w, h);
      ctx.restore();
    }
  }

  drawFish(ctx: CanvasRenderingContext2D) {
    const img = this.stage.props.fish, sc = this.stage.props.scale;
    const surf = this.stage.water.frontY + 12;
    for (const f of this.fish) {
      const u = Math.min(1, f.t / f.dur);
      const x = f.x0 + f.dir * f.dist * u;
      const y = surf - f.h * 4 * u * (1 - u);
      const vx = f.dir * f.dist, vy = -f.h * 4 * (1 - 2 * u);
      const w = (img.width / sc) * f.scale, h = (img.height / sc) * f.scale;
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(Math.atan2(vy, Math.abs(vx)) * f.dir);
      ctx.scale(f.dir, 1);
      ctx.drawImage(img, -w / 2, -h / 2, w, h);
      ctx.restore();
    }
  }

  drawWind(ctx: CanvasRenderingContext2D) {
    const g = this.gust;
    ctx.save();
    if (g > 0.02) {
      ctx.strokeStyle = "#8E6A30";
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      ctx.lineWidth = 3.5;
      for (const s of this.streaks) {
        ctx.globalAlpha = 0.8 * g;
        const d = this.gustDir;
        const tail = s.x - d * s.len;
        const wav = (t: number) => s.y + 10 * Math.sin(t * 6 + s.phase + this.time * 4);
        ctx.beginPath();
        ctx.moveTo(tail, wav(0));
        for (let i = 1; i <= 12; i++) { const t = i / 12; ctx.lineTo(tail + d * s.len * t, wav(t)); }
        // cloud curl at the head, like the 'van may' motif
        const hx = s.x, hy = wav(1);
        ctx.quadraticCurveTo(hx + d * 18, hy - 2, hx + d * 16, hy - 14);
        ctx.quadraticCurveTo(hx + d * 12, hy - 24, hx + d * 2, hy - 18);
        ctx.quadraticCurveTo(hx - d * 4, hy - 10, hx + d * 6, hy - 8);
        ctx.stroke();
      }
    }
    ctx.globalAlpha = 1;
    const img = this.stage.props.leaf, sc = this.stage.props.scale;
    for (const l of this.leaves) {
      const w = (img.width / sc) * l.s, h = (img.height / sc) * l.s;
      ctx.save();
      ctx.translate(l.x, l.y);
      ctx.rotate(l.rot);
      ctx.scale(1, Math.cos(this.time * 5 + l.phase));   // tumbling
      ctx.drawImage(img, -w / 2, -h / 2, w, h);
      ctx.restore();
    }
    ctx.restore();
  }

  /** For tests: trigger events now. */
  debugTrigger(kind: "gust" | "fish" | "birds") {
    if (kind === "gust") this.startGust();
    else if (kind === "fish") this.spawnFish();
    else this.spawnBirds();
  }
}
