// A flag / pennant cloth waving from a pole. Shared by every scene.
export type ClothMap = (x: number, y: number) => [number, number];

export interface ClothOpts {
  px: number; py: number;   // attachment point on the pole (stage px)
  side: number;             // +1 flies to the right, -1 to the left
  L: number;                // cloth length along the wave
  outline: [number, number][];
  fill: string;
  phase: number;            // per-flag phase offset
  flagPhase: number;        // accumulated global phase (constant speed)
  gust: number;             // 0..1 smoothed wind strength, widens the motion a little
  ink?: string;
  after?: (map: ClothMap, slope: (x: number) => number) => void;
}

export function drawCloth(ctx: CanvasRenderingContext2D, o: ClothOpts) {
  const { px, py, side, L, phase, gust: g } = o;
  const amp = 4 + 3 * g;
  const k = (2 * Math.PI) / (L * 0.9);
  const ph = o.flagPhase;
  const wave = (x: number) => amp * (x / L) * Math.sin(k * x - ph + phase);
  const slope = (x: number) => (amp / L) * Math.sin(k * x - ph + phase)
    + amp * (x / L) * k * Math.cos(k * x - ph + phase);
  const droop = (x: number) => (1 - g) * 0.06 * x;   // hangs a little when calm
  const map: ClothMap = (x, y) => [px + side * x, py + y + wave(x) + droop(x)];

  ctx.save();
  ctx.beginPath();
  o.outline.forEach(([x, y], i) => { const [X, Y] = map(x, y); if (i) ctx.lineTo(X, Y); else ctx.moveTo(X, Y); });
  ctx.closePath();
  ctx.fillStyle = o.fill;
  ctx.fill();
  // folds: darken where the cloth turns away, lighten where it faces the light
  const [XA] = map(0, 0), [XB] = map(L, 0);
  const shade = ctx.createLinearGradient(XA, 0, XB, 0);
  for (let i = 0; i <= 16; i++) {
    const x = (L * i) / 16, s = slope(x);
    shade.addColorStop(i / 16, s > 0 ? `rgba(20,15,25,${Math.min(0.32, s * 0.9).toFixed(3)})`
      : `rgba(255,245,225,${Math.min(0.28, -s * 0.8).toFixed(3)})`);
  }
  ctx.fillStyle = shade;
  ctx.fill();
  o.after?.(map, slope);
  ctx.strokeStyle = o.ink ?? "#2A140A";
  ctx.lineWidth = 2;
  ctx.lineJoin = "round";
  ctx.stroke();
  ctx.restore();
}

/** Outline of a swallow-tail pennant, length L, height h. */
export function pennant(L: number, h: number, N = 14): [number, number][] {
  const s: [number, number][] = [];
  for (let i = 0; i <= N; i++) s.push([(L * i) / N, -3 * Math.sin((Math.PI * i) / N)]);
  s.push([L * 0.8, h / 2]);
  for (let i = N; i >= 0; i--) s.push([(L * i) / N, h + 3 * Math.sin((Math.PI * i) / N)]);
  return s;
}

/** Outline of a rectangular flag. */
export function rectFlag(L: number, h: number, N = 14): [number, number][] {
  const s: [number, number][] = [];
  for (let i = 0; i <= N; i++) s.push([(L * i) / N, 0]);
  for (let i = N; i >= 0; i--) s.push([(L * i) / N, h]);
  return s;
}

/** Interface every scene's living-background module implements. */
export interface SceneFx {
  update(dt: number): void;
  windAccel(): number;
  drawBackground(ctx: CanvasRenderingContext2D): void;   // behind the puppets
  drawForeground(ctx: CanvasRenderingContext2D): void;   // in front of the puppets
  debugTrigger(kind: string): void;
  /** Set by the app: called when a gust of wind starts (seconds it lasts). */
  onGust?: (seconds: number) => void;
}
