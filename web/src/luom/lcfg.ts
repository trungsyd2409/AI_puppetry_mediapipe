// Tunable numbers for the Luom runner. Units: stage pixels (1600 x 900 art), seconds.
export const L = {
  scale: 0.85,            // stage px per rig design unit
  x: 420,                 // stage x of Luom's hips

  // body height on the strings (marionette): the strings carry the body, gravity pulls it down.
  // Lower the hand -> he crouches (duck). Raise it -> he is lifted. Flick it up -> he flies up (jump).
  gravity: 2200,
  maxRise: 1250,          // px/s cap of the upward speed a flick can give (~280 px jump)
  flickMin: 420,          // px/s the strings must rise to count as a flick
  flickBoost: 1.6,        // the flick speed is multiplied by this
  deadZone: 24,           // px the hand may drift down before he starts to crouch
  keyJump: 1150,          // px/s for the Space key (mouse / keyboard test)

  // run
  speed: [300, 470] as [number, number],   // ground scroll px/s, easy -> hard
  rampTime: 120,          // s of play until the hardest setting
  stepHz: 1.75,           // running steps per second at the start speed
  pxPerMetre: 100,

  // hazards
  gapPx: [[760, 1150], [460, 760]] as [number, number][],   // ground distance between obstacles, easy -> hard
  minGap: 1.3,            // s between two hazards reaching Luom
  planeEvery: [[8, 12], [4.5, 7]] as [number, number][],
  bulletEvery: [[7, 11], [3.8, 6]] as [number, number][],
  bulletSpeed: 650,       // px/s on top of the ground speed
  bulletWarn: 0.9,        // s of muzzle flash at the right edge before a burst
  planeSpeed: 260,
  bombGravity: 900,
  blastRadius: 115,
  letterChance: 0.45,
  obstacleScale: 1.0,

  hp: 10,
  tripTime: 1.1,          // s on the ground after a hit, then he gets up
  invuln: 1.9,            // s blinking after a hit
  letterPoints: 10,

  timeOfDay: 150,         // s of play from morning to dusk (it stays dusk after that)
  deathHold: 2.2,
  curtainClose: 0.9,
  curtainOpen: 1.2,
  startHold: 1.0,
  readyHold: 0.8,         // s with the strings attached before the run starts
  fixedDt: 1 / 120,
};
