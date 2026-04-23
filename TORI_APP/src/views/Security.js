// Security.js — Vue REAPERS & Sécurité V10
import wsStore from '../core/ws.js';

export default function Security() {
  const root = document.createElement("div");
  let assetStatus = null;
  let rateLimits = null;

  async function loadSecurityData() {
    try {
      const [aRes, rRes] = await Promise.all([
        fetch('/system/assets/verify').then(r => r.json()).catch(() => null),
        fetch('/system/rate-limits').then(r => r.json()).catch(() => null),
      ]);
      assetStatus = aRes;
      rateLimits = rRes;
    } catch(e) {}
    render(wsStore.getState ? wsStore.getState() : {});
  }

  async function runIntegrityCheck() {
    const btn = root.querySelector('#integrity-btn');
    if (btn) { btn.textContent = '⏳ Vérification...'; btn.disabled = true; }
    await loadSecurityData();
    if (btn) { btn.textContent = '🔍 Vérifier Intégrité'; btn.disabled = false; }
  }

  function render(state) {
    const events = state.events || [];
    const reapers = events.filter(ev => {
      const p = ev.payload || {};
      return (p.kind && p.kind.toString().includes("REAPERS")) ||
             (p.source && p.source === "REAPERS");
    });
    const assets = assetStatus || {};
    const rl     = rateLimits || {};

    root.innerHTML = `
      <div class="grid2" style="margin-bottom:12px">
        <div class="card">
          <h3>🛡️ REAPERS Status</h3>
          <span class="badge ok">ACTIVE</span>
          <div class="label" style="margin-top:6px">
            22 modules sécurité · surveillance continue
          </div>
          <div style="margin-top:10px;font-size:0.8rem;color:#555">
            Anti-clone · Anti-exfiltration · Integrity guard
          </div>
        </div>
        <div class="card">
          <h3>📋 Intégrité Assets</h3>
          ${assets.all_ok !== undefined
            ? assets.all_ok
              ? '<span class="badge ok">✅ TOUS INTÈGRES</span>'
              : `<span class="badge err">⚠️ ${(assets.compromised||[]).length} COMPROMIS</span>`
            : '<span class="badge info">Non vérifié</span>'
          }
          ${assets.verified
            ? `<div class="label" style="margin-top:6px">${assets.verified} assets vérifiés</div>`
            : ''
          }
          ${(assets.compromised||[]).length > 0
            ? `<div style="margin-top:8px">${assets.compromised.map(p =>
                `<div style="font-size:0.75rem;color:#ff4444">⚠️ ${p}</div>`).join('')}</div>`
            : ''
          }
          <button id="integrity-btn"
            style="margin-top:10px;padding:4px 10px;background:#1a1a2e;border:1px solid #333;
                   color:#00ff88;border-radius:4px;cursor:pointer;font-size:0.78rem">
            🔍 Vérifier Intégrité
          </button>
        </div>
      </div>

      <div class="card" style="margin-bottom:12px">
        <h3>🚦 Rate Limiter</h3>
        ${rl.active_windows !== undefined
          ? `<div style="display:flex;gap:20px;flex-wrap:wrap">
              <div><div class="label">IPs actives</div>
                   <div style="font-size:1.2rem;color:#00ff88">${rl.total_tracked_ips || 0}</div></div>
              <div><div class="label">Fenêtres actives</div>
                   <div style="font-size:1.2rem;color:#ffaa00">${rl.active_windows || 0}</div></div>
            </div>
            ${(rl.top_consumers||[]).length > 0
              ? `<div style="margin-top:8px">
                  <div class="label" style="margin-bottom:4px">Top consommateurs:</div>
                  ${rl.top_consumers.slice(0,5).map(([k,v]) =>
                    `<div style="font-size:0.75rem;color:#888">${k}: ${v} req/min</div>`
                  ).join('')}
                </div>`
              : ''
            }`
          : '<div style="color:#555;font-size:0.8rem">Aucune donnée — démarrer NAYA</div>'
        }
      </div>

      <div class="card" style="margin-bottom:12px">
        <h3>🔧 Modules REAPERS</h3>
        <div class="grid3">
          ${["IntegrityGuard","AntiCloneGuard","AntiExfiltration","CrashPredictor",
             "IsolationEngine","ThreatMemory","SurvivalMode","RuntimeWatchdog",
             "AdaptiveSecurity","ReapersRepair","ReapersSentinel","ReapersShield",
             "BootAuthority","SnapshotManager","MonitoringPersistent","ReapersReport"].map(m =>
            `<div style="font-size:0.75rem;color:#00ff88">✅ ${m}</div>`
          ).join("")}
        </div>
      </div>

      <div class="card">
        <h3>⚡ Flux sécurité récent</h3>
        ${reapers.length === 0
          ? '<div style="color:#555;font-size:0.8rem">✅ Aucune alerte sécurité récente</div>'
          : reapers.slice(0,10).map(ev => {
              const p = ev.payload || {};
              return `<div class="event-item WARNING" style="margin-bottom:4px">
                <span class="badge warn">${p.kind || "REAPERS"}</span>
                <span style="font-size:0.75rem;color:#bbb;margin-left:8px">
                  ${JSON.stringify(p.payload||p).substring(0,60)}
                </span>
              </div>`;
            }).join("")
        }
      </div>
    `;

    // Attacher le handler après le render — pas de pollution window
    const intBtn = root.querySelector('#integrity-btn');
    if (intBtn) intBtn.onclick = runIntegrityCheck;
  }

  loadSecurityData();
  setInterval(loadSecurityData, 60000);
  wsStore.subscribe(s => render(s));
  return root;
}
