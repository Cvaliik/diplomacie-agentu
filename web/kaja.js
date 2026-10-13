/* Ardan, hra od Kája Industries: společné skripty stránek (značka, síť hvězd, vysvětlivky). */
"use strict";

/* Logo a monogram se vkládají jako živé SVG (text v písmu Saira), až po načtení odkazu na Google Fonts.
   Každá kopie dostane vlastní předponu id, aby se gradienty a ořezy dvou kopií nepletly. */
async function vlozSvg(prvek) {
  try {
    const r = await fetch(prvek.dataset.svg);
    if (!r.ok) return;
    const pref = prvek.dataset.prefix || "x";
    let svg = await r.text();
    svg = svg.replace(/\bid="([^"]+)"/g, `id="${pref}-$1"`).replace(/url\(#([^)]+)\)/g, `url(#${pref}-$1)`);
    prvek.innerHTML = svg;
    const s = prvek.querySelector("svg");
    if (s) { s.removeAttribute("width"); s.removeAttribute("height"); s.setAttribute("aria-hidden", "true"); s.setAttribute("focusable", "false"); }
  } catch (e) { /* bez loga stránka funguje dál */ }
}

/* Síť hvězd (plexus) jen v pozadí hlavičky: pevné semínko, bez animace, nejvýš 3 spojení na hvězdu,
   linie 0,75 px, krytí 15 až 40 %. Radiální masku a umístění mimo text řeší CSS (.plexus). */
function plexus(svg) {
  if (!svg) return;
  const W = 600, H = 190, N = 46;
  let seme = 20261011;
  const nahoda = () => { seme = (seme * 1103515245 + 12345) % 2147483648; return seme / 2147483648; };
  const body = Array.from({ length: N }, () => [nahoda() * W, nahoda() * H]);
  const ns = "http://www.w3.org/2000/svg";
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.setAttribute("preserveAspectRatio", "xMidYMid slice");
  const stupen = new Array(N).fill(0);
  const hrany = [];
  for (let i = 0; i < N; i++) {
    const blizke = body.map((b, j) => [j, Math.hypot(b[0] - body[i][0], b[1] - body[i][1])])
      .filter(([j]) => j !== i).sort((a, b) => a[1] - b[1]).slice(0, 3);
    for (const [j, d] of blizke) {
      if (stupen[i] >= 3 || stupen[j] >= 3 || d > 120 || hrany.some(([a, b]) => (a === j && b === i))) continue;
      hrany.push([i, j]); stupen[i]++; stupen[j]++;
    }
  }
  for (const [i, j] of hrany) {
    const l = document.createElementNS(ns, "line");
    l.setAttribute("x1", body[i][0].toFixed(1)); l.setAttribute("y1", body[i][1].toFixed(1));
    l.setAttribute("x2", body[j][0].toFixed(1)); l.setAttribute("y2", body[j][1].toFixed(1));
    l.setAttribute("opacity", (0.15 + nahoda() * 0.25).toFixed(2));
    svg.appendChild(l);
  }
  for (const [x, y] of body) {
    const c = document.createElementNS(ns, "circle");
    c.setAttribute("cx", x.toFixed(1)); c.setAttribute("cy", y.toFixed(1));
    c.setAttribute("r", (0.8 + nahoda() * 0.9).toFixed(2));
    c.setAttribute("opacity", (0.2 + nahoda() * 0.2).toFixed(2));
    svg.appendChild(c);
  }
}

function kajaZnacka() {
  document.querySelectorAll("[data-svg]").forEach(vlozSvg);
  plexus(document.getElementById("plexus"));
}

/* ------------------------------ vysvětlivky „?“ (slovnik.js) ------------------------------ */

function textPojmu(pojem) {
  if (pojem === "fáze") {
    const c = window.ARDAN_CYKLUS;
    return c ? [c.uvod, ...Object.values(c.faze)].join(" ") : "";
  }
  return window.ardanPojem ? window.ardanPojem(pojem) : "";
}

function zavriBublinu() {
  const b = document.getElementById("bublina");
  if (b) b.remove();
  document.querySelectorAll('.vys[aria-expanded="true"]').forEach((x) => x.setAttribute("aria-expanded", "false"));
}

function ukazBublinu(tl) {
  const otevrena = tl.getAttribute("aria-expanded") === "true";
  zavriBublinu();
  if (otevrena) return;   // další klik na tentýž znak bublinu zavře
  const pojem = tl.dataset.pojem;
  const b = document.createElement("div");
  b.id = "bublina";
  b.setAttribute("role", "note");
  const e = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  b.innerHTML = `<b>${e(pojem)}</b>: ${e(textPojmu(pojem))}`;
  document.body.appendChild(b);
  const r = tl.getBoundingClientRect();
  const sirka = b.offsetWidth;
  const vlevo = Math.max(8, Math.min(r.left + window.scrollX, window.scrollX + document.documentElement.clientWidth - sirka - 8));
  b.style.left = vlevo + "px";
  b.style.top = (r.bottom + window.scrollY + 6) + "px";
  tl.setAttribute("aria-expanded", "true");
}

document.addEventListener("click", (ev) => {
  const tl = ev.target.closest(".vys");
  if (tl) { ev.stopPropagation(); ev.preventDefault(); ukazBublinu(tl); return; }
  if (!ev.target.closest("#bublina")) zavriBublinu();
}, true);
document.addEventListener("keydown", (ev) => { if (ev.key === "Escape") zavriBublinu(); });
window.addEventListener("resize", zavriBublinu);
