// tools/snimky_webu.mjs
// Celostránkové screenshoty webu v přesných šířkách (i pod 500 px, které bezhlavý Edge sám neumí).
// Spustí Edge bez okna s ladicím portem, přes protokol DevTools nastaví šířku zařízení, načte stránku
// a uloží PNG do tools/screens/. Web musí běžet na lokálním serveru (např. python -m http.server 8765).
//
//   node tools/snimky_webu.mjs http://localhost:8765/web/
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
const SNIMKY = [
  ["index-1440", "index.html", 1440, false], ["index-1024", "index.html", 1024, false], ["index-390", "index.html", 390, true],
  ["o-hre-1440", "o-hre.html", 1440, false], ["o-hre-390", "o-hre.html", 390, true]
];

const pockej = (ms) => new Promise((r) => setTimeout(r, ms));
mkdirSync(VYSTUP, { recursive: true });
const edge = spawn(EDGE, ["--headless=new", "--disable-gpu", "--hide-scrollbars", `--remote-debugging-port=${PORT}`,
  `--user-data-dir=${join(tmpdir(), "ardan-snimky-edge")}`, "about:blank"], { stdio: "ignore" });
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
for (const [jmeno, stranka, sirka, mobil] of SNIMKY) {
  await cdp("Emulation.setDeviceMetricsOverride", { width: sirka, height: 900, deviceScaleFactor: 1, mobile: mobil });
  await cdp("Page.navigate", { url: ZAKLAD + stranka });
  await pockej(4000);   // data hry, písma a logo
  const m = await cdp("Page.getLayoutMetrics");
  const vyska = Math.ceil(m.result.cssContentSize.height);
  const sw = await cdp("Runtime.evaluate", { expression: "document.documentElement.scrollWidth", returnByValue: true });
  const s = await cdp("Page.captureScreenshot", { format: "png", captureBeyondViewport: true,
    clip: { x: 0, y: 0, width: sirka, height: vyska, scale: 1 } });
  writeFileSync(join(VYSTUP, `${jmeno}.png`), Buffer.from(s.result.data, "base64"));
  console.log(`${jmeno}.png  ${sirka} x ${vyska} px, šířka obsahu ${sw.result.result.value} px`);
}
ws.close();
edge.kill();
