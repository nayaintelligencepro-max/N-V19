// Portfolio.js — Vue Portfolio 6 Projets NAYA
export default function Portfolio() {
  const root = document.createElement("div");
  let data = null;
  let interval = null;

  async function load() {
    try {
      const [portRes, cashRes] = await Promise.all([
        fetch('/portfolio').then(r => r.json()).catch(() => null),
        fetch('/pipeline').then(r => r.json()).catch(() => null),
      ]);
      data = { portfolio: portRes, cash: cashRes };
      render();
    } catch(e) {
      root.innerHTML = '<div class="card"><p style="color:#555">Portfolio indisponible</p></div>';
    }
  }

  async function triggerHunt(sectors) {
    const btn = root.querySelector('#hunt-btn');
    if (btn) { btn.textContent = '⏳ Chasse...'; btn.disabled = true; }
    try {
      const r = await fetch('/orchestrate/parallel', {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ sectors, mode: 'balanced' })
      });
      const res = await r.json();
      alert(`🎯 Chasse terminée: ${res.total_opportunities || 0} opportunités détectées`);
      await load();
    } catch(e) {}
    if (btn) { btn.textContent = '🎯 Chasse Multi-Secteurs'; btn.disabled = false; }
  }

  function statusBadge(status) {
    const cfg = {ACTIVE: ['#00ff88','✅'], BUILDING: ['#ffaa00','🔨'], PAUSED: ['#888','⏸']};
    const [color, icon] = cfg[status] || ['#888','?'];
    return `<span style="color:${color};font-size:0.75rem">${icon} ${status}</span>`;
  }

  function modelBadge(model) {
    const cfg = {one_time:'🔵 One-shot', subscription:'🔄 Récurrent', mixed:'💎 Mixte'};
    return `<span style="font-size:0.7rem;color:#888">${cfg[model]||model}</span>`;
  }

  function render() {
    const port = data?.portfolio || {};
    const kpis = port.kpis || {};
    const projects = port.projects || {};
    const cash = data?.cash || {};

    root.innerHTML = `
      <!-- KPIs Portfolio -->
      <div class="grid3" style="margin-bottom:12px">
        <div class="card" style="text-align:center">
          <div class="big-num" style="color:#00ff88">${(kpis.total_revenue_eur||0).toLocaleString('fr')}€</div>
          <div class="label">💰 Revenue Total</div>
        </div>
        <div class="card" style="text-align:center">
          <div class="big-num" style="color:#4499ff">${(kpis.total_mrr_eur||0).toLocaleString('fr')}€</div>
          <div class="label">📆 MRR (récurrent)</div>
        </div>
        <div class="card" style="text-align:center">
          <div class="big-num">${kpis.active_projects||Object.keys(projects).length}</div>
          <div class="label">🚀 Projets actifs</div>
        </div>
      </div>

      <!-- Pipeline Cash depuis cash engine -->
      ${cash.pipeline_total_eur !== undefined ? `
      <div class="card" style="margin-bottom:12px;border-left:3px solid #00ff88">
        <h3>💎 Cash Engine V10</h3>
        <div class="grid3">
          <div style="text-align:center">
            <div style="color:#00ff88;font-weight:bold;font-size:1.1rem">${(cash.pipeline_total_eur||0).toLocaleString('fr')}€</div>
            <div class="label">Pipeline total</div>
          </div>
          <div style="text-align:center">
            <div style="color:#ffaa00;font-weight:bold;font-size:1.1rem">${cash.active_deals||0}</div>
            <div class="label">Deals actifs</div>
          </div>
          <div style="text-align:center">
            <div style="color:#00ccff;font-weight:bold;font-size:1.1rem">${(cash.revenue_won_eur||0).toLocaleString('fr')}€</div>
            <div class="label">Encaissé</div>
          </div>
        </div>
      </div>` : ''}

      <!-- Actions globales -->
      <div class="card" style="margin-bottom:12px">
        <h3>⚡ Actions Globales</h3>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <button id="hunt-btn"
            style="background:#003322;color:#00ff88;border:1px solid #00ff88;padding:8px 16px;cursor:pointer;border-radius:4px;font-size:0.8rem">
            🎯 Chasse Multi-Secteurs
          </button>
          <button onclick="fetch('/sovereign/trigger',{method:'POST'}).then(r=>r.json()).then(d=>alert('Cycle déclenché: '+JSON.stringify(d).substring(0,100)))"
            style="background:#001422;color:#4499ff;border:1px solid #4499ff;padding:8px 16px;cursor:pointer;border-radius:4px;font-size:0.8rem">
            ⚡ Déclencher Sovereign
          </button>
          <button onclick="fetch('/revenue/scan',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}).then(()=>document.dispatchEvent(new CustomEvent('portfolio:reload')))"
            style="background:#001422;color:#ffaa00;border:1px solid #ffaa00;padding:8px 16px;cursor:pointer;border-radius:4px;font-size:0.8rem">
            🔍 Scan Revenue
          </button>
          <button onclick="fetch('/notify/pipeline_report',{method:'POST'}).then(r=>r.json()).then(d=>alert('Rapport Telegram: '+(d.sent?'✅ Envoyé':'❌ Échec')))"
            style="background:#001422;color:#888;border:1px solid #555;padding:8px 16px;cursor:pointer;border-radius:4px;font-size:0.8rem">
            📊 Rapport Telegram
          </button>
        </div>
      </div>

      <!-- 6 Projets -->
      <div class="grid2">
        ${Object.entries(projects).map(([pid, p]) => `
          <div class="card" style="border-left:3px solid ${p.status==='ACTIVE'?'#00ff88':p.status==='BUILDING'?'#ffaa00':'#444'}">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
              <div>
                <span style="font-size:0.7rem;color:#555;margin-right:6px">${pid}</span>
                <strong style="font-size:0.9rem">${p.name}</strong>
              </div>
              ${statusBadge(p.status)}
            </div>
            <div style="font-size:0.72rem;color:#888;margin-bottom:8px">${p.description}</div>
            ${modelBadge(p.model)}
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:10px">
              <div style="background:#111;padding:6px;border-radius:3px;text-align:center">
                <div style="color:#00ff88;font-weight:bold;font-size:0.9rem">${(p.revenue?.total||0).toLocaleString('fr')}€</div>
                <div style="font-size:0.65rem;color:#666">Revenue</div>
              </div>
              <div style="background:#111;padding:6px;border-radius:3px;text-align:center">
                <div style="color:#4499ff;font-weight:bold;font-size:0.9rem">${p.pipeline?.won||0}</div>
                <div style="font-size:0.65rem;color:#666">Deals WON</div>
              </div>
              <div style="background:#111;padding:6px;border-radius:3px;text-align:center">
                <div style="font-weight:bold;font-size:0.85rem">${p.pipeline?.qualified||0}</div>
                <div style="font-size:0.65rem;color:#666">Qualifiés</div>
              </div>
              <div style="background:#111;padding:6px;border-radius:3px;text-align:center">
                <div style="color:#ffaa00;font-weight:bold;font-size:0.85rem">${(p.premium_floor||0).toLocaleString('fr')}€</div>
                <div style="font-size:0.65rem;color:#666">Plancher</div>
              </div>
            </div>
            ${p.revenue?.mrr > 0 ? `<div style="margin-top:6px;font-size:0.72rem;color:#888">MRR: <span style="color:#00ff88">${p.revenue.mrr.toLocaleString('fr')}€/mois</span></div>` : ''}
          </div>
        `).join('')}
      </div>
    `;

    root.querySelector('#hunt-btn').onclick = () => triggerHunt(
      ['pme_b2b', 'startup_scaleup', 'healthcare_wellness', 'artisan_trades', 'ecommerce', 'liberal_professions']
    );
    // Listen for reload requests from sibling buttons (avoids window pollution)
    document.addEventListener('portfolio:reload', load, { once: true });
  }

  load();
  interval = setInterval(load, 60000);
  const obs = new MutationObserver(() => {
    if (!document.body.contains(root)) { clearInterval(interval); obs.disconnect(); }
  });
  obs.observe(document.body, {childList:true, subtree:true});
  return root;
}
