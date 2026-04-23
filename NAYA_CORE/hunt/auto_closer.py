"""
NAYA V19 — Auto-Closer Engine
═══════════════════════════════════════════════════════════════════════
Convertit automatiquement les opportunités détectées en offres envoyées.

Flux :
  1. Récupère les top opps du GlobalPainHunter (score ≥ 0.4)
  2. Enrichit les contacts (Apollo → Hunter → Pattern)
  3. Génère l'offre personnalisée via LLM (Groq ou Anthropic)
  4. Envoie l'email cold via Gmail OAuth ou SendGrid
  5. Crée le lien PayPal/Deblock pré-rempli
  6. Alerte Telegram avec le lien + suivi pipeline
  7. Programme les relances automatiques (J+2, J+5, J+10)

OBJECTIF : 1 offre envoyée toutes les 2-4 heures automatiquement
═══════════════════════════════════════════════════════════════════════
"""
import os, time, json, logging, threading, uuid
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass, field

log = logging.getLogger("NAYA.AUTO_CLOSER")


def _gs(k: str, d: str = "") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(k, d) or d
    except Exception:
        return os.environ.get(k, d)


@dataclass
class CloserJob:
    job_id: str
    opportunity_id: str
    company: str
    domain: str
    email: str
    offer_title: str
    offer_price: float
    payment_url: str = ""
    email_sent: bool = False
    telegram_alerted: bool = False
    followup_scheduled: bool = False
    created_at: float = field(default_factory=time.time)
    status: str = "pending"


DATA_FILE = Path("data/cache/auto_closer_jobs.json")


class AutoCloser:
    """
    Moteur de closing automatique.
    Tournée toutes les 2h pour convertir les opps en offres réelles.
    """

    def __init__(self):
        self._jobs: List[CloserJob] = []
        self._lock = threading.RLock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._total_offers = 0
        self._total_sent = 0
        self._total_pipeline_value = 0.0
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    def process_opportunity(self, opp: Dict) -> Optional[CloserJob]:
        """Traite une opportunité : enrichit → offre → envoi."""
        job_id = f"JOB_{uuid.uuid4().hex[:8].upper()}"
        log.info(f"[CLOSER] Processing {opp.get('company', '?')} ({opp.get('value', 0):.0f}€)")

        # 1. Enrichissement contact
        email = opp.get("email", "")
        contact_name = opp.get("contact_name", "")
        domain = opp.get("domain", "")

        if not email and domain:
            email, contact_name = self._enrich_contact(opp)

        if not email:
            # Pas d'email = alerter Telegram pour action manuelle
            self._alert_manual_action(opp)
            return None

        # 2. Générer l'offre
        offer = self._generate_offer(opp, contact_name)
        price = offer.get("price", opp.get("value", 3000))

        # 3. Créer lien paiement
        payment_url = self._create_payment_link(price, offer.get("title", "Service NAYA"), contact_name)

        # 4. Envoyer email
        sent = self._send_offer_email(
            email=email,
            contact_name=contact_name,
            company=opp.get("company", ""),
            offer=offer,
            payment_url=payment_url,
        )

        # 5. Créer job de suivi
        job = CloserJob(
            job_id=job_id,
            opportunity_id=opp.get("id", ""),
            company=opp.get("company", ""),
            domain=domain,
            email=email,
            offer_title=offer.get("title", ""),
            offer_price=price,
            payment_url=payment_url,
            email_sent=sent,
            status="sent" if sent else "enriched",
        )

        with self._lock:
            self._jobs.append(job)
            self._total_offers += 1
            if sent:
                self._total_sent += 1
                self._total_pipeline_value += price

        # 6. Alerte Telegram
        self._alert_telegram_offer(job, sent)

        # 7. Programmer relances si envoyé
        if sent:
            self._schedule_followups(job)

        self._save()
        return job

    def _enrich_contact(self, opp: Dict) -> tuple:
        """Enrichit le contact via Apollo ou Hunter.io."""
        try:
            from NAYA_CORE.enrichment.contact_enricher import get_contact_enricher
            enricher = get_contact_enricher()
            result = enricher.enrich(
                company=opp.get("company", ""),
                url=f"https://{opp.get('domain', '')}",
                sector=opp.get("category", ""),
            )
            if result.is_valid:
                log.info(f"[CLOSER] Contact enrichi: {result.email} (conf={result.confidence:.0%})")
                return result.email, result.decision_maker_name
        except Exception as e:
            log.debug(f"[CLOSER] Enrichment error: {e}")

        # Fallback : email générique entreprise
        domain = opp.get("domain", "")
        if domain and "." in domain:
            for pattern in ["contact", "info", "direction"]:
                generic = f"{pattern}@{domain}"
                log.debug(f"[CLOSER] Using generic email: {generic}")
                return generic, ""

        return "", ""

    def _generate_offer(self, opp: Dict, contact_name: str) -> Dict:
        """Génère une offre personnalisée via LLM."""
        try:
            from NAYA_CORE.execution.llm_router import LLMRouter
            router = LLMRouter()

            pain_type = opp.get("pain_type", opp.get("category", "service digital"))
            company = opp.get("company", "votre entreprise")
            value_min = opp.get("value_min", 1500)
            value_max = opp.get("value_max", 10000)
            price = max(1000, opp.get("value", 3000))

            prompt = f"""Tu es NAYA, expert en business automation. Génère une offre commerciale B2B.

Entreprise cible : {company}
Problème détecté : {opp.get("description", pain_type)[:200]}
Type de douleur : {pain_type}
Budget estimé : {value_min}€ à {value_max}€
Prix proposé : {price:.0f}€

Génère un titre d'offre court (max 10 mots) et une accroche email d'une phrase.
Format JSON: {{"title": "...", "hook": "..."}}"""

            result = router.route(prompt, task_type="offer_generation", max_tokens=200)

            # Parse JSON response
            import re
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return {
                    "title": data.get("title", f"Automatisation {pain_type}"),
                    "hook": data.get("hook", f"Solution pour optimiser votre {pain_type}"),
                    "price": price,
                    "pain_type": pain_type,
                }
        except Exception as e:
            log.debug(f"[CLOSER] LLM offer generation: {e}")

        # Fallback templates par type de douleur
        templates = {
            "automatisation": ("Automatisation de vos processus manuels en 48H", 3000),
            "ia_service_client": ("Chatbot IA pour votre service client — 0 recrutement", 2500),
            "visibilite_digitale": ("Audit digital + refonte site web en 72H", 1500),
            "marche_public": ("Dossier réponse appel d'offres clé en main", 5000),
            "ecommerce_optimisation": ("Optimisation e-commerce + récupération paniers abandonnés", 2000),
            "afrique_digital": ("Solution digitale complète sur mesure", 8000),
            "rh_talent": ("Stratégie recrutement & marque employeur", 4000),
        }
        pain_type = opp.get("pain_type", "automatisation")
        title, price = templates.get(pain_type, ("Solution sur mesure en 72H", opp.get("value", 3000)))

        return {"title": title, "hook": f"Nous avons détecté une opportunité pour {opp.get('company', 'votre entreprise')}.", "price": price, "pain_type": pain_type}

    def _create_payment_link(self, amount: float, description: str, client_name: str = "") -> str:
        """Crée un lien PayPal pré-rempli."""
        try:
            from NAYA_REVENUE_ENGINE.payment_engine import get_payment_engine
            engine = get_payment_engine()
            result = engine.create_payment_link(amount, description, client_name=client_name)
            return result.get("url", "")
        except Exception as e:
            log.debug(f"[CLOSER] Payment link error: {e}")
            # Fallback PayPal.me direct
            paypal_url = _gs("PAYPAL_ME_URL", "https://www.paypal.me/Myking987")
            return f"{paypal_url.rstrip('/')}/{amount:.2f}"

    def _send_offer_email(self, email: str, contact_name: str, company: str,
                           offer: Dict, payment_url: str) -> bool:
        """Envoie l'email d'offre via Gmail OAuth ou SendGrid."""
        subject = f"🎯 {offer.get('title', 'Proposition commerciale')} — {company}"

        greeting = f"Bonjour {contact_name}," if contact_name else "Bonjour,"

        body_html = f"""
<p>{greeting}</p>

<p>{offer.get('hook', 'Nous avons identifié une opportunité pour votre entreprise.')}</p>

<p><strong>Notre proposition : {offer.get('title', 'Solution sur mesure')}</strong></p>

<p>✅ Livraison rapide — résultats mesurables dès les premières 72H<br>
✅ Prix fixe transparent — aucune surprise<br>
✅ Paiement simple et sécurisé</p>

<p>
  <a href="{payment_url}" style="background:#0070ba;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:bold;">
    💳 ACCÉDER À L'OFFRE — {offer.get('price', 3000):.0f}€
  </a>
</p>

<p>Des questions ? Répondez directement à cet email — je vous réponds sous 2H.</p>

<p>Cordialement,<br>
<strong>Équipe NAYA</strong><br>
📧 contact@nayabot.online<br>
🌐 Solution livrée en 48-72H garantis</p>
"""

        # Essayer Gmail OAuth en premier
        try:
            from NAYA_REVENUE_ENGINE.gmail_outreach import send_email
            result = send_email(to=email, subject=subject, html_body=body_html)
            if result.get("sent"):
                log.info(f"[CLOSER] Gmail → {email}: OK")
                return True
        except Exception as e:
            log.debug(f"[CLOSER] Gmail error: {e}")

        # Fallback SendGrid
        try:
            from NAYA_CORE.integrations.sendgrid_integration import get_sendgrid
            sg = get_sendgrid()
            result = sg.send_email(
                to_email=email,
                to_name=contact_name or company,
                subject=subject,
                html_content=body_html,
            )
            if result.get("sent"):
                log.info(f"[CLOSER] SendGrid → {email}: OK")
                return True
        except Exception as e:
            log.debug(f"[CLOSER] SendGrid error: {e}")

        log.warning(f"[CLOSER] Email non envoyé pour {email} — alerting Telegram")
        return False

    def _alert_telegram_offer(self, job: CloserJob, sent: bool):
        """Alerte Telegram avec l'état du deal."""
        try:
            from NAYA_CORE.integrations.telegram_notifier import get_notifier
            notifier = get_notifier()
            status_emoji = "✅" if sent else "⚠️"
            notifier.send(
                f"{status_emoji} <b>OFFRE {'ENVOYÉE' if sent else 'PRÊTE (email manquant)'}</b>\n\n"
                f"🏢 {job.company}\n"
                f"💰 {job.offer_price:,.0f}€\n"
                f"📧 {job.email or 'email à trouver'}\n"
                f"📋 {job.offer_title}\n\n"
                f"🔗 Lien paiement: {job.payment_url}\n"
                f"🆔 Job: {job.job_id}"
            )
        except Exception:
            pass

    def _alert_manual_action(self, opp: Dict):
        """Alerte Telegram pour action manuelle (pas d'email trouvé)."""
        try:
            from NAYA_CORE.integrations.telegram_notifier import get_notifier
            notifier = get_notifier()
            notifier.send(
                f"📋 <b>ACTION MANUELLE REQUISE</b>\n\n"
                f"🏢 {opp.get('company', '?')}\n"
                f"💰 Valeur: {opp.get('value', 0):,.0f}€\n"
                f"🔗 Source: {opp.get('source_url', '')[:80]}\n\n"
                f"👉 Trouver le contact manuellement et créer l'offre\n"
                f"Répondre /close {opp.get('id', '')} pour clôturer"
            )
        except Exception:
            pass

    def _schedule_followups(self, job: CloserJob):
        """Programme les relances automatiques J+2, J+5, J+10."""
        try:
            from NAYA_REVENUE_ENGINE.followup_sequence_engine import get_followup_engine
            engine = get_followup_engine()
            engine.create_sequence(
                prospect_email=job.email,
                prospect_name=job.company,
                offer_title=job.offer_title,
                offer_price=job.offer_price,
                payment_url=job.payment_url,
                intervals_days=[2, 5, 10],
            )
            job.followup_scheduled = True
            log.info(f"[CLOSER] Relances programmées pour {job.company} (J+2, J+5, J+10)")
        except Exception as e:
            log.debug(f"[CLOSER] Followup schedule error: {e}")

    # ── Auto-cycle ───────────────────────────────────────────────────────────

    def run_cycle(self):
        """Un cycle complet : récupère les opps et les ferme."""
        try:
            from NAYA_CORE.hunt.global_pain_hunter import get_global_hunter
            hunter = get_global_hunter()
            top_opps = hunter.get_top_opportunities(n=10, min_score=0.4)
        except Exception as e:
            log.warning(f"[CLOSER] Hunter unavailable: {e}")
            return

        processed_ids = {j.opportunity_id for j in self._jobs}
        new_opps = [o for o in top_opps if o["id"] not in processed_ids][:3]  # Max 3/cycle

        for opp in new_opps:
            try:
                self.process_opportunity(opp)
                time.sleep(10)  # Pause entre chaque traitement
            except Exception as e:
                log.error(f"[CLOSER] Error processing {opp.get('company', '?')}: {e}")

        log.info(f"[CLOSER] Cycle: {len(new_opps)} opps traitées | Total pipeline: {self._total_pipeline_value:,.0f}€")

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, name="NAYA-AutoCloser", daemon=True)
        self._thread.start()
        log.info("[CLOSER] Auto-Closer V19 started")

    def stop(self):
        self._running = False

    def _loop(self):
        time.sleep(120)  # Attendre que le hunter ait des données
        while self._running:
            try:
                self.run_cycle()
            except Exception as e:
                log.error(f"[CLOSER] Loop error: {e}")
            time.sleep(int(os.getenv("NAYA_CLOSER_INTERVAL", "7200")))  # 2h défaut

    # ── Stats & Persistence ──────────────────────────────────────────────────

    def get_stats(self) -> Dict:
        with self._lock:
            sent = [j for j in self._jobs if j.email_sent]
            return {
                "total_jobs": len(self._jobs),
                "offers_sent": len(sent),
                "total_pipeline_eur": round(self._total_pipeline_value, 0),
                "avg_offer_eur": round(self._total_pipeline_value / max(len(sent), 1), 0),
                "running": self._running,
            }

    def _save(self):
        try:
            data = [
                {
                    "id": j.job_id, "opp_id": j.opportunity_id,
                    "company": j.company, "email": j.email,
                    "price": j.offer_price, "sent": j.email_sent,
                    "status": j.status, "payment_url": j.payment_url,
                }
                for j in self._jobs[-200:]
            ]
            DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        except Exception:
            pass

    def _load(self):
        try:
            if DATA_FILE.exists():
                data = json.loads(DATA_FILE.read_text())
                log.info(f"[CLOSER] Loaded {len(data)} historical jobs")
        except Exception:
            pass


# ── Singleton ────────────────────────────────────────────────────────────────

_closer: Optional[AutoCloser] = None
_closer_lock = threading.Lock()


def get_auto_closer() -> AutoCloser:
    global _closer
    if _closer is None:
        with _closer_lock:
            if _closer is None:
                _closer = AutoCloser()
    return _closer
