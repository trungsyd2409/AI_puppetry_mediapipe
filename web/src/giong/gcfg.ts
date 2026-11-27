// Tunable numbers for the Giong game. Units: stage pixels (1600 x 900 art), seconds.
export const G = {
  puppetScale: 0.8,        // stage px per rig design unit
  horseX: 430,             // stage x of the rig's reference point (design x = 330, between the hooves)
  runSpeed: 420,           // ground scroll speed while galloping (px/s)
  gallopHz: 1.45,          // gallop cycles per second at full speed

  // ropes: fixed length, set when the strings reach the puppet, never stretch.
  // Bamboo strings are always straight (they pull and push). Leg strings only pull, so they may sag.
  rope: { width: 5, core: 2.4 },
  loseAfter: 0.25,         // s without the hand -> strings cut
  attachFrames: 5,         // detections in a row before strings grow again
  growTime: 0.35,

  // horse legs and rearing
  liftFull: 80,            // design units the hoof must rise for lift = 1
  rearOn: [0.3, 0.7],      // min(front lifts) range mapped to rear 0..1
  rearAngle: 0.5,          // rad the body tips back at full rear
  stopRear: [0.35, 0.6],   // rear range where the gallop fades out

  // bamboo (position based dynamics)
  bamboo: { gravity: 500, damping: 0.965, holdFree: 0.12, holdAttached: 0.02, iters: 8, maxTilt: 1.35 },  // maxTilt rad (~77°): tip stays right of the base

  // shells
  shell: {
    gravity: 520, radius: 24, scale: 1.0,
    interval: [2.6, 1.05],   // s between shots, easy -> hard
    flight: [1.9, 1.15],     // s flight time, easy -> hard
    rampTime: 100,           // s of play until the hardest setting
    low: { x: 560, y: 640 }, // aim points: chest / front legs (stomp) and the boy's head (bamboo)
    high: { x: 455, y: 420 },
  },
  lives: 3,
  blockScore: 50,
  pxPerPoint: 40,          // distance score: 1 point per 40 px galloped

  fallTime: 3,             // s lying on the ground before the curtain closes
  curtainClose: 0.9,
  curtainOpen: 1.2,
  startHold: 1.0,          // s a hand must stay attached on the title / game-over curtain to start
  bgDarken: 0.05,          // background drawn this much darker so the rider and the shells stand out
  fixedDt: 1 / 120,
};
