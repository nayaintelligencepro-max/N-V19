// Projects.js — Vue 6 projets P01-P06 V10
import wsStore from '../core/ws.js';

const PROJECTS = [
  { id: "P01", name: "Cash Rapide", icon: "💰", desc: "Services express 24/48/72h", tiers: "1k→500k€", color: "#00ff88" },
  { id: "P02", name: "Google XR", icon: "🥽", desc: "Solutions AR/XR enterprise", tiers: "50k→150k€", color: "#4499ff" },
  { id: "P03", name: "NAYA Botanica", icon: "🌿", desc: "Cosmétiques DTC naturels", tiers: "49→499€", color: "#88cc44" },
  { id: "P04", name: "Tiny House", icon: "🏠", desc: "Habitat alternatif off-grid", tiers: "38k→115k€", color: "#ffaa00" },
  { id: "P05", name: "Marchés Oubliés", icon: "🌍", desc: "Marchés sous-exploités", tiers: "49→149€/mois", color: "#cc44ff" },
  { id: "P06", name: "Acquisition Immo", icon: "🏢", desc: "Stratégies acquisition", tiers: "2k→15k€", color: "#ff6644" },
];

export default function Projects() {
  const root = document.createElement("div");

  function render(state) {
    const events = state.events || [];
    const pipelineEvents = events.filter(ev => {
      const p = ev.payload || {};
      return p.kind === "PAIN_DETECTED" || p.kind === "OFFER_CREATED";
    });

    root.innerHTML = `
      <div class="card" style="margin-bottom:12px">
        <h3>📊 Portfolio — 6 Projets Actifs</h3>
        <div class="grid3">
          <div style="text-align:center">
            <div class="big-num">${pipelineEvents.length}</div>
            <div class="label">opportunités live</div>
          </div>
          <div style="text-align:center">
            <div class="big-num">6</div>
            <div class="label">projets actifs</div>
          </div>
          <div style="text-align:center">
            <div class="big-num" style="font-size:1rem;color:#ffaa00">∞</div>
            <div class="label">cycles autonomes</div>
          </div>
        </div>
      </div>
      <div class="grid2">
        ${PROJECTS.map(p => `
          <div class="card">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
              <span style="font-size:1.4rem">${p.icon}</span>
              <div>
                <div style="font-weight:bold;color:${p.color};font-size:0.9rem">${p.id} · ${p.name}</div>
                <div style="font-size:0.72rem;color:#888">${p.desc}</div>
              </div>
            </div>
            <div style="font-size:0.75rem;color:#666;margin-bottom:8px">Paliers: ${p.tiers}</div>
            <div style="display:flex;gap:6px">
              <button onclick="fetch('/projects/${p.id.toLowerCase()}/execute',{method:'POST'}).then(r=>r.json()).then(d=>alert('Mission: '+d.mission_id))"
                style="background:#001422;color:${p.color};border:1px solid ${p.color};padding:4px 10px;cursor:pointer;border-radius:3px;font-size:0.72rem;">▶ Execute</button>
              <button onclick="fetch('/projects/${p.id.toLowerCase()}/content',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({platform:'linkedin'})}).then(r=>r.json()).then(d=>alert('Content: '+d.mission_id))"
                style="background:#001422;color:#888;border:1px solid #333;padding:4px 10px;cursor:pointer;border-radius:3px;font-size:0.72rem;">✍ Content</button>
            </div>
          </div>
        `).join("")}
      </div>
    `;
  }

  wsStore.subscribe(s => render(s));
  return root;
}
