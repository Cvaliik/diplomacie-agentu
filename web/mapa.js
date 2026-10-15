/* Ardan v 3D (etapa 2): mapa, HUD, bublina kola, panel státu, projevy a kronika.
   three.js z CDN přes importmap (mapa.html), bez bundleru. Geometrie z web/map.json, stav světa po kolech
   z history/summary.json; plné snímky history/turn_NNN.json se čtou až při otevření panelu, projevů
   nebo pro bublinu kola. Popis v web/MAPA3D.md. */
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { CSS2DRenderer, CSS2DObject } from "three/addons/renderers/CSS2DRenderer.js";
import { Line2 } from "three/addons/lines/Line2.js";
import { LineMaterial } from "three/addons/lines/LineMaterial.js";
import { LineGeometry } from "three/addons/lines/LineGeometry.js";

const ZAKLAD = "..";
/* barvy: značka Kája Industries (kaja.css) a sémantické barvy mapy; Kalvera není Ion Blue */
const B = {
  hull: "#F3F4F6", silver: "#C8CDD4", bok: "#B4BAC3", steel: "#6E7680", graphite: "#22252A", ion: "#2F80D1",
  more: "#E3E8EE", zeme: "#F7F8FA", vysocina: "#DDE1E6",
  A: "#2B4A8C", B: "#BA544A", Atm: "#1A2D57", Btm: "#6E2A24", unie: "#6F9E73", unieHrana: "#3F7D45", zlata: "#B8902A"
};
const VYSKA = { zeme: 5, uzemi: 2, vysocina: 4, jezero: 1, mesto: 4 };
const SIRKA = 1000, HLOUBKA = 700, OX = SIRKA / 2, OZ = HLOUBKA / 2;
const HORNI = VYSKA.zeme + VYSKA.uzemi;   // horní plocha území
const HRACI = { A: "Kalverská federace", B: "Lidová republika Ostrogard" };
const KRATKE = { A: "Kalvera", B: "Ostrogard" };
const ROD = { A: "a", B: "", C: "a" };   // koncovka slovesa v minulém čase podle rodu (Kalvera, Ostrogard, Unie)
const BARVA_HRACE = { A: B.A, B: B.B, C: B.unieHrana };
const FAZE = {
  pre: "Před objevem", displacement: "Šok, vytěsnění", boom: "Rozmach", euphoria: "Euforie",
  overtrading: "Nadměrné obchodování", distress: "Finanční tíseň", panic: "Panika",
  crash: "Krach", depression: "Deprese", recovery: "Zotavení"
};
const STATUS = {
  independent: "nezávislý", sphere_A: "sféra Kalvery", sphere_B: "sféra Ostrogardu",
  occupied_A: "okupován Kalverou", occupied_B: "okupován Ostrogardem", union: "člen Unie", candidate: "kandidát Unie"
};
const STATEK = { grain: "obilí", oil: "ropa", metal: "kovy", goods: "zboží", orit: "orit" };
const STATEK_NA = { grain: "obilí", oil: "ropu", metal: "kovy", goods: "zboží", orit: "orit" };
const VYSLEDEK = {
  prijato: "přijato", podminka: "přijato s podmínkou", protinavrh: "protinávrh",
  odmitnuto: "odmítnuto", prednost_druhe_strany: "dalo přednost druhé straně", vyrazeno: "vyřazeno"
};
const AKCE_KRATCE = {
  trade_offer: "nabídka obchodu", loan: "půjčka", protect: "pakt", invade: "invaze", admit: "členství",
  pressure: "sankce", accept_offer: "přijetí nabídky", arm: "zbrojení", declare_war: "válka"
};
const KLIDNE = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const MOBIL = () => window.matchMedia("(max-width: 599px)").matches;
const deg = (d) => d * Math.PI / 180;
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const cis = (n, d = 1) => (n == null || isNaN(Number(n))) ? "–" : Number(n).toLocaleString("cs-CZ", { maximumFractionDigits: d });
const vys = (pojem) => `<button type="button" class="vys" data-pojem="${esc(pojem)}" aria-label="Co je ${esc(pojem)}">?</button>`;
const stitek = (text, slaby) => `<span class="stitek-v${slaby ? " slaby" : ""}">${esc(text)}</span>`;

async function nacti(cesta) {
  const r = await fetch(`${ZAKLAD}/${cesta}`, { cache: "no-cache" });
  if (!r.ok) throw new Error(`${cesta}: ${r.status}`);
  return cesta.endsWith(".md") ? r.text() : r.json();
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
const cary = [];   // všechny Line2 (kvůli rozlišení při změně velikosti okna)
function cara(body, barva, sirka, kryti) {
  const g = new LineGeometry();
  g.setPositions(body);
  const m = new LineMaterial({ color: barva, linewidth: sirka, transparent: kryti < 1, opacity: kryti, worldUnits: false });
  const l = new Line2(g, m);
  cary.push(l);
  return l;
}
function obrys(kruh, y, barva, sirka, kryti) {
  const body = [];
  for (const [x, z] of [...kruh, kruh[0]]) { const [sx, sz] = vScene(x, z); body.push(sx, y, sz); }
  return cara(body, barva, sirka, kryti);
}
function kruznice(barva, sirka) {
  const body = [];
  for (let i = 0; i <= 64; i++) { const a = (i / 64) * Math.PI * 2; body.push(Math.cos(a), 0, Math.sin(a)); }
  return cara(body, barva, sirka, 1);
}

/* ------------------------------ barvy vlivu ------------------------------ */
const C = (h) => new THREE.Color(h);
const SILVER40 = C(B.zeme).lerp(C(B.silver), 0.4);
const MAX_VLIV = 20;   // součet vlivu, při kterém je barva plná (práh sféry je 10 u jedné velmoci)

function vzhled(id, st, pakty, kandidati) {
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

/* ------------------------------ stav stránky ------------------------------ */
const svet = { mapa: null, souhrn: [], jmena: {}, kolo: 0, uzemi: new Map(), vybrany: null, hover: null, panel: null,
               D0: 1000, prehravani: null, animace: null, popiskyMale: [], popisekJezera: null, snimky: new Map(),
               kroniky: null, bublinaCas: null, otevreno: null };
let renderer, labeler, scene, camera, controls;
let cekaRender = false;
const vykresli = () => {
  if (cekaRender) return;
  cekaRender = true;
  requestAnimationFrame(() => { cekaRender = false; renderer.render(scene, camera); labeler.render(scene, camera); });
};
const jm = (id) => (id === "C" ? (svet.unie || "Unie") : (KRATKE[id] || svet.jmena[id] || id || ""));
const plneJmeno = (id) => (id in HRACI ? HRACI[id] : jm(id));

function snimek(t) {
  if (!svet.snimky.has(t)) svet.snimky.set(t, nacti(`history/turn_${String(t).padStart(3, "0")}.json`));
  return svet.snimky.get(t);
}

function maWebGL() {
  try { const c = document.createElement("canvas"); return Boolean(c.getContext("webgl2") || c.getContext("webgl")); }
  catch (e) { return false; }
}

/* ------------------------------ scéna ------------------------------ */
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
  // souš: deska výšky 5 s dírou jezera, boční stěny o stupeň tmavší Silver
  const zeme = new THREE.Mesh(deska(M.land, 0, VYSKA.zeme), [material(B.zeme), material(B.bok)]);
  zeme.receiveShadow = true; zeme.castShadow = true;
  scene.add(zeme);
  // jezero: hladina zapuštěná o 1 pod souš, barva moře
  for (const kruh of M.land.slice(1)) {
    const g = new THREE.ShapeGeometry(tvar([kruh]));
    g.rotateX(-Math.PI / 2);
    g.translate(0, VYSKA.zeme - VYSKA.jezero, 0);
    const h = new THREE.Mesh(g, material(B.more));
    h.receiveShadow = true;
    scene.add(h);
  }
  // vysočina: plochý schod o 4 výš, světlejší Silver místo šrafury
  for (const v of M.highlands || []) {
    const m = new THREE.Mesh(deska(v.polygon, VYSKA.zeme, VYSKA.vysocina), [material(B.vysocina), material(B.bok)]);
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
  // území, města, prstence, ložiska oritu, popisky
  const skryty = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false });
  for (const r of M.regions) {
    const cap = material(SILVER40.clone());
    const mesh = new THREE.Mesh(deska(r.polygon, VYSKA.zeme, VYSKA.uzemi), [cap, material(B.bok)]);
    mesh.castShadow = true; mesh.receiveShadow = true;
    mesh.userData = { id: r.id, druh: "uzemi" };
    scene.add(mesh);
    const hrana = obrys(r.polygon[0], HORNI + 0.06, C(B.graphite), 1, 0.6);
    scene.add(hrana);
    const [cx, cz] = vScene(r.capital_xy[0], r.capital_xy[1]);
    const mesto = new THREE.Mesh(new THREE.CylinderGeometry(1, 1, VYSKA.mesto, 32), material(B.graphite));
    mesto.position.set(cx, HORNI + VYSKA.mesto / 2, cz);
    mesto.castShadow = true;
    mesto.userData = { id: r.id, druh: "mesto" };
    scene.add(mesto);
    // prstenec 1,5 px v barvě hráče; klikací plocha prstence je neviditelný torus
    // světlý lem pod prstencem, jinak by prstenec A a B na vlastním území splynul s výplní
    const lem = kruznice(C(B.hull), 4.5);
    lem.position.set(cx, HORNI + 0.25, cz);
    lem.visible = false;
    scene.add(lem);
    const prsten = kruznice(C(B.graphite), 1.5);
    prsten.position.set(cx, HORNI + 0.35, cz);
    prsten.visible = false;
    scene.add(prsten);
    const prstenKlik = new THREE.Mesh(new THREE.TorusGeometry(1, 0.32, 6, 32), skryty);
    prstenKlik.rotateX(Math.PI / 2);
    prstenKlik.position.set(cx, HORNI + 0.6, cz);
    prstenKlik.userData = { id: r.id, druh: "prsten" };
    scene.add(prstenKlik);
    const orit = new THREE.Mesh(new THREE.OctahedronGeometry(2.4), material(B.steel));
    orit.position.set(cx, HORNI + 3, cz);
    orit.castShadow = true;
    orit.visible = false;
    scene.add(orit);
    const div = document.createElement("div");
    div.className = "popisek" + (r.id === "A" || r.id === "B" ? " hrac" : "");
    const text = document.createElement("span");   // posun nad město nese vnitřek, obal posouvá CSS2DRenderer
    text.textContent = r.id in KRATKE ? KRATKE[r.id] : (svet.jmena[r.id] || r.name);
    div.appendChild(text);
    const popisek = new CSS2DObject(div);
    popisek.position.set(cx, HORNI + VYSKA.mesto + 2, cz);
    scene.add(popisek);
    if (!(r.id in KRATKE)) svet.popiskyMale.push(popisek);
    svet.uzemi.set(r.id, { r, mesh, cap, hrana, mesto, lem, prsten, prstenKlik, orit, popisek, v: null, polomer: 3, st: {} });
  }
  for (const j of M.lakes || []) {
    if (!j.label_xy) continue;
    const d = document.createElement("div");
    d.className = "popisek jezero";
    d.innerHTML = `<span>${esc(j.name)}</span>`;
    const o = new CSS2DObject(d);
    const [x, z] = vScene(j.label_xy[0], j.label_xy[1]);
    o.position.set(x, VYSKA.zeme, z);
    scene.add(o);
    svet.popisekJezera = o;
  }
  const du = document.createElement("div");
  du.className = "popisek hrac";
  du.appendChild(document.createElement("span"));
  svet.popisekUnie = new CSS2DObject(du);
  svet.popisekUnie.visible = false;
  scene.add(svet.popisekUnie);

  // světlo: hemisférické + jedno směrové s měkkým stínem, elevace kolem 40° pro delší stín
  scene.add(new THREE.HemisphereLight(0xffffff, 0xd9dde3, 1.9));
  const slunce = new THREE.DirectionalLight(0xffffff, 1.6);
  const el = deg(40), az = deg(-135);
  slunce.position.set(700 * Math.cos(el) * Math.cos(az) * -1, 700 * Math.sin(el), 700 * Math.cos(el) * Math.sin(az) * -1);
  slunce.castShadow = true;
  slunce.shadow.mapSize.set(2048, 2048);
  Object.assign(slunce.shadow.camera, { left: -640, right: 640, top: 480, bottom: -480, near: 10, far: 2000 });
  slunce.shadow.radius = 4;
  slunce.shadow.bias = -0.0004;
  scene.add(slunce);
}

/* ------------------------------ kamera a ovládání ------------------------------ */
function vychoziVzdalenost(w, h) {
  const tan = Math.tan(deg(camera.fov / 2));
  const aspect = w / h;
  if (MOBIL()) {
    // mobil: mapa vyplní šířku s okrajem 16 px
    return (SIRKA / 2) * (w / Math.max(1, w - 32)) / (tan * aspect);
  }
  return Math.max(HLOUBKA * 0.66 / tan, SIRKA * 0.62 / (tan * aspect));
}

function nastavKameru(prvni) {
  const el = $("platno");
  const w = el.clientWidth, h = el.clientHeight;
  renderer.setSize(w, h);
  labeler.setSize(w, h);
  for (const l of cary) l.material.resolution.set(w, h);
  camera.aspect = w / h;
  const D0 = vychoziVzdalenost(w, h);
  const pomer = svet.D0 && !prvni ? controls.getDistance() / svet.D0 : 1;
  svet.D0 = D0;
  controls.minDistance = D0 / 2.5;
  controls.maxDistance = D0 / 0.7;
  if (prvni) {
    const naklon = deg(MOBIL() ? 40 : 55);
    camera.position.set(0, D0 * Math.cos(naklon), D0 * Math.sin(naklon));
    controls.target.set(0, 0, MOBIL() ? 0 : 20);
    camera.position.z += controls.target.z;
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
  // pod 1× jen A, B, Unie a jezero; na úzkém displeji malé státy i jezero až od 1,5×
  const zoom = svet.D0 / controls.getDistance();
  const prah = MOBIL() ? 1.5 : 1;
  for (const p of svet.popiskyMale) p.visible = zoom >= prah - 1e-6;
  if (svet.popisekJezera) svet.popisekJezera.visible = !MOBIL() || zoom >= 1.5 - 1e-6;
}

/* ------------------------------ kolo ------------------------------ */
function radek(t) { return svet.souhrn.find((x) => x.turn === t); }

function adresa() {
  const h = new URLSearchParams();
  h.set("kolo", svet.kolo);
  if (svet.panel) h.set("stat", svet.panel);
  history.replaceState(null, "", `#${h.toString()}`);
}

function sipka(nyni, pred) {
  if (nyni == null || pred == null) return "";
  const d = Number(nyni) - Number(pred);
  if (Math.abs(d) < 0.005) return ' <span class="sipka" aria-label="beze změny">→</span>';
  return d > 0 ? ' <span class="sipka" aria-label="roste">↑</span>' : ' <span class="sipka" aria-label="klesá">↓</span>';
}

function hud(s) {
  const i = svet.souhrn.findIndex((x) => x.turn === s.turn);
  const p = i > 0 ? svet.souhrn[i - 1] : null;
  $("h-kolo").textContent = s.turn;
  $("h-rok").textContent = s.cas || `rok ${s.day}`;
  $("h-faze").textContent = FAZE[s.phase] || s.phase;
  const idx = s.metrics && s.metrics.prosperity_index;
  $("h-index").innerHTML = idx != null ? cis(idx, 1) + sipka(idx, p && p.metrics && p.metrics.prosperity_index) : "–";
  const orit = s.prices && s.prices.orit;
  $("h-orit").innerHTML = orit != null ? cis(orit, 2) + sipka(orit, p && p.prices && p.prices.orit) : "–";
  const b = s.banks || {};
  const kap = (x) => (!x ? "–" : (x.failed ? "pád" : cis(x.capital, 1) + (x.insolvent ? "!" : "")));
  $("h-banky").textContent = `${kap(b.K)} / ${kap(b.AUR)}`;
  $("cas-rok").textContent = `${s.cas || `rok ${s.day}`} ·`;
  $("cas-kolo").textContent = `kolo ${s.turn}`;
}

function zobraz(t) {
  const s = radek(t);
  if (!s) return;
  svet.kolo = t;
  $("posuvnik").value = t;
  hud(s);
  if (s.union && s.union.name) svet.unie = s.union.name;
  adresa();
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
    const polomer = (6 + 10 * (w / maxW)) / 2;   // průměr 6 až 16
    prechody.push({ u, z: { fill: u.cap.color.clone(), polomer: u.polomer }, na: { fill: v.fill, polomer } });
    u.v = v;
    u.st = st;
    const hrac = id === "A" || id === "B";
    u.prsten.visible = hrac || clenove.has(id);
    u.lem.visible = u.prsten.visible;
    u.prsten.material.color.set(hrac ? B[id] : B.unieHrana);
    u.orit.visible = (st.orit || 0) > 0;
    nastavHranu(id);
  }
  const pu = svet.popisekUnie;
  if (clenove.size) {
    let x = 0, z = 0;
    for (const id of clenove) { const u = svet.uzemi.get(id); x += u.mesto.position.x; z += u.mesto.position.z; }
    pu.position.set(x / clenove.size, HORNI + 9, z / clenove.size);
    pu.element.firstChild.textContent = s.union.name || "Unie";
    pu.visible = true;
  } else pu.visible = false;
  animuj(prechody);
  bublinaKola(t);
  if (svet.panel) panelStatu(svet.panel);
  if (svet.otevreno === "projevy") projevy();
  if (svet.otevreno === "kronika") kronika();
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
}

/* přechod barev a velikosti měst 400 ms, lineárně; bez animace při prefers-reduced-motion */
function animuj(prechody) {
  if (svet.animace) cancelAnimationFrame(svet.animace);
  const nastav = (k) => {
    for (const p of prechody) {
      const u = p.u;
      u.cap.color.lerpColors(p.z.fill, p.na.fill, k);
      u.polomer = p.z.polomer + (p.na.polomer - p.z.polomer) * k;
      u.mesto.scale.set(u.polomer, 1, u.polomer);
      u.prsten.scale.set(u.polomer + 1.8, 1, u.polomer + 1.8);
      u.lem.scale.set(u.polomer + 1.8, 1, u.polomer + 1.8);
      u.prstenKlik.scale.setScalar(u.polomer + 1.8);
      u.orit.position.x = u.mesto.position.x + u.polomer + 4;
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

/* ------------------------------ bublina „co se stalo“ ------------------------------ */
const VETY = [
  // [priorita, druh události, věta]; co tu není, se nezobrazuje
  [1, "war_declared", (e) => `${jm(e.aggressor)} vyhlásil${ROD[e.aggressor] ?? ""} válku státu ${jm(e.defender)}.`],
  [1, "war_end", (e) => `Válka mezi státy ${jm((e.between || [])[0])} a ${jm((e.between || [])[1])} skončila.`],
  [2, "occupied", (e) => `${jm(e.attacker)} obsadil${ROD[e.attacker] ?? ""} stát ${jm(e.target)}.`],
  [2, "invade_progress", (e) => (Number(e.turns) <= 1
    ? `${jm(e.player)} zahájil${ROD[e.player] ?? ""} invazi do státu ${jm(e.target)}.`
    : `${jm(e.player)} pokračuje v invazi do státu ${jm(e.target)} (${e.turns}. kolo).`)],
  [3, "union_founded", () => "Krize zrodila Unii menších států."],
  [3, "phase", (e) => `Svět vstoupil do fáze ${FAZE[e.to] || e.to}.`],
  [4, "protect_started", (e) => `${jm(e.player)} uzavřel${ROD[e.player] ?? ""} ochranný pakt se státem ${jm(e.target)}.`],
  [5, "trade_opened", (e) => { const d = e.deal || {}; return `${jm(d.owner)} a ${d.target in HRACI ? "" : "stát "}${jm(d.target)} uzavřeli smlouvu na ${STATEK_NA[d.res] || d.res}.`; }],
  [6, "loan_given", (e) => `${jm(e.player)} půjčil${ROD[e.player] ?? ""} státu ${jm(e.target)} ${cis(e.amount)}.`]
];

async function bublinaKola(t) {
  const b = $("bublina-kola");
  let veta = null, priorita = 99;
  try {
    const sn = await snimek(t);
    if (svet.kolo !== t) return;
    for (const e of sn.events || []) {
      if (e.private) continue;
      for (const [p, druh, f] of VETY) if (e.kind === druh && p < priorita) { priorita = p; veta = f(e); }
    }
  } catch (err) { /* bez snímku jen změna indexu */ }
  if (!veta) {
    const i = svet.souhrn.findIndex((x) => x.turn === t);
    const a = i > 0 ? svet.souhrn[i - 1].metrics : null, s = svet.souhrn[i] && svet.souhrn[i].metrics;
    if (a && s && Math.abs(s.prosperity_index - a.prosperity_index) >= 0.05) {
      veta = `Index prosperity ${s.prosperity_index > a.prosperity_index ? "vzrostl" : "klesl"} na ${cis(s.prosperity_index, 1)}.`;
    }
  }
  clearTimeout(svet.bublinaCas);
  if (!veta || svet.otevreno) { b.hidden = true; return; }
  b.innerHTML = `<span class="hud">Kolo ${t}</span>${esc(veta)}`;
  b.hidden = false;
  svet.bublinaCas = setTimeout(() => { b.hidden = true; }, 6000);
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
  zobraz(Math.min(Number(p.max), Math.max(Number(p.min), Number(p.value) + krok)));
}

function prehrat() {
  const tl = $("prehrat");
  if (svet.prehravani) {
    clearInterval(svet.prehravani); svet.prehravani = null;
    tl.querySelector(".text-prehrat").textContent = "Přehrát"; tl.setAttribute("aria-pressed", "false");
    return;
  }
  const p = $("posuvnik");
  if (Number(p.value) >= Number(p.max)) zobraz(Number(p.min));
  tl.querySelector(".text-prehrat").textContent = "Zastavit"; tl.setAttribute("aria-pressed", "true");
  svet.prehravani = setInterval(() => {
    if (Number(p.value) >= Number(p.max)) { prehrat(); return; }
    posun(1);
  }, 1200);
}

/* ------------------------------ panel státu ------------------------------ */
async function panelStatu(id) {
  const box = $("panel");
  svet.panel = id;
  box.hidden = false;
  adresa();
  const t = svet.kolo;
  const s = radek(t) || {};
  const st = (s.states || {})[id] || {};
  let e = null;
  try {   // síla, produkce a dluhy jsou jen v plném snímku: čte se až teď
    const sn = await snimek(t);
    if (svet.kolo !== t || svet.panel !== id) return;
    e = id in (sn.state.npc || {}) ? sn.state.npc[id] : sn.state.players[id];
  } catch (err) { e = null; }
  const radky = [];
  const oddil = (n) => radky.push(["#", n]);
  const status = id in HRACI ? "velmoc" : (STATUS[st.status] || st.status || "");
  radky.push(["status", status, id in HRACI ? null : "sféra"]);
  radky.push(["bohatství", cis((st.wealth || 0) + (st.paper_wealth || 0)) + (st.paper_wealth ? ` (z toho papírové ${cis(st.paper_wealth)})` : "")]);
  if (e) radky.push(["síla", cis(e.power)]);
  radky.push(["obyvatelstvo", cis(st.pop, 0)]);
  if (id in HRACI) {
    radky.push(["právo", cis(st.law, 2), "právo"]);
    radky.push(["technologie", cis(st.tech, 2), "technologie"]);
    radky.push(["průmysl", cis(st.industry, 2), "průmysl"]);
  }
  oddil("Suroviny");
  const sur = st.suroviny || {};
  for (const res of ["grain", "oil", "metal"]) {
    const r = sur[res];
    if (r) radky.push([STATEK[res], `výroba ${cis(r.vyroba)}, potřeba ${cis(r.potreba)}, zásoba ${cis(r.stock)}`]);
  }
  if (st.goods) radky.push(["zboží", `výroba ${cis(st.goods.vyroba)}, potřeba ${cis(st.goods.potreba)}, zásoba ${cis(st.goods.stock)}`, "zboží (goods)"]);
  if ((st.orit || 0) > 0) radky.push(["orit", `těžba ${cis(st.orit)}`, "orit"]);
  if (!(id in HRACI)) {
    oddil("Vliv a vazby");
    radky.push(["vliv Kalvery / Ostrogardu", `${cis((st.influence || {}).A)} / ${cis((st.influence || {}).B)}`, "vliv"]);
  } else oddil("Vazby");
  const pakty = (s.deals || []).filter((d) => d.type === "protect" && (d.target === id || d.owner === id));
  if (pakty.length) radky.push(["pakty", pakty.map((d) => (d.owner === id ? `chrání ${jm(d.target)}` : `pod ochranou ${jm(d.owner)}`)).join(", "), "pakt"]);
  const smlouvy = (s.deals || []).filter((d) => d.type === "trade" && (d.target === id || d.owner === id));
  if (smlouvy.length) radky.push(["smlouvy", smlouvy.map((d) => `${STATEK[d.res] || d.res}, ${jm(d.owner === id ? d.target : d.owner)}`).join("; "), "smlouva"]);
  const db = st.dluh_banky || {};
  const dl = [["K", "kalverské"], ["AUR", "Aurelie"], ["U", "Unie"]].filter(([k]) => Number(db[k] || 0) > 0.05).map(([k, n]) => `${n} ${cis(db[k])}`);
  if (dl.length) radky.push(["dluh bankám", dl.join(" · ")]);
  if (e && e.debt) {
    const dh = ["A", "B", "C"].filter((k) => Number(e.debt[k] || 0) > 0.05).map((k) => `${jm(k)} ${cis(e.debt[k])}`);
    if (dh.length) radky.push(["dluh hráčům", dh.join(" · "), "půjčka"]);
  }
  if (e && e.prod) {
    const prod = Object.entries(e.prod).filter(([, v]) => Number(v) > 0).map(([k, v]) => `${STATEK[k] || k} ${cis(v)}`).join(", ");
    if (prod) radky.splice(4, 0, ["produkce", prod]);
  }
  if (!pakty.length && !smlouvy.length && !dl.length && radky[radky.length - 1][0] === "#") radky.push(["", "žádné"]);
  box.innerHTML = `<button type="button" class="zavrit" aria-label="Zavřít panel státu">×</button>` +
    `<span class="hud">Kolo ${t} · stát</span><h2>${esc(plneJmeno(id))}</h2>` +
    `<table>${radky.map(([k, v, p]) => (k === "#" ? `<tr class="oddil"><td colspan="2">${esc(v)}</td></tr>`
      : `<tr><td>${esc(k)}${p ? vys(p) : ""}</td><td>${esc(v)}</td></tr>`)).join("")}</table>`;
  box.querySelector(".zavrit").addEventListener("click", zavriPanel);
}

function zavriPanel() {
  $("panel").hidden = true;
  svet.panel = null;
  const pred = svet.vybrany;
  svet.vybrany = null;
  if (pred) nastavHranu(pred);
  adresa();
  vykresli();
}

/* ------------------------------ projevy (diplomatická obrazovka) ------------------------------ */
function akce(a) {
  const cil = jm(a.target);
  const res = STATEK[a.res] || a.res || "";
  switch (a.type) {
    case "trade_offer": return `Nabídka obchodu: ${res} ${cis(a.qty)} jednotek, ${cil}, ${cis(a.price_per_unit, 2)}`;
    case "loan": return `Půjčka: ${cil}, ${cis(a.amount)}`;
    case "pressure": return `Sankce: ${cil}`;
    case "protect": return `Vojenský pakt: ${cil}`;
    case "invade": return `Invaze: ${cil}`;
    case "invest_tech": return `Investice do technologie: ${a.target ? cil : "vlastní stát"}`;
    case "invest_law": return `Investice do institucí: ${a.target ? cil : "vlastní stát"}`;
    case "invest_industry": return `Investice do průmyslu: ${a.target ? cil : "vlastní stát"}`;
    case "invest_prod": return `Investice do těžby: ${res}, ${a.target ? cil : "vlastní stát"}`;
    case "explore": return "Průzkum ložisek";
    case "arm": return `Zbrojení: ${cis(a.amount ?? 8)}`;
    case "cancel": return a.retreat ? "Ústup z války" : `Zrušení ${a.deal_id || ""}`.trim();
    case "admit": return `Nabídka členství v Unii: ${cil}`;
    case "union_fund": return `Převod z fondu Unie: ${cil}, ${cis(a.amount)}`;
    case "accept_offer": return `Přijetí nabídky ${a.offer_id || ""}`.trim();
    case "set_tariff": return `Sazba cla: ${cis((a.rate || 0) * 100, 0)} %`;
    case "declare_war": return `Vyhlášení války: ${cil}`;
    case "kapitalizace_banky": return `Kapitál bance Unie: ${cis(a.amount)}`;
    case "refinancovani": return `Refinancování dluhu: ${cil}`;
    case "moratorium": return `Moratorium na splátky: ${a.target === "vsichni" ? "všichni členové" : cil}`;
    case "zprisnit_uvery": return "Zpřísnění úvěrů kalverských bank";
    case "uvolnit_uvery": return "Uvolnění úvěrů kalverských bank";
    case "sanace_bank": return "Sanace kalverských bank";
    default: return a.type || "akce";
  }
}

function prvniVety(text, n) {
  const vety = String(text).match(/[^.!?…]+[.!?…]+(\s|$)/g) || [text];
  return { zacatek: vety.slice(0, n).join("").trim(), zbytek: vety.length > n };
}

function karta(pid, m, sn, t) {
  const barva = BARVA_HRACE[pid] || B.steel;
  const jmeno = pid === "C" ? (svet.unie || "Unie") : HRACI[pid];
  let h = `<article class="karta"><h3><span class="ctverec" style="background:${barva}"></span>${esc(jmeno)}</h3>`;
  const g = m.genre || null;
  if (g && !m.silent) {
    h += `<p class="hud">${esc(g.id === 8 ? "Stanovisko k události" : g.name)}${g.chair ? `, předsedá ${esc(g.chair)}` : ""}</p>`;
    if ((g.questions || []).length) {
      h += `<div class="otazka"><span class="hud">${g.questions.length > 1 ? "Otázky novinářů" : "Otázka novináře"}</span>` +
           g.questions.map((q) => `<p>${esc(q)}</p>`).join("") + "</div>";
    }
  }
  if (m.silent) h += '<p class="ticho">Vláda nevydala prohlášení.</p>';
  else if (m.mlci) h += `<p class="ticho">${esc(m.public_statement)} (vláda se rozhodla mlčet)</p>`;
  else h += `<p class="projev" style="border-left-color:${barva}">${esc(m.public_statement)}</p>`;
  if (m.zaloha) h += `<p class="hud">${esc(m.zaloha.poznamka || "odpověděl záložní model " + m.zaloha.model)}</p>`;
  const zapis = m.duverny_zapis || m.private_reasoning;
  if (zapis) {
    const { zacatek, zbytek } = prvniVety(zapis, 2);
    h += `<div class="zapis"><span class="hud">Důvěrný zápis vlády · soupeř nevidí</span>` +
         `<p data-cely="${esc(zapis)}">${esc(zacatek)}</p>` +
         (zbytek ? '<button type="button" class="cist-dal">Číst dál</button>' : "") + "</div>";
  }
  if (m.poznamky_pro_pristi_tah) {
    h += `<details class="spis"><summary class="hud">Poznámky do spisu</summary><p>${esc(m.poznamky_pro_pristi_tah)}</p></details>`;
  }
  const platne = (sn.actions || []).filter((a) => a.player === pid);
  const zahranicni = platne.filter((a) => a.slot !== "domestic" && a.type !== "message");
  const plog = ((sn.state || {}).private_log || {})[pid] || [];
  const odpovedi = plog.filter((r) => Number(r.turn) === t);
  if (zahranicni.length) {
    h += `<p class="popis">Akce</p><ul class="seznam">${zahranicni.map((a) => {
      const o = odpovedi.find((r) => r.npc === a.target && r.action === a.type);
      const slaby = o && ["odmitnuto", "vyrazeno", "prednost_druhe_strany"].includes(o.outcome);
      return `<li>${esc(akce(a))}${o ? stitek(VYSLEDEK[o.outcome] || o.outcome, slaby) : ""}</li>`;
    }).join("")}</ul>`;
  }
  const d = m.domestic_action;
  if (d && d.type && pid !== "C") {
    const ev = (sn.events || []).filter((e) => e.player === pid);
    const hotovo = { arm: "arm", explore: "explore" }[d.type] || `${d.type}_done`;
    const odl = ev.find((e) => (e.kind === "investment_postponed" || e.kind === "investment_cancelled") && e.type === d.type);
    const vysl = ev.some((e) => e.kind === hotovo) ? stitek("provedena") : (odl ? stitek(odl.kind === "investment_postponed" ? "odložena" : "propadla", true) : stitek("zadána"));
    h += `<p class="popis">Domácí akce</p><ul class="seznam"><li>${esc(akce(d))}${vysl}</li></ul>`;
  }
  const vyrazene = (sn.rejected || []).filter((r) => r.player === pid);
  if (vyrazene.length) {
    h += `<p class="popis">Vyřazeno rozhodčím</p><ul class="seznam">${vyrazene.map((r) =>
      `<li>${esc(r.action ? akce(r.action) : "akce")}${stitek("vyřazeno", true)} <span class="duvod">${esc(r.reason)}</span></li>`).join("")}</ul>`;
  }
  const zprava = platne.find((a) => a.type === "message") || (m.message && m.message.text ? { target: m.message.target, text: m.message.text } : null);
  if (zprava && zprava.text) h += `<p class="popis">Zpráva pro ${esc(plneJmeno(zprava.target))}</p><p>${esc(zprava.text)}</p>`;
  return h + "</article>";
}

async function projevy() {
  svet.otevreno = "projevy";
  $("projevy").hidden = false;
  $("bublina-kola").hidden = true;
  const t = svet.kolo;
  $("projevy-nadpis").textContent = `Projevy · kolo ${t}`;
  const box = $("karty");
  box.innerHTML = '<p class="ticho">Načítám kolo…</p>';
  let sn;
  try { sn = await snimek(t); } catch (e) { box.innerHTML = '<p class="chyba">Snímek kola se nepodařilo načíst.</p>'; return; }
  if (svet.kolo !== t || svet.otevreno !== "projevy") return;
  const tahy = sn.turns || {};
  const poradi = ["A", "B", "C"].filter((p) => tahy[p]);
  box.innerHTML = poradi.length ? poradi.map((p) => karta(p, tahy[p], sn, t)).join("") : '<p class="ticho">V tomto kole nikdo nejednal.</p>';
  box.querySelectorAll(".cist-dal").forEach((b) => b.addEventListener("click", () => {
    const p = b.previousElementSibling;
    p.textContent = p.dataset.cely;
    b.remove();
  }));
}

/* ------------------------------ kronika ------------------------------ */
async function kronika() {
  svet.otevreno = "kronika";
  $("kronika").hidden = false;
  $("bublina-kola").hidden = true;
  const s = radek(svet.kolo) || {};
  if (!svet.kroniky) {
    try { svet.kroniky = (await nacti("chronicle/index.json")).days || []; } catch (e) { svet.kroniky = []; }
  }
  const dny = [...svet.kroniky].sort((a, b) => Number(a.day) - Number(b.day));
  const vyber = $("kronika-den");
  if (!dny.length) { $("kronika-text").innerHTML = '<p class="ticho">Kronika ještě nevyšla; píše se po zimním kole.</p>'; vyber.hidden = true; return; }
  const k = [...dny].reverse().find((x) => Number(x.day) <= Number(s.day)) || dny[0];
  vyber.innerHTML = dny.map((x) => `<option value="${x.day}"${x === k ? " selected" : ""}>Rok ${x.day}</option>`).join("");
  vyber.hidden = false;
  vyber.onchange = () => ukazKroniku(dny.find((x) => String(x.day) === vyber.value), s);
  ukazKroniku(k, s);
}

async function ukazKroniku(k, s) {
  $("kronika-popis").textContent = Number(k.day) === Number(s.day) ? `rok ${k.day}` : `poslední hotová: rok ${k.day}`;
  try {
    const text = await nacti(`chronicle/${k.file}`);
    $("kronika-text").innerHTML = window.marked ? marked.parse(text) : `<pre>${esc(text)}</pre>`;
  } catch (e) { $("kronika-text").innerHTML = '<p class="chyba">Kroniku se nepodařilo načíst.</p>'; }
}

function zavriPrekryv() {
  $("projevy").hidden = true;
  $("kronika").hidden = true;
  svet.otevreno = null;
}

/* ------------------------------ interakce ------------------------------ */
const paprsek = new THREE.Raycaster();
function zasah(ev) {
  const r = renderer.domElement.getBoundingClientRect();
  const v = new THREE.Vector2(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1);
  paprsek.setFromCamera(v, camera);
  const objekty = [];
  for (const u of svet.uzemi.values()) {
    objekty.push(u.mesh, u.mesto);
    if (u.prsten.visible) objekty.push(u.prstenKlik);
  }
  const z = paprsek.intersectObjects(objekty, false)[0];
  return z ? z.object.userData : null;
}

function tooltip(id, x, y) {
  const t = $("tooltip");
  if (!id) { t.hidden = true; return; }
  const u = svet.uzemi.get(id);
  const st = u.st || {};
  const status = id in HRACI ? "velmoc" : (STATUS[st.status] || st.status || "");
  const vliv = id in HRACI ? "–" : `${cis((st.influence || {}).A)} / ${cis((st.influence || {}).B)}`;
  t.innerHTML = `<b>${esc(plneJmeno(id))}</b>` +
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
  svet.vybrany = id;
  if (pred && pred !== id) nastavHranu(pred);
  nastavHranu(id);
  panelStatu(id);
  vykresli();
}

function pozice(id) {
  const p = svet.uzemi.get(id).mesto.position.clone().project(camera);
  const r = renderer.domElement.getBoundingClientRect();
  return [r.left + (p.x + 1) / 2 * r.width, r.top + (1 - p.y) / 2 * r.height];
}

function napojInterakce() {
  const el = renderer.domElement;
  let dolu = null;
  el.addEventListener("pointermove", (ev) => {
    if (ev.pointerType !== "mouse") return;
    const z = zasah(ev);
    const id = z ? z.id : null;
    if (id !== svet.hover) zvyrazni(id);
    tooltip(id, ev.clientX, ev.clientY);
    el.style.cursor = id ? "pointer" : "";
  });
  el.addEventListener("pointerleave", () => { zvyrazni(null); tooltip(null); });
  el.addEventListener("pointerdown", (ev) => { dolu = [ev.clientX, ev.clientY]; });
  el.addEventListener("pointerup", (ev) => {
    if (!dolu || Math.hypot(ev.clientX - dolu[0], ev.clientY - dolu[1]) > 5) { dolu = null; return; }
    dolu = null;
    const z = zasah(ev);
    tooltip(null);
    if (!z) { if (svet.panel) zavriPanel(); return; }   // klik mimo zavře panel
    if (z.druh === "prsten") { projevy(); return; }      // prstenec města A, B a členů Unie otevře projevy
    vyber(z.id);
  });
  // klávesnice: Tab prochází území v pořadí map.json, Enter = klik
  const box = $("klavesnice");
  for (const r of svet.mapa.regions) {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = plneJmeno(r.id);
    b.addEventListener("focus", () => { zvyrazni(r.id); const [x, y] = pozice(r.id); tooltip(r.id, x, y); });
    b.addEventListener("blur", () => { zvyrazni(null); tooltip(null); });
    b.addEventListener("click", () => vyber(r.id));
    box.appendChild(b);
  }
  $("bublina-kola").addEventListener("click", () => { $("bublina-kola").hidden = true; });
  $("o-projevy").addEventListener("click", projevy);
  $("o-kronika").addEventListener("click", kronika);
  document.querySelectorAll(".zavrit-prekryv").forEach((b) => b.addEventListener("click", zavriPrekryv));
  $("p-zpet").addEventListener("click", () => posun(-1));
  $("p-dal").addEventListener("click", () => posun(1));
  document.addEventListener("keydown", (ev) => {
    if (ev.key !== "Escape" || document.getElementById("bublina")) return;   // nejdřív se zavře vysvětlivka
    if (svet.otevreno) zavriPrekryv();
    else if (svet.panel) zavriPanel();
  });
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
  // stav v URL: #kolo=11&stat=N3, pro screenshoty navíc zoom=2&na=A a otevri=projevy|kronika
  const h = new URLSearchParams(location.hash.slice(1));
  const kolo = Number(h.get("kolo")) || Number(p.max);
  if (h.get("na") && Number(h.get("zoom"))) priblizNa(h.get("na"), Math.min(2.5, Math.max(0.7, Number(h.get("zoom")))));
  popiskyPodleZoomu();
  zobraz(Math.min(Number(p.max), Math.max(Number(p.min), kolo)));
  if (h.get("stat") && svet.uzemi.has(h.get("stat"))) vyber(h.get("stat"));
  if (h.get("otevri") === "projevy") await projevy();
  if (h.get("otevri") === "kronika") await kronika();
  window.ARDAN_3D_HOTOVO = true;
}

start();
