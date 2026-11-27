// Weapon trails and ice aura. Every frame, call track() for each blade (puppet weapons and
// ultimate swords), then update() and draw(). Drawn in stage pixels.
import { CFG, type Pt } from "./config";

interface Sample { tip: Pt; base: Pt; t: number }
interface Track { samples: Sample[]; seen: number; width: number; speed: number }
interface Frost { x: number; y: number; vx: number; vy: number; t: number; life: number; r: number; rot: number }

const rand = (a: number, b: number) => a + Math.random() * (b - a);

export class WeaponFx {
  private tracks = new Map<string, Track>();
  private frost: Frost[] = [];
  private time = 0;
  /** Called with 0..1 when a blade tip moves fast (for the whoosh sound). */
  onSwing?: (k: number) => void;

  track(key: string, tip: Pt, base: Pt, width = 1) {
    let tr = this.tracks.get(key);
    if (!tr) { tr = { samples: [], seen: 0, width, speed: 0 }; this.tracks.set(key, tr); }
    const prev = tr.samples[tr.samples.length - 1];
    if (prev) {
      const dt = Math.max(1e-3, this.time - prev.t);
      tr.speed = Math.hypot(tip.x - prev.tip.x, tip.y - prev.tip.y) / dt;
    }
    tr.samples.push({ tip: { ...tip }, base: { ...base }, t: this.time });
    tr.seen = this.time;
    tr.width = width;
  }

  update(dt: number) {
    this.time += dt;
    const keep = CFG.weaponFx.trailTime;
    for (const [key, tr] of this.tracks) {
      if (this.time - tr.seen > 0.2) { this.tracks.delete(key); continue; }
      while (tr.samples.length > 2 && this.time - tr.samples[0].t > keep) tr.samples.shift();
      const s = tr.samples[tr.samples.length - 1];
      // frost crystals drifting off the blade
      const len = Math.hypot(s.tip.x - s.base.x, s.tip.y - s.base.y);
      const rate = (len / 60) * (1 + Math.min(3, tr.speed / 600)) * tr.width;
      if (Math.random() < rate * dt * 8) {
        const u = Math.random();
        this.frost.push({
          x: s.base.x + (s.tip.x - s.base.x) * u + rand(-6, 6), y: s.base.y + (s.tip.y - s.base.y) * u + rand(-6, 6),
          vx: rand(-20, 20), vy: rand(-35, 5), t: 0, life: rand(0.5, 1.0), r: rand(1.5, 3.6) * tr.width, rot: rand(0, 6),
        });
      }
      if (tr.speed > CFG.weaponFx.swingSoundSpeed) this.onSwing?.(Math.min(1, tr.speed / (CFG.weaponFx.swingSoundSpeed * 2.5)));
    }
    for (const f of this.frost) { f.t += dt; f.x += f.vx * dt; f.y += f.vy * dt; f.rot += dt * 2; }
    this.frost = this.frost.filter((f) => f.t < f.life);
    if (this.frost.length > 350) this.frost.splice(0, this.frost.length - 350);
  }

  draw(ctx: CanvasRenderingContext2D) {
    ctx.save();
    ctx.globalCompositeOperation = "lighter";
    for (const tr of this.tracks.values()) {
      const S = tr.samples, n = S.length;
      if (n < 2) continue;
      const last = S[n - 1];
      // trail ribbon, brighter at the newest edge
      if (tr.speed > CFG.weaponFx.trailMinSpeed) {
        const k = Math.min(1, tr.speed / 1500);
        for (let i = 1; i < n; i++) {
          const a = S[i - 1], b = S[i];
          const age = (this.time - b.t) / CFG.weaponFx.trailTime;
          ctx.fillStyle = `rgba(150,215,255,${(0.42 * k * (1 - age) * (i / n)).toFixed(3)})`;
          ctx.beginPath();
          ctx.moveTo(a.tip.x, a.tip.y); ctx.lineTo(b.tip.x, b.tip.y);
          ctx.lineTo(b.base.x, b.base.y); ctx.lineTo(a.base.x, a.base.y);
          ctx.closePath(); ctx.fill();
        }
      }
      // icy glow along the blade
      const pulse = 0.75 + 0.25 * Math.sin(this.time * 6 + last.tip.x * 0.01);
      ctx.lineCap = "round";
      for (const [w, a] of [[14, 0.12], [7, 0.22], [2.5, 0.55]] as const) {
        ctx.strokeStyle = `rgba(160,225,255,${(a * pulse).toFixed(3)})`;
        ctx.lineWidth = w * tr.width;
        ctx.beginPath(); ctx.moveTo(last.base.x, last.base.y); ctx.lineTo(last.tip.x, last.tip.y); ctx.stroke();
      }
    }
    // frost crystals: tiny six-armed sparkles
    ctx.lineWidth = 1.2;
    for (const f of this.frost) {
      const a = Math.sin(Math.PI * (f.t / f.life));
      ctx.strokeStyle = `rgba(225,245,255,${(0.9 * a).toFixed(3)})`;
      ctx.beginPath();
      for (let i = 0; i < 3; i++) {
        const ang = f.rot + (i * Math.PI) / 3;
        ctx.moveTo(f.x - Math.cos(ang) * f.r, f.y - Math.sin(ang) * f.r);
        ctx.lineTo(f.x + Math.cos(ang) * f.r, f.y + Math.sin(ang) * f.r);
      }
      ctx.stroke();
    }
    ctx.restore();
  }

  /** Burst of ice shards (giant sword impact, shattering). */
  shatter(x: number, y: number, n = 40, power = 1) {
    for (let i = 0; i < n; i++) {
      const a = rand(-Math.PI, 0), sp = rand(80, 420) * power;
      this.frost.push({ x: x + rand(-20, 20), y: y + rand(-10, 10), vx: Math.cos(a) * sp, vy: Math.sin(a) * sp,
        t: 0, life: rand(0.5, 1.2), r: rand(2.5, 6) * power, rot: rand(0, 6) });
    }
  }
}
