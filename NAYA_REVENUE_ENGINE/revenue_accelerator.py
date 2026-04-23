"""
NAYA V19 — REVENUE ACCELERATOR
Orchestrateur haute performance pour atteindre 60K€+ en 72h.

Stratégie:
  H+0  → Scan 9 secteurs + Polynésie → 50-100 prospects qualifiés
  H+1  → Multi-LLM voting → 20-30 emails irrésistibles générés
  H+2  → Gmail OAuth2 → envoi automatique + alertes Telegram
  H+6  → Suivi ouvertures → relance prioritaire sur ouvreurs
  H+12 → 2ème vague (nouveaux prospects, nouveaux secteurs)
  H+24 → 3ème vague + follow-up J+1 sur non-répondants
  H+48 → Analyse conversion → optimiser offres perdantes
  H+72 → Rapport complet + pipeline clos

Ce module est le CHEF D'ORCHESTRE qui:
  1. Lance les scrapers en parallèle
  2. Score et priorise les prospects
  3. Génère les emails avec vote multi-LLM
  4. Envoie et alerte Telegram
  5. Suit et relance automatiquement
  6. Mesure et optimise en temps réel

Objectif réaliste 72h:
  - 200+ prospects contactés
  - 20-30 réponses positives (10-15%)
  - 5-10 deals fermés (25-30% conversion)
  - 5 deals × 10K€ moyen = 50-100K€
"""

import os
import time
import json
import logging
import threading
from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

log = logging.getLogger("NAYA.ACCELERATOR")


def _gs(key: str, default: str = "") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(key, default) or default
    except Exception:
        return os.environ.get(key, default)


class RevenueAccelerator:
    """
    Orchestrateur haute performance pour génération de revenus accélérée.
    Utilise TOUS les composants V10 en synergie.
    """

    # Secteurs prioritaires ordonnés par potentiel cash rapide
    PRIORITY_SECTORS = [
        ("regional_market", "your_region"),        # Marché de proximité — avantage terrain
        ("liberal_professions", "Paris"),      # ROI élevé, décision rapide
        ("startup_scaleup", "Paris"),          # Budget disponible, urgence réelle
        ("pme_b2b", "Lyon"),                   # Volume + récurrence
        ("healthcare_wellness", "Marseille"),  # Douleur forte, peu de concurrence
        ("ecommerce", "France"),               # ROAS, conversion mesurable
        ("artisan_trades", "Toulouse"),        # Impayés = cash immédiat
        ("restaurant_food", "Bordeaux"),       # Marge = récurrent
        ("regional_market", "your_city"),         # 2ème ville Polynésie
    ]

    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stats = {
            "started_at": None,
            "prospects_found": 0,
            "emails_sent": 0,
            "responses_received": 0,
            "deals_won": 0,
            "revenue_eur": 0.0,
            "cycles": 0,
        }
        self._init_components()

    def _init_components(self):
        """Initialise tous les composants avec fallback."""
        self._voting_engine = None
        self._gmail_sender = None
        self._tg_bot = None
        self._pipeline = None
        self._regional_scraper = None
        self._web_scraper = None

        try:
            from NAYA_CORE.execution.multi_llm_voting import get_voting_engine
            self._voting_engine = get_voting_engine()
            log.info(f"[Accelerator] VotingEngine: {self._voting_engine.provider_count} providers")
        except Exception as e:
            log.debug(f"[Accelerator] VotingEngine: {e}")

        try:
            from NAYA_CORE.integrations.gmail_oauth2 import get_gmail_sender
            self._gmail_sender = get_gmail_sender()
            log.info(f"[Accelerator] Gmail: {self._gmail_sender.get_stats()['active_channel']}")
        except Exception as e:
            log.debug(f"[Accelerator] Gmail: {e}")

        try:
            from NAYA_CORE.integrations.telegram_bot_handler import get_telegram_bot
            self._tg_bot = get_telegram_bot()
            if self._tg_bot.available:
                log.info("[Accelerator] Telegram Bot: actif")
        except Exception as e:
            log.debug(f"[Accelerator] TG Bot: {e}")

        try:
            from NAYA_REVENUE_ENGINE.pipeline_tracker import PipelineTracker
            self._pipeline = PipelineTracker()
        except Exception as e:
            log.debug(f"[Accelerator] Pipeline: {e}")

        try:
            from NAYA_REVENUE_ENGINE.regional_scraper import get_regional_scraper
            self._regional_scraper = get_regional_scraper()
            log.info("[Accelerator] Regional scraper: actif")
        except Exception as e:
            log.debug(f"[Accelerator] Regional: {e}")

        try:
            from NAYA_REVENUE_ENGINE.web_scraper import get_web_scraper
            self._web_scraper = get_web_scraper()
        except Exception as e:
            log.debug(f"[Accelerator] WebScraper: {e}")

        # Attacher le pipeline au bot Telegram
        if self._tg_bot and self._pipeline:
            self._tg_bot._pipeline = self._pipeline

    def start_72h_blitz(self):
        """
        Lance le mode BLITZ 72h pour objectif 60K€.
        Scan intensif toutes les 30 minutes.
        """
        if self._running:
            log.warning("[Accelerator] Blitz déjà en cours")
            return

        self._running = True
        self._stats["started_at"] = datetime.now(timezone.utc).isoformat()

        # Démarrer le Telegram polling
        if self._tg_bot:
            self._tg_bot.start_polling()

        # Notification de démarrage
        self._notify(
            "🚀 <b>NAYA BLITZ 72H LANCÉ</b>\n\n"
            "Objectif: 60 000€+ en 72 heures\n"
            f"Secteurs: {len(self.PRIORITY_SECTORS)}\n"
            f"LLM: {self._voting_engine.provider_count if self._voting_engine else 0} providers\n"
            f"Email: {self._gmail_sender.get_stats()['active_channel'] if self._gmail_sender else 'N/A'}\n\n"
            "⚡ Chasse lancée maintenant..."
        )

        self._thread = threading.Thread(
            target=self._blitz_loop,
            name="NAYA-BLITZ-72H",
            daemon=True
        )
        self._thread.start()
        log.info("[Accelerator] 🚀 BLITZ 72H DÉMARRÉ")

    def stop(self):
        self._running = False
        if self._tg_bot:
            self._tg_bot.stop_polling()

    def _blitz_loop(self):
        """Boucle principale du blitz 72h."""
        scan_interval = int(os.environ.get("NAYA_REVENUE_SCAN_INTERVAL", "1800"))

        while self._running:
            try:
                results = self.run_accelerated_cycle()
                self._stats["cycles"] += 1
                self._stats["prospects_found"] += results.get("prospects_found", 0)
                self._stats["emails_sent"] += results.get("emails_sent", 0)
                self._stats["revenue_eur"] += results.get("deals_value", 0)

                log.info(
                    f"[Accelerator] Cycle {self._stats['cycles']}: "
                    f"{results.get('prospects_found', 0)} prospects, "
                    f"{results.get('emails_sent', 0)} emails, "
                    f"{results.get('deals_value', 0):,.0f}€ pipeline"
                )
            except Exception as e:
                log.error(f"[Accelerator] Blitz loop: {e}")

            for _ in range(scan_interval):
                if not self._running:
                    break
                time.sleep(1)

    def run_accelerated_cycle(self) -> Dict:
        """
        Un cycle complet accéléré:
        1. Scraping parallèle (tous secteurs simultanément)
        2. Vote multi-LLM sur les CRITICAL/HIGH
        3. Envoi email immédiat
        4. Alerte Telegram
        """
        results = {
            "cycle_ts": datetime.now(timezone.utc).isoformat(),
            "prospects_found": 0,
            "emails_sent": 0,
            "alerts_sent": 0,
            "deals_value": 0.0,
            "actions": [],
        }

        # Phase 1: Scraping parallèle
        all_prospects = self._parallel_scrape()
        results["prospects_found"] = len(all_prospects)

        if not all_prospects:
            return results

        # Phase 2: Filtrer CRITICAL/HIGH uniquement
        priority_prospects = [
            p for p in all_prospects
            if p.priority in ("CRITICAL", "HIGH")
        ][:10]  # Max 10 par cycle pour rester rapide

        # Phase 3: Pour chaque prospect prioritaire
        for prospect in priority_prospects:
            try:
                action_result = self._process_priority_prospect(prospect)
                results["emails_sent"] += 1 if action_result.get("email_sent") else 0
                results["alerts_sent"] += 1 if action_result.get("telegram_sent") else 0
                results["deals_value"] += prospect.offer_price_eur
                results["actions"].append(action_result)
            except Exception as e:
                log.debug(f"[Accelerator] Prospect {prospect.company_name}: {e}")

        return results

    def _parallel_scrape(self) -> List:
        """Lance tous les scrapers en parallèle."""
        all_prospects = []

        def scrape_sector(sector_city_tuple):
            sector, city = sector_city_tuple
            prospects = []

            # Polynésie en priorité
            if sector == "regional_market" and self._regional_scraper:
                try:
                    pf_prospects = self._regional_scraper.find_prospects(None, 5, city)
                    for pf in pf_prospects:
                        std_p = pf.to_prospect()
                        prospects.append(std_p)
                except Exception as e:
                    log.debug(f"[Accelerator] Regional {city}: {e}")

            # Autres secteurs via web scraper
            elif self._web_scraper:
                try:
                    raw = self._web_scraper.find_real_prospects(sector, 5, city)
                    from NAYA_REVENUE_ENGINE.prospect_finder_v10 import ProspectFinderV10
                    finder = ProspectFinderV10()
                    for r in raw:
                        if not r.get("company_name"):
                            continue
                        import hashlib
                        pid = hashlib.md5(f"{r['company_name']}_{city}".encode()).hexdigest()[:10]
                        from NAYA_REVENUE_ENGINE.prospect_finder import Prospect
                        p = Prospect(
                            id=f"ACC_{pid.upper()}",
                            company_name=r["company_name"],
                            sector=sector,
                            city=city,
                            email=r.get("email", ""),
                            phone=r.get("phone", ""),
                            website=r.get("website", ""),
                            source=r.get("source", "accelerator"),
                        )
                        p = finder._enrich_with_pain(p)
                        prospects.append(p)
                except Exception as e:
                    log.debug(f"[Accelerator] WebScraper {sector}/{city}: {e}")

            return prospects

        # Lancer en parallèle (max 5 threads)
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(scrape_sector, sector_city): sector_city
                for sector_city in self.PRIORITY_SECTORS[:6]
            }
            for future in as_completed(futures, timeout=60):
                try:
                    prospects = future.result()
                    all_prospects.extend(prospects)
                except Exception as e:
                    log.debug(f"[Accelerator] Parallel scrape: {e}")

        # Dédupliquer et trier par score
        seen = set()
        unique = []
        for p in all_prospects:
            key = p.company_name.lower().strip()
            if key and key not in seen:
                seen.add(key)
                unique.append(p)

        unique.sort(key=lambda x: x.solvability_score, reverse=True)
        return unique

    def _process_priority_prospect(self, prospect) -> Dict:
        """
        Traite un prospect prioritaire de bout en bout.
        Génère l'email avec vote multi-LLM + envoie + alerte Telegram.
        """
        result = {
            "company": prospect.company_name,
            "sector": prospect.sector,
            "price": prospect.offer_price_eur,
            "email_sent": False,
            "telegram_sent": False,
            "email_method": "none",
        }

        # Vérifier doublon pipeline
        if self._pipeline:
            existing = {v.get("company", "").lower() for v in self._pipeline.all()}
            if prospect.company_name.lower() in existing:
                result["skipped"] = "duplicate"
                return result

        # Construire l'offre
        offer = {
            "price": prospect.offer_price_eur,
            "title": prospect.offer_title,
            "delivery_hours": prospect.offer_delivery_hours,
            "irrefutable_logic": (
                f"{prospect.company_name} perd {prospect.pain_annual_cost_eur:,.0f}€/an. "
                f"Notre intervention à {prospect.offer_price_eur:,.0f}€ = ROI "
                f"×{round(prospect.pain_annual_cost_eur/max(prospect.offer_price_eur,1),1)}"
            ),
        }

        # Générer email avec vote multi-LLM si dispo
        email_content = {"subject": "", "body": "", "provider": "fallback"}

        if self._voting_engine and self._voting_engine.available:
            prospect_data = {
                "company": prospect.company_name,
                "contact_name": prospect.contact_name,
                "sector": prospect.sector,
                "pain_category": prospect.pain_category,
                "pain_annual_cost": prospect.pain_annual_cost_eur,
                "city": prospect.city,
            }
            email_content = self._voting_engine.generate_voted_email(prospect_data, offer)
        else:
            # Fallback template
            pain = prospect.pain_category.replace("_", " ")
            monthly = round(prospect.pain_annual_cost_eur / 12)
            email_content = {
                "subject": f"Question sur {pain} chez {prospect.company_name}",
                "body": (
                    f"Bonjour,\n\n"
                    f"{prospect.company_name} perd ~{monthly:,.0f}€/mois à cause de {pain}.\n\n"
                    f"Notre solution à {prospect.offer_price_eur:,.0f}€ résout ça définitivement "
                    f"(ROI ×{round(prospect.pain_annual_cost_eur/max(prospect.offer_price_eur,1),1)}).\n\n"
                    f"10 minutes pour vérifier si ça s'applique chez vous ?\n\n"
                    f"Bien à vous,\nNAYA SUPREME"
                ),
                "provider": "fallback",
            }

        # Ajouter au pipeline
        pid = "unknown"
        if self._pipeline:
            pid = self._pipeline.add(prospect, offer["price"])

        # Alerte Telegram avec boutons actionnables
        import uuid
        approval_id = f"APR_{uuid.uuid4().hex[:8].upper()}"
        if self._tg_bot and self._tg_bot.available:
            # Enregistrer le brouillon pour approbation
            draft = {
                "id": approval_id,
                "prospect_id": pid,
                "company": prospect.company_name,
                "email": prospect.email,
                "offer_price": offer["price"],
                "draft_subject": email_content.get("subject", ""),
                "draft_body": email_content.get("body", ""),
                "llm_used": email_content.get("provider", "fallback") != "fallback",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self._tg_bot.register_approval(approval_id, draft)

            # Envoyer l'alerte Telegram
            icon = "🔴" if prospect.priority == "CRITICAL" else "🟠"
            llm_badge = f"🧠{email_content.get('provider', '?')}" if email_content.get("provider") != "fallback" else "⚙️"
            pain = prospect.pain_category.replace("_", " ")
            monthly = round(prospect.pain_annual_cost_eur / 12)

            text = (
                f"{icon} <b>{prospect.priority} — {offer['price']:,.0f}€</b> {llm_badge}\n\n"
                f"🏢 <b>{prospect.company_name}</b> ({prospect.city})\n"
                f"📧 {prospect.email or 'email à trouver'}\n\n"
                f"💔 {pain}\n"
                f"💸 {monthly:,.0f}€/mois perdus ({prospect.pain_annual_cost_eur:,.0f}€/an)\n"
                f"💰 Offre: <b>{offer['price']:,.0f}€</b> "
                f"— ROI ×{round(prospect.pain_annual_cost_eur/max(offer['price'],1),1)}\n\n"
                f"<b>📧 Objet proposé:</b>\n<i>{email_content.get('subject','')[:80]}</i>"
            )
            buttons = [[
                {"text": f"✅ Envoyer email", "callback_data": f"approve:{approval_id}"},
                {"text": f"💳 PayPal {offer['price']:.0f}€", "callback_data": f"paypal:{pid}:{offer['price']:.0f}"},
            ], [
                {"text": "❌ Ignorer", "callback_data": f"skip:{pid}"},
                {"text": "📋 Pipeline", "callback_data": "pipeline:all"},
            ]]
            tg_sent = self._tg_bot.send(text, buttons)
            result["telegram_sent"] = tg_sent

            # Mode AUTO: envoyer directement si configuré
            auto_send = os.environ.get("NAYA_AUTO_OUTREACH", "false").lower() == "true"
            if auto_send and prospect.email and self._gmail_sender:
                body_html = f"<p>{email_content.get('body','').replace(chr(10),'<br>')}</p>"
                send_result = self._gmail_sender.send(
                    to_email=prospect.email,
                    subject=email_content.get("subject", ""),
                    body_html=body_html,
                    body_text=email_content.get("body", ""),
                    to_name=prospect.contact_name,
                )
                result["email_sent"] = send_result.get("sent", False)
                result["email_method"] = send_result.get("method", "unknown")

                if result["email_sent"] and self._pipeline:
                    self._pipeline.update_status(pid, "CONTACTED", f"Auto-envoi: {result['email_method']}")

        return result

    def _notify(self, text: str, buttons: List = None):
        """Notification Telegram."""
        if self._tg_bot and self._tg_bot.available:
            self._tg_bot.send(text, buttons)

    def get_stats(self) -> Dict:
        stats = dict(self._stats)
        stats["running"] = self._running

        # Ajouter stats des composants
        if self._voting_engine:
            stats["voting_engine"] = self._voting_engine.get_stats()
        if self._gmail_sender:
            stats["gmail"] = self._gmail_sender.get_stats()
        if self._pipeline:
            try:
                stats["pipeline"] = self._pipeline.get_kpis()
            except Exception:
                pass

        # Calculer vitesse
        if stats.get("started_at"):
            start = datetime.fromisoformat(stats["started_at"])
            elapsed_h = (datetime.now(timezone.utc) - start).total_seconds() / 3600
            if elapsed_h > 0:
                stats["prospects_per_hour"] = round(stats["prospects_found"] / elapsed_h, 1)
                stats["emails_per_hour"] = round(stats["emails_sent"] / elapsed_h, 1)
                stats["revenue_per_day"] = round(stats["revenue_eur"] / max(elapsed_h / 24, 0.01), 0)
                stats["projected_72h"] = round(stats["revenue_per_day"] * 3, 0)

        return stats

    def send_72h_report(self):
        """Envoie un rapport de performance 72h sur Telegram."""
        stats = self.get_stats()
        pipeline = stats.get("pipeline", {})

        self._notify(
            f"📊 <b>RAPPORT BLITZ 72H — NAYA V19</b>\n\n"
            f"👥 Prospects trouvés: <b>{stats['prospects_found']}</b>\n"
            f"📧 Emails envoyés: <b>{stats['emails_sent']}</b>\n"
            f"💰 Pipeline total: <b>{pipeline.get('pipeline_eur', 0):,.0f}€</b>\n"
            f"✅ Won: <b>{pipeline.get('revenue_won_eur', 0):,.0f}€</b>\n"
            f"📈 Taux conv: {pipeline.get('conversion_rate', 0):.1f}%\n\n"
            f"🔄 Cycles: {stats['cycles']}\n"
            f"⚡ LLM: {stats.get('voting_engine', {}).get('provider_count', 0)} providers\n\n"
            f"<b>Projection sur 72h: {stats.get('projected_72h', 0):,.0f}€</b>"
        )


# ── Singleton ────────────────────────────────────────────────────────────────

_ACCELERATOR: Optional[RevenueAccelerator] = None


def get_accelerator() -> RevenueAccelerator:
    global _ACCELERATOR
    if _ACCELERATOR is None:
        _ACCELERATOR = RevenueAccelerator()
    return _ACCELERATOR
