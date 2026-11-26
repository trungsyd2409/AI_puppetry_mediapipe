// All tunable numbers in one place. Physics/stage units are pixels of the 1600 x 900 stage art;
// the screen shows that stage scaled into the bottom half of a square canvas.
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

  // square screen: camera on top, stage below
  view: {
    size: 1200,          // canvas is size x size
    split: 600,          // camera height; the stage fills the rest
    stageCropY: 90,      // first stage row shown (the 1600x900 stage is scaled to the canvas width)
  },
  puppetHeight: 470,     // stage px from head to feet
  dropPx: 600,           // head anchor hangs this far below the palm (strings run from the camera down)
  fingerGain: 1.3,       // how much a finger moving relative to the palm moves its limb
  targetMinY: 120,       // strings never lift the puppet above this stage row
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
