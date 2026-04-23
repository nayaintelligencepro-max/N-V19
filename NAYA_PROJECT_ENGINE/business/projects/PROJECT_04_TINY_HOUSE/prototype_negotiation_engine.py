"""
NAYA V19 — Prototype Negotiation Engine — PROJECT_04_TINY_HOUSE
================================================================
Gère la négociation des 2 premiers modules prototypes en tant que
validation qualité fournisseur (framing discret).

Contexte réel : 2 unités de validation personnelle (20 m²,
énergie renouvelable, programme complet) commandées à l'usine
sous couvert de "qualification prototype avant lancement marché".

Module ALPHA — Single level (plain):
  · Chambre parentale climatisée + WC/douche ensuite
  · Chambre enfant climatisée
  · WC/douche commun
  · Salon ouvert sur cuisine climatisé
  · Buanderie compacte
  · Énergie renouvelable (solaire + batterie)
  · Surface : 20 m²

Module BETA — Légère mezzanine (+1 niveau partiel):
  · Même programme que ALPHA
  · Chambre parentale en mezzanine (optimisation verticale)
  · Salon/cuisine niveau bas, espaces nuit niveau haut
  · Surface sol : 20 m² + mezzanine ≈ 8 m²

Discrétion : "qualification fournisseur / test produit marché"
Plancher prix : 1 000 EUR (unité de test — non applicable au plafond)
"""
import time
import uuid
import logging
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

log = logging.getLogger("NAYA.PROTO.P04")

MIN_UNIT_EUR: float = 1000.0


class ModuleVariant(Enum):
    ALPHA = "ALPHA"   # Single level, 20 m²
    BETA  = "BETA"    # Légère mezzanine, 20 m² + ~8 m² mezzanine


class NegotiationStatus(Enum):
    DRAFT               = "draft"
    RFQ_SENT            = "rfq_sent"
    SAMPLES_REQUESTED   = "samples_requested"
    PROTOTYPE_CONFIRMED = "prototype_confirmed"
    LOGISTICS_AGREED    = "logistics_agreed"
    IN_PRODUCTION       = "in_production"
    SHIPPED             = "shipped"
    RECEIVED            = "received"
    ASSESSED            = "assessed"


MODULE_SPECS: Dict[str, Dict] = {
    ModuleVariant.ALPHA.value: {
        "label": "Module ALPHA — Single Level",
        "surface_m2": 20,
        "layout": "plain",
        "description": (
            "20 m² plain — Chambre parentale (AC + WC/douche ensuite), "
            "chambre enfant (AC), WC/douche commun, salon ouvert cuisine (AC), "
            "buanderie compacte. Énergie renouvelable : panneaux solaires 1,5 kWc + batterie 5 kWh."
        ),
        "rooms": {
            "master_bedroom": {"ac": True, "ensuite_wc": True, "ensuite_shower": True},
            "child_bedroom":  {"ac": True},
            "common_wc":      {"wc": True, "shower": True},
            "living_kitchen": {"ac": True, "open_plan": True},
            "laundry":        {"compact": True},
        },
        "energy": {"solar_kwc": 1.5, "battery_kwh": 5.0, "off_grid_ready": True},
        "mezzanine": False,
        "external_framing": "Prototype validation — layout A (horizontal)",
        "target_price_eur": 18000,
    },
    ModuleVariant.BETA.value: {
        "label": "Module BETA — Légère Mezzanine",
        "surface_m2": 20,
        "mezzanine_m2": 8,
        "layout": "mezzanine",
        "description": (
            "20 m² sol + ~8 m² mezzanine — Chambre parentale (AC + WC/douche ensuite) "
            "en mezzanine, chambre enfant (AC) niveau bas, WC/douche commun, "
            "salon ouvert cuisine (AC) niveau bas, buanderie compacte. "
            "Énergie renouvelable : panneaux solaires 1,5 kWc + batterie 5 kWh."
        ),
        "rooms": {
            "master_bedroom": {"ac": True, "ensuite_wc": True, "ensuite_shower": True, "level": "mezzanine"},
            "child_bedroom":  {"ac": True, "level": "ground"},
            "common_wc":      {"wc": True, "shower": True, "level": "ground"},
            "living_kitchen": {"ac": True, "open_plan": True, "level": "ground"},
            "laundry":        {"compact": True, "level": "ground"},
        },
        "energy": {"solar_kwc": 1.5, "battery_kwh": 5.0, "off_grid_ready": True},
        "mezzanine": True,
        "external_framing": "Prototype validation — layout B (vertical optimization)",
        "target_price_eur": 20000,
    },
}

QUALIFICATION_CRITERIA: List[str] = [
    "Résistance aux vents cycloniques (normes Polynésie / DOM-TOM)",
    "Isolation thermique tropicale (R ≥ 3.0)",
    "Imperméabilité toiture (IPX6 minimum)",
    "Qualité clim intégrée (COP ≥ 3.5, marque certifiée)",
    "Panneaux solaires certifiés IEC 61215",
    "Délai livraison confirmé avant engagement commercial",
    "Documentation montage en FR/EN",
    "Service après-vente accessible hors métropole",
]

TARGET_FACTORIES: List[Dict] = [
    {"name": "Factory_A_CN", "country": "Chine",    "region": "Guangdong", "moq": 1, "lead_time_days": 60},
    {"name": "Factory_B_VN", "country": "Vietnam",  "region": "Binh Duong","moq": 1, "lead_time_days": 45},
    {"name": "Factory_C_MY", "country": "Malaisie", "region": "Selangor",  "moq": 2, "lead_time_days": 55},
    {"name": "Factory_D_FR", "country": "France",   "region": "Bretagne",  "moq": 1, "lead_time_days": 90},
]


@dataclass
class PrototypeUnit:
    """Représente une unité prototype en cours de négociation."""
    id: str = field(default_factory=lambda: f"PROTO-{uuid.uuid4().hex[:8].upper()}")
    variant: ModuleVariant = ModuleVariant.ALPHA
    status: NegotiationStatus = NegotiationStatus.DRAFT
    factory_id: Optional[str] = None
    negotiated_price_eur: float = 0.0
    logistics_cost_eur: float = 0.0
    total_cost_eur: float = 0.0
    estimated_delivery_days: int = 0
    assessment_score: float = 0.0
    assessment_notes: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    history: List[Dict] = field(default_factory=list)

    def advance(self, new_status: NegotiationStatus, notes: str = "") -> None:
        self.history.append({
            "from": self.status.value,
            "to": new_status.value,
            "ts": time.time(),
            "notes": notes,
        })
        self.status = new_status
        self.updated_at = time.time()


@dataclass
class PrototypeNegotiationSession:
    """Session de négociation des 2 modules prototypes."""
    id: str = field(default_factory=lambda: f"SESS-{uuid.uuid4().hex[:6].upper()}")
    units: Dict[str, PrototypeUnit] = field(default_factory=dict)
    framing: str = "Qualification fournisseur — validation prototype avant lancement marché"
    owner_ref: str = "INTERNAL_QA_PARTNER_01"  # Réf discrète propriétaire
    created_at: float = field(default_factory=time.time)


class PrototypeNegotiationEngine:
    """
    Moteur de négociation des 2 modules prototypes TINY_HOUSE.

    Toute communication externe utilise le framing :
    'Qualification fournisseur / validation prototype'.
    Les unités sont destinées à la validation personnelle propriétaire (discret).

    Interface publique :
        init_session()     → crée les 2 unités (ALPHA + BETA)
        advance_unit(id, status, notes) → fait avancer la négociation
        set_factory(unit_id, factory_id) → assigne un fabricant
        set_pricing(unit_id, price, logistics) → enregistre tarifs négociés
        assess_unit(unit_id, score, notes) → évalue l'unité reçue
        get_rfq_brief(unit_id) → génère le brief RFQ pour l'usine (framing discret)
        get_session_status() → état complet des 2 unités
        get_qualification_checklist() → critères d'évaluation qualité
    """

    PROJECT_ID = "PROJECT_04_TINY_HOUSE"
    FLOOR_EUR   = MIN_UNIT_EUR
    NB_PROTOTYPES = 2

    def __init__(self) -> None:
        self._lock    = threading.RLock()
        self._session: Optional[PrototypeNegotiationSession] = None
        self._initialized_at = time.time()
        log.info(f"[{self.PROJECT_ID}] PrototypeNegotiationEngine prêt")

    # ── Session ────────────────────────────────────────────────────────────

    def init_session(self) -> Dict:
        """Initialise la session avec 2 unités (ALPHA + BETA)."""
        with self._lock:
            if self._session is not None:
                return {"status": "already_initialized", "session_id": self._session.id}

            self._session = PrototypeNegotiationSession()
            for variant in (ModuleVariant.ALPHA, ModuleVariant.BETA):
                unit = PrototypeUnit(variant=variant)
                self._session.units[unit.id] = unit
                log.info(f"[PROTO] Unité créée: {unit.id} | {variant.value}")

        return {
            "session_id": self._session.id,
            "framing": self._session.framing,
            "units": {uid: u.variant.value for uid, u in self._session.units.items()},
            "status": "initialized",
        }

    # ── Négociation ────────────────────────────────────────────────────────

    def advance_unit(self, unit_id: str, new_status: str, notes: str = "") -> Dict:
        """Fait avancer le statut de négociation d'une unité."""
        with self._lock:
            unit, err = self._get_unit(unit_id)
            if err:
                return err
            try:
                status_enum = NegotiationStatus(new_status)
            except ValueError:
                valid = [s.value for s in NegotiationStatus]
                return {"error": f"Statut inconnu: {new_status}", "valid_values": valid}
            unit.advance(status_enum, notes)
            log.info(f"[PROTO] {unit_id} → {new_status}")
            return {"unit_id": unit_id, "variant": unit.variant.value,
                    "new_status": unit.status.value, "notes": notes}

    def set_factory(self, unit_id: str, factory_id: str) -> Dict:
        """Assigne un fabricant cible à une unité."""
        with self._lock:
            unit, err = self._get_unit(unit_id)
            if err:
                return err
            unit.factory_id = factory_id
            unit.updated_at = time.time()
            log.info(f"[PROTO] {unit_id} → factory: {factory_id}")
            return {"unit_id": unit_id, "factory_id": factory_id,
                    "variant": unit.variant.value, "status": unit.status.value}

    def set_pricing(self, unit_id: str, unit_price_eur: float,
                    logistics_eur: float = 0.0) -> Dict:
        """Enregistre le prix unitaire négocié + coût logistique."""
        if unit_price_eur < self.FLOOR_EUR:
            return {"error": f"Prix {unit_price_eur} EUR < plancher {self.FLOOR_EUR} EUR"}
        with self._lock:
            unit, err = self._get_unit(unit_id)
            if err:
                return err
            unit.negotiated_price_eur = unit_price_eur
            unit.logistics_cost_eur   = logistics_eur
            unit.total_cost_eur       = unit_price_eur + logistics_eur
            unit.updated_at           = time.time()
            spec = MODULE_SPECS[unit.variant.value]
            vs_target = round((unit_price_eur / spec["target_price_eur"] - 1) * 100, 1)
            log.info(f"[PROTO] {unit_id} pricing: {unit_price_eur:.0f} EUR "
                     f"({'+'if vs_target>=0 else ''}{vs_target}% vs target)")
            return {"unit_id": unit_id, "negotiated_price_eur": unit_price_eur,
                    "logistics_eur": logistics_eur, "total_cost_eur": unit.total_cost_eur,
                    "vs_target_pct": vs_target}

    def set_delivery_time(self, unit_id: str, days: int) -> Dict:
        """Enregistre le délai de livraison négocié."""
        with self._lock:
            unit, err = self._get_unit(unit_id)
            if err:
                return err
            unit.estimated_delivery_days = days
            unit.updated_at = time.time()
            return {"unit_id": unit_id, "estimated_delivery_days": days}

    # ── Assessment ─────────────────────────────────────────────────────────

    def assess_unit(self, unit_id: str, score: float, notes: str = "") -> Dict:
        """Évalue l'unité reçue (0–10) et génère rapport d'assessment."""
        if not (0.0 <= score <= 10.0):
            return {"error": "Score doit être entre 0 et 10"}
        with self._lock:
            unit, err = self._get_unit(unit_id)
            if err:
                return err
            unit.assessment_score = score
            unit.assessment_notes = notes
            unit.advance(NegotiationStatus.ASSESSED, f"Score: {score}/10 — {notes}")
            passed = score >= 7.0
            recommendation = (
                "VALIDÉ — peut servir de référence commercial et usage personnel"
                if passed else
                "REFUSÉ — retour usine, corrections requises avant lancement"
            )
            log.info(f"[PROTO] Assessment {unit_id}: {score}/10 → {recommendation[:30]}")
            return {"unit_id": unit_id, "variant": unit.variant.value,
                    "assessment_score": score, "passed": passed,
                    "recommendation": recommendation, "notes": notes,
                    "qualification_criteria": QUALIFICATION_CRITERIA}

    # ── Génération documents ───────────────────────────────────────────────

    def get_rfq_brief(self, unit_id: str) -> Dict:
        """
        Génère le brief RFQ (Request for Quotation) pour l'usine.
        Framing : qualification fournisseur, prototype validation.
        Le destinataire externe voit une demande commerciale standard.
        """
        with self._lock:
            unit, err = self._get_unit(unit_id)
            if err:
                return err
            spec = MODULE_SPECS[unit.variant.value]

        rooms_desc = ", ".join(
            f"{rm.replace('_', ' ')} ({'AC ' if v.get('ac') else ''}"
            f"{'ensuite WC/douche ' if v.get('ensuite_wc') else ''}"
            f"{'mezzanine' if v.get('level') == 'mezzanine' else ''})"
            for rm, v in spec["rooms"].items()
        )

        return {
            "rfq_id": f"RFQ-{unit_id}",
            "external_framing": spec["external_framing"],
            "purpose": (
                "Qualification fournisseur — 1 unité prototype pour validation "
                "avant commande série. Évaluation qualité, conformité specs, "
                "délai livraison et service après-vente."
            ),
            "module_variant": unit.variant.value,
            "specifications": {
                "surface_m2": spec["surface_m2"],
                "mezzanine":  spec.get("mezzanine_m2", 0),
                "rooms": rooms_desc,
                "energy_system": (
                    f"Solaire {spec['energy']['solar_kwc']} kWc + "
                    f"batterie {spec['energy']['battery_kwh']} kWh, off-grid ready"
                ),
                "climate_control": "Climatisation dans toutes pièces de vie (COP ≥ 3.5)",
                "certifications": "IEC 61215 (solaire), conformité vents cycloniques",
            },
            "delivery": {
                "destination": "Polynésie française (départ usine + livraison destination finale)",
                "packaging": "Conteneur 20' ou 40' selon variante",
                "assembly_docs": "Manuel montage FR/EN inclus obligatoire",
            },
            "quantity": 1,
            "target_price_eur": spec["target_price_eur"],
            "evaluation_criteria": QUALIFICATION_CRITERIA,
            "target_factories": TARGET_FACTORIES,
            "contact_framing": "Partenaire qualification interne NAYA",
        }

    # ── Status & stats ─────────────────────────────────────────────────────

    def get_session_status(self) -> Dict:
        """Retourne l'état complet des 2 unités en négociation."""
        with self._lock:
            if self._session is None:
                return {"status": "not_initialized", "hint": "Appeler init_session() d'abord"}
            units_out = []
            for uid, unit in self._session.units.items():
                spec = MODULE_SPECS[unit.variant.value]
                units_out.append({
                    "unit_id": uid,
                    "variant": unit.variant.value,
                    "label": spec["label"],
                    "surface_m2": spec["surface_m2"],
                    "status": unit.status.value,
                    "factory": unit.factory_id,
                    "negotiated_price_eur": unit.negotiated_price_eur,
                    "logistics_cost_eur": unit.logistics_cost_eur,
                    "total_cost_eur": unit.total_cost_eur,
                    "delivery_days": unit.estimated_delivery_days,
                    "assessment_score": unit.assessment_score,
                    "history_steps": len(unit.history),
                })
            total_cost = sum(u.total_cost_eur for u in self._session.units.values())
            all_assessed = all(
                u.status == NegotiationStatus.ASSESSED
                for u in self._session.units.values()
            )
            return {
                "session_id": self._session.id,
                "framing": self._session.framing,
                "nb_units": len(units_out),
                "total_cost_eur": total_cost,
                "units": units_out,
                "all_assessed": all_assessed,
                "uptime_seconds": int(time.time() - self._initialized_at),
            }

    def get_qualification_checklist(self) -> List[str]:
        """Retourne la checklist de qualification qualité."""
        return list(QUALIFICATION_CRITERIA)

    def get_module_specs(self, variant: str) -> Dict:
        """Retourne les specs complètes d'une variante."""
        if variant not in MODULE_SPECS:
            return {"error": f"Variante inconnue: {variant}", "valid": list(MODULE_SPECS.keys())}
        return MODULE_SPECS[variant]

    # ── Interne ────────────────────────────────────────────────────────────

    def _get_unit(self, unit_id: str):
        """Retourne (unit, None) ou (None, error_dict)."""
        if self._session is None:
            return None, {"error": "Session non initialisée", "hint": "init_session()"}
        unit = self._session.units.get(unit_id)
        if unit is None:
            return None, {"error": "Unité non trouvée", "unit_id": unit_id,
                          "valid_ids": list(self._session.units.keys())}
        return unit, None
