"""
NAYA V19 — Tester Unit Engine (Shared — Physical Product Projects)
==================================================================
Règle souveraine : pour TOUT projet à produit physique, le système
négocié systématiquement des unités testeur à envoyer au propriétaire
avant tout lancement commercial.

Motif : valider la qualité réelle avant de vendre, alimenter le
storytelling avec une expérience authentique, détecter les défauts
fournisseur en amont.

Applicable à :
  · PROJECT_04_TINY_HOUSE  (modules habitables)
  · PROJECT_03_NAYA_BOTANICA (cosmétiques naturels)
  · Tout futur projet physique

Interface :
    register_project(project_id, product_type, specs) → enregistre le projet
    request_tester(project_id, quantity, notes)       → crée une demande testeur
    update_status(request_id, status, notes)          → avance le statut
    record_assessment(request_id, score, feedback)    → retour qualité propriétaire
    get_all_requests()                                → état global toutes demandes
    get_project_requests(project_id)                  → demandes par projet
"""
import time
import uuid
import logging
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

log = logging.getLogger("NAYA.TESTER")

PHYSICAL_PROJECTS: List[str] = [
    "PROJECT_04_TINY_HOUSE",
    "PROJECT_03_NAYA_BOTANICA",
]


class TesterStatus(Enum):
    REQUESTED    = "requested"
    NEGOTIATING  = "negotiating"
    CONFIRMED    = "confirmed"
    PRODUCING    = "producing"
    SHIPPED      = "shipped"
    IN_TRANSIT   = "in_transit"
    DELIVERED    = "delivered"
    ASSESSED     = "assessed"
    REJECTED     = "rejected"


STATUS_TRANSITIONS: Dict[str, List[str]] = {
    TesterStatus.REQUESTED.value:   [TesterStatus.NEGOTIATING.value, TesterStatus.REJECTED.value],
    TesterStatus.NEGOTIATING.value: [TesterStatus.CONFIRMED.value,   TesterStatus.REJECTED.value],
    TesterStatus.CONFIRMED.value:   [TesterStatus.PRODUCING.value],
    TesterStatus.PRODUCING.value:   [TesterStatus.SHIPPED.value],
    TesterStatus.SHIPPED.value:     [TesterStatus.IN_TRANSIT.value],
    TesterStatus.IN_TRANSIT.value:  [TesterStatus.DELIVERED.value],
    TesterStatus.DELIVERED.value:   [TesterStatus.ASSESSED.value,    TesterStatus.REJECTED.value],
    TesterStatus.ASSESSED.value:    [],
    TesterStatus.REJECTED.value:    [TesterStatus.REQUESTED.value],
}


@dataclass
class TesterRequest:
    id: str = field(default_factory=lambda: f"TST-{uuid.uuid4().hex[:8].upper()}")
    project_id: str = ""
    product_type: str = ""
    quantity: int = 1
    specs_summary: str = ""
    status: TesterStatus = TesterStatus.REQUESTED
    supplier: Optional[str] = None
    tracking_ref: Optional[str] = None
    assessment_score: Optional[float] = None
    assessment_feedback: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    history: List[Dict] = field(default_factory=list)
    # Réf discrète du destinataire (propriétaire, ne jamais exposer en externe)
    _recipient_internal: str = "OWNER_QA_VALIDATOR"

    def transition(self, new_status: str, notes: str = "") -> bool:
        allowed = STATUS_TRANSITIONS.get(self.status.value, [])
        if new_status not in allowed:
            return False
        self.history.append({
            "from": self.status.value,
            "to": new_status,
            "ts": time.time(),
            "notes": notes,
        })
        self.status = TesterStatus(new_status)
        self.updated_at = time.time()
        return True


@dataclass
class RegisteredProject:
    project_id: str
    product_type: str
    is_physical: bool = True
    tester_policy: str = "mandatory"  # mandatory | optional | exempted
    default_quantity: int = 1
    notes: str = ""
    registered_at: float = field(default_factory=time.time)


class TesterUnitEngine:
    """
    Moteur testeur universel — produits physiques NAYA.

    Enforce la règle : pour tout produit physique, demander des unités
    testeur avant le lancement commercial, destinées au propriétaire
    pour validation qualité personnelle.

    Le framing externe est toujours "validation qualité / qualification
    fournisseur" — jamais "usage personnel propriétaire".
    """

    FLOOR_EUR = 0.0  # Pas de prix minimum sur les testeurs (parfois gratuits)

    def __init__(self) -> None:
        self._lock       = threading.RLock()
        self._projects:  Dict[str, RegisteredProject] = {}
        self._requests:  Dict[str, TesterRequest]     = {}
        self._initialized_at = time.time()
        # Pré-enregistrer les projets physiques connus
        self._bootstrap_known_projects()
        log.info("[TESTER] TesterUnitEngine initialisé")

    def _bootstrap_known_projects(self) -> None:
        defaults = [
            ("PROJECT_04_TINY_HOUSE",    "module_habitat_20m2",  2),
            ("PROJECT_03_NAYA_BOTANICA", "cosmétique_naturel",   3),
        ]
        for pid, ptype, qty in defaults:
            self._projects[pid] = RegisteredProject(
                project_id=pid, product_type=ptype,
                default_quantity=qty,
                notes="Pré-enregistré au boot TesterUnitEngine",
            )

    # ── Enregistrement ─────────────────────────────────────────────────────

    def register_project(self, project_id: str, product_type: str,
                         quantity: int = 1, notes: str = "") -> Dict:
        """Enregistre un projet physique dans le moteur testeur."""
        with self._lock:
            self._projects[project_id] = RegisteredProject(
                project_id=project_id, product_type=product_type,
                default_quantity=quantity, notes=notes,
            )
            log.info(f"[TESTER] Projet enregistré: {project_id} | {product_type} | qty={quantity}")
            return {"registered": True, "project_id": project_id,
                    "product_type": product_type, "default_quantity": quantity}

    # ── Demande testeur ────────────────────────────────────────────────────

    def request_tester(self, project_id: str, quantity: Optional[int] = None,
                       specs_summary: str = "", supplier: Optional[str] = None,
                       notes: str = "") -> Dict:
        """
        Crée une demande testeur pour un projet physique.
        Framing externe : 'validation qualité fournisseur'.
        """
        with self._lock:
            proj = self._projects.get(project_id)
            if proj is None:
                return {"error": f"Projet '{project_id}' non enregistré",
                        "hint": "Appeler register_project() d'abord"}
            qty = quantity if quantity is not None else proj.default_quantity
            req = TesterRequest(
                project_id=project_id,
                product_type=proj.product_type,
                quantity=qty,
                specs_summary=specs_summary or f"Unité testeur {proj.product_type} — validation qualité",
                supplier=supplier,
            )
            self._requests[req.id] = req
            log.info(f"[TESTER] Demande créée: {req.id} | {project_id} | qty={qty}")
            return {
                "request_id": req.id,
                "project_id": project_id,
                "product_type": proj.product_type,
                "quantity": qty,
                "status": req.status.value,
                "external_framing": "Validation qualité fournisseur — unité prototype",
                "notes": notes,
            }

    # ── Avancement ─────────────────────────────────────────────────────────

    def update_status(self, request_id: str, new_status: str,
                      notes: str = "", tracking_ref: Optional[str] = None,
                      supplier: Optional[str] = None) -> Dict:
        """Avance le statut d'une demande testeur."""
        with self._lock:
            req = self._requests.get(request_id)
            if req is None:
                return {"error": "Demande non trouvée", "request_id": request_id}
            if tracking_ref:
                req.tracking_ref = tracking_ref
            if supplier:
                req.supplier = supplier
            ok = req.transition(new_status, notes)
            if not ok:
                allowed = STATUS_TRANSITIONS.get(req.status.value, [])
                return {"error": f"Transition interdite: {req.status.value} → {new_status}",
                        "allowed_transitions": allowed, "request_id": request_id}
            log.info(f"[TESTER] {request_id} → {new_status}")
            return {"request_id": request_id, "new_status": new_status,
                    "project_id": req.project_id, "tracking_ref": req.tracking_ref}

    # ── Assessment ─────────────────────────────────────────────────────────

    def record_assessment(self, request_id: str, score: float,
                          feedback: str = "") -> Dict:
        """
        Enregistre le retour qualité du propriétaire sur l'unité reçue.
        Score 0–10. ≥ 7 = validé pour lancement commercial.
        """
        if not (0.0 <= score <= 10.0):
            return {"error": "Score hors plage (0–10)"}
        with self._lock:
            req = self._requests.get(request_id)
            if req is None:
                return {"error": "Demande non trouvée", "request_id": request_id}
            if req.status != TesterStatus.DELIVERED:
                return {"error": f"Assessment requis après livraison — statut actuel: {req.status.value}"}
            req.assessment_score = score
            req.assessment_feedback = feedback
            ok = req.transition(TesterStatus.ASSESSED.value, f"Score: {score}/10")
            if not ok:
                return {"error": "Transition assessment impossible"}
            passed = score >= 7.0
            action = (
                "APPROUVÉ — lancement commercial possible"
                if passed else
                "REJETÉ — retour fournisseur, corrections requises"
            )
            log.info(f"[TESTER] Assessment {request_id}: {score}/10 → {action[:30]}")
            return {
                "request_id": request_id,
                "project_id": req.project_id,
                "score": score,
                "passed": passed,
                "action": action,
                "feedback": feedback,
                "product_type": req.product_type,
            }

    # ── Stats & reporting ──────────────────────────────────────────────────

    def get_all_requests(self) -> Dict:
        """Retourne toutes les demandes testeur, toutes projets confondues."""
        with self._lock:
            reqs = list(self._requests.values())
        by_status: Dict[str, int] = {}
        by_project: Dict[str, int] = {}
        for r in reqs:
            by_status[r.status.value]    = by_status.get(r.status.value, 0) + 1
            by_project[r.project_id]     = by_project.get(r.project_id, 0) + 1
        assessed = [r for r in reqs if r.status == TesterStatus.ASSESSED]
        avg_score = (sum(r.assessment_score for r in assessed if r.assessment_score)
                     / len(assessed)) if assessed else 0.0
        return {
            "total_requests": len(reqs),
            "by_status": by_status,
            "by_project": by_project,
            "assessed_count": len(assessed),
            "avg_assessment_score": round(avg_score, 2),
            "requests": [
                {"id": r.id, "project_id": r.project_id, "product_type": r.product_type,
                 "quantity": r.quantity, "status": r.status.value,
                 "supplier": r.supplier, "tracking_ref": r.tracking_ref,
                 "assessment_score": r.assessment_score}
                for r in reqs
            ],
        }

    def get_project_requests(self, project_id: str) -> Dict:
        """Retourne toutes les demandes testeur pour un projet donné."""
        with self._lock:
            reqs = [r for r in self._requests.values() if r.project_id == project_id]
        return {
            "project_id": project_id,
            "total": len(reqs),
            "requests": [
                {"id": r.id, "quantity": r.quantity, "status": r.status.value,
                 "supplier": r.supplier, "score": r.assessment_score,
                 "specs": r.specs_summary}
                for r in reqs
            ],
        }

    def get_pending_testers(self) -> List[Dict]:
        """Retourne toutes les demandes non encore livrées/évaluées."""
        with self._lock:
            pending_statuses = {
                TesterStatus.REQUESTED,
                TesterStatus.NEGOTIATING,
                TesterStatus.CONFIRMED,
                TesterStatus.PRODUCING,
                TesterStatus.SHIPPED,
                TesterStatus.IN_TRANSIT,
            }
            return [
                {"id": r.id, "project_id": r.project_id, "status": r.status.value,
                 "product_type": r.product_type, "quantity": r.quantity}
                for r in self._requests.values()
                if r.status in pending_statuses
            ]

    def is_physical_project(self, project_id: str) -> bool:
        """Vérifie si un projet est physique (tester obligatoire)."""
        with self._lock:
            proj = self._projects.get(project_id)
            return proj is not None and proj.is_physical

    def enforce_tester_rule(self, project_id: str) -> Dict:
        """
        Vérifie que la règle testeur est respectée pour un projet physique.
        Si aucune demande n'existe → en crée une automatiquement.
        """
        with self._lock:
            if not self.is_physical_project(project_id):
                return {"enforced": False, "reason": "Projet non physique — règle non applicable"}
            existing = [r for r in self._requests.values() if r.project_id == project_id]
            if existing:
                return {"enforced": True, "existing_count": len(existing),
                        "project_id": project_id, "action": "already_requested"}
        result = self.request_tester(project_id,
                                     notes="Auto-créé par enforce_tester_rule()")
        result["enforced"] = True
        result["action"] = "auto_created"
        log.info(f"[TESTER] Règle testeur appliquée automatiquement: {project_id}")
        return result
