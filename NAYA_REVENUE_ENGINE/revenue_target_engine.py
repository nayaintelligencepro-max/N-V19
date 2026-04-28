"""
NAYA SUPREME V19 — REVENUE TARGET ENGINE
═══════════════════════════════════════════════════════════════
Tracking des objectifs euros M1→M12 avec actions OODA du jour.

OBJECTIFS RÉALISTES OODA (Observe → Orient → Decide → Act):
  M1       →  5 000€   (1 audit express ou 1 formation OT vendue)
  M2       → 15 000€   (pack audit express : 1 deal signé)
  M3       → 25 000€   (2 deals catalogue OT / énergie / transport)
  M4       → 35 000€   (pipeline chaud + premiers récurrents)
  M5       → 45 000€   (partenariats + upsell clients M1-M3)
  M6       → 60 000€   (deals Sécurité Avancée + MRR naissant)
  M7       → 70 000€   (pipeline chaud grands comptes)
  M8       → 80 000€   (MRR scale + contrats annuels)
  M9       → 85 000€   (deals Premium Full + récurrence solide)
  M10      → 90 000€   (upsell masse + références clients)
  M11      → 95 000€   (contrats annuels signés Q4)
  M12      →100 000€   (scale full : 2 consultants + MRR >20k€)

LEVIERS:
  L1 — Formation OT 1 jour        → 5k€ cash 48h   | conv. 40%
  L2 — Audit Express              → 15k€ cash 7j   | conv. 35%
  L3 — Pack Sécurité Avancée      → 40k€ cash 14j  | conv. 22%
  L4 — Pack Premium Full          → 80k€ cash 21j  | conv. 12%
  L5 — Monitoring récurrent       → 2-8k€/mois MRR | conv. 60%
  L6 — Partenariat rev-share      → 8-20k€/deal    | conv. 45%
  L7 — Upsell clients actifs      → +30% deal init | conv. 70%

MÉTHODE OODA appliquée:
  Observe  → Scanner signaux marché chaque 24h (Serper + Apollo)
  Orient   → Qualifier les leads par score (0-100) + urgence pain
  Decide   → Sélectionner levier optimal selon pipeline actuel
  Act      → Outreach personnalisé + closing ciblé sous 72h
═══════════════════════════════════════════════════════════════
"""
import json, time, uuid, logging
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from pathlib import Path
from datetime import date, datetime

log = logging.getLogger("NAYA.REVENUE_TARGETS")
ROOT = Path(__file__).resolve().parent.parent


# ── OBJECTIFS MENSUELS RÉALISTES ─────────────────────────────────────────────
# Basés sur : 1 deal OT = 15k€ minimum, pipeline 7-14j, taux conv 22-35%
# Progression douce M1→M6 puis accélération M7→M12 via récurrence + scale
OBJECTIFS = {
    1:  {"min": 3000,   "target": 5000,   "max": 12000,  "levier": "L1_formation",
         "deals_type": "1 formation OT 5k€ OU 1 audit express 15k€",
         "ooda_focus": "OBSERVE — cartographier 50 prospects OT chauds"},
    2:  {"min": 10000,  "target": 15000,  "max": 25000,  "levier": "L2_audit_express",
         "deals_type": "1 Pack Audit Express 15k€",
         "ooda_focus": "ORIENT — qualifier top 10 prospects M1, pitcher Pack Audit"},
    3:  {"min": 18000,  "target": 25000,  "max": 40000,  "levier": "L2_L3_catalogue",
         "deals_type": "1-2 deals 15-40k€ secteur Énergie/Transport",
         "ooda_focus": "DECIDE — sélectionner 3 deals chauds, closing calls planifiés"},
    4:  {"min": 25000,  "target": 35000,  "max": 50000,  "levier": "L5_recurrence",
         "deals_type": "2 deals + 2 premiers abonnés monitoring 3k€/mois",
         "ooda_focus": "ACT — convertir deals one-shot en contrats récurrents"},
    5:  {"min": 32000,  "target": 45000,  "max": 60000,  "levier": "L6_partenariat",
         "deals_type": "Partenariats Siemens/ABB + upsell clients M1-M3",
         "ooda_focus": "OBSERVE — signer 2 accords partenariat, pipeline partenaires"},
    6:  {"min": 45000,  "target": 60000,  "max": 80000,  "levier": "L3_L4_closing",
         "deals_type": "1 Pack Sécurité Avancée 40k€ + MRR 5k€",
         "ooda_focus": "ORIENT — deals >21j en attente : relance phone + escompte"},
    7:  {"min": 55000,  "target": 70000,  "max": 90000,  "levier": "L4_grands_comptes",
         "deals_type": "Grands comptes CAC40 OT (Airbus, Michelin, EDF)",
         "ooda_focus": "DECIDE — 3 grands comptes qualifiés, proposition Premium Full"},
    8:  {"min": 65000,  "target": 80000,  "max": 100000, "levier": "L5_mrr_scale",
         "deals_type": "MRR 10k€ + 1 deal Premium 80k€",
         "ooda_focus": "ACT — 5 clients monitoring récurrents signés"},
    9:  {"min": 72000,  "target": 85000,  "max": 110000, "levier": "L3_L4_pipeline",
         "deals_type": "Pipeline chaud 2+ deals 40-80k€",
         "ooda_focus": "OBSERVE — analyser taux conv par secteur, ajuster ICP"},
    10: {"min": 80000,  "target": 90000,  "max": 115000, "levier": "L7_upsell_mass",
         "deals_type": "Upsell 100% clients existants + nouveaux",
         "ooda_focus": "ORIENT — chaque client existant = +30% upsell proposé"},
    11: {"min": 88000,  "target": 95000,  "max": 120000, "levier": "contrats_annuels",
         "deals_type": "Contrats annuels 25-60k€ (budgets N+1 novembre)",
         "ooda_focus": "DECIDE — présenter contrats annuels avant clôture budgets"},
    12: {"min": 95000,  "target": 100000, "max": 130000, "levier": "scale_full",
         "deals_type": "2 consultants OT + MRR >20k€ + deals scale",
         "ooda_focus": "ACT — recruter consultant OT junior, doubler capacité delivery"},
}

# ── ACTIONS QUOTIDIENNES PAR LEVIER (OODA intégré) ───────────────────────────
ACTIONS = {
    "L1_formation": [
        "OBSERVE → Scanner LinkedIn : DSI industriels + RSSI + Directeurs Usine actifs",
        "ORIENT  → Identifier 3 contacts ayant mentionné IEC62443/NIS2 dans les 30j",
        "DECIDE  → Appeler directement (pas email) : proposer formation OT 1j à 5k€",
        "ACT     → Créer lien PayPal 5000€, envoyer programme PDF 1 page + lien",
        "METRIC  → 1 formation vendue = M1 atteint à 100% — objectif 48h max",
    ],
    "L2_audit_express": [
        "OBSERVE → Apollo : 20 nouvelles entreprises transport/énergie avec OT exposé",
        "ORIENT  → Score chaque lead : offre emploi RSSI + contrat récent + NIS2 =  score 80+",
        "DECIDE  → Envoyer pitch Pack Audit Express 15k€ aux top 5 leads scorés",
        "ACT     → Follow-up J+2 phone sur tous les pitchs envoyés > J-2",
        "METRIC  → 1 deal signé = 15k€ = objectif M2 quasi-atteint",
    ],
    "L2_L3_catalogue": [
        "OBSERVE → Générer batch 10 offres catalogue OT (secteur Énergie prioritaire)",
        "ORIENT  → Cibler OIV énergie/transport : pitch Pack Sécurité Avancée 40k€ + urgence NIS2",
        "DECIDE  → LinkedIn : 10 messages RSSI/DSI industrie par jour, personnalisés",
        "ACT     → Proposer appel découverte 20 min à tout contact qui répond",
        "METRIC  → 1 deal 15k + 1 deal 40k = 55k = objectif M3 dépassé",
    ],
    "L5_recurrence": [
        "OBSERVE → Lister 100% des clients one-shot signés M1-M3",
        "ORIENT  → Calculer ROI client sur audit livré, préparer proposition monitoring",
        "DECIDE  → Proposer monitoring mensuel 3-8k€/mois à chaque client livré",
        "ACT     → Contrat 12 mois avec -10% si engagement annuel, signature rapide",
        "METRIC  → 3 clients récurrents = 9-24k€ MRR = base solide pour scale",
    ],
    "L6_partenariat": [
        "OBSERVE → Identifier intégrateurs industriels actifs (Siemens partner, Schneider, ABB)",
        "ORIENT  → Analyser leur portfolio clients : où est le gap sécurité OT ?",
        "DECIDE  → Contacter directeur commercial : accord rev-share 30% sur deal OT",
        "ACT     → Signer accord partenariat 1 page + former le partenaire sur le pitch",
        "METRIC  → 2 partenaires actifs = +8-15k€/deal sans prospection directe",
    ],
    "L3_L4_closing": [
        "OBSERVE → Auditer pipeline : chaque deal sans réponse depuis +14j",
        "ORIENT  → Classer par probabilité closing : chaud/tiède/froid",
        "DECIDE  → Appel phone sur chauds, escompte 10% si signature avant fin mois",
        "ACT     → Envoyer proposition formelle PDF avec deadline explicite J+5",
        "METRIC  → 1 Pack Sécurité Avancée 40k€ signé = objectif M6 atteint",
    ],
    "L4_grands_comptes": [
        "OBSERVE → Identifier 3 grands comptes CAC40 OT exposé (Airbus, Michelin, EDF, SNCF)",
        "ORIENT  → Passer par procurement : cartographier décideurs achat + budgets",
        "DECIDE  → Proposition Pack Premium Full 80k€ via buyer + prescripteur interne",
        "ACT     → Relance hebdo, proposer démo gratuite 30 min sur site",
        "METRIC  → 1 deal Premium Full 80k€ = objectif M7-M8 atteint seul",
    ],
    "L5_mrr_scale": [
        "OBSERVE → Lister tous clients one-shot depuis le début, calculer potentiel MRR",
        "ORIENT  → Identifier les 5 plus grands : proposer monitoring mensuel premium",
        "DECIDE  → Prix monitoring : 3k-8k€/mois selon taille infrastructure OT",
        "ACT     → Signer 5 contrats monitoring = 15-40k€ MRR stable",
        "METRIC  → 10k€ MRR = 120k€/an récurrents = scale possible sans risque",
    ],
    "L3_L4_pipeline": [
        "OBSERVE → Analyser conversion par secteur : transport vs énergie vs industrie",
        "ORIENT  → Prioriser secteur avec meilleur taux conv et deal size moyen",
        "DECIDE  → Concentrer 80% outreach sur secteur #1, relance deals >7j",
        "ACT     → Proposer visite site gratuite pour débloquer deals hésitants",
        "METRIC  → 1 deal signé/semaine à 40k+ = objectif M9 dépassé",
    ],
    "L7_upsell_mass": [
        "OBSERVE → Cartographier 100% clients : date livraison, satisfaction, budget restant",
        "ORIENT  → Calculer upsell naturel : audit suivi 6 mois, certification IEC 62443",
        "DECIDE  → Proposer upsell à 100% clients : version avancée + certification",
        "ACT     → Envoyer proposition personnalisée : 30% du deal initial",
        "METRIC  → 10 clients × 30% upsell moyen = +45k€ sans nouveau prospect",
    ],
    "contrats_annuels": [
        "OBSERVE → Identifier clients éligibles contrat annuel (projets one-shot >3 mois)",
        "ORIENT  → Calendrier budgets N+1 : novembre = fenêtre critique à ne pas rater",
        "DECIDE  → Présenter contrat annuel : audit + veille + formation 25-60k€/an",
        "ACT     → Objectif : 5 contrats annuels = 125-300k€ ARR verrouillé",
        "METRIC  → Contrats annuels = visibilité cashflow 12 mois = scale serein",
    ],
    "scale_full": [
        "OBSERVE → Analyser charge de travail : nb d'audits/mois max en solo",
        "ORIENT  → Si >3 audits/mois : recruter consultant junior OT (40k€/an)",
        "DECIDE  → Commission 20% sur deals apportés par consultant",
        "ACT     → Objectif M12 : 80-100k€ = 2× capacité delivery même structure",
        "METRIC  → MRR >20k€ + 1 consultant = système scalable et transmissible",
    ],
}

# ── INDICATEURS OODA PAR MOIS ─────────────────────────────────────────────────
OODA_WEEKLY_TARGETS = {
    "semaine_1_2": {
        "action": "Générer 20 offres OT ciblées Apollo + Claude",
        "metric": "20 emails pitchs envoyés, 0 deal attendu",
        "objectif": "Calibrer le message, obtenir 2-3 réponses",
    },
    "semaine_3_4": {
        "action": "Follow-up sur les réponses, proposer appels découverte",
        "metric": "4-5 prospects répondent, 2 appels qualifiés bookés",
        "objectif": "Premier deal possible fin semaine 4",
    },
    "mois_2": {
        "action": "Closer premier deal, lancer batch suivant",
        "metric": "1 contrat signé 2k-15k€",
        "objectif": "Validation du message commercial",
    },
    "mois_3": {
        "action": "Pipeline 2-3 deals actifs simultanément",
        "metric": "25k€ encaissés",
        "objectif": "Répétabilité prouvée",
    },
    "mois_4_6": {
        "action": "Stream contenu récurrent + premiers MRR",
        "metric": "3 clients récurrents, MRR 5k€",
        "objectif": "Base stable pour accélérer",
    },
    "mois_6": {
        "action": "60k€ atteint — lancer SaaS NIS2 checker MVP",
        "metric": "10 premiers clients SaaS",
        "objectif": "Revenue diversifié",
    },
    "mois_6_12": {
        "action": "Scale : contrats annuels + consultant OT",
        "metric": "80-100k€/mois",
        "objectif": "Système transmissible opérationnel",
    },
}


@dataclass
class Revenue:
    id: str = field(default_factory=lambda: f"R{uuid.uuid4().hex[:6].upper()}")
    montant: float = 0.0
    source: str = ""
    levier: str = ""
    client: str = ""
    date: str = field(default_factory=lambda: date.today().isoformat())
    note: str = ""
    ooda_phase: str = ""   # OBSERVE/ORIENT/DECIDE/ACT


class RevenueTargetEngine:
    """Tracking des objectifs M1→M12 avec boucle OODA intégrée."""

    FILE = ROOT / "data" / "cache" / "revenue_targets.json"

    def __init__(self):
        self.entries: List[Revenue] = []
        self.start_date: str = date.today().isoformat()
        self.FILE.parent.mkdir(parents=True, exist_ok=True)
        self._load()
        m = self.current_month()
        obj = OBJECTIFS.get(m, OBJECTIFS[1])
        log.info("RevenueTargetEngine V19 — M%d | Objectif: %s€ | OODA: %s",
                 m, obj["target"], obj["ooda_focus"])

    def current_month(self) -> int:
        start = date.fromisoformat(self.start_date)
        today = date.today()
        m = (today.year - start.year) * 12 + (today.month - start.month) + 1
        return max(1, min(m, 12))

    def monthly_total(self) -> float:
        today = date.today()
        return sum(r.montant for r in self.entries
                   if date.fromisoformat(r.date).month == today.month
                   and date.fromisoformat(r.date).year == today.year)

    def record(self, montant: float, source: str, client: str = "",
               levier: str = "", note: str = "", ooda_phase: str = "ACT") -> str:
        """Enregistre un revenu + notification Telegram."""
        rev = Revenue(montant=montant, source=source, client=client,
                      levier=levier, note=note, ooda_phase=ooda_phase)
        self.entries.append(rev)
        self._save()
        log.info("REVENU: +%.0f€ | %s | %s | OODA: %s", montant, source, client, ooda_phase)
        self._notify(montant, source, client)
        return rev.id

    def _notify(self, montant: float, source: str, client: str):
        try:
            from NAYA_CORE.integrations.telegram_notifier import get_notifier
            total = self.monthly_total()
            obj = OBJECTIFS.get(self.current_month(), {}).get("target", 5000)
            pct = total / obj * 100
            get_notifier().send(
                f"💰 <b>+{montant:,.0f}€ encaissé!</b>\n"
                f"Source: {source} | Client: {client or '—'}\n"
                f"Total M{self.current_month()}: {total:,.0f}€ / {obj:,}€ ({pct:.0f}%)\n"
                f"{'✅ OBJECTIF ATTEINT!' if pct >= 100 else f'⚡ Reste: {obj-total:,.0f}€'}"
            )
        except Exception:
            pass

    def get_current_target(self) -> Dict:
        """Objectifs du mois courant + actions OODA du jour + deals nécessaires."""
        m = self.current_month()
        obj = OBJECTIFS.get(m, OBJECTIFS[12])
        total = self.monthly_total()
        levier = obj["levier"]
        gap = max(0.0, obj["target"] - total)

        prix_type = {
            "L1_formation": 5000, "L2_audit_express": 15000,
            "L2_L3_catalogue": 27500, "L5_recurrence": 3000,
            "L6_partenariat": 10000, "L3_L4_closing": 30000,
            "L4_grands_comptes": 80000, "L5_mrr_scale": 5000,
            "L3_L4_pipeline": 40000, "L7_upsell_mass": 12000,
            "contrats_annuels": 35000, "scale_full": 50000,
        }.get(levier, 15000)

        return {
            "mois": m,
            "objectif_min": obj["min"],
            "objectif_target": obj["target"],
            "objectif_max": obj["max"],
            "deals_type": obj.get("deals_type", ""),
            "ooda_focus_du_mois": obj.get("ooda_focus", ""),
            "realise_ce_mois": total,
            "gap_eur": gap,
            "progression_pct": round(total / obj["target"] * 100, 1),
            "statut": "✅ ATTEINT" if total >= obj["target"] else "⚡ EN COURS",
            "levier_principal": levier,
            "actions_ooda_du_jour": ACTIONS.get(levier, []),
            "deals_necessaires": {
                "prix_deal_type": prix_type,
                "nb_deals": round(gap / prix_type, 1) if prix_type else 0,
                "message": f"{round(gap/prix_type, 1) if prix_type else 1} deal(s) à {prix_type:,}€ pour combler le gap",
            },
            "prochain_palier": self._next_milestone(sum(r.montant for r in self.entries)),
            "ooda_weekly": OODA_WEEKLY_TARGETS,
        }

    def get_full_dashboard(self) -> Dict:
        """Dashboard complet M1→M12 avec OODA par mois."""
        total_all = sum(r.montant for r in self.entries)
        monthly: Dict[int, float] = {}
        for r in self.entries:
            m = date.fromisoformat(r.date).month
            monthly[m] = monthly.get(m, 0.0) + r.montant

        return {
            "start_date": self.start_date,
            "mois_courant": self.current_month(),
            "total_encaisse": total_all,
            "objectifs_par_mois": OBJECTIFS,
            "realise_par_mois": monthly,
            "current": self.get_current_target(),
            "derniers_revenus": [asdict(r) for r in self.entries[-10:]],
            "forecast_12m": {m: OBJECTIFS[m]["target"] for m in range(1, 13)},
            "annualise": {
                "objectif_annuel": sum(OBJECTIFS[m]["target"] for m in range(1, 13)),
                "realise_ytd": total_all,
                "cap_annuel_max": sum(OBJECTIFS[m]["max"] for m in range(1, 13)),
            },
        }

    def _next_milestone(self, total: float) -> Dict:
        milestones = [5000, 15000, 25000, 35000, 45000, 60000, 80000, 100000, 150000, 200000]
        for m in milestones:
            if total < m:
                return {"montant": m, "manque": m - total, "pct": round(total / m * 100, 1)}
        return {"montant": None, "message": "🏆 Tous les paliers franchis — Scale illimité"}

    def _save(self):
        try:
            data = {"start_date": self.start_date,
                    "entries": [asdict(r) for r in self.entries],
                    "ts": time.time(), "version": "V19"}
            self.FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            log.warning("RevenueTargets save: %s", e)

    def _load(self):
        try:
            if self.FILE.exists():
                d = json.loads(self.FILE.read_text(encoding="utf-8"))
                self.start_date = d.get("start_date", self.start_date)
                self.entries = [Revenue(**e) for e in d.get("entries", [])]
        except Exception as e:
            log.warning("RevenueTargets load: %s", e)


# ── SINGLETON ────────────────────────────────────────────────────────────────
_inst: Optional[RevenueTargetEngine] = None


def get_revenue_targets() -> RevenueTargetEngine:
    global _inst
    if _inst is None:
        _inst = RevenueTargetEngine()
    return _inst
