// Monitoring.js — Vue métriques système temps réel V10
export default function Monitoring() {
  const root = document.createElement("div");
  let data = null;
  let interval = null;

  async function load() {
    try {
      const [mRes, sRes, aRes] = await Promise.all([
        fetch('/monitoring/status').then(r => r.json()).catch(() => null),
        fetch('/scheduler/status').then(r => r.json()).catch(() => null),
        fetch('/system/assets').then(r => r.json()).catch(() => null),
      ]);
      data = { monitoring: mRes, scheduler: sRes, assets: aRes };
      render();
    } catch(e) {
      root.innerHTML = '<div class="card"><p style="color:#888">Monitoring indisponible</p></div>';
    }
  }

  function gauge(label, value, max=100, unit='%') {
    const pct = Math.min(100, (value/max)*100);
    const color = pct > 85 ? '#ff4444' : pct > 70 ? '#ffaa00' : '#00ff88';
    return `
      <div style="margin-bottom:12px">
        <div style="display:flex;justify-content:space-between;margin-bottom:4px">
          <span style="font-size:0.8rem;color:#888">${label}</span>
          <span style="font-size:0.8rem;color:${color}">${typeof value === 'number' ? value.toFixed(1) : value}${unit}</span>
        </div>
        <div style="height:6px;background:#1a1a2e;border-radius:3px">
          <div style="width:${pct}%;height:100%;background:${color};border-radius:3px;transition:width 0.3s"></div>
        </div>
      </div>`;
  }

  function render() {
    if (!data) return;
    const m  = data.monitoring  || {};
    const sc = data.scheduler   || {};
    const a  = data.assets      || {};
    const metrics = m.metrics || {};
    const alerts  = m.alerts  || [];
    const jobs    = sc.jobs   || {};

    root.innerHTML = `
      <div class="grid2" style="margin-bottom:12px">
        <div class="card">
          <h3>🖥️ Ressources Système</h3>
          ${gauge('CPU',    metrics.cpu_percent    || 0)}
          ${gauge('RAM',    metrics.memory_percent || 0)}
          ${gauge('Disque', metrics.disk_percent   || 0)}
          <div style="font-size:0.75rem;color:#555;margin-top:4px">
            Tick: ${m.tick || 0}
          </div>
        </div>
        <div class="card">
          <h3>⚠️ Alertes Actives</h3>
          ${alerts.length === 0
            ? '<div style="color:#00ff88;font-size:0.9rem">✅ Système sain</div>'
            : alerts.map(a => `<div class="badge err" style="display:block;margin-bottom:4px">${a}</div>`).join('')
          }
          <div style="margin-top:12px">
            <div class="label">Intégrité assets</div>
            ${a.all_critical_present
              ? '<span class="badge ok">✅ Intègres</span>'
              : '<span class="badge err">⚠️ Problème</span>'
            }
            <span style="color:#555;font-size:0.75rem;margin-left:8px">
              ${a.total_tracked || 0} fichiers suivis
            </span>
          </div>
        </div>
      </div>

      <div class="card" style="margin-bottom:12px">
        <h3>⏰ Scheduler — ${Object.keys(jobs).length} Jobs Autonomes</h3>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:8px">
          ${Object.entries(jobs).map(([name, j]) => {
            const nextMin = Math.round((j.next_run_in_s || 0) / 60);
            const intervalMin = Math.round((j.interval_s || 0) / 60);
            const hasError = j.error_count > 0;
            return `
              <div style="padding:8px;background:#0d0d1a;border-radius:6px;border:1px solid ${hasError?'#ff4444':'#1a1a2e'}">
                <div style="font-size:0.75rem;color:${j.enabled?'#00ff88':'#555'};font-weight:600">
                  ${j.enabled?'●':'○'} ${name.replace(/_/g,' ')}
                </div>
                <div style="font-size:0.7rem;color:#555;margin-top:2px">
                  ${intervalMin}min · ${j.run_count||0} runs
                  ${hasError ? `<span style="color:#ff4444"> · ${j.error_count} err</span>` : ''}
                </div>
                <div style="font-size:0.7rem;color:#888;margin-top:1px">
                  prochaine: ${nextMin > 0 ? nextMin+'min' : 'maintenant'}
                </div>
              </div>`;
          }).join('')}
        </div>
      </div>

      <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <h3 style="margin:0">Contrôles</h3>
          <button onclick="window._reloadMonitoring()"
            style="padding:4px 12px;background:#1a1a2e;border:1px solid #333;
                   color:#00ff88;border-radius:4px;cursor:pointer;font-size:0.78rem">
            🔄 Actualiser
          </button>
        </div>
      </div>
    `;
    window._reloadMonitoring = load;
  }

  load();
  interval = setInterval(load, 15000);

  // Cleanup on unmount
  root._cleanup = () => { if (interval) clearInterval(interval); };
  return root;
}
