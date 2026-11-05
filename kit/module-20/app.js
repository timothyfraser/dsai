// app.js: an offline field assistant. It answers only from the notes in notes.json.
// Three rules make up its contract:
//   1. Find the best matching note first. If nothing matches well, refuse without asking the model.
//   2. The model must reply with JSON: {"answer": "...", "source": "<note id>"}.
//   3. The answer must arrive within the time budget, or the page says it ran out of time.
import { loadEngine, memoryMB } from "../module-10/edge.js";   // the browser engine, shared with Module 10
import { bestNote } from "./match.js";                         // the note matcher, shared with refusal.mjs

// The two numbers that decide when the assistant gives up and when it refuses. TIME_BUDGET_MS comes
// from the phone rows in notes.json "measured"; MIN_SCORE from the refusal rates refusal.mjs reports.
const TIME_BUDGET_MS = 20000;  // 20 seconds: the starting guess; replace it with your phone's number
const MIN_SCORE = 2;           // how many shared words a note needs before we trust it

const $ = (id) => document.getElementById(id);
const say = (t) => { $("status").textContent = t; };
let engine = null, notes = [];

// Step 1: retrieval by shared words, in match.js (refusal.mjs scores your labelled questions with it).
// bestNote(question, notes) returns the best note and its score: how many words it shares with the question.

// Step 2: the contract check. Anything that is not valid JSON with a known source is rejected.
export function checkReply(text, noteId) {
  try {
    const obj = JSON.parse(text.slice(text.indexOf("{"), text.lastIndexOf("}") + 1));
    if (typeof obj.answer !== "string" || !obj.answer.trim()) return { ok: false, why: "no answer field" };
    if (obj.source !== noteId) return { ok: false, why: "source is not the note it was given" };
    return { ok: true, answer: obj.answer, source: obj.source };
  } catch { return { ok: false, why: "reply was not JSON" }; }
}

async function ask(question) {
  const t0 = performance.now();
  const { note, score } = bestNote(question, notes);
  if (!note || score < MIN_SCORE) {
    return { kind: "refused", text: "That is outside my field notes. I can only answer from them.", ms: Math.round(performance.now() - t0) };
  }
  const messages = [
    { role: "system", content: 'Answer only from the note. Reply with JSON only: {"answer": "...", "source": "' + note.id + '"}' },
    { role: "user", content: "Note [" + note.id + "] " + note.title + ": " + note.text + "\n\nQuestion: " + question },
  ];
  const timeout = new Promise((r) => setTimeout(() => r(null), TIME_BUDGET_MS));
  const out = await Promise.race([engine.generate(messages), timeout]);
  const ms = Math.round(performance.now() - t0);
  if (!out) return { kind: "timeout", text: "Out of time (" + TIME_BUDGET_MS / 1000 + " s). Read note " + note.id + " directly.", ms };
  const tps = out.tokens / (ms / 1000);
  const check = checkReply(out.text, note.id);
  if (!check.ok) return { kind: "broken", text: "The model broke the contract (" + check.why + "). Note " + note.id + ": " + note.text, ms, tps };
  return { kind: "answer", text: check.answer, source: note.id, ms, tps };
}

async function main() {
  notes = (await (await fetch("./notes.json")).json()).notes;
  if ("serviceWorker" in navigator) {
    try { await navigator.serviceWorker.register("./sw.js"); } catch (e) { console.warn("no service worker:", e.message); }
  }
  engine = await loadEngine(say);
  $("device").textContent = engine.device;
  $("ask").disabled = false;
  document.body.dataset.ready = "1";
}

$("form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const q = $("q").value.trim();
  if (!q) return;
  $("ask").disabled = true;
  say("Thinking on this device...");
  const r = await ask(q);
  const out = $("out");
  out.dataset.kind = r.kind;
  out.textContent = r.text + (r.source ? " [" + r.source + "]" : "");
  $("ms").textContent = r.ms + " ms";
  $("tps").textContent = r.tps ? r.tps.toFixed(1) + " tokens/s" : "n/a";
  const mb = memoryMB();
  $("mem").textContent = mb === null ? "not reported by this browser" : mb + " MB";
  say("Done.");
  $("ask").disabled = false;
});

main().catch((err) => { say("Could not start: " + err.message); document.body.dataset.ready = "error"; });
