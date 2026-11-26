"""Build assets/preview.html: both puppets on the stage, joint sliders, sway test.
Rig data is inlined so the page also works when opened straight from disk."""
import json, os
ROOT = os.path.dirname(os.path.abspath(__file__))
PUPPETS = [("teu", "Chú Tễu", 670), ("co_gai", "Cô gái áo dài", 930)]  # folder, label, stage x

rigs = []
for folder, label, x in PUPPETS:
    rig = json.load(open(os.path.join(ROOT, "puppet", folder, "rig.json")))
    for p in rig["parts"]:
        p["png"] = f"puppet/{folder}/{p['png']}"
    rigs.append({"label": label, "x": x, "rig": rig})
stage = json.load(open(os.path.join(ROOT, "background", "stage.json")))
for k in stage["layers"]:
    stage["layers"][k] = "background/" + stage["layers"][k]

html = r"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Puppet rig preview</title>
<style>
  :root { --ink:#2a140a; --panel:#f7ecd2; }
  * { box-sizing:border-box; }
  body { margin:0; font:14px/1.4 system-ui,sans-serif; color:var(--ink); background:#24140b;
         display:flex; flex-wrap:wrap; gap:16px; padding:16px; justify-content:center; align-items:flex-start; }
  canvas { width:min(1000px,100%); height:auto; border-radius:8px; background:#e9d6ad; }
  .panel { background:var(--panel); border-radius:8px; padding:12px 14px; width:320px; max-width:100%; }
  h1 { font-size:16px; margin:0 0 8px; }
  label { display:grid; grid-template-columns:96px 1fr 44px; align-items:center; gap:6px; margin:4px 0; }
  .row { display:flex; gap:8px; flex-wrap:wrap; margin:8px 0; }
  button, select { border:1px solid var(--ink); background:#fff8e6; border-radius:6px; padding:6px 10px; cursor:pointer; font:inherit; }
  button.on { background:var(--ink); color:#fff8e6; }
</style></head>
<body>
<canvas id="cv" width="1600" height="900"></canvas>
<div class="panel">
  <h1>Test khớp rối</h1>
  <div class="row"><select id="who"></select></div>
  <div class="row">
    <button id="bSway">Lắc lư</button>
    <button id="bPivot">Hiện pivot</button>
    <button id="bStr" class="on">Hiện dây</button>
    <button id="bBg" class="on">Nền</button>
    <button id="bReset">Reset</button>
  </div>
  <div id="sliders"></div>
</div>
<script>
const PUPPETS = __PUPPETS__, STAGE = __STAGE__;
const cv = document.getElementById('cv'), ctx = cv.getContext('2d');
const load = src => new Promise(r => { const i = new Image(); i.onload = () => r(i); i.onerror = () => r(null); i.src = src; });
let bgImg = null, fgImg = null, showPivot = false, showStr = true, showBg = true, sway = false, t0 = 0, sel = 0;

for (const P of PUPPETS) {
  P.parts = Object.fromEntries(P.rig.parts.map(p => [p.id, {...p, angle: 0}]));
  const top = Math.min(...P.rig.parts.map(p => p.origin[1]));
  P.k = STAGE.puppetHeight / (P.rig.feetY - top);
}

function worldMatrix(P, p) {
  let m;
  if (p.parent) { const q = P.parts[p.parent]; m = worldMatrix(P, q).translate(p.origin[0] - q.origin[0], p.origin[1] - q.origin[1]); }
  else m = new DOMMatrix().translate(p.origin[0], p.origin[1]);
  return m.translate(p.pivot[0], p.pivot[1]).rotate(p.angle).translate(-p.pivot[0], -p.pivot[1]);
}
function base(P) {  // design space -> stage pixels, feet on the floor
  return new DOMMatrix().translate(P.x, STAGE.floorY).scale(P.k).translate(-P.rig.canvas[0] / 2, -P.rig.feetY);
}

function draw() {
  ctx.setTransform(1,0,0,1,0,0);
  ctx.clearRect(0, 0, cv.width, cv.height);
  if (showBg && bgImg) ctx.drawImage(bgImg, 0, 0);
  for (const P of PUPPETS) {
    const B = base(P);
    if (showStr) for (const s of P.rig.strings) {
      const pt = B.multiply(worldMatrix(P, P.parts[s.part])).transformPoint(new DOMPoint(...s.anchor));
      ctx.setTransform(1,0,0,1,0,0);
      ctx.strokeStyle = 'rgba(40,20,10,.65)'; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.moveTo(pt.x, 0); ctx.lineTo(pt.x, pt.y); ctx.stroke();
    }
    for (const p of Object.values(P.parts).sort((a, b) => a.z - b.z)) {
      ctx.setTransform(B.multiply(worldMatrix(P, p)));
      if (p.img) ctx.drawImage(p.img, 0, 0, p.size[0], p.size[1]);
    }
    if (showPivot) for (const p of Object.values(P.parts)) {
      const pt = B.multiply(worldMatrix(P, p)).transformPoint(new DOMPoint(...p.pivot));
      ctx.setTransform(1,0,0,1,0,0);
      ctx.strokeStyle = '#18c08a'; ctx.lineWidth = 2.5;
      ctx.beginPath(); ctx.arc(pt.x, pt.y, 6, 0, 7); ctx.stroke();
    }
  }
  ctx.setTransform(1,0,0,1,0,0);
  if (showBg && fgImg) ctx.drawImage(fgImg, 0, 0);
}

const who = document.getElementById('who'), box = document.getElementById('sliders');
PUPPETS.forEach((P, i) => who.add(new Option(P.label, i)));
function buildSliders() {
  box.innerHTML = '';
  for (const p of Object.values(PUPPETS[sel].parts)) {
    if (!p.limitDeg) continue;
    const l = document.createElement('label');
    l.innerHTML = `<span>${p.id}</span><input type=range min=${p.limitDeg[0]} max=${p.limitDeg[1]} value=${p.angle} step=1><span>${Math.round(p.angle)}°</span>`;
    const [, inp, val] = l.children;
    inp.oninput = () => { p.angle = +inp.value; val.textContent = inp.value + '°'; draw(); };
    p.ui = [inp, val];
    box.appendChild(l);
  }
}
who.onchange = () => { sel = +who.value; buildSliders(); };
function setAngle(P, id, a) {
  const p = P.parts[id]; if (!p) return;
  p.angle = Math.max(p.limitDeg[0], Math.min(p.limitDeg[1], a));
  if (p.ui && P === PUPPETS[sel]) { p.ui[0].value = p.angle; p.ui[1].textContent = Math.round(p.angle) + '°'; }
}
function loop() {
  if (!sway) return;
  const t = (performance.now() - t0) / 1000;
  PUPPETS.forEach((P, i) => {
    const ph = i * 1.3;
    setAngle(P, 'head', 15 * Math.sin(t * 2 + ph));
    setAngle(P, 'hair', -10 * Math.sin(t * 2 + ph - 0.6));
    setAngle(P, 'upper_arm_L', -70 + 50 * Math.sin(t * 3 + ph));
    setAngle(P, 'forearm_L', -60 + 40 * Math.sin(t * 3 + ph + 1));
    setAngle(P, 'upper_arm_R', 70 - 50 * Math.sin(t * 3 + ph + 2));
    setAngle(P, 'forearm_R', 60 - 40 * Math.sin(t * 3 + ph + 3));
    setAngle(P, 'thigh_L', 20 * Math.sin(t * 3 + ph));
    setAngle(P, 'shin_L', 30 + 30 * Math.sin(t * 3 + ph + 1));
    setAngle(P, 'thigh_R', 20 * Math.sin(t * 3 + ph + Math.PI));
    setAngle(P, 'shin_R', -30 - 30 * Math.sin(t * 3 + ph + 1));
    setAngle(P, 'flap_front', 8 * Math.sin(t * 3 + ph - 0.8));
    setAngle(P, 'flap_back', 6 * Math.sin(t * 3 + ph - 1.2));
  });
  draw(); requestAnimationFrame(loop);
}
const tog = (id, fn) => document.getElementById(id).onclick = e => { e.target.classList.toggle('on', fn()); draw(); };
tog('bSway', () => { sway = !sway; if (sway) { t0 = performance.now(); loop(); } return sway; });
tog('bPivot', () => (showPivot = !showPivot));
tog('bStr', () => (showStr = !showStr));
tog('bBg', () => (showBg = !showBg));
document.getElementById('bReset').onclick = () => { for (const P of PUPPETS) for (const p of Object.values(P.parts)) if (p.limitDeg) setAngle(P, p.id, 0); draw(); };
window.__pose = (i, o) => { for (const k in o) setAngle(PUPPETS[i], k, o[k]); draw(); };

(async () => {
  [bgImg, fgImg] = await Promise.all([load(STAGE.layers.bg), load(STAGE.layers.fg)]);
  await Promise.all(PUPPETS.flatMap(P => Object.values(P.parts).map(async p => { p.img = await load(p.png); })));
  buildSliders(); draw(); window.__ready = true;
})();
</script>
</body></html>"""
html = html.replace("__PUPPETS__", json.dumps(rigs)).replace("__STAGE__", json.dumps(stage))
open(os.path.join(ROOT, "preview.html"), "w").write(html)
print("assets/preview.html written")
