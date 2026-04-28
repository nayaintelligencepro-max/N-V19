// EventStream.js — Feed live des événements NAYA V10
import wsStore from '../core/ws.js';

const FILTERS = ["ALL", "PAIN_DETECTED", "OFFER_CREATED", "CONTENT_GENERATED",
                 "SOVEREIGN_CYCLE", "MISSION", "REAPERS", "SYSTEM"];

export default function EventStream() {
  const root = document.createElement("div");
  let activeFilter = "ALL";

  function timeAgo(ts) {
    const d = Math.floor((Date.now() - ts) / 1000);
    if (d < 60) return `${d}s`;
    if (d < 3600) return `${Math.floor(d/60)}m`;
    return `${Math.floor(d/3600)}h`;
  }

  function eventLevel(ev) {
    const p = ev.payload || {};
    return p.level || "INFO";
  }

  function eventKind(ev) {
    const p = ev.payload || {};
    return p.kind || p.type || ev.source || "EVENT";
  }

  function renderEvent(ev) {
    const level = eventLevel(ev);
    const kind = eventKind(ev);
    const p = ev.payload || {};
    const detail = p.payload ? JSON.stringify(p.payload).substring(0, 80) : (p.message || JSON.stringify(p).substring(0,60));
    return `<div class="event-item ${level}">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <span class="badge ${level==='SUCCESS'?'ok':level==='ERROR'||level==='CRITICAL'?'err':level==='WARNING'?'warn':'info'}">${kind}</span>
        <span style="font-size:0.68rem;color:#666">${timeAgo(ev.timestamp)} · ${ev.source}</span>
      </div>
      <div style="margin-top:4px;font-size:0.75rem;color:#bbb;word-break:break-all">${detail}</div>
    </div>`;
  }

  function render(state) {
    const events = state.events || [];
    const filtered = activeFilter === "ALL" ? events :
      events.filter(ev => eventKind(ev).includes(activeFilter));

    const src = state.sources || {};
    const esStatus = src["event-stream"]?.status || "DISCONNECTED";

    root.innerHTML = `
      <div class="card" style="margin-bottom:10px">
        <div style="display:flex;align-items:center;justify-content:space-between">
          <span style="font-size:0.85rem">EventStream :8765
            <span class="badge ${esStatus==='CONNECTED'?'ok':'err'}" style="margin-left:6px">${esStatus}</span>
          </span>
          <span style="font-size:0.75rem;color:#888">${events.length} événements bufferisés</span>
        </div>
        <div style="display:flex;gap:4px;flex-wrap:wrap;margin-top:8px" id="filters"></div>
      </div>
      <div id="events-feed">
        ${filtered.length === 0
          ? '<div style="color:#555;font-size:0.8rem;padding:20px;text-align:center">Aucun événement — en attente du flux live...</div>'
          : filtered.slice(0, 40).map(renderEvent).join('')}
      </div>
    `;

    // Boutons filtres
    const filterDiv = root.querySelector("#filters");
    FILTERS.forEach(f => {
      const btn = document.createElement("button");
      btn.textContent = f;
      btn.style.cssText = `background:${activeFilter===f?'#003322':'#1a1a2e'};color:${activeFilter===f?'#00ff88':'#888'};border:1px solid ${activeFilter===f?'#00ff88':'#333'};padding:3px 8px;cursor:pointer;border-radius:3px;font-size:0.72rem;`;
      btn.onclick = () => { activeFilter = f; render(wsStore.getState()); };
      filterDiv.appendChild(btn);
    });
  }

  wsStore.subscribe(s => render(s));
  return root;
}
