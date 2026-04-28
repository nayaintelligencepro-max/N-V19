// Text.js — Affichage réponses texte NAYA V10
import wsStore from '../core/ws.js';

export default function Text() {
  const root = document.createElement("div");
  const msgs = [];

  function render(state) {
    const ev = state.lastEvent;
    if (ev && ev.source === "command-gateway") {
      const data = ev.payload || {};
      if (data.response || data.text) {
        msgs.unshift({ text: data.response || data.text, ts: Date.now() });
        if (msgs.length > 50) msgs.pop();
      }
    }

    root.innerHTML = `
      <div class="card" style="margin-bottom:10px">
        <h3>📝 Réponses texte NAYA</h3>
        <div style="font-size:0.72rem;color:#555">Écoute CommandGateway :8766 · source: command-gateway</div>
      </div>
      <div>
        ${msgs.length === 0
          ? '<div class="card" style="color:#555;font-size:0.8rem;text-align:center;padding:20px">En attente des réponses NAYA...</div>'
          : msgs.map(m => `
            <div class="card">
              <div style="font-size:0.72rem;color:#555;margin-bottom:6px">${new Date(m.ts).toLocaleTimeString()}</div>
              <div style="font-size:0.85rem;line-height:1.5;color:#e0e0e0">${m.text}</div>
            </div>
          `).join("")}
      </div>
    `;
  }

  wsStore.subscribe(s => render(s));
  return root;
}
