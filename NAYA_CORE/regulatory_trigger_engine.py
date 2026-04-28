"""
NAYA SUPREME — Regulatory Trigger Engine
══════════════════════════════════════════════════════════════════════════════
Aucun système concurrent ne fait ceci : surveiller en temps réel les échéances
réglementaires (NIS2, DORA, IEC 62443, AI Act, CNIL) et déclencher
automatiquement une chasse de prospects AVANT que le marché soit saturé.

DOCTRINE :
  Les entreprises DOIVENT acheter avant une deadline réglementaire.
  Budget identifié, urgence maximale, décideur sous pression.
  NAYA doit être en conversation AVANT les concurrents.

TRIGGERS COUVERTS :
  ● NIS2 — transpositions par pays + audits annuels
  ● DORA (Digital Operational Resilience Act) — Jan 2025 go-live + audits
  ● IEC 62443 — cycles recertification 3 ans
  ● AI Act (EU) — phases d'application par niveau de risque
  ● RGPD / CNIL — délais de mise en conformité post-sanction
  ● ISO 27001 — renouvellements triennaux
  ● Sectoriels — NF EN 50159 (ferroviaire), API CG-2 (pétrolier OT), etc.

ALGORITHME :
  1. Charger le calendrier réglementaire (JSON persistant + updates auto)
  2. Calculer pour chaque event : jours_restants, pressure_score (0-100)
  3. Si pressure_score ≥ seuil ET deadline_window → émettre HuntSignal
  4. HuntSignal consommé par PipelineManager → enqueue haute priorité

OUTPUT :
  list[RegulatoryHuntSignal] — prêt à injecter dans le pipeline NAYA
══════════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.REGULATORY_TRIGGER")

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "cache" / "regulatory_triggers.json"
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)


# ─── Structures ────────────────────────────────────────────────────────────────

@dataclass
class RegulatoryEvent:
    """Un échéance réglementaire avec son contexte business."""
    event_id: str
    regulation: str          # NIS2 | DORA | IEC62443 | AI_ACT | RGPD | ISO27001 | ...
    title: str
    deadline_iso: str        # YYYY-MM-DD
    sectors: List[str]       # secteurs visés
    countries: List[str]     # pays visés (FR, EU, US, ...)
    budget_floor_eur: int    # budget minimum typique de conformité
    budget_ceiling_eur: int
    urgency_window_days: int = 90   # fenêtre d'activation avant deadline
    active: bool = True
    notes: str = ""


@dataclass
class RegulatoryHuntSignal:
    """Signal émis vers le PipelineManager pour lancer une chasse ciblée."""
    signal_id: str
    regulation: str
    title: str
    deadline_iso: str
    days_remaining: int
    pressure_score: float    # 0-100 : plus la deadline est proche, plus c'est élevé
    target_sectors: List[str]
    target_countries: List[str]
    budget_estimate_eur: int
    priority: int            # priorité pipeline 1-100
    hunt_query: str          # requête de recherche suggérée
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ─── Calendrier réglementaire intégré ──────────────────────────────────────────

_BUILTIN_EVENTS: List[Dict] = [
    # ── NIS2 ──
    {
        "event_id": "nis2_fr_transposition",
        "regulation": "NIS2",
        "title": "NIS2 transposition France — audits conformité entreprises essentielles",
        "deadline_iso": "2025-10-18",
        "sectors": ["Transport", "Energie", "Santé", "Eau", "Numérique", "Banque"],
        "countries": ["FR", "EU"],
        "budget_floor_eur": 15000,
        "budget_ceiling_eur": 80000,
        "urgency_window_days": 180,
        "notes": "Directive UE 2022/2555 — entités essentielles et importantes",
    },
    {
        "event_id": "nis2_annual_audit_2025",
        "regulation": "NIS2",
        "title": "NIS2 — Premier cycle d'audits annuels obligatoires",
        "deadline_iso": "2026-03-31",
        "sectors": ["Transport", "Energie", "Manufacturing", "Eau"],
        "countries": ["FR", "DE", "BE", "NL", "ES"],
        "budget_floor_eur": 20000,
        "budget_ceiling_eur": 60000,
        "urgency_window_days": 120,
        "notes": "Premières sanctions possibles dès Q1 2026",
    },
    # ── DORA ──
    {
        "event_id": "dora_golive",
        "regulation": "DORA",
        "title": "DORA — Digital Operational Resilience Act opérationnel",
        "deadline_iso": "2025-01-17",
        "sectors": ["Banque", "Assurance", "Fintech", "Infrastructure Financière"],
        "countries": ["EU", "FR", "DE", "LU"],
        "budget_floor_eur": 30000,
        "budget_ceiling_eur": 150000,
        "urgency_window_days": 90,
        "notes": "ICT risk management, testing, incident reporting obligatoires",
    },
    {
        "event_id": "dora_audit_cycle_1",
        "regulation": "DORA",
        "title": "DORA — Premier cycle tests de résilience opérationnelle avancés",
        "deadline_iso": "2026-01-17",
        "sectors": ["Banque", "Assurance"],
        "countries": ["EU"],
        "budget_floor_eur": 40000,
        "budget_ceiling_eur": 200000,
        "urgency_window_days": 120,
    },
    # ── IEC 62443 ──
    {
        "event_id": "iec62443_recert_q4_2025",
        "regulation": "IEC62443",
        "title": "IEC 62443 — Vague recertifications industrielles Q4 2025",
        "deadline_iso": "2025-12-31",
        "sectors": ["Manufacturing", "Energie", "Chimie", "Eau", "Transport"],
        "countries": ["FR", "DE", "IT", "ES", "BE"],
        "budget_floor_eur": 15000,
        "budget_ceiling_eur": 80000,
        "urgency_window_days": 150,
        "notes": "Cycle 3 ans — dernière recertification Q4 2022",
    },
    {
        "event_id": "iec62443_recert_q2_2026",
        "regulation": "IEC62443",
        "title": "IEC 62443 — Vague recertifications Q2 2026",
        "deadline_iso": "2026-06-30",
        "sectors": ["Manufacturing", "Energie"],
        "countries": ["EU"],
        "budget_floor_eur": 15000,
        "budget_ceiling_eur": 60000,
        "urgency_window_days": 120,
    },
    # ── AI Act ──
    {
        "event_id": "ai_act_high_risk_2026",
        "regulation": "AI_ACT",
        "title": "AI Act UE — Conformité systèmes IA haut risque obligatoire",
        "deadline_iso": "2026-08-02",
        "sectors": ["Santé", "Transport", "Infrastructure Critique", "Manufacturing"],
        "countries": ["EU"],
        "budget_floor_eur": 20000,
        "budget_ceiling_eur": 100000,
        "urgency_window_days": 180,
        "notes": "Art.6 — systèmes annexe III (recrutement, sécurité infrastructure, etc.)",
    },
    # ── ISO 27001 ──
    {
        "event_id": "iso27001_renewal_wave_2025",
        "regulation": "ISO27001",
        "title": "ISO 27001:2022 — Vague renouvellements 2025 (transition obligatoire)",
        "deadline_iso": "2025-10-31",
        "sectors": ["Numérique", "Manufacturing", "Logistique", "Transport"],
        "countries": ["FR", "EU"],
        "budget_floor_eur": 10000,
        "budget_ceiling_eur": 40000,
        "urgency_window_days": 120,
        "notes": "Transition ISO 27001:2013 → :2022 deadline finale",
    },
    # ── NF EN 50159 (Rail) ──
    {
        "event_id": "rail_safety_50159_2026",
        "regulation": "NF_EN_50159",
        "title": "NF EN 50159 — Sécurité transmissions ferroviaires OT",
        "deadline_iso": "2026-03-01",
        "sectors": ["Transport", "Ferroviaire"],
        "countries": ["FR", "BE", "CH"],
        "budget_floor_eur": 25000,
        "budget_ceiling_eur": 90000,
        "urgency_window_days": 120,
        "notes": "SNCF, RATP, Infrabel — revue sécurité systèmes bord",
    },
    # ── CNIL / RGPD ──
    {
        "event_id": "cnil_penalty_followup",
        "regulation": "RGPD",
        "title": "RGPD — Entreprises sous mise en demeure CNIL 2025",
        "deadline_iso": "2025-09-30",
        "sectors": ["Numérique", "Retail", "Santé", "Finance"],
        "countries": ["FR"],
        "budget_floor_eur": 8000,
        "budget_ceiling_eur": 30000,
        "urgency_window_days": 90,
        "notes": "Données mises en demeure publiques CNIL — budget forcé",
    },
]


# ─── Engine ────────────────────────────────────────────────────────────────────

class RegulatoryTriggerEngine:
    """
    Surveille un calendrier réglementaire et émet des HuntSignals
    automatiquement quand une deadline approche.

    Thread-safe. Persistance JSON. Aucune dépendance externe.
    """

    PRESSURE_THRESHOLD = 30.0   # pressure_score minimum pour émettre un signal

    def __init__(self) -> None:
        self._events: List[RegulatoryEvent] = []
        self._emitted: set[str] = set()          # signal_ids déjà émis (évite les doublons)
        self._lock = threading.RLock()
        self._load()

    # ── Persistence ────────────────────────────────────────────────────────────

    def _load(self) -> None:
        """Charge état depuis JSON + injecte les événements intégrés si vide."""
        try:
            if DATA_FILE.exists():
                raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
                self._events = [RegulatoryEvent(**e) for e in raw.get("events", [])]
                self._emitted = set(raw.get("emitted", []))
        except Exception as exc:
            log.warning("RegulatoryTriggerEngine load failed: %s — using builtins", exc)

        if not self._events:
            self._events = [RegulatoryEvent(**e) for e in _BUILTIN_EVENTS]
            log.info("RegulatoryTriggerEngine — loaded %d built-in events", len(self._events))
        self._save()

    def _save(self) -> None:
        try:
            payload = {
                "events": [asdict(e) for e in self._events],
                "emitted": list(self._emitted),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            DATA_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            log.error("RegulatoryTriggerEngine save failed: %s", exc)

    # ── Core ───────────────────────────────────────────────────────────────────

    def _pressure_score(self, days_remaining: int, urgency_window: int) -> float:
        """
        Calcule le score de pression réglementaire [0-100].
        100 = deadline dépassée ou dans 7 jours
        0   = deadline dans plus de 2x urgency_window jours
        """
        if days_remaining <= 7:
            return 100.0
        if days_remaining >= urgency_window * 2:
            return 0.0
        # Courbe exponentielle inverse
        ratio = max(0.0, 1.0 - (days_remaining / urgency_window))
        return round(min(100.0, ratio ** 1.5 * 100), 2)

    def _build_hunt_query(self, event: RegulatoryEvent) -> str:
        sectors_str = " OR ".join(event.sectors[:3])
        return (
            f'"{event.regulation}" conformité '
            f'({sectors_str}) '
            f'("RSSI" OR "DSI" OR "Responsable cybersécurité" OR "DPO") '
            f'site:linkedin.com OR site:welcome.jobs OR site:apec.fr'
        )

    def scan(self, force: bool = False) -> List[RegulatoryHuntSignal]:
        """
        Analyse le calendrier et retourne les HuntSignals actifs.

        Args:
            force: Si True, réémet même les signaux déjà émis.

        Returns:
            Liste de RegulatoryHuntSignal triée par pressure_score décroissant.
        """
        today = date.today()
        signals: List[RegulatoryHuntSignal] = []

        with self._lock:
            for event in self._events:
                if not event.active:
                    continue
                try:
                    deadline = date.fromisoformat(event.deadline_iso)
                except ValueError:
                    continue

                days_remaining = (deadline - today).days
                pressure = self._pressure_score(days_remaining, event.urgency_window_days)

                if pressure < self.PRESSURE_THRESHOLD:
                    continue

                signal_id = hashlib.sha256(
                    f"{event.event_id}:{today.isoformat()}".encode()
                ).hexdigest()[:16]

                if signal_id in self._emitted and not force:
                    continue

                priority = min(100, int(pressure) + (20 if days_remaining <= 30 else 0))
                budget_mid = (event.budget_floor_eur + event.budget_ceiling_eur) // 2

                sig = RegulatoryHuntSignal(
                    signal_id=signal_id,
                    regulation=event.regulation,
                    title=event.title,
                    deadline_iso=event.deadline_iso,
                    days_remaining=days_remaining,
                    pressure_score=pressure,
                    target_sectors=event.sectors,
                    target_countries=event.countries,
                    budget_estimate_eur=budget_mid,
                    priority=priority,
                    hunt_query=self._build_hunt_query(event),
                )
                signals.append(sig)
                self._emitted.add(signal_id)

            self._save()

        signals.sort(key=lambda s: s.pressure_score, reverse=True)
        log.info(
            "RegulatoryTriggerEngine.scan() → %d signals actifs (threshold=%.0f)",
            len(signals), self.PRESSURE_THRESHOLD,
        )
        return signals

    # ── Management API ─────────────────────────────────────────────────────────

    def add_event(self, event: RegulatoryEvent) -> None:
        """Ajoute un événement réglementaire au calendrier."""
        with self._lock:
            self._events.append(event)
            self._save()
        log.info("RegulatoryTriggerEngine — event ajouté: %s", event.event_id)

    def deactivate_event(self, event_id: str) -> bool:
        """Désactive un événement (deadline passée ou hors scope)."""
        with self._lock:
            for e in self._events:
                if e.event_id == event_id:
                    e.active = False
                    self._save()
                    return True
        return False

    def status(self) -> Dict:
        """Résumé de l'état du moteur."""
        today = date.today()
        active_events = [e for e in self._events if e.active]
        upcoming = [
            e for e in active_events
            if (date.fromisoformat(e.deadline_iso) - today).days <= e.urgency_window_days
        ]
        return {
            "total_events": len(self._events),
            "active_events": len(active_events),
            "in_urgency_window": len(upcoming),
            "signals_emitted_today": len(self._emitted),
            "pressure_threshold": self.PRESSURE_THRESHOLD,
        }

    def top_opportunities(self, n: int = 5) -> List[Dict]:
        """Top N opportunités réglementaires par budget × pressure."""
        today = date.today()
        results = []
        for e in self._events:
            if not e.active:
                continue
            try:
                days = (date.fromisoformat(e.deadline_iso) - today).days
            except ValueError:
                continue
            pressure = self._pressure_score(days, e.urgency_window_days)
            score = pressure * (e.budget_ceiling_eur / 10000)
            results.append({
                "regulation": e.regulation,
                "title": e.title,
                "deadline": e.deadline_iso,
                "days_remaining": days,
                "pressure_score": pressure,
                "budget_range": f"{e.budget_floor_eur:,}–{e.budget_ceiling_eur:,} EUR",
                "sectors": e.sectors[:3],
                "opportunity_score": round(score, 1),
            })
        results.sort(key=lambda x: x["opportunity_score"], reverse=True)
        return results[:n]


# ─── Singleton ────────────────────────────────────────────────────────────────

regulatory_trigger_engine = RegulatoryTriggerEngine()
