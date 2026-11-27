// Weapon hits between puppets. A weapon part (spear, saber, ...) touching another puppet
// fast enough is a hit: the target is knocked back, its strings go slack for a moment and
// blood flies. Weapon against weapon makes sparks. Contacts are collected during the physics
// step (the world is locked there) and applied right after it.
import { type Body, type Contact, Vec2, type World } from "planck";
import { CFG } from "./config";
import type { HitFx } from "./fx_blood";
import type { Puppet } from "./puppet";
import { px } from "./physics";

export interface FixtureTag { puppet: Puppet; part: string; weapon: boolean }

interface Pending {
  kind: "hit" | "clash";
  attacker: Puppet;
  target: Puppet;
  body: Body;
  point: { x: number; y: number };   // metres
  speed: number;                     // relative speed at the contact (m/s)
}

export class Combat {
  private pending: Pending[] = [];
  private lastHit = new Map<string, number>();
  /** 0..1, decays: screen shake amount for the renderer. */
  shake = 0;

  constructor(world: World, private fx: HitFx) {
    world.on("begin-contact", (c) => this.onContact(c));
  }

  private onContact(c: Contact) {
    const fa = c.getFixtureA(), fb = c.getFixtureB();
    const ta = fa.getUserData() as FixtureTag | undefined, tb = fb.getUserData() as FixtureTag | undefined;
    if (!ta?.puppet || !tb?.puppet || ta.puppet === tb.puppet) return;
    if (!ta.weapon && !tb.weapon) return;
    const p = c.getWorldManifold(null)?.points[0];
    if (!p) return;
    const va = fa.getBody().getLinearVelocityFromWorldPoint(p);
    const vb = fb.getBody().getLinearVelocityFromWorldPoint(p);
    const speed = Math.hypot(va.x - vb.x, va.y - vb.y);
    if (speed < CFG.combat.minHitSpeed) return;
    const point = { x: p.x, y: p.y };
    if (ta.weapon && tb.weapon) {
      this.pending.push({ kind: "clash", attacker: ta.puppet, target: tb.puppet, body: fb.getBody(), point, speed });
    } else {
      const [att, tgt, body] = ta.weapon ? [ta, tb, fb.getBody()] : [tb, ta, fa.getBody()];
      this.pending.push({ kind: "hit", attacker: att.puppet, target: tgt.puppet, body, point, speed });
    }
  }

  /** Call right after world.step(). */
  resolve(now: number) {
    const C = CFG.combat;
    for (const h of this.pending) {
      const key = `${h.kind}:${h.attacker.id}>${h.target.id}`;
      if (now - (this.lastHit.get(key) ?? -1e9) < C.cooldown * 1000) continue;
      this.lastHit.set(key, now);
      const X = px(h.point.x), Y = px(h.point.y);
      if (h.kind === "clash") {
        this.fx.clash(X, Y);
        this.shake = Math.max(this.shake, 0.3);
        continue;
      }
      // push the target away from the attacker, slightly upwards
      const side = Math.sign(h.target.torsoX() - h.attacker.torsoX()) || 1;
      const dir = { x: side * 0.9, y: -0.45 };
      const n = Math.hypot(dir.x, dir.y);
      dir.x /= n; dir.y /= n;
      const k = Math.min(1, (h.speed - C.minHitSpeed) / (C.fullHitSpeed - C.minHitSpeed));
      const kick = C.knockback.min + (C.knockback.max - C.knockback.min) * k;
      h.target.knockback(h.body, Vec2(h.point.x, h.point.y), dir, kick);
      this.fx.blood(X, Y, dir.x, dir.y, k);
      this.shake = Math.max(this.shake, 0.4 + 0.6 * k);
    }
    this.pending.length = 0;
  }

  update(dt: number) { this.shake = Math.max(0, this.shake - dt * 3); }
}
