// voice.js
// Let the reader speak the question, and say plainly whether the speech stayed on the device.
// Course kit, module 10

// The Web Speech API turns speech into text. In Chrome it is SpeechRecognition (older builds:
// webkitSpeechRecognition). Some browsers send the sound to a speech service online to recognise it;
// processLocally = true asks for recognition on the device, where the browser offers it.

export function canListen() {
  return "SpeechRecognition" in self || "webkitSpeechRecognition" in self;
}

// listen(onText) starts one recording. It resolves to the path the speech took.
export function listen(onText) {
  return new Promise((resolve) => {
    if (!canListen()) return resolve("no speech input in this browser: type the question");
    const Rec = self.SpeechRecognition || self.webkitSpeechRecognition;
    const rec = new Rec();
    rec.lang = "en-US";
    // Ask, never assume: only set processLocally where the browser has it.
    const local = "processLocally" in rec;
    if (local) rec.processLocally = true;
    rec.onresult = (e) => onText(e.results[0][0].transcript);
    rec.onerror = (e) => resolve("speech failed (" + e.error + "): type the question");
    rec.onend = () => resolve(local ? "on-device recognition asked for" : "this browser may send speech to its speech service");
    rec.start();
  });
}
