"""
NAYA — CASH ENGINE REAL V8
════════════════════════════════════════════════════════════════════════════════
Le seul module qui génère vraiment de l'argent.

Doctrine: L'argent se génère par 3 mécanismes précis:
  1. DÉTECTION → offre irréfutable → conversion client réel
  2. NURTURING → pipeline chaud → closing 30-60j
  3. RÉCURRENCE → client existant → upsell/cross-sell

Ce module orchestre les 3 mécanismes en continu.
Chaque cycle = argent potentiel RÉEL tracé jusqu'au closing.
════════════════════════════════════════════════════════════════════════════════
"""
import time, uuid, logging, json, os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta, timezone
from pathlib import Path

log = logging.getLogger("NAYA.CASH_REAL")

def _gs(key: str, default: str = "") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(key, default) or default
    except Exception:
        return __import__('os').environ.get(key, default)


ROOT = Path(__file__).resolve().parent.parent
PIPELINE_FILE = ROOT / "data" / "cache" / "cash_pipeline.json"
PIPELINE_FILE.parent.mkdir(parents=True, exist_ok=True)


# ── STATUTS PIPELINE ─────────────────────────────────────────────────────────

class DealStage(Enum):
    DETECTED     = "detected"       # Douleur détectée — offre construite
    QUALIFIED    = "qualified"       # Douleur confirmée + solvabilité OK
    CONTACTED    = "contacted"       # Premier contact envoyé
    DEMO_BOOKED  = "demo_booked"    # RDV/appel planifié
    PROPOSAL_SENT= "proposal_sent"  # Offre formelle envoyée
    NEGOTIATING  = "negotiating"    # En discussion prix/conditions
    WON          = "won"            # SIGNÉ — argent réel
    LOST         = "lost"           # Refus → ZeroWaste actif
    NURTURING    = "nurturing"      # Trop tôt — on maintient le lien 30-60j

class ContactChannel(Enum):
    LINKEDIN_DM   = "linkedin_dm"
    COLD_EMAIL    = "cold_email"
    WARM_INTRO    = "warm_intro"     # Via réseau — taux de conv. 3x supérieur
    TELEGRAM_BOT  = "telegram_bot"
    PHONE_OUTBOUND= "phone_outbound"
    CONTENT_INBOUND = "content_inbound"  # Inbound via LinkedIn post NAYA


@dataclass
class Deal:
    """Un deal dans le pipeline — de la détection au paiement."""
    id: str = field(default_factory=lambda: f"DEAL_{uuid.uuid4().hex[:8].upper()}")
    sector: str = ""
    company_profile: str = ""       # Description cible
    pain_category: str = ""
    pain_annual_cost: float = 0.0
    offer_price: float = 0.0
    offer_title: str = ""
    offer_proof: str = ""
    offer_guarantee: str = ""
    irrefutable_logic: str = ""

    stage: DealStage = DealStage.DETECTED
    channel: Optional[ContactChannel] = None

    # Tracking
    created_at: float = field(default_factory=time.time)
    last_action_at: float = field(default_factory=time.time)
    next_action_at: float = 0.0
    next_action: str = ""
    contact_attempts: int = 0
    messages_sent: List[str] = field(default_factory=list)

    # Content généré
    linkedin_post: str = ""
    cold_email_subject: str = ""
    cold_email_body: str = ""
    pitch_script: str = ""
    follow_up_sequence: List[str] = field(default_factory=list)

    # Résultat
    won_at: Optional[float] = None
    revenue_collected: float = 0.0
    loss_reason: str = ""
    notes: str = ""

    @property
    def days_in_pipeline(self) -> int:
        return int((time.time() - self.created_at) / 86400)

    @property
    def roi_ratio(self) -> float:
        return round(self.pain_annual_cost / max(self.offer_price, 1), 1)

    def to_dict(self) -> Dict:
        return {
            "id": self.id, "sector": self.sector,
            "company": self.company_profile,
            "pain": self.pain_category,
            "pain_annual_cost": self.pain_annual_cost,
            "price": self.offer_price, "title": self.offer_title,
            "stage": self.stage.value, "channel": self.channel.value if self.channel else None,
            "days_pipeline": self.days_in_pipeline,
            "roi": self.roi_ratio,
            "next_action": self.next_action,
            "contact_attempts": self.contact_attempts,
            "won_at": self.won_at, "revenue": self.revenue_collected,
            "ts": datetime.fromtimestamp(self.created_at, timezone.utc).isoformat(),
        }


class CashEngineReal:
    """
    Moteur de génération d'argent réel.
    Pipeline complet: détection → contenu → contact → closing → paiement.
    """

    # Taux de conversion par étape (données empiriques B2B)
    CONVERSION_RATES = {
        DealStage.DETECTED:      0.40,   # 40% passent en qualified
        DealStage.QUALIFIED:     0.35,   # 35% contacted
        DealStage.CONTACTED:     0.25,   # 25% demo
        DealStage.DEMO_BOOKED:   0.55,   # 55% proposal
        DealStage.PROPOSAL_SENT: 0.30,   # 30% closing
        DealStage.NEGOTIATING:   0.70,   # 70% won
    }

    # Durée médiane par étape (jours)
    STAGE_DURATION = {
        DealStage.DETECTED:      0,
        DealStage.QUALIFIED:     1,
        DealStage.CONTACTED:     3,
        DealStage.DEMO_BOOKED:   5,
        DealStage.PROPOSAL_SENT: 7,
        DealStage.NEGOTIATING:   10,
    }

    def __init__(self):
        self._deals: Dict[str, Deal] = {}
        self._won_total: float = 0.0
        self._won_count: int = 0
        self._load_pipeline()
        log.info(f"[CASH REAL] Pipeline chargé: {len(self._deals)} deals actifs")

    def _load_pipeline(self):
        """Charge le pipeline depuis le disque."""
        try:
            if PIPELINE_FILE.exists():
                data = json.loads(PIPELINE_FILE.read_text())
                for d in data.get("deals", []):
                    deal = Deal(
                        id=d["id"], sector=d.get("sector",""),
                        company_profile=d.get("company",""),
                        pain_category=d.get("pain",""),
                        pain_annual_cost=d.get("pain_annual_cost",0),
                        offer_price=d.get("price",0),
                        offer_title=d.get("title",""),
                        stage=DealStage(d.get("stage","detected")),
                        contact_attempts=d.get("contact_attempts",0),
                        notes=d.get("notes",""),
                        won_at=d.get("won_at"),
                        revenue_collected=d.get("revenue",0),
                    )
                    self._deals[deal.id] = deal
                self._won_total = data.get("won_total", 0)
                self._won_count = data.get("won_count", 0)
        except Exception as e:
            log.debug(f"[CASH REAL] Load pipeline: {e}")

    def _save_pipeline(self):
        """Persiste le pipeline sur disque."""
        try:
            data = {
                "deals": [d.to_dict() for d in self._deals.values()],
                "won_total": self._won_total,
                "won_count": self._won_count,
                "saved_at": datetime.now(timezone.utc).isoformat(),
            }
            PIPELINE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        except Exception as e:
            log.debug(f"[CASH REAL] Save pipeline: {e}")

    def inject_from_hunt(self, hunt_result: Dict, sector: str) -> Optional[Deal]:
        """
        Injecte un résultat de chasse dans le pipeline.
        C'est ici que la détection devient argent potentiel.
        """
        if not hunt_result.get("qualified") or not hunt_result.get("offer"):
            return None

        offer = hunt_result["offer"]
        pain = hunt_result.get("top_pain", {})
        price = float(offer.get("price", 0))

        if price < 1000:  # Plancher absolu
            return None

        deal = Deal(
            sector=sector,
            company_profile=f"PME {sector} — CA ~{int(float(pain.get('annual_cost_eur', 100000))/pain.get('cost_ratio',0.1) if pain.get('cost_ratio') else 300000):,}€",
            pain_category=pain.get("category", sector),
            pain_annual_cost=float(pain.get("annual_cost_eur", 0)),
            offer_price=price,
            offer_title=offer.get("title", f"Solution {sector}"),
            offer_proof=offer.get("proof", ""),
            offer_guarantee=offer.get("guarantee", "Résultat ou remboursement"),
            irrefutable_logic=offer.get("irrefutable_logic", ""),
            stage=DealStage.DETECTED,
            next_action_at=time.time() + 300,  # Dans 5 minutes
            next_action="Générer contenu + préparer outreach",
        )

        # Générer la séquence de follow-up automatique
        deal.follow_up_sequence = self._build_followup_sequence(deal)

        self._deals[deal.id] = deal
        self._save_pipeline()

        log.info(f"[CASH REAL] 💎 Deal créé: {deal.id} | {deal.pain_category} | {deal.offer_price:,.0f}€ | ROI×{deal.roi_ratio}")
        return deal

    def _build_followup_sequence(self, deal: Deal) -> List[str]:
        """Séquence de follow-up sur 30 jours — basée sur la psychologie de la décision."""
        price = deal.offer_price
        pain = deal.pain_category
        annual = deal.pain_annual_cost

        return [
            f"J+0: LinkedIn post sur {pain} dans {deal.sector} — attirer l'inbound",
            f"J+1: Cold email sujet: 'Question rapide — {pain} chez [Entreprise]' — personnalisé",
            f"J+3: DM LinkedIn si pas de réponse — court, direct, preuve",
            f"J+5: Relance email avec preuve supplémentaire — cas client similaire",
            f"J+7: Valeur gratuite — envoyer mini-analyse sectorielle personnalisée",
            f"J+10: Appel de 5 min — 'J'ai une observation sur votre situation'",
            f"J+14: Email 'break-up' — crée l'urgence sans pression",
            f"J+20: Relance si intérêt via inbound ou engagement LinkedIn",
            f"J+30: Nurturing long terme — newsletter valeur toutes les 3 semaines",
        ]

    def advance_deals(self) -> List[Dict]:
        """
        Fait avancer les deals dans le pipeline.
        En mode autonome: génère les contenus et prépare les actions.
        """
        actions_taken = []
        now = time.time()

        for deal_id, deal in list(self._deals.items()):
            if deal.stage in (DealStage.WON, DealStage.LOST):
                continue
            if deal.next_action_at > now:
                continue

            action = self._advance_deal(deal)
            if action:
                actions_taken.append(action)
                deal.last_action_at = now

        if actions_taken:
            self._save_pipeline()

        return actions_taken

    def _advance_deal(self, deal: Deal) -> Optional[Dict]:
        """Avance un deal d'une étape."""
        stage = deal.stage

        if stage == DealStage.DETECTED:
            # Qualifier automatiquement si ROI > 3
            if deal.roi_ratio >= 3.0 and deal.offer_price >= 1000:
                deal.stage = DealStage.QUALIFIED
                deal.next_action = "Préparer outreach personnalisé"
                deal.next_action_at = time.time() + 600
                return {"deal_id": deal.id, "action": "qualified", "price": deal.offer_price}

        elif stage == DealStage.QUALIFIED:
            # Générer le contenu d'outreach
            content = self._generate_outreach_content(deal)
            deal.cold_email_subject = content["email_subject"]
            deal.cold_email_body = content["email_body"]
            deal.linkedin_post = content["linkedin_post"]
            deal.pitch_script = content["pitch_script"]
            deal.stage = DealStage.CONTACTED
            deal.contact_attempts += 1
            deal.messages_sent.append(f"Email J+0: {content['email_subject']}")
            deal.next_action = f"Follow-up J+3: {deal.follow_up_sequence[2] if len(deal.follow_up_sequence) > 2 else 'DM LinkedIn'}"
            deal.next_action_at = time.time() + 3 * 86400  # 3 jours
            return {
                "deal_id": deal.id, "action": "outreach_ready",
                "email_subject": content["email_subject"],
                "linkedin_post": deal.linkedin_post[:100] + "...",
                "price": deal.offer_price
            }

        elif stage == DealStage.CONTACTED and deal.days_in_pipeline > 14:
            # Trop long sans réponse → nurturing
            if deal.contact_attempts >= 3:
                deal.stage = DealStage.NURTURING
                deal.next_action = "Nurturing: valeur mensuelle pendant 60j"
                deal.next_action_at = time.time() + 21 * 86400
                return {"deal_id": deal.id, "action": "moved_to_nurturing"}

        return None

    def _generate_outreach_content(self, deal: Deal) -> Dict:
        """Génère le contenu d'outreach personnalisé pour chaque deal."""
        pain = deal.pain_category.replace("_", " ")
        sector = deal.sector.replace("_", " ")
        price = deal.offer_price
        annual = deal.pain_annual_cost
        roi = deal.roi_ratio

        return {
            "email_subject": f"Question rapide — {pain} dans votre secteur",
            "email_body": (
                f"Bonjour,\n\n"
                f"J'analyse régulièrement les entreprises du secteur {sector}. "
                f"J'ai identifié un pattern récurrent: {pain.replace('_', ' ')} "
                f"coûte en moyenne {annual:,.0f}€/an aux PME de votre profil — "
                f"sans qu'elles s'en rendent compte.\n\n"
                f"Nous venons de résoudre exactement ça pour 3 entreprises similaires. "
                f"Résultat moyen: ROI ×{roi} dès la première année.\n\n"
                f"15 minutes pour voir si c'est pertinent dans votre cas ?\n\n"
                f"Bien à vous,"
            ),
            "linkedin_post": (
                f"3 dirigeants cette semaine m'ont parlé du même problème: {pain.replace('_', ' ')}.\n\n"
                f"Ce que la plupart ne savent pas: ça leur coûte {annual:,.0f}€/an en moyenne.\n\n"
                f"La solution? {deal.offer_title}\n\n"
                f"ROI ×{roi} démontré. {deal.offer_proof}\n\n"
                f"Si vous êtes dans ce cas, envoyez-moi un message. "
                f"Je vous montre les chiffres en 20 minutes."
            ),
            "pitch_script": (
                f"'Vous avez {pain.replace('_', ' ')}? Voilà ce que ça vous coûte: {annual:,.0f}€/an. "
                f"Ce qu'on fait: {deal.offer_title}. "
                f"En {deal.offer_price:,.0f}€ vous récupérez {annual-price:,.0f}€ dès la première année. "
                f"ROI ×{roi}. {deal.offer_guarantee}. "
                f"Vous avez 20 minutes cette semaine?'"
            ),
        }

    def mark_won(self, deal_id: str, revenue: float = None) -> bool:
        """Marque un deal comme gagné — argent réel encaissé."""
        deal = self._deals.get(deal_id)
        if not deal:
            return False
        deal.stage = DealStage.WON
        deal.won_at = time.time()
        deal.revenue_collected = revenue or deal.offer_price
        self._won_total += deal.revenue_collected
        self._won_count += 1
        self._save_pipeline()
        log.info(f"[CASH REAL] 🎉 WON: {deal_id} — {deal.revenue_collected:,.0f}€ — Total: {self._won_total:,.0f}€")
        return True

    def mark_lost(self, deal_id: str, reason: str = "unknown") -> bool:
        """Marque un deal comme perdu — ZeroWaste prend le relais."""
        deal = self._deals.get(deal_id)
        if not deal:
            return False
        deal.stage = DealStage.LOST
        deal.loss_reason = reason
        self._save_pipeline()
        return True

    def get_pipeline_summary(self) -> Dict:
        """Vue d'ensemble du pipeline."""
        active = [d for d in self._deals.values() if d.stage not in (DealStage.WON, DealStage.LOST)]
        won = [d for d in self._deals.values() if d.stage == DealStage.WON]

        total_pipe_value = sum(d.offer_price for d in active)
        weighted_pipe = sum(
            d.offer_price * self.CONVERSION_RATES.get(d.stage, 0.2)
            for d in active
        )

        by_stage = {}
        for stage in DealStage:
            count = sum(1 for d in active if d.stage == stage)
            if count > 0:
                by_stage[stage.value] = count

        return {
            "active_deals": len(active),
            "pipeline_total_eur": round(total_pipe_value),
            "pipeline_weighted_eur": round(weighted_pipe),  # Valeur pondérée par taux de conv.
            "won_total_eur": round(self._won_total),
            "won_count": self._won_count,
            "by_stage": by_stage,
            "next_actions": [
                {"deal_id": d.id, "action": d.next_action, "price": d.offer_price}
                for d in sorted(active, key=lambda x: x.next_action_at)[:5]
            ],
            "top_deals": [d.to_dict() for d in sorted(active, key=lambda x: x.offer_price, reverse=True)[:3]],
        }

    def get_revenue_projection(self, days: int = 90) -> Dict:
        """Projection de revenus sur N jours basée sur le pipeline actuel."""
        active = [d for d in self._deals.values() if d.stage not in (DealStage.WON, DealStage.LOST)]

        projection = {}
        for d in active:
            stage = d.stage
            # Probabilité de conversion cumulée depuis l'étape actuelle
            prob = 1.0
            stages_order = [
                DealStage.DETECTED, DealStage.QUALIFIED, DealStage.CONTACTED,
                DealStage.DEMO_BOOKED, DealStage.PROPOSAL_SENT, DealStage.NEGOTIATING
            ]
            current_idx = stages_order.index(stage) if stage in stages_order else 0
            for s in stages_order[current_idx:]:
                prob *= self.CONVERSION_RATES.get(s, 0.3)

            # Durée restante estimée
            remaining_days = sum(
                self.STAGE_DURATION.get(s, 5)
                for s in stages_order[current_idx:]
            )
            close_day = min(remaining_days, days)

            week = (close_day // 7) + 1
            key = f"week_{week}"
            projection[key] = projection.get(key, 0) + d.offer_price * prob

        return {
            "projection_days": days,
            "by_week": {k: round(v) for k, v in sorted(projection.items())},
            "total_projected": round(sum(projection.values())),
            "confidence": "weighted_probability",
        }


# ── Singleton ──────────────────────────────────────────────────────────────────
_engine: Optional[CashEngineReal] = None
_engine_lock = __import__('threading').Lock()

def get_cash_engine() -> CashEngineReal:
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = CashEngineReal()
    return _engine
