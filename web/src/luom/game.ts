// Luom runner game flow:
//   TITLE (curtain closed) -> RESETTING -> OPENING -> READY (Luom stands, strings grow from the hand)
//   -> PLAY (he skips along; a quick upward flick of the hand = jump; he must land before the next one)
//   -> hit: he trips and gets up (10 hearts) -> 0 hearts: DEAD -> curtain -> GAMEOVER (score, best) -> ...
import type { Control } from "../puppet";
import { Background } from "../giong/background";
import { Curtain } from "../giong/curtain";
import { drawSprite } from "../giong/data";
import { clamp, smoothstep } from "../giong/mat";
import { HandRole } from "../giong/ropes";
import { Boy } from "./boy";
import type { LuomData, SkyTime } from "./data";
import { Hazards } from "./hazards";
import { L } from "./lcfg";
import { lightOverlay } from "./prep";

export const BUILD = "luom build 28-11 23:30 double jump";
console.info("[luom]", BUILD);

export type LState = "TITLE" | "RESETTING" | "OPENING" | "READY" | "PLAY" | "DEAD" | "GAMEOVER";

interface Puff { x: number; y: number; age: number; s: number }
interface Note { x: number; y: number; age: number; k: number }
interface Popup { x: number; y: number; age: number; text: string; color: string }
interface Flyer { x: number; y: number; age: number }

const BACK = ["sky", "clouds", "far", "mountains", "village", "river", "field", "path"];
const INK = "#2A1C14", NGA = "#EBDDB8", SON = "#A33A27", VANG = "#D7AE5A";

function loadBest(): number { try { return Number(localStorage.getItem("luom_best") || 0); } catch { return 0; } }
function saveBest(v: number) { try { localStorage.setItem("luom_best", String(v)); } catch { /* private mode */ } }
const hex = (h: string) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
const mixC = (a: number[], b: number[], u: number) => a.map((v, i) => v + (b[i] - v) * u);
const rgb = (c: number[], a = 1) => `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a})`;

export class LuomGame {
  state: LState = "TITLE";
  stateTime = 0;
  time = 0;
  playTime = 0;
  scroll = 0;
  speed = 0;
  hp = L.hp;
  letters = 0;
  best = loadBest();
  shake = 0;
  debug = false;
  tod = 0;

  readonly boy: Boy;
  readonly hz: Hazards;
  readonly bg: Background;
  readonly curtain: Curtain;
  readonly hand = new HandRole("luom", "#C9A35A");
  private dust: Puff[] = [];
  private notes: Note[] = [];
  private popups: Popup[] = [];
  private flyers: Flyer[] = [];
  private startKey = false;
  private nextNote = 1;
  private lastStep = 0;
  private overlay: HTMLCanvasElement | null = null;
  private vignette: HTMLCanvasElement | null = null;
  private handY = NaN;
  private handT = 0;
  private handV = 0;        // upward speed of the hand (stage px/s)
  private armed = true;
  jumps = 0;
  private G: number;
  private cropY: number;

  constructor(private data: LuomData, cropY: number) {
    this.cropY = cropY;
    this.G = data.stage.groundY;
    this.boy = new Boy(data.rig, this.G);
    this.boy.maxJump = L.maxJumpFrac * (this.G - cropY);
    this.hz = new Hazards(data.fx, this.G, this.boy.x);
    this.bg = new Background(data.stage, data.fx);
    this.curtain = new Curtain(data.fx, cropY);
    this.curtain.title = "LƯỢM";
    this.curtain.style = { title: "#5A321B", card: "#E6D4AA", edge: INK, accent: SON, text: INK, width: 880 };
    this.curtain.lines = ["Run Luom through the ripe rice fields", "Flick the hand up to jump, flick again in the air to double jump",
      "Index finger: shoulder · middle finger: cap",
      "Show a hand for 1 s (or press Enter) to start"];
  }

  private set(s: LState) { this.state = s; this.stateTime = 0; }
  pressStart() { this.startKey = true; }

  onKey(code: string, down: boolean) {
    const before = this.boy.doubleAt;
    if (code === "Space" && down && (this.state === "PLAY" || this.state === "READY") && this.boy.jump(L.keyJump)) {
      this.jumps++;
      if (this.boy.doubleAt !== before) this.doublePuff();
    }
  }

  /** Paper cloud puff under the feet on the double jump. */
  private doublePuff() {
    const f = this.boy.feet();
    for (let i = 0; i < 3; i++) this.dust.push({ x: f.x - 30 + i * 30, y: f.y + 4, age: 0, s: 0.8 });
  }

  /** One hand drives Luom: the hand nearest to him on screen. */
  onHands(controls: Control[] | null, now: number) {
    if (!controls) return;
    const c = controls.length ? [...controls].sort((a, b) => Math.abs(a.palm.x - this.boy.x) - Math.abs(b.palm.x - this.boy.x))[0] : null;
    const allow = this.state === "OPENING" || this.state === "READY" || this.state === "PLAY";
    this.hand.onHand(c, now, allow);
    // hand speed from the filtered fingertips, measured per camera sample
    if (c && this.hand.state !== "DETACHED") {
      const y = (this.hand.tips[0].y + this.hand.tips[1].y) / 2;
      const dt = (now - this.handT) / 1000;
      if (!Number.isNaN(this.handY) && dt > 0.005 && dt < 0.25) this.handV = this.handV * 0.35 + ((this.handY - y) / dt) * 0.65;
      this.handY = y; this.handT = now;
    } else { this.handY = NaN; this.handV = 0; }
  }

  /** Jump height for a flick of speed v. */
  private flickHeight(v: number) { return L.jumpMin + (v - L.flickSpeed) * L.flickGain; }

  get distance() { return Math.floor(this.scroll / L.pxPerMetre); }
  get score() { return this.letters * L.letterPoints + this.distance; }

  private resetRound() {
    this.boy.reset();
    this.hz.reset();
    this.hp = L.hp; this.letters = 0; this.scroll = 0; this.playTime = 0; this.speed = 0; this.tod = 0;
    this.dust = []; this.notes = []; this.popups = []; this.flyers = [];
  }

  update(dt: number, now: number) {
    this.time += dt;
    this.stateTime += dt;
    this.shake = Math.max(0, this.shake - dt * 2.5);
    this.curtain.update(dt);
    this.bg.update(dt, this.time);
    this.hand.update(dt, this.boy.anchors(), now);

    switch (this.state) {
      case "TITLE":
      case "GAMEOVER": {
        const handReady = this.hand.presentTime > L.startHold && (this.state === "TITLE" || this.stateTime > 2.5);
        if (this.startKey || handReady) { this.curtain.lines = ["Get ready..."]; this.set("RESETTING"); }
        break;
      }
      case "RESETTING":
        if (this.stateTime > 0.7) { this.resetRound(); this.curtain.animate(0, L.curtainOpen); this.set("OPENING"); }
        break;
      case "OPENING":
        if (this.curtain.open) this.set("READY");
        break;
      case "READY":
        if ((this.hand.attached && this.hand.attachedTime > L.readyHold) || this.startKey) this.set("PLAY");
        break;
      case "DEAD":
        if (this.stateTime > L.deathHold && this.curtain.c === 0) this.curtain.animate(1, L.curtainClose);
        if (this.curtain.closed) {
          if (this.score > this.best) { this.best = this.score; saveBest(this.best); }
          this.curtain.lines = ["Game over", `Letters delivered: ${this.letters}`, `Distance: ${this.distance} m`,
            `Score: ${this.score}   ·   Best: ${this.best}`, "Show a hand or press Enter to play again"];
          this.set("GAMEOVER");
        }
        break;
    }
    this.startKey = false;

    // ---- Luom
    const b = this.boy;
    const playing = this.state === "PLAY";
    const d = clamp(this.playTime / L.rampTime, 0, 1);
    const target = playing ? (L.speed[0] + (L.speed[1] - L.speed[0]) * d) * (b.tripping ? 0.3 : 1) : 0;
    this.speed += (target - this.speed) * Math.min(1, dt * (b.tripping || this.state === "DEAD" ? 4 : 1.5));
    b.run += ((playing ? 1 : 0) - b.run) * Math.min(1, dt * 4);
    b.skipHz = L.skipHz * Math.max(0.7, Math.sqrt(this.speed / L.speed[0]));
    const steps = Math.floor(b.ph / Math.PI);
    // jump: a quick upward flick while on the path; land before the next one
    if (performance.now() - this.handT > 150) this.handV *= Math.pow(0.02, dt);   // no new camera sample: forget the speed
    if ((playing || this.state === "READY") && this.hand.attached) {
      // re-arm once the hand slows down: on the path, or in the air while a double jump is left
      if (!this.armed && this.handV < L.flickRearm && (b.grounded || b.airJumps > 0)) this.armed = true;
      const before = b.doubleAt;
      if (this.armed && this.handV > L.flickSpeed && b.jump(this.flickHeight(this.handV))) {
        this.armed = false; this.jumps++;
        if (b.doubleAt !== before) this.doublePuff();
      } else if (!b.grounded) b.boost(this.flickHeight(this.handV));
    }
    b.update(dt, this.time);

    if (playing) {
      this.playTime += dt;
      this.scroll += this.speed * dt;
      this.tod = clamp(this.playTime / L.timeOfDay, 0, 1);
    } else if (this.state === "DEAD") this.scroll += this.speed * dt;

    // ---- hazards
    if (playing || this.state === "DEAD") {
      const ev = this.hz.update(dt, this.speed, d, playing ? b.hitCircles() : null, playing && !b.invulnerable);
      for (const p of ev.letters) {
        this.letters++;
        this.flyers.push({ x: p.x, y: p.y, age: 0 });
        this.popups.push({ x: p.x, y: p.y - 30, age: 0, text: `+${L.letterPoints}`, color: VANG });
      }
      if (ev.blasts.length) this.shake = Math.max(this.shake, 0.6);
      if (ev.hits.length && playing) this.hurt();
    }

    // ---- dust, notes, popups
    const feet = b.feet();
    if (b.run > 0.5 && b.e < 4 && !b.tripping && Math.floor(b.ph / Math.PI) !== steps && this.time - this.lastStep > 0.12) {
      this.lastStep = this.time;
      this.dust.push({ x: feet.x, y: this.G - 6, age: 0, s: 0.5 });
    }
    if (b.landed > 0.18) for (let i = 0; i < 3; i++) this.dust.push({ x: feet.x - 30 + i * 30, y: this.G - 6, age: 0, s: 0.7 });
    for (const p of this.dust) { p.age += dt; p.x -= (this.speed * 0.8 + 30) * dt; p.y -= 18 * dt; }
    this.dust = this.dust.filter((p) => p.age < 0.7);
    if (playing && !b.tripping && (this.nextNote -= dt) < 0) {
      const m = b.mouth();
      this.notes.push({ x: m.x + 60, y: m.y - 50, age: 0, k: Math.random() < 0.5 ? 0 : 1 });
      this.nextNote = 1.6 + Math.random() * 1.6;
    }
    for (const n of this.notes) n.age += dt;
    this.notes = this.notes.filter((n) => n.age < 2);
    for (const p of this.popups) p.age += dt;
    this.popups = this.popups.filter((p) => p.age < 0.9);
    for (const f of this.flyers) f.age += dt;
    this.flyers = this.flyers.filter((f) => f.age < 0.6);
  }

  private hurt() {
    const b = this.boy;
    this.hp--;
    this.shake = Math.max(this.shake, 0.7);
    const h = b.headCircle().c;
    this.popups.push({ x: h.x, y: h.y - 60, age: 0, text: "-1", color: "#E0533A" });
    if (this.hp <= 0) {
      this.hp = 0;
      b.dead = true; b.deadAt = this.time; b.e = 0;
      this.hand.cut(performance.now());
      this.set("DEAD");
    } else b.hitAt = this.time;
  }

  // ------------------------------------------------------------------ draw (stage transform already set)
  private sky(): SkyTime & { mix: { top: number[]; bottom: number[]; tint: number[] } } {
    const T = this.data.stage.skyTimes, keys = ["morning", "afternoon", "dusk"] as const;
    const f = this.tod * 2, i = Math.min(1, Math.floor(f)), w = f - i;
    const A = T[keys[i]], B = T[keys[i + 1]];
    return { ...A, mix: { top: mixC(hex(A.top), hex(B.top), w), bottom: mixC(hex(A.bottom), hex(B.bottom), w), tint: mixC(A.tint, B.tint, w) } };
  }

  drawStage(ctx: CanvasRenderingContext2D) {
    const t = this.time, st = this.data.stage, sp = st.sprites, G = this.G;
    const sky = this.sky().mix;
    // sky and the drum sun on its arc
    const gr = ctx.createLinearGradient(0, this.cropY, 0, 640);
    gr.addColorStop(0, rgb(sky.top)); gr.addColorStop(1, rgb(sky.bottom));
    ctx.fillStyle = gr; ctx.fillRect(-60, -60, 1720, 1020);
    const arc = st.sun.arc;
    const sx = arc.x0 + (arc.x1 - arc.x0) * this.tod;
    const sy = arc.yLow - (arc.yLow - arc.yHigh) * Math.sin(Math.PI * (0.25 + 0.75 * this.tod));
    drawSprite(ctx, sp[st.sun.sprite], sx, sy, st.sun.scale, t * 0.05);

    this.bg.drawIds(ctx, this.scroll, t, ["sky", "clouds"]);
    this.hz.drawSky(ctx, t);
    this.bg.drawIds(ctx, this.scroll, t, BACK.slice(2));
    this.hz.drawGround(ctx);
    for (const p of this.dust) drawSprite(ctx, this.data.fx.dust, p.x, p.y, p.s + p.age * 0.8, 0, 1 - p.age / 0.7);
    this.boy.draw(ctx);
    for (const n of this.notes)
      drawSprite(ctx, this.data.fx["note_" + n.k], n.x + n.age * 30 - n.age * this.speed * 0.2, n.y - n.age * 50 + Math.sin(n.age * 5) * 6,
        0.8, Math.sin(n.age * 3) * 0.3, 1 - n.age / 2);
    this.hz.drawFront(ctx, t);
    this.bg.drawIds(ctx, this.scroll, t, ["front"]);
    // fixed stage frame
    drawSprite(ctx, sp[st.frame.bottom], 0, 900);
    drawSprite(ctx, sp[st.frame.top], 0, this.cropY);
    this.drawLight(ctx, sky.tint, G);
    if (this.debug) this.drawDebug(ctx);
    if (!this.curtain.closed) this.drawHud(ctx);
    this.curtain.draw(ctx, t);
  }

  /** Time-of-day tint, warm vignette centred on Luom and do paper grain, all from images baked once. */
  private drawLight(ctx: CanvasRenderingContext2D, tint: number[], G: number) {
    const st = this.data.stage, V = st.vignette, y0 = this.cropY;
    if (!this.overlay) {
      this.overlay = lightOverlay(st.paper, y0, this.boy.x + 30, G - 170, V.color, V.strength, V.radius, 0.3, true);
      this.vignette = lightOverlay(st.paper, y0, this.boy.x + 30, G - 170, V.color, 0.6, V.radius, 0, true);
    }
    ctx.save();
    if (tint[3] > 0.001) { ctx.fillStyle = rgb(tint, Math.min(0.5, tint[3] * 1.4)); ctx.fillRect(-60, y0, 1720, 960 - y0); }
    ctx.drawImage(this.overlay, 0, y0, 1600, 900 - y0);
    const dusk = Math.max(0, this.tod - 0.6) / 0.4;
    if (dusk > 0.01) { ctx.globalAlpha = dusk; ctx.drawImage(this.vignette!, 0, y0, 1600, 900 - y0); }
    ctx.restore();
  }

  drawStrings(ctx: CanvasRenderingContext2D, now: number) {
    if (this.curtain.closed) return;
    this.hand.draw(ctx, this.boy.anchors(), now);
  }

  private text(ctx: CanvasRenderingContext2D, s: string, x: number, y: number, color = NGA) {
    ctx.fillStyle = "rgba(20,10,6,0.65)"; ctx.fillText(s, x + 2, y + 2);
    ctx.fillStyle = color; ctx.fillText(s, x, y);
  }

  private drawHud(ctx: CanvasRenderingContext2D) {
    const fx = this.data.fx, y = this.cropY + 115;
    ctx.save();
    for (let i = 0; i < L.hp; i++) drawSprite(ctx, i < this.hp ? fx.heart : fx.heart_empty, 50 + i * 40, y, 0.9);
    drawSprite(ctx, fx.letter, 1300, y, 0.95);
    ctx.textBaseline = "middle";
    ctx.font = "bold 30px Georgia, serif";
    ctx.textAlign = "left";
    this.text(ctx, `× ${this.letters}`, 1334, y + 2);
    ctx.font = "22px Georgia, serif";
    this.text(ctx, `${this.distance} m`, 1440, y + 2);
    ctx.textAlign = "right";
    ctx.font = "18px Georgia, serif";
    this.text(ctx, `Best ${this.best}`, 1560, y + 36, "rgba(235,221,184,0.85)");
    ctx.textAlign = "center";
    for (const f of this.flyers) {   // caught letters fly into the counter
      const u = smoothstep(0, 0.6, f.age);
      drawSprite(ctx, fx.letter, f.x + (1300 - f.x) * u, f.y + (y - f.y) * u - Math.sin(u * Math.PI) * 80, 1.1 - 0.2 * u, u * 6);
    }
    for (const p of this.popups) {
      ctx.globalAlpha = 1 - p.age / 0.9;
      ctx.font = "bold 34px Georgia, serif";
      this.text(ctx, p.text, p.x, p.y - p.age * 60, p.color);
    }
    ctx.globalAlpha = 1;
    const msg = this.state === "READY"
      ? (this.hand.state === "DETACHED" ? "Show your hand to take the strings" : "Hold the strings... get ready to run!")
      : this.state === "PLAY" && !this.hand.attached ? "Show your hand to take the strings again" : "";
    if (msg) { ctx.font = "bold 32px Georgia, serif"; this.text(ctx, msg, 800, this.cropY + 190); }
    if (this.state === "PLAY" && this.playTime < 6 && this.hand.attached) {
      ctx.font = "26px Georgia, serif";
      this.text(ctx, "Flick the hand up to jump · flick again in the air for a double jump", 800, this.cropY + 190, `rgba(235,221,184,${1 - smoothstep(4, 6, this.playTime)})`);
    }
    ctx.fillStyle = "rgba(235,221,184,0.5)";
    ctx.font = "15px Georgia, serif";
    ctx.textAlign = "left";
    ctx.fillText(BUILD, 16, 812);
    ctx.restore();
  }

  private drawDebug(ctx: CanvasRenderingContext2D) {
    ctx.save();
    ctx.strokeStyle = "#f33"; ctx.lineWidth = 2;
    for (const c of this.boy.hitCircles()) { ctx.beginPath(); ctx.arc(c.c.x, c.c.y, c.r, 0, Math.PI * 2); ctx.stroke(); }
    this.hz.drawDebug(ctx);
    ctx.fillStyle = "#fff"; ctx.font = "16px monospace"; ctx.textAlign = "left";
    ctx.fillText(`e ${this.boy.e.toFixed(0)}  hand ${this.handV.toFixed(0)}  armed ${this.armed}  speed ${this.speed.toFixed(0)}  tod ${this.tod.toFixed(2)}`, 20, this.cropY + 170);
    ctx.restore();
  }
}
