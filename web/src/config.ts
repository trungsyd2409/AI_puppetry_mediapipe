// All tunable numbers in one place. Physics/stage units are pixels of the 1600 x 900 stage art;
// the screen shows that stage scaled into the bottom half of a square canvas.
export interface SceneCfg { title: string; background: string; puppets: string[]; fx: "snow" | "thuydinh"; accent: string }

export const SCENES: Record<string, SceneCfg> = {
  // default: snow-mountain camp, winter warrior (left hand) and Streltsy guard (right hand)
  snow: { title: "Chiến binh tuyết", background: "background_snow", puppets: ["chien_binh_tuyet", "ve_binh_streltsy"], fx: "snow", accent: "#BFD7F2" },
  // the water-puppet pavilion with Chu Teu and the ao dai girl: open with ?scene=thuydinh
  thuydinh: { title: "Rối Thủy Đình", background: "background", puppets: ["teu", "co_gai"], fx: "thuydinh", accent: "#E2B44A" },
};
export const DEFAULT_SCENE = "snow";

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
    // "fixed": every rope has its own fixed length (fractions of the screen height below)
    // "slack": head rope = lengths.middle; the other ropes are measured so the puppet hangs in its
    //          rest pose, then given extra slack so the limbs move freely
    mode: "slack" as "fixed" | "slack",
    lengths: { middle: 0.3, indexRing: 0.25, thumbPinky: 0.2 },
    slack: { indexRing: 0.03, thumbPinky: 0.06 },
    omega: 16,             // stiffness of the head rope (rad/s); higher = less stretch
    limbOmega: 13,         // stiffness of the hand/knee ropes
    zeta: 0.6,             // damping along the rope
    maxAccel: 220,         // m/s^2 clamp so fast hands do not explode the ragdoll
    attachedDamping: 1.1,  // air drag while hanging, stops endless pendulum swinging
  },
  upright: { kp: 25, kd: 6, radius: 0.7 },
  // MediaPipe labels hands as if the image were mirrored; our webcam frames are not, so the
  // label is flipped once. If left/right still come out swapped on your webcam, set this to true.
  swapHandedness: false,

  // living background
  ambience: {
    fishEvery: [4, 9],       // s between carp jumps
    birdsEvery: [7, 15],     // s between flocks of cranes
    gustEvery: [9, 16],      // s between gusts of wind
    gustDuration: 4,         // s
    windAccel: 3,            // m/s^2 pushed on the puppets at the peak of a gust
  },

  // weapon fights between puppets
  combat: {
    weapons: ["spear", "saber"],   // rig part ids that count as weapons
    minHitSpeed: 2.0,              // m/s relative speed for a touch to count as a hit
    fullHitSpeed: 9,               // m/s for the strongest hit
    cooldown: 0.35,                // s between two hits of the same attacker on the same target
    knockback: { min: 3, max: 9 }, // m/s given to the target
    staggerTime: 0.45,             // s the target's strings stay slack after a hit
    staggerStrength: 0.15,         // string strength while staggered
    shakePx: 10,                   // screen shake at the strongest hit
  },

  // ultimates
  ult: {
    gestureWindow: 0.35,       // s: index up -> index down must happen within this time
    angleTolerance: 45,        // degrees from straight up / down that still count
    lockAfter: 0.3,            // s the strings stay locked after the L pose is seen
    cooldown: 10,              // s
    kinds: { chien_binh_tuyet: "giantSword", ve_binh_streltsy: "swordRain" } as Record<string, "giantSword" | "swordRain">,
    giantSword: { fallTime: 0.7, detach: 1, hitWidth: 34, knockback: 7 },
    swordRain: { duration: 4, perSecond: 14, spread: 300, knockback: { min: 6, max: 11 } },
    testKeys: ["u", "i"],      // keyboard: cast for puppet 1 / puppet 2 (mouse testing)
  },

  // weapon trails and ice aura
  weaponFx: {
    bladeFrom: { spear: 0.55, saber: 0.12 } as Record<string, number>,   // where the glowing part starts
    trailTime: 0.16,           // s of history in the trail
    trailMinSpeed: 250,        // px/s before a trail shows
    swingSoundSpeed: 900,      // px/s tip speed that plays a whoosh
  },

  sound: { enabled: true, volume: 0.6 },

  // landmark smoothing (One Euro filter, stage pixels)
  euro: { minCutoff: 1.4, beta: 0.01, dCutoff: 1.0 },
};

export type Pt = { x: number; y: number };
