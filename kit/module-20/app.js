// app.js: an offline field assistant. It answers only from the notes in notes.json.
// Three rules make up its contract:
//   1. Find the best matching note first. If nothing matches well, refuse without asking the model.
//   2. The model must reply with JSON: {"answer": "...", "source": "<note id>"}.
//   3. The answer must arrive within the time budget, or the page says it ran out of time.
import { graphicsPath, stubMode, memoryMB, chosenModel, showRoute, CHROME_LINE } from "../module-10/edge.js";   // engine helpers, shared with Module 10
import { bestNote } from "./match.js";                         // the note matcher, shared with refusal.mjs

// The two numbers that decide when the assistant gives up and when it refuses. TIME_BUDGET_MS comes
// from the phone rows in notes.json "measured"; MIN_SCORE from the refusal rates refusal.mjs reports.
const TIME_BUDGET_MS = 20000;  // 20 seconds: the starting guess; replace it with your phone's number
const MIN_SCORE = 2;           // how many shared words a note needs before we trust it

const $ = (id) => document.getElementById(id);
let offlineNote = "";   // set when the service worker could not install
const say = (t) => { $("status").textContent = offlineNote ? t + " " + offlineNote : t; };
let engine = null, notes = [];

// Step 1: retrieval by shared words, in match.js (refusal.mjs scores your labelled questions with it).
// bestNote(question, notes) returns the best note and its score: how many words it shares with the question.

// Step 2: the contract check. Anything that is not valid JSON with a known source is rejected.
// The one thing removed first is a ```json fence around the reply, which small models often add.
export function checkReply(text, noteId) {
  try {
    const fence = text.trim().match(/^```(?:json)?\s*\n([\s\S]*?)\n?```$/);
    const obj = JSON.parse(fence ? fence[1] : text);
    if (typeof obj.answer !== "string" || !obj.answer.trim()) return { ok: false, why: "no answer field" };
    if (obj.source !== noteId) return { ok: false, why: "source is not the note it was given" };
    return { ok: true, answer: obj.answer, source: obj.source };
  } catch { return { ok: false, why: "reply was not JSON" }; }
}

// One worked example shows a small model the exact reply shape; without it the format broke.
export function systemLine(id) {
  return 'Answer only from the note, in one short sentence. Reply with one JSON object and nothing else.\n' +
    'Example: for note [n9] "Radios: carry a charged radio." and the question "What do I carry?", the reply is:\n' +
    '{"answer": "Carry a charged radio.", "source": "n9"}\n' +
    'Now reply for note [' + id + '] in exactly that form, with "source": "' + id + '".';
}

// The model runs in Module 10's worker, on its own thread, so the time budget can fire even
// when the model is stuck on the CPU. The page only sends messages and waits for replies.
let worker = null, nextId = 0, gpu = null;
const waiting = new Map();
function startWorker() {
  return new Promise((resolve, reject) => {
    // The worker file sits outside this page's service worker scope, so a plain Worker could not load it offline.
    // A tiny blob worker that imports it is controlled like the page, so the saved copies serve it.
    const src = 'import "' + new URL("../module-10/worker.js", import.meta.url).href + '";';
    worker = new Worker(URL.createObjectURL(new Blob([src], { type: "text/javascript" })), { type: "module" });
    worker.onmessage = ({ data: m }) => {
      if (m.type === "status") say(m.text);
      if (m.type === "loaded") resolve(m);
      if (m.type === "error" && m.id === undefined) reject(new Error(m.message));
      if (m.type === "reply" || (m.type === "error" && m.id !== undefined)) { waiting.get(m.id)?.(m); waiting.delete(m.id); }
    };
    worker.onerror = (e) => reject(new Error(e.message || "the model worker failed to start"));
    worker.postMessage({ type: "load", device: gpu.device, why: gpu.why, stub: stubMode(), model: chosenModel() });
  });
}
function generate(messages) {
  const id = ++nextId;
  return new Promise((resolve, reject) => {
    waiting.set(id, (m) => (m.type === "reply" ? resolve(m) : reject(new Error(m.message))));
    worker.postMessage({ type: "generate", id, messages, device: gpu.device, why: gpu.why, stub: stubMode(), model: chosenModel() });
  });
}

async function ask(question) {
  const t0 = performance.now();
  const { note, score } = bestNote(question, notes);
  if (!note || score < MIN_SCORE) {
    return { kind: "refused", text: "That is outside my field notes. I can only answer from them.", ms: Math.round(performance.now() - t0) };
  }
  const messages = [
    { role: "system", content: systemLine(note.id) },
    { role: "user", content: "Note [" + note.id + "] " + note.title + ": " + note.text + "\n\nQuestion: " + question },
  ];
  let timer;
  const timeout = new Promise((r) => { timer = setTimeout(() => r(null), TIME_BUDGET_MS); });
  if (!gpu.ok) return { kind: "nomodel", text: "The model is not running. Note " + note.id + ": " + note.text, ms: Math.round(performance.now() - t0) };
  const out = await Promise.race([generate(messages), timeout]).finally(() => clearTimeout(timer));
  const ms = Math.round(performance.now() - t0);
  if (!out) return { kind: "timeout", text: "Out of time (" + TIME_BUDGET_MS / 1000 + " s). Read note " + note.id + " directly.", ms };
  const tps = out.tokens / (ms / 1000);
  const check = checkReply(out.text, note.id);
  if (!check.ok) return { kind: "broken", text: "The model broke the contract (" + check.why + "). Note " + note.id + ": " + note.text, ms, tps };
  return { kind: "answer", text: check.answer, source: note.id, ms, tps };
}

async function main() {
  showRoute($("route"));
  notes = (await (await fetch("./notes.json")).json()).notes;
  const noOffline = () => { offlineNote = "Offline use is not available in this browser."; say("Starting..."); };
  if ("serviceWorker" in navigator) {
    try {
      const reg = await navigator.serviceWorker.register("./sw.js");
      const w = reg.installing || reg.waiting || reg.active;
      if (w && w.state === "redundant") noOffline();
      else if (w) w.addEventListener("statechange", () => { if (w.state === "redundant") noOffline(); });
    } catch (e) { console.warn("no service worker:", e.message); noOffline(); }
  } else { noOffline(); }
  gpu = await graphicsPath();
  if (gpu.ok) {
    engine = await startWorker();
    $("device").textContent = engine.engine;
  } else {
    // No graphics path: load no model, say so once, and still show the matching note.
    $("device").textContent = "no model";
    say(CHROME_LINE);
  }
  $("ask").disabled = false;
  document.body.dataset.ready = "1";
}

$("form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const q = $("q").value.trim();
  if (!q) return;
  $("ask").disabled = true;
  say(gpu.ok ? "Thinking on this device..." : CHROME_LINE + " The model is not running; showing the matching note.");
  const r = await ask(q);
  const out = $("out");
  out.dataset.kind = r.kind;
  out.textContent = r.text + (r.source ? " [" + r.source + "]" : "");
  $("ms").textContent = r.ms + " ms";
  $("tps").textContent = r.tps ? r.tps.toFixed(1) + " tokens/s" : "n/a";
  const mb = memoryMB();
  $("mem").textContent = mb === null ? "not reported by this browser" : mb + " MB";
  say(gpu.ok ? "Done." : CHROME_LINE + " The model is not running; this is the matching note.");
  $("ask").disabled = false;
});

main().catch((err) => { say("Could not start: " + err.message); document.body.dataset.ready = "error"; });
