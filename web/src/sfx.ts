// Sound effects synthesised with the Web Audio API (no audio files needed).
// The AudioContext can only start after a user gesture, so call unlock() from a click.
import { CFG } from "./config";

export class Sfx {
  private ctx: AudioContext | null = null;
  private master: GainNode | null = null;
  private noiseBuf: AudioBuffer | null = null;
  private last = new Map<string, number>();
  enabled = CFG.sound.enabled;

  unlock() {
    if (!this.ctx) {
      const AC = window.AudioContext ?? (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      this.ctx = new AC();
      this.master = this.ctx.createGain();
      this.master.gain.value = CFG.sound.volume;
      const comp = this.ctx.createDynamicsCompressor();
      this.master.connect(comp).connect(this.ctx.destination);
      const len = this.ctx.sampleRate * 1.5;
      this.noiseBuf = this.ctx.createBuffer(1, len, this.ctx.sampleRate);
      const data = this.noiseBuf.getChannelData(0);
      for (let i = 0; i < len; i++) data[i] = Math.random() * 2 - 1;
    }
    void this.ctx.resume();
  }

  toggle() { this.enabled = !this.enabled; return this.enabled; }

  /** Rate limit per sound name. */
  private ok(name: string, gapMs: number) {
    if (!this.enabled || !this.ctx || this.ctx.state !== "running") return false;
    const now = performance.now();
    if (now - (this.last.get(name) ?? -1e9) < gapMs) return false;
    this.last.set(name, now);
    return true;
  }

  // ---------------------------------------------------------------- building blocks
  private env(g: GainNode, t: number, peak: number, attack: number, decay: number) {
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(peak, t + attack);
    g.gain.exponentialRampToValueAtTime(0.0001, t + attack + decay);
  }

  private noise(opts: { type: BiquadFilterType; f0: number; f1?: number; q?: number; peak: number; attack: number; decay: number; delay?: number }) {
    const c = this.ctx!, t = c.currentTime + (opts.delay ?? 0);
    const src = c.createBufferSource();
    src.buffer = this.noiseBuf;
    const f = c.createBiquadFilter();
    f.type = opts.type;
    f.Q.value = opts.q ?? 1;
    f.frequency.setValueAtTime(opts.f0, t);
    if (opts.f1) f.frequency.exponentialRampToValueAtTime(opts.f1, t + opts.attack + opts.decay);
    const g = c.createGain();
    this.env(g, t, opts.peak, opts.attack, opts.decay);
    src.connect(f).connect(g).connect(this.master!);
    src.start(t, Math.random());
    src.stop(t + opts.attack + opts.decay + 0.05);
  }

  private tone(opts: { type: OscillatorType; f0: number; f1?: number; peak: number; attack: number; decay: number; delay?: number }) {
    const c = this.ctx!, t = c.currentTime + (opts.delay ?? 0);
    const o = c.createOscillator();
    o.type = opts.type;
    o.frequency.setValueAtTime(opts.f0, t);
    if (opts.f1) o.frequency.exponentialRampToValueAtTime(opts.f1, t + opts.attack + opts.decay);
    const g = c.createGain();
    this.env(g, t, opts.peak, opts.attack, opts.decay);
    o.connect(g).connect(this.master!);
    o.start(t);
    o.stop(t + opts.attack + opts.decay + 0.05);
  }

  // ---------------------------------------------------------------- game sounds
  /** Weapon swung fast. speed 0..1 */
  swing(speed: number) {
    if (!this.ok("swing", 180)) return;
    this.noise({ type: "bandpass", f0: 500 + 500 * speed, f1: 2600 + 1600 * speed, q: 2, peak: 0.25 + 0.3 * speed, attack: 0.04, decay: 0.18 });
  }

  /** Weapon hits a body. k 0..1 */
  hit(k: number) {
    if (!this.ok("hit", 60)) return;
    this.tone({ type: "sine", f0: 160, f1: 45, peak: 0.6 + 0.3 * k, attack: 0.005, decay: 0.22 });
    this.noise({ type: "lowpass", f0: 1800, f1: 300, peak: 0.45 + 0.3 * k, attack: 0.003, decay: 0.12 });
    this.noise({ type: "bandpass", f0: 900, q: 3, peak: 0.25, attack: 0.01, decay: 0.2, delay: 0.03 });
  }

  /** Two weapons clash. */
  clash() {
    if (!this.ok("clash", 80)) return;
    for (const [f, p] of [[2350, 0.22], [3170, 0.16], [4420, 0.12], [5890, 0.08]] as const)
      this.tone({ type: "triangle", f0: f * (0.97 + Math.random() * 0.06), peak: p, attack: 0.002, decay: 0.55 });
    this.noise({ type: "highpass", f0: 3000, peak: 0.3, attack: 0.001, decay: 0.05 });
  }

  /** Strings snap. */
  stringCut() {
    if (!this.ok("cut", 120)) return;
    this.tone({ type: "sawtooth", f0: 520, f1: 120, peak: 0.12, attack: 0.002, decay: 0.25 });
    this.noise({ type: "highpass", f0: 2500, peak: 0.15, attack: 0.001, decay: 0.04 });
  }

  /** Strings re-attach. */
  stringAttach() {
    if (!this.ok("attach", 200)) return;
    this.tone({ type: "triangle", f0: 660, peak: 0.12, attack: 0.005, decay: 0.3 });
    this.tone({ type: "triangle", f0: 990, peak: 0.08, attack: 0.005, decay: 0.3, delay: 0.08 });
  }

  /** Ultimate cast: rising icy shimmer. */
  ultCast() {
    if (!this.ok("cast", 300)) return;
    this.noise({ type: "bandpass", f0: 400, f1: 5000, q: 4, peak: 0.35, attack: 0.25, decay: 0.35 });
    [784, 988, 1175, 1568].forEach((f, i) =>
      this.tone({ type: "sine", f0: f, peak: 0.12, attack: 0.01, decay: 0.6, delay: i * 0.07 }));
  }

  /** Giant sword falling: descending whistle. */
  giantFall(seconds: number) {
    if (!this.ok("fall", 300)) return;
    this.tone({ type: "sine", f0: 1800, f1: 260, peak: 0.12, attack: 0.05, decay: seconds });
    this.noise({ type: "bandpass", f0: 300, f1: 2400, q: 1.5, peak: 0.25, attack: seconds * 0.9, decay: 0.1 });
  }

  /** Giant sword impact: boom + ice shatter. */
  giantImpact() {
    if (!this.ok("impact", 200)) return;
    this.tone({ type: "sine", f0: 90, f1: 30, peak: 0.9, attack: 0.005, decay: 0.9 });
    this.noise({ type: "lowpass", f0: 900, f1: 120, peak: 0.7, attack: 0.005, decay: 0.7 });
    for (let i = 0; i < 9; i++)
      this.tone({ type: "triangle", f0: 2500 + Math.random() * 3500, peak: 0.07, attack: 0.002, decay: 0.15, delay: 0.04 + Math.random() * 0.35 });
  }

  /** One small sword of the rain lands. */
  rainSword() {
    if (!this.ok("rain", 70)) return;
    this.tone({ type: "triangle", f0: 1800 + Math.random() * 1500, peak: 0.06, attack: 0.002, decay: 0.12 });
    this.noise({ type: "highpass", f0: 2500, peak: 0.07, attack: 0.002, decay: 0.05 });
  }

  /** Gust of wind. */
  gust(seconds: number) {
    if (!this.ok("gust", 2000)) return;
    this.noise({ type: "bandpass", f0: 250, f1: 900, q: 0.8, peak: 0.22, attack: seconds * 0.45, decay: seconds * 0.55 });
  }

  /** Random campfire crackle, call every frame. */
  crackle(dt: number) {
    if (Math.random() > dt * 6 || !this.ok("crackle", 40)) return;
    this.noise({ type: "highpass", f0: 1500 + Math.random() * 2500, peak: 0.03 + Math.random() * 0.04, attack: 0.001, decay: 0.02 + Math.random() * 0.03 });
  }
}
