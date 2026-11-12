// check.mjs
// The checks for this module's browser page, run in a real headless browser with Playwright.
// Course kit, module 10

// One-time install, from this folder (a student laptop needs both):
//   npm install playwright          gets Playwright, the tool that drives a real browser from a script
//   npx playwright install chromium downloads the browser Playwright will drive
// Usage, from this folder:
//   EDGE_STUB=1 node check.mjs     fake browser model, no download (what CI runs)
//   node check.mjs                 the real model (needs the network for the first load)
//   EDGE_MODEL=light opens every page with ?model=light, so the whole check runs on the lighter route.
//   EDGE_BROWSER=chrome (or msedge) runs your installed browser; a real-model run needs it, because the bundled headless browser has no graphics adapter.
// The team API is never called: page.route() stands in for it, so the checks can make it
// answer, fail, go slow, or vanish on purpose. Nine checks:
//   C1 the page starts and names its engine
//   C2 the server's answer is shown and labelled as the server's
//   C3 with WebGPU removed, the page says to use Google Chrome and loads no model
//   C4 with the built-in model present it is used; with it removed the page falls back and says which path
//   C5 for each state in rules.json (server down, slow, offline) the path that answered matches the rule
//   C6 with the network off, after one visit, a reload still opens and answers (or says plainly it cannot)
//   C7 no file the page served holds anything that looks like a key
//   C8 measures.json parses and holds at least two devices with every number
//   C9 the page names the model it runs: the lighter-route line with ?model=light, the default-route line without

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
const KIT = path.dirname(HERE);   // serve kit/, the folder Module 20 shares this engine from
const STUB = process.env.EDGE_STUB === "1";
const LIGHT = process.env.EDGE_MODEL === "light";
const TIMEOUT_MS = 1500;          // the page's API timeout for these checks (?timeout=)
const RULES = JSON.parse(fs.readFileSync(path.join(HERE, "rules.json"), "utf8"));
const TYPES = { ".html": "text/html", ".js": "text/javascript", ".mjs": "text/javascript", ".json": "application/json" };

// 1. SERVE THE KIT FOLDER ON A LOCAL PORT, and remember every file it served (for C7) ###################################

const served = new Set();
const server = http.createServer((req, res) => {
  const p = decodeURIComponent(new URL(req.url, "http://x").pathname);
  const file = path.join(KIT, p.endsWith("/") ? p + "index.html" : p);
  if (!file.startsWith(KIT) || !fs.existsSync(file)) { res.writeHead(404); return res.end(); }
  served.add(file);
  // These two headers let the page use the browser's full speed features (shared memory) for the model.
  res.writeHead(200, { "content-type": TYPES[path.extname(file)] || "application/octet-stream",
    "cross-origin-opener-policy": "same-origin", "cross-origin-embedder-policy": "credentialless" });
  fs.createReadStream(file).pipe(res);
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const base = "http://127.0.0.1:" + server.address().port + "/module-10/?api=/api/ask&timeout=" + TIMEOUT_MS + (STUB ? "&stub=1" : "");
const url = base + (LIGHT ? "&model=light" : "");

let failed = 0;
const check = (n, label, ok, detail) => {
  console.log((ok ? "PASS" : "FAIL") + "  C" + n + ": " + label + (detail ? "  (" + detail + ")" : ""));
  if (!ok) failed++;
};

const browser = await chromium.launch(process.env.EDGE_BROWSER ? { channel: process.env.EDGE_BROWSER } : {});
const loadMs = STUB ? 15000 : 900000;   // a real first load of the model downloads about 760 MB
const replyMs = STUB ? 15000 : 240000;  // one real reply, on a slow device

// 2. THE FAKE API, AND ONE FRESH BROWSER PER CASE ###################################

// mode is one of "ok", "down", "slow", "gone" (no reply at all, as with no network). The page sends POST /api/ask with {"question": "..."}.
let mode = "ok";
// init is a script run in the page before its own code: how a check removes a browser feature.
async function open(init) {
  const context = await browser.newContext();
  context.setDefaultTimeout(replyMs);
  if (init) await context.addInitScript(init);
  const page = await context.newPage();
  await page.route("**/api/ask", async (route) => {
    if (mode === "gone") return route.abort("internetdisconnected");
    if (mode === "down") return route.fulfill({ status: 500, contentType: "application/json", body: '{"detail":"server error"}' });
    if (mode === "slow") await new Promise((r) => setTimeout(r, TIMEOUT_MS + 2000));
    const q = JSON.parse(route.request().postData() || "{}").question || "";
    return route.fulfill({ status: 200, contentType: "application/json",
      body: JSON.stringify({ answer: "Server answer to: " + q, source: "team-api" }) }).catch(() => {});
  });
  await page.goto(url, { timeout: loadMs });
  await page.waitForFunction(() => document.body.dataset.ready, null, { timeout: loadMs });
  return { context, page };
}

// Ask one question and read back what the page showed.
async function askQ(page, q) {
  await page.fill("#q", q);
  await page.click("#ask");
  await page.waitForFunction(() => document.querySelector("#out").dataset.kind, null, { timeout: replyMs });
  const r = await page.evaluate(() => ({
    kind: document.querySelector("#out").dataset.kind,
    text: document.querySelector("#out").textContent,
    path: document.querySelector("#path").textContent,
    engine: document.querySelector("#engine").textContent,
    builtin: document.querySelector("#builtin").textContent,
    ms: parseInt(document.querySelector("#ms").textContent, 10),
  }));
  await page.evaluate(() => { delete document.querySelector("#out").dataset.kind; });
  return r;
}
const BROWSER = ["builtin", "shipped"];
const NO_GPU = () => { delete Navigator.prototype.gpu; };
const NO_BUILTIN = () => { delete self.LanguageModel; };
// A stand-in for the browser's own model, so C4 can prove the page uses it when it is there.
const FAKE_BUILTIN = () => {
  self.LanguageModel = { availability: async () => "available",
    create: async () => ({ prompt: async () => '{"answer": "Built-in stand-in answer.", "source": "browser"}', destroy() {} }) };
};

// 3. THE CHECKS ###################################

try {
  console.log("mode: " + (STUB ? "stub (fake browser model)" : "real browser model") + "; route: " + (LIGHT ? "lighter model" : "default model") + "; API: mocked with page.route; API timeout " + TIMEOUT_MS + " ms");

  const { context, page } = await open(NO_BUILTIN);
  const engine = await page.textContent("#engine");
  check(1, "page starts and names its engine", /webgpu|stub/.test(engine), engine);

  mode = "ok";
  const a = await askQ(page, "Where is the spare pump?");
  check(2, "server answer shown, labelled as the server's",
    a.kind === "server" && a.text.includes("Server answer to: Where is the spare pump?") && a.path === "the team server",
    a.path + ", " + a.ms + " ms: " + a.text.slice(0, 60));

  // No graphics path: the page must say to use Google Chrome, and start no model (no worker at all).
  const g = await open(() => {
    delete Navigator.prototype.gpu; delete self.LanguageModel;
    window.__workers = 0; const W = window.Worker;
    window.Worker = class extends W { constructor(...a) { super(...a); window.__workers++; } };
  });
  mode = "down";
  const c3 = await askQ(g.page, "Where is the spare pump?");
  const workers = await g.page.evaluate(() => window.__workers);
  const chromeLine = "This page needs Google Chrome with graphics acceleration on. Open it in Chrome to run the model.";
  check(3, "No WebGPU: the page says to use Google Chrome and loads no model",
    c3.engine === chromeLine && workers === 0 && c3.kind !== "shipped" && !c3.text.includes("this page's model"),
    "engine line: " + c3.engine.slice(0, 40) + "...; workers started: " + workers + "; answer: " + c3.path);
  await g.context.close();

  const f = await open(FAKE_BUILTIN);
  const c4a = await askQ(f.page, "Where is the spare pump?");
  await f.context.close();
  const c4b = await askQ(page, "Where is the spare pump?");
  check(4, "built-in model used when present; without it, falls back and says which path",
    c4a.kind === "builtin" && c4b.kind === "shipped" && c4b.text.includes("this page's model") && /no built-in model/.test(c4b.builtin),
    "with: " + c4a.path + "; without: " + c4b.path + " (" + c4b.builtin + ")");

  const states = [["server_down", "down", false], ["server_slow", "slow", false], ["offline", "gone", true]];
  const seen = [];
  let rulesHold = true;
  for (const [state, m, offline] of states) {
    mode = m;
    await context.setOffline(offline);
    const r = await askQ(page, "How do I reset the sensor?");
    const want = RULES.when[state] === "browser" ? BROWSER.includes(r.kind) : r.kind === "none";
    const inTime = state !== "server_slow" || r.ms < TIMEOUT_MS + 1000 + (STUB ? 0 : 60000);
    if (!want || !inTime) rulesHold = false;
    seen.push(state + " -> " + r.path + " (" + r.ms + " ms)");
  }
  await context.setOffline(false);
  check(5, "the path taken matches rules.json for down, slow and offline", rulesHold, seen.join("; "));

  // One visit with the download done; then cut the network and reload.
  await page.click("#prep");
  await page.waitForFunction(() => document.body.dataset.device, null, { timeout: loadMs });
  await page.waitForFunction(() => navigator.serviceWorker && navigator.serviceWorker.ready.then(() => true), null, { timeout: 10000 });
  await page.reload();  // second load: now the service worker controls the page
  await page.waitForFunction(() => document.body.dataset.ready, null, { timeout: loadMs });
  await page.unroute("**/api/ask");
  await context.setOffline(true);
  await page.reload();
  await page.waitForFunction(() => document.body.dataset.ready, null, { timeout: loadMs });
  const d = await askQ(page, "Where is the spare pump?");
  check(6, "network off after one visit: reload opens and answers or says plainly it cannot",
    BROWSER.includes(d.kind) || d.kind === "none", d.path + ", " + d.ms + " ms");
  await context.close();

  // The route line under the status names the model in use, and links to the other route.
  const route = async (u) => {
    const c = await browser.newContext(); const p = await c.newPage();
    await p.goto(u, { timeout: loadMs });
    await p.waitForFunction(() => document.body.dataset.ready, null, { timeout: loadMs });
    const r = await p.evaluate(() => ({ text: document.querySelector("#route").textContent, link: document.querySelector("#route a")?.getAttribute("href") || "" }));
    await c.close();
    return r;
  };
  const lt = await route(base + "&model=light"), df = await route(base);
  check(9, "the page names its model: lighter-route line with ?model=light, default-route line without",
    lt.text.startsWith("Running the lighter model, Qwen2.5 0.5B (Alibaba).") && lt.text.endsWith("Back to the default model") && !lt.link.includes("model=light") && lt.link.includes("timeout=") &&
    df.text === "Short on memory? Load the lighter model." && df.link.includes("model=light") && !df.text.includes("Qwen"),
    "light: " + lt.text.slice(0, 40) + "...; default: " + df.text);
} catch (err) {
  check("x", "the check script itself ran", false, err.message.split("\n")[0]);
} finally {
  await browser.close();
  server.close();
}

// 4. CHECKS ON FILES, NO BROWSER NEEDED ###################################

// A key in a file the page serves is a key anyone can read: open the page, view the source.
const KEY = /sk-[A-Za-z0-9_-]{16,}|AIza[0-9A-Za-z_-]{20,}|Bearer [A-Za-z0-9._-]{16,}|api_key[=][^&\s"']{8,}/;
const hits = [...served].filter((f) => KEY.test(fs.readFileSync(f, "utf8"))).map((f) => path.relative(KIT, f));
check(7, "no key in any served file", served.size > 0 && hits.length === 0, served.size + " files searched" + (hits.length ? "; hit in " + hits.join(", ") : ""));

// measures.json is yours: one object per device, saved with the page's "Save this device's numbers" button.
const FIELDS = ["device", "engine", "download_mb", "load_ms", "reply_ms", "tokens_per_s", "server_reply_ms", "runs"];
let c8 = false, why = "";
try {
  const m = JSON.parse(fs.readFileSync(path.join(HERE, "measures.json"), "utf8"));
  const devs = m.devices || [];
  const bad = devs.filter((d) => FIELDS.some((k) => d[k] === undefined || d[k] === null) || !(d.download_mb >= 0) || !(d.reply_ms > 0) || !(d.runs >= 3));
  c8 = devs.length >= 2 && bad.length === 0;
  why = devs.length + " device(s)" + (bad.length ? "; incomplete: " + bad.map((d) => d.device || "?").join(", ") : "");
} catch (err) { why = fs.existsSync(path.join(HERE, "measures.json")) ? "measures.json did not parse: " + err.message : "no measures.json yet: measure on two devices first"; }
check(8, "measures.json parses and has at least two devices", c8, why);

console.log(failed ? "RESULT: " + failed + " check(s) failed" : "RESULT: all checks passed");
process.exit(failed ? 1 : 0);
