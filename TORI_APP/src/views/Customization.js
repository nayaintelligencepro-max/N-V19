// Customization.js — Panneau personnalisation TORI V19
const STORAGE_KEY = "tori_customization";

const THEMES = {
  neon: { label: "⚡ Neon Green (défaut)", accent: "#7c3aed", accent2: "#a855f7", success: "#10b981", bg: "#0a0a0f" },
  cyber: { label: "🔵 Cyber Blue", accent: "#0ea5e9", accent2: "#38bdf8", success: "#10b981", bg: "#0a0f14" },
  gold: { label: "🟡 Gold Premium", accent: "#d97706", accent2: "#f59e0b", success: "#10b981", bg: "#0f0a00" },
  red: { label: "🔴 REAPERS Red", accent: "#dc2626", accent2: "#ef4444", success: "#22c55e", bg: "#0f0000" },
  mono: { label: "⬜ Monochrome", accent: "#6b7280", accent2: "#9ca3af", success: "#6b7280", bg: "#0a0a0a" },
};

function loadSettings() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}"); } catch { return {}; }
}

function saveSettings(settings) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
}

function applyTheme(themeKey) {
  const t = THEMES[themeKey];
  if (!t) return;
  const root = document.documentElement;
  root.style.setProperty("--accent", t.accent);
  root.style.setProperty("--accent2", t.accent2);
  root.style.setProperty("--success", t.success);
  root.style.setProperty("--bg", t.bg);
  document.body.style.background = t.bg;
  const s = loadSettings();
  s.theme = themeKey;
  saveSettings(s);
}

function applyCustomColor(varName, color) {
  document.documentElement.style.setProperty(varName, color);
  const s = loadSettings();
  if (!s.custom) s.custom = {};
  s.custom[varName] = color;
  saveSettings(s);
}

function applyFontSize(size) {
  document.documentElement.style.fontSize = size + "px";
  const s = loadSettings();
  s.fontSize = size;
  saveSettings(s);
}

function applyDensity(mode) {
  const base = mode === "compact" ? "0.5rem" : mode === "wide" ? "1.5rem" : "1.25rem";
  document.querySelectorAll(".view").forEach(el => el.style.padding = base);
  const s = loadSettings();
  s.density = mode;
  saveSettings(s);
}

export function restoreCustomization() {
  const s = loadSettings();
  if (s.theme) applyTheme(s.theme);
  if (s.custom) Object.entries(s.custom).forEach(([k, v]) => document.documentElement.style.setProperty(k, v));
  if (s.fontSize) document.documentElement.style.fontSize = s.fontSize + "px";
  if (s.density) applyDensity(s.density);
}

export default function Customization() {
  const s = loadSettings();
  const root = document.createElement("div");
  root.style.display = "contents";

  root.innerHTML = `
    <!-- THÈMES -->
    <div class="card">
      <h3>🎨 Thèmes</h3>
      <div style="display:flex;flex-direction:column;gap:8px;margin-top:8px" id="theme-list">
        ${Object.entries(THEMES).map(([key, t]) => `
          <button data-theme="${key}"
            style="display:flex;align-items:center;gap:10px;background:${s.theme===key?'#1a1a2e':'#111'};
                   border:1px solid ${s.theme===key?'#7c3aed':'#333'};color:#e0e0e0;padding:10px 14px;
                   border-radius:6px;cursor:pointer;text-align:left;font-size:0.82rem">
            <span style="display:inline-block;width:14px;height:14px;border-radius:3px;background:${t.accent}"></span>
            ${t.label}
            ${s.theme===key ? ' <span style="margin-left:auto;color:#a855f7;font-size:0.75rem">✓ Actif</span>' : ''}
          </button>
        `).join("")}
      </div>
    </div>

    <!-- COULEURS PERSONNALISÉES -->
    <div class="card">
      <h3>🖌️ Couleurs personnalisées</h3>
      <div class="grid2" style="margin-top:8px">
        ${[
          ["--accent",   "Accent principal", "#7c3aed"],
          ["--accent2",  "Accent secondaire","#a855f7"],
          ["--success",  "Succès / Actif",   "#10b981"],
          ["--gold",     "Gold / Revenue",   "#f59e0b"],
          ["--danger",   "Danger / Erreur",  "#ef4444"],
          ["--bg",       "Fond",             "#0a0a0f"],
        ].map(([varName, label, def]) => {
          const current = getComputedStyle(document.documentElement).getPropertyValue(varName).trim() || def;
          return `<div>
            <div style="font-size:0.72rem;color:#888;margin-bottom:4px">${label}</div>
            <div style="display:flex;gap:6px;align-items:center">
              <input type="color" value="${current.startsWith('#') ? current : def}"
                data-var="${varName}"
                style="width:36px;height:28px;border:none;background:none;cursor:pointer;padding:0">
              <span style="font-size:0.7rem;color:#555" id="color-val-${varName.replace('--','')}">${current}</span>
            </div>
          </div>`;
        }).join("")}
      </div>
    </div>

    <!-- TYPOGRAPHIE & DENSITÉ -->
    <div class="card">
      <h3>📐 Taille & Densité</h3>
      <div style="margin-top:10px;margin-bottom:14px">
        <div style="font-size:0.75rem;color:#888;margin-bottom:6px">Taille de police (px)</div>
        <div style="display:flex;gap:6px">
          ${[13,14,15,16].map(sz => `
            <button data-fontsize="${sz}"
              style="padding:5px 12px;border-radius:4px;cursor:pointer;font-size:0.8rem;
                     background:${(s.fontSize||14)===sz?'#1a1a2e':'#111'};
                     border:1px solid ${(s.fontSize||14)===sz?'#7c3aed':'#333'};color:#e0e0e0">
              ${sz}px
            </button>`
          ).join("")}
        </div>
      </div>
      <div>
        <div style="font-size:0.75rem;color:#888;margin-bottom:6px">Densité d'affichage</div>
        <div style="display:flex;gap:6px">
          ${[["compact","Compact"],["normal","Normal"],["wide","Large"]].map(([k,l]) => `
            <button data-density="${k}"
              style="padding:5px 14px;border-radius:4px;cursor:pointer;font-size:0.8rem;
                     background:${(s.density||'normal')===k?'#1a1a2e':'#111'};
                     border:1px solid ${(s.density||'normal')===k?'#7c3aed':'#333'};color:#e0e0e0">
              ${l}
            </button>`
          ).join("")}
        </div>
      </div>
    </div>

    <!-- ENDPOINTS (informatif) -->
    <div class="card">
      <h3>📡 Connexions actives</h3>
      <div class="grid2" style="font-size:0.78rem;margin-top:8px">
        <div><div style="color:#555;font-size:0.7rem">API REST</div><div class="mono">http://localhost:8080</div></div>
        <div><div style="color:#555;font-size:0.7rem">WebSocket principal</div><div class="mono">ws://localhost:8080/ws</div></div>
        <div><div style="color:#555;font-size:0.7rem">EventStream</div><div class="mono">ws://localhost:8765</div></div>
        <div><div style="color:#555;font-size:0.7rem">CommandGateway</div><div class="mono">ws://localhost:8766</div></div>
        <div><div style="color:#555;font-size:0.7rem">ObservationBus</div><div class="mono">ws://localhost:8899</div></div>
        <div><div style="color:#555;font-size:0.7rem">Docs</div><div><a href="/docs" target="_blank" style="color:#a855f7">/docs</a></div></div>
      </div>
    </div>

    <!-- ACTIONS RAPIDES -->
    <div class="card">
      <h3>⚡ Actions rapides</h3>
      <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:8px">
        ${[
          ["🔍 Status", "/status"],
          ["⚡ Cycle souverain", "/hunt/cycle"],
          ["📊 Portfolio", "/business/portfolio"],
          ["🛡️ REAPERS", "/system/diagnostic"],
          ["⏰ Scheduler", "/scheduler/status"],
          ["📡 TORI Status", "/tori/status"],
        ].map(([label, url]) => `
          <button data-quick-url="${url}"
            style="background:#111;color:#aaa;border:1px solid #333;padding:6px 12px;cursor:pointer;border-radius:4px;font-size:0.78rem">
            ${label}
          </button>
        `).join("")}
      </div>
    </div>

    <!-- RESET -->
    <div class="card" style="text-align:center">
      <button id="reset-custom-btn"
        style="background:#330000;color:#ff4444;border:1px solid #ff4444;padding:8px 20px;cursor:pointer;border-radius:6px;font-size:0.82rem">
        🗑️ Réinitialiser toutes les personnalisations
      </button>
    </div>
  `;

  // Themes
  root.querySelectorAll("[data-theme]").forEach(btn => {
    btn.onclick = () => {
      applyTheme(btn.dataset.theme);
      root.querySelectorAll("[data-theme]").forEach(b => {
        b.style.borderColor = b.dataset.theme === btn.dataset.theme ? "#7c3aed" : "#333";
        b.style.background = b.dataset.theme === btn.dataset.theme ? "#1a1a2e" : "#111";
      });
    };
  });

  // Custom colors
  root.querySelectorAll("input[type=color][data-var]").forEach(inp => {
    inp.oninput = () => {
      applyCustomColor(inp.dataset.var, inp.value);
      const span = root.querySelector(`#color-val-${inp.dataset.var.replace('--','')}`);
      if (span) span.textContent = inp.value;
    };
  });

  // Font size
  root.querySelectorAll("[data-fontsize]").forEach(btn => {
    btn.onclick = () => {
      const sz = parseInt(btn.dataset.fontsize);
      applyFontSize(sz);
      root.querySelectorAll("[data-fontsize]").forEach(b => {
        b.style.borderColor = parseInt(b.dataset.fontsize) === sz ? "#7c3aed" : "#333";
        b.style.background = parseInt(b.dataset.fontsize) === sz ? "#1a1a2e" : "#111";
      });
    };
  });

  // Density
  root.querySelectorAll("[data-density]").forEach(btn => {
    btn.onclick = () => {
      applyDensity(btn.dataset.density);
      root.querySelectorAll("[data-density]").forEach(b => {
        b.style.borderColor = b.dataset.density === btn.dataset.density ? "#7c3aed" : "#333";
        b.style.background = b.dataset.density === btn.dataset.density ? "#1a1a2e" : "#111";
      });
    };
  });

  // Quick actions
  root.querySelectorAll("[data-quick-url]").forEach(btn => {
    btn.onclick = () => {
      fetch(btn.dataset.quickUrl)
        .then(r => r.json())
        .then(d => alert(JSON.stringify(d, null, 2).substring(0, 500)))
        .catch(() => alert(`${btn.dataset.quickUrl}: Serveur non accessible`));
    };
  });

  // Reset
  root.querySelector("#reset-custom-btn").onclick = () => {
    if (!confirm("Réinitialiser toutes les personnalisations TORI ?")) return;
    localStorage.removeItem(STORAGE_KEY);
    document.documentElement.removeAttribute("style");
    document.body.style.background = "";
    document.querySelectorAll(".view").forEach(el => el.style.padding = "");
    alert("✅ Personnalisations réinitialisées. Rechargez la page.");
  };

  return root;
}

