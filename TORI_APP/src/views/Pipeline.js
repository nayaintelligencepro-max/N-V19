// Pipeline.js — Vue Pipeline Cash Réel V10
import wsStore from '../core/ws.js';

export default function Pipeline() {
  const root = document.createElement("div");
  let pipelineData = null;
  let projectionData = null;

  async function loadPipeline() {
    try {
      const [pRes, prRes] = await Promise.all([
        fetch('/pipeline'), fetch('/pipeline/projection?days=90')
      ]);
      pipelineData = await pRes.json();
      projectionData = await prRes.json();
      render();
    } catch(e) {
      root.innerHTML = '<div class="card"><p style="color:#888">Pipeline indisponible — démarrer NAYA</p></div>';
    }
  }

  async function markWon(dealId) {
    const revenue = prompt("Montant encaissé (€) — laisser vide pour montant offre:");
    if (revenue === null) return;
    await fetch(`/pipeline/${dealId}/won`, {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({revenue: parseFloat(revenue) || 0})
    });
    await loadPipeline();
  }

  async function advancePipeline() {
    const r = await fetch('/pipeline/advance', {method:'POST'});
    const d = await r.json();
    alert(`${d.actions_taken} deals avancés`);
    await loadPipeline();
  }

  function stageColor(stage) {
    const c = {
      detected:'#334', qualified:'#343', contacted:'#433',
      demo_booked:'#443', proposal_sent:'#344', negotiating:'#484',
      won:'#0a3', lost:'#300', nurturing:'#333'
    };
    return c[stage] || '#222';
  }

  function render() {
    if (!pipelineData) { root.innerHTML = '<div class="card">Chargement...</div>'; return; }

    const p = pipelineData;
    const proj = projectionData || {};
    const topDeals = p.top_deals || [];
    const nextActions = p.next_actions || [];
    const byStage = p.by_stage || {};
    const byWeek = proj.by_week || {};

    root.innerHTML = `
      <!-- KPIs principaux -->
      <div class="grid3" style="margin-bottom:12px">
        <div class="card" style="text-align:center">
          <div class="big-num">${p.pipeline_total_eur?.toLocaleString('fr') || 0}€</div>
          <div class="label">Pipeline total</div>
        </div>
        <div class="card" style="text-align:center">
          <div class="big-num" style="color:#ffaa00">${p.pipeline_weighted_eur?.toLocaleString('fr') || 0}€</div>
          <div class="label">Pipeline pondéré</div>
        </div>
        <div class="card" style="text-align:center">
          <div class="big-num" style="color:#00ff88">${p.won_total_eur?.toLocaleString('fr') || 0}€</div>
          <div class="label">WON total (${p.won_count || 0} deals)</div>
        </div>
      </div>

      <!-- Pipeline par étape -->
      <div class="card" style="margin-bottom:12px">
        <h3>📊 Pipeline par étape (${p.active_deals || 0} deals actifs)</h3>
        <div style="display:flex;flex-wrap:wrap;gap:8px">
          ${Object.entries(byStage).map(([stage, count]) => `
            <div style="background:${stageColor(stage)};padding:6px 12px;border-radius:4px;font-size:0.78rem">
              <b>${count}</b> ${stage.replace(/_/g,' ')}
            </div>
          `).join('')}
        </div>
      </div>

      <!-- Projection revenus 90j -->
      ${Object.keys(byWeek).length > 0 ? `
      <div class="card" style="margin-bottom:12px">
        <h3>🔮 Projection 90 jours — ${proj.total_projected?.toLocaleString('fr') || 0}€</h3>
        <div style="display:flex;gap:8px;align-items:flex-end;height:60px">
          ${Object.entries(byWeek).map(([week, val]) => {
            const maxVal = Math.max(...Object.values(byWeek));
            const h = maxVal > 0 ? Math.round((val / maxVal) * 50) : 5;
            return `<div style="text-align:center;flex:1">
              <div style="background:#003322;height:${h}px;border-radius:3px 3px 0 0"></div>
              <div style="font-size:0.6rem;color:#888">${week.replace('week_','S')}</div>
              <div style="font-size:0.65rem;color:#00ff88">${(val/1000).toFixed(0)}k</div>
            </div>`;
          }).join('')}
        </div>
      </div>
      ` : ''}

      <!-- Top deals -->
      ${topDeals.length > 0 ? `
      <div class="card" style="margin-bottom:12px">
        <h3>🏆 Top Deals</h3>
        ${topDeals.map(d => `
          <div style="padding:8px;border-left:3px solid ${d.stage==='won'?'#00ff88':d.stage==='negotiating'?'#ffaa00':'#4499ff'};margin-bottom:8px">
            <div style="display:flex;justify-content:space-between">
              <span style="font-size:0.85rem;font-weight:bold;color:#00ff88">${d.price?.toLocaleString('fr') || 0}€</span>
              <span class="badge ${d.stage==='won'?'ok':d.stage==='negotiating'?'warn':'info'}">${d.stage?.replace(/_/g,' ')}</span>
            </div>
            <div style="font-size:0.72rem;color:#aaa">${d.sector?.replace(/_/g,' ')} · ${d.pain?.replace(/_/g,' ')} · ROI ×${d.roi}</div>
            <div style="font-size:0.7rem;color:#888;margin-top:4px">${d.next_action || 'En attente'}</div>
            ${d.stage !== 'won' && d.stage !== 'lost' ? `
              <button onclick="window._markWon('${d.id}')"
                style="background:#003322;color:#00ff88;border:1px solid #00ff88;padding:3px 8px;cursor:pointer;border-radius:3px;font-size:0.7rem;margin-top:6px">
                ✅ Marquer WON
              </button>` : ''}
          </div>
        `).join('')}
      </div>
      ` : '<div class="card" style="margin-bottom:12px"><p style="color:#555;font-size:0.8rem">Aucun deal dans le pipeline — lancer un cycle hunt</p></div>'}

      <!-- Prochaines actions -->
      ${nextActions.length > 0 ? `
      <div class="card" style="margin-bottom:12px">
        <h3>⚡ Prochaines actions</h3>
        ${nextActions.map(a => `
          <div style="padding:6px 8px;border-left:3px solid #ffaa00;margin-bottom:6px;font-size:0.78rem">
            <span style="color:#ffaa00;font-weight:bold">${a.price?.toLocaleString('fr') || 0}€</span>
            <span style="color:#bbb;margin-left:8px">${a.action}</span>
          </div>
        `).join('')}
      </div>
      ` : ''}

      <!-- Boutons d'action -->
      <div class="card">
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <button onclick="window._advancePipeline()" class="send-btn">⚡ Avancer Pipeline</button>
          <button onclick="window._loadPipeline()" 
            style="background:#1a1a2e;color:#888;border:1px solid #333;padding:8px 18px;cursor:pointer;border-radius:4px">
            🔄 Actualiser
          </button>
          <button onclick="fetch('/notify/pipeline_report',{method:'POST'}).then(()=>alert('Envoyé sur Telegram'))"
            style="background:#1a1a2e;color:#4499ff;border:1px solid #4499ff;padding:8px 18px;cursor:pointer;border-radius:4px">
            📱 Rapport Telegram
          </button>
        </div>
      </div>
    `;
  }

  // Expose méthodes globales pour onclick
  window._markWon = (id) => markWon(id).then(() => loadPipeline());
  window._advancePipeline = () => advancePipeline();
  window._loadPipeline = () => loadPipeline();

  // Écouter les deals en pipeline depuis EventStream
  wsStore.subscribe(state => {
    const evt = state.lastEvent;
    if (evt && evt.source === 'event-stream') {
      try {
        const d = JSON.parse(evt.payload);
        if (d.kind === 'DEAL_PIPELINE') loadPipeline();
      } catch(_) {}
    }
  });

  loadPipeline();
  return root;
}
