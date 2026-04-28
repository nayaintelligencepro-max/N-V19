"""
NAYA SUPREME V19 — PARALLEL PIPELINE MANAGER
═══════════════════════════════════════════════════════════════
4 projets actifs EN PERMANENCE. Rechargement auto. Zéro idle.

PRINCIPE:
  ┌─────────────────────────────────────────────────────────┐
  │  SLOT 1 [ACTIF]  → projet A (ex: Catalogue OT 15k€)    │
  │  SLOT 2 [ACTIF]  → projet B (ex: IEC62443 Energie 40k€)│
  │  SLOT 3 [ACTIF]  → projet C (ex: Formation OT 5k€)     │
  │  SLOT 4 [ACTIF]  → projet D (ex: Upsell client 8k€)    │
  └─────────────────────────────────────────────────────────┘
  Dès qu'un slot se libère → rechargement depuis la queue
  Chaque projet fermé → recyclé en v+1 avec objectif +30%
  Tout asset créé → versionné dans la bibliothèque ZeroWaste

CYCLE DE VIE:
  QUEUE → SLOT_ACTIF → [DONE / FAILED] → RECYCLE_v+1 → QUEUE
═══════════════════════════════════════════════════════════════
"""
import json, time, uuid, logging, threading
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from enum import Enum
from pathlib import Path
from datetime import datetime

log = logging.getLogger("NAYA.PARALLEL")
ROOT = Path(__file__).resolve().parent.parent


class ProjStatus(Enum):
    QUEUED    = "queued"
    ACTIVE    = "active"
    DONE      = "done"
    FAILED    = "failed"
    RECYCLED  = "recycled"


class ProjType(Enum):
    CATALOGUE_OT   = "catalogue_ot"
    FORMATION      = "formation"
    UPSELL         = "upsell"
    OUTREACH       = "outreach"
    MEGA_PROJECT   = "mega_project"
    PARTENARIAT    = "partenariat"
    INBOUND        = "inbound"


@dataclass
class Projet:
    id: str = field(default_factory=lambda: f"P{uuid.uuid4().hex[:6].upper()}")
    nom: str = ""
    type: ProjType = ProjType.CATALOGUE_OT
    status: ProjStatus = ProjStatus.QUEUED
    slot: Optional[int] = None
    target_eur: float = 0.0
    earned_eur: float = 0.0
    priority: float = 0.5        # 0..1 — trié par priorité
    version: int = 1
    parent_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    done_at: Optional[float] = None
    actions: List[str] = field(default_factory=list)
    assets: List[str] = field(default_factory=list)   # IDs d'assets ZeroWaste
    notes: str = ""


@dataclass
class Slot:
    id: int
    projet: Optional[Projet] = None

    @property
    def libre(self) -> bool:
        return self.projet is None


class ParallelPipelineManager:
    """
    Gestionnaire de 4 slots parallèles.
    Rechargement automatique. Recyclage systématique. Zéro idle.
    """
    N_SLOTS = 4
    FILE = ROOT / "data" / "cache" / "parallel_pipeline.json"

    def __init__(self):
        self.slots: List[Slot] = [Slot(i) for i in range(self.N_SLOTS)]
        self.queue: List[Projet] = []
        self.archives: List[Projet] = []
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.FILE.parent.mkdir(parents=True, exist_ok=True)
        self._load()
        self._seed_if_empty()
        log.info("ParallelPipelineManager V19 — %d slots", self.N_SLOTS)

    # ── SEED INITIAL ──────────────────────────────────────────────────────
    def _seed_if_empty(self):
        """Pré-charge 8 projets de démarrage si le pipeline est vide."""
        if self.queue or any(s.projet for s in self.slots):
            return
        seeds = [
            Projet(nom="Catalogue OT Transport — 10 pitchs",
                   type=ProjType.CATALOGUE_OT, target_eur=15_000, priority=0.98,
                   actions=["Générer 10 pitchs email Transport", "Envoyer via Gmail",
                             "Follow-up J+3 par LinkedIn", "Closing appel téléphonique"]),
            Projet(nom="IEC62443 Énergie — 5 OIV NIS2",
                   type=ProjType.CATALOGUE_OT, target_eur=40_000, priority=0.95,
                   actions=["Contacter 5 RSSI OIV énergie", "Pitch Pack Sécurité Avancée 40k",
                             "Deadline NIS2 comme urgence", "Closing sous 14j"]),
            Projet(nom="Formation OT 1 jour — cash 48h",
                   type=ProjType.FORMATION, target_eur=5_000, priority=0.99,
                   actions=["Appeler 3 DSI industriels connus", "Proposer formation 1j à 5k€",
                             "Créer lien PayPal 5000€", "Livrer contenu PDF inclus"]),
            Projet(nom="Upsell — Monitoring mensuel clients actifs",
                   type=ProjType.UPSELL, target_eur=3_000, priority=0.88,
                   actions=["Proposer monitoring 2k-5k€/mois à clients M1",
                             "Contrat 12 mois avec -10% annuel",
                             "Objectif 3 clients = 6k€ MRR"]),
            Projet(nom="Outreach Industrie Manufacturière — 15 contacts",
                   type=ProjType.OUTREACH, target_eur=18_000, priority=0.82,
                   actions=["LinkedIn 10 messages/j RSSI industrie", "Pack Audit Express 15k",
                             "Argument: ISO 27001 + IEC 62443 = compliant NIS2"]),
            Projet(nom="Partenariat intégrateur industriel",
                   type=ProjType.PARTENARIAT, target_eur=25_000, priority=0.75,
                   actions=["Contacter 3 intégrateurs (Siemens partner, Schneider)",
                             "Accord rev-share 30% sur deals apportés",
                             "Premier deal commun en 30j"]),
            Projet(nom="Catalogue OT Polynésie — marché local",
                   type=ProjType.CATALOGUE_OT, target_eur=12_000, priority=0.70,
                   actions=["Adapter catalogue OT secteur Pacifique",
                             "Prospecter OPT, EDT, Air Tahiti, Port Papeete",
                             "Pack Audit Express 12k€ adapté"]),
            Projet(nom="Pack Premium Full — Grand Compte CAC40",
                   type=ProjType.CATALOGUE_OT, target_eur=80_000, priority=0.65,
                   actions=["Identifier 3 grands comptes avec OT exposé",
                             "Passer par procurement / acheteurs",
                             "Closing 45j Pack Premium Full 80k€"]),
        ]
        for p in seeds:
            self.enqueue(p)

    # ── GESTION QUEUE ─────────────────────────────────────────────────────
    def enqueue(self, projet: Projet):
        """Ajoute un projet en queue triée par priorité."""
        with self._lock:
            self.queue.append(projet)
            self.queue.sort(key=lambda p: p.priority, reverse=True)
        self._fill_slots()
        log.info("Queue +1: %s (prio=%.2f) | queue=%d", projet.nom, projet.priority, len(self.queue))

    def _fill_slots(self):
        """Remplit tous les slots libres depuis la queue."""
        with self._lock:
            for slot in self.slots:
                if slot.libre and self.queue:
                    p = self.queue.pop(0)
                    slot.projet = p
                    p.status = ProjStatus.ACTIVE
                    p.slot = slot.id
                    p.started_at = time.time()
                    log.info("SLOT %d → %s | target=%s€", slot.id, p.nom, p.target_eur)
        self._save()

    # ── CLOSING / RECYCLAGE ───────────────────────────────────────────────
    def close_project(self, project_id: str, earned: float = 0.0,
                      success: bool = True, assets: List[str] = None):
        """
        Ferme un projet, enregistre le revenu, le recycle en v+1.
        Principe ZERO WASTE: chaque fermeture génère un nouveau projet recyclé.
        """
        with self._lock:
            for slot in self.slots:
                if slot.projet and slot.projet.id == project_id:
                    p = slot.projet
                    p.status = ProjStatus.DONE if success else ProjStatus.FAILED
                    p.earned_eur = earned
                    p.done_at = time.time()
                    if assets:
                        p.assets.extend(assets)

                    # RECYCLAGE AUTOMATIQUE
                    recycled = self._recycle(p)

                    self.archives.append(p)
                    slot.projet = None  # Libérer le slot

                    log.info("SLOT %d FERMÉ: %s | +%.0f€ | Recyclé: v%d",
                             slot.id, p.nom, earned, recycled.version)
                    break

        self._fill_slots()  # Recharger immédiatement
        self._save()

    def _recycle(self, p: Projet) -> Projet:
        """
        Recycle le projet en v+1 :
        - Réutilise les actions, assets, et contexte
        - Augmente l'objectif de +30%
        - Boost la priorité de +0.05
        """
        recycled = Projet(
            nom=f"[v{p.version+1}] {p.nom.lstrip('[v0123456789] ')}",
            type=p.type,
            target_eur=round(p.target_eur * 1.30, -2),  # +30%, arrondi centaine
            priority=min(p.priority + 0.05, 0.99),
            version=p.version + 1,
            parent_id=p.id,
            actions=[f"↩ REPRISE: {a}" for a in p.actions[:3]] + [
                "Recycler les assets de la version précédente",
                "Affiner le pitch basé sur les retours",
            ],
            assets=p.assets.copy(),
            notes=f"Recyclé depuis {p.id} | earned={p.earned_eur}€ | success={p.status.value}",
            status=ProjStatus.RECYCLED,
        )
        recycled.status = ProjStatus.QUEUED
        self.queue.append(recycled)
        self.queue.sort(key=lambda x: x.priority, reverse=True)
        log.info("RECYCLE: %s → v%d | target=%s€", recycled.nom, recycled.version, recycled.target_eur)
        return recycled

    # ── MONITOR ───────────────────────────────────────────────────────────
    def start(self):
        """Démarre le monitoring background (vérif toutes les 5 min)."""
        self._running = True
        self._thread = threading.Thread(target=self._monitor, daemon=True)
        self._thread.start()
        log.info("ParallelPipeline monitor démarré")

    def stop(self):
        self._running = False

    def _monitor(self):
        """Détecte les slots bloqués >7j et les force-recycle."""
        while self._running:
            try:
                self._fill_slots()   # S'assurer que les slots sont toujours remplis
                self._check_stalled()
                time.sleep(300)
            except Exception as e:
                log.warning("Monitor: %s", e)
                time.sleep(60)

    def _check_stalled(self):
        """Relance les projets bloqués depuis plus de 7 jours."""
        threshold = 7 * 86400
        with self._lock:
            for slot in self.slots:
                if slot.projet and slot.projet.started_at:
                    age = time.time() - slot.projet.started_at
                    if age > threshold:
                        slot.projet.actions.append(
                            f"[AUTO-RELANCE {datetime.now().strftime('%d/%m')}] "
                            "Projet bloqué — appel direct prospect prioritaire"
                        )
                        log.warning("Projet bloqué: %s (%.0fj)", slot.projet.nom, age/86400)

    # ── DASHBOARD ────────────────────────────────────────────────────────
    def get_dashboard(self) -> Dict:
        actifs = [p for s in self.slots if (p := s.projet)]
        total_earned = sum(p.earned_eur for p in self.archives)
        pipeline_val = sum(p.target_eur for p in actifs) + sum(
            p.target_eur for p in self.queue[:5])
        recycled_count = sum(1 for p in self.queue if p.status == ProjStatus.RECYCLED
                              or (p.parent_id is not None))
        return {
            "slots_actifs": len(actifs),
            "slots_libres": self.N_SLOTS - len(actifs),
            "projets_actifs": [
                {"id": p.id, "nom": p.nom, "target": p.target_eur,
                 "actions_prochaines": p.actions[:2],
                 "age_jours": round((time.time() - (p.started_at or time.time())) / 86400, 1)}
                for p in actifs
            ],
            "queue_taille": len(self.queue),
            "queue_top3": [{"nom": p.nom, "target": p.target_eur,
                             "prio": p.priority} for p in self.queue[:3]],
            "projets_fermes": len(self.archives),
            "projets_recycles": recycled_count,
            "revenu_total": total_earned,
            "valeur_pipeline": pipeline_val,
            "zero_waste_taux": f"{recycled_count/max(len(self.archives),1)*100:.0f}%",
        }

    # ── PERSIST ──────────────────────────────────────────────────────────
    def _save(self):
        def _ser(o):
            d = asdict(o)
            d["type"] = o.type.value
            d["status"] = o.status.value
            return d
        try:
            data = {
                "slots": [{"id": s.id, "projet": _ser(s.projet) if s.projet else None}
                           for s in self.slots],
                "queue": [_ser(p) for p in self.queue],
                "archives": [_ser(p) for p in self.archives[-100:]],
                "ts": time.time(),
            }
            self.FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            log.warning("Pipeline save: %s", e)

    def _load(self):
        def _deser(d: dict) -> Projet:
            d = {**d}
            d["type"] = ProjType(d.get("type", "catalogue_ot"))
            d["status"] = ProjStatus(d.get("status", "queued"))
            return Projet(**{k: v for k, v in d.items() if k in Projet.__dataclass_fields__})
        try:
            if self.FILE.exists():
                data = json.loads(self.FILE.read_text(encoding="utf-8"))
                for sd in data.get("slots", []):
                    if sd.get("projet"):
                        p = _deser(sd["projet"])
                        self.slots[sd["id"]].projet = p
                self.queue = [_deser(p) for p in data.get("queue", [])]
                self.archives = [_deser(p) for p in data.get("archives", [])]
                log.info("Pipeline chargé: %d slots, %d queue, %d archives",
                         sum(1 for s in self.slots if s.projet),
                         len(self.queue), len(self.archives))
        except Exception as e:
            log.warning("Pipeline load: %s", e)


# ── SINGLETON ────────────────────────────────────────────────────────────────
_inst: Optional[ParallelPipelineManager] = None

def get_parallel_pipeline() -> ParallelPipelineManager:
    global _inst
    if _inst is None:
        _inst = ParallelPipelineManager()
        _inst.start()
    return _inst
