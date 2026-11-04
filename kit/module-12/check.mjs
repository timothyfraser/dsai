// check.mjs
// The checks for this module's interface, run in a real headless browser with Playwright.
// Course kit, module 12

// Usage, from this folder (kit/module-12/), after npm install:
//   API_STUB=1 node check.mjs                                  fake API, all seven checks (what CI runs)
//   VITE_API_URL=https://your-team-api.example.org/ask node check.mjs   your real API, checks 1, 2, 3 and 7
// With API_STUB=1 your API is never called: page.route() stands in for it, so the checks can
// make it answer, fail or go slow on purpose. Seven checks, numbered as on the module page:
//   1. the page builds, and the API address in it is the one in VITE_API_URL
//   2. an empty question sends nothing and says so in words
//   3. asked with the keyboard only, the answer is shown with its source
//   4. while the API is working, the page says so and the Ask button is off
//   5. a slow API: the page gives up within its timeout and says so in words
//   6. a broken API (HTTP 500): the old answer is gone and a plain sentence says why
//   7. on a phone-width screen, nothing scrolls sideways and the button is big enough to tap

// 0. SETUP ###################################

import http from "node:http";                     // for serving the built page
import fs from "node:fs";                         // for reading the built files
import os from "node:os";                         // for a scratch folder
import path from "node:path";                     // for file paths
import { spawnSync } from "node:child_process";   // for running vite build
import { createRequire } from "node:module";      // for finding Playwright
import { fileURLToPath } from "node:url";         // for this file's own folder

// Playwright: a normal install first (npm install playwright); PW_REQUIRE is only a fallback folder.
let chromium;
try { ({ chromium } = await import("playwright")); }
catch (err) {
  if (!process.env.PW_REQUIRE) { console.log("FAIL  Playwright is not installed: run npm install playwright, then npx playwright install chromium"); process.exit(1); }
  ({ chromium } = createRequire(process.env.PW_REQUIRE)("playwright"));
}
const HERE = path.dirname(fileURLToPath(import.meta.url));
const STUB = process.env.API_STUB === "1";
const TIMEOUT_MS = 1500;   // the page's API timeout for these checks, passed as VITE_API_TIMEOUT_MS
// In stub mode the page calls /api/ask on its own server, and page.route answers for the API.
const API_URL = STUB ? "/api/ask" : process.env.VITE_API_URL || "";
const TYPES = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml" };

// Fail fast, in words, when the check is run from the wrong place or before npm install.
const VITE = path.join(HERE, "node_modules", "vite", "bin", "vite.js");
if (!fs.existsSync(VITE)) { console.log("FAIL  run npm install in kit/module-12/ first (no node_modules/vite)"); process.exit(1); }
if (!API_URL) { console.log("FAIL  set API_STUB=1 for the fake API, or VITE_API_URL for your own"); process.exit(1); }

let failed = 0, skipped = 0;
const check = (n, label, ok, detail) => {
  console.log((ok ? "PASS" : "FAIL") + "  check " + n + ": " + label + (detail ? "  (" + detail + ")" : ""));
  if (!ok) failed++;
};
const skip = (n, label, why) => { console.log("SKIP  check " + n + ": " + label + "  (" + why + ")"); skipped++; };

// 1. BUILD THE PAGE INTO A SCRATCH FOLDER ###################################

console.log("mode: " + (STUB ? "stub (fake API with page.route)" : "real API at " + API_URL) + "; API timeout " + TIMEOUT_MS + " ms");

// The build goes to a scratch folder, so the check never touches your own dist/.
// --base ./ is the same build as npm run build: file paths stay relative, so the page also works in a sub-folder.
const OUT = fs.mkdtempSync(path.join(os.tmpdir(), "m12-check-"));
const built = spawnSync(process.execPath, [VITE, "build", "--base", "./", "--outDir", OUT, "--emptyOutDir", "--logLevel", "error"], {
  cwd: HERE, encoding: "utf8",
  env: { ...process.env, VITE_API_URL: API_URL, VITE_API_TIMEOUT_MS: String(TIMEOUT_MS) },
});
const assets = fs.existsSync(path.join(OUT, "assets")) ? fs.readdirSync(path.join(OUT, "assets")) : [];
const js = assets.filter((f) => f.endsWith(".js")).map((f) => fs.readFileSync(path.join(OUT, "assets", f), "utf8")).join("\n");
check(1, "page builds, with the API address from VITE_API_URL",
  built.status === 0 && js.includes(JSON.stringify(API_URL)), built.status === 0 ? "address " + API_URL : (built.stderr || "").split("\n")[0]);
if (built.status !== 0) process.exit(1);

// 2. SERVE THE BUILT PAGE ON A LOCAL PORT ###################################

const server = http.createServer((req, res) => {
  const p = decodeURIComponent(new URL(req.url, "http://x").pathname);
  const file = path.join(OUT, p === "/" ? "index.html" : p);
  if (!file.startsWith(OUT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { "content-type": TYPES[path.extname(file)] || "application/octet-stream" });
  fs.createReadStream(file).pipe(res);
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const url = "http://127.0.0.1:" + server.address().port + "/";

const browser = await chromium.launch();
const page = await browser.newPage();

// 3. THE FAKE API: change how it behaves before each check ###################################

// mode is one of "ok", "error", "slow". The page sends POST with {"question": "..."}.
let mode = "ok";
let calls = 0;
if (STUB) {
  await page.route("**/api/ask", async (route) => {
    calls++;
    if (mode === "error") return route.fulfill({ status: 500, contentType: "application/json", body: '{"detail":"server error"}' });
    if (mode === "slow") await new Promise((r) => setTimeout(r, TIMEOUT_MS + 2000));
    const q = JSON.parse(route.request().postData() || "{}").question || "";
    return route.fulfill({ status: 200, contentType: "application/json",
      body: JSON.stringify({ answer: "Stub answer to: " + q, source: "maintenance-log.csv, row 12" }) }).catch(() => {});
  });
}

// Ask with the keyboard only: find the box by its label, as a screen reader does, type, press Enter.
async function askByKeyboard(q) {
  await page.getByLabel("Your question").focus();
  await page.keyboard.press("Control+A");
  await page.keyboard.type(q);
  const t0 = Date.now();
  await page.keyboard.press("Enter");
  return t0;
}
const finalState = () => page.waitForFunction(() => ["answer", "error", "empty"].includes(document.querySelector("main").dataset.state), null, { timeout: 30000 });
const read = (sel) => page.locator(sel).count().then((n) => (n ? page.textContent(sel) : ""));

// 4. THE CHECKS ###################################

try {
  await page.goto(url);
  await page.waitForSelector("main[data-state='idle']", { timeout: 15000 });

  // Check 2: an empty question.
  const before = calls;
  await askByKeyboard("");
  await finalState();
  const st2 = await read("#status");
  check(2, "empty question sends nothing and says so", (await page.locator("main").getAttribute("data-state")) === "empty" && calls === before && /Nothing was sent/.test(st2), st2);

  // Check 3: the answer with its source, asked by keyboard alone.
  mode = "ok";
  await askByKeyboard("When was pump 4 last serviced?");
  await finalState();
  const ans = await read("#answer-text"), src = await read("#source");
  check(3, "keyboard only: answer shown with its source",
    (await page.locator("main").getAttribute("data-state")) === "answer" && ans.length > 0 && src.startsWith("Source: "),
    ans.slice(0, 50) + " | " + src.slice(0, 50));

  if (STUB) {
    // Checks 4 and 5: one slow question. Look at the page while it waits, then time the give-up.
    mode = "slow";
    const t0 = await askByKeyboard("How do I reset the sensor?");
    await page.waitForTimeout(300);
    const busy = await page.evaluate(() => ({
      state: document.querySelector("main").dataset.state,
      disabled: document.querySelector("button[type=submit]").disabled,
      status: document.querySelector("#status").textContent,
      oldAnswer: !!document.querySelector("#answer"),
    }));
    check(4, "while waiting: says so, button off, old answer gone",
      busy.state === "loading" && busy.disabled && /Asking/.test(busy.status) && !busy.oldAnswer, busy.status);
    await finalState();
    const ms = Date.now() - t0, err5 = await read("#error");
    check(5, "slow API: gives up within the timeout, in words", ms < TIMEOUT_MS + 1000 && /took longer than/.test(err5), ms + " ms: " + err5.slice(0, 60));

    // Check 6: a broken API, right after a good answer.
    mode = "ok";
    await askByKeyboard("Where is the spare pump?");
    await finalState();
    mode = "error";
    await askByKeyboard("Where is the spare pump?");
    await finalState();
    const err6 = await read("#error");
    check(6, "broken API (HTTP 500): old answer gone, plain sentence",
      (await page.locator("#answer").count()) === 0 && /^No answer: the server answered with an error/.test(err6), err6.slice(0, 70));
  } else {
    skip(4, "while waiting", "needs API_STUB=1 to slow the API on purpose");
    skip(5, "slow API", "needs API_STUB=1");
    skip(6, "broken API", "needs API_STUB=1");
  }

  // Check 7: a phone-width screen, 390 by 844 like a small phone.
  await page.setViewportSize({ width: 390, height: 844 });
  const phone = await page.evaluate(() => ({
    sideways: document.documentElement.scrollWidth > window.innerWidth,
    button: Math.round(document.querySelector("button[type=submit]").getBoundingClientRect().height),
  }));
  check(7, "phone width: no sideways scroll, button at least 44 px tall", !phone.sideways && phone.button >= 44,
    "scroll " + (phone.sideways ? "yes" : "no") + ", button " + phone.button + " px");
} catch (err) {
  check("x", "the check script itself ran", false, err.message.split("\n")[0]);
} finally {
  await browser.close();
  server.close();
  fs.rmSync(OUT, { recursive: true, force: true });
}
console.log(failed ? "RESULT: " + failed + " check(s) failed" : "RESULT: all checks passed" + (skipped ? " (" + skipped + " skipped)" : ""));
process.exit(failed ? 1 : 0);
