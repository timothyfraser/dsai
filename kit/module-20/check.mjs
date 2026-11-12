// check.mjs: the lab's checks, run in a real headless browser with Playwright.
// One-time install, from this folder:  npm install playwright   then   npx playwright install chromium
//   EDGE_STUB=1 node check.mjs      fake model, no network needed (what CI runs)
//   node check.mjs                  the real model (needs the network for the first load)
//   EDGE_MODEL=light opens every page with ?model=light, so the whole check runs on the lighter route.
//   EDGE_BROWSER=chrome (or msedge) runs your installed browser; a real-model run needs it, because the bundled headless browser has no graphics adapter.
// Your written decision on MIN_SCORE and TIME_BUDGET_MS has its own check: node decision.mjs
// It serves the kit folder on a local port (the engine is ../module-10/edge.js), opens the page, and runs seven checks:
//   1. the page starts and reports its engine
//   2. a question inside the notes gets an answer, with its source, within the time budget
//   3. a question outside the notes is refused
//   4. with the network cut off, a reload still works and still answers
//   5. the question about the bottle label reaches the labelling note, n4
//   6. with WebGPU removed, the page says to use Google Chrome, loads no model, and still shows the matching note
//   7. the page names the model it runs: the lighter-route line with ?model=light, the default-route line without
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

// Load Playwright: first from a normal install (npm install playwright), then, only if you set
// PW_REQUIRE to a folder that holds it, from there.
const here = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = here("playwright")); }
catch (e) {
  if (!process.env.PW_REQUIRE) {
    console.error("Playwright is not installed. Run:  npm install playwright   then:  npx playwright install chromium");
    process.exit(1);
  }
  ({ chromium } = createRequire(process.env.PW_REQUIRE)("playwright"));
}
const HERE = path.dirname(fileURLToPath(import.meta.url));
const STUB = process.env.EDGE_STUB === "1";
const LIGHT = process.env.EDGE_MODEL === "light";
const KIT = path.dirname(HERE);   // serve kit/, so ../module-10/edge.js (the shared engine) resolves
// The time budget is read from app.js, so the check tests the number you chose, not a copy of it.
const BUDGET_MS = Number(fs.readFileSync(path.join(HERE, "app.js"), "utf8").match(/const TIME_BUDGET_MS = (\d+)/)[1]);
const TYPES = { ".html": "text/html", ".js": "text/javascript", ".mjs": "text/javascript", ".json": "application/json" };

const server = http.createServer((req, res) => {
  const p = decodeURIComponent(new URL(req.url, "http://x").pathname);
  const file = path.join(KIT, p.endsWith("/") ? p + "index.html" : p);
  if (!file.startsWith(KIT) || !fs.existsSync(file)) { res.writeHead(404); return res.end(); }
  // These two headers let the page use the browser's full speed features (shared memory) for the model.
  res.writeHead(200, { "content-type": TYPES[path.extname(file)] || "application/octet-stream",
    "cross-origin-opener-policy": "same-origin", "cross-origin-embedder-policy": "credentialless" });
  fs.createReadStream(file).pipe(res);
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const base = "http://127.0.0.1:" + server.address().port + "/module-20/" + (STUB ? "?stub=1" : "");
const url = base + (LIGHT ? (STUB ? "&" : "?") + "model=light" : "");

let failed = 0;
const check = (n, label, ok, detail) => {
  console.log((ok ? "PASS" : "FAIL") + "  check " + n + ": " + label + (detail ? "  (" + detail + ")" : ""));
  if (!ok) failed++;
};

const browser = await chromium.launch(process.env.EDGE_BROWSER ? { channel: process.env.EDGE_BROWSER } : {});
const context = await browser.newContext();
const loadMs = STUB ? 15000 : 900000;   // a real first load downloads about 760 MB
const replyMs = STUB ? 15000 : 240000;  // one real reply, on a slow device
context.setDefaultTimeout(replyMs);
const page = await context.newPage();

async function askQ(q) {
  await page.fill("#q", q);
  await page.click("#ask");
  await page.waitForFunction(() => document.querySelector("#out").dataset.kind, null, { timeout: Math.max(BUDGET_MS + 5000, replyMs) });
  const r = await page.evaluate(() => ({
    kind: document.querySelector("#out").dataset.kind,
    text: document.querySelector("#out").textContent,
    ms: parseInt(document.querySelector("#ms").textContent, 10),
  }));
  await page.evaluate(() => { delete document.querySelector("#out").dataset.kind; });
  return r;
}

try {
  const gpu = await page.evaluate(async () => !!(navigator.gpu && (await navigator.gpu.requestAdapter().catch(() => null))));
  console.log("mode: " + (STUB ? "stub (fake model)" : "real model") + "; route: " + (LIGHT ? "lighter model" : "default model") + "; WebGPU adapter in this browser: " + (gpu ? "yes" : "no"));

  await page.goto(url, { timeout: loadMs });
  await page.waitForFunction(() => document.body.dataset.ready, null, { timeout: loadMs });
  const ready = await page.evaluate(() => document.body.dataset.ready);
  const device = await page.textContent("#device");
  check(1, "page starts and names its engine", ready === "1", "engine: " + device);
  if (ready !== "1") throw new Error("page did not start: " + (await page.textContent("#status")));

  const a = await askQ("How do I take a water sample from the stream?");
  check(2, "in-scope question answered with a source, within " + BUDGET_MS / 1000 + " s",
    a.kind === "answer" && /\[n\d+\]/.test(a.text) && a.ms <= BUDGET_MS, a.kind + ", " + a.ms + " ms: " + a.text.slice(0, 70));

  const b = await askQ("Who won the football game last night?");
  check(3, "out-of-scope question refused", b.kind === "refused", b.text.slice(0, 60));

  await page.waitForFunction(() => navigator.serviceWorker && navigator.serviceWorker.ready.then(() => true), null, { timeout: 10000 });
  await page.reload();  // second load: now the service worker controls the page
  await page.waitForFunction(() => document.body.dataset.ready, null, { timeout: loadMs });
  await context.setOffline(true);
  await page.reload();
  await page.waitForFunction(() => document.body.dataset.ready, null, { timeout: loadMs });
  const c = await askQ("What should I write on the bottle label?");
  check(4, "works offline after first load", c.kind === "answer", c.kind + ", " + c.ms + " ms");

  // The stub model names the note it was given, so the source tag shows which note the matcher picked.
  await context.setOffline(false);
  const d = await askQ("What should I write on the bottle label?");
  check(5, "the bottle label question reaches the labelling note", /\[n4\]/.test(d.text), d.kind + ": " + d.text.slice(0, 70));

  // No graphics path: the page says to use Google Chrome, starts no model, and still shows the matching note.
  const g = await context.newPage();
  await g.addInitScript(() => {
    delete Navigator.prototype.gpu;
    window.__workers = 0; const W = window.Worker;
    window.Worker = class extends W { constructor(...a) { super(...a); window.__workers++; } };
  });
  await g.goto(url, { timeout: loadMs });
  await g.waitForFunction(() => document.body.dataset.ready, null, { timeout: loadMs });
  await g.fill("#q", "What should I write on the bottle label?");
  await g.click("#ask");
  await g.waitForFunction(() => document.querySelector("#out").dataset.kind, null, { timeout: 5000 });
  const n = await g.evaluate(() => ({ status: document.querySelector("#status").textContent, out: document.querySelector("#out").textContent, workers: window.__workers }));
  const chromeLine = "This page needs Google Chrome with graphics acceleration on. Open it in Chrome to run the model.";
  check(6, "No WebGPU: the page says to use Google Chrome, loads no model, still shows the matching note",
    n.status.startsWith(chromeLine) && n.workers === 0 && n.out.includes("Label every bottle"), "workers started: " + n.workers + "; " + n.out.slice(0, 60));

  // The route line under the status names the model in use, and links to the other route.
  const route = async (u) => {
    const r = await context.newPage();
    await r.goto(u, { timeout: loadMs });
    await r.waitForFunction(() => document.body.dataset.ready, null, { timeout: loadMs });
    const v = await r.evaluate(() => ({ text: document.querySelector("#route").textContent, link: document.querySelector("#route a")?.getAttribute("href") || "" }));
    await r.close();
    return v;
  };
  const lt = await route(base + (STUB ? "&" : "?") + "model=light"), df = await route(base);
  check(7, "the page names its model: lighter-route line with ?model=light, the default-route line without",
    lt.text.startsWith("Running the lighter model, LFM2 350M (Liquid AI). It breaks the reply format more often than the default, and a company with $10 million or more in revenue needs a licence from Liquid AI to use it.") && lt.text.endsWith("Back to the default model") && !lt.link.includes("model=light") &&
    df.text === "Short on memory? Load the lighter model." && df.link.includes("model=light") && (!STUB || df.link.includes("stub=1")) && !df.text.includes("LFM2"),
    "light: " + lt.text.slice(0, 40) + "...; default: " + df.text);
} catch (err) {
  check("x", "the check script itself ran", false, err.message.split("\n")[0]);
} finally {
  await browser.close();
  server.close();
}
console.log(failed ? "RESULT: " + failed + " check(s) failed" : "RESULT: all checks passed");
process.exit(failed ? 1 : 0);
