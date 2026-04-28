"""
NAYA V19.3 — OODA DASHBOARD (FastAPI + WebSocket)
Dashboard temps réel pour voir les cycles en live.

Routes:
- GET  /                   → HTML dashboard (embedded)
- GET  /api/stats          → snapshot stats JSON
- GET  /api/cycles         → historique cycles
- GET  /api/breakers       → état circuit breakers
- GET  /api/revenue        → résumé ledger
- GET  /api/pains          → stats pains registry
- WS   /ws/live            → broadcast des events en temps réel

Démarrage:
    uvicorn NAYA_DASHBOARD.ooda_dashboard:app --host 0.0.0.0 --port 8080
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Set, Dict, Any, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse

log = logging.getLogger("NAYA.DASHBOARD")

app = FastAPI(title="NAYA OODA Dashboard", version="19.3")


# ═════════════════════════════════════════════════════════════════
# WEBSOCKET MANAGER
# ═════════════════════════════════════════════════════════════════

class LiveBroadcaster:
    def __init__(self):
        self.clients: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        async with self._lock:
            self.clients.add(ws)
        log.info(f"WS connected ({len(self.clients)} clients)")

    async def disconnect(self, ws: WebSocket):
        async with self._lock:
            self.clients.discard(ws)
        log.info(f"WS disconnected ({len(self.clients)} clients)")

    async def broadcast(self, event: Dict[str, Any]):
        """Broadcast event à tous les clients connectés."""
        if not self.clients:
            return
        payload = json.dumps({
            "ts": datetime.now(timezone.utc).isoformat(),
            **event
        })
        stale = []
        for ws in list(self.clients):
            try:
                await ws.send_text(payload)
            except Exception:
                stale.append(ws)
        async with self._lock:
            for ws in stale:
                self.clients.discard(ws)


broadcaster = LiveBroadcaster()


# ═════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═════════════════════════════════════════════════════════════════

@app.get("/api/stats")
async def api_stats():
    """Snapshot global du système."""
    try:
        from NAYA_CORE.multi_agent_orchestrator import multi_agent_orchestrator
        return multi_agent_orchestrator.get_global_stats()
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/cycles")
async def api_cycles():
    """Historique des cycles (derniers 50)."""
    try:
        from NAYA_CORE.multi_agent_orchestrator import multi_agent_orchestrator
        hist = multi_agent_orchestrator.cycle_history[-50:]
        return {"count": len(hist), "cycles": hist}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/breakers")
async def api_breakers():
    """État des circuit breakers."""
    try:
        from NAYA_CORE.resilience.circuit_breaker import breaker_registry
        return breaker_registry.global_stats()
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/revenue")
async def api_revenue():
    """Résumé ledger revenue."""
    try:
        from NAYA_REVENUE_ENGINE.reconciliation_engine import reconciler
        return reconciler.ledger.summary()
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/pains")
async def api_pains():
    """Stats pain registry (les 32 pains unifiés)."""
    try:
        from NAYA_CORE.pain import pain_registry
        return pain_registry.global_stats()
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/health")
async def api_health():
    return {"status": "ok", "version": "19.3", "ts": datetime.now(timezone.utc).isoformat()}


# ═════════════════════════════════════════════════════════════════
# WEBSOCKET LIVE FEED
# ═════════════════════════════════════════════════════════════════

@app.websocket("/ws/live")
async def ws_live(ws: WebSocket):
    await broadcaster.connect(ws)
    try:
        # Push initial snapshot
        snapshot = await api_stats()
        await ws.send_text(json.dumps({"type": "snapshot", "data": snapshot}))
        # Heartbeat + keep-alive
        while True:
            await asyncio.sleep(5)
            await ws.send_text(json.dumps({"type": "heartbeat"}))
    except WebSocketDisconnect:
        await broadcaster.disconnect(ws)
    except Exception as e:
        log.error(f"WS error: {e}")
        await broadcaster.disconnect(ws)


# ═════════════════════════════════════════════════════════════════
# BACKGROUND PUSHER — relaie les events du système
# ═════════════════════════════════════════════════════════════════

async def push_cycle_update():
    """Appelé par l'orchestrateur après chaque cycle."""
    try:
        from NAYA_CORE.multi_agent_orchestrator import multi_agent_orchestrator
        last = multi_agent_orchestrator.cycle_history[-1] if multi_agent_orchestrator.cycle_history else None
        if last:
            await broadcaster.broadcast({
                "type": "cycle_complete",
                "cycle": last.get("cycle"),
                "phases": last.get("phases"),
                "elapsed": last.get("elapsed_seconds"),
            })
    except Exception as e:
        log.debug(f"push_cycle_update error: {e}")


async def push_payment_event(payment: Dict):
    """Appelé par le reconciler quand un paiement arrive."""
    await broadcaster.broadcast({
        "type": "payment",
        "data": payment,
    })


# ═════════════════════════════════════════════════════════════════
# HTML DASHBOARD (single-file, pas de dépendances externes)
# ═════════════════════════════════════════════════════════════════

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>NAYA OODA Dashboard — V19.3</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
    background: #0a0e1a; color: #d4d8e8; padding: 20px;
    min-height: 100vh;
  }
  .header {
    display: flex; justify-content: space-between; align-items: center;
    padding-bottom: 20px; border-bottom: 1px solid #1e2740;
    margin-bottom: 24px;
  }
  h1 { font-size: 1.4em; color: #5bd97a; letter-spacing: 0.5px; }
  .status { font-size: 0.85em; }
  .status .dot {
    display: inline-block; width: 8px; height: 8px;
    border-radius: 50%; background: #5bd97a; margin-right: 6px;
    animation: pulse 2s infinite;
  }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
  .grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 16px; margin-bottom: 24px;
  }
  .card {
    background: #131a2e; border: 1px solid #1e2740;
    border-radius: 8px; padding: 18px;
  }
  .card h2 {
    font-size: 0.75em; text-transform: uppercase; letter-spacing: 1px;
    color: #6b7594; margin-bottom: 12px;
  }
  .metric { font-size: 1.8em; color: #5bd97a; font-weight: 600; }
  .metric.warn { color: #f0b429; }
  .metric.bad { color: #e84848; }
  .sub { font-size: 0.85em; color: #6b7594; margin-top: 4px; }
  .feed {
    background: #0d1220; border: 1px solid #1e2740;
    border-radius: 8px; padding: 16px;
    height: 280px; overflow-y: auto;
  }
  .event {
    padding: 8px 10px; margin-bottom: 6px;
    background: #131a2e; border-left: 3px solid #5bd97a;
    font-size: 0.85em; border-radius: 4px;
  }
  .event.payment { border-color: #f0b429; }
  .event.error { border-color: #e84848; }
  .ts { color: #6b7594; font-size: 0.75em; margin-right: 8px; }
  button {
    background: #1e2740; color: #d4d8e8; border: 1px solid #2a3552;
    padding: 8px 14px; border-radius: 4px; cursor: pointer;
    font-family: inherit; font-size: 0.85em;
  }
  button:hover { background: #2a3552; }
  .phases { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-top: 8px; }
  .phase { background: #0d1220; padding: 8px; border-radius: 4px; font-size: 0.8em; }
  .phase .n { color: #5bd97a; font-weight: 600; display: block; font-size: 1.2em; }
</style>
</head>
<body>
<div class="header">
  <h1>🧠 NAYA SUPREME — OODA Dashboard V19.3</h1>
  <div class="status"><span class="dot"></span><span id="ws-status">Connecting...</span></div>
</div>

<div class="grid">
  <div class="card">
    <h2>💰 Revenue lifetime</h2>
    <div class="metric" id="revenue-total">—</div>
    <div class="sub" id="revenue-month">Mois en cours: —</div>
  </div>
  <div class="card">
    <h2>🔄 Cycles exécutés</h2>
    <div class="metric" id="cycles-count">—</div>
    <div class="sub" id="cycles-errors">Erreurs: —</div>
  </div>
  <div class="card">
    <h2>🎯 Pain engines actifs</h2>
    <div class="metric" id="pains-count">—</div>
    <div class="sub" id="pains-detected">Détectés: —</div>
  </div>
  <div class="card">
    <h2>⚡ Circuit breakers</h2>
    <div class="metric" id="breakers-open">—</div>
    <div class="sub" id="breakers-sub">Open / Total</div>
  </div>
</div>

<div class="card" style="margin-bottom: 24px;">
  <h2>📊 Dernier cycle</h2>
  <div class="phases" id="last-cycle-phases">
    <div class="phase"><span class="n">—</span>detection</div>
    <div class="phase"><span class="n">—</span>enrichment</div>
    <div class="phase"><span class="n">—</span>offers</div>
    <div class="phase"><span class="n">—</span>outreach €</div>
    <div class="phase"><span class="n">—</span>monitoring</div>
    <div class="phase"><span class="n">—</span>closing</div>
    <div class="phase"><span class="n">—</span>audits</div>
    <div class="phase"><span class="n">—</span>content</div>
  </div>
</div>

<div class="card">
  <h2>📡 Live feed</h2>
  <div class="feed" id="feed"></div>
  <div style="margin-top: 12px;">
    <button onclick="refresh()">Refresh snapshot</button>
    <button onclick="document.getElementById('feed').innerHTML=''">Clear feed</button>
  </div>
</div>

<script>
const wsUrl = (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/live';
let ws;

function fmt(n) {
  if (n === null || n === undefined) return '—';
  if (typeof n === 'number' && n > 999) return (n/1000).toFixed(1) + 'k';
  return n;
}

function addEvent(type, text) {
  const feed = document.getElementById('feed');
  const div = document.createElement('div');
  div.className = 'event ' + type;
  const ts = new Date().toLocaleTimeString();
  div.innerHTML = '<span class="ts">' + ts + '</span>' + text;
  feed.insertBefore(div, feed.firstChild);
  while (feed.children.length > 50) feed.removeChild(feed.lastChild);
}

async function refresh() {
  try {
    const [stats, rev, pains, breakers] = await Promise.all([
      fetch('/api/stats').then(r=>r.json()),
      fetch('/api/revenue').then(r=>r.json()),
      fetch('/api/pains').then(r=>r.json()),
      fetch('/api/breakers').then(r=>r.json()),
    ]);
    document.getElementById('revenue-total').textContent = (rev.revenue_lifetime_eur||0).toFixed(0) + ' €';
    document.getElementById('revenue-month').textContent = 'Mois: ' + (rev.revenue_current_month_eur||0).toFixed(0) + ' € | Orphelins: ' + (rev.orphans||0);
    document.getElementById('cycles-count').textContent = stats.total_cycles || 0;
    document.getElementById('cycles-errors').textContent = 'Erreurs: ' + (stats.error_count || 0);
    document.getElementById('pains-count').textContent = pains.engines || 0;
    document.getElementById('pains-detected').textContent = 'Détectés: ' + (pains.total_detected||0) + ' | Revenue: ' + (pains.total_revenue||0).toFixed(0) + '€';
    document.getElementById('breakers-open').textContent = (breakers.open||0) + ' / ' + (breakers.breakers||0);
    const m = document.getElementById('breakers-open');
    m.className = 'metric' + ((breakers.open||0) > 0 ? ' bad' : '');
    const lc = stats.last_cycle;
    if (lc && lc.phases) {
      const p = lc.phases;
      const div = document.getElementById('last-cycle-phases');
      div.innerHTML =
        '<div class="phase"><span class="n">' + fmt(p.detection) + '</span>detection</div>' +
        '<div class="phase"><span class="n">' + fmt(p.enrichment) + '</span>enrichment</div>' +
        '<div class="phase"><span class="n">' + fmt(p.offers) + '</span>offers</div>' +
        '<div class="phase"><span class="n">' + fmt(p.outreach) + '</span>outreach €</div>' +
        '<div class="phase"><span class="n">' + fmt(p.monitoring) + '</span>monitoring</div>' +
        '<div class="phase"><span class="n">' + fmt(p.closing) + '</span>closing</div>' +
        '<div class="phase"><span class="n">' + fmt(p.audits) + '</span>audits</div>' +
        '<div class="phase"><span class="n">' + fmt(p.content) + '</span>content</div>';
    }
  } catch(e) { console.error(e); }
}

function connectWS() {
  ws = new WebSocket(wsUrl);
  ws.onopen = () => {
    document.getElementById('ws-status').textContent = 'Live';
    addEvent('', 'WebSocket connecté');
  };
  ws.onclose = () => {
    document.getElementById('ws-status').textContent = 'Reconnexion...';
    setTimeout(connectWS, 3000);
  };
  ws.onmessage = (ev) => {
    try {
      const msg = JSON.parse(ev.data);
      if (msg.type === 'cycle_complete') {
        addEvent('', '🔄 Cycle #' + msg.cycle + ' terminé (' + (msg.elapsed||0).toFixed(2) + 's) — outreach: ' + fmt(msg.phases?.outreach) + '€');
        refresh();
      } else if (msg.type === 'payment') {
        addEvent('payment', '💰 Paiement: ' + JSON.stringify(msg.data).slice(0, 120));
        refresh();
      } else if (msg.type === 'snapshot') {
        // snapshot initial
      }
    } catch(e) {}
  };
}

connectWS();
refresh();
setInterval(refresh, 15000);
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(DASHBOARD_HTML)


__all__ = ["app", "broadcaster", "push_cycle_update", "push_payment_event"]
