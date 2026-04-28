// Commands.js — Interface de commande / chat avec NAYA V10
import wsStore from '../core/ws.js';

export default function Commands() {
  const root = document.createElement("div");
  const history = [];

  const GW_URL = "ws://127.0.0.1:8766";
  let ws = null;
  let wsReady = false;

  function connectGateway() {
    ws = new WebSocket(GW_URL);
    ws.onopen = () => {
      wsReady = true;
      renderStatus("CONNECTED");
    };
    ws.onmessage = e => {
      try {
        const data = JSON.parse(e.data);
        if (data.type === "gateway_ready") return;
        if (data.response) {
          addMsg("naya", data.response, data.voice);
        } else if (data.type === "rejected") {
          addMsg("naya", `⚠️ Commande rejetée: ${data.reason}`, false);
        } else if (data.type === "error") {
          addMsg("naya", `❌ Erreur: ${data.reason}`, false);
        }
      } catch (_) {}
    };
    ws.onclose = () => {
      wsReady = false;
      renderStatus("DISCONNECTED");
      setTimeout(connectGateway, 3000);
    };
    ws.onerror = () => { wsReady = false; renderStatus("ERROR"); };
  }

  function addMsg(who, text, voice = false) {
    history.push({ who, text, ts: Date.now(), voice });
    renderChat();
    if (voice && who === "naya" && "speechSynthesis" in window) {
      const u = new SpeechSynthesisUtterance(text);
      u.lang = "fr-FR";
      speechSynthesis.speak(u);
    }
  }

  function sendMsg(text) {
    if (!text.trim()) return;
    addMsg("user", text);
    if (ws && wsReady) {
      ws.send(JSON.stringify({
        intent: "USER_MESSAGE",
        text,
        timestamp: Date.now()
      }));
    } else {
      // Fallback: appel API REST
      fetch("/brain/think", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: text, task_type: "strategic" })
      }).then(r => r.json())
        .then(d => addMsg("naya", d.text || "Pas de réponse LLM", true))
        .catch(() => addMsg("naya", "NAYA opérationnelle — LLM non configuré", false));
    }
  }

  let gwStatus = "DISCONNECTED";

  function renderStatus(s) {
    gwStatus = s;
    const el = root.querySelector("#gw-status");
    if (el) {
      el.textContent = s;
      el.className = `badge ${s==='CONNECTED'?'ok':'err'}`;
    }
  }

  function renderChat() {
    const feed = root.querySelector("#chat-feed");
    if (!feed) return;
    feed.innerHTML = history.slice(-30).map(m => `
      <div class="chat-msg ${m.who}">
        ${m.who === "naya" ? "" : ""}
        ${m.text}
        ${m.voice ? ' <span style="font-size:0.65rem;color:#00ff8866">🔊</span>' : ""}
        <div style="font-size:0.65rem;color:#555;margin-top:3px">${new Date(m.ts).toLocaleTimeString()}</div>
      </div>
    `).join("");
    feed.scrollTop = feed.scrollHeight;
  }

  root.innerHTML = `
    <div class="card" style="margin-bottom:10px">
      <div style="display:flex;align-items:center;justify-content:space-between">
        <span style="font-size:0.85rem">CommandGateway :8766</span>
        <span id="gw-status" class="badge err">CONNECTING</span>
      </div>
      <div style="font-size:0.72rem;color:#555;margin-top:4px">Pipeline sécurisé 10 étapes — signature · replay guard · permission matrix · REAPERS</div>
    </div>
    <div class="card" style="margin-bottom:10px;min-height:300px;max-height:400px;overflow-y:auto;display:flex;flex-direction:column" id="chat-feed">
      <div style="color:#555;font-size:0.8rem;text-align:center;padding:20px">Connecté à NAYA — Envoyez une intention...</div>
    </div>
    <div class="card">
      <div style="display:flex;gap:8px;align-items:flex-end">
        <textarea id="msg-input" rows="2" placeholder="Votre intention pour NAYA..." style="flex:1;resize:none"></textarea>
        <button class="send-btn" id="send-btn">Envoyer</button>
      </div>
      <div style="display:flex;gap:6px;margin-top:8px;flex-wrap:wrap">
        ${["HUNT", "STATUS", "CYCLE", "PIPELINE", "PROJETS"].map(cmd =>
          `<button onclick="document.getElementById('msg-input').value='${cmd}';document.getElementById('send-btn').click()"
           style="background:#1a1a2e;color:#888;border:1px solid #333;padding:3px 10px;cursor:pointer;border-radius:3px;font-size:0.72rem;">${cmd}</button>`
        ).join("")}
      </div>
    </div>
  `;

  root.querySelector("#send-btn").onclick = () => {
    const input = root.querySelector("#msg-input");
    if (input.value.trim()) {
      sendMsg(input.value.trim());
      input.value = "";
    }
  };
  root.querySelector("#msg-input").onkeydown = e => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      root.querySelector("#send-btn").click();
    }
  };

  connectGateway();
  return root;
}
