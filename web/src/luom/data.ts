// Loads the Luom rig, the layered paper stage (sky colours, sun, stage frame) and the fx sprites.
import { type GPart, type GStage, json, loadImage, type PropDef, type Sprite, type SpriteJson, sprites } from "../giong/data";

const BASE = import.meta.env.BASE_URL;

export interface LuomString { id: string; part: string; anchorWorld: [number, number]; finger: string; mpLandmark: number }
export interface LuomRig {
  canvas: [number, number]; pngScale: number; groundY: number;
  parts: GPart[]; strings: LuomString[];
  headCenter: [number, number]; hips: [number, number][]; ankles: [number, number][];
}
export interface SkyTime { top: string; bottom: string; sun: string; tint: [number, number, number, number] }
export interface LuomStage extends GStage {
  groundY: number;
  frame: { bottom: string; top: string };
  sun: { sprite: string; arc: { x0: number; x1: number; yLow: number; yHigh: number }; scale: number };
  skyTimes: Record<"morning" | "afternoon" | "dusk", SkyTime>;
  vignette: { strength: number; radius: number; color: [number, number, number] };
  paper: HTMLImageElement;
}
export type FxSprite = Sprite & { box?: [number, number, number, number] };
export interface LuomData { rig: LuomRig; stage: LuomStage; fx: Record<string, FxSprite> }

export async function loadLuom(): Promise<LuomData> {
  const rigJ = await json<Omit<LuomRig, "parts"> & { parts: Omit<GPart, "img">[] }>("assets/puppet/luom/rig.json");
  const parts = await Promise.all(rigJ.parts.map(async (p) => ({ ...p, img: await loadImage(`${BASE}assets/puppet/luom/${p.png}`) })));

  const dir = "assets/background_luom";
  const st = await json<Omit<LuomStage, "layers" | "sprites" | "paper"> & {
    layers: { id: string; png: string | null; parallax: number; front: boolean }[];
    sprites: SpriteJson; props: PropDef[]; paper: string;
  }>(`${dir}/stage.json`);
  const layers = await Promise.all(st.layers.map(async (l) => ({
    id: l.id, parallax: l.parallax, front: l.front,
    img: l.png ? await loadImage(`${BASE}${dir}/${l.png}`) : null,
  })));
  const stage: LuomStage = {
    ...st, layers, sprites: await sprites(dir, st.sprites), paper: await loadImage(`${BASE}${dir}/${st.paper}`),
  };

  const fxJ = await json<SpriteJson & Record<string, { box?: [number, number, number, number] }>>("assets/fx_luom/fx.json");
  const fx: Record<string, FxSprite> = await sprites("assets/fx_luom", fxJ);
  for (const [k, v] of Object.entries(fxJ)) if (v.box) fx[k].box = v.box;
  return { rig: { ...rigJ, parts }, stage, fx };
}
