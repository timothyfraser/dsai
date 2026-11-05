// measure.js
// Keep the numbers that decide the hybrid rule, and hand them to the reader as a file.
// Course kit, module 10

// 1. HOW MANY MEGABYTES DID THIS PAGE (OR WORKER) DOWNLOAD? ###################################

// The browser keeps a timing entry for every file it fetched. transferSize is the bytes that came
// over the network: 0 when the file came from the cache, which is what you want on a second visit.
// A file from another site reports 0 unless that site allows it, so read the number as a floor.
export function downloadedMB(entries) {
  const bytes = entries.reduce((sum, e) => sum + (e.transferSize || 0), 0);
  return Math.round((bytes / 1048576) * 10) / 10;
}

// 2. ONE LIST OF RUNS PER DEVICE ###################################

const runs = [];
export function record(run) { runs.push(run); }   // run = { path, engine, reply_ms, tokens_per_s }

const median = (xs) => {
  const s = xs.filter((x) => typeof x === "number").sort((a, b) => a - b);
  return s.length ? s[Math.floor(s.length / 2)] : null;
};

// The device's entry for measures.json. Medians, so one slow first answer does not decide the rule.
export function summary(device, load) {
  const browser = runs.filter((r) => r.path !== "server");
  return {
    device,
    engine: load.engine || null,
    download_mb: load.download_mb ?? null,
    load_ms: load.load_ms ?? null,
    reply_ms: median(browser.map((r) => r.reply_ms)),
    tokens_per_s: median(browser.map((r) => r.tokens_per_s)),
    server_reply_ms: median(runs.filter((r) => r.path === "server").map((r) => r.reply_ms)),
    runs: runs.length,
  };
}

// 3. SAVE IT: the reader presses a button and gets one JSON file ###################################

// Paste each device's object into the "devices" list in measures.json (at least two devices).
export function saveFile(obj, name = "measures-device.json") {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([JSON.stringify(obj, null, 2)], { type: "application/json" }));
  a.download = name;
  a.click();
}
