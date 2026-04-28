#!/usr/bin/env python3
"""
NAYA OUTREACH - Meeting Booker Module
Prise de RDV automatique via Calendly API
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import aiohttp
from dataclasses import dataclass


@dataclass
class MeetingSlot:
    """Créneau de meeting disponible"""
    start_time: datetime
    end_time: datetime
    calendly_url: str
    timezone: str = "Pacific/Tahiti"


class MeetingBooker:
    """
    Gestionnaire automatique de prise de RDV
    Intégration Calendly API pour scheduling automatisé
    """

    def __init__(self):
        self.calendly_api_key = os.getenv("CALENDLY_API_KEY", "")
        self.calendly_event_type = os.getenv("CALENDLY_EVENT_TYPE", "")
        self.base_url = "https://api.calendly.com"
        self.headers = {
            "Authorization": f"Bearer {self.calendly_api_key}",
            "Content-Type": "application/json"
        }

    async def get_available_slots(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_slots: int = 5
    ) -> List[MeetingSlot]:
        """
        Récupère les créneaux disponibles

        Args:
            start_date: Date début recherche (défaut: aujourd'hui)
            end_date: Date fin recherche (défaut: +14 jours)
            min_slots: Nombre minimum de créneaux à retourner

        Returns:
            Liste de créneaux disponibles
        """
        if not start_date:
            start_date = datetime.now()
        if not end_date:
            end_date = start_date + timedelta(days=14)

        slots = []

        # Mode dégradé si pas de clé API
        if not self.calendly_api_key:
            # Génération de slots par défaut (9h-17h, jours ouvrés)
            current_date = start_date
            while len(slots) < min_slots and current_date <= end_date:
                # Ignorer weekends
                if current_date.weekday() < 5:  # Lundi=0, Vendredi=4
                    for hour in [9, 11, 14, 16]:
                        slot_time = current_date.replace(
                            hour=hour,
                            minute=0,
                            second=0,
                            microsecond=0
                        )
                        slots.append(MeetingSlot(
                            start_time=slot_time,
                            end_time=slot_time + timedelta(hours=1),
                            calendly_url=f"https://calendly.com/naya-supreme/meeting?date={slot_time.strftime('%Y-%m-%d')}&time={hour}:00",
                            timezone="Pacific/Tahiti"
                        ))
                        if len(slots) >= min_slots:
                            break
                current_date += timedelta(days=1)
            return slots[:min_slots]

        # Appel API Calendly réel
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "event_type": self.calendly_event_type,
                    "start_time": start_date.isoformat(),
                    "end_time": end_date.isoformat(),
                    "count": min_slots
                }

                async with session.get(
                    f"{self.base_url}/event_type_available_times",
                    headers=self.headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        for slot_data in data.get("collection", []):
                            slots.append(MeetingSlot(
                                start_time=datetime.fromisoformat(
                                    slot_data["start_time"].replace("Z", "+00:00")
                                ),
                                end_time=datetime.fromisoformat(
                                    slot_data["end_time"].replace("Z", "+00:00")
                                ),
                                calendly_url=slot_data.get("scheduling_url", ""),
                                timezone=slot_data.get("timezone", "Pacific/Tahiti")
                            ))
                    else:
                        # Fallback mode dégradé
                        return await self.get_available_slots(
                            start_date, end_date, min_slots
                        )
        except Exception as e:
            print(f"Calendly API error: {e}, using fallback slots")
            # Retour au mode dégradé
            return await self.get_available_slots(start_date, end_date, min_slots)

        return slots

    async def book_meeting(
        self,
        prospect_email: str,
        prospect_name: str,
        slot: MeetingSlot,
        message: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Réserve un créneau pour un prospect

        Args:
            prospect_email: Email du prospect
            prospect_name: Nom du prospect
            slot: Créneau sélectionné
            message: Message optionnel pour le prospect

        Returns:
            Détails de la réservation
        """
        booking_data = {
            "prospect_email": prospect_email,
            "prospect_name": prospect_name,
            "start_time": slot.start_time.isoformat(),
            "end_time": slot.end_time.isoformat(),
            "calendly_url": slot.calendly_url,
            "message": message or "",
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }

        if not self.calendly_api_key:
            # Mode simulation
            booking_data["status"] = "simulated"
            booking_data["booking_url"] = slot.calendly_url
            return booking_data

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "event_type_uuid": self.calendly_event_type,
                    "invitee": {
                        "email": prospect_email,
                        "name": prospect_name
                    },
                    "start_time": slot.start_time.isoformat(),
                    "timezone": slot.timezone,
                    "questions_and_answers": [
                        {
                            "question": "Message",
                            "answer": message or "Réunion NAYA SUPREME - Audit OT / IEC 62443"
                        }
                    ]
                }

                async with session.post(
                    f"{self.base_url}/scheduled_events",
                    headers=self.headers,
                    json=payload
                ) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        booking_data["status"] = "confirmed"
                        booking_data["booking_url"] = data.get("resource", {}).get("uri", slot.calendly_url)
                        booking_data["event_id"] = data.get("resource", {}).get("uuid", "")
                    else:
                        booking_data["status"] = "failed"
                        booking_data["error"] = f"API returned {response.status}"
        except Exception as e:
            booking_data["status"] = "failed"
            booking_data["error"] = str(e)

        return booking_data

    async def cancel_meeting(self, event_id: str, reason: Optional[str] = None) -> bool:
        """
        Annule un meeting réservé

        Args:
            event_id: ID de l'événement Calendly
            reason: Raison de l'annulation

        Returns:
            True si annulation réussie
        """
        if not self.calendly_api_key or not event_id:
            return False

        try:
            async with aiohttp.ClientSession() as session:
                payload = {"reason": reason or "Annulation par le système"}

                async with session.post(
                    f"{self.base_url}/scheduled_events/{event_id}/cancellation",
                    headers=self.headers,
                    json=payload
                ) as response:
                    return response.status in [200, 204]
        except Exception:
            return False

    async def send_meeting_invitation(
        self,
        prospect_email: str,
        prospect_name: str,
        offer_context: Optional[Dict] = None
    ) -> Dict[str, any]:
        """
        Envoie une invitation de meeting avec créneaux proposés

        Args:
            prospect_email: Email du prospect
            prospect_name: Nom du prospect
            offer_context: Contexte de l'offre (secteur, douleur, etc.)

        Returns:
            Détails de l'invitation envoyée
        """
        slots = await self.get_available_slots(min_slots=3)

        invitation = {
            "prospect_email": prospect_email,
            "prospect_name": prospect_name,
            "subject": f"🎯 {prospect_name} - Audit OT / IEC 62443 : Créneaux disponibles",
            "available_slots": [
                {
                    "date": slot.start_time.strftime("%d/%m/%Y"),
                    "time": slot.start_time.strftime("%H:%M"),
                    "duration": "60 min",
                    "booking_url": slot.calendly_url
                }
                for slot in slots
            ],
            "message": self._build_invitation_message(prospect_name, offer_context),
            "sent_at": datetime.now().isoformat()
        }

        return invitation

    def _build_invitation_message(
        self,
        prospect_name: str,
        context: Optional[Dict] = None
    ) -> str:
        """Construit le message d'invitation personnalisé"""
        sector = context.get("sector", "votre secteur") if context else "votre secteur"
        pain = context.get("pain", "vos enjeux OT") if context else "vos enjeux OT"

        return f"""Bonjour {prospect_name},

Suite à notre échange concernant {pain} dans le secteur {sector}, je vous propose un audit flash OT / IEC 62443.

🎯 Objectif : Identifier les gaps de sécurité critiques en 48h
📊 Livrable : Rapport avec roadmap priorisée
💰 Investissement : À partir de 5 000 EUR

Merci de sélectionner un créneau qui vous convient.

Cordialement,
NAYA SUPREME - Cybersécurité OT & Conformité IEC 62443
"""


# Instance globale
meeting_booker = MeetingBooker()


async def main():
    """Test du module"""
    print("🗓️  NAYA Meeting Booker - Test Module")

    # Test 1: Récupération des créneaux
    slots = await meeting_booker.get_available_slots(min_slots=5)
    print(f"\n✅ {len(slots)} créneaux disponibles:")
    for i, slot in enumerate(slots[:3], 1):
        print(f"   {i}. {slot.start_time.strftime('%d/%m/%Y %H:%M')} - {slot.end_time.strftime('%H:%M')}")

    # Test 2: Invitation
    invitation = await meeting_booker.send_meeting_invitation(
        prospect_email="rssi@transport-corp.fr",
        prospect_name="Jean Dupont",
        offer_context={
            "sector": "Transport & Logistique",
            "pain": "Conformité NIS2"
        }
    )
    print(f"\n✅ Invitation créée:")
    print(f"   Destinataire: {invitation['prospect_name']}")
    print(f"   Créneaux proposés: {len(invitation['available_slots'])}")

    # Test 3: Réservation (mode simulation)
    booking = await meeting_booker.book_meeting(
        prospect_email="rssi@transport-corp.fr",
        prospect_name="Jean Dupont",
        slot=slots[0],
        message="Audit OT flash - Conformité NIS2"
    )
    print(f"\n✅ Réservation:")
    print(f"   Status: {booking['status']}")
    print(f"   URL: {booking.get('booking_url', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(main())
