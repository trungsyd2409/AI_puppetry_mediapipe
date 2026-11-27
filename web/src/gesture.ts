// Ultimate gesture: "L" hand (index straight, middle/ring/pinky curled) with the index pointing
// UP, then flipped so the index points DOWN within CFG.ult.gestureWindow seconds.
// While the hand is in the L pose (or just left it) the strings are locked so curling the
// fingers does not yank the puppet, and a short tracking loss does not count as "hand lost".
import { CFG, type Pt } from "./config";

export type Pose = "up" | "down" | null;

const d = (a: Pt, b: Pt, asp: number) => Math.hypot((a.x - b.x) * asp, a.y - b.y);

/** Classify one hand. lm: 21 normalised landmarks; asp: video width / height. */
export function classify(lm: Pt[], asp = 4 / 3): Pose {
  const w = lm[0];
  const ext = (tip: number, pip: number) => d(lm[tip], w, asp) > d(lm[pip], w, asp) * 1.12;
  const curled = (tip: number, pip: number) => d(lm[tip], w, asp) < d(lm[pip], w, asp) * 1.02;
  if (!ext(8, 6)) return null;
  if (!(curled(12, 10) && curled(16, 14) && curled(20, 18))) return null;
  // index direction from its knuckle to its tip, corrected for the video aspect ratio
  const vx = (lm[8].x - lm[5].x) * asp, vy = lm[8].y - lm[5].y;
  const ang = (Math.atan2(vx, -vy) * 180) / Math.PI;   // 0 = straight up, +-180 = straight down
  const tol = CFG.ult.angleTolerance;
  if (Math.abs(ang) < tol) return "up";
  if (Math.abs(ang) > 180 - tol) return "down";
  return null;
}

export class GestureTracker {
  private lastUp = -1e9;
  private lastPose = -1e9;
  private lastFire = -1e9;
  pose: Pose = null;
  private grace = -1e9;

  /** True while a gesture is in progress (strings locked / hand loss tolerated). */
  busy(now: number) { return now < this.grace; }

  /** lm = null when this puppet got no hand in this tracking sample. */
  update(lm: Pt[] | null, now: number, asp: number): { locked: boolean; fire: boolean; graceUntil: number } {
    const win = CFG.ult.gestureWindow * 1000;
    let fire = false;
    this.pose = lm ? classify(lm, asp) : null;
    if (this.pose) this.lastPose = now;
    if (this.pose === "up") this.lastUp = now;
    else if (this.pose === "down" && now - this.lastUp <= win && now - this.lastFire > 600) {
      fire = true;
      this.lastFire = now;
      this.lastUp = -1e9;
    }
    const locked = now - this.lastPose < CFG.ult.lockAfter * 1000;
    // during the flip the camera may lose the blurred hand: do not drop the puppet
    const graceUntil = Math.max(this.lastUp + win, this.lastPose) + 200;
    this.grace = graceUntil;
    return { locked, fire, graceUntil };
  }
}
