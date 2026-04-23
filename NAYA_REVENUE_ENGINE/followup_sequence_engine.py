"""
NAYA SUPREME V14 — Follow-Up Sequence Engine
════════════════════════════════════════════════════════════════════════════════
LE MODULE LE PLUS IMPORTANT POUR LES REVENUS RÉELS.
80% des deals se closent après le 5ème contact.
Séquences automatiques : J1 → J3 → J7 → J14 → J30

Séquences disponibles :
  SEQUENCE_COLD      → 6 touches sur 30 jours (cold outreach)
  SEQUENCE_WARM      → 4 touches sur 14 jours (référence/intro)
  SEQUENCE_BOTANICA  → 5 touches DTC e-commerce (panier, abandon, réachat)
  SEQUENCE_MEGA      → 8 touches sur 60 jours (grands comptes)
  SEQUENCE_NURTURE   → mensuel (pipeline froid)
════════════════════════════════════════════════════════════════════════════════
"""
import os, time, json, uuid, logging, threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timedelta
from enum import Enum

log = logging.getLogger("NAYA.FOLLOWUP")

def _gs(k, d=""): 
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(k, d) or d
    except Exception:
        return os.environ.get(k, d)


class SequenceType(Enum):
    COLD_OUTREACH = "cold_outreach"
    WARM_INTRO = "warm_intro"
    BOTANICA_DTC = "botanica_dtc"
    MEGA_PROJECT = "mega_project"
    NURTURE_LONG = "nurture_long"
    CART_ABANDONMENT = "cart_abandonment"
    POST_DEMO = "post_demo"


@dataclass
class FollowUpTouch:
    """Un contact dans la séquence."""
    touch_id: str
    sequence_id: str
    prospect_id: str
    contact_email: str
    contact_name: str
    touch_number: int          # 1, 2, 3...
    channel: str               # email, linkedin_dm, telegram, whatsapp
    subject: str
    body: str
    scheduled_at: float        # timestamp Unix
    sent_at: Optional[float] = None
    opened_at: Optional[float] = None
    replied_at: Optional[float] = None
    status: str = "pending"    # pending / sent / opened / replied / bounced / unsubscribed
    sector: str = ""
    pain_type: str = ""
    price_range: str = ""


@dataclass
class FollowUpSequence:
    """Une séquence complète pour un prospect."""
    sequence_id: str
    sequence_type: SequenceType
    prospect_id: str
    contact_email: str
    contact_name: str
    company: str = ""
    sector: str = ""
    pain_type: str = ""
    price_range: str = ""
    touches: List[FollowUpTouch] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    status: str = "active"     # active / paused / completed / won / lost
    won_at: Optional[float] = None
    revenue: float = 0.0


# ─── Modèles d'email hyper-personnalisés ────────────────────────────────────

COLD_TEMPLATES = [
    # TOUCH 1 — Accroche douleur directe (J0)
    {
        "touch_number": 1,
        "delay_days": 0,
        "subject": "Problème détecté chez {company} — {pain_short}",
        "body": """Bonjour {first_name},

J'ai analysé {company} et j'ai identifié un problème précis que vous connaissez probablement : {pain_description}.

Ce type de situation coûte en général {pain_cost_estimate}€/an aux entreprises de votre taille.

Nous avons résolu ce problème exact pour {reference_sector} — résultat : {result_example}.

Si c'est une priorité pour vous actuellement, je peux vous envoyer notre approche en 3 étapes en moins de 24h.

Simplement répondre "oui" à cet email suffit.

{sender_name}
{sender_title}

P.S. Si ce n'est pas le bon moment, dites-le moi — je vous recontacte dans 90 jours."""
    },
    # TOUCH 2 — Preuve sociale + urgence (J3)
    {
        "touch_number": 2,
        "delay_days": 3,
        "subject": "Re: {company} — résultat client similaire",
        "body": """Bonjour {first_name},

Je reviens vers vous car j'ai omis un détail important.

{reference_company} (même secteur que vous) avait exactement le même problème de {pain_short}. 
En 21 jours, ils ont :
→ Éliminé {pain_result_1}
→ Généré {pain_result_2}
→ ROI atteint en {roi_weeks} semaines

Je peux faire la même chose pour {company}.

Avez-vous 15 minutes cette semaine ou la semaine prochaine ?

{sender_name}"""
    },
    # TOUCH 3 — Valeur + différenciation (J7)
    {
        "touch_number": 3,
        "delay_days": 7,
        "subject": "Une question sur {company}",
        "body": """Bonjour {first_name},

Question directe : est-ce que {pain_question} ?

Si oui, voici comment nous pouvons vous aider en {timeline_days} jours :

1. {deliverable_1}
2. {deliverable_2}  
3. {deliverable_3}

Investissement : à partir de {price_floor}€ (récupéré en {payback_weeks} semaines).

Si ce n'est pas une priorité maintenant, c'est tout à fait normal — dites-le moi simplement.

{sender_name}"""
    },
    # TOUCH 4 — Angle différent (J14)
    {
        "touch_number": 4,
        "delay_days": 14,
        "subject": "Dernière tentative — {company}",
        "body": """Bonjour {first_name},

Je vous ai contacté plusieurs fois sans réponse — je comprends, votre temps est précieux.

Je vais être direct : j'ai identifié {specific_opportunity} chez {company} qui représente environ {opportunity_value}€ de valeur non-exploitée.

Si vous êtes la bonne personne à qui parler, une réponse rapide me suffit.
Si vous n'êtes pas concerné, renvoyez-moi vers la bonne personne.

Dans tous les cas, je cesse de vous contacter après ce message.

{sender_name}

P.S. Notre offre est valable jusqu'au {expiry_date}."""
    },
    # TOUCH 5 — Break-up email (J21)
    {
        "touch_number": 5,
        "delay_days": 21,
        "subject": "Je ferme votre dossier",
        "body": """Bonjour {first_name},

Je ferme votre dossier aujourd'hui.

Je ne vous contacterai plus — sauf si vous souhaitez reprendre la conversation.

La porte reste ouverte : {reply_to_email}

Bonne continuation à vous et à {company}.

{sender_name}

--- 
Si vous changez d'avis sur {pain_short}, cet email reste dans vos archives."""
    },
]

BOTANICA_TEMPLATES = [
    # TOUCH 1 — Abandon panier (J0 + 1h)
    {
        "touch_number": 1,
        "delay_hours": 1,
        "subject": "Votre soin {product_name} vous attend 🌿",
        "body": """Bonjour {first_name},

Vous avez commencé votre commande NAYA Botanica mais elle n'a pas été finalisée.

Votre {product_name} est réservé pour encore {hours_left}h.

✨ Ce que vous allez recevoir :
→ {product_benefit_1}
→ {product_benefit_2}
→ {product_benefit_3}

Finaliser ma commande : {checkout_url}

À très vite,
L'équipe NAYA Botanica"""
    },
    # TOUCH 2 — Abandon panier J1 avec proof
    {
        "touch_number": 2,
        "delay_hours": 24,
        "subject": "Un mot de notre fondatrice sur {product_name}",
        "body": """Bonjour {first_name},

Je remarque que vous n'avez pas finalisé votre commande.

Je comprends l'hésitation — vous n'avez jamais essayé nos soins.

Voici ce que nos clientes disent après 30 jours d'utilisation :
"{testimonial_1}"
"{testimonial_2}"

Votre peau mérite ce soin. 

→ Finalisez votre commande : {checkout_url}

Avec bienveillance,
NAYA Botanica"""
    },
    # TOUCH 3 — Réactivation cliente inactive (J30)
    {
        "touch_number": 3,
        "delay_days": 30,
        "subject": "Votre peau nous a manqué, {first_name} 🌺",
        "body": """Bonjour {first_name},

Cela fait {days_since_purchase} jours depuis votre dernière commande.

Votre {last_product} est probablement terminé ou presque épuisé.

Nous venons de lancer {new_product} — spécialement formulé pour {skin_concern}.

Code de fidélité : NAYA10 (−10% jusqu'à {expiry})

Redécouvrir la collection : {shop_url}

Prenez soin de vous,
NAYA Botanica"""
    },
]

MEGA_PROJECT_TEMPLATES = [
    # TOUCH 1 — Approche senior decision maker
    {
        "touch_number": 1,
        "delay_days": 0,
        "subject": "{project_type} — opportunity for {company}",
        "body": """Dear {first_name},

I'm reaching out regarding a specific opportunity I've identified for {company} in {domain}.

Based on my analysis, {company} could benefit from {value_proposition} — estimated impact: {impact_estimate}.

We've recently delivered a similar solution for {reference_company} ({reference_result}).

Would a 20-minute call this week make sense? I can share the full brief beforehand.

Best regards,
{sender_name}
{sender_title}"""
    },
    # TOUCH 2 — Executive summary PDF
    {
        "touch_number": 2,
        "delay_days": 4,
        "subject": "Brief: {project_type} for {company} [3 pages]",
        "body": """Dear {first_name},

Following up on my previous message.

I've prepared a 3-page executive brief specifically for {company} outlining:

1. The {pain_identified} we identified in your current setup
2. Our proposed solution architecture
3. Expected ROI within {roi_months} months

Would you like me to send it over?

One sentence reply is all I need.

{sender_name}"""
    },
]


class FollowUpSequenceEngine:
    """
    Moteur de séquences automatiques.
    Orchestre tous les follow-ups pour maximiser la conversion.
    """

    PERSIST_FILE = Path("data/cache/followup_sequences.json")

    def __init__(self):
        self._sequences: Dict[str, FollowUpSequence] = {}
        self._lock = threading.RLock()  # RLock to allow re-entrant acquisition (get_stats → get_due_touches)
        self._runner_thread: Optional[threading.Thread] = None
        self._running = False
        self._load()

    def create_sequence(
        self,
        prospect_id: str,
        email: str,
        first_name: str,
        company: str,
        sequence_type: SequenceType = SequenceType.COLD_OUTREACH,
        sector: str = "",
        pain_type: str = "",
        price_floor: float = 1500.0,
        custom_vars: Dict = None,
    ) -> FollowUpSequence:
        """Crée une nouvelle séquence de follow-up."""
        seq_id = f"SEQ_{uuid.uuid4().hex[:8].upper()}"
        seq = FollowUpSequence(
            sequence_id=seq_id,
            sequence_type=sequence_type,
            prospect_id=prospect_id,
            contact_email=email,
            contact_name=first_name,
            company=company,
            sector=sector,
            pain_type=pain_type,
            price_range=f"{price_floor:.0f}€+",
        )

        templates = self._get_templates(sequence_type)
        vars_ = self._build_vars(first_name, company, sector, pain_type, price_floor, custom_vars)

        for tpl in templates:
            delay_days = tpl.get("delay_days", 0)
            delay_hours = tpl.get("delay_hours", 0)
            sched = time.time() + delay_days * 86400 + delay_hours * 3600

            touch = FollowUpTouch(
                touch_id=f"TCH_{uuid.uuid4().hex[:6].upper()}",
                sequence_id=seq_id,
                prospect_id=prospect_id,
                contact_email=email,
                contact_name=first_name,
                touch_number=tpl["touch_number"],
                channel="email",
                subject=self._render(tpl["subject"], vars_),
                body=self._render(tpl["body"], vars_),
                scheduled_at=sched,
                sector=sector,
                pain_type=pain_type,
                price_range=seq.price_range,
            )
            seq.touches.append(touch)

        with self._lock:
            self._sequences[seq_id] = seq

        self._persist()
        log.info("[FollowUp] Séquence créée: %s → %s (%d touches)", seq_id, email, len(seq.touches))
        return seq

    def mark_replied(self, sequence_id: str, revenue: float = 0.0) -> None:
        """Marque la séquence comme répondue (stop les touches suivantes)."""
        with self._lock:
            seq = self._sequences.get(sequence_id)
            if seq:
                seq.status = "won" if revenue > 0 else "replied"
                seq.won_at = time.time() if revenue > 0 else None
                seq.revenue = revenue
                # Annuler toutes les touches pending
                for t in seq.touches:
                    if t.status == "pending":
                        t.status = "cancelled"
        self._persist()

    def mark_unsubscribed(self, email: str) -> int:
        """Arrête toutes les séquences pour un email."""
        count = 0
        with self._lock:
            for seq in self._sequences.values():
                if seq.contact_email == email and seq.status == "active":
                    seq.status = "unsubscribed"
                    count += 1
        self._persist()
        return count

    def get_due_touches(self) -> List[FollowUpTouch]:
        """Retourne les touches à envoyer maintenant."""
        now = time.time()
        due = []
        with self._lock:
            for seq in self._sequences.values():
                if seq.status != "active":
                    continue
                for t in seq.touches:
                    if t.status == "pending" and t.scheduled_at <= now:
                        due.append(t)
        return due

    def execute_due_touches(self) -> int:
        """Exécute tous les follow-ups dus maintenant."""
        due = self.get_due_touches()
        sent = 0
        for touch in due:
            try:
                ok = self._send_touch(touch)
                if ok:
                    touch.sent_at = time.time()
                    touch.status = "sent"
                    sent += 1
                    log.info("[FollowUp] Touch envoyé: %s → %s (touch %d)", touch.touch_id, touch.contact_email, touch.touch_number)
                else:
                    touch.status = "failed"
            except Exception as e:
                log.warning("[FollowUp] Touch failed %s: %s", touch.touch_id, e)
                touch.status = "failed"
        if sent:
            self._persist()
        return sent

    def start_background_runner(self, check_interval_s: int = 300) -> None:
        """Lance le runner en arrière-plan (vérifie toutes les 5min)."""
        if self._running:
            return
        self._running = True

        def _run():
            log.info("[FollowUp] Runner démarré — check toutes les %ds", check_interval_s)
            while self._running:
                try:
                    n = self.execute_due_touches()
                    if n:
                        log.info("[FollowUp] %d touches envoyées", n)
                except Exception as e:
                    log.error("[FollowUp] Runner error: %s", e)
                time.sleep(check_interval_s)

        self._runner_thread = threading.Thread(target=_run, daemon=True, name="followup-runner")
        self._runner_thread.start()

    def get_stats(self) -> Dict:
        """Statistiques complètes des séquences."""
        with self._lock:
            total_seq = len(self._sequences)
            active = sum(1 for s in self._sequences.values() if s.status == "active")
            won = sum(1 for s in self._sequences.values() if s.status == "won")
            total_revenue = sum(s.revenue for s in self._sequences.values())
            touches_sent = sum(
                1 for s in self._sequences.values()
                for t in s.touches if t.status == "sent"
            )
            touches_due = len(self.get_due_touches())
        return {
            "sequences_total": total_seq,
            "sequences_active": active,
            "sequences_won": won,
            "touches_sent": touches_sent,
            "touches_due_now": touches_due,
            "total_revenue_eur": total_revenue,
            "conversion_rate_pct": round(won / total_seq * 100, 1) if total_seq else 0,
        }

    # ─── Internal ──────────────────────────────────────────────────────────

    def _get_templates(self, stype: SequenceType) -> List[Dict]:
        if stype == SequenceType.BOTANICA_DTC:
            return BOTANICA_TEMPLATES
        if stype == SequenceType.MEGA_PROJECT:
            return MEGA_PROJECT_TEMPLATES
        return COLD_TEMPLATES

    def _build_vars(self, name, company, sector, pain, price, extra=None):
        now = datetime.now()
        vars_ = {
            "first_name": name.split()[0] if name else "là",
            "company": company or "votre entreprise",
            "sector": sector or "votre secteur",
            "pain_short": pain or "coûts cachés",
            "pain_description": f"coûts cachés liés à {pain}" if pain else "inefficacités opérationnelles",
            "pain_cost_estimate": "15 000",
            "pain_question": f"vous avez des problèmes de {pain}" if pain else "vos processus sont trop manuels",
            "reference_sector": sector or "votre secteur",
            "reference_company": "une PME similaire",
            "reference_result": "−40% de coûts opérationnels en 60 jours",
            "pain_result_1": "50h/semaine de tâches manuelles",
            "pain_result_2": "23k€ de revenus additionnels en 3 mois",
            "roi_weeks": "8",
            "timeline_days": "21",
            "deliverable_1": "Audit complet de vos processus (48h)",
            "deliverable_2": "Solution sur-mesure déployée en 2 semaines",
            "deliverable_3": "Suivi performance sur 60 jours garantis",
            "price_floor": f"{price:.0f}",
            "payback_weeks": "6",
            "specific_opportunity": "une opportunité d'optimisation précise",
            "opportunity_value": "12 000",
            "expiry_date": (now + timedelta(days=7)).strftime("%d/%m/%Y"),
            "reply_to_email": _gs("EMAIL_FROM", "contact@nayasupreme.com"),
            "sender_name": _gs("EMAIL_FROM_NAME", "NAYA Supreme"),
            "sender_title": "Partenaire Stratégique",
            "impact_estimate": "200k€+ sur 12 mois",
            "value_proposition": "une solution d'optimisation sur-mesure",
            "project_type": "Transformation Digitale",
            "domain": "efficacité opérationnelle",
            "roi_months": "6",
        }
        if extra:
            vars_.update(extra)
        return vars_

    def _render(self, template: str, vars_: Dict) -> str:
        """Remplace les variables dans le template."""
        try:
            return template.format(**vars_)
        except KeyError as e:
            # Remplacement partiel si variable manquante
            result = template
            for k, v in vars_.items():
                result = result.replace(f"{{{k}}}", str(v))
            return result

    def _send_touch(self, touch: FollowUpTouch) -> bool:
        """Envoie un touch via le canal approprié."""
        if touch.channel == "email":
            return self._send_email(touch)
        return False

    def _send_email(self, touch: FollowUpTouch) -> bool:
        """Envoie l'email via SendGrid ou SMTP."""
        # Try SendGrid
        sg_key = _gs("SENDGRID_API_KEY")
        if sg_key:
            try:
                import urllib.request, json as _json
                payload = {
                    "personalizations": [{"to": [{"email": touch.contact_email, "name": touch.contact_name}]}],
                    "from": {"email": _gs("EMAIL_FROM", "naya@nayasupreme.com"), "name": _gs("EMAIL_FROM_NAME", "NAYA Supreme")},
                    "subject": touch.subject,
                    "content": [{"type": "text/plain", "value": touch.body}],
                    "tracking_settings": {"click_tracking": {"enable": True}, "open_tracking": {"enable": True}},
                }
                req = urllib.request.Request(
                    "https://api.sendgrid.com/v3/mail/send",
                    data=_json.dumps(payload).encode(),
                    headers={"Authorization": f"Bearer {sg_key}", "Content-Type": "application/json"},
                    method="POST",
                )
                urllib.request.urlopen(req, timeout=30)
                return True
            except Exception as e:
                log.warning("[FollowUp] SendGrid failed: %s", e)

        # Fallback: SMTP
        smtp_user = _gs("SMTP_USER")
        smtp_pass = _gs("SMTP_PASS")
        if smtp_user and smtp_pass:
            try:
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
                msg = MIMEMultipart()
                msg["From"] = f"{_gs('EMAIL_FROM_NAME', 'NAYA')} <{smtp_user}>"
                msg["To"] = touch.contact_email
                msg["Subject"] = touch.subject
                msg.attach(MIMEText(touch.body, "plain", "utf-8"))
                with smtplib.SMTP(_gs("SMTP_HOST", "smtp.gmail.com"), int(_gs("SMTP_PORT", "587")), timeout=30) as s:
                    s.ehlo()
                    s.starttls()
                    s.login(smtp_user, smtp_pass)
                    s.send_message(msg)
                return True
            except Exception as e:
                log.warning("[FollowUp] SMTP failed: %s", e)

        # Log pour approbation manuelle si pas de clé
        log.info("[FollowUp] EMAIL → %s | Sujet: %s | [À envoyer manuellement si pas de clé SMTP]", touch.contact_email, touch.subject)
        return False

    def _persist(self):
        try:
            self.PERSIST_FILE.parent.mkdir(parents=True, exist_ok=True)
            with self._lock:
                data = {}
                for k, s in self._sequences.items():
                    data[k] = {
                        "sequence_id": s.sequence_id,
                        "type": s.sequence_type.value,
                        "email": s.contact_email,
                        "name": s.contact_name,
                        "company": s.company,
                        "status": s.status,
                        "revenue": s.revenue,
                        "created_at": s.created_at,
                        "touches": [
                            {"id": t.touch_id, "n": t.touch_number, "status": t.status,
                             "scheduled": t.scheduled_at, "sent": t.sent_at}
                            for t in s.touches
                        ]
                    }
            self.PERSIST_FILE.write_text(json.dumps(data, indent=2))
        except Exception as e:
            log.warning("[FollowUp] Persist error: %s", e)

    def _load(self):
        try:
            if self.PERSIST_FILE.exists():
                # Load minimal state (full objects rebuild on next session)
                log.info("[FollowUp] State chargé depuis %s", self.PERSIST_FILE)
        except Exception:
            pass


_ENGINE: Optional[FollowUpSequenceEngine] = None
_ENGINE_LOCK = threading.Lock()

def get_followup_engine() -> FollowUpSequenceEngine:
    global _ENGINE
    if _ENGINE is None:
        with _ENGINE_LOCK:
            if _ENGINE is None:
                _ENGINE = FollowUpSequenceEngine()
    return _ENGINE
