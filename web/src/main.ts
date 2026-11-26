import "./style.css";
import { CFG, type Pt } from "./config";
import { loadPuppets, loadStage, type PuppetAsset, type Stage } from "./assets";
import { CameraHands, type HandObs, type HandSource, MouseHands } from "./hands";
import { createWorld } from "./physics";
import { type Control, Puppet } from "./puppet";
import { drawHud, drawInset } from "./render";
import type { World } from "planck";

const LABELS: Record<string, string> = { teu: "Chú Tễu", co_gai: "Cô gái áo dài" };

const canvas = document.getElementById("stage") as HTMLCanvasElement;
const ctx = canvas.getContext("2d")!;
const video = document.getElementById("video") as HTMLVideoElement;
const overlay = document.getElementById("overlay")!;
const statusEl = document.getElementById("status")!;
const pickEl = document.getElementById("pick") as HTMLSelectElement;

let stage: Stage;
let assets: PuppetAsset[] = [];
let world: World;
let puppets: Puppet[] = [];
let source: HandSource | null = null;
let lastHands: HandObs[] = [];
let showDebug = false, showHud = true;

// ------------------------------------------------------------------ mapping
const cm = CFG.camMap;
function camToStage(p: Pt): Pt {
  return {
    x: cm.stageX0 + ((p.x - cm.x0) / (cm.x1 - cm.x0)) * (cm.stageX1 - cm.stageX0),
    y: cm.stageY0 + ((p.y - cm.y0) / (cm.y1 - cm.y0)) * (cm.stageY1 - cm.stageY0),
  };
}
function stageToCam(p: Pt): Pt {
  return {
    x: cm.x0 + ((p.x - cm.stageX0) / (cm.stageX1 - cm.stageX0)) * (cm.x1 - cm.x0),
    y: cm.y0 + ((p.y - cm.stageY0) / (cm.stageY1 - cm.stageY0)) * (cm.y1 - cm.y0),
  };
}
function toControl(h: HandObs): Control {
  const palmIdx = [0, 5, 9, 13, 17];
  const palmN = palmIdx.reduce((a, i) => ({ x: a.x + h.lm[i].x / 5, y: a.y + h.lm[i].y / 5 }), { x: 0, y: 0 });
  return { palm: camToStage(palmN), tips: [4, 8, 12, 16, 20].map((i) => camToStage(h.lm[i])) };
}

// ------------------------------------------------------------------ puppets
function spawn() {
  puppets.forEach((p) => p.destroy());
  const order = Object.keys(LABELS);
  const rank = (id: string) => (order.includes(id) ? order.indexOf(id) : 99);
  const ids = pickEl.value === "all" ? assets.map((a) => a.id).sort((a, b) => rank(a) - rank(b)) : [pickEl.value];
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
  source = new MouseHands(canvas, stageToCam);
  overlay.classList.add("hidden");
}

// ------------------------------------------------------------------ loop
let last = performance.now(), acc = 0, renderHz = 60, trackHz = 0, lastSample = 0;

function frame(now: number) {
  const dt = Math.min(0.1, (now - last) / 1000);
  last = now;
  renderHz += (1 / Math.max(dt, 1e-3) - renderHz) * 0.05;

  const obs = source?.poll(now) ?? null;
  if (obs) {
    if (lastSample) trackHz += (1000 / Math.max(1, now - lastSample) - trackHz) * 0.1;
    lastSample = now;
    lastHands = obs;
    const owners = assign(obs.map(toControl));
    for (const p of puppets) p.onHand(owners.get(p) ?? null, now);
  }

  for (const p of puppets) p.update(dt, now);
  acc += dt;
  let n = 0;
  while (acc >= CFG.fixedDt && n < CFG.maxSubSteps) {
    for (const p of puppets) p.applyForces();
    world.step(CFG.fixedDt, 8, 3);
    acc -= CFG.fixedDt;
    n++;
  }
  if (n === CFG.maxSubSteps) acc = 0;

  render(now);
  requestAnimationFrame(frame);
}

function render(now: number) {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.drawImage(stage.bg, 0, 0, canvas.width, canvas.height);
  for (const p of puppets) p.draw(ctx);
  for (const p of puppets) p.drawStrings(ctx, now);
  ctx.drawImage(stage.fg, 0, 0, canvas.width, canvas.height);
  if (showDebug) puppets.forEach((p) => p.drawDebug(ctx));
  if (showHud) {
    drawHud(ctx, {
      source: source ? (source.kind === "camera" ? "camera / MediaPipe" : "mouse (test)") : "none",
      hands: lastHands.length,
      renderHz, trackHz,
      inferMs: source?.inferMs ?? 0,
      sampleAge: source ? now - source.lastSampleTime : 0,
      puppets,
    });
    drawInset(ctx, canvas.width, source?.video, lastHands, source?.kind === "mouse");
  }
}

// ------------------------------------------------------------------ boot
async function boot() {
  statusEl.textContent = "Đang tải rối và sân khấu...";
  [stage, assets] = await Promise.all([loadStage(), loadPuppets()]);
  canvas.width = stage.size[0];
  canvas.height = stage.size[1];
  world = createWorld(stage);
  pickEl.innerHTML = `<option value="all">Cả hai rối</option>` +
    assets.map((a) => `<option value="${a.id}">${LABELS[a.id] ?? a.id}</option>`).join("");
  spawn();
  statusEl.textContent = "Chọn cách điều khiển.";
  requestAnimationFrame(frame);
}

document.getElementById("btnCamera")!.onclick = () => useCamera();
document.getElementById("btnMouse")!.onclick = () => useMouse();
document.getElementById("tbCamera")!.onclick = () => useCamera();
document.getElementById("tbMouse")!.onclick = () => useMouse();
document.getElementById("tbReset")!.onclick = () => spawn();
pickEl.onchange = () => spawn();
window.addEventListener("keydown", (e) => {
  if (e.target instanceof HTMLSelectElement) return;
  const k = e.key.toLowerCase();
  if (k === "d") showDebug = !showDebug;
  else if (k === "h") showHud = !showHud;
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
(window as unknown as { __app: object }).__app = { get puppets() { return puppets; }, useMouse };
