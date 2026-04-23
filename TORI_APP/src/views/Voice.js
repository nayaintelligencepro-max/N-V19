// Voice.js — TTS NAYA V10
import wsStore from '../core/ws.js';

export default function Voice() {
  const root = document.createElement("div");
  let ttsEnabled = true;
  let speaking = false;

  function render(state) {
    const ev = state.lastEvent;
    if (ev && ev.source === "command-gateway" && ttsEnabled) {
      const data = ev.payload || {};
      if ((data.voice === true || data.voice === "true") && (data.response || data.text)) {
        const text = data.response || data.text;
        if ("speechSynthesis" in window) {
          speaking = true;
          updateSpeakingState();
          const u = new SpeechSynthesisUtterance(text);
          u.lang = "fr-FR";
          u.rate = 1.0;
          u.onend = () => { speaking = false; updateSpeakingState(); };
          speechSynthesis.speak(u);
        }
      }
    }
  }

  function updateSpeakingState() {
    const indicator = root.querySelector("#speaking-indicator");
    if (indicator) {
      indicator.textContent = speaking ? "🔊 NAYA parle..." : "🔇 En attente";
      indicator.style.color = speaking ? "#00ff88" : "#555";
    }
  }

  root.innerHTML = `
    <div class="card" style="text-align:center;padding:30px">
      <div style="font-size:3rem;margin-bottom:16px">🎤</div>
      <div id="speaking-indicator" style="font-size:1.1rem;color:#555">🔇 En attente</div>
      <div style="margin-top:20px">
        <button id="tts-toggle-btn"
          style="background:#003322;color:#00ff88;border:1px solid #00ff88;padding:10px 20px;cursor:pointer;border-radius:6px">
          🔊 Voix active
        </button>
      </div>
      <div style="font-size:0.75rem;color:#555;margin-top:16px">
        NAYA répond vocalement via le CommandGateway :8766<br>
        Navigateur requis: WebSpeech API
      </div>
    </div>
  `;

  const ttsToggleBtn = root.querySelector("#tts-toggle-btn");
  ttsToggleBtn.onclick = () => {
    ttsEnabled = !ttsEnabled;
    ttsToggleBtn.textContent = ttsEnabled ? "🔊 Voix active" : "🔇 Voix désactivée";
    ttsToggleBtn.style.background = ttsEnabled ? "#003322" : "#1a1a2e";
    ttsToggleBtn.style.borderColor = ttsEnabled ? "#00ff88" : "#555";
    ttsToggleBtn.style.color = ttsEnabled ? "#00ff88" : "#888";
  };

  wsStore.subscribe(s => render(s));
  return root;
}
