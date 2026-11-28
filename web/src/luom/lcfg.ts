// Tunable numbers for the Luom runner. Units: stage pixels (1600 x 900 art), seconds.
export const L = {
  scale: 0.85,            // stage px per rig design unit
  x: 420,                 // stage x of Luom's hips

  // jump: a quick upward flick of the hand. Holding the hand up does nothing more.
  // He must land before he can jump again.
  gravity: 2300,
  flickSpeed: 430,        // stage px/s the hand must rise to start a jump
  flickRearm: 180,        // the hand must slow below this (on the ground) before the next jump
  jumpMin: 200,           // px the feet rise for the smallest flick (clears every obstacle)
  maxJumpFrac: 0.6,       // highest jump = 3/5 of the play area height (path to the top of the stage)
  flickGain: 0.2,         // extra height per px/s of flick speed above flickSpeed
  boostWindow: 0.12,      // s after take-off during which a faster flick still adds height
  keyJump: 260,           // px for the Space key (mouse / keyboard test)

  // skipping run (chay nhay chan sao): one skip per half cycle, a little hop on each
  skipHz: 2.3,            // skips per second at the start speed
  skipHop: 32,            // px the body hops on each skip

  speed: [300, 470] as [number, number],   // ground scroll px/s, easy -> hard
  rampTime: 120,          // s of play until the hardest setting
  pxPerMetre: 100,

  // hazards (all are jumped over)
  gapPx: [[760, 1150], [480, 780]] as [number, number][],   // ground distance between obstacles, easy -> hard
  minGap: 1.35,           // s between two hazards reaching Luom (one jump each)
  planeEvery: [[8, 12], [4.5, 7]] as [number, number][],
  bulletEvery: [[7, 11], [4, 6.5]] as [number, number][],
  bulletSpeed: 600,       // px/s on top of the ground speed
  bulletWarn: 1.0,        // s of muzzle flash at the right edge before a burst
  bulletHeight: 60,       // px above the path: low, so he jumps over them
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
};
