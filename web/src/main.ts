// Thanh Giong game: a boy on a horse holding a bamboo pole, driven by two hands through webcam strings.
// Square screen: webcam on top, the 1600x900 stage below; strings run from the fingertips down to the puppet.
import "./style.css";
import { CFG, type Pt } from "./config";
import { CameraHands, type HandObs, type HandSource, MouseHands } from "./hands";
import type { Control } from "./puppet";
import { drawCamera } from "./render";
import { loadGiong } from "./giong/data";
import { Game } from "./giong/game";

const canvas = document.getElementById("stage") as HTMLCanvasElement;
const ctx = canvas.getContext("2d")!;
const video = document.getElementById("video") as HTMLVideoElement;
const overlay = document.getElementById("overlay")!;
const statusEl = document.getElementById("status")!;

let game: Game;
let source: HandSource | null = null;
let fakeHands: HandObs[] | null = null;      // tests can inject hands
let lastHands: HandObs[] = [];

// ------------------------------------------------------------------ mapping
const V = CFG.view;
const W = V.size;
const S = W / 1600;
const stageOffsetY = V.split - V.stageCropY * S;

function camRect() {
  const vw = video.videoWidth || 640, vh = video.videoHeight || 480;
  const sc = Math.max(W / vw, V.split / vh);
  const dw = vw * sc, dh = vh * sc;
  return { ox: (W - dw) / 2, oy: (V.split - dh) / 2, dw, dh };
}
const normToScreen = (p: Pt): Pt => { const r = camRect(); return { x: r.ox + p.x * r.dw, y: r.oy + p.y * r.dh }; };
const screenToNorm = (p: Pt): Pt => { const r = camRect(); return { x: (p.x - r.ox) / r.dw, y: (p.y - r.oy) / r.dh }; };
const screenToStage = (p: Pt): Pt => ({ x: p.x / S, y: (p.y - stageOffsetY) / S });
const camToStage = (p: Pt): Pt => screenToStage(normToScreen(p));

function toControl(h: HandObs): Control {
  const palmIdx = [0, 5, 9, 13, 17];
  const palmN = palmIdx.reduce((a, i) => ({ x: a.x + h.lm[i].x / 5, y: a.y + h.lm[i].y / 5 }), { x: 0, y: 0 });
  return { palm: camToStage(palmN), tips: [4, 8, 12, 16, 20].map((i) => camToStage(h.lm[i])), indexRight: h.lm[5].x > h.lm[17].x };
}

// ------------------------------------------------------------------ input
async function useCamera() {
  source?.dispose();
  source = null;
  overlay.classList.remove("hidden");
  try {
    const cam = new CameraHands(video);
    await cam.init((s) => (statusEl.textContent = s));
    source = cam;
    overlay.classList.add("hidden");
  } catch (e) {
    console.error(e);
    statusEl.textContent = `Could not open the camera or load the model: ${(e as Error).message}. Check camera permission and the network (the page must run on https or localhost), or try mouse mode.`;
  }
}

function useMouse() {
  source?.dispose();
  source = new MouseHands(canvas, screenToNorm);
  overlay.classList.add("hidden");
}

// ------------------------------------------------------------------ loop
let last = performance.now();

function frame(now: number) {
  const dt = Math.min(0.05, (now - last) / 1000);
  last = now;
  const obs = fakeHands ?? source?.poll(now) ?? null;
  if (obs) { lastHands = obs; game.onHands(obs.map(toControl), now); }
  game.update(dt, now);
  render(now);
  requestAnimationFrame(frame);
}

function render(now: number) {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, W, W);
  const hint = lastHands.length ? [] : source?.kind === "mouse"
    ? ["MOUSE MODE", "Hold the left button: left half moves the bamboo, right half moves the horse legs",
      "Keys 2, 3: lift index / middle finger · release the button: strings break"]
    : ["Camera is off", "Press Camera [C] or Mouse [M]"];
  drawCamera(ctx, W, V.split, source?.kind === "camera" ? source.video : undefined, camRect(), lastHands, normToScreen, hint);

  const sh = game.shake;
  const jx = sh ? (Math.random() - 0.5) * 18 * sh : 0, jy = sh ? (Math.random() - 0.5) * 12 * sh : 0;
  ctx.save();
  ctx.beginPath(); ctx.rect(0, V.split, W, W - V.split); ctx.clip();
  ctx.setTransform(S, 0, 0, S, jx, stageOffsetY + jy);
  game.drawStage(ctx);
  ctx.restore();

  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = "#A63A25";
  ctx.fillRect(0, V.split - 3, W, 6);
  ctx.fillStyle = "#D7A443";
  ctx.fillRect(0, V.split - 1, W, 2);

  ctx.setTransform(S, 0, 0, S, jx, stageOffsetY + jy);
  game.drawStrings(ctx, now);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
}

// ------------------------------------------------------------------ boot
async function boot() {
  statusEl.textContent = "Loading the puppet and the stage...";
  const data = await loadGiong();
  canvas.width = W;
  canvas.height = W;
  game = new Game(data, V.stageCropY);
  statusEl.textContent = "Choose how to play.";
  requestAnimationFrame(frame);
}

document.getElementById("btnCamera")!.onclick = () => useCamera();
document.getElementById("btnMouse")!.onclick = () => useMouse();
window.addEventListener("keydown", (e) => {
  const k = e.key.toLowerCase();
  if (k === "d") game.debug = !game.debug;
  else if (k === "enter") game.pressStart();
  else if (k === "c") useCamera();
  else if (k === "m") useMouse();
});
document.addEventListener("visibilitychange", () => { last = performance.now(); });

boot().catch((e) => {
  console.error(e);
  statusEl.textContent = `Could not load the assets: ${(e as Error).message}. Run "npm run dev" (it copies the assets first).`;
});

// handy for automated tests
(window as unknown as { __app: object }).__app = {
  get game() { return game; }, useMouse,
  /** Inject hands in normalised camera coords (null = back to the real source). */
  setHands(h: HandObs[] | null) { fakeHands = h; },
};
