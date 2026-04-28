// src/main.js — TORI V19 — Bootstrap cockpit souverain
import { connectWS } from './core/ws.js';
import { views } from './views/index.js';
import { restoreCustomization } from './views/Customization.js';

// Restaurer personnalisations sauvegardées avant d'afficher l'UI
restoreCustomization();

const nav = document.getElementById("nav");
const view = document.getElementById("view");
const status = document.getElementById("status");

// Navigation
Object.keys(views).forEach(k => {
  const b = document.createElement("button");
  b.textContent = k;
  b.onclick = () => {
    document.querySelectorAll("nav button").forEach(x => x.classList.remove("active"));
    b.classList.add("active");
    const result = views[k]();
    if (typeof result === "string") {
      view.innerHTML = result;
    } else {
      view.innerHTML = "";
      view.appendChild(result);
    }
  };
  nav.appendChild(b);
});

// CSS inline pour le cockpit
const style = document.createElement("style");
style.textContent = `
* { box-sizing: border-box; }
body { background: #0a0a0f; color: #e0e0e0; font-family: 'Courier New', monospace; margin: 0; }
header { background: #111; padding: 10px 20px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #00ff8833; }
header h2 { margin: 0; color: #00ff88; font-size: 1rem; }
#status { font-size: 0.8rem; padding: 4px 10px; border-radius: 4px; background: #1a1a2e; }
nav { background: #111; padding: 8px 20px; display: flex; gap: 6px; flex-wrap: wrap; border-bottom: 1px solid #222; }
nav button { background: #1a1a2e; color: #aaa; border: 1px solid #333; padding: 5px 12px; cursor: pointer; border-radius: 4px; font-size: 0.78rem; }
nav button:hover, nav button.active { background: #003322; color: #00ff88; border-color: #00ff88; }
#view { padding: 16px 20px; }
.card { background: #111; border: 1px solid #222; border-radius: 6px; padding: 14px; margin-bottom: 12px; }
.card h3 { margin: 0 0 8px; font-size: 0.9rem; color: #00ff88; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.grid3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 0.72rem; font-weight: bold; }
.badge.ok { background: #003322; color: #00ff88; }
.badge.warn { background: #332200; color: #ffaa00; }
.badge.err { background: #330000; color: #ff4444; }
.badge.info { background: #001433; color: #4499ff; }
.event-item { padding: 6px 8px; border-left: 3px solid #333; margin-bottom: 6px; font-size: 0.78rem; }
.event-item.SUCCESS { border-color: #00ff88; }
.event-item.INFO { border-color: #4499ff; }
.event-item.WARNING { border-color: #ffaa00; }
.event-item.ERROR, .event-item.CRITICAL { border-color: #ff4444; }
.mono { font-family: monospace; font-size: 0.78rem; color: #88cc88; }
.big-num { font-size: 1.6rem; font-weight: bold; color: #00ff88; }
.label { font-size: 0.7rem; color: #888; margin-top: 2px; }
input, textarea { background: #1a1a2e; color: #e0e0e0; border: 1px solid #333; padding: 8px 10px; border-radius: 4px; font-family: monospace; font-size: 0.85rem; width: 100%; }
input:focus, textarea:focus { outline: none; border-color: #00ff88; }
button.send-btn { background: #003322; color: #00ff88; border: 1px solid #00ff88; padding: 8px 18px; cursor: pointer; border-radius: 4px; font-size: 0.85rem; margin-top: 6px; }
button.send-btn:hover { background: #00ff88; color: #000; }
.chat-msg { padding: 8px 12px; border-radius: 6px; margin-bottom: 8px; max-width: 80%; font-size: 0.85rem; line-height: 1.4; }
.chat-msg.user { background: #1a2a3a; margin-left: auto; text-align: right; }
.chat-msg.naya { background: #0a1a0a; border: 1px solid #00ff8833; }
.chat-msg.naya::before { content: "⚡ NAYA  "; color: #00ff88; font-weight: bold; font-size: 0.75rem; display: block; margin-bottom: 4px; }
.progress { background: #1a1a2e; border-radius: 4px; height: 8px; overflow: hidden; }
.progress-bar { height: 100%; background: #00ff88; transition: width 0.3s; }
`;
document.head.appendChild(style);

connectWS(status);

// Vue initiale : Boot
const firstBtn = nav.querySelector("button");
if (firstBtn) firstBtn.click();
