#!/usr/bin/env python3
"""
NAYA V19 — Pre-Deployment Sales Validator
═══════════════════════════════════════════════════════════════════════════════
GATE DE VALIDATION : Aucun déploiement sans 2 ventes réelles encaissées.

Séquence obligatoire (2 ventes réelles par déploiement) :
  TEST 1 → Local (port 3000) : vente 1 = 15 000 EUR + vente 2 = 25 000 EUR → déploiement local
  TEST 2 → Docker            : vente 1 = 25 000 EUR + vente 2 = 35 000 EUR → déploiement docker
  TEST 3 → Vercel            : vente 1 = 35 000 EUR + vente 2 = 45 000 EUR → déploiement vercel
  TEST 4 → Render            : vente 1 = 45 000 EUR + vente 2 = 55 000 EUR → déploiement render
  TEST 5 → Cloud Run         : vente 1 = 55 000 EUR + vente 2 = 65 000 EUR → déploiement cloud run

Chaque vente (x2 par test) :
  1. Lance le pipeline revenue complet (prospect → offre → outreach → closing → paiement)
  2. Attend confirmation encaissement réel (webhook PayPal/Deblock ou validation manuelle)
  3. Notifie Telegram : ✅ vente confirmée + montant + client + méthode
  4. Enregistre dans le ledger (SHA-256 immuable)
  5. Après les 2 ventes → déverrouille l'étape de déploiement suivante

Total objectif : 400 000 EUR encaissés (10 ventes sur 5 déploiements)

Usage :
  python tools/pre_deploy_validator.py --run-all          # Séquence complète 5 tests
  python tools/pre_deploy_validator.py --test local       # Test individuel
  python tools/pre_deploy_validator.py --status           # État courant
  python tools/pre_deploy_validator.py --confirm PAY_XXX  # Confirmer manuellement un paiement
"""

import os
import sys
import json
import time
import uuid
import hashlib
import logging
import threading
import argparse
import urllib.request
import urllib.parse
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("NAYA.PREVALIDATE")

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

VALIDATION_LEDGER = ROOT / "data" / "validation" / "pre_deploy_ledger.json"
VALIDATION_LOCK   = ROOT / "data" / "validation" / ".lock"

LOCAL_PORT = 3000   # Port local cible

DEPLOYMENT_TARGETS = [
    {"id": "local",     "label": "Local (port 3000)",       "sale1_eur": 15_000, "sale2_eur": 25_000, "index": 1},
    {"id": "docker",    "label": "Docker (conteneurisé)",   "sale1_eur": 25_000, "sale2_eur": 35_000, "index": 2},
    {"id": "vercel",    "label": "Vercel (serverless)",     "sale1_eur": 35_000, "sale2_eur": 45_000, "index": 3},
    {"id": "render",    "label": "Render (PaaS)",           "sale1_eur": 45_000, "sale2_eur": 55_000, "index": 4},
    {"id": "cloud_run", "label": "Google Cloud Run",        "sale1_eur": 55_000, "sale2_eur": 65_000, "index": 5},
]

# Offres B2B haute valeur — 2 offres distinctes par déploiement (vente 1 + vente 2)
HIGH_VALUE_OFFERS_BY_TARGET: Dict[str, Dict[str, List[Dict]]] = {
    "local": {
        "sale1": [
            {"title": "Audit Cybersécurité OT Express",         "price": 15_000, "sector": "Transport/Logistique"},
            {"title": "Mission Consulting B2B — Résultat 30j",  "price": 15_000, "sector": "PME"},
            {"title": "Pack Transformation Digitale PME",       "price": 15_000, "sector": "Commerce"},
        ],
        "sale2": [
            {"title": "Mission Conformité NIS2 — 45 jours",     "price": 25_000, "sector": "Industrie"},
            {"title": "Programme Formation OT Sécurité Avancée","price": 25_000, "sector": "Manufacturier"},
            {"title": "Audit IEC 62443 Niveau SL-2",            "price": 25_000, "sector": "Énergie"},
        ],
    },
    "docker": {
        "sale1": [
            {"title": "Audit IEC 62443 Niveau SL-2",            "price": 25_000, "sector": "Énergie"},
            {"title": "Mission Conformité NIS2 — 60 jours",     "price": 25_000, "sector": "Industrie"},
            {"title": "Programme Formation OT Sécurité",        "price": 25_000, "sector": "Manufacturier"},
        ],
        "sale2": [
            {"title": "Audit SCADA Critique + Roadmap",         "price": 35_000, "sector": "Utilities"},
            {"title": "Mission Remédiation OT Complète",        "price": 35_000, "sector": "Transport"},
            {"title": "SaaS NIS2 Checker 3 ans",                "price": 35_000, "sector": "Multi-secteur"},
        ],
    },
    "vercel": {
        "sale1": [
            {"title": "Audit SCADA Critique + Roadmap",         "price": 35_000, "sector": "Utilities"},
            {"title": "Mission Remédiation OT Complète",        "price": 35_000, "sector": "Transport"},
            {"title": "SaaS NIS2 Checker 3 ans",                "price": 35_000, "sector": "Multi-secteur"},
        ],
        "sale2": [
            {"title": "Programme Cybersécurité Industrielle",   "price": 45_000, "sector": "Énergie & Gaz"},
            {"title": "Audit + Remédiation IEC 62443 SL-3",     "price": 45_000, "sector": "Infrastructure"},
            {"title": "Contrat Retainer Sécurité OT 12 mois",   "price": 45_000, "sector": "Manufacturing"},
        ],
    },
    "render": {
        "sale1": [
            {"title": "Programme Cybersécurité Industrielle",   "price": 45_000, "sector": "Énergie & Gaz"},
            {"title": "Audit + Remédiation IEC 62443 SL-3",     "price": 45_000, "sector": "Infrastructure"},
            {"title": "Contrat Retainer Sécurité OT 12 mois",   "price": 45_000, "sector": "Manufacturing"},
        ],
        "sale2": [
            {"title": "Mission Stratégique Cybersécurité OT",   "price": 55_000, "sector": "Gouvernement"},
            {"title": "Audit Infrastructure Critique NIS2",     "price": 55_000, "sector": "Énergie"},
            {"title": "Retainer Premium Sécurité 18 mois",      "price": 55_000, "sector": "Defence"},
        ],
    },
    "cloud_run": {
        "sale1": [
            {"title": "Mission Stratégique Cybersécurité OT",   "price": 55_000, "sector": "Gouvernement"},
            {"title": "Audit Infrastructure Critique NIS2",     "price": 55_000, "sector": "Énergie"},
            {"title": "Retainer Premium Sécurité 18 mois",      "price": 55_000, "sector": "Defence"},
        ],
        "sale2": [
            {"title": "Programme Grand Compte OT CAC40",        "price": 65_000, "sector": "Industrie Lourde"},
            {"title": "Contrat Cadre Cybersécurité OT 24 mois", "price": 65_000, "sector": "Infrastructure Critique"},
            {"title": "Audit Full-Scope IEC 62443 SL-4",        "price": 65_000, "sector": "Énergie Nucléaire"},
        ],
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _gs(key: str, default: str = "") -> str:
    """Charge un secret depuis l'environnement ou le SecretsLoader."""
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(key, default) or default
    except Exception:
        return os.environ.get(key, default)


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


def _print_banner(msg: str, char: str = "═") -> None:
    width = 70
    print(f"\n{char * width}")
    print(f"  {msg}")
    print(f"{char * width}")


# ══════════════════════════════════════════════════════════════════════════════
# TELEGRAM NOTIFIER (standalone — pas de dépendance externe)
# ══════════════════════════════════════════════════════════════════════════════

class _Telegram:
    """Envoi Telegram direct — pas de thread, retry intégré."""

    def __init__(self):
        self._token   = _gs("TELEGRAM_BOT_TOKEN", "")
        self._chat_id = _gs("TELEGRAM_CHAT_ID", "")
        # Fallback: lire depuis SECRETS/keys/telegram.json
        if not self._token or not self._chat_id:
            self._load_from_file()

    def _load_from_file(self) -> None:
        candidates = [
            ROOT / "SECRETS" / "keys" / "telegram.json",
            ROOT / "SECRETS" / "telegram.json",
        ]
        for f in candidates:
            if f.exists():
                try:
                    d = json.loads(f.read_text())
                    self._token   = self._token   or d.get("bot_token", d.get("token", ""))
                    self._chat_id = self._chat_id or str(d.get("chat_id", ""))
                    if self._token and self._chat_id:
                        log.info(f"[TELEGRAM] Config chargée depuis {f.name}")
                        break
                except Exception as e:
                    log.debug(f"[TELEGRAM] Erreur lecture {f}: {e}")

    def send(self, text: str, retries: int = 3) -> bool:
        if not self._token or not self._chat_id:
            log.warning("[TELEGRAM] ⚠️  Token/Chat_ID manquant — notification skippée")
            return False
        for attempt in range(retries):
            try:
                url  = f"https://api.telegram.org/bot{self._token}/sendMessage"
                data = urllib.parse.urlencode({
                    "chat_id": self._chat_id,
                    "text": text[:4096],
                    "parse_mode": "HTML",
                }).encode()
                req  = urllib.request.Request(url, data=data)
                urllib.request.urlopen(req, timeout=15)
                log.info(f"[TELEGRAM] ✅ Message envoyé ({len(text)} chars)")
                return True
            except Exception as e:
                log.debug(f"[TELEGRAM] Tentative {attempt + 1} échouée: {e}")
                time.sleep(2 ** attempt)
        log.error("[TELEGRAM] ❌ Échec après 3 tentatives")
        return False

    def notify_sale_validated(
        self,
        test_index: int,
        sale_number: int,
        deploy_target: str,
        amount_eur: float,
        client_name: str,
        payment_method: str,
        payment_id: str,
        sha256_hash: str,
    ) -> bool:
        ts = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
        msg = (
            f"🚀 <b>NAYA V19 — VENTE RÉELLE VALIDÉE</b>\n"
            f"{'━' * 35}\n"
            f"🎯 Test #{test_index} — Vente {sale_number}/2 — <b>{deploy_target.upper()}</b>\n"
            f"💰 Montant encaissé : <b>{amount_eur:,.0f} EUR</b>\n"
            f"🏢 Client : {client_name}\n"
            f"💳 Méthode : {payment_method.upper()}\n"
            f"🔑 Réf paiement : <code>{payment_id}</code>\n"
            f"🔒 SHA-256 : <code>{sha256_hash[:16]}…</code>\n"
            f"⏰ {ts}\n"
            f"{'━' * 35}\n"
        )
        if sale_number == 2:
            msg += f"✅ <b>Déploiement {deploy_target.upper()} DÉVERROUILLÉ (2/2 ventes ✅)</b>"
        else:
            msg += f"⏩ Vente 1/2 confirmée — Lancement de la vente 2…"
        return self.send(msg)

    def notify_sequence_start(self, total_tests: int) -> None:
        msg = (
            f"🔔 <b>NAYA V19 — SÉQUENCE VALIDATION DÉMARRÉE</b>\n"
            f"{'━' * 35}\n"
            f"📋 {total_tests} tests à valider (2 ventes réelles par test)\n"
            f"💰 Montants par test :\n"
            f"   Test 1 (LOCAL  port 3000) : 15 000 + 25 000 EUR\n"
            f"   Test 2 (DOCKER)           : 25 000 + 35 000 EUR\n"
            f"   Test 3 (VERCEL)           : 35 000 + 45 000 EUR\n"
            f"   Test 4 (RENDER)           : 45 000 + 55 000 EUR\n"
            f"   Test 5 (CLOUD RUN)        : 55 000 + 65 000 EUR\n"
            f"🎯 Condition : 2 ventes réelles encaissées avant chaque déploiement\n"
            f"🏆 Objectif total : 400 000 EUR (10 ventes)\n"
            f"⏰ Démarré : {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')}"
        )
        self.send(msg)

    def notify_sequence_complete(self, total_eur: float) -> None:
        msg = (
            f"🏆 <b>NAYA V19 — VALIDATION COMPLÈTE</b>\n"
            f"{'━' * 35}\n"
            f"✅ 5/5 tests réussis (10 ventes réelles encaissées)\n"
            f"💰 Total encaissé : <b>{total_eur:,.0f} EUR</b>\n"
            f"🚀 Tous les déploiements déverrouillés :\n"
            f"   ✅ Local port 3000 (15k + 25k)\n"
            f"   ✅ Docker         (25k + 35k)\n"
            f"   ✅ Vercel         (35k + 45k)\n"
            f"   ✅ Render         (45k + 55k)\n"
            f"   ✅ Cloud Run      (55k + 65k)\n"
            f"⏰ {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')}"
        )
        self.send(msg)

    def notify_test_started(self, test_index: int, deploy_target: str, sale1_eur: float, sale2_eur: float) -> None:
        msg = (
            f"▶️ <b>TEST #{test_index} DÉMARRÉ</b>\n"
            f"🎯 Cible : {deploy_target.upper()}\n"
            f"💰 Vente 1 requise : {sale1_eur:,.0f} EUR réels\n"
            f"💰 Vente 2 requise : {sale2_eur:,.0f} EUR réels\n"
            f"🔄 Pipeline revenue en cours (vente 1/2)…"
        )
        self.send(msg)

    def notify_payment_link_sent(
        self,
        test_index: int,
        sale_number: int,
        prospect: str,
        amount: float,
        payment_url: str,
        payment_id: str,
    ) -> None:
        msg = (
            f"📤 <b>TEST #{test_index} — VENTE {sale_number}/2 — LIEN PAIEMENT ENVOYÉ</b>\n"
            f"🏢 Prospect : {prospect}\n"
            f"💰 Montant : {amount:,.0f} EUR\n"
            f"🔗 Lien : {payment_url}\n"
            f"🔑 Réf : <code>{payment_id}</code>\n"
            f"⏳ En attente d'encaissement…\n\n"
            f"Pour confirmer manuellement :\n"
            f"<code>python tools/pre_deploy_validator.py --confirm {payment_id}</code>"
        )
        self.send(msg)


# ══════════════════════════════════════════════════════════════════════════════
# PAYMENT LINK GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

class _PaymentLinks:
    """Génère les liens de paiement PayPal.me et Deblock."""

    def __init__(self):
        self._paypal  = _gs("PAYPAL_ME_URL",  "https://www.paypal.me/Myking987")
        self._deblock = _gs("DEBLOCK_ME_URL", "")
        if not self._deblock:
            self._deblock = self._load_deblock()

    def _load_deblock(self) -> str:
        candidates = [
            ROOT / "SECRETS" / "keys" / "payment" / "deblock.json",
            ROOT / "SECRETS" / "keys" / "payments_index.json",
        ]
        for f in candidates:
            if f.exists():
                try:
                    d = json.loads(f.read_text())
                    url = d.get("DEBLOCK_ME_URL") or d.get("link") or d.get("deblock_url", "")
                    if url:
                        return url
                except Exception:
                    pass
        return "https://deblock.com/a-ftp860"

    def paypal(self, amount: float, description: str = "") -> str:
        base = self._paypal.rstrip("/")
        return f"{base}/{amount:.0f}"

    def deblock(self, amount: float, description: str = "", ref: str = "") -> str:
        base = self._deblock.rstrip("/")
        safe = urllib.parse.quote(description[:60])
        return f"{base}?amount={amount:.0f}&description={safe}&ref={ref}"

    def best(self, amount: float, description: str = "", ref: str = "") -> Tuple[str, str]:
        """Retourne (url, méthode) avec PayPal en priorité."""
        if "paypal.me/" in self._paypal:
            return self.paypal(amount, description), "paypal"
        return self.deblock(amount, description, ref), "deblock"


# ══════════════════════════════════════════════════════════════════════════════
# VALIDATION LEDGER (persistance + intégrité SHA-256)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ValidationRecord:
    payment_id:      str
    deploy_target:   str
    test_index:      int
    sale_number:     int       # 1 or 2
    target_eur:      float
    amount_collected: float
    client_name:     str
    payment_method:  str
    payment_url:     str
    offer_title:     str
    status:          str       # pending | confirmed | failed
    created_at:      str       = field(default_factory=_now_iso)
    confirmed_at:    Optional[str] = None
    sha256_hash:     str       = ""
    telegram_sent:   bool      = False

    def compute_hash(self) -> str:
        """Hash immuable de la transaction."""
        payload = (
            f"{self.payment_id}|{self.deploy_target}|{self.sale_number}"
            f"|{self.amount_collected}|{self.client_name}|{self.confirmed_at}"
        )
        return _sha256(payload)


class ValidationLedger:
    """Registre persistant des validations pré-déploiement."""

    def __init__(self):
        VALIDATION_LEDGER.parent.mkdir(parents=True, exist_ok=True)
        self._records: Dict[str, ValidationRecord] = {}
        self._lock = threading.RLock()
        self._load()

    def _load(self) -> None:
        if VALIDATION_LEDGER.exists():
            try:
                raw = json.loads(VALIDATION_LEDGER.read_text())
                for pid, d in raw.items():
                    self._records[pid] = ValidationRecord(**d)
                log.info(f"[LEDGER] {len(self._records)} records chargés")
            except Exception as e:
                log.error(f"[LEDGER] Erreur chargement: {e}")

    def _save(self) -> None:
        try:
            data = {pid: asdict(r) for pid, r in self._records.items()}
            VALIDATION_LEDGER.write_text(json.dumps(data, indent=2))
        except Exception as e:
            log.error(f"[LEDGER] Erreur sauvegarde: {e}")

    def create(self, rec: ValidationRecord) -> ValidationRecord:
        with self._lock:
            self._records[rec.payment_id] = rec
            self._save()
        return rec

    def confirm(self, payment_id: str, amount_received: float) -> Optional[ValidationRecord]:
        with self._lock:
            rec = self._records.get(payment_id)
            if not rec:
                return None
            rec.amount_collected = amount_received
            rec.status           = "confirmed"
            rec.confirmed_at     = _now_iso()
            rec.sha256_hash      = rec.compute_hash()
            self._save()
        return rec

    def get(self, payment_id: str) -> Optional[ValidationRecord]:
        return self._records.get(payment_id)

    def get_by_target(self, deploy_target: str) -> Optional[ValidationRecord]:
        """Returns the confirmed record for sale 1 of the target (legacy compatibility)."""
        return self.get_confirmed_sale(deploy_target, 1)

    def get_confirmed_sale(self, deploy_target: str, sale_number: int) -> Optional[ValidationRecord]:
        """Returns the confirmed ValidationRecord for a specific sale of a target."""
        for r in self._records.values():
            if r.deploy_target == deploy_target and r.sale_number == sale_number and r.status == "confirmed":
                return r
        return None

    def get_pending_sale(self, deploy_target: str, sale_number: int) -> Optional[ValidationRecord]:
        """Returns the pending ValidationRecord for a specific sale of a target."""
        for r in self._records.values():
            if r.deploy_target == deploy_target and r.sale_number == sale_number and r.status == "pending":
                return r
        return None

    def is_sale_confirmed(self, deploy_target: str, sale_number: int) -> bool:
        """Returns True if a specific sale for the target is confirmed."""
        rec = self.get_confirmed_sale(deploy_target, sale_number)
        return rec is not None and rec.amount_collected >= rec.target_eur

    def is_validated(self, deploy_target: str) -> bool:
        """Returns True only when BOTH sales (1 and 2) are confirmed for the target."""
        return self.is_sale_confirmed(deploy_target, 1) and self.is_sale_confirmed(deploy_target, 2)

    def get_all_confirmed(self) -> List[ValidationRecord]:
        return [r for r in self._records.values() if r.status == "confirmed"]

    def get_all_pending(self) -> List[ValidationRecord]:
        return [r for r in self._records.values() if r.status == "pending"]

    def status_report(self) -> Dict:
        results: Dict[str, Any] = {}
        for t in DEPLOYMENT_TARGETS:
            tid = t["id"]
            sale1 = self.get_confirmed_sale(tid, 1)
            sale2 = self.get_confirmed_sale(tid, 2)
            pend1 = self.get_pending_sale(tid, 1)
            pend2 = self.get_pending_sale(tid, 2)

            if sale1 and sale2:
                state = "✅ VALIDÉ (2/2 ventes)"
            elif sale1:
                if pend2:
                    state = f"⏳ Vente 1 ✅ — Vente 2 EN ATTENTE ({pend2.payment_id})"
                else:
                    state = "⏳ Vente 1 ✅ — Vente 2 NON DÉMARRÉE"
            elif pend1:
                state = f"⏳ Vente 1 EN ATTENTE ({pend1.payment_id})"
            else:
                state = "🔲 NON DÉMARRÉ"

            results[tid] = state
        return results


# ══════════════════════════════════════════════════════════════════════════════
# REVENUE PIPELINE BRIDGE
# ══════════════════════════════════════════════════════════════════════════════

class _RevenuePipelineBridge:
    """
    Lance le pipeline revenue réel pour trouver et closer un deal.
    Utilise les modules disponibles dans le projet.
    """

    def find_best_prospect(self, target_eur: float, sector: str) -> Dict:
        """
        Tente de trouver un prospect qualifié via le système existant.
        Retourne les données du meilleur prospect disponible.
        """
        # Essai 1 — ProspectFinder réel
        try:
            from NAYA_REVENUE_ENGINE.prospect_finder import ProspectFinder
            finder = ProspectFinder()
            prospects = finder.find_high_value_prospects(min_amount=target_eur * 0.8)
            if prospects:
                p = prospects[0]
                return {
                    "name": getattr(p, "contact_name", "") or getattr(p, "company_name", "Unknown"),
                    "company": getattr(p, "company_name", "Unknown"),
                    "email": getattr(p, "email", ""),
                    "sector": getattr(p, "sector", sector),
                    "score": getattr(p, "solvability_score", 80),
                    "source": "prospect_finder",
                }
        except Exception as e:
            log.debug(f"[PIPELINE] ProspectFinder: {e}")

        # Essai 2 — Pain Hunter B2B
        try:
            from HUNTING_AGENTS.pain_hunter_b2b import PainHunterB2B
            hunter = PainHunterB2B()
            pains  = hunter.hunt(limit=3)
            if pains:
                p = pains[0]
                return {
                    "name": p.get("contact_name", p.get("company", "Unknown")),
                    "company": p.get("company", "Unknown"),
                    "email": p.get("email", ""),
                    "sector": p.get("sector", sector),
                    "score": p.get("score", 75),
                    "source": "pain_hunter_b2b",
                }
        except Exception as e:
            log.debug(f"[PIPELINE] PainHunterB2B: {e}")

        # Essai 3 — Revenue Sprint engine (canaux détectés)
        try:
            from NAYA_REVENUE_ENGINE.revenue_sprint_engine import get_revenue_sprint
            sprint = get_revenue_sprint()
            status = sprint.start_sprint()
            if status.get("channels_active"):
                return {
                    "name": "Prospect Qualifié Pipeline",
                    "company": f"Entreprise Secteur {sector}",
                    "email": "",
                    "sector": sector,
                    "score": 72,
                    "source": "revenue_sprint",
                }
        except Exception as e:
            log.debug(f"[PIPELINE] RevenueSprint: {e}")

        # Fallback — prospect synthétique généré pour la séquence d'outreach
        return {
            "name": f"Décideur {sector}",
            "company": f"Entreprise Cible {sector} #{uuid.uuid4().hex[:4].upper()}",
            "email": "",
            "sector": sector,
            "score": 70,
            "source": "synthetic_pipeline",
        }

    def generate_offer(self, prospect: Dict, offer_config: Dict) -> Dict:
        """Génère l'offre commerciale pour le prospect."""
        try:
            from NAYA_REVENUE_ENGINE.offer_generator import OfferGenerator
            gen   = OfferGenerator()
            offer = gen.generate(
                prospect_name=prospect["company"],
                sector=prospect["sector"],
                pain=offer_config.get("title", ""),
                budget=offer_config["price"],
            )
            return offer if isinstance(offer, dict) else asdict(offer) if hasattr(offer, "__dataclass_fields__") else {"title": offer_config["title"], "price": offer_config["price"]}
        except Exception as e:
            log.debug(f"[PIPELINE] OfferGenerator: {e}")
            return {"title": offer_config["title"], "price": offer_config["price"]}

    def launch_outreach(self, prospect: Dict, offer: Dict, payment_url: str) -> bool:
        """Lance l'outreach multi-canal avec le lien de paiement."""
        try:
            from NAYA_REVENUE_ENGINE.outreach_engine import OutreachEngine
            engine = OutreachEngine()
            engine.send_outreach(
                prospect_email=prospect.get("email", ""),
                prospect_name=prospect.get("name", ""),
                offer_title=offer.get("title", ""),
                offer_price=offer.get("price", 0),
                payment_url=payment_url,
            )
            log.info(f"[PIPELINE] ✅ Outreach lancé vers {prospect.get('name')}")
            return True
        except Exception as e:
            log.debug(f"[PIPELINE] OutreachEngine: {e}")

        # Essai multi-canal
        try:
            from NAYA_REVENUE_ENGINE.multi_persona_outreach import MultiPersonaOutreach
            mp = MultiPersonaOutreach()
            mp.run_sequence(
                target=prospect.get("name", ""),
                offer=offer.get("title", ""),
                amount=offer.get("price", 0),
                payment_link=payment_url,
            )
            return True
        except Exception as e:
            log.debug(f"[PIPELINE] MultiPersonaOutreach: {e}")

        return False


# ══════════════════════════════════════════════════════════════════════════════
# PAYMENT CONFIRMATION POLLER
# ══════════════════════════════════════════════════════════════════════════════

class _PaymentPoller:
    """
    Surveille la confirmation de paiement.
    Modes :
      - webhook  : endpoint FastAPI /webhooks/payment (si disponible)
      - manual   : confirmation via CLI ou Telegram bot
    """

    POLL_INTERVAL_SEC = 30
    MAX_WAIT_SEC      = 7200   # 2H max par test

    def wait_for_confirmation(
        self,
        payment_id: str,
        ledger: ValidationLedger,
        target_eur: float,
        test_index: int,
    ) -> Tuple[bool, float]:
        """
        Attend la confirmation de paiement.
        Retourne (succès, montant_reçu).
        """
        deadline  = time.time() + self.MAX_WAIT_SEC
        elapsed   = 0
        log.info(f"[POLLER] Attente paiement {payment_id} (max {self.MAX_WAIT_SEC // 60} min)…")

        while time.time() < deadline:
            # Vérifier si confirmé dans le ledger (via CLI --confirm ou webhook)
            rec = ledger.get(payment_id)
            if rec and rec.status == "confirmed":
                log.info(f"[POLLER] ✅ Paiement {payment_id} confirmé: {rec.amount_collected:.0f}€")
                return True, rec.amount_collected

            # Essayer l'API PayPal (si token disponible)
            confirmed, amount = self._check_paypal_api(payment_id, target_eur)
            if confirmed:
                ledger.confirm(payment_id, amount)
                return True, amount

            elapsed += self.POLL_INTERVAL_SEC
            mins_left = (deadline - time.time()) / 60
            print(f"  ⏳ Test #{test_index} — Attente paiement {payment_id} "
                  f"({elapsed // 60:.0f} min écoulées, {mins_left:.0f} min restantes)", end="\r")
            time.sleep(self.POLL_INTERVAL_SEC)

        return False, 0.0

    def _check_paypal_api(self, payment_id: str, expected_amount: float) -> Tuple[bool, float]:
        """Tente de vérifier le paiement via PayPal API IPN/Webhooks."""
        try:
            paypal_token = _gs("PAYPAL_ACCESS_TOKEN", "")
            if not paypal_token:
                return False, 0.0

            # Chercher dans les transactions récentes
            url = "https://api.paypal.com/v1/reporting/transactions"
            headers = {
                "Authorization": f"Bearer {paypal_token}",
                "Content-Type": "application/json",
            }
            params = urllib.parse.urlencode({
                "start_date": datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00Z"),
                "end_date":   datetime.now(timezone.utc).strftime("%Y-%m-%dT23:59:59Z"),
                "fields":     "transaction_info",
            })
            req  = urllib.request.Request(f"{url}?{params}", headers=headers)
            resp = json.loads(urllib.request.urlopen(req, timeout=10).read())

            for tx in resp.get("transaction_details", []):
                info   = tx.get("transaction_info", {})
                amount = float(info.get("transaction_amount", {}).get("value", 0))
                status = info.get("transaction_status", "")
                if status == "S" and abs(amount - expected_amount) < 1.0:
                    return True, amount
        except Exception as e:
            log.debug(f"[POLLER] PayPal API check: {e}")
        return False, 0.0


# ══════════════════════════════════════════════════════════════════════════════
# CORE VALIDATOR
# ══════════════════════════════════════════════════════════════════════════════

class PreDeployValidator:
    """
    Orchestrateur principal de la séquence de validation pré-déploiement.
    """

    def __init__(self):
        self.ledger   = ValidationLedger()
        self.telegram = _Telegram()
        self.payments = _PaymentLinks()
        self.pipeline = _RevenuePipelineBridge()
        self.poller   = _PaymentPoller()

    # ── Test individuel (2 ventes séquentielles) ─────────────────────────────

    def run_test(self, deploy_target: str, skip_if_done: bool = True) -> bool:
        """
        Exécute le test de validation pour un déploiement cible.
        Requiert 2 ventes réelles confirmées (sale 1 puis sale 2).
        Retourne True seulement si les 2 ventes sont confirmées.
        """
        cfg = next((t for t in DEPLOYMENT_TARGETS if t["id"] == deploy_target), None)
        if not cfg:
            log.error(f"[VALIDATOR] Cible inconnue: {deploy_target}")
            return False

        test_index = cfg["index"]
        sale1_eur  = cfg["sale1_eur"]
        sale2_eur  = cfg["sale2_eur"]
        label      = cfg["label"]

        # Déjà entièrement validé (2 ventes) ?
        if skip_if_done and self.ledger.is_validated(deploy_target):
            log.info(f"[VALIDATOR] ✅ {deploy_target} déjà validé (2/2 ventes) — skip")
            return True

        _print_banner(
            f"TEST #{test_index} — {label} | Vente 1: {sale1_eur:,.0f} EUR + Vente 2: {sale2_eur:,.0f} EUR",
            char="━",
        )
        self.telegram.notify_test_started(test_index, deploy_target, sale1_eur, sale2_eur)

        # ── Vente 1 ───────────────────────────────────────────────────────────
        if not self.ledger.is_sale_confirmed(deploy_target, 1):
            ok = self._run_single_sale(
                deploy_target=deploy_target,
                test_index=test_index,
                sale_number=1,
                target_eur=sale1_eur,
                offer_key="sale1",
            )
            if not ok:
                return False
            print()

        # ── Vente 2 ───────────────────────────────────────────────────────────
        if not self.ledger.is_sale_confirmed(deploy_target, 2):
            self.telegram.send(
                f"⏩ <b>TEST #{test_index} — Vente 1 ✅ confirmée</b>\n"
                f"🎯 Lancement de la <b>vente 2/2</b> ({sale2_eur:,.0f} EUR) pour {deploy_target.upper()}…"
            )
            ok = self._run_single_sale(
                deploy_target=deploy_target,
                test_index=test_index,
                sale_number=2,
                target_eur=sale2_eur,
                offer_key="sale2",
            )
            if not ok:
                return False

        _print_banner(
            f"✅ TEST #{test_index} VALIDÉ — 2/2 ventes confirmées — Déploiement {deploy_target.upper()} DÉVERROUILLÉ",
            char="═",
        )
        return True

    def _run_single_sale(
        self,
        deploy_target: str,
        test_index: int,
        sale_number: int,
        target_eur: float,
        offer_key: str,
    ) -> bool:
        """
        Exécute une vente unique (1 ou 2) pour un déploiement cible.
        Retourne True si la vente est confirmée.
        """
        # Vente déjà en attente ?
        existing_pending = self.ledger.get_pending_sale(deploy_target, sale_number)
        if existing_pending:
            log.info(f"[VALIDATOR] Paiement en attente trouvé: {existing_pending.payment_id}")
            return self._wait_and_confirm(existing_pending, test_index, sale_number)

        _print_banner(
            f"TEST #{test_index} — Vente {sale_number}/2 | {deploy_target.upper()} | {target_eur:,.0f} EUR",
            char="─",
        )

        # 1. Sélectionner l'offre pour cette vente
        offers_map = HIGH_VALUE_OFFERS_BY_TARGET.get(deploy_target, {})
        offers     = offers_map.get(offer_key, [])
        offer      = offers[0] if offers else {"title": "Mission Premium", "price": target_eur, "sector": "B2B"}

        # 2. Trouver le meilleur prospect
        print(f"\n  🔍 Recherche prospect (vente {sale_number}/2, objectif ≥ {target_eur:,.0f}€)…")
        prospect = self.pipeline.find_best_prospect(target_eur, offer["sector"])
        print(f"  ✅ Prospect : {prospect['company']} ({prospect['sector']}) — Score {prospect['score']}/100")

        # 3. Générer l'offre
        print(f"\n  📋 Offre : {offer['title']} @ {offer['price']:,.0f}€…")
        offer_data = self.pipeline.generate_offer(prospect, offer)

        # 4. Générer lien de paiement
        payment_id  = f"PDV_{deploy_target.upper()}_S{sale_number}_{uuid.uuid4().hex[:8].upper()}"
        payment_url, method = self.payments.best(
            target_eur,
            description=offer["title"],
            ref=payment_id,
        )
        print(f"  💳 Lien paiement ({method.upper()}) : {payment_url}")

        # 5. Enregistrer dans le ledger
        rec = ValidationRecord(
            payment_id=payment_id,
            deploy_target=deploy_target,
            test_index=test_index,
            sale_number=sale_number,
            target_eur=target_eur,
            amount_collected=0.0,
            client_name=prospect["company"],
            payment_method=method,
            payment_url=payment_url,
            offer_title=offer["title"],
            status="pending",
        )
        self.ledger.create(rec)

        # 6. Notifier Telegram avec lien
        self.telegram.notify_payment_link_sent(
            test_index=test_index,
            sale_number=sale_number,
            prospect=prospect["company"],
            amount=target_eur,
            payment_url=payment_url,
            payment_id=payment_id,
        )

        # 7. Lancer l'outreach
        print(f"\n  📤 Lancement outreach multi-canal…")
        outreach_ok = self.pipeline.launch_outreach(prospect, offer_data, payment_url)
        if outreach_ok:
            print(f"  ✅ Outreach envoyé via pipeline")
        else:
            print(f"  ℹ️  Outreach: pipeline non configuré — lien généré manuellement")

        # 8. Attendre confirmation
        print(f"\n  ⏳ En attente d'encaissement réel ({target_eur:,.0f}€)…")
        print(f"     → Lien paiement : {payment_url}")
        print(f"     → Pour confirmer : python tools/pre_deploy_validator.py --confirm {payment_id}")
        print()

        return self._wait_and_confirm(rec, test_index, sale_number)

    def _wait_and_confirm(self, rec: ValidationRecord, test_index: int, sale_number: int) -> bool:
        """Attend et confirme un paiement en attente."""
        success, amount = self.poller.wait_for_confirmation(
            payment_id=rec.payment_id,
            ledger=self.ledger,
            target_eur=rec.target_eur,
            test_index=test_index,
        )

        if success:
            confirmed = self.ledger.get(rec.payment_id)
            if confirmed:
                self._on_sale_confirmed(confirmed)
            return True

        # Timeout — test échoué
        print(f"\n  ⏰ Timeout — Test #{test_index} vente {sale_number}/2 non complétée dans le délai imparti")
        print(f"     → Reprendre avec : python tools/pre_deploy_validator.py --confirm {rec.payment_id}")
        self.telegram.send(
            f"⚠️ <b>TEST #{test_index} — VENTE {sale_number}/2 TIMEOUT</b>\n"
            f"Le paiement {rec.payment_id} n'a pas été confirmé dans les délais.\n"
            f"Pour confirmer manuellement:\n"
            f"<code>python tools/pre_deploy_validator.py --confirm {rec.payment_id}</code>"
        )
        return False

    def _on_sale_confirmed(self, rec: ValidationRecord) -> None:
        """Actions post-confirmation d'une vente : Telegram + log."""
        print(f"\n  💰 ✅ VENTE {rec.sale_number}/2 CONFIRMÉE : {rec.amount_collected:,.0f}€ — {rec.client_name}")

        # Notification Telegram
        ok = self.telegram.notify_sale_validated(
            test_index=rec.test_index,
            sale_number=rec.sale_number,
            deploy_target=rec.deploy_target,
            amount_eur=rec.amount_collected,
            client_name=rec.client_name,
            payment_method=rec.payment_method,
            payment_id=rec.payment_id,
            sha256_hash=rec.sha256_hash,
        )
        rec.telegram_sent = ok
        self.ledger._save()

    # ── Séquence complète ────────────────────────────────────────────────────

    def run_full_sequence(self) -> bool:
        """
        Exécute les 5 tests séquentiellement (2 ventes par test).
        Chaque test doit réussir (2 ventes confirmées) avant de passer au suivant.
        Retourne True si tous les tests passent.
        """
        _print_banner("NAYA V19 — SÉQUENCE VALIDATION PRÉ-DÉPLOIEMENT COMPLÈTE")
        print(f"\n  Objectif : 10 ventes réelles encaissées (2 par déploiement)")
        print(f"  Séquence : 15k+25k → 25k+35k → 35k+45k → 45k+55k → 55k+65k EUR")
        print(f"  Total cible : 400 000 EUR\n")

        self.telegram.notify_sequence_start(len(DEPLOYMENT_TARGETS))

        results = {}
        for target in DEPLOYMENT_TARGETS:
            tid   = target["id"]
            success = self.run_test(tid, skip_if_done=True)
            results[tid] = success
            if not success:
                print(f"\n  ❌ Test {tid} non validé — séquence interrompue")
                print(f"     Reprendre avec : python tools/pre_deploy_validator.py --run-all")
                return False
            print()

        # Tous réussis
        total_eur = sum(t["sale1_eur"] + t["sale2_eur"] for t in DEPLOYMENT_TARGETS)
        self.telegram.notify_sequence_complete(total_eur)

        _print_banner(
            f"🏆 VALIDATION COMPLÈTE — {total_eur:,.0f} EUR ENCAISSÉS — TOUS DÉPLOIEMENTS AUTORISÉS"
        )
        return True

    # ── Confirmation manuelle ────────────────────────────────────────────────

    def manual_confirm(self, payment_id: str, amount: Optional[float] = None) -> bool:
        """Confirme manuellement un paiement (après vérification humaine)."""
        rec = self.ledger.get(payment_id)
        if not rec:
            print(f"  ❌ Payment ID {payment_id} introuvable dans le ledger")
            return False

        final_amount = amount or rec.target_eur
        confirmed    = self.ledger.confirm(payment_id, final_amount)
        if confirmed:
            self._on_sale_confirmed(confirmed)
            return True
        return False

    # ── Gate de déploiement ──────────────────────────────────────────────────

    def check_deploy_gate(self, deploy_target: str) -> bool:
        """
        Vérifie qu'un déploiement est autorisé (2 ventes confirmées).
        Appelé par tools/deploy.py avant chaque déploiement.
        """
        if self.ledger.is_validated(deploy_target):
            s1 = self.ledger.get_confirmed_sale(deploy_target, 1)
            s2 = self.ledger.get_confirmed_sale(deploy_target, 2)
            print(
                f"  ✅ Déploiement {deploy_target} autorisé\n"
                f"     Vente 1 : {s1.amount_collected:,.0f}€ le {s1.confirmed_at[:10]}\n"
                f"     Vente 2 : {s2.amount_collected:,.0f}€ le {s2.confirmed_at[:10]}"
            )
            return True

        cfg = next((t for t in DEPLOYMENT_TARGETS if t["id"] == deploy_target), None)
        s1_eur = cfg["sale1_eur"] if cfg else 0
        s2_eur = cfg["sale2_eur"] if cfg else 0

        print(f"\n  🚫 DÉPLOIEMENT {deploy_target.upper()} BLOQUÉ")
        print(f"     Condition : 2 ventes réelles encaissées ({s1_eur:,.0f}€ + {s2_eur:,.0f}€)")
        print(f"     Lancer    : python tools/pre_deploy_validator.py --test {deploy_target}")
        return False

    # ── Statut ───────────────────────────────────────────────────────────────

    def print_status(self) -> None:
        """Affiche l'état de tous les tests de validation."""
        _print_banner("NAYA V19 — ÉTAT VALIDATION PRÉ-DÉPLOIEMENT (2 ventes/test)")
        report = self.ledger.status_report()
        total_confirmed = 0.0

        for t in DEPLOYMENT_TARGETS:
            tid    = t["id"]
            label  = t["label"]
            s1_eur = t["sale1_eur"]
            s2_eur = t["sale2_eur"]
            state  = report.get(tid, "🔲 NON DÉMARRÉ")

            s1 = self.ledger.get_confirmed_sale(tid, 1)
            s2 = self.ledger.get_confirmed_sale(tid, 2)
            if s1:
                total_confirmed += s1.amount_collected
            if s2:
                total_confirmed += s2.amount_collected

            detail = ""
            if s1 and s2:
                detail = f" — {s1.amount_collected:,.0f}€ + {s2.amount_collected:,.0f}€"
            elif s1:
                detail = f" — Vente1: {s1.amount_collected:,.0f}€ ✅"

            print(f"  #{t['index']} {label:30} {s1_eur:>6,.0f}+{s2_eur:<6,.0f}€   {state}{detail}")

        print(f"\n  Total encaissé : {total_confirmed:,.0f} EUR")
        print(f"  Objectif total : 400 000 EUR (10 ventes)")
        print()


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def main() -> int:
    parser = argparse.ArgumentParser(
        description="NAYA V19 — Pre-Deployment Sales Validator (2 ventes réelles / déploiement)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  python tools/pre_deploy_validator.py --run-all
  python tools/pre_deploy_validator.py --test local
  python tools/pre_deploy_validator.py --test docker
  python tools/pre_deploy_validator.py --confirm PDV_LOCAL_S1_XXXXXX
  python tools/pre_deploy_validator.py --confirm PDV_LOCAL_S1_XXXXXX --amount 15000
  python tools/pre_deploy_validator.py --confirm PDV_LOCAL_S2_XXXXXX --amount 25000
  python tools/pre_deploy_validator.py --status
  python tools/pre_deploy_validator.py --check local

Séquence (2 ventes par déploiement) :
  Test 1 LOCAL      : vente 1 = 15 000 EUR + vente 2 = 25 000 EUR → port 3000
  Test 2 DOCKER     : vente 1 = 25 000 EUR + vente 2 = 35 000 EUR
  Test 3 VERCEL     : vente 1 = 35 000 EUR + vente 2 = 45 000 EUR
  Test 4 RENDER     : vente 1 = 45 000 EUR + vente 2 = 55 000 EUR
  Test 5 CLOUD RUN  : vente 1 = 55 000 EUR + vente 2 = 65 000 EUR
  Total             : 400 000 EUR (10 ventes)
        """,
    )
    parser.add_argument("--run-all",   action="store_true",  help="Séquence complète 5 tests")
    parser.add_argument("--test",      metavar="TARGET",      help="Test individuel: local|docker|vercel|render|cloud_run")
    parser.add_argument("--confirm",   metavar="PAYMENT_ID",  help="Confirmer manuellement un paiement")
    parser.add_argument("--amount",    type=float,            help="Montant confirmé (avec --confirm)")
    parser.add_argument("--status",    action="store_true",   help="Afficher l'état courant")
    parser.add_argument("--check",     metavar="TARGET",      help="Vérifier si déploiement autorisé")
    args = parser.parse_args()

    validator = PreDeployValidator()

    if args.status:
        validator.print_status()
        return 0

    if args.check:
        ok = validator.check_deploy_gate(args.check)
        return 0 if ok else 1

    if args.confirm:
        ok = validator.manual_confirm(args.confirm, args.amount)
        return 0 if ok else 1

    if args.test:
        valid_targets = {t["id"] for t in DEPLOYMENT_TARGETS}
        if args.test not in valid_targets:
            print(f"❌ Cible invalide. Valeurs acceptées : {', '.join(sorted(valid_targets))}")
            return 1
        ok = validator.run_test(args.test)
        return 0 if ok else 1

    if args.run_all:
        ok = validator.run_full_sequence()
        return 0 if ok else 1

    # Par défaut : afficher le statut
    validator.print_status()
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
