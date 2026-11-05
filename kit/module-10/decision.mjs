// decision.mjs
// The check on your written decision: DECISION.md, read beside rules.json and measures.json.
// Course kit, module 10

// Usage, from this folder:  node decision.mjs      (no browser, no Playwright, no network)
// A script can check that the decision is complete and tied to your numbers. Whether it is right
// is for the reviewer. Three checks:
//   D1 DECISION.md has the three parts: ## Decision, ## Alternatives, ## Evidence
//   D2 the Decision part quotes the "rule" sentence from rules.json, and Alternatives names at least two
//   D3 the Evidence part cites at least two numbers that appear in measures.json

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const read = (f) => (fs.existsSync(path.join(HERE, f)) ? fs.readFileSync(path.join(HERE, f), "utf8") : null);
let failed = 0;
const check = (n, label, ok, detail) => {
  console.log((ok ? "PASS" : "FAIL") + "  D" + n + ": " + label + (detail ? "  (" + detail + ")" : ""));
  if (!ok) failed++;
};

// 1. SPLIT DECISION.md INTO ITS PARTS ###################################

const text = read("DECISION.md") || "";
const part = (name) => (text.split(/^## /m).find((s) => s.toLowerCase().startsWith(name)) || "").slice(name.length).trim();
const decision = part("decision"), alternatives = part("alternatives"), evidence = part("evidence");
check(1, "DECISION.md has Decision, Alternatives and Evidence",
  decision && alternatives && evidence, text ? "" : "no DECISION.md yet");

// 2. THE RULE IS THE ONE THE PAGE RUNS, AND IT BEAT SOMETHING ###################################

const rule = JSON.parse(read("rules.json")).rule;
const alts = alternatives.split("\n").filter((l) => /^\s*[-*] /.test(l)).length;
check(2, "the decision quotes rules.json's rule and names at least two alternatives",
  decision.includes(rule) && alts >= 2, alts + " alternative(s) listed");

// 3. THE EVIDENCE IS YOUR MEASURED NUMBERS, NOT A GUESS ###################################

let numbers = [];
try {
  for (const d of JSON.parse(read("measures.json")).devices) for (const v of Object.values(d)) if (typeof v === "number") numbers.push(String(v));
} catch { /* no measures.json: D3 fails and says so */ }
const cited = [...new Set(numbers.filter((n) => new RegExp("(^|[^0-9.])" + n.replace(".", "\\.") + "([^0-9.]|$)").test(evidence)))];
check(3, "the evidence cites at least two numbers from measures.json",
  cited.length >= 2, numbers.length ? "cited: " + (cited.join(", ") || "none") : "no measures.json yet");

console.log(failed ? "RESULT: " + failed + " check(s) failed" : "RESULT: all checks passed");
process.exit(failed ? 1 : 0);
