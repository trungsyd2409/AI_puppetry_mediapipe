// Loads the chim lac rig, the village stage (layers + props) and the flappy fx (+ the stage curtain).
import { type GPart, type GStage, json, loadImage, type PropDef, type Sprite, type SpriteJson, sprites } from "../giong/data";

const BASE = import.meta.env.BASE_URL;

export interface BirdString { id: string; part: string; anchorWorld: [number, number]; finger: string; mpLandmark: number }
export interface BirdRig {
  canvas: [number, number]; pngScale: number;
  parts: GPart[]; strings: BirdString[];
  head: [number, number]; beakTip: [number, number];
}
export interface FlappyData { rig: BirdRig; stage: GStage & { groundY: number }; fx: Record<string, Sprite> }

export async function loadFlappy(): Promise<FlappyData> {
  const rigJ = await json<Omit<BirdRig, "parts"> & { parts: Omit<GPart, "img">[] }>("assets/puppet/chim_lac/rig.json");
  const parts = await Promise.all(rigJ.parts.map(async (p) => ({ ...p, img: await loadImage(`${BASE}assets/puppet/chim_lac/${p.png}`) })));

  const st = await json<{
    size: [number, number]; floorY: number; groundY: number; wind: number;
    layers: { id: string; png: string | null; parallax: number; front: boolean }[];
    sprites: SpriteJson; props: PropDef[];
  }>("assets/background_lang/stage.json");
  const layers = await Promise.all(st.layers.map(async (l) => ({
    id: l.id, parallax: l.parallax, front: l.front,
    img: l.png ? await loadImage(`${BASE}assets/background_lang/${l.png}`) : null,
  })));
  const stage = { size: st.size, floorY: st.floorY, groundY: st.groundY, wind: st.wind, layers, props: st.props,
    sprites: await sprites("assets/background_lang", st.sprites) };

  const fx = await sprites("assets/fx_flappy", await json<SpriteJson>("assets/fx_flappy/fx.json"));
  const giongFx = await json<SpriteJson>("assets/fx_giong/fx.json");
  const curtain = await sprites("assets/fx_giong", { curtain_panel: giongFx.curtain_panel, curtain_top: giongFx.curtain_top,
    score_plaque: giongFx.score_plaque });
  return { rig: { ...rigJ, parts }, stage, fx: { ...fx, ...curtain } };
}
