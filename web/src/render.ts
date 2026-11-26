// HUD panel and webcam inset, drawn on the stage canvas.
import { HAND_CONNECTIONS, type HandObs } from "./hands";
import type { Puppet } from "./puppet";

export interface HudInfo {
  source: string;
  hands: number;
  renderHz: number;
  trackHz: number;
  inferMs: number;
  sampleAge: number;
  puppets: Puppet[];
}

const STATE_COLOR: Record<string, string> = { ATTACHED: "#4ade80", REATTACHING: "#facc15", DETACHED: "#f87171" };
const MONO = "13px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace";

export function drawHud(ctx: CanvasRenderingContext2D, h: HudInfo) {
  const lines: [string, string, string?][] = [
    ["AGENT", "THUY DINH PUPPETRY", "#5eead4"],
    ["input", h.source],
    ["hands", String(h.hands)],
    ["render / track", `${h.renderHz.toFixed(0)} / ${h.trackHz.toFixed(0)} Hz`],
    ["inference", `${h.inferMs.toFixed(1)} ms`],
    ["sample age", `${h.sampleAge.toFixed(0)} ms`],
  ];
  for (const p of h.puppets)
    lines.push([p.label, `${p.state.padEnd(11)} ${p.strength.toFixed(2)}`, STATE_COLOR[p.state]]);

  const x = 16, y = 16, w = 330, lh = 19, hgt = lines.length * lh + 18;
  ctx.save();
  ctx.fillStyle = "rgba(12,8,6,0.72)";
  ctx.strokeStyle = "rgba(94,234,212,0.6)";
  ctx.lineWidth = 1;
  ctx.beginPath(); ctx.roundRect(x, y, w, hgt, 6); ctx.fill(); ctx.stroke();
  ctx.font = MONO;
  ctx.textBaseline = "top";
  lines.forEach(([k, v, c], i) => {
    ctx.fillStyle = "rgba(255,255,255,0.6)";
    ctx.fillText(k, x + 12, y + 10 + i * lh);
    ctx.fillStyle = c ?? "#f5f5f4";
    ctx.fillText(v, x + 130, y + 10 + i * lh);
  });
  ctx.restore();
}

export function drawInset(ctx: CanvasRenderingContext2D, canvasW: number, video: HTMLVideoElement | undefined,
  hands: HandObs[], mouseMode: boolean) {
  const w = 256, h = 192, x = canvasW - w - 16, y = 16;
  ctx.save();
  ctx.fillStyle = "rgba(12,8,6,0.75)";
  ctx.beginPath(); ctx.roundRect(x, y, w, h, 6); ctx.fill();
  ctx.save();
  ctx.beginPath(); ctx.roundRect(x, y, w, h, 6); ctx.clip();
  if (video && video.readyState >= 2) {
    ctx.translate(x + w, y);
    ctx.scale(-1, 1);                       // mirror like a selfie
    ctx.drawImage(video, 0, 0, w, h);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
  } else if (mouseMode) {
    ctx.fillStyle = "rgba(255,255,255,0.75)";
    ctx.font = MONO;
    ctx.textAlign = "center";
    const lines = hands.length
      ? ["CHẾ ĐỘ CHUỘT", "phím 1-5: nhấc từng ngón"]
      : ["CHẾ ĐỘ CHUỘT", "giữ chuột trái trên sân khấu", "phím 1-5: nhấc từng ngón", "thả chuột: rối ngã"];
    lines.forEach((l, i) => ctx.fillText(l, x + w / 2, hands.length ? y + h - 40 + i * 18 : y + h / 2 - 26 + i * 20));
  }
  ctx.restore();
  // landmarks (already mirrored)
  ctx.lineWidth = 2;
  for (const hand of hands) {
    const P = hand.lm.map((p) => ({ x: x + p.x * w, y: y + p.y * h }));
    ctx.strokeStyle = "rgba(94,234,212,0.9)";
    ctx.beginPath();
    for (const [a, b] of HAND_CONNECTIONS) { ctx.moveTo(P[a].x, P[a].y); ctx.lineTo(P[b].x, P[b].y); }
    ctx.stroke();
    ctx.fillStyle = "#fef3c7";
    for (const p of P) { ctx.beginPath(); ctx.arc(p.x, p.y, 2.2, 0, Math.PI * 2); ctx.fill(); }
  }
  ctx.strokeStyle = "rgba(94,234,212,0.6)";
  ctx.lineWidth = 1;
  ctx.beginPath(); ctx.roundRect(x, y, w, h, 6); ctx.stroke();
  ctx.restore();
}
