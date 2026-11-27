// Game flow:
//   TITLE (curtain closed) -> RESETTING -> OPENING -> PLAY -> (shell hits) FALL 3 s -> respawn in place -> PLAY ...
//   last life lost: FALL -> CLOSING -> GAMEOVER (curtain closed, score) -> RESETTING -> OPENING
import type { Control } from "../puppet";
import { Background } from "./background";
import { Curtain } from "./curtain";
import { drawSprite, type GData } from "./data";
import { G } from "./gcfg";
import { Ragdoll } from "./ragdoll";
import { HandRole } from "./ropes";
import { Rider } from "./rider";
import { Shells } from "./shells";

export type GameState = "TITLE" | "OPENING" | "PLAY" | "FALL" | "CLOSING" | "RESETTING" | "GAMEOVER";

export class Game {
  state: GameState = "TITLE";
  stateTime = 0;
  time = 0;
  scroll = 0;
  lives = G.lives;
  distance = 0;
  blocks = 0;
  playTime = 0;
  shake = 0;
  debug = false;
  invuln = 0;            // s of blinking after a respawn: shells pass through
  private banner = "";   // short text over the stage after a respawn
  private bannerT = 0;

  readonly rider: Rider;
  readonly bg: Background;
  readonly shells: Shells;
  readonly curtain: Curtain;
  readonly bamboo = new HandRole("bamboo", "#2F7A55");
  readonly legs = new HandRole("legs", "#A63A25", true);
  private ragdoll: Ragdoll | null = null;
  private acc = 0;
  private hoofY: number[] = [];
  private startKey = false;

  constructor(private data: GData, cropY: number) {
    this.rider = new Rider(data);
    this.bg = new Background(data.stage, data.fx);
    this.shells = new Shells(data.fx, data.stage.floorY);
    this.curtain = new Curtain(data.fx, cropY);
    this.showTitle();
  }

  get score() { return Math.floor(this.distance / G.pxPerPoint) + this.blocks * G.blockScore; }

  private set(s: GameState) { this.state = s; this.stateTime = 0; }

  private showTitle() {
    this.curtain.title = "THÁNH GIÓNG";
    this.curtain.lines = ["The boy on the horse", "Left hand: bamboo strings · right hand: horse leg strings",
      "Show a hand to the camera for 1 s (or press Enter) to start"];
  }

  pressStart() { this.startKey = true; }

  private resetRound() {
    this.rider.reset();
    this.shells.clear();
    this.ragdoll = null;
    this.hoofY = [];
  }

  /** Hands sorted by screen x: left hand -> bamboo, right hand -> legs. One hand: by screen side. */
  onHands(controls: Control[] | null, now: number) {
    if (!controls) return;
    let left: Control | null = null, right: Control | null = null;
    const hs = [...controls].sort((a, b) => a.palm.x - b.palm.x);
    if (hs.length >= 2) { left = hs[0]; right = hs[hs.length - 1]; }
    else if (hs.length === 1) { if (hs[0].palm.x < 800) left = hs[0]; else right = hs[0]; }
    const allow = this.state === "OPENING" || this.state === "PLAY";
    this.bamboo.onHand(left, now, allow);
    this.legs.onHand(right, now, allow);
  }

  update(dt: number, now: number) {
    this.time += dt;
    this.stateTime += dt;
    this.shake = Math.max(0, this.shake - dt * 2.5);
    this.curtain.update(dt);
    this.bg.update(dt, this.time);

    const anchors = this.rider.anchors();
    this.bamboo.update(dt, anchors.bamboo, now);
    this.legs.update(dt, anchors.legs, now);

    switch (this.state) {
      case "TITLE":
      case "GAMEOVER":
        const handReady = Math.max(this.bamboo.presentTime, this.legs.presentTime) > G.startHold
          && (this.state === "TITLE" || this.stateTime > 3);   // time to read the score first
        if (this.startKey || handReady) {
          if (this.state === "GAMEOVER") { this.lives = G.lives; this.distance = 0; this.blocks = 0; this.playTime = 0; }
          this.curtain.lines = ["Round 1", "Get ready..."];
          this.set("RESETTING");
        }
        break;
      case "RESETTING":
        if (this.stateTime > 0.7) { this.resetRound(); this.curtain.animate(0, G.curtainOpen); this.set("OPENING"); }
        break;
      case "OPENING":
        if (this.curtain.open) this.set("PLAY");
        break;
      case "FALL":
        if (this.stateTime > G.fallTime) {
          if (this.lives > 0) this.respawn();
          else { this.curtain.animate(1, G.curtainClose); this.set("CLOSING"); }
        }
        break;
      case "CLOSING":
        if (this.curtain.closed) {
          this.curtain.lines = ["Game over", `Score: ${this.score}`,
            `Distance ${Math.floor(this.distance / 100)} m · ${this.blocks} shells blocked`,
            "Show a hand or press Enter to play again"];
          this.set("GAMEOVER");
        }
        break;
    }
    this.startKey = false;

    this.invuln = Math.max(0, this.invuln - dt);
    this.bannerT = Math.max(0, this.bannerT - dt);
    const alive = this.state === "OPENING" || this.state === "PLAY" || this.state === "RESETTING";
    if (alive) this.stepRider(dt);
    if (this.state === "PLAY") {
      this.playTime += dt;
      this.scroll += this.rider.speed * dt;
      this.distance += this.rider.speed * dt;
    }
    if (this.ragdoll) this.ragdoll.step(dt);

    const events = this.shells.update(dt, this.state === "PLAY", this.playTime, this.state === "PLAY" ? this.rider.hitShapes() : null);
    for (const e of events) {
      if (e.kind === "block" || e.kind === "stomp") this.blocks++;
      else if (e.kind === "hit" && this.state === "PLAY" && this.invuln <= 0) this.fall(e.part, { x: e.vx, y: e.vy });
    }
  }

  private stepRider(dt: number) {
    const r = this.rider;
    r.ropes = { legs: this.legs.ropes(), bamboo: this.bamboo.ropes() };
    r.update(dt, this.time, this.legs.attached);
    this.acc += dt;
    let n = 0;
    while (this.acc >= G.fixedDt && n < 8) { r.stepBamboo(G.fixedDt, this.bamboo.attached); this.acc -= G.fixedDt; n++; }
    if (n === 8) this.acc = 0;
    r.finishPose();
    // hoof strikes kick up dust
    if (r.run > 0.3) {
      const hooves = [...r.hoofPoints(), ...r.hindHoofPoints()];
      hooves.forEach((h, i) => {
        const prev = this.hoofY[i];
        const ground = r.floorY - 14;
        if (prev !== undefined && prev < ground && h.y >= ground) this.shells.kickDust(h, r.speed);
        this.hoofY[i] = h.y;
      });
    }
  }

  /** Back on the horse where it fell: a burst of dust, a short blink, strings grow again. */
  private respawn() {
    this.resetRound();
    const r = this.rider;
    for (let i = 0; i < 14; i++) this.shells.kickDust({ x: r.M.body[4] + (Math.random() - 0.5) * 260, y: r.floorY }, -120, 1);
    this.shells.burst({ x: G.horseX - 20, y: r.floorY - 200 });   // starts at the smoke frames
    this.invuln = 2;
    this.banner = this.lives === 1 ? "Last life!" : `${this.lives} lives left`;
    this.bannerT = 1.8;
    this.set("PLAY");
  }

  private fall(part: string, vel: { x: number; y: number }) {
    this.lives--;
    this.shake = 1;
    this.ragdoll = new Ragdoll(this.rider, part, vel);
    this.bamboo.cut(performance.now());
    this.legs.cut(performance.now());
    this.set("FALL");
  }

  // ------------------------------------------------------------------ draw (stage transform already set)
  drawStage(ctx: CanvasRenderingContext2D) {
    const t = this.time;
    this.bg.drawBack(ctx, this.scroll, t);
    // darken the background a little (cheap: one translucent rect over the back layers)
    ctx.save();
    ctx.fillStyle = `rgba(0,0,0,${G.bgDarken})`;
    ctx.fillRect(-50, -50, 1700, 1000);
    ctx.restore();
    this.shells.drawDust(ctx);
    if (this.ragdoll) this.ragdoll.draw(ctx);
    else if (this.invuln <= 0 || Math.floor(this.invuln * 10) % 2 === 0) this.rider.draw(ctx, t);
    this.shells.draw(ctx, t);
    ctx.save();
    ctx.filter = `brightness(${(1 - G.bgDarken) * 100}%)`;   // foreground grass matches the darker background
    this.bg.drawFront(ctx, this.scroll, t);
    ctx.restore();
    if (this.debug && !this.ragdoll) this.drawDebug(ctx);
    if (!this.curtain.closed) this.drawHud(ctx);
    if (this.bannerT > 0) this.drawBanner(ctx);
    this.curtain.draw(ctx, t);
  }

  drawStrings(ctx: CanvasRenderingContext2D, now: number) {
    if (this.ragdoll || this.curtain.closed) return;
    const a = this.rider.anchors();
    this.bamboo.draw(ctx, a.bamboo, now);
    this.legs.draw(ctx, a.legs, now);
  }

  private drawHud(ctx: CanvasRenderingContext2D) {
    for (let i = 0; i < G.lives; i++) drawSprite(ctx, this.data.fx[i < this.lives ? "life" : "life_lost"], 70 + i * 48, 175, 1.1);
    drawSprite(ctx, this.data.fx.score_plaque, 1420, 160, 0.85);
    ctx.save();
    ctx.fillStyle = "#F4ECD6";
    ctx.font = "bold 30px Georgia, serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(`Score ${this.score}`, 1420, 162);
    ctx.restore();
  }

  private drawBanner(ctx: CanvasRenderingContext2D) {
    const a = Math.min(1, this.bannerT / 0.4);
    ctx.save();
    ctx.globalAlpha = a;
    drawSprite(ctx, this.data.fx.score_plaque, 800, 300, 1.2);
    ctx.fillStyle = "#F4ECD6";
    ctx.font = "bold 36px Georgia, serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(this.banner, 800, 302);
    ctx.restore();
  }

  private drawDebug(ctx: CanvasRenderingContext2D) {
    ctx.save();
    ctx.lineWidth = 2;
    for (const h of this.rider.hitShapes()) {
      ctx.strokeStyle = h.kind === "bamboo" ? "#00c" : h.kind === "stomp" ? "#0a0" : "#c00";
      ctx.lineWidth = 2;
      ctx.beginPath();
      if (h.a.x === h.b.x && h.a.y === h.b.y) ctx.arc(h.a.x, h.a.y, h.r, 0, Math.PI * 2);
      else { ctx.lineWidth = h.r * 2; ctx.globalAlpha = 0.3; ctx.moveTo(h.a.x, h.a.y); ctx.lineTo(h.b.x, h.b.y); }
      ctx.stroke();
      ctx.globalAlpha = 1;
    }
    ctx.restore();
  }
}
