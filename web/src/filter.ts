// One Euro filter (Casiez et al. 2012): low lag when moving fast, smooth when still.
import type { Pt } from "./config";

const alpha = (cutoff: number, dt: number) => {
  const tau = 1 / (2 * Math.PI * cutoff);
  return 1 / (1 + tau / dt);
};

export class OneEuro {
  private x: number | null = null;
  private dx = 0;
  constructor(private minCutoff: number, private beta: number, private dCutoff: number) {}

  reset() { this.x = null; this.dx = 0; }

  filter(value: number, dt: number): number {
    if (this.x === null || dt <= 0) { this.x = value; return value; }
    const d = (value - this.x) / dt;
    this.dx += alpha(this.dCutoff, dt) * (d - this.dx);
    const cutoff = this.minCutoff + this.beta * Math.abs(this.dx);
    this.x += alpha(cutoff, dt) * (value - this.x);
    return this.x;
  }
}

export class PointFilter {
  private fx: OneEuro; private fy: OneEuro;
  constructor(minCutoff: number, beta: number, dCutoff: number) {
    this.fx = new OneEuro(minCutoff, beta, dCutoff);
    this.fy = new OneEuro(minCutoff, beta, dCutoff);
  }
  reset() { this.fx.reset(); this.fy.reset(); }
  filter(p: Pt, dt: number): Pt { return { x: this.fx.filter(p.x, dt), y: this.fy.filter(p.y, dt) }; }
}
