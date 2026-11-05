// match.js: how the field assistant picks a note, kept in its own file so two things share it:
// the page (app.js) and refusal.mjs, which measures refusal rates on a laptop with no model.
// No browser and no engine here, so Node can import it as it is.

// Words that carry no meaning for matching.
const STOP = new Set("a an the and or of to in on at is are was be do i you it my what how when where which why with for from by can should".split(" "));
export const words = (s) => s.toLowerCase().match(/[a-z0-9-]+/g)?.filter((w) => !STOP.has(w) && w.length > 2) ?? [];

// Retrieval by shared words. Small, readable, and it needs no second model.
// The score is how many of the note's words also appear in the question.
export function bestNote(question, notes) {
  const q = new Set(words(question));
  let best = null, score = 0;
  for (const n of notes) {
    const s = words(n.title + " " + n.text).filter((w) => q.has(w)).length;
    if (s > score) { best = n; score = s; }
  }
  return { note: best, score };
}
