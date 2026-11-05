// check.mjs: the lab's checks, run in a real headless browser with Playwright.
// One-time install, from this folder:  npm install playwright   then   npx playwright install chromium
//   EDGE_STUB=1 node check.mjs      fake model, no network needed (what CI runs)
//   node check.mjs                  the real model (needs the network for the first load)
// Your written decision on MIN_SCORE and TIME_BUDGET_MS has its own check: node decision.mjs
// It serves the kit folder on a local port (the engine is ../module-10/edge.js), opens the page, and runs four checks:
//   1. the page starts and reports its engine
//   2. a question inside the notes gets an answer, with its source, within the time budget
//   3. a question outside the notes is refused
//   4. with the network cut off, a reload still works and still answers
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
const KIT = path.dirname(HERE);   // serve kit/, so ../module-10/edge.js (the shared engine) resolves
// The time budget is read from app.js, so the check tests the number you chose, not a copy of it.
const BUDGET_MS = Number(fs.readFileSync(path.join(HERE, "app.js"), "utf8").match(/const TIME_BUDGET_MS = (\d+)/)[1]);
const TYPES = { ".html": "text/html", ".js": "text/javascript", ".mjs": "text/javascript", ".json": "application/json" };

const server = http.createServer((req, res) => {
  const p = decodeURIComponent(new URL(req.url, "http://x").pathname);
  const file = path.join(KIT, p.endsWith("/") ? p + "index.html" : p);
  if (!file.startsWith(KIT) || !fs.existsSync(file)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { "content-type": TYPES[path.extname(file)] || "application/octet-stream" });
  fs.createReadStream(file).pipe(res);
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const url = "http://127.0.0.1:" + server.address().port + "/module-20/" + (STUB ? "?stub=1" : "");

let failed = 0;
const check = (n, label, ok, detail) => {
  console.log((ok ? "PASS" : "FAIL") + "  check " + n + ": " + label + (detail ? "  (" + detail + ")" : ""));
  if (!ok) failed++;
};

const browser = await chromium.launch();
const context = await browser.newContext();
const page = await context.newPage();
const loadMs = STUB ? 15000 : 600000;  // a real first load downloads the model

async function askQ(q) {
  await page.fill("#q", q);
  await page.click("#ask");
  await page.waitForFunction(() => document.querySelector("#out").dataset.kind, null, { timeout: BUDGET_MS + 5000 });
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
  console.log("mode: " + (STUB ? "stub (fake model)" : "real model") + "; WebGPU adapter in this browser: " + (gpu ? "yes" : "no, WASM path"));

  await page.goto(url);
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
} catch (err) {
  check("x", "the check script itself ran", false, err.message.split("\n")[0]);
} finally {
  await browser.close();
  server.close();
}
console.log(failed ? "RESULT: " + failed + " check(s) failed" : "RESULT: all checks passed");
process.exit(failed ? 1 : 0);
