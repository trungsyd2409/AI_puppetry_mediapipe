// Hit effects in stage pixels: cartoon blood drops that fly, land and leave fading stains,
// a short impact burst, and metal sparks when two weapons clash.
const rand = (a: number, b: number) => a + Math.random() * (b - a);

interface Drop { x: number; y: number; vx: number; vy: number; r: number; groundY: number }
interface Stain { x: number; y: number; rx: number; ry: number; rot: number; t: number; life: number }
interface Burst { x: number; y: number; t: number; angle: number; k: number }
interface Spark { x: number; y: number; vx: number; vy: number; t: number }

const BLOOD = "#B3121F";
const BLOOD_D = "#5E0A10";

export class HitFx {
  private drops: Drop[] = [];
  private stains: Stain[] = [];
  private bursts: Burst[] = [];
  private sparks: Spark[] = [];

  constructor(private floorY: number) {}

  /** dir: unit vector the blow pushes towards; k: 0..1 strength. */
  blood(x: number, y: number, dx: number, dy: number, k: number) {
    const base = Math.atan2(dy, dx);
    const n = Math.round(14 + 22 * k);
    for (let i = 0; i < n; i++) {
      const a = base + rand(-0.7, 0.7) + (Math.random() < 0.2 ? Math.PI + rand(-0.5, 0.5) : 0);
      const sp = rand(160, 520) * (0.6 + 0.7 * k);
      this.drops.push({
        x, y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp - rand(60, 220), r: rand(2, 5.5),
        groundY: this.floorY + rand(-6, 34),
      });
    }
    this.bursts.push({ x, y, t: 0, angle: base, k });
  }

  clash(x: number, y: number) {
    for (let i = 0; i < 16; i++) {
      const a = rand(0, Math.PI * 2), sp = rand(200, 520);
      this.sparks.push({ x, y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp - 120, t: 0 });
    }
  }

  update(dt: number) {
    for (const d of this.drops) { d.vy += 1400 * dt; d.x += d.vx * dt; d.y += d.vy * dt; }
    for (const d of this.drops) {
      if (d.y >= d.groundY && d.vy > 0) {
        this.stains.push({ x: d.x, y: d.groundY, rx: d.r * rand(1.8, 3.4), ry: d.r * rand(0.6, 1.0),
          rot: rand(-0.2, 0.2), t: 0, life: rand(6, 9) });
      }
    }
    this.drops = this.drops.filter((d) => !(d.y >= d.groundY && d.vy > 0) && d.y < this.floorY + 300);
    for (const s of this.stains) s.t += dt;
    this.stains = this.stains.filter((s) => s.t < s.life);
    if (this.stains.length > 400) this.stains.splice(0, this.stains.length - 400);
    for (const b of this.bursts) b.t += dt;
    this.bursts = this.bursts.filter((b) => b.t < 0.18);
    for (const s of this.sparks) { s.t += dt; s.vy += 900 * dt; s.x += s.vx * dt; s.y += s.vy * dt; }
    this.sparks = this.sparks.filter((s) => s.t < 0.5);
  }

  /** Stains on the ground, behind the puppets. */
  drawBack(ctx: CanvasRenderingContext2D) {
    ctx.save();
    for (const s of this.stains) {
      const a = Math.min(1, (s.life - s.t) / 2) * 0.85;
      ctx.globalAlpha = a;
      ctx.fillStyle = BLOOD;
      ctx.beginPath(); ctx.ellipse(s.x, s.y, s.rx, s.ry, s.rot, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = BLOOD_D;
      ctx.beginPath(); ctx.ellipse(s.x, s.y + s.ry * 0.2, s.rx * 0.5, s.ry * 0.45, s.rot, 0, Math.PI * 2); ctx.fill();
    }
    ctx.restore();
  }

  /** Flying drops, impact bursts and sparks, in front of the puppets. */
  drawFront(ctx: CanvasRenderingContext2D) {
    ctx.save();
    for (const b of this.bursts) {
      const u = b.t / 0.18, R = (26 + 30 * b.k) * (0.6 + u);
      ctx.globalAlpha = 1 - u;
      ctx.fillStyle = BLOOD;
      ctx.strokeStyle = BLOOD_D;
      ctx.lineWidth = 2;
      ctx.beginPath();
      for (let i = 0; i < 14; i++) {
        const a = b.angle + (i / 14) * Math.PI * 2, rr = i % 2 ? R * 0.45 : R;
        const px = b.x + Math.cos(a) * rr, py = b.y + Math.sin(a) * rr;
        if (i) ctx.lineTo(px, py); else ctx.moveTo(px, py);
      }
      ctx.closePath(); ctx.fill(); ctx.stroke();
    }
    ctx.globalAlpha = 1;
    for (const d of this.drops) {
      const sp = Math.hypot(d.vx, d.vy);
      const stretch = 1 + Math.min(1.6, sp / 400);
      ctx.fillStyle = BLOOD;
      ctx.strokeStyle = BLOOD_D;
      ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.ellipse(d.x, d.y, d.r * stretch, d.r, Math.atan2(d.vy, d.vx), 0, Math.PI * 2);
      ctx.fill(); ctx.stroke();
    }
    ctx.lineCap = "round";
    for (const s of this.sparks) {
      ctx.strokeStyle = `rgba(255,${200 + Math.round(55 * (1 - s.t * 2))},120,${(1 - s.t / 0.5).toFixed(3)})`;
      ctx.lineWidth = 2.4;
      ctx.beginPath(); ctx.moveTo(s.x, s.y); ctx.lineTo(s.x - s.vx * 0.025, s.y - s.vy * 0.025); ctx.stroke();
    }
    ctx.restore();
  }
}
