// Boot.js — Progress démarrage NAYA V10
import wsStore from '../core/ws.js';

export default function Boot() {
  const root = document.createElement("div");

  const STEPS = [
    "Database","Constitution","Event Bus","Business Engines","Executive Engine",
    "Channel Registry","Evolution System","REAPERS Security","LLM Brain",
    "Business Factory","Autonomous Engine","Scheduler","Full Activator",
    "A1 EventStream :8765","A2 CommandGW :8766","A3 ObsBus :8899",
    "A4 Sovereign Automation","Sovereign Engine V3","System Registry"
  ];

  function render(state) {
    const sys = state.systemStatus;
    const comps = sys ? (sys.component_list || []) : [];
    const status = sys ? sys.status : "BOOTING";
    const TOTAL = Math.max(STEPS.length, comps.length);
    const pct = comps.length > 0 ? Math.round(comps.length / TOTAL * 100) : 0;

    root.innerHTML = `
      <div class="card">
        <h3>⚡ NAYA SUPREME V10.0 — Boot Status</h3>
        <div style="margin-bottom:12px">
          <span class="badge ${status==='OPERATIONAL'?'ok':'warn'}">${status}</span>
          <span style="margin-left:10px;font-size:0.8rem;color:#888">${comps.length} modules actifs</span>
        </div>
        <div class="progress" style="margin-bottom:16px">
          <div class="progress-bar" style="width:${pct}%"></div>
        </div>
        <div style="font-size:0.75rem;color:#888;margin-bottom:12px">${pct}% chargé</div>
      </div>
      <div class="grid3">
        ${STEPS.map(step => {
          const active = comps.some(c => c.toLowerCase().includes(step.toLowerCase().replace(/[: ]/g,'').substring(0,8)));
          const isA = step.startsWith("A");
          return `<div class="card" style="padding:10px">
            <div style="font-size:0.78rem;color:${active?'#00ff88':isA?'#ffaa00':'#555'}">${active?'✅':'⏳'} ${step}</div>
          </div>`;
        }).join('')}
      </div>
    `;
  }

  wsStore.subscribe(s => render(s));
  return root;
}
