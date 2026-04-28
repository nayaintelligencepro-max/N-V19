#!/usr/bin/env python3
"""
NAYA MEMORY - Offer Memory Module  
Mémorisation et apprentissage des offres gagnantes
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class OfferResult:
    """Résultat d'une offre commerciale"""
    offer_id: str
    prospect_sector: str
    prospect_company: str
    offer_value_eur: float
    tier: str  # TIER1, TIER2, TIER3, TIER4
    pain_detected: str
    solution_proposed: str
    email_subject: str
    email_body_preview: str  # Premiers 500 chars
    linkedin_message_preview: str
    sent_at: str
    response_status: str  # sent, opened, replied, meeting_booked, won, lost, ignored
    response_time_hours: Optional[float] = None
    won_amount_eur: Optional[float] = None
    feedback: Optional[str] = None
    variant: str = "A"  # Pour A/B testing


class OfferMemory:
    """
    Mémoire des offres commerciales avec apprentissage continu
    Stocke TOUTES les offres envoyées et leur résultat
    """

    def __init__(self, storage_path: str = "data/memory/offers.json"):
        self.storage_path = storage_path
        self.offers: List[OfferResult] = []
        self._load_memory()

    def _load_memory(self):
        """Charge la mémoire depuis le fichier"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.offers = [OfferResult(**offer) for offer in data]
        except FileNotFoundError:
            self.offers = []
        except Exception as e:
            print(f"Error loading offer memory: {e}")
            self.offers = []

    def _save_memory(self):
        """Sauvegarde la mémoire dans le fichier"""
        try:
            import os
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump([asdict(offer) for offer in self.offers], f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving offer memory: {e}")

    async def save_offer(self, offer_data: Dict) -> str:
        """
        Enregistre une nouvelle offre envoyée

        Args:
            offer_data: Données de l'offre (voir OfferResult)

        Returns:
            offer_id généré
        """
        offer_id = f"OFFER_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.offers)+1}"

        offer = OfferResult(
            offer_id=offer_id,
            prospect_sector=offer_data.get("prospect_sector", "Unknown"),
            prospect_company=offer_data.get("prospect_company", "Unknown"),
            offer_value_eur=float(offer_data.get("offer_value_eur", 0)),
            tier=offer_data.get("tier", "TIER1"),
            pain_detected=offer_data.get("pain_detected", ""),
            solution_proposed=offer_data.get("solution_proposed", ""),
            email_subject=offer_data.get("email_subject", ""),
            email_body_preview=offer_data.get("email_body", "")[:500],
            linkedin_message_preview=offer_data.get("linkedin_message", "")[:300],
            sent_at=datetime.now().isoformat(),
            response_status="sent",
            variant=offer_data.get("variant", "A")
        )

        self.offers.append(offer)
        self._save_memory()

        return offer_id

    async def update_offer_status(
        self,
        offer_id: str,
        status: str,
        response_time_hours: Optional[float] = None,
        won_amount_eur: Optional[float] = None,
        feedback: Optional[str] = None
    ):
        """
        Met à jour le statut d'une offre

        Args:
            offer_id: ID de l'offre
            status: Nouveau statut (opened, replied, meeting_booked, won, lost, ignored)
            response_time_hours: Temps de réponse en heures
            won_amount_eur: Montant gagné si won
            feedback: Feedback du prospect
        """
        for offer in self.offers:
            if offer.offer_id == offer_id:
                offer.response_status = status
                if response_time_hours is not None:
                    offer.response_time_hours = response_time_hours
                if won_amount_eur is not None:
                    offer.won_amount_eur = won_amount_eur
                if feedback:
                    offer.feedback = feedback
                self._save_memory()
                break

    async def get_winning_patterns(self, sector: Optional[str] = None, tier: Optional[str] = None) -> Dict:
        """
        Analyse les patterns des offres gagnantes

        Args:
            sector: Filtrer par secteur (optionnel)
            tier: Filtrer par tier (optionnel)

        Returns:
            Patterns détectés (sujets, approches, timing)
        """
        won_offers = [o for o in self.offers if o.response_status == "won"]

        if sector:
            won_offers = [o for o in won_offers if o.prospect_sector == sector]
        if tier:
            won_offers = [o for o in won_offers if o.tier == tier]

        if not won_offers:
            return {
                "count": 0,
                "avg_value_eur": 0,
                "avg_response_time_hours": 0,
                "best_subjects": [],
                "best_approaches": []
            }

        total_value = sum(o.won_amount_eur or 0 for o in won_offers)
        response_times = [o.response_time_hours for o in won_offers if o.response_time_hours]

        # Analyse des sujets les plus efficaces
        subject_scores = {}
        for offer in won_offers:
            # Extraire mots-clés du sujet
            keywords = offer.email_subject.lower().split()
            for kw in keywords:
                if len(kw) > 4:  # Mots significatifs seulement
                    subject_scores[kw] = subject_scores.get(kw, 0) + 1

        best_subjects = sorted(subject_scores.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "count": len(won_offers),
            "avg_value_eur": total_value / len(won_offers),
            "avg_response_time_hours": sum(response_times) / len(response_times) if response_times else 0,
            "best_subjects": [kw for kw, _ in best_subjects],
            "best_tier": max(won_offers, key=lambda o: o.won_amount_eur or 0).tier if won_offers else "TIER1",
            "conversion_rate": len(won_offers) / len(self.offers) if self.offers else 0
        }

    async def search_similar_wins(self, prospect_profile: Dict) -> List[OfferResult]:
        """
        Recherche des offres gagnantes similaires au profil prospect

        Args:
            prospect_profile: {sector, pain, budget_estimate, tier}

        Returns:
            Liste des offres similaires qui ont gagné (max 5)
        """
        sector = prospect_profile.get("sector", "")
        pain = prospect_profile.get("pain", "")

        won_offers = [o for o in self.offers if o.response_status == "won"]

        # Score de similarité
        scored_offers = []
        for offer in won_offers:
            score = 0
            if offer.prospect_sector == sector:
                score += 50
            if pain.lower() in offer.pain_detected.lower():
                score += 30
            if offer.tier == prospect_profile.get("tier", "TIER1"):
                score += 20

            if score > 0:
                scored_offers.append((score, offer))

        # Trier par score et retourner top 5
        scored_offers.sort(key=lambda x: x[0], reverse=True)
        return [offer for _, offer in scored_offers[:5]]

    async def get_stats(self) -> Dict:
        """Statistiques globales de la mémoire"""
        total = len(self.offers)
        if total == 0:
            return {"total": 0, "won": 0, "conversion_rate": 0}

        won = len([o for o in self.offers if o.response_status == "won"])
        replied = len([o for o in self.offers if o.response_status in ["replied", "meeting_booked", "won"]])

        total_won_value = sum(o.won_amount_eur or 0 for o in self.offers if o.response_status == "won")

        return {
            "total": total,
            "won": won,
            "replied": replied,
            "conversion_rate": won / total,
            "reply_rate": replied / total,
            "total_won_value_eur": total_won_value,
            "avg_deal_size_eur": total_won_value / won if won > 0 else 0
        }


# Instance globale
offer_memory = OfferMemory()


async def main():
    """Test du module"""
    print("💾 NAYA Offer Memory - Test Module")

    # Test 1: Enregistrer une offre
    offer_id = await offer_memory.save_offer({
        "prospect_sector": "Transport & Logistique",
        "prospect_company": "SNCF",
        "offer_value_eur": 15000,
        "tier": "TIER2",
        "pain_detected": "Conformité NIS2 - deadline 2024",
        "solution_proposed": "Audit IEC 62443 express + roadmap",
        "email_subject": "🚨 SNCF - Conformité NIS2 : 6 mois pour agir",
        "email_body": "Bonjour, j'ai détecté que SNCF doit se conformer à NIS2...",
        "linkedin_message": "Conformité NIS2 transport - audit flash disponible",
        "variant": "A"
    })
    print(f"\n✅ Offre enregistrée: {offer_id}")

    # Test 2: Mise à jour statut
    await offer_memory.update_offer_status(
        offer_id=offer_id,
        status="won",
        response_time_hours=48.5,
        won_amount_eur=15000,
        feedback="Excellent rapport, nous signons"
    )
    print(f"✅ Statut mis à jour: WON")

    # Test 3: Patterns gagnants
    patterns = await offer_memory.get_winning_patterns(sector="Transport & Logistique")
    print(f"\n✅ Patterns gagnants:")
    print(f"   Offres gagnées: {patterns['count']}")
    print(f"   Valeur moyenne: {patterns['avg_value_eur']:.0f} EUR")

    # Test 4: Stats globales
    stats = await offer_memory.get_stats()
    print(f"\n✅ Statistiques:")
    print(f"   Total offres: {stats['total']}")
    print(f"   Taux conversion: {stats['conversion_rate']*100:.1f}%")
    print(f"   Valeur totale gagnée: {stats['total_won_value_eur']:.0f} EUR")


if __name__ == "__main__":
    asyncio.run(main())
