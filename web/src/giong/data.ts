// Loads the Giong rig, the parallax stage (layers + animated props) and the fx sprites.
import type { Shape } from "../assets";

const BASE = import.meta.env.BASE_URL;

export interface GPart {
  id: string; parent: string | null; z: number; png: string;
  origin: [number, number]; size: [number, number];
  pivot: [number, number]; pivotWorld: [number, number];
  limitDeg: [number, number] | null; density: number; colliders: Shape[];
  img: HTMLImageElement;
}

export interface GString { id: string; part: string; anchorWorld: [number, number]; hand: "left" | "right"; finger: string; mpLandmark: number }

export interface GRig {
  canvas: [number, number]; feetY: number; groundY: number; pngScale: number;
  parts: GPart[]; strings: GString[];
  gripNear: [number, number]; gripFar: [number, number];
  bambooEnds: [[number, number], [number, number]];
  tailRoot: [number, number];
}

export interface Sprite { img: HTMLImageElement; size: [number, number]; anchor: [number, number]; pngScale: number }

export interface PropDef {
  layer: string; type: "anim" | "sway" | "smoke" | "drift" | "flock" | "spin" | "catapult";
  x: number; y: number | [number, number]; scale?: number | [number, number];
  frames?: string[]; fps?: number; sprite?: string;
  amp?: number; speed?: number; vx?: number | [number, number]; bob?: number;
  rate?: number; life?: number; rise?: number; grow?: number; embers?: boolean;
  count?: number; period?: number;
}

export interface GStage {
  size: [number, number]; floorY: number; wind: number;
  layers: { id: string; img: HTMLImageElement | null; parallax: number; front: boolean }[];
  sprites: Record<string, Sprite>;
  props: PropDef[];
}

export interface GData { rig: GRig; stage: GStage; fx: Record<string, Sprite> }

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

type SpriteJson = Record<string, { png: string; size: [number, number]; anchor: [number, number]; pngScale: number }>;

async function sprites(dir: string, defs: SpriteJson): Promise<Record<string, Sprite>> {
  const out: Record<string, Sprite> = {};
  await Promise.all(Object.entries(defs).map(async ([k, v]) => {
    out[k] = { img: await loadImage(`${BASE}${dir}/${v.png}`), size: v.size, anchor: v.anchor, pngScale: v.pngScale };
  }));
  return out;
}

export async function loadGiong(): Promise<GData> {
  const rigJ = await json<Omit<GRig, "parts"> & { parts: Omit<GPart, "img">[] }>("assets/puppet/giong/rig.json");
  const parts = await Promise.all(rigJ.parts.map(async (p) => ({
    ...p, img: await loadImage(`${BASE}assets/puppet/giong/${p.png}`),
  })));
  const rig: GRig = { ...rigJ, parts };

  const st = await json<{
    size: [number, number]; floorY: number; wind: number;
    layers: { id: string; png: string | null; parallax: number; front: boolean }[];
    sprites: SpriteJson; props: PropDef[];
  }>("assets/background_giong/stage.json");
  const layers = await Promise.all(st.layers.map(async (l) => ({
    id: l.id, parallax: l.parallax, front: l.front,
    img: l.png ? await loadImage(`${BASE}assets/background_giong/${l.png}`) : null,
  })));
  const stage: GStage = {
    size: st.size, floorY: st.floorY, wind: st.wind, layers, props: st.props,
    sprites: await sprites("assets/background_giong", st.sprites),
  };
  const fx = await sprites("assets/fx_giong", await json<SpriteJson>("assets/fx_giong/fx.json"));
  return { rig, stage, fx };
}

/** Draw a sprite with its anchor at (x, y). s = stage px per design unit. */
export function drawSprite(ctx: CanvasRenderingContext2D, sp: Sprite | undefined, x: number, y: number,
  s = 1, rot = 0, alpha = 1, flip = false) {
  if (!sp) return;
  const k = s / sp.pngScale;
  ctx.save();
  if (alpha < 1) ctx.globalAlpha *= Math.max(0, alpha);
  ctx.translate(x, y);
  if (rot) ctx.rotate(rot);
  ctx.scale(flip ? -k : k, k);
  ctx.drawImage(sp.img, -sp.anchor[0] * sp.pngScale, -sp.anchor[1] * sp.pngScale);
  ctx.restore();
}
