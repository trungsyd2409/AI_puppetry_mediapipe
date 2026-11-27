// Fall animation: when a shell hits, every part becomes a Planck body starting from the current pose.
// The boy is no longer fixed to the saddle and the bamboo is let go, so both tumble off the horse.
import { type Body, BoxShape, CircleShape, EdgeShape, RevoluteJoint, type RevoluteJointOpt, Vec2, World } from "planck";
import type { Pt } from "../config";
import type { GPart } from "./data";
import { apply, angleOf, type M } from "./mat";
import type { Rider } from "./rider";

const PPM = 100;
const m = (v: number) => v / PPM;
const NO_JOINT = new Set(["boy_torso", "bamboo"]);       // detached when falling
const NO_LIMIT = new Set(["boy_arm_near_upper", "boy_arm_near_fore", "boy_arm_far_upper", "boy_arm_far_fore", "tail"]);

interface RB { part: GPart; body: Body }

export class Ragdoll {
  private world: World;
  private bodies: RB[] = [];
  private k: number;
  private acc = 0;

  constructor(rider: Rider, hitPart: string, hitVel: Pt) {
    this.k = rider.k;
    this.world = new World({ gravity: Vec2(0, 30) });
    const ground = this.world.createBody({ type: "static" });
    const fy = m(rider.floorY);
    ground.createFixture(new EdgeShape(Vec2(m(-400), fy), Vec2(m(2000), fy)), { friction: 0.9 });
    ground.createFixture(new EdgeShape(Vec2(m(-60), m(-800)), Vec2(m(-60), fy)), { friction: 0.5 });
    const s = this.k / PPM;
    const byId = new Map<string, Body>();
    const order: GPart[] = [];
    const visit = (p: GPart) => { if (order.includes(p)) return; if (p.parent) visit(rider.byId.get(p.parent)!); order.push(p); };
    rider.parts.forEach(visit);

    for (const p of order) {
      const M: M = rider.M[p.id];
      const pos = apply(M, p.pivotWorld[0], p.pivotWorld[1]);
      const body = this.world.createBody({ type: "dynamic", position: Vec2(m(pos.x), m(pos.y)), angle: angleOf(M),
        linearDamping: 0.1, angularDamping: 1.0 });
      const fix = { density: p.density, friction: 0.8, restitution: 0.1, filterGroupIndex: -7 };
      const shapes = p.colliders.length ? p.colliders : [{ type: "circle" as const, c: [0, 0] as [number, number], r: 10 }];
      for (const sh of shapes) {
        if (sh.type === "circle") body.createFixture(new CircleShape(Vec2(sh.c[0] * s, sh.c[1] * s), sh.r * s), fix);
        else {
          const a = Vec2(sh.a[0] * s, sh.a[1] * s), b = Vec2(sh.b[0] * s, sh.b[1] * s), r = sh.r * s;
          const len = Math.hypot(b.x - a.x, b.y - a.y);
          if (len > 1e-4) body.createFixture(new BoxShape(len / 2, r, Vec2((a.x + b.x) / 2, (a.y + b.y) / 2), Math.atan2(b.y - a.y, b.x - a.x)), fix);
          body.createFixture(new CircleShape(a, r), fix);
          body.createFixture(new CircleShape(b, r), fix);
        }
      }
      byId.set(p.id, body);
      this.bodies.push({ part: p, body });
      if (p.parent && !NO_JOINT.has(p.id)) {
        const parent = byId.get(p.parent)!;
        const lim = NO_LIMIT.has(p.id) ? null : p.limitDeg;
        // referenceAngle 0: joint limits are measured from the rest pose of the rig
        const opt = {
          enableLimit: !!lim, referenceAngle: 0,
          lowerAngle: lim ? (lim[0] * Math.PI) / 180 : 0, upperAngle: lim ? (lim[1] * Math.PI) / 180 : 0,
          enableMotor: true, motorSpeed: 0, maxMotorTorque: 0.4 * body.getMass(),
        };
        this.world.createJoint(new RevoluteJoint(opt as RevoluteJointOpt, parent, body, body.getPosition()));
      }
    }
    this.bodies.sort((x, y) => x.part.z - y.part.z);
    // arms keep holding each other, the boy keeps a loose hold on the bamboo
    const torso = byId.get("boy_torso")!, bam = byId.get("bamboo")!, fore = byId.get("boy_arm_near_fore")!;
    const fist = apply(rider.M.boy_arm_near_fore, rider.rig.gripNear[0], rider.rig.gripNear[1]);
    this.world.createJoint(new RevoluteJoint({}, fore, bam, Vec2(m(fist.x), m(fist.y))));
    void torso;

    // knock-back: shell pushes the hit part, the horse tips over backwards, the boy is thrown off
    const kick = Vec2(m(hitVel.x) * 0.35, m(hitVel.y) * 0.35 - 2);
    for (const { part, body } of this.bodies) {
      const boy = part.id.startsWith("boy") || part.id === "bamboo";
      const v = boy ? Vec2(kick.x * 1.2 - 1.5, -6 - Math.random() * 1.5) : Vec2(kick.x * 0.5, -2.5);
      body.setLinearVelocity(v);
      if (part.id === hitPart) body.applyLinearImpulse(Vec2(kick.x * body.getMass() * 2, kick.y * body.getMass()), body.getWorldCenter());
    }
    byId.get("body")!.setAngularVelocity(-2.2);
    torso.setAngularVelocity(-5);
  }

  step(dt: number) {
    this.acc += dt;
    while (this.acc >= 1 / 120) { this.world.step(1 / 120, 8, 3); this.acc -= 1 / 120; }
  }

  draw(ctx: CanvasRenderingContext2D) {
    for (const { part: p, body } of this.bodies) {
      const pos = body.getPosition();
      ctx.save();
      ctx.translate(pos.x * PPM, pos.y * PPM);
      ctx.rotate(body.getAngle());
      ctx.scale(this.k, this.k);
      ctx.translate(-p.pivotWorld[0], -p.pivotWorld[1]);
      ctx.drawImage(p.img, p.origin[0], p.origin[1], p.size[0], p.size[1]);
      ctx.restore();
    }
  }
}
