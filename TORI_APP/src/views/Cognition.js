// Cognition.js — Vue Intelligence & Marchés Oubliés (9 langues)
export default function Cognition() {
  const root = document.createElement("div");
  let cogData = null;
  const LANG_FLAGS = {
    zh:'🇨🇳', ar:'🇸🇦', es:'🇪🇸', pt:'🇧🇷', sw:'🇰🇪', hi:'🇮🇳', vi:'🇻🇳', tl:'🇵🇭', pid:'🌍'
  };

  async function load() {
    try {
      const r = await fetch('/cognition/status');
      cogData = await r.json();
      render();
    } catch(e) {}
  }

  async function humanize() {
    const message = document.getElementById('hum-msg')?.value || '';
    const audience = document.getElementById('hum-audience')?.value || 'dirigeant PME';
    if (!message.trim()) return;
    const btn = document.getElementById('hum-btn');
    if (btn) { btn.textContent = '⏳'; btn.disabled = true; }
    try {
      const r = await fetch('/cognition/humanize', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({message, audience, tone:'authority'})
      });
      const d = await r.json();
      const out = document.getElementById('hum-out');
      if (out) {
        out.style.display = 'block';
        out.innerHTML = `<div style="color:#00ff88;font-size:0.8rem;margin-bottom:4px">✅ Message humanisé:</div>
          <div style="font-size:0.8rem;padding:8px;background:#111;border-radius:4px">${d.humanized||d.original}</div>`;
      }
    } catch(e) {}
    if (btn) { btn.textContent = '✨ Humaniser'; btn.disabled = false; }
  }

  async function translateMsg() {
    const message = document.getElementById('tr-msg')?.value || '';
    const lang = document.getElementById('tr-lang')?.value || 'ar';
    if (!message.trim()) return;
    const btn = document.getElementById('tr-btn');
    if (btn) { btn.textContent = '⏳'; btn.disabled = true; }
    try {
      const r = await fetch('/cognition/multilingual', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({message, language: lang})
      });
      const d = await r.json();
      if (d.error) {
        document.getElementById('tr-out').style.display = 'block';
        document.getElementById('tr-out').innerHTML = `<div style="color:#ff4444">${d.error}</div>`;
      } else {
        const out = document.getElementById('tr-out');
        out.style.display = 'block';
        out.innerHTML = `<div style="color:#00ff88;font-size:0.75rem">✅ ${d.language_name}</div>
          <div style="font-size:0.85rem;padding:8px;background:#111;border-radius:4px;margin-top:4px;direction:${lang==='ar'?'rtl':'ltr'}">${d.adapted_message||message}</div>
          ${d.cultural_notes ? `<div style="font-size:0.7rem;color:#888;margin-top:4px">📌 ${d.cultural_notes}</div>` : ''}`;
      }
    } catch(e) {}
    if (btn) { btn.textContent = '🌍 Adapter'; btn.disabled = false; }
  }

  function render() {
    const langs = cogData?.languages_detail || {};
    root.innerHTML = `
      <div class="grid2" style="margin-bottom:12px">
        <div class="card" style="text-align:center">
          <div class="big-num" style="color:#00ff88">${cogData?.language_count||9}</div>
          <div class="label">🌍 Langues supportées</div>
        </div>
        <div class="card" style="text-align:center">
          <div class="big-num" style="color:#4499ff">P05</div>
          <div class="label">Marchés Oubliés (diaspora)</div>
        </div>
      </div>

      <!-- Langues grid -->
      <div class="card" style="margin-bottom:12px">
        <h3>🗣️ Langues des Marchés Oubliés</h3>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:10px">
          ${Object.entries(langs).map(([code, l]) => `
            <div style="background:#111;padding:8px;border-radius:4px;text-align:center">
              <div style="font-size:1.5rem">${LANG_FLAGS[code]||'🌐'}</div>
              <div style="font-size:0.75rem;font-weight:bold">${l.name}</div>
              <div style="font-size:0.65rem;color:#888">${l.dialects} dialectes</div>
              <div style="font-size:0.65rem;color:#00ff88">${(l.cultural_nuance*100).toFixed(0)}% nuance</div>
            </div>
          `).join('')}
        </div>
      </div>

      <!-- Humanisation Tool -->
      <div class="card" style="margin-bottom:12px">
        <h3>✨ Humanisation de Message</h3>
        <div style="margin-bottom:8px">
          <label style="font-size:0.75rem;color:#888">Message commercial:</label>
          <textarea id="hum-msg" style="width:100%;background:#111;color:#e0e0e0;border:1px solid #333;padding:8px;border-radius:4px;margin-top:4px;font-size:0.8rem;height:80px;resize:vertical"></textarea>
        </div>
        <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px">
          <select id="hum-audience" style="background:#111;color:#e0e0e0;border:1px solid #333;padding:6px;border-radius:4px;font-size:0.8rem;flex:1">
            <option>dirigeant PME</option>
            <option>CEO startup</option>
            <option>artisan indépendant</option>
            <option>praticien santé</option>
            <option>commerçant</option>
            <option>chef restaurateur</option>
          </select>
          <button id="hum-btn"
            style="background:#003322;color:#00ff88;border:1px solid #00ff88;padding:6px 12px;cursor:pointer;border-radius:4px;font-size:0.8rem;white-space:nowrap">
            ✨ Humaniser
          </button>
        </div>
        <div id="hum-out" style="display:none"></div>
      </div>

      <!-- Multilingual Tool -->
      <div class="card">
        <h3>🌍 Adaptation Multilingue</h3>
        <div style="margin-bottom:8px">
          <label style="font-size:0.75rem;color:#888">Message à adapter:</label>
          <textarea id="tr-msg" style="width:100%;background:#111;color:#e0e0e0;border:1px solid #333;padding:8px;border-radius:4px;margin-top:4px;font-size:0.8rem;height:70px;resize:vertical"></textarea>
        </div>
        <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px">
          <select id="tr-lang" style="background:#111;color:#e0e0e0;border:1px solid #333;padding:6px;border-radius:4px;font-size:0.8rem;flex:1">
            ${Object.keys(langs).map(code =>
              `<option value="${code}">${LANG_FLAGS[code]||'🌐'} ${langs[code]?.name||code}</option>`
            ).join('')}
          </select>
          <button id="tr-btn"
            style="background:#001422;color:#4499ff;border:1px solid #4499ff;padding:6px 12px;cursor:pointer;border-radius:4px;font-size:0.8rem;white-space:nowrap">
            🌍 Adapter
          </button>
        </div>
        <div id="tr-out" style="display:none"></div>
      </div>
    `;
    root.querySelector('#hum-btn').onclick = humanize;
    root.querySelector('#tr-btn').onclick = translateMsg;
  }

  // Render initial sans données
  root.innerHTML = '<div class="card"><p style="color:#555">Chargement module Cognition...</p></div>';
  load();
  return root;
}
