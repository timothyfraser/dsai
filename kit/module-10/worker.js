// worker.js
// Run the page's own model beside the page, on its own thread, so the buttons never freeze.
// Course kit, module 10

// A Web Worker is a script the browser runs beside the page. It cannot touch the page; the two
// send each other messages. The page sends {type: "load"} or {type: "generate"}; this file answers.

import { loadEngine } from "./edge.js";
import { downloadedMB } from "./measure.js";

let engine = null;
const status = (text) => self.postMessage({ type: "status", text });

self.onmessage = async ({ data: m }) => {
  try {
    // 1. LOAD ONCE, and report what the load cost ###################################
    if (!engine) {
      const t0 = performance.now();
      // The page asked the browser which engine to use; pass its answer in (see edge.js).
      engine = await loadEngine(status, { device: m.device, why: m.why, stub: m.stub, model: m.model });
      self.postMessage({ type: "loaded", engine: engine.device,
        load_ms: Math.round(performance.now() - t0),
        download_mb: downloadedMB(performance.getEntriesByType("resource")) });
    }
    // 2. ANSWER ONE QUESTION ###################################
    if (m.type === "generate") {
      const t0 = performance.now();
      const out = await engine.generate(m.messages, 96);
      self.postMessage({ type: "reply", id: m.id, text: out.text, tokens: out.tokens, ms: Math.round(performance.now() - t0) });
    }
  } catch (err) {
    self.postMessage({ type: "error", id: m.id, message: err.message });
  }
};
