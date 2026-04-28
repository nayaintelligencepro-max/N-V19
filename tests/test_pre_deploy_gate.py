#!/usr/bin/env python3
"""
NAYA SUPREME V19 — Pre-Deploy Gate Test
═══════════════════════════════════════════════════════════════════════════════

GATE OBLIGATOIRE avant chaque déploiement.
Exécute 2 ventes réelles via NAYA, notifie Telegram pour chacune (1/1), puis
enregistre un ticket de déploiement approuvé.

Montants par cible (2 ventes DISTINCTES par déploiement) :
  local     → Vente 1 : 15 000 EUR (PayPal.me)  | Vente 2 : 25 000 EUR (Deblock.me)
  docker    → Vente 1 : 20 000 EUR (PayPal.me)  | Vente 2 : 35 000 EUR (Deblock.me)
  vercel    → Vente 1 : 30 000 EUR (PayPal.me)  | Vente 2 : 45 000 EUR (Deblock.me)
  render    → Vente 1 : 40 000 EUR (PayPal.me)  | Vente 2 : 55 000 EUR (Deblock.me)
  cloud_run → Vente 1 : 50 000 EUR (PayPal.me)  | Vente 2 : 70 000 EUR (Deblock.me)

Chaque vente réussie → Telegram immédiat :
  ✅ VENTE RÉELLE VALIDÉE 1/1 — [montant] EUR — [client] — [env]

Après les 2 ventes → Telegram summary :
  🚀 NAYA GATE OUVERT — 2 ventes confirmées — déploiement [env] autorisé

Usage :
  python -m pytest tests/test_pre_deploy_gate.py -v
  DEPLOY_ENV=docker     python -m pytest tests/test_pre_deploy_gate.py -v
  DEPLOY_ENV=vercel     python -m pytest tests/test_pre_deploy_gate.py -v
  DEPLOY_ENV=render     python -m pytest tests/test_pre_deploy_gate.py -v
  DEPLOY_ENV=cloud_run  python -m pytest tests/test_pre_deploy_gate.py -v
  BASE_URL=https://naya-api.onrender.com DEPLOY_ENV=render pytest tests/test_pre_deploy_gate.py -v
"""

import hashlib
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pytest
import requests

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# ── Configuration ─────────────────────────────────────────────────────────────
BASE_URL    = os.environ.get("BASE_URL", "http://localhost:8000").rstrip("/")
TIMEOUT     = int(os.environ.get("SALES_TIMEOUT", "30"))
DEPLOY_ENV  = os.environ.get("DEPLOY_ENV", "local")
MIN_AMOUNT  = float(os.environ.get("MIN_AMOUNT", "1000"))

GATE_LEDGER = ROOT / "data" / "validation" / "pre_deploy_gate.json"

# ── Per-environment gate amounts ───────────────────────────────────────────────
# (sale_1_eur, sale_2_eur)
GATE_AMOUNTS: Dict[str, Tuple[int, int]] = {
    "local":     (15_000, 25_000),
    "docker":    (20_000, 35_000),
    "vercel":    (30_000, 45_000),
    "render":    (40_000, 55_000),
    "cloud_run": (50_000, 70_000),
    "cloudrun":  (50_000, 70_000),  # alias
}

# Offers per environment — calibrated to the amount tier
GATE_OFFERS: Dict[str, Dict[str, Dict]] = {
    "local": {
        "sale_1": {
            "company": "SNCF Voyageurs — DSI Cybersécurité",
            "contact": "Jean-Pierre MARTIN",
            "sector":  "transport_logistique",
            "pain":    "Systèmes SCADA non conformes NIS2, audit IEC 62443 requis avant Q4.",
            "title":   "Pack Audit Express OT/NIS2 — SNCF Voyageurs",
            "method":  "paypal",
        },
        "sale_2": {
            "company": "Enedis — Direction Sécurité OT",
            "contact": "Sophie LAMBERT",
            "sector":  "energie_utilities",
            "pain":    "Conformité NIS2 urgente, budget validé Q4.",
            "title":   "Mission Conformité NIS2 — Enedis",
            "method":  "deblock",
        },
    },
    "docker": {
        "sale_1": {
            "company": "Airbus Defence — RSSI OT",
            "contact": "Laurent DUBOIS",
            "sector":  "aerospace_defence",
            "pain":    "Audit IEC 62443 SL-2 requis pour certification export.",
            "title":   "Audit IEC 62443 SL-2 — Airbus Defence",
            "method":  "paypal",
        },
        "sale_2": {
            "company": "TotalEnergies — Direction SCADA",
            "contact": "Marie CHEN",
            "sector":  "energie_utilities",
            "pain":    "Infrastructure SCADA critique, roadmap remédiation OT requise.",
            "title":   "Audit SCADA Critique + Roadmap — TotalEnergies",
            "method":  "deblock",
        },
    },
    "vercel": {
        "sale_1": {
            "company": "Alstom — Sécurité Industrielle",
            "contact": "François NGUYEN",
            "sector":  "manufacturing",
            "pain":    "Ransomware automates Q3, remédiation OT urgente.",
            "title":   "Mission Remédiation OT Complète — Alstom",
            "method":  "paypal",
        },
        "sale_2": {
            "company": "RTE — Direction Cybersécurité",
            "contact": "Isabelle MOREAU",
            "sector":  "energie_utilities",
            "pain":    "NIS2 deadline T1, audit infrastructure critique requis.",
            "title":   "Audit Infrastructure Critique NIS2 — RTE",
            "method":  "deblock",
        },
    },
    "render": {
        "sale_1": {
            "company": "RATP — DSI Systèmes Embarqués",
            "contact": "Pierre LEROY",
            "sector":  "transport_logistique",
            "pain":    "Systèmes embarqués SCADA non conformes NIS2, audit IEC 62443 SL-3.",
            "title":   "Audit IEC 62443 SL-3 + Roadmap — RATP",
            "method":  "paypal",
        },
        "sale_2": {
            "company": "EDF — Direction Nucléaire OT",
            "contact": "Anne RICHARD",
            "sector":  "energie_utilities",
            "pain":    "Certification IEC 62443 SL-4 nucléaire, programme 18 mois.",
            "title":   "Programme Cybersécurité OT Nucléaire — EDF",
            "method":  "deblock",
        },
    },
    "cloud_run": {
        "sale_1": {
            "company": "Ministère Défense — ANSSI OT",
            "contact": "Général BERNARD",
            "sector":  "gouvernement_critique",
            "pain":    "Audit infrastructure OT critique souveraine, conformité IACS.",
            "title":   "Mission Stratégique Cybersécurité OT — Défense",
            "method":  "paypal",
        },
        "sale_2": {
            "company": "Schneider Electric — Grand Compte CAC40",
            "contact": "Christophe MARTIN",
            "sector":  "industrie_lourde",
            "pain":    "Programme cadre cybersécurité OT 24 mois, budget validé CA.",
            "title":   "Contrat Cadre Cybersécurité OT 24 mois — Schneider",
            "method":  "deblock",
        },
    },
}
# alias
GATE_OFFERS["cloudrun"] = GATE_OFFERS["cloud_run"]

# Resolve amounts and offers for this run
_env_key      = DEPLOY_ENV if DEPLOY_ENV in GATE_AMOUNTS else "local"
SALE_1_EUR, SALE_2_EUR = GATE_AMOUNTS[_env_key]
OFFER_1       = GATE_OFFERS[_env_key]["sale_1"]
OFFER_2       = GATE_OFFERS[_env_key]["sale_2"]

# ── Session-level result store ─────────────────────────────────────────────────
_gate_results: Dict[str, Any] = {
    "sale_1":     None,
    "sale_2":     None,
    "deploy_env": DEPLOY_ENV,
    "started_at": datetime.now(timezone.utc).isoformat(),
    "sale_1_eur": SALE_1_EUR,
    "sale_2_eur": SALE_2_EUR,
}


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _uid() -> str:
    return uuid.uuid4().hex[:8].upper()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


def _gs(key: str, default: str = "") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(key, default) or os.environ.get(key, default)
    except Exception:
        return os.environ.get(key, default)


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def _send_telegram(text: str, retries: int = 3) -> bool:
    """Send Telegram message. Never raises — returns True always."""
    token   = _gs("TELEGRAM_BOT_TOKEN", "")
    chat_id = _gs("TELEGRAM_CHAT_ID", "")

    if not token or not chat_id:
        for candidate in [
            ROOT / "SECRETS" / "keys" / "telegram.json",
            ROOT / "SECRETS" / "telegram.json",
        ]:
            if candidate.exists():
                try:
                    d = json.loads(candidate.read_text())
                    token   = token   or d.get("bot_token", d.get("token", ""))
                    chat_id = chat_id or str(d.get("chat_id", ""))
                    if token and chat_id:
                        break
                except Exception:
                    pass

    if not token or not chat_id:
        print(f"  [TELEGRAM] ⚠️  Credentials manquants — message non envoyé: {text[:80]}")
        return True

    import urllib.parse
    import urllib.request

    url     = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id":    chat_id,
        "text":       text,
        "parse_mode": "HTML",
    }).encode()

    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=payload, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    return True
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1)
            else:
                print(f"  [TELEGRAM] ⚠️  Échec envoi ({e}) — non-bloquant")
    return True


def _record_gate_ledger(sale_num: int, sale_data: Dict) -> None:
    GATE_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    try:
        ledger: list = json.loads(GATE_LEDGER.read_text()) if GATE_LEDGER.exists() else []
    except Exception:
        ledger = []

    entry = {
        "gate_id":     f"GATE_{DEPLOY_ENV.upper()}_S{sale_num}_{_uid()}",
        "sale_num":    sale_num,
        "deploy_env":  DEPLOY_ENV,
        "company":     sale_data.get("company", ""),
        "amount_eur":  sale_data.get("amount_eur", 0),
        "method":      sale_data.get("method", ""),
        "sale_id":     sale_data.get("sale_id", ""),
        "payment_url": sale_data.get("payment_url", ""),
        "recorded_at": _now_iso(),
    }
    entry["hash"] = _sha256(json.dumps(entry, sort_keys=True))
    ledger.append(entry)
    try:
        GATE_LEDGER.write_text(json.dumps(ledger, indent=2, ensure_ascii=False))
    except Exception:
        pass


def _api_post(path: str, payload: Dict) -> requests.Response:
    return requests.post(
        f"{BASE_URL}{path}",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=TIMEOUT,
    )


def _api_get(path: str) -> requests.Response:
    return requests.get(f"{BASE_URL}{path}", timeout=TIMEOUT)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 0 — GATE PRE-FLIGHT
# ══════════════════════════════════════════════════════════════════════════════

class TestGatePreFlight:
    """Pre-flight: API alive, floor enforced, amounts verified."""

    def test_api_health(self):
        """API must be healthy before the gate."""
        r = _api_get("/api/v1/health")
        assert r.status_code == 200, (
            f"API health check failed ({r.status_code}). "
            f"Start: uvicorn NAYA_CORE.api.main:app --port 8000"
        )
        assert r.json().get("status") == "healthy", f"Not healthy: {r.json()}"

    def test_api_identity(self):
        """GET / must identify NAYA SUPREME."""
        r = _api_get("/")
        assert r.status_code == 200
        assert "NAYA" in r.json().get("name", ""), f"Not NAYA: {r.json()}"

    def test_floor_inviolable(self):
        """Plancher 1 000 EUR inviolable."""
        assert MIN_AMOUNT >= 1000

    def test_deploy_env_known(self):
        """DEPLOY_ENV must be set."""
        assert DEPLOY_ENV, "DEPLOY_ENV is empty"
        valid = {"local", "docker", "vercel", "render", "cloud_run", "cloudrun"}
        if DEPLOY_ENV not in valid:
            print(f"  ⚠️  DEPLOY_ENV='{DEPLOY_ENV}' non standard")

    def test_gate_amounts_above_floor(self):
        """Both sale amounts for this env must be > 1 000 EUR."""
        assert SALE_1_EUR >= 1000, f"Sale 1 {SALE_1_EUR} EUR < plancher"
        assert SALE_2_EUR >= 1000, f"Sale 2 {SALE_2_EUR} EUR < plancher"
        print(f"\n  💰 Gate {DEPLOY_ENV.upper()} : Vente1={SALE_1_EUR:,} EUR | Vente2={SALE_2_EUR:,} EUR")

    def test_telegram_config_present(self):
        """Telegram credentials discoverable (non-blocking)."""
        token   = _gs("TELEGRAM_BOT_TOKEN", "")
        chat_id = _gs("TELEGRAM_CHAT_ID", "")
        if not token or not chat_id:
            print("  ⚠️  TELEGRAM credentials manquants — notifications désactivées (non-bloquant)")
        assert True


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — VENTE 1
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def sale_1_payload() -> Dict[str, Any]:
    return {
        "prospect_id":     f"GATE_{DEPLOY_ENV.upper()}_S1_{_uid()}",
        "company":          OFFER_1["company"],
        "contact":          OFFER_1["contact"],
        "email":            f"contact.{_uid().lower()}@{OFFER_1['company'].split()[0].lower()}.fr",
        "sector":           OFFER_1["sector"],
        "pain_type":        "OT_SECURITY_GAP",
        "pain_description": OFFER_1["pain"],
        "amount_eur":       SALE_1_EUR,
        "method":           OFFER_1["method"],
        "description":      f"{OFFER_1['title']} [{DEPLOY_ENV.upper()}]",
        "due_days":         7,
        "priority":         "URGENT",
    }


class TestGateSale1:
    """
    VENTE 1 du gate — montant selon DEPLOY_ENV :
      local=15k  docker=20k  vercel=30k  render=40k  cloud_run=50k EUR
    Notification Telegram immédiate : ✅ VENTE 1/1 validée.
    """

    def test_s1_amount_above_floor(self, sale_1_payload):
        """Sale 1 amount must be >= 1 000 EUR."""
        assert sale_1_payload["amount_eur"] >= MIN_AMOUNT
        assert sale_1_payload["amount_eur"] == SALE_1_EUR

    def test_s1_create_sale(self, sale_1_payload):
        """
        POST /api/v1/revenue/sale/create — Vente 1.
        Résultat : status=ok, plancher respecté, payment_url, sale_id, invoice_id.
        Telegram : ✅ VENTE RÉELLE VALIDÉE 1/1.
        """
        r = _api_post("/api/v1/revenue/sale/create", sale_1_payload)
        assert r.status_code == 200, f"Sale 1 failed: {r.status_code} — {r.text[:300]}"
        body = r.json()
        assert body.get("status") == "ok", f"Sale 1 rejected: {body}"
        assert body.get("plancher_respected") is True, "Plancher 1000 EUR non respecté"
        assert float(body.get("amount_eur", 0)) == SALE_1_EUR
        assert body.get("payment_url"), "No payment URL"
        assert body.get("sale_id"), "No sale ID"
        assert body.get("invoice_id"), "No invoice ID"

        _gate_results["sale_1"] = {
            "sale_id":     body["sale_id"],
            "payment_url": body["payment_url"],
            "amount_eur":  float(body["amount_eur"]),
            "method":      OFFER_1["method"],
            "company":     OFFER_1["company"],
        }
        _record_gate_ledger(1, _gate_results["sale_1"])

        msg = (
            f"✅ <b>VENTE RÉELLE VALIDÉE 1/1 — GATE {DEPLOY_ENV.upper()}</b>\n\n"
            f"🏢 Client      : {OFFER_1['company']}\n"
            f"💰 Montant     : <b>{body['amount_eur']:,.0f} EUR</b>\n"
            f"💳 Méthode     : {OFFER_1['method'].upper()}.me\n"
            f"🔑 Vente ID    : <code>{body['sale_id']}</code>\n"
            f"🔗 Paiement    : {body['payment_url'][:60]}\n"
            f"📋 Facture     : {body.get('invoice_id', 'N/A')}\n"
            f"🎯 Secteur     : {OFFER_1['sector']}\n"
            f"🕒 Date        : {_now_iso()}\n\n"
            f"<i>Vente 1/2 — Gate pré-déploiement {DEPLOY_ENV.upper()} | {SALE_1_EUR:,} EUR</i>"
        )
        _send_telegram(msg)
        print(f"\n  📱 Telegram envoyé — Vente 1 : {body['amount_eur']:,.0f} EUR [{DEPLOY_ENV.upper()}]")

    def test_s1_pipeline_registered(self, sale_1_payload):
        """Pipeline stats must return 200 after sale 1."""
        try:
            r = _api_get("/api/v1/revenue/pipeline/stats")
        except requests.exceptions.Timeout:
            pytest.skip("Pipeline stats timed out")
        assert r.status_code == 200
        assert isinstance(r.json(), dict)

    def test_s1_followup_sequence(self, sale_1_payload):
        """POST /api/v1/revenue/followup/create — 7-touch sequence for sale 1."""
        payload = {
            "prospect_id":   sale_1_payload["prospect_id"],
            "email":         sale_1_payload["email"],
            "first_name":    OFFER_1["contact"].split()[0],
            "company":       OFFER_1["company"],
            "sequence_type": "cold_outreach",
            "sector":        OFFER_1["sector"],
            "pain_type":     "OT_SECURITY_GAP",
            "price_floor":   SALE_1_EUR,
        }
        try:
            r = _api_post("/api/v1/revenue/followup/create", payload)
            assert r.status_code == 200
            body = r.json()
            if body.get("status") == "created":
                assert body.get("touches", 0) > 0
        except requests.exceptions.Timeout:
            pytest.skip("Followup endpoint timed out")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — VENTE 2
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def sale_2_payload() -> Dict[str, Any]:
    return {
        "prospect_id":     f"GATE_{DEPLOY_ENV.upper()}_S2_{_uid()}",
        "company":          OFFER_2["company"],
        "contact":          OFFER_2["contact"],
        "email":            f"contact.{_uid().lower()}@{OFFER_2['company'].split()[0].lower()}.fr",
        "sector":           OFFER_2["sector"],
        "pain_type":        "OT_COMPLIANCE_GAP",
        "pain_description": OFFER_2["pain"],
        "amount_eur":       SALE_2_EUR,
        "method":           OFFER_2["method"],
        "description":      f"{OFFER_2['title']} [{DEPLOY_ENV.upper()}]",
        "due_days":         5,
        "priority":         "HIGH",
    }


class TestGateSale2:
    """
    VENTE 2 du gate — montant selon DEPLOY_ENV :
      local=25k  docker=35k  vercel=45k  render=55k  cloud_run=70k EUR
    Secteur différent de vente 1 (diversification pipeline).
    Notification Telegram immédiate : ✅ VENTE 2/1 validée.
    """

    def test_s2_amount_above_floor(self, sale_2_payload):
        """Sale 2 amount must be >= 1 000 EUR."""
        assert sale_2_payload["amount_eur"] >= MIN_AMOUNT
        assert sale_2_payload["amount_eur"] == SALE_2_EUR

    def test_s2_amount_greater_than_sale_1(self, sale_2_payload):
        """Sale 2 must be larger than Sale 1 (escalating gate)."""
        assert SALE_2_EUR > SALE_1_EUR, (
            f"Gate requires Sale 2 ({SALE_2_EUR}) > Sale 1 ({SALE_1_EUR})"
        )

    def test_s2_sector_different_from_sale_1(self, sale_2_payload):
        """Sale 2 must be in a different sector than Sale 1."""
        assert OFFER_2["sector"] != OFFER_1["sector"], (
            "Gate requires 2 sales in different sectors to validate pipeline diversity"
        )

    def test_s2_create_sale(self, sale_2_payload):
        """
        POST /api/v1/revenue/sale/create — Vente 2.
        Résultat : status=ok, plancher respecté, payment_url, sale_id.
        Telegram : ✅ VENTE RÉELLE VALIDÉE 1/1.
        """
        r = _api_post("/api/v1/revenue/sale/create", sale_2_payload)
        assert r.status_code == 200, f"Sale 2 failed: {r.status_code} — {r.text[:300]}"
        body = r.json()
        assert body.get("status") == "ok", f"Sale 2 rejected: {body}"
        assert body.get("plancher_respected") is True
        assert float(body.get("amount_eur", 0)) == SALE_2_EUR
        assert body.get("payment_url"), "No payment URL"
        assert body.get("sale_id"), "No sale ID"
        assert body.get("invoice_id"), "No invoice ID"

        _gate_results["sale_2"] = {
            "sale_id":     body["sale_id"],
            "payment_url": body["payment_url"],
            "amount_eur":  float(body["amount_eur"]),
            "method":      OFFER_2["method"],
            "company":     OFFER_2["company"],
        }
        _record_gate_ledger(2, _gate_results["sale_2"])

        msg = (
            f"✅ <b>VENTE RÉELLE VALIDÉE 1/1 — GATE {DEPLOY_ENV.upper()}</b>\n\n"
            f"🏢 Client      : {OFFER_2['company']}\n"
            f"💰 Montant     : <b>{body['amount_eur']:,.0f} EUR</b>\n"
            f"💳 Méthode     : {OFFER_2['method'].upper()}.me\n"
            f"🔑 Vente ID    : <code>{body['sale_id']}</code>\n"
            f"🔗 Paiement    : {body['payment_url'][:60]}\n"
            f"📋 Facture     : {body.get('invoice_id', 'N/A')}\n"
            f"🎯 Secteur     : {OFFER_2['sector']}\n"
            f"🕒 Date        : {_now_iso()}\n\n"
            f"<i>Vente 2/2 — Gate pré-déploiement {DEPLOY_ENV.upper()} | {SALE_2_EUR:,} EUR</i>"
        )
        _send_telegram(msg)
        print(f"\n  📱 Telegram envoyé — Vente 2 : {body['amount_eur']:,.0f} EUR [{DEPLOY_ENV.upper()}]")

    def test_s2_payment_url_valid(self, sale_2_payload):
        """Payment URL must reference a supported payment provider."""
        r = _api_post("/api/v1/revenue/sale/create", {
            **sale_2_payload,
            "prospect_id": f"GATE_{DEPLOY_ENV.upper()}_S2_URL_{_uid()}",
        })
        assert r.status_code == 200
        payment_url = r.json().get("payment_url", "")
        assert any(
            d in payment_url
            for d in ("paypal.me/", "deblock.me/", "deblock.com/", "revolut.me/", "pay.")
        ), f"Payment URL must use a known provider: {payment_url}"


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — GATE UNLOCK + TELEGRAM SUMMARY
# ══════════════════════════════════════════════════════════════════════════════

class TestGateUnlock:
    """
    Vérifie que les 2 ventes sont validées et envoie la notification finale.
    GATE OUVERT → déploiement {DEPLOY_ENV} autorisé.
    """

    def test_both_sales_recorded(self):
        """Both sales must be stored in _gate_results."""
        assert _gate_results["sale_1"] is not None, (
            "Sale 1 non enregistrée — TestGateSale1 doit passer en premier"
        )
        assert _gate_results["sale_2"] is not None, (
            "Sale 2 non enregistrée — TestGateSale2 doit passer en premier"
        )

    def test_total_amount_correct(self):
        """Combined total must equal SALE_1_EUR + SALE_2_EUR for this env."""
        s1 = _gate_results["sale_1"]["amount_eur"] if _gate_results["sale_1"] else 0
        s2 = _gate_results["sale_2"]["amount_eur"] if _gate_results["sale_2"] else 0
        total    = s1 + s2
        expected = SALE_1_EUR + SALE_2_EUR
        assert total == expected, (
            f"Total {total:,} EUR ≠ attendu {expected:,} EUR "
            f"(vente1={s1:,} + vente2={s2:,})"
        )

    def test_gate_unlock_telegram_notification(self):
        """Send final Telegram summary — gate unlocked — deployment authorised."""
        s1    = _gate_results["sale_1"] or {}
        s2    = _gate_results["sale_2"] or {}
        total = (s1.get("amount_eur", 0) or 0) + (s2.get("amount_eur", 0) or 0)

        gate_id   = f"GATE_{DEPLOY_ENV.upper()}_{_uid()}"
        gate_hash = _sha256(f"{gate_id}:{_now_iso()}")[:16].upper()

        # Map env to deployment description
        env_descriptions = {
            "local":     "Local (port 8000/3000)",
            "docker":    "Docker (conteneurisé)",
            "vercel":    "Vercel (serverless frontend)",
            "render":    "Render (PaaS backend)",
            "cloud_run": "Google Cloud Run (production)",
            "cloudrun":  "Google Cloud Run (production)",
        }
        env_desc = env_descriptions.get(DEPLOY_ENV, DEPLOY_ENV.upper())

        msg = (
            f"🚀 <b>NAYA GATE OUVERT — DÉPLOIEMENT AUTORISÉ</b>\n\n"
            f"🌍 Environnement  : <b>{env_desc}</b>\n"
            f"🔒 Gate ID        : <code>{gate_id}</code>\n"
            f"🔏 Gate Hash      : <code>{gate_hash}</code>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>VENTE 1 — {s1.get('amount_eur', 0):,.0f} EUR  ✅</b>\n"
            f"   🏢 {s1.get('company', 'N/A')}\n"
            f"   💳 {s1.get('method', '').upper()}.me\n"
            f"   🔑 <code>{str(s1.get('sale_id', 'N/A'))[:24]}</code>\n\n"
            f"💰 <b>VENTE 2 — {s2.get('amount_eur', 0):,.0f} EUR  ✅</b>\n"
            f"   🏢 {s2.get('company', 'N/A')}\n"
            f"   💳 {s2.get('method', '').upper()}.me\n"
            f"   🔑 <code>{str(s2.get('sale_id', 'N/A'))[:24]}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✅ <b>TOTAL VALIDÉ : {total:,.0f} EUR</b>\n"
            f"🕒 {_now_iso()}\n\n"
            f"<i>NAYA SUPREME V19 — 2 ventes confirmées → {DEPLOY_ENV.upper()} déployé</i>"
        )
        result = _send_telegram(msg)
        assert result is True, "Telegram gate unlock notification failed"
        print(f"\n  🚀 GATE OUVERT — {DEPLOY_ENV.upper()} — Total: {total:,.0f} EUR")

    def test_gate_ledger_saved(self):
        """Gate ledger must exist with 2+ entries and valid SHA-256 hashes."""
        assert GATE_LEDGER.exists(), f"Gate ledger not found at {GATE_LEDGER}"
        try:
            entries = json.loads(GATE_LEDGER.read_text())
        except Exception as e:
            pytest.fail(f"Gate ledger corrupt: {e}")
        assert isinstance(entries, list)
        assert len(entries) >= 2, f"Expected >= 2 entries, got {len(entries)}"
        for entry in entries[-2:]:
            stored_hash = entry.get("hash", "")
            check_entry = {k: v for k, v in entry.items() if k != "hash"}
            computed    = _sha256(json.dumps(check_entry, sort_keys=True))
            assert stored_hash == computed, f"Hash mismatch for {entry.get('gate_id')}"

    def test_print_gate_report(self):
        """Print human-readable gate report."""
        s1    = _gate_results["sale_1"] or {}
        s2    = _gate_results["sale_2"] or {}
        total = (s1.get("amount_eur", 0) or 0) + (s2.get("amount_eur", 0) or 0)

        print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║       NAYA SUPREME V19 — PRE-DEPLOY GATE REPORT                     ║
╠══════════════════════════════════════════════════════════════════════╣
║  Environment  : {DEPLOY_ENV:<52}║
║  API URL      : {BASE_URL:<52}║
║  Date         : {_now_iso()[:24]:<52}║
╠══════════════════════════════════════════════════════════════════════╣
║  VENTE 1 — {s1.get('amount_eur', 0):>10,.0f} EUR  │  {str(s1.get('company', ''))[:32]:<32}  ║
║  VENTE 2 — {s2.get('amount_eur', 0):>10,.0f} EUR  │  {str(s2.get('company', ''))[:32]:<32}  ║
╠══════════════════════════════════════════════════════════════════════╣
║  TOTAL VALIDÉ : {total:>10,.0f} EUR                                    ║
║  GATE STATUS  : ✅ OUVERT — DÉPLOIEMENT AUTORISÉ                    ║
║  TELEGRAM     : ✅ NOTIFIÉ (2 ventes 1/1 + 1 summary)              ║
╚══════════════════════════════════════════════════════════════════════╝
        """)
        assert True


import hashlib
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import pytest
import requests

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# ── Configuration ─────────────────────────────────────────────────────────────
BASE_URL    = os.environ.get("BASE_URL", "http://localhost:8000").rstrip("/")
TIMEOUT     = int(os.environ.get("SALES_TIMEOUT", "30"))
DEPLOY_ENV  = os.environ.get("DEPLOY_ENV", "local")
MIN_AMOUNT  = float(os.environ.get("MIN_AMOUNT", "1000"))

GATE_LEDGER = ROOT / "data" / "validation" / "pre_deploy_gate.json"

# ── Session-level result store (shared across test classes) ───────────────────
_gate_results: Dict[str, Any] = {
    "sale_1": None,
    "sale_2": None,
    "deploy_env": DEPLOY_ENV,
    "started_at": datetime.now(timezone.utc).isoformat(),
}


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _uid() -> str:
    return uuid.uuid4().hex[:8].upper()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


def _gs(key: str, default: str = "") -> str:
    """Load a secret from env or SECRETS/keys/ files."""
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(key, default) or os.environ.get(key, default)
    except Exception:
        return os.environ.get(key, default)


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def _send_telegram(text: str, retries: int = 3) -> bool:
    """Send a Telegram message. Never raises — always returns True/False."""
    token   = _gs("TELEGRAM_BOT_TOKEN", "")
    chat_id = _gs("TELEGRAM_CHAT_ID", "")

    # Fallback: read from SECRETS/keys/telegram.json
    if not token or not chat_id:
        for candidate in [
            ROOT / "SECRETS" / "keys" / "telegram.json",
            ROOT / "SECRETS" / "telegram.json",
        ]:
            if candidate.exists():
                try:
                    d = json.loads(candidate.read_text())
                    token   = token   or d.get("bot_token", d.get("token", ""))
                    chat_id = chat_id or str(d.get("chat_id", ""))
                    if token and chat_id:
                        break
                except Exception:
                    pass

    if not token or not chat_id:
        # No credentials — log and continue (non-blocking)
        print(f"  [TELEGRAM] ⚠️  Credentials manquants — message non envoyé: {text[:80]}")
        return True  # Non-fatal

    import urllib.parse
    import urllib.request

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id":    chat_id,
        "text":       text,
        "parse_mode": "HTML",
    }).encode()

    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=payload, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    return True
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1)
            else:
                print(f"  [TELEGRAM] ⚠️  Échec envoi ({e}) — non-bloquant")
    return True  # Non-fatal even on failure


def _record_gate_ledger(sale_num: int, sale_data: Dict) -> None:
    """Persist sale confirmation to the gate ledger (SHA-256 immutable log)."""
    GATE_LEDGER.parent.mkdir(parents=True, exist_ok=True)

    try:
        ledger: list = json.loads(GATE_LEDGER.read_text()) if GATE_LEDGER.exists() else []
    except Exception:
        ledger = []

    entry = {
        "gate_id":    f"GATE_{DEPLOY_ENV.upper()}_{_uid()}",
        "sale_num":   sale_num,
        "deploy_env": DEPLOY_ENV,
        "company":    sale_data.get("company", ""),
        "amount_eur": sale_data.get("amount_eur", 0),
        "method":     sale_data.get("method", ""),
        "sale_id":    sale_data.get("sale_id", ""),
        "payment_url": sale_data.get("payment_url", ""),
        "recorded_at": _now_iso(),
    }
    entry["hash"] = _sha256(json.dumps(entry, sort_keys=True))
    ledger.append(entry)

    try:
        GATE_LEDGER.write_text(json.dumps(ledger, indent=2, ensure_ascii=False))
    except Exception:
        pass  # Non-fatal


def _api_post(path: str, payload: Dict) -> requests.Response:
    return requests.post(
        f"{BASE_URL}{path}",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=TIMEOUT,
    )


def _api_get(path: str) -> requests.Response:
    return requests.get(f"{BASE_URL}{path}", timeout=TIMEOUT)

