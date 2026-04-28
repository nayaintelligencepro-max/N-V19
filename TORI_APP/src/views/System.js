// System.js — Dashboard graphique NAYA V10
import wsStore from '../core/ws.js';

export default function System() {
  const root = document.createElement("div");
  let metricsData = null;
  let assetsData = null;

  async function loadExtended() {
    try {
      const [mRes, aRes] = await Promise.all([
        fetch('/monitoring/alerts').then(r => r.json()).catch(() => null),
        fetch('/system/assets').then(r => r.json()).catch(() => null),
      ]);
      metricsData = mRes;
      assetsData = aRes;
    } catch(e) {}
  }

  function fmt(s) {
    if (!s) return "—";
    if (typeof s === "object") return JSON.stringify(s).substring(0, 60);
    return String(s).substring(0, 60);
  }

  function statusBadge(v) {
    if (!v || v === "inactive") return '<span class="badge err">INACTIVE</span>';
    if (String(v).includes("ACTIVE") || String(v).includes("active") || String(v).includes("ONLINE"))
      return '<span class="badge ok">ACTIVE</span>';
    if (String(v).includes("error") || String(v).includes("ERROR"))
      return '<span class="badge err">ERROR</span>';
    return '<span class="badge info">' + String(v).substring(0,20) + '</span>';
  }

  function healthBadge(pct) {
    if (pct === undefined || pct === null) return '<span class="badge info">N/A</span>';
    const n = parseFloat(pct);
    if (n > 85) return `<span class="badge err">${n.toFixed(0)}%</span>`;
    if (n > 70) return `<span class="badge warn">${n.toFixed(0)}%</span>`;
    return `<span class="badge ok">${n.toFixed(0)}%</span>`;
  }

  function render(state) {
    const sys = state.systemStatus;
    if (!sys) {
      root.innerHTML = '<div class="card"><h3>System</h3><p style="color:#888">Connexion au système...</p></div>';
      return;
    }
    const amels = sys.ameliorations_v7 || {};
    const tori  = sys.tori_infrastructure || {};
    const brain = sys.brain || {};
    const auto  = sys.autonomous || {};
    const metrics = metricsData || {};
    const assets  = assetsData || {};

    root.innerHTML = `
      <div class="grid3" style="margin-bottom:12px">
        <div class="card" style="text-align:center">
          <div class="big-num">${sys.version || 'V10'}</div>
          <div class="label">VERSION</div>
        </div>
        <div class="card" style="text-align:center">
          <div class="big-num" style="color:${sys.status==='OPERATIONAL'?'#00ff88':'#ffaa00'}">${sys.status}</div>
          <div class="label">STATUT</div>
        </div>
        <div class="card" style="text-align:center">
          <div class="big-num">${sys.components || 0}</div>
          <div class="label">MODULES</div>
        </div>
      </div>

      <div class="grid2" style="margin-bottom:12px">
        <div class="card">
          <h3>⏱ Uptime</h3>
          <div style="font-size:1.2rem;color:#00ff88">${sys.uptime || '—'}</div>
          <div class="label">${sys.environment || 'local'} · ${sys.timestamp ? new Date(sys.timestamp).toLocaleTimeString() : ''}</div>
        </div>
        <div class="card">
          <h3>🧠 LLM Brain</h3>
          <div>${brain.available ? '<span class="badge ok">ONLINE</span>' : '<span class="badge warn">NO_KEY</span>'}</div>
          <div class="label" style="margin-top:6px">${brain.cache_size !== undefined ? brain.cache_size + ' cache' : ''} ${brain.providers_online || ''}</div>
        </div>
      </div>

      <div class="card" style="margin-bottom:12px">
        <h3>🖥️ Métriques Système</h3>
        <div class="grid3">
          <div>
            <div class="label">CPU</div>
            ${healthBadge(metrics.metrics?.cpu_percent ?? null)}
          </div>
          <div>
            <div class="label">RAM</div>
            ${healthBadge(metrics.metrics?.memory_percent ?? null)}
          </div>
          <div>
            <div class="label">Disque</div>
            ${healthBadge(metrics.metrics?.disk_percent ?? null)}
          </div>
        </div>
        ${metrics.alerts && metrics.alerts.length > 0
          ? `<div style="margin-top:8px">${metrics.alerts.map(a => `<span class="badge err" style="margin-right:4px">${a}</span>`).join('')}</div>`
          : '<div style="margin-top:8px;color:#555;font-size:0.78rem">✅ Aucune alerte système</div>'
        }
      </div>

      <div class="card" style="margin-bottom:12px">
        <h3>🔒 Intégrité Assets</h3>
        ${assets.initialized
          ? `<div>
              ${assets.all_critical_present
                ? '<span class="badge ok">TOUS PRÉSENTS</span>'
                : '<span class="badge err">FICHIERS MANQUANTS</span>'
              }
              <span style="margin-left:10px;color:#888;font-size:0.8rem">
                ${assets.critical_assets || 0} assets critiques · ${assets.total_tracked || 0} suivis
              </span>
            </div>`
          : '<span class="badge warn">Non initialisé</span>'
        }
      </div>

      <div class="card" style="margin-bottom:12px">
        <h3>📡 Infrastructure TORI — 3 WebSocket</h3>
        <div class="grid3">
          <div>
            <div class="label">EventStream :8765</div>
            ${statusBadge(tori.event_stream)}
          </div>
          <div>
            <div class="label">CommandGateway :8766</div>
            ${statusBadge(tori.command_gateway)}
          </div>
          <div>
            <div class="label">ObservationBus :8899</div>
            ${statusBadge(tori.observation_bus)}
          </div>
        </div>
      </div>

      <div class="card" style="margin-bottom:12px">
        <h3>⚡ 8 Améliorations V10</h3>
        <div class="grid2">
          ${Object.entries(amels).map(([k, v]) => `
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
              ${statusBadge(v)}
              <span style="font-size:0.78rem;color:#aaa">${k.replace(/_/g,' ')}</span>
            </div>
          `).join('')}
        </div>
      </div>

      <div class="card">
        <h3>🤖 Autonomous Engine</h3>
        <div style="font-size:0.8rem">
          <span class="badge ${auto.running?'ok':'warn'}">${auto.running?'RUNNING':'STANDBY'}</span>
          <span style="margin-left:10px;color:#888">${auto.total_missions_completed || 0} missions · ${auto.active_missions || 0} actives</span>
        </div>
      </div>
    `;
  }

  // Chargement initial + refresh toutes les 30s
  loadExtended().then(() => wsStore.subscribe(s => render(s)));
  setInterval(loadExtended, 30000);

  return root;
}
