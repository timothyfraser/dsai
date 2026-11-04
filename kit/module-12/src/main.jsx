// main.jsx
// The entry point: find the empty box in index.html and draw the App inside it.
// Course kit, module 12

// 0. SETUP ###################################

import React from "react";                    // for JSX, the HTML-like lines in App.jsx
import { createRoot } from "react-dom/client"; // for drawing React into the page
import App from "./App.jsx";                  // the page itself

// 1. DRAW THE APP ###################################

// index.html holds one empty <div id="root">. React fills it and redraws it whenever state changes.
createRoot(document.getElementById("root")).render(<App />);
