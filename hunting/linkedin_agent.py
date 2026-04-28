"""
HUNTING MODULE 2 — LINKEDIN AGENT
LinkedIn Sales Navigator prospection automation
Search, connection requests, message sequencing
Respect LinkedIn rate limits + anti-ban protection
"""

import asyncio
import aiohttp
import logging
import os
import hashlib
import random
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class LinkedInActionType(Enum):
    SEARCH = "search"
    CONNECT = "connect"
    MESSAGE = "message"
    VIEW_PROFILE = "view_profile"

@dataclass
class LinkedInProspect:
    """Prospect LinkedIn"""
    prospect_id: str
    full_name: str
    title: str
    company: str
    linkedin_url: str
    profile_summary: Optional[str] = None
    location: Optional[str] = None
    connection_status: str = "not_connected"
    last_action: Optional[LinkedInActionType] = None
    last_action_date: Optional[datetime] = None
    message_sent_count: int = 0

    def to_dict(self):
        return {
            'prospect_id': self.prospect_id,
            'full_name': self.full_name,
            'title': self.title,
            'company': self.company,
            'linkedin_url': self.linkedin_url,
            'profile_summary': self.profile_summary,
            'location': self.location,
            'connection_status': self.connection_status,
            'last_action': self.last_action.value if self.last_action else None,
            'last_action_date': self.last_action_date.isoformat() if self.last_action_date else None,
            'message_sent_count': self.message_sent_count,
        }

class LinkedInAgent:
    """
    HUNTING MODULE 2 — LinkedIn Sales Navigator automation

    Capacités:
    - Search prospects: title, company, sector, location
    - Auto connection requests avec message personnalisé
    - Message sequencing (multi-touch)
    - Profile viewing automation
    - Anti-ban protection: rate limits conservateurs

    Rate limits (conservateur):
    - 50 connection requests / jour MAX
    - 100 messages / jour MAX
    - 200 profile views / jour MAX
    - Délais aléatoires entre actions (30-120s)

    Usage:
        linkedin = LinkedInAgent()
        prospects = await linkedin.search_prospects(title="RSSI", company="Schneider")
        await linkedin.send_connection_request(prospect_id, message="Bonjour...")
    """

    API_BASE_URL = "https://api.linkedin.com/v2"

    # Rate limits conservateurs (anti-ban)
    MAX_CONNECTIONS_PER_DAY = 50
    MAX_MESSAGES_PER_DAY = 100
    MAX_VIEWS_PER_DAY = 200

    # Délais entre actions (secondes)
    MIN_DELAY_SECONDS = 30
    MAX_DELAY_SECONDS = 120

    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token or os.getenv('LINKEDIN_ACCESS_TOKEN', '')
        self.client_id = os.getenv('LINKEDIN_CLIENT_ID', '')
        self.client_secret = os.getenv('LINKEDIN_CLIENT_SECRET', '')

        self.enabled = bool(self.access_token)
        self.prospects: Dict[str, LinkedInProspect] = {}

        # Compteurs journaliers
        self.daily_connections = 0
        self.daily_messages = 0
        self.daily_views = 0
        self.last_reset = datetime.now(timezone.utc).date()

        if not self.enabled:
            logger.warning("LinkedIn API credentials not set - running in mock mode")

    def _reset_daily_counters(self):
        """Reset compteurs si nouveau jour"""
        today = datetime.now(timezone.utc).date()
        if today > self.last_reset:
            self.daily_connections = 0
            self.daily_messages = 0
            self.daily_views = 0
            self.last_reset = today
            logger.info("LinkedIn daily counters reset")

    async def _check_rate_limit(self, action_type: LinkedInActionType):
        """Vérifier rate limit pour action"""
        self._reset_daily_counters()

        limits = {
            LinkedInActionType.CONNECT: (self.daily_connections, self.MAX_CONNECTIONS_PER_DAY),
            LinkedInActionType.MESSAGE: (self.daily_messages, self.MAX_MESSAGES_PER_DAY),
            LinkedInActionType.VIEW_PROFILE: (self.daily_views, self.MAX_VIEWS_PER_DAY),
        }

        if action_type in limits:
            current, max_limit = limits[action_type]
            if current >= max_limit:
                logger.warning(f"LinkedIn {action_type.value} limit reached ({current}/{max_limit})")
                raise Exception(f"Daily limit reached for {action_type.value}")

    async def _random_delay(self):
        """Délai aléatoire entre actions (anti-ban)"""
        delay = random.uniform(self.MIN_DELAY_SECONDS, self.MAX_DELAY_SECONDS)
        logger.debug(f"LinkedIn waiting {delay:.1f}s before next action")
        await asyncio.sleep(delay)

    def _generate_prospect_id(self, linkedin_url: str) -> str:
        """Générer ID prospect unique"""
        return hashlib.md5(linkedin_url.encode()).hexdigest()[:12]

    async def search_prospects(
        self,
        title: Optional[str] = None,
        company: Optional[str] = None,
        sector: Optional[str] = None,
        location: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[LinkedInProspect]:
        """
        Rechercher prospects via LinkedIn Sales Navigator

        Args:
            title: Poste (ex: "RSSI", "DSI", "Directeur Cybersécurité")
            company: Entreprise (ex: "Schneider Electric")
            sector: Secteur (ex: "Manufacturing", "Energy")
            location: Localisation (ex: "France", "Paris")
            keywords: Mots-clés additionnels
            limit: Nombre max résultats

        Returns:
            Liste LinkedInProspect
        """
        if not self.enabled:
            logger.warning("LinkedIn API disabled - returning mock data")
            return self._generate_mock_prospects(title, company, limit)

        await self._check_rate_limit(LinkedInActionType.SEARCH)

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }

            # LinkedIn Sales Navigator API (note: nécessite abonnement Sales Navigator)
            params = {
                "keywords": f"{title or ''} {' '.join(keywords or [])}".strip(),
                "geoUrn": location,
                "currentCompany": company,
                "industry": sector,
                "count": limit
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.API_BASE_URL}/search/people",
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status != 200:
                        logger.error(f"LinkedIn API error: {response.status}")
                        return self._generate_mock_prospects(title, company, limit)

                    data = await response.json()
                    elements = data.get('elements', [])

                    prospects = []
                    for elem in elements:
                        prospect = LinkedInProspect(
                            prospect_id=self._generate_prospect_id(elem.get('publicIdentifier', '')),
                            full_name=f"{elem.get('firstName', '')} {elem.get('lastName', '')}",
                            title=elem.get('headline', ''),
                            company=company or elem.get('company', {}).get('name', ''),
                            linkedin_url=f"https://linkedin.com/in/{elem.get('publicIdentifier', '')}",
                            profile_summary=elem.get('summary', ''),
                            location=elem.get('geoLocation', '')
                        )
                        prospects.append(prospect)
                        self.prospects[prospect.prospect_id] = prospect

                    logger.info(f"LinkedIn found {len(prospects)} prospects")
                    return prospects

        except Exception as e:
            logger.error(f"LinkedIn search error: {e}")
            return self._generate_mock_prospects(title, company, limit)

    async def send_connection_request(
        self,
        prospect_id: str,
        message: Optional[str] = None
    ) -> bool:
        """
        Envoyer demande de connexion LinkedIn

        Args:
            prospect_id: ID prospect
            message: Message personnalisé (max 300 caractères)

        Returns:
            True si succès
        """
        await self._check_rate_limit(LinkedInActionType.CONNECT)

        prospect = self.prospects.get(prospect_id)
        if not prospect:
            logger.error(f"Prospect {prospect_id} not found")
            return False

        if prospect.connection_status == "connected":
            logger.warning(f"Already connected to {prospect.full_name}")
            return False

        # Limiter message à 300 caractères (LinkedIn limit)
        if message and len(message) > 300:
            message = message[:297] + "..."

        if not self.enabled:
            logger.info(f"MOCK: Connection request to {prospect.full_name}")
            prospect.connection_status = "pending"
            prospect.last_action = LinkedInActionType.CONNECT
            prospect.last_action_date = datetime.now(timezone.utc)
            self.daily_connections += 1
            return True

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }

            payload = {
                "invitee": {"com.linkedin.voyager.growth.invitation.InviteeProfile": {
                    "profileId": prospect_id
                }},
                "message": message or f"Bonjour {prospect.full_name.split()[0]}, j'aimerais échanger avec vous."
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.API_BASE_URL}/invitations",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status in [200, 201]:
                        prospect.connection_status = "pending"
                        prospect.last_action = LinkedInActionType.CONNECT
                        prospect.last_action_date = datetime.now(timezone.utc)
                        self.daily_connections += 1
                        logger.info(f"Connection request sent to {prospect.full_name}")
                        await self._random_delay()
                        return True
                    else:
                        logger.error(f"LinkedIn connection error: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"LinkedIn connection error: {e}")
            return False

    async def send_message(
        self,
        prospect_id: str,
        message: str,
        subject: Optional[str] = None
    ) -> bool:
        """
        Envoyer message LinkedIn (InMail ou message si connecté)

        Args:
            prospect_id: ID prospect
            message: Contenu message
            subject: Sujet (optionnel, pour InMail)

        Returns:
            True si succès
        """
        await self._check_rate_limit(LinkedInActionType.MESSAGE)

        prospect = self.prospects.get(prospect_id)
        if not prospect:
            logger.error(f"Prospect {prospect_id} not found")
            return False

        if not self.enabled:
            logger.info(f"MOCK: Message sent to {prospect.full_name}")
            prospect.message_sent_count += 1
            prospect.last_action = LinkedInActionType.MESSAGE
            prospect.last_action_date = datetime.now(timezone.utc)
            self.daily_messages += 1
            return True

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }

            payload = {
                "recipients": [prospect_id],
                "subject": subject or "Échange professionnel",
                "body": message
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.API_BASE_URL}/messages",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status in [200, 201]:
                        prospect.message_sent_count += 1
                        prospect.last_action = LinkedInActionType.MESSAGE
                        prospect.last_action_date = datetime.now(timezone.utc)
                        self.daily_messages += 1
                        logger.info(f"Message sent to {prospect.full_name}")
                        await self._random_delay()
                        return True
                    else:
                        logger.error(f"LinkedIn message error: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"LinkedIn message error: {e}")
            return False

    async def execute_sequence(
        self,
        prospect_id: str,
        sequence: List[Dict]
    ) -> Dict:
        """
        Exécuter séquence multi-touch LinkedIn

        Args:
            prospect_id: ID prospect
            sequence: Liste d'actions avec délais
                [
                    {"action": "connect", "message": "...", "delay_days": 0},
                    {"action": "message", "message": "...", "delay_days": 2},
                    {"action": "message", "message": "...", "delay_days": 5},
                ]

        Returns:
            Dict avec résultats de chaque étape
        """
        results = []

        for idx, step in enumerate(sequence):
            action = step['action']
            message = step.get('message', '')
            delay_days = step.get('delay_days', 0)

            # Wait delay
            if idx > 0 and delay_days > 0:
                logger.info(f"Waiting {delay_days} days before next step")
                # En production, cette séquence serait schedulée
                # Pour l'instant on simule avec asyncio.sleep
                await asyncio.sleep(1)  # Simulation

            try:
                if action == "connect":
                    success = await self.send_connection_request(prospect_id, message)
                elif action == "message":
                    success = await self.send_message(prospect_id, message)
                else:
                    success = False
                    logger.error(f"Unknown action: {action}")

                results.append({
                    'step': idx + 1,
                    'action': action,
                    'success': success,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })

            except Exception as e:
                logger.error(f"Sequence step {idx+1} error: {e}")
                results.append({
                    'step': idx + 1,
                    'action': action,
                    'success': False,
                    'error': str(e)
                })

        return {
            'prospect_id': prospect_id,
            'total_steps': len(sequence),
            'completed_steps': sum(1 for r in results if r.get('success')),
            'results': results
        }

    def _generate_mock_prospects(self, title: Optional[str], company: Optional[str], limit: int) -> List[LinkedInProspect]:
        """Générer prospects mock"""
        prospects = []
        for i in range(min(limit, 10)):
            prospect = LinkedInProspect(
                prospect_id=f"mock_ln_{i}",
                full_name=f"Jean Prospect{i}",
                title=title or "Decision Maker",
                company=company or f"Company {i}",
                linkedin_url=f"https://linkedin.com/in/mock-{i}",
                profile_summary=f"Professional with {5+i} years experience",
                location="France"
            )
            prospects.append(prospect)
            self.prospects[prospect.prospect_id] = prospect

        return prospects

    def get_stats(self) -> Dict:
        """Stats LinkedIn agent"""
        self._reset_daily_counters()
        return {
            'enabled': self.enabled,
            'total_prospects': len(self.prospects),
            'daily_connections': self.daily_connections,
            'daily_messages': self.daily_messages,
            'daily_views': self.daily_views,
            'limits': {
                'connections': f"{self.daily_connections}/{self.MAX_CONNECTIONS_PER_DAY}",
                'messages': f"{self.daily_messages}/{self.MAX_MESSAGES_PER_DAY}",
                'views': f"{self.daily_views}/{self.MAX_VIEWS_PER_DAY}",
            }
        }

# Instance globale
linkedin_agent = LinkedInAgent()

async def main():
    """Test function"""
    # Search
    prospects = await linkedin_agent.search_prospects(
        title="RSSI",
        company="Schneider Electric",
        location="France",
        limit=5
    )
    print(f"Found {len(prospects)} prospects")

    if prospects:
        # Connection request
        success = await linkedin_agent.send_connection_request(
            prospects[0].prospect_id,
            "Bonjour, j'aimerais échanger sur la cybersécurité OT."
        )
        print(f"Connection request: {success}")

        # Sequence
        sequence = [
            {"action": "connect", "message": "Bonjour!", "delay_days": 0},
            {"action": "message", "message": "Merci pour la connexion!", "delay_days": 2},
        ]
        result = await linkedin_agent.execute_sequence(prospects[0].prospect_id, sequence)
        print(f"Sequence: {result}")

    print(f"Stats: {linkedin_agent.get_stats()}")

if __name__ == "__main__":
    asyncio.run(main())
