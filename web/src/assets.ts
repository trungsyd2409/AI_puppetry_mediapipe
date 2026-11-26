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

export interface Pole { x: number; top: number; side: number }

export interface Stage {
  size: [number, number];
  floorY: number;
  stageX: [number, number];
  puppetHeight: number;
  poles: Pole[];
  water: { surfaceY: number; frontY: number };
  bg: HTMLImageElement;
  fgWater: HTMLImageElement;
  fgLotus: HTMLImageElement;
  props: { fish: HTMLImageElement; crane: HTMLImageElement[]; leaf: HTMLImageElement; scale: number };
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

interface StageJson {
  size: [number, number]; floorY: number; stageX: [number, number]; puppetHeight: number;
  poles: Pole[]; water: { surfaceY: number; frontY: number };
  layers: { bg: string; fgWater: string; fgLotus: string };
  props: { fish: string; crane: string[]; leaf: string; scale: number };
}

export async function loadStage(): Promise<Stage> {
  const s = await json<StageJson>("assets/background/stage.json");
  const img = (f: string) => loadImage(`${BASE}assets/background/${f}`);
  const [bg, fgWater, fgLotus, fish, leaf, ...crane] = await Promise.all([
    img(s.layers.bg), img(s.layers.fgWater), img(s.layers.fgLotus),
    img(s.props.fish), img(s.props.leaf), ...s.props.crane.map(img),
  ]);
  return {
    size: s.size, floorY: s.floorY, stageX: s.stageX, puppetHeight: s.puppetHeight,
    poles: s.poles, water: s.water, bg, fgWater, fgLotus,
    props: { fish, leaf, crane, scale: s.props.scale },
  };
}
