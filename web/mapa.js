/* Ardan v 3D, etapa 1 (prototyp). three.js z CDN přes importmap (mapa.html), bez bundleru.
   Geometrie z web/map.json, stav světa po kolech z history/summary.json. Popis v web/MAPA3D.md. */
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { CSS2DRenderer, CSS2DObject } from "three/addons/renderers/CSS2DRenderer.js";
import { Line2 } from "three/addons/lines/Line2.js";
import { LineMaterial } from "three/addons/lines/LineMaterial.js";
import { LineGeometry } from "three/addons/lines/LineGeometry.js";

const ZAKLAD = "..";
/* barvy: značka Kája Industries (kaja.css) a sémantické barvy dnešní mapy; Kalvera není Ion Blue */
const B = {
  hull: "#F3F4F6", silver: "#C8CDD4", steel: "#6E7680", graphite: "#22252A", ion: "#2F80D1",
  more: "#E3E8EE", zeme: "#F7F8FA", vysocina: "#DDE1E6",
  A: "#2B4A8C", B: "#BA544A", Atm: "#1A2D57", Btm: "#6E2A24", unie: "#6F9E73", unieHrana: "#3F7D45", zlata: "#B8902A"
};
const VYSKA = { zeme: 2, uzemi: 1, vysocina: 3, jezero: 1, mesto: 3 };
const SIRKA = 1000, HLOUBKA = 700, OX = SIRKA / 2, OZ = HLOUBKA / 2;
const HORNI = VYSKA.zeme + VYSKA.uzemi;   // horní plocha území
const HRACI = { A: "Kalverská federace", B: "Lidová republika Ostrogard" };
const KRATKE = { A: "Kalvera", B: "Ostrogard" };
const FAZE = {
  pre: "Před objevem", displacement: "Šok, vytěsnění", boom: "Rozmach", euphoria: "Euforie",
  overtrading: "Nadměrné obchodování", distress: "Finanční tíseň", panic: "Panika",
  crash: "Krach", depression: "Deprese", recovery: "Zotavení"
};
const STATUS = {
  independent: "nezávislý", sphere_A: "sféra Kalvery", sphere_B: "sféra Ostrogardu",
  occupied_A: "okupován Kalverou", occupied_B: "okupován Ostrogardem", union: "člen Unie", candidate: "kandidát Unie"
};
const KLIDNE = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const MOBIL = () => window.matchMedia("(max-width: 599px)").matches;
const deg = (d) => d * Math.PI / 180;
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const cis = (n, d = 1) => (n == null || isNaN(Number(n))) ? "–" : Number(n).toLocaleString("cs-CZ", { maximumFractionDigits: d });

async function nacti(cesta) {
  const r = await fetch(`${ZAKLAD}/${cesta}`, { cache: "no-cache" });
  if (!r.ok) throw new Error(`${cesta}: ${r.status}`);
  return r.json();
}

/* ------------------------------ síť hvězd v okrajích ------------------------------ */
function plexusOkraj(svg) {
  const W = 1600, H = 1000, N = 130;
  let seme = 20261014;
  const nahoda = () => { seme = (seme * 1103515245 + 12345) % 2147483648; return seme / 2147483648; };
  const body = Array.from({ length: N }, () => [nahoda() * W, nahoda() * H]);
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.setAttribute("preserveAspectRatio", "xMidYMid slice");
  const ns = "http://www.w3.org/2000/svg";
  const stupen = new Array(N).fill(0);
  for (let i = 0; i < N; i++) {
    const blizke = body.map((b, j) => [j, Math.hypot(b[0] - body[i][0], b[1] - body[i][1])])
      .filter(([j]) => j !== i).sort((a, b) => a[1] - b[1]).slice(0, 3);
    for (const [j, d] of blizke) {
      if (stupen[i] >= 3 || stupen[j] >= 3 || d > 170 || j < i) continue;
      stupen[i]++; stupen[j]++;
      const l = document.createElementNS(ns, "line");
      l.setAttribute("x1", body[i][0].toFixed(1)); l.setAttribute("y1", body[i][1].toFixed(1));
      l.setAttribute("x2", body[j][0].toFixed(1)); l.setAttribute("y2", body[j][1].toFixed(1));
      l.setAttribute("opacity", (0.15 + nahoda() * 0.25).toFixed(2));
      svg.appendChild(l);
    }
  }
  for (const [x, y] of body) {
    const c = document.createElementNS(ns, "circle");
    c.setAttribute("cx", x.toFixed(1)); c.setAttribute("cy", y.toFixed(1)); c.setAttribute("r", (0.9 + nahoda()).toFixed(2));
    c.setAttribute("opacity", (0.2 + nahoda() * 0.2).toFixed(2));
    svg.appendChild(c);
  }
}

/* ------------------------------ geometrie ------------------------------ */
// mapa: x vpravo, y dolů; scéna: x vpravo, z k divákovi (jih), y nahoru. Sever je vzadu, tedy nahoře.
const vScene = (x, y) => [x - OX, y - OZ];
function tvar(kruhy) {
  const s = new THREE.Shape(kruhy[0].map(([x, y]) => new THREE.Vector2(x - OX, -(y - OZ))));
  for (const d of kruhy.slice(1)) s.holes.push(new THREE.Path(d.map(([x, y]) => new THREE.Vector2(x - OX, -(y - OZ)))));
  return s;
}
function deska(kruhy, zaklad, vyska) {
  const g = new THREE.ExtrudeGeometry(tvar(kruhy), { depth: vyska, bevelEnabled: false, curveSegments: 1 });
  g.rotateX(-Math.PI / 2);
  g.translate(0, zaklad, 0);
  return g;
}
const material = (barva) => new THREE.MeshStandardMaterial({ color: barva, roughness: 0.92, metalness: 0 });

function obrys(kruh, y, barva, sirka, kryti) {
  const body = [];
  for (const [x, z] of [...kruh, kruh[0]]) { const [sx, sz] = vScene(x, z); body.push(sx, y, sz); }
  const g = new LineGeometry();
  g.setPositions(body);
  const m = new LineMaterial({ color: barva, linewidth: sirka, transparent: kryti < 1, opacity: kryti, worldUnits: false });
  return new Line2(g, m);
}

/* ------------------------------ barvy vlivu ------------------------------ */
const C = (h) => new THREE.Color(h);
const SILVER40 = C(B.zeme).lerp(C(B.silver), 0.4);
const MAX_VLIV = 20;   // součet vlivu, při kterém je barva plná (práh sféry je 10 u jedné velmoci)

function vzhled(id, st, pakty, kandidati) {
  // vrací výplň a hranu území pro dané kolo
  const v = { fill: SILVER40.clone(), hrana: C(B.graphite), sirka: 1, kryti: 0.6 };
  if (id === "A" || id === "B") {
    v.fill = C(B[id]); v.hrana = C(B[id + "tm"]); v.sirka = 2; v.kryti = 1;
    return v;
  }
  const s = st.status || "independent";
  const infA = Math.max(0, (st.influence || {}).A || 0), infB = Math.max(0, (st.influence || {}).B || 0);
  if (s === "union") v.fill = C(B.unie);
  else if (s === "occupied_A" || s === "occupied_B") v.fill = C(B[s.slice(-1) + "tm"]);
  else if (s === "sphere_A" || s === "sphere_B") v.fill = C(B[s.slice(-1)]);
  else if (infA + infB > 0) {
    const odstin = C(B.A).lerp(C(B.B), infB / (infA + infB));
    v.fill = SILVER40.clone().lerp(odstin, Math.min(1, (infA + infB) / MAX_VLIV));
  }
  // hrany: sféra > pakt > kandidát > padlá říše
  if (st.kind === "fallen") { v.hrana = C(B.zlata); v.sirka = 2; v.kryti = 1; }
  if (s === "candidate" || kandidati.has(id)) { v.hrana = C(B.unieHrana); v.sirka = 2; v.kryti = 1; }
  if (pakty[id]) { v.hrana = C(B[pakty[id]] || B.graphite); v.sirka = 2; v.kryti = 1; }
  if (s === "sphere_A" || s === "sphere_B") { v.hrana = C(B[s.slice(-1) + "tm"]); v.sirka = 2; v.kryti = 1; }
  return v;
}

/* ------------------------------ scéna ------------------------------ */
const svet = { mapa: null, souhrn: [], jmena: {}, kolo: 0, uzemi: new Map(), mesta: new Map(), vybrany: null, hover: null,
               D0: 1000, prehravani: null, animace: null, popiskyMale: [] };
let renderer, labeler, scene, camera, controls;
let cekaRender = false;
const vykresli = () => {
  if (cekaRender) return;
  cekaRender = true;
  requestAnimationFrame(() => { cekaRender = false; renderer.render(scene, camera); labeler.render(scene, camera); });
};

function maWebGL() {
  try { const c = document.createElement("canvas"); return Boolean(c.getContext("webgl2") || c.getContext("webgl")); }
  catch (e) { return false; }
}

function postavScenu() {
  const M = svet.mapa;
  scene = new THREE.Scene();
  // moře: rovina #E3E8EE, k okrajům plynule průhledná (barva ve vrcholech, žádná textura), za ní Hull White
  const mg = new THREE.PlaneGeometry(SIRKA * 2.4, HLOUBKA * 2.6, 48, 48);
  const pozice = mg.attributes.position, barvy = [];
  const mc = C(B.more);
  for (let i = 0; i < pozice.count; i++) {
    const nx = pozice.getX(i) / (SIRKA * 0.62), ny = pozice.getY(i) / (HLOUBKA * 0.68);
    const d = Math.sqrt(nx * nx + ny * ny);
    barvy.push(mc.r, mc.g, mc.b, Math.max(0, Math.min(1, (1.75 - d) / 0.75)));
  }
  mg.setAttribute("color", new THREE.Float32BufferAttribute(barvy, 4));
  const more = new THREE.Mesh(mg, new THREE.MeshStandardMaterial({ vertexColors: true, transparent: true, roughness: 0.95,
                                                                    metalness: 0, depthWrite: false }));
  more.rotateX(-Math.PI / 2);
  more.receiveShadow = true;
  more.renderOrder = -1;
  scene.add(more);
  // souš: deska výšky 2 s dírou jezera, boční stěny Silver
  const zeme = new THREE.Mesh(deska(M.land, 0, VYSKA.zeme), [material(B.zeme), material(B.silver)]);
  zeme.receiveShadow = true; zeme.castShadow = true;
  scene.add(zeme);
  // jezero: hladina zapuštěná o 1 pod souš, barva moře
  const otvor = M.land.slice(1);
  for (const kruh of otvor) {
    const g = new THREE.ShapeGeometry(tvar([kruh]));
    g.rotateX(-Math.PI / 2);
    g.translate(0, VYSKA.zeme - VYSKA.jezero, 0);
    const h = new THREE.Mesh(g, material(B.more));
    h.receiveShadow = true;
    scene.add(h);
  }
  // vysočina: plochý schod o 3 výš, světlejší Silver místo šrafury
  for (const v of M.highlands || []) {
    const m = new THREE.Mesh(deska(v.polygon, VYSKA.zeme, VYSKA.vysocina), [material(B.vysocina), material(B.silver)]);
    m.castShadow = true; m.receiveShadow = true;
    scene.add(m);
    scene.add(obrys(v.polygon[0], VYSKA.zeme + VYSKA.vysocina + 0.05, C(B.steel), 1, 0.6));
  }
  // námořní trasy: tečkovaná linka Steel na hladině
  for (const t of M.sea_routes || []) {
    const body = t.path.map(([x, y]) => { const [sx, sz] = vScene(x, y); return new THREE.Vector3(sx, 0.2, sz); });
    const l = new THREE.Line(new THREE.BufferGeometry().setFromPoints(body),
      new THREE.LineDashedMaterial({ color: B.steel, dashSize: 1.5, gapSize: 5 }));
    l.computeLineDistances();
    scene.add(l);
  }
  // území: extruze výšky 1 nad souší, výplň podle vlivu, hrana Line2 (šířka v pixelech)
  for (const r of M.regions) {
    const cap = material(SILVER40.clone()), bok = material(B.silver);
    const mesh = new THREE.Mesh(deska(r.polygon, VYSKA.zeme, VYSKA.uzemi), [cap, bok]);
    mesh.castShadow = true; mesh.receiveShadow = true;
    mesh.userData.id = r.id;
    scene.add(mesh);
    const hrana = obrys(r.polygon[0], HORNI + 0.06, C(B.graphite), 1, 0.6);
    scene.add(hrana);
    // hlavní město: válec, prstenec pro A, B a členy Unie, oktaedr ložiska oritu
    const [cx, cz] = vScene(r.capital_xy[0], r.capital_xy[1]);
    const mesto = new THREE.Mesh(new THREE.CylinderGeometry(1, 1, VYSKA.mesto, 28), material(B.graphite));
    mesto.position.set(cx, HORNI + VYSKA.mesto / 2, cz);
    mesto.castShadow = true;
    scene.add(mesto);
    const prsten = new THREE.Mesh(new THREE.TorusGeometry(1, 0.06, 8, 48), new THREE.MeshBasicMaterial({ color: B.graphite }));
    prsten.rotateX(Math.PI / 2);
    prsten.position.set(cx, HORNI + 0.4, cz);
    prsten.visible = false;
    scene.add(prsten);
    const orit = new THREE.Mesh(new THREE.OctahedronGeometry(2.2), material(B.steel));
    orit.position.set(cx, HORNI + 2.6, cz);
    orit.castShadow = true;
    orit.visible = false;
    scene.add(orit);
    // popisek
    const div = document.createElement("div");
    div.className = "popisek" + (r.id === "A" || r.id === "B" ? " hrac" : "");
    // text ve vnitřním prvku: transformaci obalu přepisuje CSS2DRenderer, posun nad město nese vnitřek
    const text = document.createElement("span");
    text.textContent = r.id in KRATKE ? KRATKE[r.id] : (svet.jmena[r.id] || r.name);
    div.appendChild(text);
    const popisek = new CSS2DObject(div);
    popisek.position.set(cx, HORNI + VYSKA.mesto + 2, cz);
    scene.add(popisek);
    if (!(r.id in KRATKE)) svet.popiskyMale.push(popisek);
    svet.uzemi.set(r.id, { r, mesh, cap, hrana, mesto, prsten, orit, popisek, v: null, polomer: 2, cil: null });
  }
  // popisek jezera a Unie
  for (const j of M.lakes || []) {
    if (!j.label_xy) continue;
    const d = document.createElement("div");
    d.className = "popisek jezero";
    d.textContent = j.name;
    const o = new CSS2DObject(d);
    const [x, z] = vScene(j.label_xy[0], j.label_xy[1]);
    o.position.set(x, VYSKA.zeme, z);
    scene.add(o);
  }
  const du = document.createElement("div");
  du.className = "popisek hrac";
  du.appendChild(document.createElement("span"));
  svet.popisekUnie = new CSS2DObject(du);
  svet.popisekUnie.visible = false;
  scene.add(svet.popisekUnie);

  // světlo: hemisférické + jedno směrové s měkkým stínem
  scene.add(new THREE.HemisphereLight(0xffffff, 0xd9dde3, 1.9));
  const slunce = new THREE.DirectionalLight(0xffffff, 1.6);
  slunce.position.set(-260, 520, 300);
  slunce.castShadow = true;
  slunce.shadow.mapSize.set(2048, 2048);
  Object.assign(slunce.shadow.camera, { left: -620, right: 620, top: 460, bottom: -460, near: 10, far: 1500 });
  slunce.shadow.radius = 4;
  slunce.shadow.bias = -0.0004;
  scene.add(slunce);
}

/* ------------------------------ kamera a ovládání ------------------------------ */
function nastavKameru(prvni) {
  const el = $("platno");
  const w = el.clientWidth, h = el.clientHeight;
  renderer.setSize(w, h);
  labeler.setSize(w, h);
  for (const u of svet.uzemi.values()) u.hrana.material.resolution.set(w, h);
  scene.traverse((o) => { if (o.material && o.material.isLineMaterial) o.material.resolution.set(w, h); });
  camera.aspect = w / h;
  // vzdálenost, ve které je vidět celá mapa (s rezervou na lišty)
  const tan = Math.tan(deg(camera.fov / 2));
  const D0 = Math.max(HLOUBKA * 0.62 / tan, SIRKA * 0.62 / (tan * camera.aspect));
  const pomer = svet.D0 ? controls.getDistance() / svet.D0 : 1;
  svet.D0 = D0;
  controls.minDistance = D0 / 2.5;
  controls.maxDistance = D0 / 0.7;
  if (prvni) {
    const naklon = deg(MOBIL() ? 40 : 50);
    camera.position.set(0, D0 * Math.cos(naklon), D0 * Math.sin(naklon));
    controls.target.set(0, 0, 0);
  } else {
    const smer = camera.position.clone().sub(controls.target).normalize();
    camera.position.copy(controls.target).addScaledVector(smer, D0 * pomer);
  }
  camera.updateProjectionMatrix();
  controls.update();
  vykresli();
}

function omezPosun() {
  const t = controls.target;
  const nx = Math.min(OX, Math.max(-OX, t.x)), nz = Math.min(OZ, Math.max(-OZ, t.z));
  const d = new THREE.Vector3(nx - t.x, -t.y, nz - t.z);
  if (d.lengthSq() > 0) { t.add(d); camera.position.add(d); }
}

function priblizNa(id, zoom) {
  const u = svet.uzemi.get(id);
  if (!u) return;
  const smer = camera.position.clone().sub(controls.target).normalize();
  controls.target.set(u.mesto.position.x, 0, u.mesto.position.z);
  camera.position.copy(controls.target).addScaledVector(smer, svet.D0 / zoom);
  omezPosun();
  controls.update();
}

function popiskyPodleZoomu() {
  // pod 1× jen A, B, Unie a jezero; na úzkém displeji se malé státy slévají, proto tam až od 1,5×
  const zoom = svet.D0 / controls.getDistance();
  const prah = MOBIL() ? 1.5 : 1;
  for (const p of svet.popiskyMale) p.visible = zoom >= prah - 1e-6;
}

/* ------------------------------ kolo ------------------------------ */
function radek(t) { return svet.souhrn.find((x) => x.turn === t); }

function zobraz(t) {
  const s = radek(t);
  if (!s) return;
  svet.kolo = t;
  $("posuvnik").value = t;
  $("cas-rok").textContent = `${s.cas || `rok ${s.day}`} ·`;
  $("cas-kolo").textContent = `kolo ${t}`;
  history.replaceState(null, "", `#kolo=${t}`);
  const pakty = {};
  for (const d of s.deals || []) if (d.type === "protect") pakty[d.target] = d.owner;
  const kandidati = new Set((s.union && s.union.candidates) || []);
  const clenove = new Set((s.union && s.union.active && s.union.members) || []);
  let maxW = 1;
  for (const st of Object.values(s.states)) maxW = Math.max(maxW, (st.wealth || 0) + (st.paper_wealth || 0));
  const prechody = [];
  for (const [id, u] of svet.uzemi) {
    const st = s.states[id] || {};
    const v = vzhled(id, st, pakty, kandidati);
    const w = Math.max(0, (st.wealth || 0) + (st.paper_wealth || 0));
    const polomer = (4 + 10 * (w / maxW)) / 2;
    prechody.push({ u, z: { fill: u.cap.color.clone(), polomer: u.polomer }, na: { fill: v.fill, polomer } });
    u.v = v;
    u.st = st;
    // prstenec: A a B své barvy, členové Unie zelený
    const hrac = id === "A" || id === "B";
    u.prsten.visible = hrac || clenove.has(id);
    u.prsten.material.color.set(hrac ? B[id] : B.unieHrana);
    u.orit.visible = (st.orit || 0) > 0;
    nastavHranu(id);
  }
  // popisek Unie nad těžištěm hlavních měst členů
  const pu = svet.popisekUnie;
  if (clenove.size) {
    let x = 0, z = 0;
    for (const id of clenove) { const u = svet.uzemi.get(id); x += u.mesto.position.x; z += u.mesto.position.z; }
    pu.position.set(x / clenove.size, HORNI + 8, z / clenove.size);
    pu.element.firstChild.textContent = s.union.name || "Unie";
    pu.visible = true;
  } else pu.visible = false;
  animuj(prechody);
}

function nastavHranu(id) {
  const u = svet.uzemi.get(id);
  if (!u || !u.v) return;
  const aktivni = svet.hover === id || svet.vybrany === id;
  const m = u.hrana.material;
  m.color.copy(aktivni ? C(B.ion) : u.v.hrana);
  m.linewidth = aktivni ? 2 : u.v.sirka;
  m.opacity = aktivni ? 1 : u.v.kryti;
  m.transparent = m.opacity < 1;
  u.hrana.position.y = aktivni ? 0.04 : 0;
}

/* přechod barev a velikosti měst 400 ms, lineárně; bez animace při prefers-reduced-motion */
function animuj(prechody) {
  if (svet.animace) cancelAnimationFrame(svet.animace);
  const nastav = (k) => {
    for (const p of prechody) {
      p.u.cap.color.lerpColors(p.z.fill, p.na.fill, k);
      p.u.polomer = p.z.polomer + (p.na.polomer - p.z.polomer) * k;
      p.u.mesto.scale.set(p.u.polomer, 1, p.u.polomer);
      p.u.prsten.scale.setScalar(p.u.polomer + 1.6);
      p.u.orit.position.x = p.u.mesto.position.x + p.u.polomer + 3.4;
    }
    renderer.render(scene, camera); labeler.render(scene, camera);
  };
  if (KLIDNE) { nastav(1); return; }
  const start = performance.now();
  const krok = (cas) => {
    const k = Math.min(1, (cas - start) / 400);
    nastav(k);
    svet.animace = k < 1 ? requestAnimationFrame(krok) : null;
  };
  svet.animace = requestAnimationFrame(krok);
}

/* ------------------------------ lišta kol ------------------------------ */
function znackySlideru() {
  const box = $("znacky");
  box.replaceChildren();
  const min = Number($("posuvnik").min), max = Number($("posuvnik").max);
  const rozsah = Math.max(1, max - min);
  const kde = (t) => `${((t - min) / rozsah) * 100}%`;
  const popisujKazdy = rozsah > 45 ? 15 : (rozsah > 18 ? 6 : 3);
  for (let t = min; t <= max; t++) {
    if (t % 3 !== 0) continue;
    const z = document.createElement("i");
    z.className = "znacka-den";
    z.style.left = kde(t);
    if (t % popisujKazdy === 0) z.innerHTML = `<span>${t / 3}. den</span>`;
    box.appendChild(z);
  }
  let pred = null;
  for (const r of svet.souhrn) {
    if (pred !== null && r.phase !== pred) {
      const z = document.createElement("i");
      z.className = "znacka-faze";
      z.style.left = kde(r.turn);
      z.tabIndex = 0;
      z.innerHTML = `<b>${esc(FAZE[r.phase] || r.phase)} · kolo ${r.turn}</b>`;
      box.appendChild(z);
    }
    pred = r.phase;
  }
}

function posun(krok) {
  const p = $("posuvnik");
  const t = Math.min(Number(p.max), Math.max(Number(p.min), Number(p.value) + krok));
  zobraz(t);
}

function prehrat() {
  const tl = $("prehrat");
  if (svet.prehravani) {
    clearInterval(svet.prehravani); svet.prehravani = null;
    tl.textContent = "Přehrát"; tl.setAttribute("aria-pressed", "false");
    return;
  }
  const p = $("posuvnik");
  if (Number(p.value) >= Number(p.max)) zobraz(Number(p.min));
  tl.textContent = "Zastavit"; tl.setAttribute("aria-pressed", "true");
  svet.prehravani = setInterval(() => {
    if (Number(p.value) >= Number(p.max)) { prehrat(); return; }
    posun(1);
  }, 1200);
}

/* ------------------------------ interakce ------------------------------ */
const paprsek = new THREE.Raycaster();
function uzemiPodKurzorem(ev) {
  const r = renderer.domElement.getBoundingClientRect();
  const v = new THREE.Vector2(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1);
  paprsek.setFromCamera(v, camera);
  const zasah = paprsek.intersectObjects([...svet.uzemi.values()].map((u) => u.mesh), false)[0];
  return zasah ? zasah.object.userData.id : null;
}

function tooltip(id, x, y) {
  const t = $("tooltip");
  if (!id) { t.hidden = true; return; }
  const u = svet.uzemi.get(id);
  const st = u.st || {};
  const jmeno = id in HRACI ? HRACI[id] : (svet.jmena[id] || u.r.name);
  const status = id in HRACI ? "velmoc" : (STATUS[st.status] || st.status || "");
  const vliv = id in HRACI ? "–" : `${cis((st.influence || {}).A)} / ${cis((st.influence || {}).B)}`;
  t.innerHTML = `<b>${esc(jmeno)}</b>` +
    `<div class="radek"><span>Status</span><span>${esc(status)}</span></div>` +
    `<div class="radek"><span>Vliv A / B</span><span>${esc(vliv)}</span></div>` +
    `<div class="radek"><span>Bohatství</span><span>${cis((st.wealth || 0) + (st.paper_wealth || 0))}</span></div>`;
  t.hidden = false;
  const sirka = t.offsetWidth, vyska = t.offsetHeight;
  t.style.left = Math.min(window.innerWidth - sirka - 8, Math.max(8, x + 14)) + "px";
  t.style.top = Math.min(window.innerHeight - vyska - 8, Math.max(8, y + 14)) + "px";
}

function zvyrazni(id) {
  const pred = svet.hover;
  svet.hover = id;
  if (pred && pred !== id) nastavHranu(pred);
  if (id) nastavHranu(id);
  vykresli();
}

function vyber(id) {
  const pred = svet.vybrany;
  svet.vybrany = pred === id ? null : id;
  if (pred) nastavHranu(pred);
  if (id) nastavHranu(id);
  console.log(id);   // panel státu přijde v etapě 2
  vykresli();
}

function pozicePopisku(id) {
  const u = svet.uzemi.get(id);
  const p = u.mesto.position.clone().project(camera);
  const r = renderer.domElement.getBoundingClientRect();
  return [r.left + (p.x + 1) / 2 * r.width, r.top + (1 - p.y) / 2 * r.height];
}

function napojInterakce() {
  const el = renderer.domElement;
  let dolu = null;
  el.addEventListener("pointermove", (ev) => {
    if (ev.pointerType !== "mouse") return;
    const id = uzemiPodKurzorem(ev);
    if (id !== svet.hover) zvyrazni(id);
    tooltip(id, ev.clientX, ev.clientY);
    el.style.cursor = id ? "pointer" : "";
  });
  el.addEventListener("pointerleave", () => { zvyrazni(null); tooltip(null); });
  el.addEventListener("pointerdown", (ev) => { dolu = [ev.clientX, ev.clientY]; });
  el.addEventListener("pointerup", (ev) => {
    if (!dolu || Math.hypot(ev.clientX - dolu[0], ev.clientY - dolu[1]) > 5) { dolu = null; return; }
    dolu = null;
    const id = uzemiPodKurzorem(ev);
    if (id) {
      vyber(id);
      if (ev.pointerType !== "mouse") { const [x, y] = pozicePopisku(id); tooltip(svet.vybrany ? id : null, x, y); }
    }
  });
  // klávesnice: Tab prochází území v pořadí map.json, Enter = klik
  const box = $("klavesnice");
  for (const r of svet.mapa.regions) {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = r.id in HRACI ? HRACI[r.id] : (svet.jmena[r.id] || r.name);
    b.addEventListener("focus", () => { zvyrazni(r.id); const [x, y] = pozicePopisku(r.id); tooltip(r.id, x, y); });
    b.addEventListener("blur", () => { zvyrazni(null); tooltip(null); });
    b.addEventListener("click", () => vyber(r.id));
    box.appendChild(b);
  }
}

/* ------------------------------ start ------------------------------ */
async function start() {
  if (typeof vlozSvg === "function") document.querySelectorAll("[data-svg]").forEach(vlozSvg);
  plexusOkraj($("plexus-okraj"));
  if (!maWebGL()) {
    $("platno").innerHTML = '<div class="bez-webgl"><p>3D mapa potřebuje WebGL.</p><a class="tlacitko" href="index.html">Zpět na mapu ve 2D</a></div>';
    return;
  }
  let npc;
  try {
    [svet.mapa, npc] = await Promise.all([nacti("web/map.json"), nacti("npc.json")]);
    svet.souhrn = (await nacti("history/summary.json")).turns || [];
  } catch (e) {
    $("platno").innerHTML = `<div class="bez-webgl"><p class="chyba">Data hry se nepodařilo načíst (${esc(e.message)}).</p></div>`;
    return;
  }
  for (const n of npc.npc || []) svet.jmena[n.id] = n.name;
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.setClearColor(0x000000, 0);
  $("platno").appendChild(renderer.domElement);
  labeler = new CSS2DRenderer({ element: $("popisky") });
  camera = new THREE.PerspectiveCamera(32, 1, 5, 6000);
  postavScenu();
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = false;
  controls.screenSpacePanning = false;          // posun po rovině mapy
  controls.minAzimuthAngle = 0;                 // otáčení kolem svislé osy zakázané, sever nahoře
  controls.maxAzimuthAngle = 0;
  controls.minPolarAngle = deg(35);              // náklon 35 až 65°
  controls.maxPolarAngle = deg(65);
  controls.mouseButtons = { LEFT: THREE.MOUSE.PAN, MIDDLE: THREE.MOUSE.DOLLY, RIGHT: THREE.MOUSE.ROTATE };
  controls.touches = { ONE: THREE.TOUCH.PAN, TWO: THREE.TOUCH.DOLLY_ROTATE };
  controls.addEventListener("change", () => { omezPosun(); popiskyPodleZoomu(); vykresli(); });
  nastavKameru(true);
  window.addEventListener("resize", () => nastavKameru(false));
  napojInterakce();

  if (!svet.souhrn.length) return;
  const p = $("posuvnik");
  p.min = svet.souhrn[0].turn;
  p.max = svet.souhrn[svet.souhrn.length - 1].turn;
  p.addEventListener("input", () => zobraz(Number(p.value)));
  $("zpet").addEventListener("click", () => posun(-1));
  $("dal").addEventListener("click", () => posun(1));
  $("prehrat").addEventListener("click", prehrat);
  $("lista").hidden = false;
  znackySlideru();
  // stav v URL: #kolo=11, volitelně zoom=2&na=A (sdílení a screenshoty)
  const h = new URLSearchParams(location.hash.slice(1));
  const kolo = Number(h.get("kolo")) || Number(p.max);
  if (h.get("na") && Number(h.get("zoom"))) priblizNa(h.get("na"), Math.min(2.5, Math.max(0.7, Number(h.get("zoom")))));
  popiskyPodleZoomu();
  zobraz(Math.min(Number(p.max), Math.max(Number(p.min), kolo)));
  window.ARDAN_3D_HOTOVO = true;
}

start();
