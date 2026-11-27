// Runs before `npm run dev` / `npm run build`.
// 1. Copies the puppet + stage assets from ../assets into public/assets
// 2. Copies the MediaPipe wasm files into public/mediapipe/wasm
// 3. Downloads the hand landmarker model into public/models (once)
import { cpSync, existsSync, mkdirSync, readdirSync, rmSync, statSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const WEB = join(dirname(fileURLToPath(import.meta.url)), "..");
const ASSETS = join(WEB, "..", "assets");
const PUB = join(WEB, "public");
const MODEL_URL =
  "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task";

function copyPuppets() {
  const dst = join(PUB, "assets");
  rmSync(dst, { recursive: true, force: true });
  const puppetRoot = join(ASSETS, "puppet");
  const ids = [];
  for (const name of readdirSync(puppetRoot)) {
    const dir = join(puppetRoot, name);
    if (!statSync(dir).isDirectory() || !existsSync(join(dir, "rig.json"))) continue;
    mkdirSync(join(dst, "puppet", name, "parts"), { recursive: true });
    cpSync(join(dir, "rig.json"), join(dst, "puppet", name, "rig.json"));
    for (const f of readdirSync(join(dir, "parts")))
      if (f.endsWith(".png")) cpSync(join(dir, "parts", f), join(dst, "puppet", name, "parts", f));
    ids.push(name);
  }
  // every assets/<folder>/stage.json is a scene background
  const scenes = [];
  for (const name of readdirSync(ASSETS)) {
    const dir = join(ASSETS, name);
    if (!statSync(dir).isDirectory() || !existsSync(join(dir, "stage.json"))) continue;
    mkdirSync(join(dst, name), { recursive: true });
    for (const f of readdirSync(dir))
      if (f.endsWith(".png") || f.endsWith(".json")) cpSync(join(dir, f), join(dst, name, f));
    if (existsSync(join(dir, "props"))) {
      mkdirSync(join(dst, name, "props"), { recursive: true });
      for (const f of readdirSync(join(dir, "props")))
        if (f.endsWith(".png")) cpSync(join(dir, "props", f), join(dst, name, "props", f));
    }
    scenes.push(name);
  }
  writeFileSync(join(dst, "puppets.json"), JSON.stringify(ids, null, 2));
  console.log(`[setup] assets copied: puppets ${ids.join(", ")}; scenes ${scenes.join(", ")}`);
}

function copyWasm() {
  const src = join(WEB, "node_modules", "@mediapipe", "tasks-vision", "wasm");
  const dst = join(PUB, "mediapipe", "wasm");
  if (!existsSync(src)) {
    console.warn("[setup] MediaPipe not installed yet, run `npm install` first");
    return;
  }
  mkdirSync(dst, { recursive: true });
  cpSync(src, dst, { recursive: true });
  console.log("[setup] MediaPipe wasm copied");
}

async function fetchModel() {
  const dst = join(PUB, "models", "hand_landmarker.task");
  if (existsSync(dst) && statSync(dst).size > 1_000_000) return;
  mkdirSync(dirname(dst), { recursive: true });
  try {
    const res = await fetch(MODEL_URL);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    writeFileSync(dst, Buffer.from(await res.arrayBuffer()));
    console.log("[setup] hand_landmarker.task downloaded");
  } catch (e) {
    console.warn(`[setup] could not download the model (${e.message}); the app will load it from Google at runtime`);
  }
}

copyPuppets();
copyWasm();
await fetchModel();
