// Planck world with a floor and two side walls. y points DOWN (same as the canvas),
// so gravity is +y and positive angles turn clockwise on screen.
import { EdgeShape, Vec2, World } from "planck";
import { CFG } from "./config";
import type { Stage } from "./assets";

export const CAT_WORLD = 0x0001;
export const CAT_PUPPET = 0x0002;

export const m = (px: number) => px / CFG.ppm;   // stage px -> metres
export const px = (mt: number) => mt * CFG.ppm;  // metres -> stage px

export function createWorld(stage: Stage): World {
  const world = new World({ gravity: Vec2(0, CFG.gravity) });
  const [w] = stage.size;
  const ground = world.createBody({ type: "static" });
  const fix = { friction: 0.9, restitution: 0.05, filterCategoryBits: CAT_WORLD, filterMaskBits: 0xffff };
  ground.createFixture(new EdgeShape(Vec2(m(-500), m(stage.floorY)), Vec2(m(w + 500), m(stage.floorY))), fix);
  const x0 = m(CFG.wallMargin), x1 = m(w - CFG.wallMargin);
  ground.createFixture(new EdgeShape(Vec2(x0, m(-2000)), Vec2(x0, m(stage.floorY))), fix);
  ground.createFixture(new EdgeShape(Vec2(x1, m(-2000)), Vec2(x1, m(stage.floorY))), fix);
  return world;
}
