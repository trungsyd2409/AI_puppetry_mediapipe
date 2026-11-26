// Loads rig.json files, part images and the stage background.
const BASE = import.meta.env.BASE_URL;

export type Shape =
  | { type: "circle"; c: [number, number]; r: number }
  | { type: "capsule"; a: [number, number]; b: [number, number]; r: number };

export interface RigPart {
  id: string;
  parent: string | null;
  z: number;
  png: string;
  origin: [number, number];
  size: [number, number];
  pivot: [number, number];
  pivotWorld: [number, number];
  limitDeg: [number, number] | null;
  density: number;
  colliders: Shape[];
}

export interface RigString {
  id: string;
  part: string;
  anchor: [number, number];
  anchorWorld: [number, number];
  finger: string;
  mpLandmark: number;
}

export interface Rig {
  name: string;
  canvas: [number, number];
  feetY: number;
  parts: RigPart[];
  strings: RigString[];
}

export interface PuppetAsset { id: string; rig: Rig; images: Map<string, HTMLImageElement> }

export interface Stage {
  size: [number, number];
  floorY: number;
  stageX: [number, number];
  puppetHeight: number;
  bg: HTMLImageElement;
  fg: HTMLImageElement;
}

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error(`cannot load ${src}`));
    img.src = src;
  });
}

async function json<T>(path: string): Promise<T> {
  const res = await fetch(BASE + path);
  if (!res.ok) throw new Error(`cannot load ${path} (${res.status})`);
  return res.json() as Promise<T>;
}

export async function loadPuppets(): Promise<PuppetAsset[]> {
  const ids = await json<string[]>("assets/puppets.json");
  return Promise.all(ids.map(async (id) => {
    const rig = await json<Rig>(`assets/puppet/${id}/rig.json`);
    const images = new Map<string, HTMLImageElement>();
    await Promise.all(rig.parts.map(async (p) => {
      images.set(p.id, await loadImage(`${BASE}assets/puppet/${id}/${p.png}`));
    }));
    return { id, rig, images };
  }));
}

export async function loadStage(): Promise<Stage> {
  const s = await json<{ size: [number, number]; floorY: number; stageX: [number, number]; puppetHeight: number }>(
    "assets/background/stage.json");
  const [bg, fg] = await Promise.all([
    loadImage(`${BASE}assets/background/stage_bg.png`),
    loadImage(`${BASE}assets/background/stage_fg.png`),
  ]);
  return { ...s, bg, fg };
}
