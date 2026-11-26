// Hand input: MediaPipe webcam tracking, or a mouse "fake hand" for testing.
// Both output landmarks in normalised [0,1] coords, already mirrored (selfie view).
import { FilesetResolver, HandLandmarker } from "@mediapipe/tasks-vision";
import { CFG, type Pt } from "./config";

export interface HandObs { lm: Pt[]; score: number }

export interface HandSource {
  readonly kind: "camera" | "mouse";
  /** New observations, or null when there is no new frame yet. */
  poll(now: number): HandObs[] | null;
  inferMs: number;
  lastSampleTime: number;
  video?: HTMLVideoElement;
  dispose(): void;
}

const BASE = import.meta.env.BASE_URL;
const REMOTE_MODEL =
  "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task";

// ------------------------------------------------------------------ camera
export class CameraHands implements HandSource {
  readonly kind = "camera" as const;
  inferMs = 0;
  lastSampleTime = 0;
  video: HTMLVideoElement;
  private landmarker!: HandLandmarker;
  private lastVideoTime = -1;
  private lastDetect = 0;
  private stream: MediaStream | null = null;

  constructor(video: HTMLVideoElement) { this.video = video; }

  async init(onStatus: (s: string) => void) {
    onStatus("Đang xin quyền camera...");
    this.stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" }, audio: false,
    });
    this.video.srcObject = this.stream;
    this.video.muted = true;
    this.video.playsInline = true;
    await this.video.play();

    onStatus("Đang tải mô hình MediaPipe...");
    const vision = await FilesetResolver.forVisionTasks(`${BASE}mediapipe/wasm`);
    const local = `${BASE}models/hand_landmarker.task`;
    // dev servers answer missing files with index.html, so check the content type too
    const hasLocal = await fetch(local, { method: "HEAD" })
      .then((r) => r.ok && !(r.headers.get("content-type") ?? "").includes("text/html"))
      .catch(() => false);
    const modelAssetPath = hasLocal ? local : REMOTE_MODEL;
    const make = (delegate: "GPU" | "CPU") => HandLandmarker.createFromOptions(vision, {
      baseOptions: { modelAssetPath, delegate },
      runningMode: "VIDEO",
      numHands: 2,
      minHandDetectionConfidence: 0.5,
      minHandPresenceConfidence: 0.5,
      minTrackingConfidence: 0.5,
    });
    try { this.landmarker = await make("GPU"); }
    catch { this.landmarker = await make("CPU"); }
  }

  poll(now: number): HandObs[] | null {
    const v = this.video;
    if (v.readyState < 2 || v.currentTime === this.lastVideoTime) return null;
    if (now - this.lastDetect < 1000 / CFG.maxDetectHz) return null;
    this.lastVideoTime = v.currentTime;
    this.lastDetect = now;
    const t0 = performance.now();
    const res = this.landmarker.detectForVideo(v, now);
    this.inferMs = performance.now() - t0;
    this.lastSampleTime = now;
    return res.landmarks.map((lm, i) => ({
      lm: lm.map((p) => ({ x: 1 - p.x, y: p.y })),
      score: res.handedness[i]?.[0]?.score ?? 1,
    }));
  }

  dispose() {
    this.stream?.getTracks().forEach((t) => t.stop());
    this.landmarker?.close();
  }
}

// ------------------------------------------------------------------ mouse
// Hold the mouse button on the stage = hand visible. Keys 1..5 lift a finger
// (thumb, index, middle, ring, pinky). Release = hand lost -> puppet falls.
const FINGER_TIPS = [4, 8, 12, 16, 20];

export class MouseHands implements HandSource {
  readonly kind = "mouse" as const;
  inferMs = 0;
  lastSampleTime = 0;
  private pos: Pt | null = null;       // normalised
  private down = false;
  private lifted = new Set<number>();
  private lastEmit = 0;
  private off: (() => void)[] = [];

  constructor(canvas: HTMLCanvasElement, private stageToNorm: (p: Pt) => Pt) {
    const toStage = (e: PointerEvent): Pt => {
      const r = canvas.getBoundingClientRect();
      return { x: ((e.clientX - r.left) / r.width) * canvas.width, y: ((e.clientY - r.top) / r.height) * canvas.height };
    };
    const move = (e: PointerEvent) => { this.pos = this.stageToNorm(toStage(e)); };
    const down = (e: PointerEvent) => { move(e); this.down = true; canvas.setPointerCapture(e.pointerId); };
    const up = () => { this.down = false; };
    const key = (e: KeyboardEvent) => {
      const i = "12345".indexOf(e.key);
      if (i < 0) return;
      if (e.type === "keydown") this.lifted.add(i); else this.lifted.delete(i);
    };
    canvas.addEventListener("pointermove", move);
    canvas.addEventListener("pointerdown", down);
    window.addEventListener("pointerup", up);
    window.addEventListener("keydown", key);
    window.addEventListener("keyup", key);
    this.off.push(() => {
      canvas.removeEventListener("pointermove", move);
      canvas.removeEventListener("pointerdown", down);
      window.removeEventListener("pointerup", up);
      window.removeEventListener("keydown", key);
      window.removeEventListener("keyup", key);
    });
  }

  poll(now: number): HandObs[] | null {
    if (now - this.lastEmit < 1000 / CFG.maxDetectHz) return null;
    this.lastEmit = now;
    this.lastSampleTime = now;
    if (!this.down || !this.pos) return [];
    return [{ lm: fakeHand(this.pos, this.lifted), score: 1 }];
  }

  dispose() { this.off.forEach((f) => f()); }
}

/** 21 MediaPipe-style landmarks for a hand hanging fingers-down at `palm`. */
function fakeHand(palm: Pt, lifted: Set<number>): Pt[] {
  const lm: Pt[] = new Array(21).fill(null).map(() => ({ x: palm.x, y: palm.y }));
  lm[0] = { x: palm.x, y: palm.y - 0.07 };                 // wrist above the palm
  const bases = [-0.045, -0.03, -0.005, 0.02, 0.04];        // MCP x offsets
  const tipDx = [-0.075, -0.04, -0.005, 0.03, 0.06];
  const tipDy = [0.03, 0.085, 0.095, 0.088, 0.07];
  for (let f = 0; f < 5; f++) {
    const lift = lifted.has(f) ? -0.06 : 0;
    const mcp = { x: palm.x + bases[f], y: palm.y + (f === 0 ? -0.03 : 0) };
    const tip = { x: palm.x + tipDx[f], y: palm.y + tipDy[f] + lift };
    const first = f === 0 ? 1 : f * 4 + 1;
    for (let j = 0; j < 4; j++) {
      const t = (j + 1) / 4;
      lm[first + j] = { x: mcp.x + (tip.x - mcp.x) * t, y: mcp.y + (tip.y - mcp.y) * t };
    }
    lm[FINGER_TIPS[f]] = tip;
  }
  return lm;
}

export const HAND_CONNECTIONS: [number, number][] = [
  [0, 1], [1, 2], [2, 3], [3, 4], [0, 5], [5, 6], [6, 7], [7, 8], [5, 9], [9, 10], [10, 11], [11, 12],
  [9, 13], [13, 14], [14, 15], [15, 16], [13, 17], [17, 18], [18, 19], [19, 20], [0, 17],
];
