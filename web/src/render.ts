// Screen-space drawing: camera half, HUD panel and event log.
import { HAND_CONNECTIONS, type HandObs } from "./hands";
import type { Pt } from "./config";
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
const MONO = "15px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace";
const PANEL_BG = "rgba(10,10,14,0.68)";
const PANEL_LINE = "rgba(94,234,212,0.55)";

function panel(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number) {
  ctx.fillStyle = PANEL_BG;
  ctx.strokeStyle = PANEL_LINE;
  ctx.lineWidth = 1;
  ctx.beginPath(); ctx.roundRect(x, y, w, h, 6); ctx.fill(); ctx.stroke();
}

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
  const x = 14, y = 14, w = 360, lh = 21;
  ctx.save();
  panel(ctx, x, y, w, lines.length * lh + 18);
  ctx.font = MONO;
  ctx.textBaseline = "top";
  lines.forEach(([k, v, c], i) => {
    ctx.fillStyle = "rgba(255,255,255,0.6)";
    ctx.fillText(k, x + 12, y + 10 + i * lh);
    ctx.fillStyle = c ?? "#f5f5f4";
    ctx.fillText(v, x + 150, y + 10 + i * lh);
  });
  ctx.restore();
}

export interface LogLine { t: number; text: string; color: string }

export function drawLog(ctx: CanvasRenderingContext2D, canvasW: number, log: LogLine[], now: number) {
  const rows = log.slice(-6);
  const w = 400, lh = 21, x = canvasW - w - 14, y = 14;
  ctx.save();
  panel(ctx, x, y, w, 36 + Math.max(1, rows.length) * lh);
  ctx.font = MONO;
  ctx.textBaseline = "top";
  ctx.fillStyle = "#5eead4";
  ctx.fillText("puppet@thuydinh:~$ watch", x + 12, y + 10);
  rows.forEach((r, i) => {
    const age = ((now - r.t) / 1000).toFixed(1).padStart(5);
    ctx.fillStyle = "rgba(255,255,255,0.45)";
    ctx.fillText(`${age}s`, x + 12, y + 34 + i * lh);
    ctx.fillStyle = r.color;
    ctx.fillText(r.text, x + 80, y + 34 + i * lh);
  });
  ctx.restore();
}

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
