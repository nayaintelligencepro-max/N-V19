"""
NAYA EMAIL PERSONALIZER
Personnalisation IA niveau individuel - 10x Instantly.ai
Utilise LLM multi-model fallback pour générer emails ultra-personnalisés
Apprend des victoires passées via vector memory
"""

import asyncio
import logging
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class EmailPersonalizer:
    """
    Personnalisation d'emails par IA

    Capacités:
    - Génération d'emails personnalisés par template
    - Apprentissage des victoires passées (vector memory)
    - Multi-LLM fallback (Groq → DeepSeek → Anthropic → Templates)
    - Variables dynamiques (nom, entreprise, signal, secteur, etc.)
    - Ton adaptatif selon le secteur et la séniorité
    """

    # Templates de base statiques (fallback si LLM fail)
    STATIC_TEMPLATES = {
        'email_touch1_signal': {
            'subject': '🎯 {signal_detected} — {company_name}',
            'body': """Bonjour {prospect_name},

J'ai détecté que {company_name} {signal_context}.

En 2024, {stat_sector} des entreprises {sector} ont été victimes d'incidents OT coûtant en moyenne {avg_cost_eur} EUR.

Nous avons aidé {similar_company} à sécuriser son infrastructure OT en {timeframe} avec un ROI de {roi_percent}%.

Seriez-vous disponible pour un échange de 15 minutes cette semaine ?

Cordialement,
{sender_name}
{sender_title}
"""
        },
        'email_touch3_value': {
            'subject': '📊 Comment {competitor} a réduit ses incidents OT de 78%',
            'body': """Bonjour {prospect_name},

Suite à mon dernier message, je voulais partager un cas concret.

{competitor_name} ({competitor_sector}) a mis en place notre solution d'audit IEC 62443 et a obtenu:
- 78% de réduction des incidents de sécurité OT
- Conformité NIS2 atteinte en 4 mois
- ROI de 340% la première année

Leur contexte ressemblait fortement au vôtre: {similarity_points}.

Je vous envoie le cas d'étude complet ?

Cordialement,
{sender_name}
"""
        },
        'email_touch5_objection': {
            'subject': '❓ Pourquoi {company_name} n\'a pas encore audité son OT ?',
            'body': """Bonjour {prospect_name},

Question directe: qu'est-ce qui empêche {company_name} d'auditer son infrastructure OT aujourd'hui ?

Les 3 raisons les plus fréquentes que j'entends:
1. "Pas de budget" → Notre Pack Audit Express démarre à 15k EUR (ROI 3-6 mois)
2. "Pas le temps" → L'audit complet prend 5 jours
3. "On a déjà une solution" → 89% des solutions existantes ne couvrent pas l'OT

Laquelle s'applique à vous ?

{sender_name}
"""
        },
        'email_touch7_final': {
            'subject': '✋ Dernière tentative — {prospect_name}',
            'body': """Bonjour {prospect_name},

J'ai tenté de vous contacter 6 fois ces 3 dernières semaines.

Si ce n'est pas le bon moment, aucun souci - je respecte totalement ça.

Par contre, si vous êtes intéressé mais débordé, répondez simplement "RAPPEL_M+2" et je vous recontacte dans 2 mois.

Sinon, je vous retire de ma liste et vous souhaite plein succès.

Cordialement,
{sender_name}
"""
        }
    }

    def __init__(self,
                 llm_router=None,
                 vector_memory=None,
                 sender_name: str = "Stéphanie MAMA",
                 sender_title: str = "Cybersecurity OT Specialist"):
        """
        Initialise le personalizer

        Args:
            llm_router: Router LLM multi-model (Groq → DeepSeek → Anthropic → Templates)
            vector_memory: Mémoire vectorielle pour apprendre des victoires
            sender_name: Nom de l'expéditeur
            sender_title: Titre de l'expéditeur
        """
        self.llm_router = llm_router
        self.vector_memory = vector_memory
        self.sender_name = sender_name
        self.sender_title = sender_title

        # Statistiques sectorielles (pour enrichissement)
        self.sector_stats = {
            'transport': {
                'incident_rate': '67%',
                'avg_cost_eur': '125 000',
                'compliance_deadline': 'Octobre 2024 (NIS2)'
            },
            'energie': {
                'incident_rate': '73%',
                'avg_cost_eur': '340 000',
                'compliance_deadline': 'Janvier 2025 (NIS2)'
            },
            'industrie': {
                'incident_rate': '59%',
                'avg_cost_eur': '98 000',
                'compliance_deadline': 'Décembre 2024 (ISO 27001)'
            }
        }

        logger.info("EmailPersonalizer initialized")

    async def personalize(self,
                         template_id: str,
                         prospect_data: Dict[str, Any],
                         touch_number: int) -> Dict[str, str]:
        """
        Personnalise un email pour un prospect spécifique

        Args:
            template_id: ID du template ('email_touch1_signal', etc.)
            prospect_data: Données du prospect (name, email, company, sector, context)
            touch_number: Numéro de la touche (1-7)

        Returns:
            Dict avec 'subject' et 'body' personnalisés
        """
        logger.info(f"Personalizing {template_id} for {prospect_data.get('name')} (touch {touch_number})")

        try:
            # 1. Récupérer les victoires similaires de la vector memory
            similar_wins = await self._get_similar_wins(prospect_data) if self.vector_memory else []

            # 2. Enrichir les données prospect avec contexte
            enriched_data = await self._enrich_prospect_data(prospect_data, similar_wins)

            # 3. Générer via LLM ou fallback template statique
            if self.llm_router:
                result = await self._generate_with_llm(template_id, enriched_data, touch_number)
            else:
                result = await self._generate_from_template(template_id, enriched_data)

            # 4. Validation et fallback si nécessaire
            if not result.get('subject') or not result.get('body'):
                logger.warning(f"LLM generation failed for {template_id}, falling back to static template")
                result = await self._generate_from_template(template_id, enriched_data)

            logger.info(f"Email personalized successfully for {prospect_data.get('name')}")
            return result

        except Exception as e:
            logger.error(f"Error personalizing email: {e}")
            # Fallback absolu sur template statique
            return await self._generate_from_template(template_id, prospect_data)

    async def _get_similar_wins(self, prospect_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Récupère les victoires similaires depuis la vector memory

        Args:
            prospect_data: Données du prospect

        Returns:
            Liste de cas similaires gagnants
        """
        if not self.vector_memory:
            return []

        try:
            query = f"{prospect_data.get('sector', '')} {prospect_data.get('company', '')} OT security"
            similar = await self.vector_memory.search_similar_wins(
                query=query,
                sector=prospect_data.get('sector'),
                limit=3
            )
            logger.info(f"Found {len(similar)} similar wins for {prospect_data.get('company')}")
            return similar
        except Exception as e:
            logger.error(f"Error fetching similar wins: {e}")
            return []

    async def _enrich_prospect_data(self,
                                   prospect_data: Dict[str, Any],
                                   similar_wins: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Enrichit les données prospect avec statistiques sectorielles et cas similaires

        Args:
            prospect_data: Données de base du prospect
            similar_wins: Cas similaires gagnants

        Returns:
            Données enrichies prêtes pour la génération
        """
        enriched = prospect_data.copy()

        # Ajouter les infos sender
        enriched['sender_name'] = self.sender_name
        enriched['sender_title'] = self.sender_title

        # Ajouter les stats sectorielles
        sector = prospect_data.get('sector', 'industrie').lower()
        sector_info = self.sector_stats.get(sector, self.sector_stats['industrie'])
        enriched.update({
            'stat_sector': sector_info['incident_rate'],
            'avg_cost_eur': sector_info['avg_cost_eur'],
            'compliance_deadline': sector_info['compliance_deadline']
        })

        # Ajouter des exemples de cas similaires
        if similar_wins:
            best_win = similar_wins[0]
            enriched['similar_company'] = best_win.get('company_name', 'un acteur du secteur')
            enriched['competitor_name'] = best_win.get('company_name', 'Un concurrent')
            enriched['competitor_sector'] = best_win.get('sector', sector)
            enriched['roi_percent'] = best_win.get('roi', '280')
            enriched['timeframe'] = best_win.get('timeframe', '6 mois')
            enriched['similarity_points'] = best_win.get('pain_points', 'infrastructure OT critique')
        else:
            # Données génériques si pas de cas similaire
            enriched.update({
                'similar_company': 'plusieurs acteurs du secteur',
                'competitor_name': 'Un acteur majeur',
                'competitor_sector': sector,
                'roi_percent': '280',
                'timeframe': '6 mois',
                'similarity_points': 'infrastructure OT critique à sécuriser'
            })

        # Extraire le signal détecté du contexte
        context = prospect_data.get('context', {})
        enriched['signal_detected'] = context.get('signal', 'opportunité de sécurisation OT')
        enriched['signal_context'] = context.get('signal_context', 'recherche des solutions de cybersécurité OT')

        return enriched

    async def _generate_with_llm(self,
                                template_id: str,
                                enriched_data: Dict[str, Any],
                                touch_number: int) -> Dict[str, str]:
        """
        Génère l'email via LLM (avec fallback multi-model)

        Args:
            template_id: ID du template
            enriched_data: Données enrichies
            touch_number: Numéro de touche

        Returns:
            Dict avec subject et body générés
        """
        # Récupérer le template statique comme référence
        static_template = self.STATIC_TEMPLATES.get(template_id, {})

        # Construire le prompt pour le LLM
        prompt = self._build_llm_prompt(template_id, enriched_data, touch_number, static_template)

        try:
            # Appel au LLM router (gère automatiquement Groq → DeepSeek → Anthropic → Template)
            response = await self.llm_router.generate(
                prompt=prompt,
                max_tokens=800,
                temperature=0.7,
                system_message="Tu es un expert en outreach B2B cybersécurité OT. Génère des emails personnalisés, concis, orientés valeur."
            )

            # Parser la réponse (format JSON attendu: {"subject": "...", "body": "..."})
            result = self._parse_llm_response(response)
            return result

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            # Fallback sur template statique
            return await self._generate_from_template(template_id, enriched_data)

    def _build_llm_prompt(self,
                         template_id: str,
                         enriched_data: Dict[str, Any],
                         touch_number: int,
                         static_template: Dict[str, str]) -> str:
        """
        Construit le prompt pour le LLM

        Args:
            template_id: ID du template
            enriched_data: Données enrichies
            touch_number: Numéro de touche
            static_template: Template statique comme référence

        Returns:
            Prompt complet
        """
        context_json = json.dumps(enriched_data, indent=2, ensure_ascii=False)

        prompt = f"""Génère un email B2B ultra-personnalisé pour la touche {touch_number} d'une séquence outreach.

TEMPLATE DE RÉFÉRENCE (à améliorer et personnaliser):
Sujet: {static_template.get('subject', '')}
Corps: {static_template.get('body', '')}

DONNÉES PROSPECT:
{context_json}

CONTRAINTES:
- Sujet: max 60 caractères, accrocheur, utilise emoji si pertinent
- Corps: max 150 mots, ultra-personnalisé, orienté VALEUR (pas features)
- Ton: professionnel mais humain, direct, pas de langue de bois
- Call-to-action: clair et simple (15 min call, cas d'étude, question)
- Utilise les données réelles (nom, entreprise, secteur, signal, stats)

Réponds UNIQUEMENT en JSON:
{{
  "subject": "ton sujet personnalisé",
  "body": "ton corps d'email personnalisé"
}}
"""
        return prompt

    def _parse_llm_response(self, response: str) -> Dict[str, str]:
        """
        Parse la réponse du LLM (JSON attendu)

        Args:
            response: Réponse brute du LLM

        Returns:
            Dict avec subject et body
        """
        try:
            # Nettoyer la réponse (enlever les backticks markdown si présents)
            cleaned = response.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            if cleaned.startswith('```'):
                cleaned = cleaned[3:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            # Parser le JSON
            parsed = json.loads(cleaned)

            if 'subject' in parsed and 'body' in parsed:
                return {
                    'subject': parsed['subject'],
                    'body': parsed['body']
                }
            else:
                logger.error("LLM response missing subject or body")
                return {}

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Raw response: {response}")
            return {}

    async def _generate_from_template(self,
                                     template_id: str,
                                     data: Dict[str, Any]) -> Dict[str, str]:
        """
        Génère l'email depuis template statique (fallback)

        Args:
            template_id: ID du template
            data: Données pour remplacement variables

        Returns:
            Dict avec subject et body
        """
        template = self.STATIC_TEMPLATES.get(template_id)

        if not template:
            logger.error(f"Template {template_id} not found")
            # Template d'urgence absolue
            return {
                'subject': f"Re: {data.get('company', 'votre entreprise')}",
                'body': f"Bonjour {data.get('name', 'Madame, Monsieur')},\n\nJe me permets de vous contacter...\n\nCordialement,\n{self.sender_name}"
            }

        # Remplacer les variables dans le template
        subject = self._replace_variables(template['subject'], data)
        body = self._replace_variables(template['body'], data)

        return {'subject': subject, 'body': body}

    def _replace_variables(self, text: str, data: Dict[str, Any]) -> str:
        """
        Remplace les variables {var} dans le texte

        Args:
            text: Texte avec variables
            data: Données pour remplacement

        Returns:
            Texte avec variables remplacées
        """
        result = text

        for key, value in data.items():
            placeholder = f"{{{key}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))

        # Remplacer les variables manquantes par des valeurs par défaut
        result = result.replace('{prospect_name}', data.get('name', 'Madame, Monsieur'))
        result = result.replace('{company_name}', data.get('company', 'votre entreprise'))
        result = result.replace('{sender_name}', self.sender_name)
        result = result.replace('{sender_title}', self.sender_title)

        return result

    async def learn_from_win(self,
                            template_id: str,
                            prospect_data: Dict[str, Any],
                            email_content: Dict[str, str],
                            outcome: str) -> bool:
        """
        Apprend d'une victoire pour améliorer les futures personnalisations

        Args:
            template_id: Template utilisé
            prospect_data: Données du prospect
            email_content: Contenu de l'email (subject + body)
            outcome: Résultat ('meeting_booked', 'positive_reply', etc.)

        Returns:
            True si sauvegardé avec succès
        """
        if not self.vector_memory:
            logger.warning("Vector memory not available, cannot learn from win")
            return False

        try:
            win_data = {
                'template_id': template_id,
                'sector': prospect_data.get('sector'),
                'company_name': prospect_data.get('company'),
                'subject': email_content.get('subject'),
                'body': email_content.get('body'),
                'outcome': outcome,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            await self.vector_memory.save_win(win_data)
            logger.info(f"Learned from win: {template_id} → {outcome}")
            return True

        except Exception as e:
            logger.error(f"Error learning from win: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de personnalisation"""
        return {
            'sender_name': self.sender_name,
            'sender_title': self.sender_title,
            'templates_available': len(self.STATIC_TEMPLATES),
            'sectors_supported': len(self.sector_stats),
            'llm_enabled': self.llm_router is not None,
            'vector_memory_enabled': self.vector_memory is not None
        }


__all__ = ['EmailPersonalizer']
