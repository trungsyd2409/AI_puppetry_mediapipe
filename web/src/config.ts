// All tunable numbers in one place. Stage units are pixels of the 1600 x 900 stage.
export const CFG = {
  // physics
  ppm: 100,              // stage pixels per physics metre
  gravity: 30,           // m/s^2 (higher than real so the big puppets fall snappily)
  fixedDt: 1 / 120,
  maxSubSteps: 6,
  jointFriction: 0.6,    // joint friction torque per kg of the child part (N*m/kg)
  linearDamping: 0.15,
  angularDamping: 1.2,
  wallMargin: 40,

  // camera (normalised, already mirrored) -> stage control area
  camMap: { x0: 0.1, x1: 0.9, y0: 0.08, y1: 0.75, stageX0: 200, stageX1: 1400, stageY0: 30, stageY1: 470 },
  dropPx: 110,           // head anchor hangs this far below the palm
  fingerGain: 1.7,       // how much a finger moving relative to the palm moves its limb
  maxDetectHz: 30,

  // hand presence state machine
  loseAfter: 0.25,       // s without a hand -> strings cut, ragdoll
  attachFrames: 5,       // consecutive detections before strings reconnect
  growTime: 0.35,        // s: strings grow from fingertips to the puppet
  standTime: 0.9,        // s: string strength ramps 0 -> 1, puppet stands up

  // string springs
  headSpring: { omega: 9, zeta: 0.9 },
  limbSpring: { omega: 8, zeta: 0.75 },
  maxAccel: 150,         // m/s^2 clamp so fast hands do not explode the ragdoll
  upright: { kp: 30, kd: 7, radius: 0.7 },

  // landmark smoothing (One Euro filter, stage pixels)
  euro: { minCutoff: 1.4, beta: 0.01, dCutoff: 1.0 },
};

export type Pt = { x: number; y: number };
