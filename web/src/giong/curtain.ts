// Dong Ho stage curtain: two red panels slide in from the sides, a green valance drops from the top.
// c = 0 open, 1 closed. Text is written on the valance plaque and on a paper card in the middle.
import { drawSprite, type Sprite } from "./data";

export class Curtain {
  c = 1;
  private from = 1; private to = 1; private t = 0; private dur = 1;
  title = "THÁNH GIÓNG";
  lines: string[] = [];
  /** Colours of the title on the valance plaque and of the paper card. */
  style = { title: "#F4ECD6", card: "#EFE2C2", edge: "#241A14", accent: "#A63A25", text: "#241A14", width: 760 };

  constructor(private fx: Record<string, Sprite>, private cropY: number) {}

  animate(to: number, dur: number) { this.from = this.c; this.to = to; this.t = 0; this.dur = dur; }
  get moving() { return this.t < this.dur && this.c !== this.to; }
  get closed() { return this.c > 0.999; }
  get open() { return this.c < 0.001; }

  update(dt: number) {
    if (this.c === this.to) return;
    this.t += dt;
    const u = Math.min(1, this.t / this.dur);
    const e = u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2;   // ease in-out
    this.c = this.from + (this.to - this.from) * e;
    if (u >= 1) this.c = this.to;
  }

  draw(ctx: CanvasRenderingContext2D, t: number) {
    if (this.c <= 0.001) return;
    const panel = this.fx.curtain_panel, top = this.fx.curtain_top;
    const c = this.c;
    // a little sway while moving
    const sway = Math.sin(t * 7) * 6 * (1 - Math.abs(2 * c - 1));
    drawSprite(ctx, panel, -820 + 820 * c + sway, 0, 1);
    drawSprite(ctx, panel, 1600 - 820 * c - sway + 820, 0, 1, 0, 1, true);
    const vy = this.cropY - 200 * (1 - c);
    drawSprite(ctx, top, 0, vy, 1);
    if (c < 0.98) return;
    ctx.save();
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillStyle = this.style.title;
    ctx.font = "bold 34px Georgia, 'Times New Roman', serif";
    ctx.fillText(this.title, 800, vy + 93);
    if (this.lines.length) {
      const w = this.style.width, h = 70 + this.lines.length * 52, x = 800 - w / 2, y = 520 - h / 2;
      ctx.fillStyle = this.style.card;
      ctx.strokeStyle = this.style.edge;
      ctx.lineWidth = 5;
      ctx.beginPath(); ctx.roundRect(x, y, w, h, 14); ctx.fill(); ctx.stroke();
      ctx.strokeStyle = this.style.accent; ctx.lineWidth = 2; ctx.setLineDash([10, 7]);
      ctx.beginPath(); ctx.roundRect(x + 12, y + 12, w - 24, h - 24, 10); ctx.stroke(); ctx.setLineDash([]);
      this.lines.forEach((l, i) => {
        ctx.fillStyle = i === 0 ? this.style.accent : this.style.text;
        ctx.font = i === 0 ? "bold 40px Georgia, serif" : "28px Georgia, serif";
        ctx.fillText(l, 800, y + 60 + i * 52);
      });
    }
    ctx.restore();
  }
}
