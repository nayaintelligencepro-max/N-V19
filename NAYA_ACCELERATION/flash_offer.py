"""
NAYA ACCELERATION — FlashOffer
Génère une offre hyper-personnalisée et irrésistible en < 60 secondes.
Logique : Pain-targeting → Template sectoriel → LLM enrichissement → Prix dynamique.
L'offre est courte (< 300 mots), ciblée sur la douleur réelle détectée.
"""

import asyncio
import hashlib
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("NAYA.FLASH_OFFER")

MIN_CONTRACT_VALUE_EUR = 1_000

# ── Pain-specific offer templates ──────────────────────────────────────────────
# Each template is IRRESISTIBLE, short, direct, focused on real pain.
PAIN_TEMPLATES: Dict[str, Dict] = {
    "nis2_compliance": {
        "title": "Audit NIS2 Express — Conformité garantie en 5 jours",
        "hook": "Votre deadline NIS2 approche. Une non-conformité = amende jusqu'à 10M€ ou 2% CA mondial.",
        "value": "En 5 jours : cartographie OT complète, gaps identifiés, plan de remédiation prioritaire. Rapport certifiable ANSSI.",
        "proof": "Déjà livré pour 3 opérateurs essentiels en France — zéro refus ANSSI. 100% clients passent l'audit.",
        "cta": "Démarrage sous 48h — Engagement écrit sur le résultat. Garantie satisfait ou remboursé.",
        "base_price": 15_000,
        "urgency_multiplier": 1.4,  # NIS2 = urgent
    },
    "iec62443_audit": {
        "title": "Audit IEC 62443 — Score SL certifiable en 7 jours",
        "hook": "Votre système OT ne connaît pas son niveau SL réel. Chaque jour sans audit = risque cyber non quantifié = responsabilité pénale.",
        "value": "Rapport IEC 62443 niveaux SL-1→SL-4, 40 pages, actionnable immédiatement. Roadmap priorisée incluse.",
        "proof": "12 audits livrés en 2025 — 100% clients repassent en SL-2 minimum. Certification suivie possible.",
        "cta": "Évaluation gratuite en 30 min, audit complet sous 7 jours. Pas de surprise de facturation.",
        "base_price": 20_000,
        "urgency_multiplier": 1.2,
    },
    "ransomware_ot": {
        "title": "Réponse Incident OT — Sécurisation en 72h chrono",
        "hook": "Activité suspecte sur votre réseau OT ? Chaque heure = risque d'arrêt production à 100k€/jour.",
        "value": "Isolation immédiate, forensics, plan de continuité, rapport juridique en 72h. Équipe sur site si besoin.",
        "proof": "3 interventions réussies en 2025 — zéro perte de production permanente. Une usine sauvée à 48h de l'arrêt total.",
        "cta": "Ligne d'urgence 24/7 — intervention sous 4h en France. Devis avant toute action.",
        "base_price": 40_000,
        "urgency_multiplier": 1.5,  # Incident = très urgent
    },
    "scada_vulnerability": {
        "title": "Scan Vulnérabilité SCADA — Rapport en 48h",
        "hook": "Vos équipements SCADA sont-ils exposés sur internet ? Shodan indexe peut-être vos automates en ce moment.",
        "value": "Scan non-intrusif, liste des CVE actives, priorisation risques selon CVSS, correctifs recommandés prêts à déployer.",
        "proof": "Découvert en moyenne 7 vulnérabilités critiques par client en 2025. Une exposition Modbus stoppée avant exploitation.",
        "cta": "Résultats sous 48h — format exécutif + technique inclus. Pas d'accès à vos systèmes requis.",
        "base_price": 12_000,
        "urgency_multiplier": 1.3,
    },
    "ot_training": {
        "title": "Formation Sécurité OT — Équipe opérationnelle en 2 jours",
        "hook": "Votre équipe OT n'est pas formée aux cybermenaces industrielles. C'est LA première vulnérabilité à corriger.",
        "value": "Formation 2 jours en présentiel : threat modeling OT, détection anomalies, réponse incident. Exercices pratiques inclus.",
        "proof": "85% des participants passent la certification ICS-CERT après nos 2 jours. Retour sur investissement immédiat.",
        "cta": "Format entreprise (6-20 personnes) — disponible sous 2 semaines. Adaptation à votre secteur incluse.",
        "base_price": 8_000,
        "urgency_multiplier": 1.0,
    },
    "pentest_ot": {
        "title": "Pentest OT Avancé — Failles critiques révélées en 10 jours",
        "hook": "Vos concurrents ou des attaquants testent peut-être déjà vos systèmes OT. Êtes-vous certains de votre défense ?",
        "value": "Pentest complet OT : reconnaissance, exploitation contrôlée, élévation de privilèges. Rapport exécutif + correctifs détaillés.",
        "proof": "16 pentests OT en 2025 — 92% ont révélé au moins 1 faille critique exploitable. Aucun système endommagé.",
        "cta": "Devis personnalisé en 24h. Engagement de confidentialité absolue. Conformité NIS2/IEC 62443.",
        "base_price": 30_000,
        "urgency_multiplier": 1.1,
    },
}

SECTOR_PRICE_MULTIPLIERS = {
    "energie": 2.5,
    "defense": 3.0,
    "transport_logistique": 1.8,
    "manufacturing": 1.5,
    "iec62443": 1.6,
    "utilities": 2.0,
}

SIZE_MULTIPLIERS = {
    "startup": 0.5,
    "pme": 1.0,
    "eti": 1.5,
    "grand_compte": 2.5,
    "cac40": 4.0,
    "etat": 3.0,
}


@dataclass
class OfferResult:
    """Offre ultra-personnalisée générée par FlashOffer."""
    offer_id: str
    signal_id: str
    company: str
    contact_name: str
    sector: str
    pain_type: str
    email_subject: str
    email_body: str       # < 300 mots, ciblé sur la douleur
    linkedin_message: str  # < 100 mots pour LinkedIn
    price_eur: int
    price_display: str    # "15 000 EUR" ou "sur devis"
    urgency_hook: str
    pdf_summary: str      # Résumé 1 page pour PDF
    generation_time_ms: int
    personalization_score: float  # 0-1
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict:
        return {
            "offer_id": self.offer_id,
            "signal_id": self.signal_id,
            "company": self.company,
            "contact_name": self.contact_name,
            "sector": self.sector,
            "pain_type": self.pain_type,
            "email_subject": self.email_subject,
            "email_body": self.email_body,
            "linkedin_message": self.linkedin_message,
            "price_eur": self.price_eur,
            "price_display": self.price_display,
            "urgency_hook": self.urgency_hook,
            "generation_time_ms": self.generation_time_ms,
            "personalization_score": self.personalization_score,
            "generated_at": self.generated_at.isoformat(),
        }


class FlashOffer:
    """
    Génère une offre personnalisée en < 60 secondes.
    Stratégie : template pain-specific → enrichissement LLM (optionnel) → prix dynamique.
    """

    def __init__(self, llm_timeout_seconds: int = 5, use_llm: bool = False):
        self.llm_timeout = llm_timeout_seconds
        self.use_llm = use_llm  # Template-first by default for speed
        self._groq_key = os.getenv("GROQ_API_KEY", "")
        self._anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

    async def generate(
        self,
        company: str,
        sector: str,
        pain_description: str,
        contact_name: str = "",
        contact_title: str = "",
        budget_estimate: int = 15_000,
        urgency: str = "medium",
        signal_id: str = "",
        company_size: str = "pme",
    ) -> OfferResult:
        """
        Génère une offre en < 45 secondes.
        Mode template-first pour vitesse maximale.
        Garantie : prix ≥ MIN_CONTRACT_VALUE_EUR.
        """
        start_ms = int(time.time() * 1000)

        # 1. Identify pain type from description
        pain_type = self._classify_pain(pain_description, sector)

        # 2. Get base template
        template = PAIN_TEMPLATES.get(pain_type, PAIN_TEMPLATES["iec62443_audit"])

        # 3. Calculate dynamic price
        price = self._calculate_price(template["base_price"], sector, company_size, urgency, budget_estimate)

        # 4. Generate offer text (LLM if available, template fallback)
        email_subject, email_body, linkedin_msg = await self._generate_text(
            template, company, contact_name, contact_title, sector, pain_description, price, urgency
        )

        # 5. Build PDF summary
        pdf_summary = self._build_pdf_summary(template, company, contact_name, price, pain_description)

        offer_id = hashlib.sha256(f"{company}{pain_type}{time.time()}".encode()).hexdigest()[:16]
        elapsed_ms = max(1, int(time.time() * 1000) - start_ms)

        personalization = self._score_personalization(
            company, contact_name, contact_title, pain_description, email_body
        )

        offer = OfferResult(
            offer_id=offer_id,
            signal_id=signal_id,
            company=company,
            contact_name=contact_name,
            sector=sector,
            pain_type=pain_type,
            email_subject=email_subject,
            email_body=email_body,
            linkedin_message=linkedin_msg,
            price_eur=price,
            price_display=f"{price:,} EUR".replace(",", " "),
            urgency_hook=template["hook"],
            pdf_summary=pdf_summary,
            generation_time_ms=elapsed_ms,
            personalization_score=personalization,
        )
        logger.info(
            f"FlashOffer: {company} | {pain_type} | {price} EUR | {elapsed_ms}ms | "
            f"personalization={personalization:.2f}"
        )
        return offer

    # ── Text generation ────────────────────────────────────────────────────

    async def _generate_text(
        self,
        template: Dict,
        company: str,
        contact_name: str,
        contact_title: str,
        sector: str,
        pain_description: str,
        price: int,
        urgency: str,
    ) -> Tuple[str, str, str]:
        """
        Template-first pour vitesse (< 45s).
        LLM enrichment optionnel uniquement si self.use_llm=True ET clé disponible.
        """
        greeting = f"M. / Mme {contact_name}" if contact_name else "Madame, Monsieur"
        title = template["title"]
        hook = template["hook"]
        value = template["value"]
        proof = template["proof"]
        cta = template["cta"]
        price_str = f"{price:,}".replace(",", " ")

        # LLM enrichment ONLY if explicitly enabled AND key available
        if self.use_llm and self._groq_key:
            try:
                enriched = await asyncio.wait_for(
                    self._llm_enrich_groq(
                        company, contact_name, contact_title, sector,
                        pain_description, price, template
                    ),
                    timeout=self.llm_timeout,
                )
                if enriched:
                    email_subject, email_body = enriched
                    linkedin = self._build_linkedin(company, contact_name, pain_description, price)
                    return email_subject, email_body, linkedin
            except (asyncio.TimeoutError, Exception) as exc:
                logger.debug(f"LLM enrichment skipped/timeout: {exc}")

        # Template response — FAST < 5ms, always reliable
        subject = f"{title} — {company}"
        body = f"""{greeting},

{hook}

**Ce que nous proposons à {company} :**
{value}

**Pourquoi nous faire confiance :**
{proof}

**Votre investissement : {price_str} EUR TTC**
Retour sur investissement estimé : prévention d'une amende ou d'un incident à 10× ce montant.

**Prochaine étape :**
{cta}

Répondez à cet email ou appelez-nous directement — nous répondons sous 2h.

Cordialement,
Stéphanie MAMA
NAYA Intelligence | Cybersécurité OT / IEC 62443 / NIS2
"""

        linkedin = self._build_linkedin(company, contact_name, pain_description, price)
        return subject, body.strip(), linkedin

    async def _llm_enrich_groq(
        self, company: str, contact_name: str, contact_title: str,
        sector: str, pain_description: str, price: int, template: Dict
    ) -> Optional[Tuple[str, str]]:
        """Enrichissement Groq Llama 3.3 70B — ultra rapide < 3s."""
        try:
            import aiohttp
            prompt = f"""Email commercial COURT cybersécurité OT (max 150 mots).
NE PAS utiliser jargon générique. CIBLER la douleur précise.

Entreprise: {company}
Contact: {contact_name} ({contact_title})
Douleur: {pain_description}
Prix: {price:,} EUR
Accroche: {template['hook'][:100]}

Format:
Objet: [sujet < 8 mots]
---
[Corps 120-150 mots, professionnel]"""

            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 300,  # Reduced from 400
                "temperature": 0.6,  # More focused
            }
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.llm_timeout)) as sess:
                async with sess.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    json=payload,
                    headers={"Authorization": f"Bearer {self._groq_key}", "Content-Type": "application/json"},
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content = data["choices"][0]["message"]["content"]
                        lines = content.strip().split("\n")
                        subject = ""
                        body_lines = []
                        in_body = False
                        for line in lines:
                            if line.startswith("Objet:"):
                                subject = line.replace("Objet:", "").strip()
                            elif line.strip() == "---":
                                in_body = True
                            elif in_body:
                                body_lines.append(line)
                        if subject and body_lines:
                            return subject, "\n".join(body_lines).strip()
        except Exception as exc:
            logger.debug(f"Groq enrich error: {exc}")
        return None

    def _build_linkedin(self, company: str, contact_name: str, pain: str, price: int) -> str:
        name = contact_name.split()[0] if contact_name else "vous"
        return (
            f"Bonjour {name}, j'ai détecté un signal lié à {company} concernant "
            f"la sécurité OT. En 5 min, je peux vous montrer exactement le risque "
            f"et comment le résoudre (investissement à partir de {price:,} EUR). "
            f"Échangeons cette semaine ?"
        ).replace(",", " ")

    def _build_pdf_summary(
        self, template: Dict, company: str, contact: str, price: int, pain: str
    ) -> str:
        return (
            f"OFFRE COMMERCIALE — {template['title']}\n"
            f"Client : {company} | Contact : {contact}\n\n"
            f"PROBLÉMATIQUE DÉTECTÉE :\n{pain[:300]}\n\n"
            f"NOTRE SOLUTION :\n{template['value']}\n\n"
            f"PREUVES :\n{template['proof']}\n\n"
            f"PROCHAINE ÉTAPE :\n{template['cta']}\n\n"
            f"INVESTISSEMENT : {price:,} EUR TTC\n"
            f"Validité : 30 jours"
        )

    # ── Helpers ────────────────────────────────────────────────────────────

    def _classify_pain(self, pain_description: str, sector: str) -> str:
        """Identifie le type de douleur dominant."""
        text = (pain_description + " " + sector).lower()
        if any(w in text for w in ["nis2", "directive", "conformité", "anssi", "deadline"]):
            return "nis2_compliance"
        if any(w in text for w in ["ransomware", "attaque", "incident", "compromis", "breach"]):
            return "ransomware_ot"
        if any(w in text for w in ["scada", "shodan", "exposé", "vulnérabilité", "cve"]):
            return "scada_vulnerability"
        if any(w in text for w in ["formation", "training", "équipe", "sensibilisation"]):
            return "ot_training"
        return "iec62443_audit"  # default

    def _calculate_price(
        self, base: int, sector: str, company_size: str, urgency: str, budget: int
    ) -> int:
        """Prix dynamique contextuel. Plancher = MIN_CONTRACT_VALUE_EUR."""
        price = base
        price = int(price * SECTOR_PRICE_MULTIPLIERS.get(sector, 1.0))
        price = int(price * SIZE_MULTIPLIERS.get(company_size, 1.0))

        if urgency == "critical":
            price = int(price * 1.3)  # urgency premium
        elif urgency == "high":
            price = int(price * 1.15)

        # Don't exceed 60% of estimated budget (leave room for client)
        if budget > 0:
            price = min(price, int(budget * 0.6))

        # Enforce floor
        price = max(price, MIN_CONTRACT_VALUE_EUR)

        # Round to nearest 500
        price = round(price / 500) * 500
        return price

    def _score_personalization(
        self, company: str, contact: str, title: str, pain: str, body: str
    ) -> float:
        """Score la personnalisation 0-1 basé sur mentions dans le corps."""
        score = 0.0
        body_lower = body.lower()
        if company.lower()[:8] in body_lower:
            score += 0.3
        if contact and contact.split()[0].lower() in body_lower:
            score += 0.2
        if title and any(w.lower() in body_lower for w in title.split()):
            score += 0.15
        pain_words = [w for w in pain.lower().split() if len(w) > 5][:5]
        matched = sum(1 for w in pain_words if w in body_lower)
        score += min(matched / max(len(pain_words), 1) * 0.35, 0.35)
        return round(min(score, 1.0), 2)


_flash_instance: Optional[FlashOffer] = None


def get_flash_offer() -> FlashOffer:
    global _flash_instance
    if _flash_instance is None:
        _flash_instance = FlashOffer()
    return _flash_instance
