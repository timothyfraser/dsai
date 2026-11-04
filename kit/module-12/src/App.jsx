// App.jsx
// One page that asks your team's API a question and shows the answer with where it came from.
// Course kit, module 12

// Read it top to bottom; each numbered section is one idea.
// The page has five states, and the reader must always be able to tell which one they are in.

// 0. SETUP ###################################

import React, { useState } from "react";     // for state: values that redraw the page when they change
import { askApi, API_URL } from "./api.js";  // the one file that talks to the API

// 1. THE FIVE STATES ###################################

// idle:    nothing asked yet
// empty:   Ask was pressed with an empty box, so nothing was sent
// loading: the question is on its way; the button is off so it cannot be sent twice
// answer:  the API answered; show the answer AND its source
// error:   no answer; say why in one plain sentence and what to do next
const MESSAGES = {
  idle: "Type a question and press Ask.",
  empty: "Type a question first. Nothing was sent.",
  loading: "Asking your team's system...",
  answer: "Answered.",
  error: "No answer this time.",
};

export default function App() {
  const [question, setQuestion] = useState("");
  const [state, setState] = useState("idle");
  const [reply, setReply] = useState(null);

  // 2. ASK, AND MOVE BETWEEN STATES ###################################

  // A form's submit event fires for the button AND for the Enter key, so keyboard users get the same page.
  async function onSubmit(event) {
    event.preventDefault();
    const q = question.trim();
    if (!q) { setState("empty"); setReply(null); return; }
    setState("loading");
    setReply(null);  // clear the old answer at once: an old answer under a new question is a wrong answer
    const r = await askApi(q);
    setReply(r);
    setState(r.ok ? "answer" : "error");
  }

  // 3. DRAW THE PAGE ###################################

  // Every input has a <label>, so a screen reader says what the box is for and a tap on the words focuses it.
  // role="status" reads the state aloud when it changes; role="alert" interrupts, so it is kept for errors.
  return (
    <main data-state={state}>
      <h1>Ask the team system</h1>
      <p className="hint">Answers come from {API_URL || "no API yet"}.</p>

      <form onSubmit={onSubmit}>
        <label htmlFor="q">Your question</label>
        <div className="row">
          <input id="q" value={question} onChange={(e) => setQuestion(e.target.value)} autoComplete="off" />
          <button type="submit" disabled={state === "loading"}>{state === "loading" ? "Asking..." : "Ask"}</button>
        </div>
      </form>

      <p id="status" role="status" aria-live="polite" aria-busy={state === "loading"}>{MESSAGES[state]}</p>

      {/* 4. THE ANSWER AND ITS SOURCE: the source is part of the answer, never hidden behind a click */}
      {state === "answer" && (
        <section id="answer" aria-labelledby="answer-h">
          <h2 id="answer-h">Answer</h2>
          <p id="answer-text">{reply.answer}</p>
          <p id="source" className={reply.source ? "src" : "src missing"}>
            {reply.source ? "Source: " + reply.source : "Source: the API did not say. Check this answer before you use it."}
          </p>
        </section>
      )}

      {/* 5. THE ERROR: what went wrong, in words, and what the reader can do about it */}
      {state === "error" && (
        <p id="error" role="alert">
          No answer: {reply.why}. Try again in a minute; if it keeps happening, tell the team that runs the API.
        </p>
      )}
    </main>
  );
}
