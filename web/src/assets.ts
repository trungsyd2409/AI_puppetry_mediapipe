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
  folder: string;
  size: [number, number];
  floorY: number;
  stageX: [number, number];
  puppetHeight: number;
  /** Everything else from stage.json (poles, water, fire, ...) for the scene module. */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  meta: Record<string, any>;
  layers: Record<string, HTMLImageElement>;
  props: Record<string, HTMLImageElement[]>;
  propScale: number;
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

/** Load the given puppets (all listed in puppets.json when `ids` is omitted). */
export async function loadPuppets(ids?: string[]): Promise<PuppetAsset[]> {
  const all = await json<string[]>("assets/puppets.json");
  const want = ids ? all.filter((id) => ids.includes(id)) : all;
  return Promise.all(want.map(async (id) => {
    const rig = await json<Rig>(`assets/puppet/${id}/rig.json`);
    const images = new Map<string, HTMLImageElement>();
    await Promise.all(rig.parts.map(async (p) => {
      images.set(p.id, await loadImage(`${BASE}assets/puppet/${id}/${p.png}`));
    }));
    return { id, rig, images };
  }));
}

/** Load assets/<folder>/stage.json and every image listed in its `layers` and `props`. */
export async function loadStage(folder: string): Promise<Stage> {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const s = await json<Record<string, any>>(`assets/${folder}/stage.json`);
  const img = (f: string) => loadImage(`${BASE}assets/${folder}/${f}`);
  const layers: Record<string, HTMLImageElement> = {};
  const props: Record<string, HTMLImageElement[]> = {};
  await Promise.all(Object.entries(s.layers ?? {}).map(async ([k, f]) => { layers[k] = await img(f as string); }));
  await Promise.all(Object.entries(s.props ?? {}).map(async ([k, v]) => {
    if (typeof v === "string") props[k] = [await img(v)];
    else if (Array.isArray(v)) props[k] = await Promise.all(v.map((f: string) => img(f)));
  }));
  return {
    folder, size: s.size, floorY: s.floorY, stageX: s.stageX, puppetHeight: s.puppetHeight,
    meta: s, layers, props, propScale: typeof s.props?.scale === "number" ? s.props.scale : 2,
  };
}
