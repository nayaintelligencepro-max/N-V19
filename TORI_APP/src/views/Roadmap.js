// Roadmap.js — Vue timeline 36 mois + opportunités anticipées V19
export default function Roadmap() {
  const root = document.createElement("div");
  let data = null;
  let interval = null;

  const PHASE_COLORS = {
    OBSERVE: "#7c3aed",
    ORIENT:  "#2563eb",
    DECIDE:  "#d97706",
    ACT:     "#16a34a",
  };

  const STATUS_ICON = {
    exceeded:  "🚀",
    achieved:  "✅",
    on_track:  "📈",
    pending:   "⏳",
    behind:    "⚠️",
    unknown:   "❓",
  };

  async function load() {
    try {
      const [roadRes, learnRes, riskRes] = await Promise.all([
        fetch("/api/v1/evolution/anticipation/roadmap").then(r => r.json()).catch(() => null),
        fetch("/api/v1/evolution/learner/params").then(r => r.json()).catch(() => null),
        fetch("/api/v1/evolution/deals/risk").then(r => r.json()).catch(() => null),
      ]);
      data = { roadmap: roadRes, learn: learnRes, risk: riskRes };
      render();
    } catch (e) {
      root.innerHTML = '<div class="card"><p style="color:#888">Roadmap indisponible</p></div>';
    }
  }

  function card(content, extra = "") {
    return `<div class="card" style="margin-bottom:16px;${extra}">${content}</div>`;
  }

  function sectionTitle(icon, title) {
    return `<h3 style="color:#7c3aed;margin:0 0 14px;font-size:0.95rem;letter-spacing:1px">
      ${icon} ${title}</h3>`;
  }

  function renderCurrentMilestone(cm) {
    if (!cm) return "";
    const pct = cm.target_eur > 0
      ? Math.min(100, (cm.achieved_eur / cm.target_eur) * 100)
      : 0;
    const color = pct >= 100 ? "#16a34a" : pct >= 50 ? "#d97706" : "#7c3aed";
    const icon = STATUS_ICON[cm.status] || "⏳";
    return card(`
      ${sectionTitle("🎯", `JALON COURANT — M${cm.month}`)}
      <div style="display:flex;justify-content:space-between;margin-bottom:8px">
        <span style="color:#ccc;font-size:0.85rem">${cm.focus}</span>
        <span style="color:#fff;font-weight:bold">${icon} ${cm.status.toUpperCase()}</span>
      </div>
      <div style="display:flex;justify-content:space-between;margin-bottom:6px">
        <span style="color:#888;font-size:0.8rem">Réalisé: ${(cm.achieved_eur||0).toLocaleString("fr-FR")}€</span>
        <span style="color:#888;font-size:0.8rem">Cible: ${cm.target_eur.toLocaleString("fr-FR")}€</span>
      </div>
      <div style="height:10px;background:#1a1a2e;border-radius:5px">
        <div style="width:${pct}%;height:100%;background:${color};border-radius:5px;transition:width 0.5s"></div>
      </div>
      <div style="text-align:right;color:${color};font-size:0.8rem;margin-top:4px">${pct.toFixed(1)}%</div>
    `);
  }

  function renderOpportunities(opps) {
    if (!opps || opps.length === 0) return "";
    const rows = opps.slice(0, 5).map(o => `
      <div style="border-left:3px solid #7c3aed;padding:8px 12px;margin-bottom:8px;background:#0d0d1a;border-radius:0 6px 6px 0">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span style="color:#fff;font-size:0.85rem;font-weight:600">${o.label}</span>
          <span style="color:#00ff88;font-size:0.8rem;white-space:nowrap;margin-left:8px">
            ${(o.expected_value_eur||0).toLocaleString("fr-FR")}€
          </span>
        </div>
        <div style="display:flex;justify-content:space-between;margin-top:4px">
          <span style="color:#888;font-size:0.75rem">Dans ${o.horizon_days}j · ${(o.probability*100).toFixed(0)}% prob</span>
          <span style="color:#7c3aed;font-size:0.75rem">${o.sector}</span>
        </div>
        <div style="color:#aaa;font-size:0.75rem;margin-top:4px;border-top:1px solid #1a1a2e;padding-top:4px">
          ▶ ${o.action}
        </div>
      </div>
    `).join("");
    return card(`
      ${sectionTitle("🔮", "OPPORTUNITÉS ANTICIPÉES — 90 jours")}
      ${rows}
    `);
  }

  function renderRoadmapTimeline(months) {
    if (!months || months.length === 0) return "";
    const current = months.find(m => m.is_current);
    const currentMonth = current ? current.month : 1;

    // Afficher les 12 premiers mois + le mois courant
    const displayed = months.filter(m => m.month <= Math.max(12, currentMonth + 3));

    const bars = displayed.map(m => {
      const pct = m.target_eur > 0
        ? Math.min(100, ((m.achieved_eur || 0) / m.target_eur) * 100)
        : 0;
      const color = PHASE_COLORS[m.phase] || "#7c3aed";
      const icon = STATUS_ICON[m.status] || "⏳";
      const isCurrent = m.is_current;
      return `
        <div style="
          ${isCurrent ? "border:2px solid #7c3aed;" : "border:1px solid #1a1a2e;"}
          background:#0d0d1a;border-radius:6px;padding:8px;
          min-width:70px;flex-shrink:0;text-align:center
        ">
          <div style="color:${isCurrent ? "#7c3aed" : "#888"};font-size:0.7rem;font-weight:bold">M${m.month}</div>
          <div style="color:#fff;font-size:0.65rem;margin:2px 0">${icon}</div>
          <div style="height:40px;background:#1a1a2e;border-radius:3px;position:relative;margin:4px 0">
            <div style="
              position:absolute;bottom:0;width:100%;
              height:${pct}%;background:${color};border-radius:3px;transition:height 0.5s
            "></div>
          </div>
          <div style="color:${color};font-size:0.6rem">${(m.target_eur/1000).toFixed(0)}k€</div>
          <div style="
            background:${color}22;color:${color};
            font-size:0.55rem;padding:1px 3px;border-radius:2px;margin-top:2px
          ">${m.phase}</div>
        </div>
      `;
    }).join("");

    return card(`
      ${sectionTitle("📅", "ROADMAP 36 MOIS — OODA")}
      <div style="overflow-x:auto;padding-bottom:8px">
        <div style="display:flex;gap:6px;min-width:max-content">
          ${bars}
        </div>
      </div>
      <div style="display:flex;gap:12px;margin-top:8px;flex-wrap:wrap">
        ${Object.entries(PHASE_COLORS).map(([phase, color]) => `
          <span style="color:${color};font-size:0.7rem">■ ${phase}</span>
        `).join("")}
      </div>
    `);
  }

  function renderLearnerParams(learn) {
    if (!learn || !learn.params) return "";
    const p = learn.params;
    const summary = learn.summary || {};
    return card(`
      ${sectionTitle("🧠", "APPRENTISSAGE — Paramètres optimisés")}
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:0.8rem">
        <div>
          <span style="color:#888">Version paramètres</span><br>
          <span style="color:#fff;font-weight:bold">v${p.version}</span>
        </div>
        <div>
          <span style="color:#888">Ticket cible</span><br>
          <span style="color:#00ff88;font-weight:bold">${(p.target_ticket_eur||0).toLocaleString("fr-FR")}€</span>
        </div>
        <div>
          <span style="color:#888">Taux conversion</span><br>
          <span style="color:#fff">${((summary.global_conversion_rate||0)*100).toFixed(1)}%</span>
        </div>
        <div>
          <span style="color:#888">Multiplicateur qualité</span><br>
          <span style="color:#7c3aed">×${(p.quality_multiplier||1).toFixed(3)}</span>
        </div>
        <div>
          <span style="color:#888">Score qualité min</span><br>
          <span style="color:#fff">${((p.min_quality_score||0)*100).toFixed(0)}/100</span>
        </div>
        <div>
          <span style="color:#888">Deals appris</span><br>
          <span style="color:#fff">${summary.total_outcomes||0}</span>
        </div>
      </div>
      <div style="margin-top:10px">
        <span style="color:#888;font-size:0.75rem">Top secteurs : </span>
        ${(p.top_sectors||[]).slice(0,4).map(s =>
          `<span style="background:#1a1a2e;color:#7c3aed;padding:2px 6px;border-radius:3px;font-size:0.7rem;margin:2px">${s}</span>`
        ).join("")}
      </div>
    `);
  }

  function renderDealRisk(risk) {
    if (!risk) return "";
    const tempColors = { hot: "#ef4444", warm: "#f59e0b", cold: "#60a5fa", lost: "#6b7280" };
    const tempEmoji = { hot: "🔥", warm: "🟡", cold: "❄️", lost: "💀" };
    const byTemp = risk.by_temperature || {};
    return card(`
      ${sectionTitle("🌡️", "DEALS — Températures")}
      <div style="display:flex;gap:12px;margin-bottom:12px;flex-wrap:wrap">
        ${["hot","warm","cold","lost"].map(t => `
          <div style="text-align:center;padding:8px 12px;background:#0d0d1a;border-radius:6px;
            border:1px solid ${tempColors[t]}44">
            <div style="font-size:1.2rem">${tempEmoji[t]}</div>
            <div style="color:${tempColors[t]};font-size:1.1rem;font-weight:bold">${byTemp[t]||0}</div>
            <div style="color:#888;font-size:0.7rem">${t.toUpperCase()}</div>
          </div>
        `).join("")}
      </div>
      <div style="display:flex;justify-content:space-between;font-size:0.8rem">
        <span style="color:#888">Pipeline total:</span>
        <span style="color:#fff">${(risk.pipeline_eur||0).toLocaleString("fr-FR")}€</span>
      </div>
      <div style="display:flex;justify-content:space-between;font-size:0.8rem;margin-top:4px">
        <span style="color:#888">À risque:</span>
        <span style="color:#ef4444">${(risk.at_risk_eur||0).toLocaleString("fr-FR")}€</span>
      </div>
    `);
  }

  function render() {
    if (!data) return;
    const rd = data.roadmap || {};
    const learn = data.learn || {};
    const risk = data.risk || {};

    root.innerHTML = `
      <div style="max-width:900px">
        <div style="margin-bottom:20px;display:flex;justify-content:space-between;align-items:center">
          <h2 style="color:#7c3aed;margin:0;font-size:1.1rem;letter-spacing:2px">
            🗺️ NAYA ROADMAP — VISION 36 MOIS
          </h2>
          <button onclick="this.closest('[data-view]') && window.__roadmapRefresh && window.__roadmapRefresh()"
            style="background:#7c3aed22;border:1px solid #7c3aed;color:#7c3aed;
            padding:6px 12px;border-radius:4px;cursor:pointer;font-size:0.75rem">
            ↺ Actualiser
          </button>
        </div>
        ${renderCurrentMilestone(rd.current_milestone)}
        ${renderOpportunities(rd.opportunities_90d)}
        ${renderRoadmapTimeline(rd.roadmap)}
        ${renderLearnerParams(learn)}
        ${renderDealRisk(risk)}
      </div>
    `;

    // Bouton refresh
    window.__roadmapRefresh = load;
  }

  // Chargement initial + rafraîchissement toutes les 5 min
  load();
  interval = setInterval(load, 5 * 60 * 1000);

  // Nettoyage mémoire quand la vue est détruite
  root.__cleanup = () => {
    clearInterval(interval);
    delete window.__roadmapRefresh;
  };

  return root;
}
