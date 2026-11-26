// One marionette: ragdoll bodies built from rig.json + strings driven by a hand.
//
// State machine
//   DETACHED     no strings, pure ragdoll (falls to the floor)
//   REATTACHING  hand is back: strings grow from fingertips to the puppet (growTime),
//                then string strength ramps 0 -> 1 and the puppet stands up (standTime)
//   ATTACHED     strings pull each anchor toward a target computed from the hand
import {
  type Body, BoxShape, CircleShape, type PolygonShape, RevoluteJoint, Vec2, type World,
} from "planck";
import { CFG, type Pt } from "./config";
import type { PuppetAsset, RigPart, RigString, Shape, Stage } from "./assets";
import { CAT_PUPPET, CAT_WORLD, m, px } from "./physics";
import { PointFilter } from "./filter";

export type PuppetState = "DETACHED" | "REATTACHING" | "ATTACHED";

/** Hand in stage pixels. tips: thumb, index, middle, ring, pinky. */
export interface Control { palm: Pt; tips: Pt[] }

const TIP_SLOT: Record<number, number> = { 4: 0, 8: 1, 12: 2, 16: 3, 20: 4 };
const FINGER_COLORS = ["#ff9f43", "#feca57", "#48dbfb", "#1dd1a1", "#ff6b9d"];

interface PartRT { def: RigPart; body: Body; img: HTMLImageElement }

interface StringRT {
  def: RigString;
  part: PartRT;
  local: Vec2;          // anchor in body-local metres
  slot: number;         // finger slot 0..4
  restRel: Pt;          // rest offset from the head anchor (px)
  chainMass: number;    // mass this string supports (limb chain)
  isHead: boolean;
  target: Pt;           // px
  start: Pt | null;     // anchor position when the stand-up phase began
}

const smooth = (t: number) => { const c = Math.min(1, Math.max(0, t)); return c * c * (3 - 2 * c); };
const lerp = (a: Pt, b: Pt, t: number): Pt => ({ x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t });

export class Puppet {
  readonly id: string;
  readonly label: string;
  readonly k: number;                 // stage px per design unit
  state: PuppetState = "DETACHED";
  stateTime = 0;
  strength = 0;
  control: Control | null = null;     // filtered hand, stage px

  private parts: PartRT[] = [];
  private byId = new Map<string, PartRT>();
  private strings: StringRT[] = [];
  private torso!: PartRT;
  private totalMass = 0;
  private headSupport = 0;
  private lastSeen = -Infinity;
  private seenFrames = 0;
  private calib: Pt[] = [];
  private filters = Array.from({ length: 6 }, () => new PointFilter(CFG.euro.minCutoff, CFG.euro.beta, CFG.euro.dCutoff));
  private lastSample = 0;
  private detachedAt = -Infinity;
  private droppedTips: Pt[] = [];

  constructor(private world: World, asset: PuppetAsset, private stage: Stage, homeX: number, label: string) {
    this.id = asset.id;
    this.label = label;
    const rig = asset.rig;
    const top = Math.min(...rig.parts.map((p) => p.origin[1]));
    this.k = (CFG.puppetHeight || stage.puppetHeight) / (rig.feetY - top);
    const toStage = (x: number, y: number): Pt => ({
      x: homeX + (x - rig.canvas[0] / 2) * this.k,
      y: stage.floorY + (y - rig.feetY) * this.k - 2,
    });

    // parents before children
    const ordered: RigPart[] = [];
    const visit = (p: RigPart) => {
      if (ordered.includes(p)) return;
      const parent = rig.parts.find((q) => q.id === p.parent);
      if (parent) visit(parent);
      ordered.push(p);
    };
    rig.parts.forEach(visit);

    const s = this.k / CFG.ppm; // design units -> metres
    for (const def of ordered) {
      const pos = toStage(...def.pivotWorld);
      const body = world.createBody({
        type: "dynamic", position: Vec2(m(pos.x), m(pos.y)), angle: 0,
        linearDamping: CFG.linearDamping, angularDamping: CFG.angularDamping,
      });
      const fix = { density: def.density, friction: 0.7, restitution: 0.05,
        filterCategoryBits: CAT_PUPPET, filterMaskBits: CAT_WORLD };
      const shapes: Shape[] = def.colliders.length ? def.colliders : [{ type: "circle", c: [0, 0], r: 10 }];
      for (const sh of shapes) {
        if (sh.type === "circle") {
          body.createFixture(new CircleShape(Vec2(sh.c[0] * s, sh.c[1] * s), sh.r * s), fix);
        } else {
          const a = Vec2(sh.a[0] * s, sh.a[1] * s), b = Vec2(sh.b[0] * s, sh.b[1] * s), r = sh.r * s;
          const len = Math.hypot(b.x - a.x, b.y - a.y);
          if (len > 1e-4) {
            const ang = Math.atan2(b.y - a.y, b.x - a.x);
            body.createFixture(new BoxShape(len / 2, r, Vec2((a.x + b.x) / 2, (a.y + b.y) / 2), ang), fix);
          }
          body.createFixture(new CircleShape(a, r), fix);
          body.createFixture(new CircleShape(b, r), fix);
        }
      }
      const rt: PartRT = { def, body, img: asset.images.get(def.id)! };
      this.parts.push(rt);
      this.byId.set(def.id, rt);
      if (def.parent) {
        const parent = this.byId.get(def.parent)!;
        const lim = def.limitDeg;
        world.createJoint(new RevoluteJoint({
          enableLimit: !!lim,
          lowerAngle: lim ? (lim[0] * Math.PI) / 180 : 0,
          upperAngle: lim ? (lim[1] * Math.PI) / 180 : 0,
          enableMotor: true, motorSpeed: 0, maxMotorTorque: CFG.jointFriction * body.getMass(),
        }, parent.body, body, body.getPosition()));
      } else {
        this.torso = rt;
      }
    }
    this.parts.sort((a, b) => a.def.z - b.def.z);
    this.totalMass = this.parts.reduce((acc, p) => acc + p.body.getMass(), 0);

    // strings
    const headDef = rig.strings.find((st) => st.mpLandmark === 12) ?? rig.strings[0];
    const headRest = toStage(...headDef.anchorWorld);
    let limbMass = 0;
    for (const def of rig.strings) {
      const part = this.byId.get(def.part)!;
      const w = toStage(...def.anchorWorld);
      const isHead = def === headDef;
      let chainMass = 0;
      if (!isHead) {
        for (let p: PartRT | undefined = part; p && p !== this.torso; p = p.def.parent ? this.byId.get(p.def.parent) : undefined)
          chainMass += p.body.getMass();
        limbMass += chainMass;
      }
      this.strings.push({
        def, part, isHead, chainMass,
        local: part.body.getLocalPoint(Vec2(m(w.x), m(w.y))),
        slot: TIP_SLOT[def.mpLandmark] ?? 2,
        restRel: { x: w.x - headRest.x, y: w.y - headRest.y },
        target: w, start: null,
      });
    }
    this.headSupport = Math.max(0.2 * this.totalMass, this.totalMass - limbMass);
    this.kick();
  }

  /** Small random push so a balanced puppet does not stay standing when the strings go. */
  private kick() {
    const dir = Math.random() < 0.5 ? -1 : 1;
    const head = this.strings.find((st) => st.isHead)!;
    const top = head.part.body.getWorldPoint(head.local);
    head.part.body.applyLinearImpulse(Vec2(dir * this.totalMass * (0.8 + Math.random() * 0.6), 0), top, true);
    for (const p of this.parts)
      p.body.applyAngularImpulse((Math.random() - 0.5) * 0.08 * p.body.getInertia(), true);
  }

  // ---------------------------------------------------------------- input
  /** Called once per tracking sample. `raw` = hand assigned to this puppet or null. */
  onHand(raw: Control | null, now: number) {
    if (!raw) { this.seenFrames = 0; return; }
    const dt = Math.min(0.2, (now - this.lastSample) / 1000);
    this.lastSample = now;
    if (now - this.lastSeen > CFG.loseAfter * 1000) this.filters.forEach((f) => f.reset());
    this.lastSeen = now;
    this.seenFrames++;
    this.control = {
      palm: this.filters[0].filter(raw.palm, dt),
      tips: raw.tips.map((t, i) => this.filters[i + 1].filter(t, dt)),
    };
  }

  // ---------------------------------------------------------------- state
  update(dt: number, now: number) {
    this.stateTime += dt;
    const present = now - this.lastSeen < CFG.loseAfter * 1000;
    if (this.state !== "DETACHED" && !present) this.detach(now);
    else if (this.state === "DETACHED" && this.seenFrames >= CFG.attachFrames && this.control) this.reattach();
    else if (this.state === "REATTACHING" && this.stateTime >= CFG.growTime + CFG.standTime) this.setState("ATTACHED");

    if (this.state === "ATTACHED") this.strength = 1;
    else if (this.state === "REATTACHING") this.strength = smooth((this.stateTime - CFG.growTime) / CFG.standTime);
    else this.strength = 0;

    if (this.control && this.state !== "DETACHED") this.computeTargets();
  }

  private setState(s: PuppetState) { this.state = s; this.stateTime = 0; }

  private detach(now: number) {
    this.droppedTips = this.strings.map((st) => this.control?.tips[st.slot] ?? this.anchorPx(st));
    this.detachedAt = now;
    this.control = null;
    this.setState("DETACHED");
    this.kick();
  }

  private reattach() {
    const c = this.control!;
    this.calib = c.tips.map((t) => ({ x: t.x - c.palm.x, y: t.y - c.palm.y }));
    this.strings.forEach((st) => (st.start = null));
    this.setState("REATTACHING");
  }

  private computeTargets() {
    const c = this.control!;
    const base = { x: c.palm.x, y: c.palm.y + CFG.dropPx };
    const standing = this.state === "REATTACHING" && this.stateTime >= CFG.growTime;
    const e = smooth((this.stateTime - CFG.growTime) / CFG.standTime);
    const [x0, x1] = [CFG.wallMargin + 30, this.stage.size[0] - CFG.wallMargin - 30];
    for (const st of this.strings) {
      const tip = c.tips[st.slot], cal = this.calib[st.slot];
      const d = { x: (tip.x - c.palm.x - cal.x) * CFG.fingerGain, y: (tip.y - c.palm.y - cal.y) * CFG.fingerGain };
      let t = { x: base.x + st.restRel.x + d.x, y: base.y + st.restRel.y + d.y };
      t = { x: Math.min(x1, Math.max(x0, t.x)), y: Math.min(this.stage.floorY + 40, Math.max(CFG.targetMinY, t.y)) };
      if (this.state === "REATTACHING") {
        if (standing && !st.start) st.start = this.anchorPx(st);
        if (st.start) t = lerp(st.start, t, e);
      }
      st.target = t;
    }
  }

  // ---------------------------------------------------------------- physics
  /** Call before every fixed physics step. */
  applyForces() {
    const s = this.strength;
    if (s <= 0) return;
    const g = CFG.gravity;
    for (const st of this.strings) {
      const body = st.part.body;
      const p = body.getWorldPoint(st.local);
      const v = body.getLinearVelocityFromWorldPoint(p);
      const sp = st.isHead ? CFG.headSpring : CFG.limbSpring;
      const mass = st.isHead ? this.headSupport : st.chainMass;
      let ax = sp.omega ** 2 * (m(st.target.x) - p.x) - 2 * sp.zeta * sp.omega * v.x;
      let ay = sp.omega ** 2 * (m(st.target.y) - p.y) - 2 * sp.zeta * sp.omega * v.y;
      const a = Math.hypot(ax, ay);
      if (a > CFG.maxAccel) { ax *= CFG.maxAccel / a; ay *= CFG.maxAccel / a; }
      body.applyForce(Vec2(s * mass * ax, s * mass * (ay - g)), p, true);
    }
    // keep the torso roughly upright while strings hold it, like a real control bar
    const tb = this.torso.body;
    let th = tb.getAngle() % (2 * Math.PI);
    if (th > Math.PI) th -= 2 * Math.PI;
    if (th < -Math.PI) th += 2 * Math.PI;
    const { kp, kd, radius } = CFG.upright;
    tb.applyTorque(s * this.totalMass * radius * radius * (-kp * th - kd * tb.getAngularVelocity()), true);
  }

  anchorPx(st: StringRT): Pt {
    const p = st.part.body.getWorldPoint(st.local);
    return { x: px(p.x), y: px(p.y) };
  }

  torsoX() { return px(this.torso.body.getPosition().x); }

  destroy() { this.parts.forEach((p) => this.world.destroyBody(p.body)); }

  // ---------------------------------------------------------------- drawing
  draw(ctx: CanvasRenderingContext2D) {
    const k = this.k;
    for (const p of this.parts) {
      const pos = p.body.getPosition();
      ctx.save();
      ctx.translate(px(pos.x), px(pos.y));
      ctx.rotate(p.body.getAngle());
      ctx.drawImage(p.img, -p.def.pivot[0] * k, -p.def.pivot[1] * k, p.def.size[0] * k, p.def.size[1] * k);
      ctx.restore();
    }
  }

  drawStrings(ctx: CanvasRenderingContext2D, now: number) {
    ctx.save();
    ctx.lineCap = "round";
    if (this.state === "DETACHED") {
      // broken strings fall from where the fingers were and fade out
      const age = (now - this.detachedAt) / 1000;
      const alpha = 1 - age / 1.4;
      if (alpha > 0) {
        this.strings.forEach((st, i) => {
          const a = this.anchorPx(st);
          const from = this.droppedTips[i] ?? a;
          const top = lerp(from, { x: a.x + 18 * Math.sin(i * 2.1), y: a.y - 40 }, smooth(age / 0.7));
          const ctrl = { x: (a.x + top.x) / 2 + 25 * Math.sin(age * 6 + i), y: Math.max(a.y, top.y) + 20 };
          ctx.strokeStyle = `rgba(30,16,8,${0.8 * alpha})`;
          ctx.lineWidth = 1.6;
          ctx.beginPath(); ctx.moveTo(top.x, top.y); ctx.quadraticCurveTo(ctrl.x, ctrl.y, a.x, a.y); ctx.stroke();
        });
      }
    } else if (this.control) {
      const grow = this.state === "REATTACHING" ? smooth(this.stateTime / CFG.growTime) : 1;
      for (const st of this.strings) {
        const tip = this.control.tips[st.slot];
        const a = this.anchorPx(st);
        const end = lerp(tip, a, grow);
        ctx.strokeStyle = "rgba(255,236,190,0.35)";
        ctx.lineWidth = 3.2;
        ctx.beginPath(); ctx.moveTo(tip.x, tip.y); ctx.lineTo(end.x, end.y); ctx.stroke();
        ctx.strokeStyle = "rgba(30,16,8,0.9)";
        ctx.lineWidth = 1.5;
        ctx.beginPath(); ctx.moveTo(tip.x, tip.y); ctx.lineTo(end.x, end.y); ctx.stroke();
        if (grow < 1) {
          ctx.fillStyle = "#ffe08a";
          ctx.beginPath(); ctx.arc(end.x, end.y, 4, 0, Math.PI * 2); ctx.fill();
        } else {
          ctx.fillStyle = "#e2b44a";
          ctx.beginPath(); ctx.arc(a.x, a.y, 3, 0, Math.PI * 2); ctx.fill();
        }
      }
    }
    // fingertip markers
    if (this.control) {
      this.control.tips.forEach((t, i) => {
        ctx.fillStyle = FINGER_COLORS[i];
        ctx.strokeStyle = "rgba(20,10,5,0.8)";
        ctx.lineWidth = 1.5;
        ctx.beginPath(); ctx.arc(t.x, t.y, 6, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
      });
    }
    ctx.restore();
  }

  drawDebug(ctx: CanvasRenderingContext2D) {
    ctx.save();
    ctx.lineWidth = 1.5;
    for (const p of this.parts) {
      for (let f = p.body.getFixtureList(); f; f = f.getNext()) {
        const sh = f.getShape();
        ctx.strokeStyle = "rgba(0,255,170,0.9)";
        ctx.beginPath();
        if (sh.getType() === "circle") {
          const c = p.body.getWorldPoint((sh as CircleShape).getCenter());
          ctx.arc(px(c.x), px(c.y), px(sh.getRadius()), 0, Math.PI * 2);
        } else if (sh.getType() === "polygon") {
          const ps = sh as PolygonShape;
          for (let i = 0; i < ps.m_count; i++) {
            const v = p.body.getWorldPoint(ps.m_vertices[i]);
            if (i === 0) ctx.moveTo(px(v.x), px(v.y)); else ctx.lineTo(px(v.x), px(v.y));
          }
          ctx.closePath();
        }
        ctx.stroke();
      }
    }
    for (const st of this.strings) {
      if (this.state === "DETACHED") continue;
      ctx.strokeStyle = "rgba(255,60,60,0.9)";
      ctx.beginPath(); ctx.arc(st.target.x, st.target.y, 7, 0, Math.PI * 2); ctx.stroke();
    }
    ctx.restore();
  }
}
