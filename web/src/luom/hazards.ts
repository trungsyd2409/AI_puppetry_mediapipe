// Everything that comes at Luom, plus the letters to pick up.
//   ground things : sheaf, stump, fence (jump), craters left by bombs (jump), they ride with the path
//   bullets       : low bursts of two after a muzzle flash at the right edge (jump)
//   planes, bombs : a plane drops a bomb ahead of him; a dark mark shows where it will land;
//                   the blast hurts if he is close, then a crater stays on the path
//   letters       : folded letters floating over the path, some up high (jump to catch them)
// Hazards are spaced in time (L.minGap) so there is always a way through.
import type { Pt } from "../config";
import { drawSprite } from "../giong/data";
import type { Circle } from "./boy";
import type { FxSprite } from "./data";
import { L } from "./lcfg";

export type HitKind = "obstacle" | "crater" | "bullet" | "bomb" | "blast";
export interface Thing { k: string; x: number; y: number; s: number; kind: "obstacle" | "crater" | "letter"; done: boolean; ph: number }
interface Bullet { x: number; y: number; done: boolean }
interface Burst { y: number; t: number; fired: number }
interface Plane { x: number; y: number; dropX: number; landX: number; dropped: boolean }
interface Bomb { x: number; y: number; vx: number; vy: number; landX: number; done: boolean }
export interface Blast { x: number; y: number; age: number }
export interface Events { hits: HitKind[]; letters: Pt[]; blasts: Pt[] }

const rand = (a: number, b: number) => a + Math.random() * (b - a);
const lerpR = (r: [number, number][], d: number): [number, number] =>
  [r[0][0] + (r[1][0] - r[0][0]) * d, r[0][1] + (r[1][1] - r[0][1]) * d];

function circleBox(c: Circle, x0: number, y0: number, x1: number, y1: number): boolean {
  const nx = Math.max(x0, Math.min(c.c.x, x1)), ny = Math.max(y0, Math.min(c.c.y, y1));
  return (c.c.x - nx) ** 2 + (c.c.y - ny) ** 2 < c.r * c.r;
}

export class Hazards {
  things: Thing[] = [];
  bullets: Bullet[] = [];
  bursts: Burst[] = [];
  planes: Plane[] = [];
  bombs: Bomb[] = [];
  blasts: Blast[] = [];
  private time = 0;
  private dist = 0;
  private nextGround = 0;
  private nextPlane = 0;
  private nextBurst = 0;
  private busy: number[] = [];

  constructor(private fx: Record<string, FxSprite>, private ground: number, private boyX: number) {
    this.reset();
  }

  reset() {
    this.things = []; this.bullets = []; this.bursts = []; this.planes = []; this.bombs = []; this.blasts = [];
    this.time = 0; this.dist = 0; this.busy = [];
    this.nextGround = 900; this.nextPlane = 6; this.nextBurst = 9;
  }

  private free(arrive: number) { return this.busy.every((b) => Math.abs(b - arrive) >= L.minGap); }
  private book(arrive: number) { this.busy.push(arrive); }

  /** d = difficulty 0..1, speed = ground px/s. */
  update(dt: number, speed: number, d: number, circles: Circle[] | null, canHit: boolean): Events {
    const ev: Events = { hits: [], letters: [], blasts: [] };
    this.time += dt;
    this.dist += speed * dt;
    this.busy = this.busy.filter((b) => b > this.time - 1);
    const G = this.ground, spawnX = 1780;

    // ---- spawning
    if (this.dist >= this.nextGround) {
      const arrive = this.time + (spawnX - this.boyX) / Math.max(1, speed);
      if (this.free(arrive)) {
        this.book(arrive);
        const k = ["sheaf", "stump", "fence"][Math.floor(Math.random() * 3)];
        const s = L.obstacleScale * rand(0.9, 1.05);
        this.things.push({ k, x: spawnX, y: G + 4, s, kind: "obstacle", done: false, ph: 0 });
        const gap = lerpR(L.gapPx, d);
        const next = rand(gap[0], gap[1]);
        if (Math.random() < 0.3) this.letter(spawnX, G - 330);                 // reward for the jump
        else if (Math.random() < L.letterChance) this.letter(spawnX + next * 0.5, Math.random() < 0.5 ? G - 230 : G - 430);
        this.nextGround = this.dist + next;
      } else this.nextGround = this.dist + 80;
    }
    if (this.time >= this.nextPlane) {
      const landX = this.boyX + rand(330, 700);
      const fall = Math.sqrt((2 * (G - 300)) / L.bombGravity);
      const arrive = this.time + 1.2 + fall + (landX - this.boyX) / Math.max(1, speed);
      if (this.free(arrive)) {
        this.book(arrive);
        const y = rand(230, 300);
        this.planes.push({ x: 1900, y, landX, dropX: landX + L.planeSpeed * Math.sqrt((2 * (G - y - 20)) / L.bombGravity), dropped: false });
        const r = lerpR(L.planeEvery, d);
        this.nextPlane = this.time + rand(r[0], r[1]);
      } else this.nextPlane = this.time + 0.4;
    }
    if (this.time >= this.nextBurst) {
      const arrive = this.time + L.bulletWarn + (1700 - this.boyX) / (speed + L.bulletSpeed);
      if (this.free(arrive) && this.free(arrive + 0.25)) {
        this.book(arrive); this.book(arrive + 0.25);
        this.bursts.push({ y: G - L.bulletHeight + rand(-4, 4), t: 0, fired: 0 });
        const r = lerpR(L.bulletEvery, d);
        this.nextBurst = this.time + rand(r[0], r[1]);
      } else this.nextBurst = this.time + 0.4;
    }

    // ---- motion
    for (const o of this.things) { o.x -= speed * dt; o.ph += dt; }
    for (const b of this.bursts) {
      b.t += dt;
      while (b.t > L.bulletWarn + b.fired * 0.11 && b.fired < 2) { this.bullets.push({ x: 1680, y: b.y + b.fired * 3, done: false }); b.fired++; }
    }
    this.bursts = this.bursts.filter((b) => b.fired < 2);
    for (const b of this.bullets) b.x -= (speed + L.bulletSpeed) * dt;
    for (const p of this.planes) {
      p.x -= L.planeSpeed * dt;
      if (!p.dropped && p.x <= p.dropX) { p.dropped = true; this.bombs.push({ x: p.x - 10, y: p.y + 24, vx: -L.planeSpeed, vy: 0, landX: p.landX, done: false }); }
    }
    for (const b of this.bombs) {
      b.vy += L.bombGravity * dt; b.x += b.vx * dt; b.y += b.vy * dt;
      b.landX -= 0;   // the mark stays where the bomb will land
      if (b.y >= G - 6) {
        b.done = true;
        this.blasts.push({ x: b.x, y: G - 20, age: 0 });
        this.things.push({ k: "crater", x: b.x, y: G + 8, s: 1, kind: "crater", done: false, ph: 0 });
        ev.blasts.push({ x: b.x, y: G - 20 });
        if (circles && canHit && circles.some((c) => Math.hypot(c.c.x - b.x, c.c.y - (G - 50)) < L.blastRadius + c.r * 0.5)) ev.hits.push("blast");
      }
    }
    for (const bl of this.blasts) { bl.age += dt; bl.x -= speed * dt; }

    // ---- collisions
    if (circles) {
      for (const o of this.things) {
        if (o.done) continue;
        const sp = this.fx[o.k];
        if (o.kind === "letter") {
          const y = o.y + Math.sin(o.ph * 3) * 10;
          if (circles.some((c) => Math.hypot(c.c.x - o.x, c.c.y - y) < c.r + 30)) { o.done = true; ev.letters.push({ x: o.x, y }); }
          continue;
        }
        if (!canHit || !sp.box) continue;
        const [x0, y0r, x1, y1] = sp.box, s = o.s, y0 = o.kind === "crater" ? -22 : y0r;   // a crater catches the feet
        if (circles.some((c) => circleBox(c, o.x + x0 * s, o.y + y0 * s, o.x + x1 * s, o.y + y1 * s))) { o.done = true; ev.hits.push(o.kind); }
      }
      if (canHit) {
        const bb = this.fx.bullet.box!, s = 1.2;
        for (const b of this.bullets) {
          if (b.done) continue;
          if (circles.some((c) => circleBox(c, b.x + bb[0] * s, b.y + bb[1] * s, b.x + bb[2] * s, b.y + bb[3] * s))) { b.done = true; ev.hits.push("bullet"); }
        }
        const mb = this.fx.bomb.box!;
        for (const b of this.bombs) {
          if (b.done) continue;
          if (circles.some((c) => circleBox(c, b.x + mb[0] * 0.9, b.y + mb[1] * 0.9, b.x + mb[2] * 0.9, b.y + mb[3] * 0.9))) {
            b.done = true; ev.hits.push("bomb");
            this.blasts.push({ x: b.x, y: b.y, age: 0 }); ev.blasts.push({ x: b.x, y: b.y });
          }
        }
      }
    }

    // ---- clean up
    this.things = this.things.filter((o) => o.x > -200 && !(o.kind === "letter" && o.done));
    this.bullets = this.bullets.filter((b) => b.x > -120 && !b.done);
    this.planes = this.planes.filter((p) => p.x > -260);
    this.bombs = this.bombs.filter((b) => !b.done);
    this.blasts = this.blasts.filter((b) => b.age < 0.8);
    return ev;
  }

  private letter(x: number, y: number) {
    this.things.push({ k: "letter", x, y, s: 1, kind: "letter", done: false, ph: Math.random() * 6 });
  }

  // ------------------------------------------------------------------ draw
  drawSky(ctx: CanvasRenderingContext2D, t: number) {
    for (const p of this.planes) drawSprite(ctx, this.fx["plane_" + (Math.floor(t * 20) % 2)], p.x, p.y + Math.sin(t * 2 + p.y) * 4, 0.85);
  }

  /** Craters, obstacles and landing marks (on the path, behind Luom). */
  drawGround(ctx: CanvasRenderingContext2D) {
    for (const b of this.bombs) {   // landing mark grows as the bomb comes down
      const k = Math.min(1, Math.max(0, (b.y - 200) / (this.ground - 200)));
      ctx.save();
      ctx.fillStyle = `rgba(40,20,10,${0.15 + 0.35 * k})`;
      ctx.beginPath(); ctx.ellipse(b.x + b.vx * 0, this.ground + 2, 30 + 50 * k, 7 + 6 * k, 0, 0, Math.PI * 2); ctx.fill();
      ctx.restore();
    }
    for (const o of this.things) if (o.kind === "crater") drawSprite(ctx, this.fx[o.done ? "crater" : "crater_hi"], o.x, o.y, o.s);
    for (const o of this.things) if (o.kind === "obstacle") drawSprite(ctx, this.fx[o.done ? o.k : o.k + "_hi"], o.x, o.y, o.s, o.done ? 0.25 : 0);
  }

  /** Letters, bullets, bombs and blasts (in front of Luom). */
  drawFront(ctx: CanvasRenderingContext2D, t: number) {
    for (const o of this.things) if (o.kind === "letter")
      drawSprite(ctx, this.fx.letter_hi, o.x, o.y + Math.sin(o.ph * 3) * 10, 1.1, Math.sin(o.ph * 2) * 0.25);
    for (const b of this.bursts) {   // muzzle flash at the right edge
      const on = Math.floor(b.t * 10) % 2 === 0;
      if (on) drawSprite(ctx, this.fx.explode_0, 1590, b.y, 0.35, 0, 0.9);
    }
    for (const b of this.bullets) drawSprite(ctx, this.fx.bullet_hi, b.x, b.y, 1.2);
    for (const b of this.bombs) drawSprite(ctx, this.fx.bomb_hi, b.x, b.y, 0.9, Math.atan2(b.vy, b.vx) - Math.PI / 2);
    for (const b of this.blasts) drawSprite(ctx, this.fx["explode_" + Math.min(3, Math.floor(b.age / 0.15))], b.x, b.y, 1.15, 0, 1 - Math.max(0, b.age - 0.5) * 3);
    void t;
  }

  drawDebug(ctx: CanvasRenderingContext2D) {
    ctx.save();
    ctx.strokeStyle = "#0ff"; ctx.lineWidth = 2;
    for (const o of this.things) {
      const sp = this.fx[o.k];
      if (!sp.box) continue;
      const [x0, y0, x1, y1] = sp.box;
      ctx.strokeRect(o.x + x0 * o.s, o.y + y0 * o.s, (x1 - x0) * o.s, (y1 - y0) * o.s);
    }
    const bb = this.fx.bullet.box!;
    for (const b of this.bullets) ctx.strokeRect(b.x + bb[0] * 1.2, b.y + bb[1] * 1.2, (bb[2] - bb[0]) * 1.2, (bb[3] - bb[1]) * 1.2);
    const by = this.ground - L.bulletHeight;
    ctx.beginPath(); ctx.moveTo(0, by); ctx.lineTo(1600, by); ctx.setLineDash([8, 8]); ctx.stroke();
    ctx.restore();
  }
}
