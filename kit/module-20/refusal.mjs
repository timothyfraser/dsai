// refusal.mjs: how often the field assistant refuses, at a few MIN_SCORE values, with no model.
// Usage, from this folder:  node refusal.mjs      (no browser, no phone, no network)
// It scores every question in questions.json with bestNote() from match.js, the matcher the page runs,
// and prints a narrow table (it reads on a phone), one row per MIN_SCORE:
//   min       the MIN_SCORE value; "<- now" marks the one app.js uses
//   in-ref    in-scope refused: the share of questions your notes answer that the page would refuse (a missed answer)
//   out-ref   out-of-scope refused: the share of questions outside your notes that it refuses (the higher the better)
//   wrong     in-scope questions that pass the threshold but match a different note than the label
// Refusal happens before the model is called, so these rates are the same on a laptop and on a phone.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { bestNote } from "./match.js";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const load = (f) => JSON.parse(fs.readFileSync(path.join(HERE, f), "utf8"));
const notes = load("notes.json").notes;
const { in_scope = [], out_of_scope = [] } = load("questions.json");
const current = Number(fs.readFileSync(path.join(HERE, "app.js"), "utf8").match(/const MIN_SCORE = (\d+)/)[1]);

// The share as a whole percent, the form decision.mjs looks for in DECISION.md.
const pct = (k, n) => (n ? Math.round((100 * k) / n) : 0) + "%";

export function rates(minScore, notesList = notes, inS = in_scope, outS = out_of_scope) {
  const refused = (q) => { const r = bestNote(q, notesList); return !r.note || r.score < minScore; };
  const inRef = inS.filter((x) => refused(x.q)).length;
  const outRef = outS.filter((x) => refused(x.q)).length;
  const wrong = inS.filter((x) => !refused(x.q) && bestNote(x.q, notesList).note.id !== x.note).length;
  return { in_scope: pct(inRef, inS.length), out_of_scope: pct(outRef, outS.length), wrong };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  console.log(in_scope.length + " in-scope, " + out_of_scope.length + " out-of-scope, " + notes.length + " notes");
  console.log("min  in-ref  out-ref  wrong");
  for (const m of [...new Set([1, 2, 3, current])].sort((a, b) => a - b)) {
    const r = rates(m);
    console.log(String(m).padEnd(5) + r.in_scope.padEnd(8) + r.out_of_scope.padEnd(9) + r.wrong + (m === current ? "  <- now" : ""));
  }
  console.log("min: MIN_SCORE (now: app.js)");
  console.log("in-ref: in-scope refused");
  console.log("out-ref: out-of-scope refused");
  console.log("wrong: answered from the wrong note");
  console.log("Best score per question (shared words, best note):");
  for (const [label, list] of [["in ", in_scope], ["out", out_of_scope]]) {
    for (const x of list) { const r = bestNote(x.q, notes); console.log(label + " " + r.score + " " + (r.note ? r.note.id : "--") + "  " + x.q); }
  }
}
