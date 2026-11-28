// Flappy chim lac game flow:
//   TITLE (curtain closed) -> RESETTING -> OPENING -> READY (bird hovers, strings grow from the hand)
//   -> PLAY (columns move; strings attached = the bird follows the hand; no strings = it falls)
//   -> crash into bamboo or the dyke road -> DEAD -> CLOSING -> GAMEOVER (score, best) -> RESETTING ...
import type { Control } from "../puppet";
import { Background } from "../giong/background";
import { Curtain } from "../giong/curtain";
import { drawSprite } from "../giong/data";
import { HandRole } from "../giong/ropes";
import { Bird } from "./bird";
import type { FlappyData } from "./data";
import { F } from "./fcfg";
import { Pipes } from "./pipes";

export const BUILD = "flappy build 28-11 14:40";
console.info("[chim lac]", BUILD);

export type FState = "TITLE" | "RESETTING" | "OPENING" | "READY" | "PLAY" | "DEAD" | "CLOSING" | "GAMEOVER";

interface Feather { x: number; y: number; vx: number; vy: number; rot: number; vr: number; k: number; age: number }
interface Popup { x: number; y: number; age: number }

function loadBest(): number { try { return Number(localStorage.getItem("chimlac_best") || 0); } catch { return 0; } }
function saveBest(v: number) { try { localStorage.setItem("chimlac_best", String(v)); } catch { /* private mode */ } }

export class FlappyGame {
  state: FState = "TITLE";
  stateTime = 0;
  time = 0;
  scroll = 0;
  score = 0;
  best = loadBest();
  shake = 0;
  debug = false;

  readonly bird: Bird;
  readonly pipes: Pipes;
  readonly bg: Background;
  readonly curtain: Curtain;
  readonly hand = new HandRole("bird", "#2F7A55");
  private feathers: Feather[] = [];
  private popups: Popup[] = [];
  private impactAt = -9;
  private startKey = false;
  private groundY: number;

  constructor(private data: FlappyData, cropY: number) {
    this.groundY = data.stage.groundY;
    this.bird = new Bird(data.rig);
    this.pipes = new Pipes(data.fx, this.groundY);
    this.bg = new Background(data.stage, data.fx);
    this.curtain = new Curtain(data.fx, cropY);
    this.curtain.title = "CHIM LẠC";
    this.curtain.lines = ["Fly the lac bird through the bamboo", "Index finger: near wing · middle finger: far wing",
      "Show a hand to the camera for 1 s (or press Enter) to start"];
  }

  private set(s: FState) { this.state = s; this.stateTime = 0; }
  pressStart() { this.startKey = true; }

  /** One hand drives the bird: the hand nearest the bird on screen. */
  onHands(controls: Control[] | null, now: number) {
    if (!controls) return;
    const c = controls.length ? [...controls].sort((a, b) => Math.abs(a.palm.x - this.bird.x) - Math.abs(b.palm.x - this.bird.x))[0] : null;
    const allow = this.state === "OPENING" || this.state === "READY" || this.state === "PLAY";
    this.hand.onHand(c, now, allow);
  }

  private resetRound() {
    this.bird.reset();
    this.pipes.reset();
    this.score = 0;
    this.feathers = [];
    this.popups = [];
  }

  update(dt: number, now: number) {
    this.time += dt;
    this.stateTime += dt;
    this.shake = Math.max(0, this.shake - dt * 2.5);
    this.curtain.update(dt);
    this.bg.update(dt, this.time);
    this.hand.update(dt, this.bird.anchors(), now);

    switch (this.state) {
      case "TITLE":
      case "GAMEOVER": {
        const handReady = this.hand.presentTime > F.startHold && (this.state === "TITLE" || this.stateTime > 2.5);
        if (this.startKey || handReady) { this.curtain.lines = ["Get ready..."]; this.set("RESETTING"); }
        break;
      }
      case "RESETTING":
        if (this.stateTime > 0.7) { this.resetRound(); this.curtain.animate(0, F.curtainOpen); this.set("OPENING"); }
        break;
      case "OPENING":
        if (this.curtain.open) this.set("READY");
        break;
      case "READY":
        if (this.hand.attached || this.startKey) this.set("PLAY");
        break;
      case "DEAD":
        if (this.stateTime > F.deathHold && this.curtain.c === 0) this.curtain.animate(1, F.curtainClose);
        if (this.curtain.closed) {
          if (this.score > this.best) { this.best = this.score; saveBest(this.best); }
          this.curtain.lines = ["Game over", `Score: ${this.score}`, `Best: ${this.best}`, "Show a hand or press Enter to play again"];
          this.set("GAMEOVER");
        }
        break;
    }
    this.startKey = false;

    // bird
    const b = this.bird;
    if (this.state === "PLAY") {
      b.ropes = this.hand.ropes();
      b.mode = this.hand.attached ? "rope" : "fall";
    } else if (this.state !== "DEAD") {
      b.mode = this.hand.attached && this.state === "READY" ? "rope" : "hover";
      b.ropes = this.hand.ropes();
    }
    b.update(dt, this.time);
    if (b.mode === "dead" && b.y > this.groundY - 30) { b.y = this.groundY - 30; b.vy = 0; }

    if (this.state === "PLAY") {
      this.scroll += F.speed * dt;
      const passed = this.pipes.update(dt, b.x);
      if (passed) { this.score += passed; this.popups.push({ x: b.x + 40, y: b.y - 70, age: 0 }); }
      const circles = b.hitCircles();
      const ground = circles.some((c) => c.c.y + c.r > this.groundY);
      if (ground || this.pipes.hit(circles)) this.crash();
    }

    for (const f of this.feathers) { f.age += dt; f.vy += 260 * dt; f.vx *= 0.98; f.x += f.vx * dt; f.y += f.vy * dt * 0.6; f.rot += f.vr * dt; }
    this.feathers = this.feathers.filter((f) => f.age < 2.2);
    for (const p of this.popups) p.age += dt;
    this.popups = this.popups.filter((p) => p.age < 0.9);
  }

  private crash() {
    const b = this.bird;
    this.impactAt = this.time;
    this.shake = 1;
    for (let i = 0; i < 14; i++) this.feathers.push({ x: b.x, y: b.y, vx: (Math.random() - 0.5) * 420, vy: -120 - Math.random() * 280,
      rot: Math.random() * 6, vr: (Math.random() - 0.5) * 8, k: i % 3, age: 0 });
    b.mode = "dead";
    b.vy = -280;
    this.hand.cut(performance.now());
    this.set("DEAD");
  }

  // ------------------------------------------------------------------ draw (stage transform already set)
  drawStage(ctx: CanvasRenderingContext2D) {
    const t = this.time;
    this.bg.drawIds(ctx, this.scroll, t, ["sky", "clouds", "mountains", "village", "fields"]);
    // background 20% darker so the bird and the bamboo stand out
    ctx.save();
    ctx.fillStyle = `rgba(0,0,0,${F.bgDarken})`;
    ctx.fillRect(-50, -50, 1700, 1000);
    ctx.restore();
    this.pipes.draw(ctx);
    ctx.save();
    ctx.filter = `brightness(${(1 - F.bgDarken) * 100}%)`;
    this.bg.drawIds(ctx, this.scroll, t, ["ground"]);
    ctx.restore();
    this.bird.draw(ctx);
    const it = t - this.impactAt;
    if (it < 0.5) drawSprite(ctx, this.data.fx.impact, this.bird.x + 60, this.bird.y, 1 + it * 2, it * 3, 1 - it * 2);
    for (const f of this.feathers) drawSprite(ctx, this.data.fx[`feather_${f.k}`], f.x, f.y, 0.9, f.rot + Math.sin(f.age * 6) * 0.4, Math.max(0, 1 - f.age / 2.2));
    if (this.debug) this.drawDebug(ctx);
    if (!this.curtain.closed) this.drawHud(ctx);
    this.curtain.draw(ctx, t);
  }

  drawStrings(ctx: CanvasRenderingContext2D, now: number) {
    if (this.curtain.closed || this.state === "DEAD") return;
    this.hand.draw(ctx, this.bird.anchors(), now);
  }

  private drawHud(ctx: CanvasRenderingContext2D) {
    ctx.save();
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    drawSprite(ctx, this.data.fx.score_plaque, 800, 160, 0.7);
    ctx.fillStyle = "#F4ECD6";
    ctx.font = "bold 40px Georgia, serif";
    ctx.fillText(String(this.score), 800, 162);
    ctx.font = "20px Georgia, serif";
    ctx.fillStyle = "rgba(244,236,214,0.9)";
    ctx.fillText(`Best ${this.best}`, 1460, 130);
    for (const p of this.popups) {
      ctx.globalAlpha = 1 - p.age / 0.9;
      ctx.fillStyle = "#D7A443";
      ctx.font = "bold 34px Georgia, serif";
      ctx.fillText("+1", p.x, p.y - p.age * 60);
    }
    ctx.globalAlpha = 1;
    if (this.state === "READY") {
      ctx.fillStyle = "#F4ECD6";
      ctx.font = "bold 30px Georgia, serif";
      ctx.fillText(this.hand.state === "DETACHED" ? "Show your hand to hold the strings" : "Hold on...", 800, 300);
    }
    ctx.fillStyle = "rgba(244,236,214,0.6)";
    ctx.font = "16px Georgia, serif";
    ctx.textAlign = "left";
    ctx.fillText(BUILD, 16, 880);
    ctx.restore();
  }

  private drawDebug(ctx: CanvasRenderingContext2D) {
    ctx.save();
    ctx.strokeStyle = "#f33";
    ctx.lineWidth = 2;
    for (const c of this.bird.hitCircles()) { ctx.beginPath(); ctx.arc(c.c.x, c.c.y, c.r, 0, Math.PI * 2); ctx.stroke(); }
    ctx.restore();
  }
}
