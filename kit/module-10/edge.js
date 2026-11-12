// edge.js: run a small language model inside the browser, on the device itself.
// Course kit, module 10 (Module 20 imports it from here as ../module-10/edge.js).
// One file, no build step. The model runs on the graphics chip (WebGPU), in Google Chrome.
// A browser with no graphics path gets one plain line telling the reader to open the page in Chrome, and no model loads.
// The processor-only (WASM) branch below is kept so you can measure it against the graphics path; no page answers on it.
// The runtime is Transformers.js, pinned to one exact version so the page never changes under you.
// With ?stub=1 in the address (or window.EDGE_STUB = true) no model loads at all:
// a fake model answers instantly, so the check script can run on any machine.

export const RUNTIME_URL =
  "https://cdn.jsdelivr.net/npm/@huggingface/transformers@4.3.1/dist/transformers.min.js";

// Gemma 3 1B (Google), 4-bit weights: about 760 MB, downloaded once, then cached. Smaller models did not keep the JSON reply format.
export const MODEL_ID = "onnx-community/gemma-3-1b-it-ONNX-GQA";

export function stubMode() {
  if (typeof window !== "undefined" && window.EDGE_STUB === true) return true;
  return new URLSearchParams(location.search).get("stub") === "1";
}

// The one line a page shows when the browser has no graphics path.
export const CHROME_LINE = "This page needs Google Chrome with graphics acceleration on. Open it in Chrome to run the model.";

// Can this page run the model? Ask, never assume. In stub mode no graphics chip is needed
// (the fake model runs anywhere), so a browser that still has the WebGPU object counts as a yes;
// a check that removes navigator.gpu gets the Chrome line even in stub mode.
export async function graphicsPath() {
  const d = await detectDevice();
  if (d.device === "webgpu" || (stubMode() && "gpu" in navigator)) return { ok: true, device: d.device === "webgpu" ? "webgpu" : "stub", why: d.why };
  return { ok: false, device: "none", why: d.why };
}

// Which engine can this device use? Ask, never assume.
export async function detectDevice() {
  if (!("gpu" in navigator)) return { device: "wasm", why: "this browser has no WebGPU" };
  try {
    const adapter = await navigator.gpu.requestAdapter();
    if (!adapter) return { device: "wasm", why: "WebGPU is present but no graphics adapter answered" };
    return { device: "webgpu", why: "WebGPU adapter found" };
  } catch (err) {
    return { device: "wasm", why: "WebGPU request failed: " + err.message };
  }
}

// Memory in use by this page, where the browser reports it (Chromium only).
export function memoryMB() {
  const m = performance.memory;
  return m ? Math.round(m.usedJSHeapSize / 1048576) : null;
}

// The fake model used in stub mode. It follows the same contract as the real one:
// it returns JSON text with an answer and the id of the note it used.
function stubGenerate(messages) {
  const user = messages[messages.length - 1].content;
  const note = (user.match(/\[(n\d+)\]/) || [])[1] || "n1";
  return JSON.stringify({ answer: "Stub answer drawn from note " + note + ".", source: note });
}

// Load the engine once. onStatus(text) reports progress to the page.
// opts.device ("webgpu" or "wasm") and opts.stub let a caller that already asked pass its answers in:
// worker.js does, because a check that removes WebGPU from the page cannot reach inside a worker.
export async function loadEngine(onStatus = () => {}, opts = {}) {
  if (opts.stub || stubMode()) {
    onStatus("Stub model ready (no download).");
    return { device: "stub", why: "stub mode", generate: async (msgs) => ({ text: stubGenerate(msgs), tokens: 12 }) };
  }
  const { device, why } = opts.device ? { device: opts.device, why: opts.why || "chosen by the page" } : await detectDevice();
  onStatus("Engine: " + device + " (" + why + "). Loading the runtime...");
  const tf = await import(RUNTIME_URL);
  const dtype = device === "webgpu" ? "q4f16" : "q4";
  const pipe = await tf.pipeline("text-generation", MODEL_ID, {
    device, dtype,
    progress_callback: (p) => { if (p.status === "progress") onStatus("Downloading " + p.file + ": " + Math.round(p.progress) + "%"); },
  });
  onStatus("Model ready on " + device + ".");
  return {
    device, why,
    generate: async (messages, maxNewTokens = 128) => {
      const out = await pipe(messages, { max_new_tokens: maxNewTokens, do_sample: false });
      const text = out[0].generated_text.at(-1).content;
      const tokens = pipe.tokenizer.encode(text).length;
      return { text, tokens };
    },
  };
}
