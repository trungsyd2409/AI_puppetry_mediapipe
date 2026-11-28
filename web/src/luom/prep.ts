// One-off image work at load time so each frame stays cheap:
//   cropLayer : drop the empty sky rows of a 1600x900 layer (less to draw every frame)
//   glowSprite: a copy of a sprite with a bright cut-paper outline and a soft halo (hazard highlight)
//   lightOverlay: vignette + paper grain baked into one half-resolution image
import type { Sprite } from "../giong/data";

export function cropLayer(img: HTMLImageElement): { img: HTMLCanvasElement; y: number } {
  const c = document.createElement("canvas");
  c.width = img.width; c.height = img.height;
  const g = c.getContext("2d", { willReadFrequently: true })!;
  g.drawImage(img, 0, 0);
  const data = g.getImageData(0, 0, img.width, img.height).data;
  let top = 0;
  outer: for (let y = 0; y < img.height; y++) {
    for (let x = 3; x < img.width * 4; x += 16) if (data[y * img.width * 4 + x] > 4) { top = y; break outer; }
  }
  top = Math.max(0, top - 24);   // keep the soft shadow above the paper edge
  const out = document.createElement("canvas");
  out.width = img.width; out.height = img.height - top;
  out.getContext("2d")!.drawImage(img, 0, -top);
  return { img: out, y: top };
}

export function glowSprite(sp: Sprite, color: string, width = 7, halo = 10): Sprite {
  const pad = width + halo * 2;
  const w = sp.img.width + pad * 2, h = sp.img.height + pad * 2;
  // silhouette in the glow colour
  const sil = document.createElement("canvas");
  sil.width = w; sil.height = h;
  const s = sil.getContext("2d")!;
  s.drawImage(sp.img, pad, pad);
  s.globalCompositeOperation = "source-in";
  s.fillStyle = color; s.fillRect(0, 0, w, h);
  const out = document.createElement("canvas");
  out.width = w; out.height = h;
  const o = out.getContext("2d")!;
  o.filter = `blur(${halo}px)`;                       // soft halo
  o.globalAlpha = 0.9;
  for (let i = 0; i < 2; i++) o.drawImage(sil, 0, 0);
  o.filter = "none"; o.globalAlpha = 1;
  for (let a = 0; a < 16; a++) {                       // crisp outline (dilated silhouette)
    const r = (a / 16) * Math.PI * 2;
    o.drawImage(sil, Math.cos(r) * width, Math.sin(r) * width);
  }
  o.drawImage(sp.img, pad, pad);
  const k = sp.pngScale;
  return { img: out, size: [w / k, h / k], anchor: [sp.anchor[0] + pad / k, sp.anchor[1] + pad / k], pngScale: k };
}

/** Half-resolution overlay for the stage (1600 x (900 - cropY)): vignette around (vx, vy) + paper grain. */
export function lightOverlay(paper: HTMLImageElement, cropY: number, vx: number, vy: number,
  color: [number, number, number], strength: number, radius: number, grain = 0.3, vignette = true): HTMLCanvasElement {
  const W = 800, H = Math.round((900 - cropY) / 2);
  const c = document.createElement("canvas");
  c.width = W; c.height = H;
  const g = c.getContext("2d")!;
  if (grain > 0) {   // paper grain as darkness: (1 - paper) * grain
    const t = document.createElement("canvas");
    t.width = paper.width; t.height = paper.height;
    const tg = t.getContext("2d", { willReadFrequently: true })!;
    tg.drawImage(paper, 0, 0);
    const id = tg.getImageData(0, 0, t.width, t.height);
    for (let i = 0; i < id.data.length; i += 4) {
      const v = (id.data[i] + id.data[i + 1] + id.data[i + 2]) / 765;
      id.data[i + 3] = Math.round(Math.min(1, (1 - v) * grain) * 255);
      id.data[i] = color[0]; id.data[i + 1] = color[1]; id.data[i + 2] = color[2];
    }
    tg.putImageData(id, 0, 0);
    g.save(); g.scale(0.5, 0.5);
    g.fillStyle = g.createPattern(t, "repeat")!;
    g.fillRect(0, 0, W * 2, H * 2);
    g.restore();
  }
  if (vignette) {
    const x = vx / 2, y = (vy - cropY) / 2, R = (1150 * radius + 300) / 2;
    const vg = g.createRadialGradient(x, y, 80, x, y, R);
    const rgb = color.join(",");
    vg.addColorStop(0, `rgba(${rgb},0)`); vg.addColorStop(0.45, `rgba(${rgb},${strength * 0.25})`); vg.addColorStop(1, `rgba(${rgb},${strength})`);
    g.fillStyle = vg; g.fillRect(0, 0, W, H);
  }
  return c;
}

/** Draw an image once into a canvas: Chrome then never has to decode the PNG again while drawing. */
export function toCanvas(img: HTMLImageElement | HTMLCanvasElement): HTMLCanvasElement {
  if (img instanceof HTMLCanvasElement) return img;
  const c = document.createElement("canvas");
  c.width = img.width; c.height = img.height;
  c.getContext("2d")!.drawImage(img, 0, 0);
  return c;
}
