// decision.mjs
// The check on your written decision: why MIN_SCORE and TIME_BUDGET_MS have the values they have.
// Course kit, module 20

// Usage, from this folder:  node decision.mjs      (no browser, no Playwright, no network)
// It reads app.js, notes.json ("measured"), questions.json and DECISION.md. A script can check that the
// decision is complete and tied to numbers you measured; whether it is right is for the reviewer.
//   D1 notes.json "measured" holds complete rows only, and at least one is this page on a phone
//   D2 DECISION.md has ## Decision, ## Alternatives, ## Evidence, ## Why on the phone and
//      ## Model choice, and the Decision names MIN_SCORE and TIME_BUDGET_MS with the values app.js uses
//   D3 TIME_BUDGET_MS is at least the slowest reply this page took on a phone, and Evidence cites two
//      measured numbers
//   D4 questions.json labels at least five questions of each kind, and Evidence cites the in-scope and
//      out-of-scope refusal rates refusal.mjs reports at the MIN_SCORE app.js uses
//   D5 ## Model choice names a model you measured in notes.json

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const read = (f) => (fs.existsSync(path.join(HERE, f)) ? fs.readFileSync(path.join(HERE, f), "utf8") : "");
let failed = 0;
const check = (n, label, ok, detail) => {
  console.log((ok ? "PASS" : "FAIL") + "  D" + n + ": " + label + (detail ? "  (" + detail + ")" : ""));
  if (!ok) failed++;
};

// 1. THE MEASUREMENTS: one object per phone, app and model ###################################

// app: "edge-gallery" (Google AI Edge Gallery), "pocketpal" (PocketPal AI) or "page" (this field assistant);
// job: what you asked it to do, in a few words; first_tps: tokens per second on the first reply;
// after_ten_tps: after ten replies with no pause; slowest_reply_ms: the slowest reply;
// warm: did the phone get warm (true or false).
const FIELDS = ["phone", "app", "model", "job", "first_tps", "after_ten_tps", "slowest_reply_ms", "warm"];
const phones = JSON.parse(read("notes.json")).measured?.phones || [];
const full = phones.filter((p) => FIELDS.every((k) => p[k] !== undefined && p[k] !== null && p[k] !== ""));
// The time budget is this page's, so it is set from rows that measured this page.
const page = full.filter((p) => p.app === "page");
check(1, "notes.json rows are complete, and at least one measures this page on a phone",
  page.length >= 1 && full.length === phones.length,
  phones.length + " row(s), " + full.length + " complete, " + page.length + " of this page");

// 2. THE DECISION NAMES THE NUMBERS THE PAGE RUNS ###################################

const app = read("app.js");
const budget = Number(app.match(/const TIME_BUDGET_MS = (\d+)/)[1]);
const minScore = Number(app.match(/const MIN_SCORE = (\d+)/)[1]);
const text = read("DECISION.md");
const part = (name) => (text.split(/^## /m).find((s) => s.toLowerCase().startsWith(name)) || "").slice(name.length).trim();
const decision = part("decision"), evidence = part("evidence");
const names = (k, v) => new RegExp(k + "\\D{0,20}" + v + "(\\D|$)").test(decision);
const missing = ["decision", "alternatives", "evidence", "why on the phone", "model choice"].filter((k) => !part(k));
check(2, "DECISION.md has its five parts and names MIN_SCORE " + minScore + " and TIME_BUDGET_MS " + budget,
  missing.length === 0 && names("MIN_SCORE", minScore) && names("TIME_BUDGET_MS", budget),
  text ? (missing.length ? "missing or empty: ## " + missing.join(", ## ") : "") : "no DECISION.md yet");

// 3. THE BUDGET COVERS THE PHONE YOU MEASURED, AND THE EVIDENCE SAYS SO ###################################

const slowest = Math.max(0, ...page.map((p) => p.slowest_reply_ms));
const numbers = full.flatMap((p) => Object.values(p).filter((v) => typeof v === "number").map(String));
const cited = [...new Set(numbers.filter((n) => new RegExp("(^|[^0-9.])" + n.replace(".", "\\.") + "([^0-9.]|$)").test(evidence)))];
check(3, "TIME_BUDGET_MS covers this page's slowest reply on a phone, and the evidence cites two measured numbers",
  page.length > 0 && budget >= slowest && cited.length >= 2,
  "budget " + budget + " ms, slowest measured " + (page.length ? slowest + " ms" : "none") + ", cited: " + (cited.join(", ") || "none"));

// 4. MIN_SCORE RESTS ON MEASURED REFUSAL RATES, AND THE EVIDENCE SAYS SO ###################################

// The rates come from refusal.mjs, which scores questions.json with the page's own matcher.
const qs = read("questions.json") ? JSON.parse(read("questions.json")) : {};
const labelled = (qs.in_scope || []).length >= 5 && (qs.out_of_scope || []).length >= 5;
let r = null;
if (labelled) r = (await import("./refusal.mjs")).rates(minScore);
const has = (p) => new RegExp("(^|[^0-9.])" + p.replace("%", "\\s?%")).test(evidence);
check(4, "Evidence cites the refusal rates at MIN_SCORE " + minScore + " from refusal.mjs",
  Boolean(r) && has(r.in_scope) && has(r.out_of_scope),
  r ? "in-scope refused " + r.in_scope + ", out-of-scope refused " + r.out_of_scope + "; run node refusal.mjs"
    : "questions.json needs at least five in_scope and five out_of_scope questions");

// 5. THE MODEL CHOICE RESTS ON A MODEL YOU MEASURED ###################################

// Who the worker is and where they stand is for the reviewer; that the model was measured is checkable.
const choice = part("model choice").toLowerCase();
const models = [...new Set(full.map((p) => String(p.model)))];
const named = models.filter((m) => choice.includes(m.toLowerCase()));
check(5, "## Model choice names a model you measured in notes.json", named.length >= 1,
  models.length ? "measured: " + models.join(", ") + "; named: " + (named.join(", ") || "none") : "no measured model yet");

console.log(failed ? "RESULT: " + failed + " check(s) failed" : "RESULT: all checks passed");
process.exit(failed ? 1 : 0);
