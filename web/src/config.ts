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
  maxDetectHz: 30,

  // hand presence state machine
  loseAfter: 0.25,       // s without a hand -> strings cut, ragdoll
  attachFrames: 5,       // consecutive detections before strings reconnect
  growTime: 0.35,        // s: strings grow from fingertips to the puppet
  standTime: 0.9,        // s: string strength ramps 0 -> 1, puppet stands up

  // strings = ropes of fixed length with a little stretch
  rope: {
    lengthOfScreen: 0.3,   // head string length as a fraction of the screen height
    omega: 16,             // stiffness of the head rope (rad/s); higher = less stretch
    limbOmega: 13,         // stiffness of the hand/knee ropes
    zeta: 0.6,             // damping along the rope
    maxAccel: 220,         // m/s^2 clamp so fast hands do not explode the ragdoll
    attachedDamping: 1.1,  // air drag while hanging, stops endless pendulum swinging
  },
  upright: { kp: 25, kd: 6, radius: 0.7 },

  // living background
  ambience: {
    fishEvery: [4, 9],       // s between carp jumps
    birdsEvery: [7, 15],     // s between flocks of cranes
    gustEvery: [9, 16],      // s between gusts of wind
    gustDuration: 4,         // s
    windAccel: 3,            // m/s^2 pushed on the puppets at the peak of a gust
  },

  // landmark smoothing (One Euro filter, stage pixels)
  euro: { minCutoff: 1.4, beta: 0.01, dCutoff: 1.0 },
};

export type Pt = { x: number; y: number };
