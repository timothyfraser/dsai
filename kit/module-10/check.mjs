// check.mjs
// The checks for this module's browser page, run in a real headless browser with Playwright.
// Course kit, module 10

// One-time install, from this folder (a student laptop needs both):
//   npm install playwright          gets Playwright, the tool that drives a real browser from a script
//   npx playwright install chromium downloads the browser Playwright will drive
// Usage, from this folder:
//   EDGE_STUB=1 node check.mjs     fake browser model, no download (what CI runs)
//   node check.mjs                 the real model (needs the network for the first load)
// The team API is never called: page.route() stands in for it, so the checks can make it
// answer, fail, go slow, or vanish on purpose. Eight checks:
//   C1 the page starts and names its engine
//   C2 the server's answer is shown and labelled as the server's
//   C3 with WebGPU removed, the page names WASM and still answers
//   C4 with the built-in model present it is used; with it removed the page falls back and says which path
//   C5 for each state in rules.json (server down, slow, offline) the path that answered matches the rule
//   C6 with the network off, after one visit, a reload still opens and answers (or says plainly it cannot)
//   C7 no file the page served holds anything that looks like a key
//   C8 measures.json parses and holds at least two devices with every number

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
  res.writeHead(200, { "content-type": TYPES[path.extname(file)] || "application/octet-stream" });
  fs.createReadStream(file).pipe(res);
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const url = "http://127.0.0.1:" + server.address().port + "/module-10/?api=/api/ask&timeout=" + TIMEOUT_MS + (STUB ? "&stub=1" : "");

let failed = 0;
const check = (n, label, ok, detail) => {
  console.log((ok ? "PASS" : "FAIL") + "  C" + n + ": " + label + (detail ? "  (" + detail + ")" : ""));
  if (!ok) failed++;
};

const browser = await chromium.launch();
const loadMs = STUB ? 15000 : 600000;  // a real first load of the model downloads a few hundred MB

// 2. THE FAKE API, AND ONE FRESH BROWSER PER CASE ###################################

// mode is one of "ok", "down", "slow", "gone" (no reply at all, as with no network). The page sends POST /api/ask with {"question": "..."}.
let mode = "ok";
// init is a script run in the page before its own code: how a check removes a browser feature.
async function open(init) {
  const context = await browser.newContext();
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
  await page.goto(url);
  await page.waitForFunction(() => document.body.dataset.ready, null, { timeout: 15000 });
  return { context, page };
}

// Ask one question and read back what the page showed.
async function askQ(page, q) {
  await page.fill("#q", q);
  await page.click("#ask");
  await page.waitForFunction(() => document.querySelector("#out").dataset.kind, null, { timeout: loadMs });
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
  console.log("mode: " + (STUB ? "stub (fake browser model)" : "real browser model") + "; API: mocked with page.route; API timeout " + TIMEOUT_MS + " ms");

  const { context, page } = await open(NO_BUILTIN);
  const engine = await page.textContent("#engine");
  check(1, "page starts and names its engine", /webgpu|wasm/.test(engine), engine);

  mode = "ok";
  const a = await askQ(page, "Where is the spare pump?");
  check(2, "server answer shown, labelled as the server's",
    a.kind === "server" && a.text.includes("Server answer to: Where is the spare pump?") && a.path === "the team server",
    a.path + ", " + a.ms + " ms: " + a.text.slice(0, 60));

  const g = await open(() => { delete Navigator.prototype.gpu; delete self.LanguageModel; });
  mode = "down";
  const c3 = await askQ(g.page, "Where is the spare pump?");
  check(3, "no WebGPU: names WASM and still answers",
    c3.engine.startsWith("wasm") && BROWSER.includes(c3.kind), c3.engine + "; " + c3.path);
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
  await page.waitForFunction(() => document.body.dataset.ready, null, { timeout: 15000 });
  await page.unroute("**/api/ask");
  await context.setOffline(true);
  await page.reload();
  await page.waitForFunction(() => document.body.dataset.ready, null, { timeout: 15000 });
  const d = await askQ(page, "Where is the spare pump?");
  check(6, "network off after one visit: reload opens and answers or says plainly it cannot",
    BROWSER.includes(d.kind) || d.kind === "none", d.path + ", " + d.ms + " ms");
  await context.close();
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
