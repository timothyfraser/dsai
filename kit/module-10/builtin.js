// builtin.js
// Use the browser's own language model when the browser has one, and say so when it does not.
// Course kit, module 10

// Per Chrome's and Edge's pages (dated in this module's Sources), Chrome 148 and later on desktop offers this to web
// pages as the Prompt API (LanguageModel); Edge has its own in developer preview. Safari, Firefox
// and Chrome on phones do not. So this file is an extra path, never the only one.

// 1. ASK FIRST: is there a built-in model, and is it ready? ###################################

// Returns { model, why }. model is null whenever the page must use another path; why says which.
export async function builtinModel() {
  if (!("LanguageModel" in self)) return { model: null, why: "this browser has no built-in model" };
  let state;
  try { state = await self.LanguageModel.availability(); }
  catch (err) { return { model: null, why: "the built-in model did not answer: " + err.message }; }
  // "available" means ready now. Anything else ("downloadable", "downloading", "unavailable")
  // would start a large download or cannot run here, so this page does not wait for it.
  if (state !== "available") return { model: null, why: "the built-in model is " + state + " on this device" };
  return { model: { generate }, why: "the browser's own model is ready" };
}

// 2. ONE QUESTION, SAME SHAPE AS THE OTHER PATHS ###################################

// A new session per question keeps old questions out of new answers.
async function generate(messages) {
  const [system, ...rest] = messages;
  const session = await self.LanguageModel.create({ initialPrompts: [system] });
  try {
    const text = await session.prompt(rest.map((m) => m.content).join("\n"));
    return { text, tokens: null };   // the Prompt API does not report a token count for the reply
  } finally {
    session.destroy();
  }
}
