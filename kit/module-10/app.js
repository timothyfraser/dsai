// app.js
// The front door: ask the team's API, and when it cannot answer, ask a small model on this device.
// Course kit, module 10

// Read it top to bottom; each numbered section is one idea.
// The on-device engine is Module 20's edge.js, reused as it is: this file never loads a model itself.

// 0. SETUP ###################################

import { loadEngine } from "../module-20/edge.js";

const params = new URLSearchParams(location.search);

// Put your team's API address here (the /ask endpoint you deployed in Module 4).
// It must accept POST with {"question": "..."} and reply {"answer": "...", "source": "..."}.
// ?api=... in the page address overrides it, which is how check.mjs points the page at a fake API.
const API_URL = params.get("api") || "https://your-team-api.example.org/ask";

// How long to wait for the server before giving up on it, in milliseconds.
// Too short and a slow server is never used; too long and the user stares at "Loading".
const API_TIMEOUT_MS = Number(params.get("timeout")) || 8000;

const $ = (id) => document.getElementById(id);
const say = (t) => { $("status").textContent = t; };
let engine = null;  // the on-device engine, loaded only when it is first needed

// 1. ASK THE SERVER, WITH A TIMEOUT ###################################

// fetch() on its own can wait for minutes. An AbortController cancels it when the timer runs out.
// Every way this can fail becomes one plain sentence, because the user cannot read an error code.
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
    if (!res.ok) return { ok: false, why: "the server answered with an error (HTTP " + res.status + ")" };
    const body = await res.json();
    if (typeof body.answer !== "string") return { ok: false, why: "the server's reply had no answer in it" };
    return { ok: true, answer: body.answer, source: body.source || null };
  } catch (err) {
    if (err.name === "AbortError") return { ok: false, why: "the server took longer than " + API_TIMEOUT_MS / 1000 + " s" };
    return { ok: false, why: "the server could not be reached (" + (navigator.onLine ? "it may be down" : "this device is offline") + ")" };
  } finally {
    clearTimeout(timer);
  }
}

// 2. FALL BACK TO THE MODEL ON THIS DEVICE ###################################

// The first call loads the engine (WebGPU or WASM, Module 20 Step 4); later calls reuse it.
// The small model is told to keep the same reply shape as the server, so the page treats both alike.
async function getEngine() {
  if (!engine) engine = await loadEngine(say);
  return engine;
}

async function askDevice(question) {
  const e = await getEngine();
  const messages = [
    { role: "system", content: 'You are a small offline helper. Answer in one or two sentences. Reply with JSON only: {"answer": "...", "source": "on-device"}' },
    { role: "user", content: question },
  ];
  const out = await e.generate(messages, 96);
  // A small model sometimes breaks the JSON shape; then show its plain text rather than nothing.
  try {
    const obj = JSON.parse(out.text.slice(out.text.indexOf("{"), out.text.lastIndexOf("}") + 1));
    if (typeof obj.answer === "string" && obj.answer.trim()) return obj.answer;
  } catch { /* fall through */ }
  return out.text.trim();
}

// 3. ONE QUESTION, TWO PATHS ###################################

// Server first, device second. The label on the answer always says which one answered.
async function ask(question) {
  const t0 = performance.now();
  say("Asking the server...");
  const s = await askServer(question);
  if (s.ok) {
    return { kind: "server", path: "the team server", text: s.answer + (s.source ? " [" + s.source + "]" : ""), ms: Math.round(performance.now() - t0), why: "" };
  }
  say("No answer from the server: " + s.why + ". Asking the model on this device...");
  try {
    const text = await askDevice(question);
    return { kind: "device", path: "on device", text: "On device: " + text, ms: Math.round(performance.now() - t0), why: s.why };
  } catch (err) {
    return { kind: "error", path: "nothing", text: "Neither the server nor this device could answer. The server: " + s.why + ". The device: " + err.message + ".", ms: Math.round(performance.now() - t0), why: s.why };
  }
}

// 4. SHOW THE ANSWER, AND KEEP THE NUMBERS ###################################

// Time to answer and the path that answered are the two numbers to measure in this module.
function show(r) {
  const out = $("out");
  out.dataset.kind = r.kind;
  out.textContent = r.text;
  $("path").textContent = r.path;
  $("ms").textContent = r.ms + " ms";
  $("api").textContent = r.kind === "server" ? "answered" : r.why;
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
  try { await getEngine(); say("Offline model ready on " + engine.device + "."); document.body.dataset.device = engine.device; }
  catch (err) { say("Could not download the offline model: " + err.message); $("prep").disabled = false; }
});

// 5. START: register the service worker, then open the question box ###################################

// The service worker (sw.js) keeps copies of this page's files, so it opens with the network off.
// Module 20 Step 5 explains it in depth.
async function main() {
  if ("serviceWorker" in navigator) {
    try { await navigator.serviceWorker.register("./sw.js"); } catch (e) { console.warn("no service worker:", e.message); }
  }
  $("ask").disabled = false;
  document.body.dataset.ready = "1";
  say("Ready. Server: " + API_URL);
}

main().catch((err) => { say("Could not start: " + err.message); document.body.dataset.ready = "error"; });
