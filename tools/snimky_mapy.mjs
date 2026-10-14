// tools/snimky_mapy.mjs
// Screenshoty 3D mapy (web/mapa.html) ve velikosti okna, s WebGL přes softwarový SwiftShader.
// Odvozeno z tools/snimky_webu.mjs.
// Spustí Edge bez okna s ladicím portem, přes protokol DevTools nastaví šířku zařízení, načte stránku
// a uloží PNG do tools/screens/. Web musí běžet na lokálním serveru (např. python -m http.server 8765).
//
//   node tools/snimky_mapy.mjs http://localhost:8765/web/
//
import { spawn } from "node:child_process";
import { writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { tmpdir } from "node:os";

const ZAKLAD = process.argv[2] || "http://localhost:8765/web/";
const EDGE = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
const PORT = 9333;
const VYSTUP = join(dirname(fileURLToPath(import.meta.url)), "screens");
const SNIMKY = [];
for (const [s, w, h, mobil] of [["1440", 1440, 900, false], ["390", 390, 844, true]]) {
  SNIMKY.push([`mapa3d-${s}-vychozi-k11`, "mapa.html#kolo=11", w, h, mobil]);
  SNIMKY.push([`mapa3d-${s}-vychozi-k1`, "mapa.html#kolo=1", w, h, mobil]);
  SNIMKY.push([`mapa3d-${s}-kalvera-2x-k11`, "mapa.html#kolo=11&zoom=2&na=A", w, h, mobil]);
}

const pockej = (ms) => new Promise((r) => setTimeout(r, ms));
mkdirSync(VYSTUP, { recursive: true });
const edge = spawn(EDGE, ["--headless=new", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--hide-scrollbars",
  `--remote-debugging-port=${PORT}`,
  `--user-data-dir=${join(tmpdir(), "ardan-snimky-mapy")}`, "about:blank"], { stdio: "ignore" });
let cil = null;
for (let i = 0; i < 40 && !cil; i++) {
  await pockej(250);
  try { cil = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === "page"); } catch (e) { /* jeste nebezi */ }
}
if (!cil) { console.error("Edge se nespustil"); edge.kill(); process.exit(1); }
const ws = new WebSocket(cil.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener("open", r, { once: true }));
let id = 0;
const cekajici = new Map();
ws.addEventListener("message", (ev) => {
  const m = JSON.parse(ev.data);
  if (m.id && cekajici.has(m.id)) { cekajici.get(m.id)(m); cekajici.delete(m.id); }
});
const cdp = (method, params = {}) => new Promise((r) => { id += 1; cekajici.set(id, r); ws.send(JSON.stringify({ id, method, params })); });

await cdp("Page.enable");
for (const [jmeno, stranka, sirka, vyska, mobil] of SNIMKY) {
  await cdp("Emulation.setDeviceMetricsOverride", { width: sirka, height: vyska, deviceScaleFactor: 1, mobile: mobil });
  await cdp("Page.navigate", { url: "about:blank" });
  await pockej(300);
  await cdp("Page.navigate", { url: ZAKLAD + stranka });
  let hotovo = false;
  for (let i = 0; i < 40 && !hotovo; i++) {
    await pockej(250);
    const r = await cdp("Runtime.evaluate", { expression: "Boolean(window.ARDAN_3D_HOTOVO)", returnByValue: true });
    hotovo = r.result.result.value;
  }
  await pockej(1500);   // přechod barev 400 ms, písma a stíny
  const sw = await cdp("Runtime.evaluate", { expression: "document.documentElement.scrollWidth", returnByValue: true });
  const s = await cdp("Page.captureScreenshot", { format: "png" });
  writeFileSync(join(VYSTUP, `${jmeno}.png`), Buffer.from(s.result.data, "base64"));
  console.log(`${jmeno}.png  ${sirka} x ${vyska} px, mapa hotová: ${hotovo}, šířka obsahu ${sw.result.result.value} px`);
}
ws.close();
edge.kill();
