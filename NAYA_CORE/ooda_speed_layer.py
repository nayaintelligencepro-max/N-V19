"""
NAYA SUPREME — OODA Speed Layer
══════════════════════════════════════════════════════════════════════════════
Le différenciateur absolu : signal détecté → premier contact envoyé en < 90s.

DOCTRINE :
  La moyenne des concurrents humains réagit en 24-72h à un signal de marché.
  Les outils SaaS (Clay, Instantly) réagissent en 2-8h.
  NAYA réagit en < 90 secondes. C'est le moat de vitesse.

  Premier arrivé = 3x plus de chances de répondre.
  (Source : Harvard Business Review — "The Short Life of Online Sales Leads")

BOUCLE OODA NAYA :
  OBSERVE  → SignalRouter collecte les signaux entrants (pain, regulatory, news, reply)
  ORIENT   → CompositeScorer analyse et priorise (vecteur 6D)
  DECIDE   → ActionSelector choisit l'action optimale en < 1s
  ACT      → ActionExecutor émet l'ordre d'exécution (pipeline/outreach/offer)

TYPES DE SIGNAUX :
  ● pain_detected      → PainHunterAgent a trouvé une douleur score ≥ 70
  ● regulatory_trigger → RegulatoryTriggerEngine a émis un HuntSignal
  ● reply_received     → Prospect a répondu à un email ou message LinkedIn
  ● news_break         → Actualité cyberattaque / incident OT détectée
  ● job_post           → Offre d'emploi RSSI/OT détectée = budget confirmé

GARANTIE VITESSE :
  Chaque signal entrant est traité dans un ThreadPoolExecutor dédié.
  Objectif : < 90s de signal_received_at → action_dispatched_at.

OUTPUT :
  OODAAction — action priorisée prête pour dispatch (pipeline / outreach / offer)
══════════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional, Any

log = logging.getLogger("NAYA.OODA_SPEED")

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "cache" / "ooda_speed_layer.json"
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

# Types de signaux reconnus
SIGNAL_TYPES = {
    "pain_detected",
    "regulatory_trigger",
    "reply_received",
    "news_break",
    "job_post",
    "competitor_move",
    "contract_signed",
    "payment_received",
}


# ─── Structures ────────────────────────────────────────────────────────────────

@dataclass
class OODASignal:
    """Signal entrant dans la boucle OODA."""
    signal_id: str
    signal_type: str                # pain_detected | regulatory_trigger | ...
    payload: Dict[str, Any]         # données brutes du signal
    source: str                     # agent ou module source
    urgency: float = 0.5            # 0-1
    received_at: float = field(default_factory=time.time)
    processed: bool = False
    processing_time_ms: float = 0.0


@dataclass
class OODAAction:
    """Action décidée par la boucle OODA."""
    action_id: str
    signal_id: str
    action_type: str        # enqueue_hunt | send_offer | send_reply | generate_audit | ...
    priority: int           # 1-100
    payload: Dict[str, Any]
    rationale: str          # pourquoi cette action
    dispatch_target: str    # pipeline_manager | outreach_agent | offer_writer | ...
    sla_seconds: int        # délai max d'exécution
    dispatched_at: Optional[float] = None
    completed: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ─── Decision Rules ────────────────────────────────────────────────────────────

class OODADecisionRules:
    """
    Règles de décision déterministes pour la phase DECIDE de la boucle OODA.
    Chaque règle : (signal_type, condition) → (action_type, priority, sla_seconds, target)
    """

    @staticmethod
    def decide(signal: OODASignal) -> Optional[Dict[str, Any]]:
        """
        Retourne le descripteur d'action ou None si le signal doit être ignoré.
        """
        st = signal.signal_type
        p = signal.payload

        # ── pain_detected ────────────────────────────────────────────────────
        if st == "pain_detected":
            score = float(p.get("score", 0))
            budget = float(p.get("budget_estimate_eur", 0))
            if score >= 80 and budget >= 15000:
                return {
                    "action_type": "enqueue_hunt_urgent",
                    "priority": min(100, int(score) + 10),
                    "sla_seconds": 60,
                    "dispatch_target": "pipeline_manager",
                    "rationale": f"Pain score={score:.0f}, budget={budget:,.0f} EUR → chasse urgente",
                }
            if score >= 70:
                return {
                    "action_type": "enqueue_hunt",
                    "priority": int(score),
                    "sla_seconds": 90,
                    "dispatch_target": "pipeline_manager",
                    "rationale": f"Pain score={score:.0f} ≥ 70 → chasse standard",
                }

        # ── regulatory_trigger ───────────────────────────────────────────────
        elif st == "regulatory_trigger":
            pressure = float(p.get("pressure_score", 0))
            days = int(p.get("days_remaining", 999))
            budget = int(p.get("budget_estimate_eur", 0))
            if days <= 30 and pressure >= 80:
                return {
                    "action_type": "launch_regulatory_sprint",
                    "priority": 95,
                    "sla_seconds": 45,
                    "dispatch_target": "pipeline_manager",
                    "rationale": f"Deadline réglementaire dans {days}j (pressure={pressure:.0f}) → sprint immédiat",
                }
            if pressure >= 50:
                return {
                    "action_type": "enqueue_regulatory_hunt",
                    "priority": min(90, int(pressure)),
                    "sla_seconds": 90,
                    "dispatch_target": "pipeline_manager",
                    "rationale": f"Pression réglementaire {pressure:.0f} → chasse conformité {p.get('regulation', '')}",
                }

        # ── reply_received ───────────────────────────────────────────────────
        elif st == "reply_received":
            sentiment = p.get("sentiment", "neutral")
            reply_type = p.get("reply_type", "unknown")
            if sentiment == "positive" or reply_type == "interested":
                return {
                    "action_type": "send_meeting_link",
                    "priority": 98,
                    "sla_seconds": 30,
                    "dispatch_target": "closer_agent",
                    "rationale": "Réponse positive → envoyer lien de RDV immédiatement",
                }
            if reply_type == "objection":
                return {
                    "action_type": "handle_objection",
                    "priority": 85,
                    "sla_seconds": 60,
                    "dispatch_target": "closer_agent",
                    "rationale": "Objection détectée → réponse personnalisée < 60s",
                }
            if reply_type == "not_interested":
                return {
                    "action_type": "graceful_exit_and_recycle",
                    "priority": 40,
                    "sla_seconds": 300,
                    "dispatch_target": "zero_waste_recycler",
                    "rationale": "Pas intéressé → recycler contenu, relancer dans 90j",
                }

        # ── news_break ───────────────────────────────────────────────────────
        elif st == "news_break":
            keywords = p.get("keywords", [])
            hot_keywords = {"cyberattaque", "ransomware", "incident", "fuite", "compromis"}
            if any(kw in hot_keywords for kw in keywords):
                return {
                    "action_type": "generate_breaking_content",
                    "priority": 88,
                    "sla_seconds": 120,
                    "dispatch_target": "content_agent",
                    "rationale": f"Incident OT détecté → article LinkedIn + outreach avec angle actualité",
                }
            return {
                "action_type": "enrich_market_context",
                "priority": 55,
                "sla_seconds": 600,
                "dispatch_target": "researcher_agent",
                "rationale": "Actualité sectorielle → enrichir contexte marché",
            }

        # ── job_post ─────────────────────────────────────────────────────────
        elif st == "job_post":
            role = p.get("role", "").lower()
            hot_roles = {"rssi", "ot security", "iec 62443", "scada security", "cybersécurité industrielle"}
            if any(r in role for r in hot_roles):
                return {
                    "action_type": "enqueue_job_signal_hunt",
                    "priority": 80,
                    "sla_seconds": 90,
                    "dispatch_target": "pipeline_manager",
                    "rationale": f"Offre emploi '{p.get('role', '')}' → budget confirmé, lancer chasse",
                }

        # ── contract_signed ──────────────────────────────────────────────────
        elif st == "contract_signed":
            return {
                "action_type": "trigger_upsell_sequence",
                "priority": 75,
                "sla_seconds": 120,
                "dispatch_target": "closer_agent",
                "rationale": "Contrat signé → lancer séquence upsell dans 72h",
            }

        # ── payment_received ─────────────────────────────────────────────────
        elif st == "payment_received":
            return {
                "action_type": "record_revenue_and_recycle",
                "priority": 70,
                "sla_seconds": 60,
                "dispatch_target": "revenue_tracker",
                "rationale": "Paiement reçu → tracker + recycler assets → préparer next deal",
            }

        return None  # signal ignoré


# ─── Engine ────────────────────────────────────────────────────────────────────

class OODASpeedLayer:
    """
    Boucle OODA temps-réel : traite chaque signal entrant en < 90 secondes.

    Utilise un ThreadPoolExecutor pour garantir le parallélisme.
    Les actions produites sont stockées + dispatched vers les agents concernés.
    """

    SLA_TARGET_MS = 90_000   # 90 secondes

    def __init__(self, max_workers: int = 8) -> None:
        self._signals: List[OODASignal] = []
        self._actions: List[OODAAction] = []
        self._dispatchers: Dict[str, Callable[[OODAAction], None]] = {}
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="OODA")
        self._metrics = {
            "signals_received": 0,
            "signals_processed": 0,
            "actions_dispatched": 0,
            "avg_processing_ms": 0.0,
            "sla_breaches": 0,
        }
        self._load()
        log.info("OODASpeedLayer — initialisé avec %d workers, SLA=90s", max_workers)

    # ── Persistence ────────────────────────────────────────────────────────────

    def _load(self) -> None:
        try:
            if DATA_FILE.exists():
                raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
                self._metrics = raw.get("metrics", self._metrics)
        except Exception:
            pass

    def _save(self) -> None:
        try:
            DATA_FILE.write_text(
                json.dumps(
                    {"metrics": self._metrics, "updated_at": datetime.now(timezone.utc).isoformat()},
                    ensure_ascii=False, indent=2,
                ),
                encoding="utf-8",
            )
        except Exception:
            pass

    # ── Dispatcher Registration ────────────────────────────────────────────────

    def register_dispatcher(self, target: str, handler: Callable[[OODAAction], None]) -> None:
        """
        Enregistre un handler pour un dispatch_target donné.
        Exemple : register_dispatcher("pipeline_manager", pipeline_manager.enqueue_action)
        """
        self._dispatchers[target] = handler
        log.info("OODASpeedLayer — dispatcher enregistré: %s", target)

    # ── Signal Processing ──────────────────────────────────────────────────────

    def _process_signal(self, signal: OODASignal) -> Optional[OODAAction]:
        """
        Core OODA loop pour un signal.
        Retourne l'action décidée ou None.
        """
        t_start = time.time()

        # ── ORIENT ──
        # (le scoring composite est délégué au CompositeScorerV2 quand disponible)
        if signal.signal_type not in SIGNAL_TYPES:
            log.warning("OODASpeedLayer — signal type inconnu: %s", signal.signal_type)
            return None

        # ── DECIDE ──
        decision = OODADecisionRules.decide(signal)
        if decision is None:
            signal.processed = True
            signal.processing_time_ms = (time.time() - t_start) * 1000
            return None

        # ── ACT ──
        action_id = hashlib.sha256(
            f"{signal.signal_id}:{decision['action_type']}:{time.time()}".encode()
        ).hexdigest()[:16]

        action = OODAAction(
            action_id=action_id,
            signal_id=signal.signal_id,
            action_type=decision["action_type"],
            priority=decision["priority"],
            payload={**signal.payload, "_signal_type": signal.signal_type},
            rationale=decision["rationale"],
            dispatch_target=decision["dispatch_target"],
            sla_seconds=decision["sla_seconds"],
            dispatched_at=time.time(),
        )

        # Dispatcher l'action
        handler = self._dispatchers.get(decision["dispatch_target"])
        if handler:
            try:
                handler(action)
                action.completed = True
            except Exception as exc:
                log.error("OODASpeedLayer — dispatch failed for %s: %s", action.action_id, exc)

        processing_ms = (time.time() - t_start) * 1000
        signal.processed = True
        signal.processing_time_ms = processing_ms

        # Métriques
        with self._lock:
            self._metrics["signals_processed"] += 1
            self._metrics["actions_dispatched"] += 1
            n = self._metrics["signals_processed"]
            self._metrics["avg_processing_ms"] = (
                (self._metrics["avg_processing_ms"] * (n - 1) + processing_ms) / n
            )
            if processing_ms > self.SLA_TARGET_MS:
                self._metrics["sla_breaches"] += 1
                log.warning(
                    "OODASpeedLayer — SLA breach: %.0fms > %dms pour signal %s",
                    processing_ms, self.SLA_TARGET_MS, signal.signal_id[:8],
                )

        log.info(
            "OODA [%.0fms] %s → %s (prio=%d)",
            processing_ms, signal.signal_type, action.action_type, action.priority,
        )
        return action

    # ── Public API ─────────────────────────────────────────────────────────────

    def ingest(self, signal_type: str, payload: Dict[str, Any], source: str = "unknown") -> str:
        """
        Injecte un signal dans la boucle OODA.
        Non-bloquant : le traitement est soumis au ThreadPoolExecutor.

        Returns:
            signal_id pour tracking
        """
        signal_id = hashlib.sha256(
            f"{signal_type}:{source}:{time.time()}".encode()
        ).hexdigest()[:16]

        urgency_map = {
            "reply_received": 1.0,
            "regulatory_trigger": 0.9,
            "pain_detected": 0.8,
            "news_break": 0.75,
            "job_post": 0.7,
            "contract_signed": 0.85,
            "payment_received": 0.8,
        }

        signal = OODASignal(
            signal_id=signal_id,
            signal_type=signal_type,
            payload=payload,
            source=source,
            urgency=urgency_map.get(signal_type, 0.5),
        )

        with self._lock:
            self._signals.append(signal)
            if len(self._signals) > 5000:
                self._signals = self._signals[-2500:]
            self._metrics["signals_received"] += 1

        # Soumettre au pool
        self._executor.submit(self._process_signal, signal)
        self._save()

        log.debug("OODASpeedLayer — signal ingéré: %s/%s", signal_type, signal_id[:8])
        return signal_id

    def ingest_sync(self, signal_type: str, payload: Dict[str, Any], source: str = "unknown") -> Optional[OODAAction]:
        """
        Version synchrone pour tests et intégrations directes.
        Bloque jusqu'à l'action décidée.
        """
        signal_id = hashlib.sha256(
            f"{signal_type}:{source}:{time.time()}".encode()
        ).hexdigest()[:16]

        signal = OODASignal(
            signal_id=signal_id,
            signal_type=signal_type,
            payload=payload,
            source=source,
        )
        return self._process_signal(signal)

    def status(self) -> Dict:
        """Dashboard temps-réel de la boucle OODA."""
        with self._lock:
            pending = sum(1 for s in self._signals if not s.processed)
            recent = [s for s in self._signals[-20:]]
            avg_ms = self._metrics.get("avg_processing_ms", 0)
            sla_ok = avg_ms < self.SLA_TARGET_MS

        return {
            "signals_received": self._metrics["signals_received"],
            "signals_processed": self._metrics["signals_processed"],
            "signals_pending": pending,
            "actions_dispatched": self._metrics["actions_dispatched"],
            "avg_processing_ms": round(avg_ms, 1),
            "sla_target_ms": self.SLA_TARGET_MS,
            "sla_status": "✅ OK" if sla_ok else "⚠️ BREACH",
            "sla_breaches": self._metrics["sla_breaches"],
            "dispatchers_registered": list(self._dispatchers.keys()),
        }

    def recent_actions(self, n: int = 10) -> List[Dict]:
        """Dernières N actions dispatched."""
        with self._lock:
            signals_with_action = [s for s in self._signals[-100:] if s.processed]
        return [
            {
                "signal_type": s.signal_type,
                "source": s.source,
                "processing_ms": round(s.processing_time_ms, 1),
                "received_at": datetime.fromtimestamp(s.received_at, tz=timezone.utc).isoformat(),
            }
            for s in signals_with_action[-n:]
        ]

    def shutdown(self) -> None:
        """Arrêt propre du ThreadPoolExecutor."""
        self._executor.shutdown(wait=True)
        log.info("OODASpeedLayer — shutdown complet")


# ─── Singleton ────────────────────────────────────────────────────────────────

ooda_speed_layer = OODASpeedLayer()
