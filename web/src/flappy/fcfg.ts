// Tunable numbers for Flappy chim lac. Units: stage pixels (1600 x 900 art), seconds.
export const F = {
  birdScale: 0.46,        // stage px per rig design unit
  birdX: 420,             // stage x of the bird (design point 330, 210)
  hoverY: 430,            // where the bird waits before the strings attach

  // strings: fixed length (set when they reach the wings), always straight
  wingTolerance: 8,       // px of rope error allowed so the wings can keep a small natural flap
  maxClimb: 1400,         // px/s: how fast the bird may follow a sudden hand move
  flapHz: 1.6,

  gravity: 1500,          // falling when the strings are cut
  // bamboo columns (original Flappy Bird rules: fixed gap and speed, 1 point per column)
  speed: 210,
  spacing: 430,
  gap: 280,
  gapRange: [270, 620] as [number, number],   // stage y range of the gap centre
  colScale: 0.9,
  firstColumnX: 1500,

  bgDarken: 0.2,          // background drawn 20% darker so the bird and the bamboo stand out
  deathHold: 1.4,         // s after the crash before the curtain closes
  curtainClose: 0.9,
  curtainOpen: 1.2,
  startHold: 1.0,
  fixedDt: 1 / 120,
};
