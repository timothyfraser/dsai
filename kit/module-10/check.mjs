// check.mjs
// The checks for this module's front door, run in a real headless browser with Playwright.
// Course kit, module 10

// One-time install, from this folder (a student laptop needs both):
//   npm install playwright          gets Playwright, the tool that drives a real browser from a script
//   npx playwright install chromium downloads the browser Playwright will drive
// Usage, from this folder:
//   EDGE_STUB=1 node check.mjs     fake on-device model, no download (what CI runs)
//   node check.mjs                 the real on-device model (needs the network for the first load)
// The team API is never called: page.route() stands in for it, so the checks can make it
// answer, fail, go slow, or vanish on purpose. Five checks:
//   1. the page starts
//   2. the API's answer is shown and labelled as the server's
//   3. with the API down (HTTP 500), the page still answers, labelled "on device"
//   4. with the API too slow, the page gives up on it within its timeout and answers on device
//   5. with the network off, after the first load, a reload still opens and still answers

// 0. SETUP ###################################

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
const KIT = path.dirname(HERE);   // serve kit/, so ../module-20/edge.js resolves
const STUB = process.env.EDGE_STUB === "1";
const TIMEOUT_MS = 1500;          // the page's API timeout for these checks (?timeout=)
const TYPES = { ".html": "text/html", ".js": "text/javascript", ".mjs": "text/javascript", ".json": "application/json" };

// 1. SERVE THE KIT FOLDER ON A LOCAL PORT ###################################

const server = http.createServer((req, res) => {
  const p = decodeURIComponent(new URL(req.url, "http://x").pathname);
  const file = path.join(KIT, p.endsWith("/") ? p + "index.html" : p);
  if (!file.startsWith(KIT) || !fs.existsSync(file)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { "content-type": TYPES[path.extname(file)] || "application/octet-stream" });
  fs.createReadStream(file).pipe(res);
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const base = "http://127.0.0.1:" + server.address().port + "/module-10/";
const url = base + "?api=/api/ask&timeout=" + TIMEOUT_MS + (STUB ? "&stub=1" : "");

let failed = 0;
const check = (n, label, ok, detail) => {
  console.log((ok ? "PASS" : "FAIL") + "  check " + n + ": " + label + (detail ? "  (" + detail + ")" : ""));
  if (!ok) failed++;
};

const browser = await chromium.launch();
const context = await browser.newContext();
const page = await context.newPage();
const loadMs = STUB ? 15000 : 600000;  // a real first load of the model downloads a few hundred MB

// 2. THE FAKE API: change how it behaves before each check ###################################

// mode is one of "ok", "down", "slow". The page sends POST /api/ask with {"question": "..."}.
let mode = "ok";
await page.route("**/api/ask", async (route) => {
  if (mode === "down") return route.fulfill({ status: 500, contentType: "application/json", body: '{"detail":"server error"}' });
  if (mode === "slow") await new Promise((r) => setTimeout(r, TIMEOUT_MS + 2000));
  const q = JSON.parse(route.request().postData() || "{}").question || "";
  return route.fulfill({ status: 200, contentType: "application/json",
    body: JSON.stringify({ answer: "Server answer to: " + q, source: "team-api" }) }).catch(() => {});
});

// Ask one question and read back what the page showed.
async function askQ(q) {
  await page.fill("#q", q);
  await page.click("#ask");
  await page.waitForFunction(() => document.querySelector("#out").dataset.kind, null, { timeout: loadMs });
  const r = await page.evaluate(() => ({
    kind: document.querySelector("#out").dataset.kind,
    text: document.querySelector("#out").textContent,
    path: document.querySelector("#path").textContent,
    ms: parseInt(document.querySelector("#ms").textContent, 10),
  }));
  await page.evaluate(() => { delete document.querySelector("#out").dataset.kind; });
  return r;
}

// 3. THE CHECKS ###################################

try {
  console.log("mode: " + (STUB ? "stub (fake on-device model)" : "real on-device model") + "; API: mocked with page.route; API timeout " + TIMEOUT_MS + " ms");

  await page.goto(url);
  await page.waitForFunction(() => document.body.dataset.ready, null, { timeout: 15000 });
  check(1, "page starts", (await page.evaluate(() => document.body.dataset.ready)) === "1", await page.textContent("#status"));

  mode = "ok";
  const a = await askQ("Where is the spare pump?");
  check(2, "API answer shown, labelled as the server's",
    a.kind === "server" && a.text.includes("Server answer to: Where is the spare pump?") && a.path === "the team server",
    a.path + ", " + a.ms + " ms: " + a.text.slice(0, 60));

  mode = "down";
  const b = await askQ("Where is the spare pump?");
  check(3, "API down (HTTP 500): still answers, labelled on device",
    b.kind === "device" && b.text.startsWith("On device:") && b.path === "on device",
    b.path + ", " + b.ms + " ms: " + b.text.slice(0, 60));

  mode = "slow";
  const c = await askQ("How do I reset the sensor?");
  check(4, "API too slow: gives up within the timeout and answers on device",
    c.kind === "device" && c.ms < TIMEOUT_MS + 1000 + (STUB ? 0 : 60000),
    c.path + ", " + c.ms + " ms");

  // First load is done; make sure the offline model is saved, then cut the network.
  await page.click("#prep");
  await page.waitForFunction(() => document.body.dataset.device, null, { timeout: loadMs });
  await page.waitForFunction(() => navigator.serviceWorker && navigator.serviceWorker.ready.then(() => true), null, { timeout: 10000 });
  await page.reload();  // second load: now the service worker controls the page
  await page.waitForFunction(() => document.body.dataset.ready, null, { timeout: 15000 });
  await page.unroute("**/api/ask");
  await context.setOffline(true);
  await page.reload();
  await page.waitForFunction(() => document.body.dataset.ready, null, { timeout: 15000 });
  const d = await askQ("Where is the spare pump?");
  check(5, "network off after first load: reload opens and still answers on device",
    d.kind === "device" && d.text.startsWith("On device:"), d.path + ", " + d.ms + " ms");
} catch (err) {
  check("x", "the check script itself ran", false, err.message.split("\n")[0]);
} finally {
  await browser.close();
  server.close();
}
console.log(failed ? "RESULT: " + failed + " check(s) failed" : "RESULT: all checks passed");
process.exit(failed ? 1 : 0);
