// Screen-space drawing: the camera half.
import { HAND_CONNECTIONS, type HandObs } from "./hands";
import type { Pt } from "./config";

/** Top half: mirrored webcam (cover-fit) or a placeholder, plus hand skeletons. */
export function drawCamera(ctx: CanvasRenderingContext2D, W: number, H: number,
  video: HTMLVideoElement | undefined, rect: { ox: number; oy: number; dw: number; dh: number },
  hands: HandObs[], toScreen: (p: Pt) => Pt, hint: string[]) {
  ctx.save();
  ctx.beginPath(); ctx.rect(0, 0, W, H); ctx.clip();
  if (video && video.readyState >= 2) {
    ctx.translate(W, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, rect.ox, rect.oy, rect.dw, rect.dh);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = "rgba(20,12,6,0.18)";
    ctx.fillRect(0, 0, W, H);
  } else {
    const g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, "#151a1f"); g.addColorStop(1, "#24170e");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);
    ctx.strokeStyle = "rgba(94,234,212,0.07)";
    ctx.lineWidth = 1;
    for (let x = 0; x < W; x += 40) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
    for (let y = 0; y < H; y += 40) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
    ctx.fillStyle = "rgba(255,255,255,0.7)";
    ctx.font = "20px system-ui, sans-serif";
    ctx.textAlign = "center";
    hint.forEach((l, i) => ctx.fillText(l, W / 2, H / 2 - ((hint.length - 1) * 28) / 2 + i * 28));
  }
  for (const hand of hands) {
    const P = hand.lm.map(toScreen);
    ctx.strokeStyle = "rgba(94,234,212,0.85)";
    ctx.lineWidth = 3;
    ctx.beginPath();
    for (const [a, b] of HAND_CONNECTIONS) { ctx.moveTo(P[a].x, P[a].y); ctx.lineTo(P[b].x, P[b].y); }
    ctx.stroke();
    ctx.fillStyle = "#e0fffa";
    for (const p of P) { ctx.beginPath(); ctx.arc(p.x, p.y, 3.5, 0, Math.PI * 2); ctx.fill(); }
  }
  ctx.restore();
}
