// app.js
// The front door: ask the team's API, and answer in the browser only when rules.json says so.
// Course kit, module 10

// Read it top to bottom; each numbered section is one idea.
// Three paths can answer: the team server, the browser's own model (builtin.js), and the
// page's own model (edge.js, run in worker.js). Every answer is labelled with the path that gave it.

// 0. SETUP ###################################

import { graphicsPath, stubMode, CHROME_LINE } from "./edge.js";
import { builtinModel } from "./builtin.js";
import { record, summary, saveFile } from "./measure.js";
import { canListen, listen } from "./voice.js";

const params = new URLSearchParams(location.search);

// Put your team's API address here (the /ask endpoint you deployed in Module 4).
// It must accept POST with {"question": "..."} and reply {"answer": "...", "source": "..."}.
// ?api=... in the page address overrides it, which is how check.mjs points the page at a fake API.
const API_URL = params.get("api") || "https://your-team-api.example.org/ask";

// The hybrid rule is data, not code, so a reviewer can read it and check.mjs can test it.
const RULES = await (await fetch("./rules.json")).json();

// How long to wait for the server before giving up on it, in milliseconds.
// Too short and a slow server is never used; too long and the user stares at "Loading".
const API_TIMEOUT_MS = Number(params.get("timeout")) || RULES.timeout_ms;

const $ = (id) => document.getElementById(id);
const say = (t) => { $("status").textContent = t; };
let gpu = null;      // what the browser said about WebGPU, asked once at start
let builtin = null;  // { model, why } from builtin.js
let load = {};       // what loading the page's own model cost: engine, download_mb, load_ms

// 1. ASK THE SERVER, WITH A TIMEOUT ###################################

// fetch() on its own can wait for minutes. An AbortController cancels it when the timer runs out.
// Every way this can fail becomes one plain sentence, because the user cannot read an error code.
// state names the failure the same way rules.json does: server_down, server_slow or offline.
async function askServer(question) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), API_TIMEOUT_MS);
  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ question }),
      signal: ctrl.signal,
    });
    if (!res.ok) return { ok: false, state: "server_down", why: "the server answered with an error (HTTP " + res.status + ")" };
    const body = await res.json();
    if (typeof body.answer !== "string") return { ok: false, state: "server_down", why: "the server's reply had no answer in it" };
    return { ok: true, answer: body.answer, source: body.source || null };
  } catch (err) {
    if (err.name === "AbortError") return { ok: false, state: "server_slow", why: "the server took longer than " + API_TIMEOUT_MS / 1000 + " s" };
    if (!navigator.onLine) return { ok: false, state: "offline", why: "this device is offline" };
    return { ok: false, state: "server_down", why: "the server could not be reached (it may be down)" };
  } finally {
    clearTimeout(timer);
  }
}

// 2. THE PAGE'S OWN MODEL, IN A WORKER ###################################

// The worker loads edge.js on its own thread; the page only sends messages and waits for replies.
// It is started on first use, so nothing downloads until a question or the button needs it.
let worker = null, nextId = 0;
const waiting = new Map();
function shipped(messages) {
  if (!gpu.ok) return Promise.reject(new Error(CHROME_LINE));   // no graphics path: no model is ever started
  if (!worker) {
    worker = new Worker(new URL("./worker.js", import.meta.url), { type: "module" });
    worker.onmessage = ({ data: m }) => {
      if (m.type === "status") say(m.text);
      if (m.type === "loaded") {
        load = m;
        // In stub mode (?stub=1) a fake model stands in; the engine named is still the one the browser offered.
        $("engine").textContent = (m.engine === "stub" ? "fake model" : m.engine) + " (" + gpu.why + ")";
        document.body.dataset.device = m.engine;
      }
      if (m.type === "reply" || m.type === "error") { waiting.get(m.id)?.(m); waiting.delete(m.id); }
    };
  }
  const id = ++nextId;
  return new Promise((resolve, reject) => {
    waiting.set(id, (m) => (m.type === "reply" ? resolve(m) : reject(new Error(m.message))));
    worker.postMessage({ type: messages ? "generate" : "load", id, messages, device: gpu.device, why: gpu.why, stub: stubMode() });
  });
}

// 3. ANSWER IN THE BROWSER: the browser's own model if it is ready, else the page's ###################################

// The small model is told to keep the same reply shape as the server, so the page treats every path alike.
async function askBrowser(question) {
  const messages = [
    { role: "system", content: 'You are a small offline helper. Answer in one or two sentences. Reply with JSON only: {"answer": "...", "source": "browser"}' },
    { role: "user", content: question },
  ];
  const t0 = performance.now();
  let kind = "shipped", out;
  if (RULES.browser_order[0] === "builtin" && builtin.model) { kind = "builtin"; out = await builtin.model.generate(messages); }
  else out = await shipped(messages);
  const ms = Math.round(performance.now() - t0);
  // A small model sometimes breaks the JSON shape; then show its plain text rather than nothing.
  let text = out.text.trim();
  try {
    const obj = JSON.parse(out.text.slice(out.text.indexOf("{"), out.text.lastIndexOf("}") + 1));
    if (typeof obj.answer === "string" && obj.answer.trim()) text = obj.answer;
  } catch { /* keep the plain text */ }
  return { kind, text, tokens_per_s: out.tokens ? Math.round((out.tokens / (ms / 1000)) * 10) / 10 : null };
}

// 4. ONE QUESTION: the rule decides the path ###################################

const LABEL = { server: "the team server", builtin: "the browser's own model", shipped: "this page's model", none: "nothing", error: "nothing" };
async function ask(question) {
  const t0 = performance.now();
  say("Asking the server...");
  const s = await askServer(question);
  const done = (r) => ({ ...r, path: LABEL[r.kind], ms: Math.round(performance.now() - t0) });
  if (s.ok) return done({ kind: "server", text: s.answer + (s.source ? " [" + s.source + "]" : ""), why: "" });
  // The rule says, for this state, whether the browser may answer at all.
  if (RULES.when[s.state] !== "browser") {
    return done({ kind: "none", text: "No answer: " + s.why + ", and this page is set not to answer from the browser when that happens.", why: s.why });
  }
  say("No answer from the server: " + s.why + ". Answering in the browser...");
  try {
    const b = await askBrowser(question);
    return done({ kind: b.kind, text: "In the browser (" + LABEL[b.kind] + "): " + b.text, why: s.why, tokens_per_s: b.tokens_per_s });
  } catch (err) {
    return done({ kind: "error", text: "Neither the server nor the browser could answer. The server: " + s.why + ". The browser: " + err.message + ".", why: s.why });
  }
}

// 5. SHOW THE ANSWER, AND KEEP THE NUMBERS ###################################

// Time to answer and the path that answered are the two numbers a reader feels.
function show(r) {
  const out = $("out");
  out.dataset.kind = r.kind;
  out.textContent = r.text;
  $("path").textContent = r.path;
  $("ms").textContent = r.ms + " ms";
  $("api").textContent = r.kind === "server" ? "answered" : r.why;
  record({ path: r.kind, engine: r.kind === "shipped" ? load.engine : r.kind, reply_ms: r.ms, tokens_per_s: r.tokens_per_s ?? null });
  const li = document.createElement("li");
  li.textContent = r.path + ", " + r.ms + " ms";
  $("log").prepend(li);
  say("Done.");
}

$("form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const q = $("q").value.trim();
  if (!q) return;
  $("ask").disabled = true;
  show(await ask(q));
  $("ask").disabled = false;
});

// The offline model is downloaded only when the user asks, never as a surprise on a phone plan.
$("prep").addEventListener("click", async () => {
  $("prep").disabled = true;
  try { await shipped(null); say("Offline model ready on " + load.engine + ", " + load.download_mb + " MB downloaded."); }
  catch (err) { say("Could not download the offline model: " + err.message); $("prep").disabled = false; }
});

$("save").addEventListener("click", () => saveFile(summary(navigator.userAgent, load)));

$("mic").addEventListener("click", async () => { $("speech").textContent = await listen((t) => { $("q").value = t; }); });

// 6. START: ask the browser what it has, register the service worker, open the question box ###################################

// Ask, never assume: WebGPU, the built-in model and speech are each checked, and the answer is shown.
async function main() {
  gpu = await graphicsPath();
  $("engine").textContent = gpu.ok ? gpu.device + " (" + gpu.why + "), not loaded yet" : CHROME_LINE;
  if (!gpu.ok) $("prep").disabled = true;
  builtin = await builtinModel();
  $("builtin").textContent = builtin.why;
  $("speech").textContent = canListen() ? "available" : "not in this browser: type the question";
  $("mic").disabled = !canListen();
  $("rule").textContent = RULES.rule;
  // The service worker (sw.js) keeps copies of this page's files, so it opens with the network off.
  if ("serviceWorker" in navigator) {
    try { await navigator.serviceWorker.register("./sw.js"); } catch (e) { console.warn("no service worker:", e.message); }
  }
  $("ask").disabled = false;
  document.body.dataset.ready = "1";
  say(gpu.ok ? "Ready. Server: " + API_URL : CHROME_LINE + " Ready. Server: " + API_URL);
}

main().catch((err) => { say("Could not start: " + err.message); document.body.dataset.ready = "error"; });
