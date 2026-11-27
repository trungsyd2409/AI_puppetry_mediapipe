import "./style.css";
import { CFG, DEFAULT_SCENE, SCENES, type Pt } from "./config";
import { loadPuppets, loadStage, type PuppetAsset, type Stage } from "./assets";
import { CameraHands, type HandObs, type HandSource, MouseHands } from "./hands";
import { createWorld } from "./physics";
import { type Control, Puppet } from "./puppet";
import { drawCamera } from "./render";
import type { SceneFx } from "./cloth";
import { ThuyDinhFx } from "./fx_thuydinh";
import { SnowFx } from "./fx_snow";
import { HitFx } from "./fx_blood";
import { Combat } from "./combat";
import type { World } from "planck";

const LABELS: Record<string, string> = { teu: "Chú Tễu", co_gai: "Cô gái áo dài", chien_binh_tuyet: "Chiến binh tuyết", ve_binh_streltsy: "Vệ binh Streltsy" };

const sceneId = new URLSearchParams(location.search).get("scene") ?? DEFAULT_SCENE;
const SCENE = SCENES[sceneId] ?? SCENES[DEFAULT_SCENE];

const canvas = document.getElementById("stage") as HTMLCanvasElement;
const ctx = canvas.getContext("2d")!;
const video = document.getElementById("video") as HTMLVideoElement;
const overlay = document.getElementById("overlay")!;
const statusEl = document.getElementById("status")!;

let stage: Stage;
let amb: SceneFx;
let assets: PuppetAsset[] = [];
let world: World;
let puppets: Puppet[] = [];
let source: HandSource | null = null;
let lastHands: HandObs[] = [];
let showDebug = false;
let hitFx: HitFx;
let combat: Combat;

// ------------------------------------------------------------------ mapping
// Screen = square canvas. Top `split` px: mirrored webcam (cover-fit).
// Bottom: the 1600x900 stage scaled to the canvas width, starting at stage row stageCropY.
// Physics and puppets live in stage pixels; fingertips above the stage get negative stage y,
// so strings naturally run from the camera half down to the puppets.
const V = CFG.view;
const W = V.size;
const S = W / 1600;                                   // stage px -> screen px
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
let shakeX = 0, shakeY = 0;
const stageTransform = () => ctx.setTransform(S, 0, 0, S, shakeX, stageOffsetY + shakeY);

function toControl(h: HandObs): Control {
  const palmIdx = [0, 5, 9, 13, 17];
  const palmN = palmIdx.reduce((a, i) => ({ x: a.x + h.lm[i].x / 5, y: a.y + h.lm[i].y / 5 }), { x: 0, y: 0 });
  return {
    palm: camToStage(palmN),
    tips: [4, 8, 12, 16, 20].map((i) => camToStage(h.lm[i])),
    // right hand -> index side wired to the screen-left limbs; fall back to the knuckles if unknown
    indexRight: h.right !== undefined ? !h.right : h.lm[5].x > h.lm[17].x,
  };
}

// ------------------------------------------------------------------ puppets
function spawn() {
  puppets.forEach((p) => p.destroy());
  const ids = SCENE.puppets.filter((id) => assets.some((a) => a.id === id));
  const xs = ids.length === 1 ? [800] : ids.map((_, i) => 670 + (260 * i) / Math.max(1, ids.length - 1));
  puppets = ids.map((id, i) => new Puppet(world, assets.find((a) => a.id === id)!, stage, xs[i], LABELS[id] ?? id));
}

// Which hand drives which puppet: sort hands left->right and give them to the puppets
// sorted by their current x. A single hand keeps the puppet it had last time.
let lastOwner: Puppet | null = null;
function assign(controls: Control[]): Map<Puppet, Control> {
  const out = new Map<Puppet, Control>();
  if (!controls.length || !puppets.length) return out;
  if (puppets.length === 1) { out.set(puppets[0], controls[0]); return out; }
  const byX = [...puppets].sort((a, b) => a.torsoX() - b.torsoX());
  if (controls.length >= 2) {
    const hs = [...controls].sort((a, b) => a.palm.x - b.palm.x);
    out.set(byX[0], hs[0]);
    out.set(byX[byX.length - 1], hs[hs.length - 1]);
    lastOwner = null;
    return out;
  }
  const c = controls[0];
  const owner = lastOwner ?? byX.reduce((best, p) =>
    Math.abs(p.torsoX() - c.palm.x) < Math.abs(best.torsoX() - c.palm.x) ? p : best);
  out.set(owner, c);
  lastOwner = owner;
  return out;
}

// ------------------------------------------------------------------ input sources
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
    statusEl.textContent = `Lỗi khi mở camera hoặc tải mô hình: ${(e as Error).message}. Kiểm tra quyền camera và mạng (trang phải chạy trên https hoặc localhost), hoặc thử chế độ chuột.`;
  }
}

function useMouse() {
  source?.dispose();
  source = new MouseHands(canvas, screenToNorm);
  overlay.classList.add("hidden");
}

// ------------------------------------------------------------------ loop
let last = performance.now(), acc = 0;

function frame(now: number) {
  const dt = Math.min(0.1, (now - last) / 1000);
  last = now;

  const obs = source?.poll(now) ?? null;
  if (obs) {
    lastHands = obs;
    const owners = assign(obs.map(toControl));
    for (const p of puppets) p.onHand(owners.get(p) ?? null, now);
  }

  for (const p of puppets) p.update(dt, now);
  amb.update(dt);
  hitFx.update(dt);
  combat.update(dt);
  const sh = combat.shake * combat.shake * CFG.combat.shakePx;
  shakeX = (Math.random() - 0.5) * 2 * sh;
  shakeY = (Math.random() - 0.5) * 2 * sh;
  acc += dt;
  let n = 0;
  while (acc >= CFG.fixedDt && n < CFG.maxSubSteps) {
    const wind = amb.windAccel();
    for (const p of puppets) { p.applyForces(); p.applyWind(wind); }
    world.step(CFG.fixedDt, 8, 3);
    combat.resolve(now);
    acc -= CFG.fixedDt;
    n++;
  }
  if (n === CFG.maxSubSteps) acc = 0;

  render(now);
  requestAnimationFrame(frame);
}

function render(now: number) {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, W, W);

  // top: camera
  const hint = lastHands.length ? [] : source?.kind === "mouse"
    ? ["CHẾ ĐỘ CHUỘT", "Giữ chuột trái ở đây để làm bàn tay", "Phím 1-5: nhấc từng ngón · thả chuột: rối ngã"]
    : ["Chưa bật camera", "Bấm Camera [C] hoặc Chuột [M]"];
  drawCamera(ctx, W, V.split, source?.kind === "camera" ? source.video : undefined, camRect(), lastHands, normToScreen, hint);

  // bottom: stage
  ctx.save();
  ctx.beginPath(); ctx.rect(0, V.split, W, W - V.split); ctx.clip();
  stageTransform();
  amb.drawBackground(ctx);
  hitFx.drawBack(ctx);
  for (const p of puppets) p.draw(ctx);
  hitFx.drawFront(ctx);
  amb.drawForeground(ctx);
  ctx.restore();

  // divider
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = SCENE.accent;
  ctx.fillRect(0, V.split - 2, W, 4);

  // strings cross both halves
  stageTransform();
  for (const p of puppets) p.drawStrings(ctx, now);
  if (showDebug) puppets.forEach((p) => p.drawDebug(ctx));
  ctx.setTransform(1, 0, 0, 1, 0, 0);

}

// ------------------------------------------------------------------ boot
async function boot() {
  statusEl.textContent = "Đang tải rối và sân khấu...";
  [stage, assets] = await Promise.all([loadStage(SCENE.background), loadPuppets(SCENE.puppets)]);
  canvas.width = W;
  canvas.height = W;
  world = createWorld(stage);
  hitFx = new HitFx(stage.floorY);
  combat = new Combat(world, hitFx);
  amb = SCENE.fx === "snow" ? new SnowFx(stage) : new ThuyDinhFx(stage);
  spawn();
  statusEl.textContent = "Chọn cách điều khiển.";
  requestAnimationFrame(frame);
}

document.title = SCENE.title;
document.getElementById("title")!.textContent = SCENE.title;
document.getElementById("btnCamera")!.onclick = () => useCamera();
document.getElementById("btnMouse")!.onclick = () => useMouse();
window.addEventListener("keydown", (e) => {
  const k = e.key.toLowerCase();
  if (k === "d") showDebug = !showDebug;
  else if (k === "r") spawn();
  else if (k === "c") useCamera();
  else if (k === "m") useMouse();
});
document.addEventListener("visibilitychange", () => { last = performance.now(); acc = 0; });

boot().catch((e) => {
  console.error(e);
  statusEl.textContent = `Lỗi tải asset: ${(e as Error).message}. Hãy chạy "npm run dev" (lệnh này tự chép asset).`;
});

// handy for automated tests
(window as unknown as { __app: object }).__app = { get puppets() { return puppets; }, useMouse, get amb() { return amb; }, get world() { return world; }, get combat() { return combat; } };
