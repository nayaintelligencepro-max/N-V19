// Revenue.js — Vue Revenue Engine V1
import wsStore from '../core/ws.js';

export default function Revenue() {
  const root = document.createElement("div");
  let data = null;
  let refreshInterval = null;

  async function fetchRevenue() {
    try {
      const [statusR, pipelineR] = await Promise.all([
        fetch('/revenue/status').then(r => r.json()).catch(() => null),
        fetch('/revenue/pipeline').then(r => r.json()).catch(() => null),
      ]);
      data = { status: statusR, pipeline: pipelineR };
      render(data);
    } catch (_) {}
  }

  async function runScan() {
    const btn = root.querySelector('#scan-btn');
    if (btn) { btn.textContent = '⏳ Scan en cours...'; btn.disabled = true; }
    try {
      const r = await fetch('/revenue/scan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
      const result = await r.json();
      if (btn) { btn.textContent = '🔍 Scan Maintenant'; btn.disabled = false; }
      await fetchRevenue();
    } catch (_) { if (btn) { btn.textContent = '🔍 Scan Maintenant'; btn.disabled = false; } }
  }

  async function createPayment(pid) {
    const r = await fetch(`/revenue/payment/${pid}`, { method: 'POST' });
    const result = await r.json();
    if (result.url) {
      window.open(result.url, '_blank');
      alert(`💳 Lien Stripe créé: ${result.url}\nMontant: ${result.amount?.toLocaleString('fr')}€`);
    } else {
      alert(result.manual || result.reason || 'Configurer Stripe dans .env');
    }
    await fetchRevenue();
  }

  async function markWon(pid, company) {
    if (!confirm(`Marquer ${company} comme CLOSED_WON ?`)) return;
    await fetch(`/revenue/won/${pid}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
    await fetchRevenue();
  }

  function prio(p) {
    const cfg = { CRITICAL: ['🔴', '#ff4444'], HIGH: ['🟠', '#ff8800'], MEDIUM: ['🟡', '#ffaa00'], LOW: ['⚪', '#888'] };
    return cfg[p] || ['⚪', '#888'];
  }

  function renderStage(name, data) {
    const [icon] = { NEW: ['🆕'], ALERTED: ['📡'], CONTACTED: ['📧'], RESPONDED: ['💬'],
                     MEETING: ['🤝'], PROPOSAL_SENT: ['📋'], CLOSED_WON: ['✅'], CLOSED_LOST: ['❌'] }[name] || ['•'];
    return `<div style="text-align:center;padding:6px">
      <div style="font-size:1.1rem">${icon}</div>
      <div style="font-size:0.72rem;color:#888">${name.replace('_',' ')}</div>
      <div style="font-weight:bold;color:#00ff88">${data?.count || 0}</div>
      <div style="font-size:0.68rem;color:#666">${(data?.value_eur || 0).toLocaleString('fr')}€</div>
    </div>`;
  }

  function render(d) {
    if (!d) {
      root.innerHTML = '<div class="card"><p style="color:#555">Chargement Revenue Engine...</p></div>';
      return;
    }

    const st = d.status || {};
    const pl = d.pipeline || {};
    const kpis = pl.kpis || {};
    const hot = pl.hot_prospects || [];
    const daily = pl.daily_report || {};
    const stages = kpis.stages || {};
    const pipeline_info = st.pipeline || {};
    const outreach = st.outreach || {};
    const payment_st = st.payment || {};
    const channels = outreach.channels || {};

    root.innerHTML = `
      <!-- Header KPIs -->
      <div class="grid3" style="margin-bottom:12px">
        <div class="card" style="text-align:center">
          <div class="big-num" style="color:#00ff88">${(kpis.revenue_won_eur || 0).toLocaleString('fr')}€</div>
          <div class="label">💰 Revenus confirmés</div>
        </div>
        <div class="card" style="text-align:center">
          <div class="big-num" style="color:#4499ff">${(kpis.pipeline_eur || 0).toLocaleString('fr')}€</div>
          <div class="label">📊 Pipeline total</div>
        </div>
        <div class="card" style="text-align:center">
          <div class="big-num">${kpis.total_prospects || 0}</div>
          <div class="label">👥 Prospects</div>
        </div>
      </div>

      <!-- Stats rapides -->
      <div class="grid3" style="margin-bottom:12px">
        <div class="card" style="text-align:center">
          <div style="font-size:1.2rem;color:#ffaa00">${kpis.conversion_rate || 0}%</div>
          <div class="label">Taux conversion</div>
        </div>
        <div class="card" style="text-align:center">
          <div style="font-size:1.2rem;color:#00ff88">${(kpis.avg_deal_size || 0).toLocaleString('fr')}€</div>
          <div class="label">Deal moyen</div>
        </div>
        <div class="card" style="text-align:center">
          <div style="font-size:1.2rem">${daily.new_prospects_today || 0}</div>
          <div class="label">Nouveaux aujourd'hui</div>
        </div>
      </div>

      <!-- Canaux + Actions -->
      <div class="grid2" style="margin-bottom:12px">
        <div class="card">
          <h3>📡 Canaux actifs</h3>
          ${[
            ['Telegram', channels.telegram],
            ['SendGrid Email', channels.sendgrid],
            ['SMTP', channels.smtp],
            ['Stripe Paiement', payment_st.available],
            ['Twilio SMS', channels.twilio],
          ].map(([name, ok]) =>
            `<div style="display:flex;justify-content:space-between;margin-bottom:4px;font-size:0.8rem">
              <span>${name}</span>
              <span class="badge ${ok ? 'ok' : 'warn'}">${ok ? 'ACTIF' : 'CONFIG REQUIS'}</span>
            </div>`
          ).join('')}
          <div style="font-size:0.72rem;color:#555;margin-top:6px">
            Mode: <b style="color:${outreach.mode === 'auto' ? '#00ff88' : '#ffaa00'}">${outreach.mode === 'auto' ? 'AUTO-SEND' : 'APPROBATION'}</b>
          </div>
        </div>
        <div class="card">
          <h3>⚡ Actions</h3>
          <button id="scan-btn" onclick="document.getElementById('scan-btn').click()"
            style="width:100%;background:#003322;color:#00ff88;border:1px solid #00ff88;padding:8px;cursor:pointer;border-radius:4px;margin-bottom:8px;font-size:0.85rem">
            🔍 Scan Maintenant
          </button>
          <div style="font-size:0.75rem;color:#666">Cycle #${st.cycle_count || 0} — Scan toutes les ${(st.scan_interval_s || 1800)/60} min</div>
          <div style="font-size:0.75rem;color:#666;margin-top:4px">${st.emails_sent_total || 0} emails envoyés total</div>
          <div style="font-size:0.75rem;color:#666">${outreach.pending_approvals || 0} approbation(s) en attente</div>
        </div>
      </div>

      <!-- Pipeline stages -->
      <div class="card" style="margin-bottom:12px">
        <h3>🔄 Pipeline stages</h3>
        <div style="display:grid;grid-template-columns:repeat(8,1fr);gap:4px">
          ${['NEW','ALERTED','CONTACTED','RESPONDED','MEETING','PROPOSAL_SENT','CLOSED_WON','CLOSED_LOST'].map(s => renderStage(s, stages[s])).join('')}
        </div>
      </div>

      <!-- Hot prospects -->
      <div class="card">
        <h3>🔥 Prospects prioritaires (${hot.length})</h3>
        ${hot.length === 0
          ? '<div style="color:#555;font-size:0.8rem">Aucun prospect — cliquer Scan Maintenant</div>'
          : hot.map(p => {
              const [icon, color] = prio(p.priority);
              return `<div style="padding:8px;border-left:3px solid ${color};margin-bottom:6px;background:#111">
                <div style="display:flex;justify-content:space-between;align-items:center">
                  <div>
                    <span style="font-weight:bold;font-size:0.85rem">${icon} ${p.company}</span>
                    <span style="font-size:0.72rem;color:#888;margin-left:6px">${p.sector?.replace('_',' ')} · ${p.city || ''}</span>
                  </div>
                  <div style="text-align:right">
                    <div style="color:#00ff88;font-weight:bold">${(p.offer_price || 0).toLocaleString('fr')}€</div>
                    <span class="badge ${p.status==='CONTACTED'?'ok':p.status==='NEW'?'warn':'info'}">${p.status}</span>
                  </div>
                </div>
                <div style="font-size:0.72rem;color:#aaa;margin-top:3px">${p.offer_title || ''}</div>
                <div style="font-size:0.68rem;color:#666">${p.email ? '📧 '+p.email : 'Email non disponible'}</div>
                <div style="display:flex;gap:6px;margin-top:6px">
                  <button onclick="window._revenueCreatePayment('${p.id}')"
                    style="background:#001422;color:#4499ff;border:1px solid #4499ff;padding:3px 8px;cursor:pointer;border-radius:3px;font-size:0.68rem">
                    💳 Lien Paiement
                  </button>
                  <button onclick="window._revenueMarkWon('${p.id}', '${p.company?.replace("'","\\'")||""}')"
                    style="background:#001422;color:#00ff88;border:1px solid #00ff88;padding:3px 8px;cursor:pointer;border-radius:3px;font-size:0.68rem">
                    ✅ Marquer WON
                  </button>
                </div>
              </div>`;
            }).join('')
        }
      </div>
    `;

    // Connecter les boutons
    root.querySelector('#scan-btn').onclick = runScan;
    window._revenueCreatePayment = createPayment;
    window._revenueMarkWon = markWon;
  }

  // Chargement initial + refresh auto 30s
  fetchRevenue();
  refreshInterval = setInterval(fetchRevenue, 30000);

  // Cleanup
  const observer = new MutationObserver(() => {
    if (!document.body.contains(root)) {
      clearInterval(refreshInterval);
      observer.disconnect();
    }
  });
  observer.observe(document.body, { childList: true, subtree: true });

  return root;
}
