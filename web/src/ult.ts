// Ultimates, drawn and simulated in stage pixels.
//   giantSword (white warrior): a huge ice sword drops on the opponent's head (aimed where the
//     head was when cast, so it can be dodged). A hit breaks the opponent into pieces that fly
//     around for 3 s, then reassemble; only then can the strings reconnect.
//   swordRain (red guard): for 4 s small ice swords fly at the opponent from every side. The
//     opponent's strings are cut the whole time and each hit throws them in a random direction.
import { CFG, type Pt } from "./config";
import type { Puppet } from "./puppet";
import type { HitFx } from "./fx_blood";
import type { Sfx } from "./sfx";
import type { WeaponFx } from "./weaponfx";
import { Vec2 } from "planck";
import { m } from "./physics";

const rand = (a: number, b: number) => a + Math.random() * (b - a);
const INK = "#1B2433";

interface Giant { id: number; caster: Puppet; target: Puppet | null; x: number; y: number; y0: number; t: number; hit: boolean; landed: number }
interface RainSword { x: number; y: number; vx: number; vy: number; landed: number; gone: boolean; id: number }
interface Rain { caster: Puppet; target: Puppet | null; t: number; acc: number }
interface Flash { x: number; y: number; t: number }

export class Ultimates {
  private readyAt = new Map<Puppet, number>();
  private giants: Giant[] = [];
  private rains: Rain[] = [];
  private swords: RainSword[] = [];
  private flashes: Flash[] = [];
  private nextId = 0;
  private time = 0;

  constructor(private floorY: number, private topY: number, private hitFx: HitFx, private sfx: Sfx,
    private wfx: WeaponFx, private shake: (k: number) => void) {}

  /** 0..1 cooldown progress (1 = ready). */
  charge(p: Puppet, now: number) {
    const r = this.readyAt.get(p) ?? 0;
    return r <= now ? 1 : 1 - (r - now) / (CFG.ult.cooldown * 1000);
  }

  cast(caster: Puppet, target: Puppet | null, now: number): boolean {
    if (this.charge(caster, now) < 1) return false;
    const kind = CFG.ult.kinds[caster.id];
    if (!kind) return false;
    this.readyAt.set(caster, now + CFG.ult.cooldown * 1000);
    const h = caster.headPx();
    this.flashes.push({ x: h.x, y: h.y, t: 0 });
    this.sfx.ultCast();
    if (kind === "giantSword") {
      const aim = target ? target.headPx() : { x: caster.torsoX() + 250, y: this.floorY - 300 };
      const y0 = this.topY - 520;
      this.giants.push({ id: this.nextId++, caster, target, x: aim.x, y: y0, y0, t: 0, hit: false, landed: 0 });
      this.sfx.giantFall(CFG.ult.giantSword.fallTime);
    } else {
      this.rains.push({ caster, target, t: 0, acc: 0 });
      target?.forceDetach(now, CFG.ult.swordRain.duration);
    }
    return true;
  }

  // ---------------------------------------------------------------- simulation
  update(dt: number, now: number) {
    this.time += dt;
    const G = CFG.ult.giantSword;
    for (const g of this.giants) {
      g.t += dt;
      if (!g.landed) {
        const u = Math.min(1, g.t / G.fallTime);
        g.y = g.y0 + (this.floorY + 18 - g.y0) * u * u;     // tip position, accelerating
        if (!g.hit && g.target) this.giantHitTest(g, now);
        if (u >= 1) {
          g.landed = g.t;
          this.shake(0.7);
          this.wfx.shatter(g.x, this.floorY, 50, 1.2);
          if (!g.hit) this.sfx.giantImpact();
        }
      }
      if (g.landed && g.t - g.landed >= 1.1) {   // dissolve into ice dust
        this.wfx.shatter(g.x, g.y - 150, 60, 1.4);
        this.sfx.rainSword();
      } else {
        this.wfx.track(`giant${g.id}`, { x: g.x, y: g.y }, { x: g.x, y: g.y - 300 }, 2.2);
      }
    }
    this.giants = this.giants.filter((g) => !g.landed || g.t - g.landed < 1.1);

    const R = CFG.ult.swordRain;
    for (const r of this.rains) {
      r.t += dt;
      r.acc += dt * R.perSecond;
      const aim = r.target ? r.target.torsoPx() : { x: r.caster.torsoX() + 300, y: this.floorY - 250 };
      while (r.acc >= 1 && r.t < R.duration) {
        r.acc -= 1;
        // come from anywhere above or beside the target (never from under the ground)
        const from = (rand(-195, 15) * Math.PI) / 180;
        const sx = aim.x + Math.cos(from) * 1050, sy = aim.y + Math.sin(from) * 1050;
        const tx = aim.x + rand(-R.aimSpread, R.aimSpread), ty = aim.y + rand(-R.aimSpread, R.aimSpread);
        const d = Math.hypot(tx - sx, ty - sy), sp = rand(R.speed[0], R.speed[1]);
        this.swords.push({ x: sx, y: sy, vx: ((tx - sx) / d) * sp, vy: ((ty - sy) / d) * sp,
          landed: 0, gone: false, id: this.nextId++ });
      }
      for (const s of this.swords) {
        if (s.landed || s.gone || !r.target) continue;
        const body = r.target.hitTest(s.x, s.y) ?? r.target.hitTest(s.x - s.vx * 0.02, s.y - s.vy * 0.02);
        if (body) {
          s.gone = true;
          const a = rand(0, Math.PI * 2);                 // up, down, left, right: anything
          const dir = { x: Math.cos(a), y: Math.sin(a) };
          r.target.knockback(body, Vec2(m(s.x), m(s.y)), dir, rand(R.knockback.min, R.knockback.max));
          this.hitFx.blood(s.x, s.y, dir.x, dir.y, 0.2);
          this.sfx.hit(0.5);
          this.shake(0.35);
        }
      }
    }
    this.rains = this.rains.filter((r) => r.t < R.duration + 0.2);
    for (const s of this.swords) {
      if (s.gone) continue;
      if (!s.landed) {
        s.x += s.vx * dt; s.y += s.vy * dt;
        if (s.y >= this.floorY + 14 && s.vy > 0) { s.y = this.floorY + 14; s.landed = this.time; this.sfx.rainSword(); this.wfx.shatter(s.x, s.y, 4, 0.5); }
        else if (s.x < -400 || s.x > 2000 || s.y < this.topY - 1200) s.gone = true;
      } else if (this.time - s.landed > 0.8) {
        s.gone = true;
      }
    }
    this.swords = this.swords.filter((s) => !s.gone);
    for (const f of this.flashes) f.t += dt;
    this.flashes = this.flashes.filter((f) => f.t < 0.6);
  }

  private giantHitTest(g: Giant, now: number) {
    const t = g.target!, w = CFG.ult.giantSword.hitWidth;
    for (const dy of [0, -60, -120])
      for (const dx of [0, -w, w]) {
        const body = t.hitTest(g.x + dx, g.y + dy);
        if (!body) continue;
        g.hit = true;
        const side = Math.sign(t.torsoX() - g.x) || 1;
        t.shatter(now, CFG.ult.giantSword.scatterTime);
        this.hitFx.blood(g.x, g.y + dy, side, -0.6, 1);
        this.hitFx.blood(g.x, g.y + dy, -side, -0.6, 0.8);
        this.wfx.shatter(g.x, g.y + dy, 30, 1);
        this.sfx.hit(1);
        this.sfx.giantImpact();
        this.shake(1);
        return;
      }
  }

  // ---------------------------------------------------------------- drawing
  /** Warnings on the ground (behind the puppets). */
  drawBack(ctx: CanvasRenderingContext2D) {
    ctx.save();
    for (const g of this.giants) {
      if (g.landed) continue;
      const u = Math.min(1, g.t / CFG.ult.giantSword.fallTime);
      const r = 70 + 30 * u;
      ctx.globalCompositeOperation = "lighter";
      const grad = ctx.createRadialGradient(g.x, this.floorY, 0, g.x, this.floorY, r);
      grad.addColorStop(0, `rgba(140,210,255,${0.15 + 0.35 * u})`);
      grad.addColorStop(1, "rgba(140,210,255,0)");
      ctx.fillStyle = grad;
      ctx.beginPath(); ctx.ellipse(g.x, this.floorY + 6, r, r * 0.28, 0, 0, Math.PI * 2); ctx.fill();
      ctx.globalCompositeOperation = "source-over";
      ctx.strokeStyle = `rgba(200,235,255,${0.5 + 0.5 * Math.sin(this.time * 20)})`;
      ctx.lineWidth = 2.5;
      ctx.setLineDash([10, 8]);
      ctx.beginPath(); ctx.ellipse(g.x, this.floorY + 6, r * 0.8, r * 0.22, 0, 0, Math.PI * 2); ctx.stroke();
      ctx.setLineDash([]);
    }
    ctx.restore();
  }

  /** Swords and cast flashes (in front of the puppets). */
  drawFront(ctx: CanvasRenderingContext2D) {
    for (const g of this.giants) {
      const fade = g.landed ? Math.max(0, 1 - (g.t - g.landed) / 1.1) : 1;
      this.drawSword(ctx, g.x, g.y, Math.PI / 2, 2.2, fade);
    }
    for (const s of this.swords) {
      const ang = Math.atan2(s.vy, s.vx);
      const fade = s.landed ? Math.max(0, 1 - (this.time - s.landed) / 0.8) : 1;
      if (!s.landed) {   // streak
        ctx.save();
        ctx.globalCompositeOperation = "lighter";
        ctx.strokeStyle = "rgba(160,225,255,0.45)";
        ctx.lineWidth = 6;
        ctx.lineCap = "round";
        ctx.beginPath(); ctx.moveTo(s.x - s.vx * 0.09, s.y - s.vy * 0.09); ctx.lineTo(s.x, s.y); ctx.stroke();
        ctx.restore();
      }
      this.drawSword(ctx, s.x, s.y, ang, 0.42, fade);
    }
    ctx.save();
    ctx.globalCompositeOperation = "lighter";
    for (const f of this.flashes) {
      const u = f.t / 0.6, r = 30 + 160 * u;
      ctx.strokeStyle = `rgba(170,230,255,${(1 - u).toFixed(3)})`;
      ctx.lineWidth = 6 * (1 - u) + 1;
      ctx.beginPath(); ctx.arc(f.x, f.y, r, 0, Math.PI * 2); ctx.stroke();
      for (let i = 0; i < 6; i++) {
        const a = (i * Math.PI) / 3 + u;
        ctx.beginPath(); ctx.moveTo(f.x + Math.cos(a) * r * 0.4, f.y + Math.sin(a) * r * 0.4);
        ctx.lineTo(f.x + Math.cos(a) * r * 0.75, f.y + Math.sin(a) * r * 0.75); ctx.stroke();
      }
    }
    ctx.restore();
  }

  /** Ice sword: tip at (x, y), pointing along `ang`, length about 190 * scale px. */
  private drawSword(ctx: CanvasRenderingContext2D, x: number, y: number, ang: number, scale: number, alpha: number) {
    if (alpha <= 0) return;
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.translate(x, y);
    ctx.rotate(ang - Math.PI / 2);   // local +y points from hilt to tip
    ctx.scale(scale, scale);
    const L = 150;
    const grad = ctx.createLinearGradient(-14, 0, 14, 0);
    grad.addColorStop(0, "#6FB7EA"); grad.addColorStop(0.5, "#F4FBFF"); grad.addColorStop(1, "#4F95D0");
    ctx.fillStyle = grad;
    ctx.strokeStyle = INK;
    ctx.lineWidth = 2.2 / scale + 0.6;
    ctx.beginPath();   // blade
    ctx.moveTo(0, 0); ctx.lineTo(-13, -26); ctx.lineTo(-12, -L); ctx.lineTo(12, -L); ctx.lineTo(13, -26); ctx.closePath();
    ctx.fill(); ctx.stroke();
    ctx.strokeStyle = "rgba(60,120,190,0.8)";
    ctx.lineWidth = 1.4;
    ctx.beginPath(); ctx.moveTo(0, -6); ctx.lineTo(0, -L + 4); ctx.stroke();
    // crystal guard
    ctx.fillStyle = "#BFE6FF";
    ctx.strokeStyle = INK;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(-40, -L - 4); ctx.lineTo(-18, -L - 14); ctx.lineTo(0, -L - 8); ctx.lineTo(18, -L - 14);
    ctx.lineTo(40, -L - 4); ctx.lineTo(18, -L + 4); ctx.lineTo(0, -L - 1); ctx.lineTo(-18, -L + 4); ctx.closePath();
    ctx.fill(); ctx.stroke();
    // grip + pommel
    ctx.fillStyle = "#1E3A6E";
    ctx.fillRect(-6, -L - 46, 12, 36); ctx.strokeRect(-6, -L - 46, 12, 36);
    ctx.fillStyle = "#E8F6FF";
    ctx.beginPath(); ctx.moveTo(0, -L - 64); ctx.lineTo(10, -L - 52); ctx.lineTo(0, -L - 44); ctx.lineTo(-10, -L - 52); ctx.closePath();
    ctx.fill(); ctx.stroke();
    ctx.restore();
  }

  /** Cooldown ring above each puppet's head. */
  drawUi(ctx: CanvasRenderingContext2D, puppets: Puppet[], now: number) {
    for (const p of puppets) {
      if (!CFG.ult.kinds[p.id]) continue;
      const h: Pt = p.headPx();
      const x = h.x, y = h.y - 34, r = 15, c = this.charge(p, now);
      ctx.save();
      ctx.fillStyle = "rgba(10,20,35,0.55)";
      ctx.beginPath(); ctx.arc(x, y, r + 4, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = "rgba(255,255,255,0.18)";
      ctx.lineWidth = 4;
      ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.stroke();
      ctx.strokeStyle = c >= 1 ? "#9FE3FF" : "#5C8FC0";
      ctx.beginPath(); ctx.arc(x, y, r, -Math.PI / 2, -Math.PI / 2 + c * Math.PI * 2); ctx.stroke();
      if (c >= 1) {   // ready: pulsing glow + snowflake
        ctx.globalCompositeOperation = "lighter";
        ctx.strokeStyle = `rgba(160,230,255,${0.35 + 0.3 * Math.sin(this.time * 6)})`;
        ctx.lineWidth = 8;
        ctx.beginPath(); ctx.arc(x, y, r + 2, 0, Math.PI * 2); ctx.stroke();
        ctx.globalCompositeOperation = "source-over";
        ctx.strokeStyle = "#E8F8FF";
        ctx.lineWidth = 2;
        ctx.beginPath();
        for (let i = 0; i < 3; i++) {
          const a = (i * Math.PI) / 3 + Math.PI / 6;
          ctx.moveTo(x - Math.cos(a) * 8, y - Math.sin(a) * 8); ctx.lineTo(x + Math.cos(a) * 8, y + Math.sin(a) * 8);
        }
        ctx.stroke();
      }
      ctx.restore();
    }
  }
}
