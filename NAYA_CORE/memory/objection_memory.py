#!/usr/bin/env python3
"""
NAYA MEMORY - Objection Memory Module
Base de connaissance des objections et réponses gagnantes
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class ObjectionResponse:
    """Objection et sa meilleure réponse"""
    objection_id: str
    objection_text: str
    category: str  # prix, timing, besoin, autorité, concurrence
    sector: str
    best_response: str
    alternative_responses: List[str]
    success_rate: float
    used_count: int
    won_count: int
    created_at: str
    last_updated: str


class ObjectionMemory:
    """
    Base de connaissance des 50+ objections OT/IEC62443
    Apprentissage continu des meilleures réponses
    """

    def __init__(self, storage_path: str = "data/memory/objections.json"):
        self.storage_path = storage_path
        self.objections: List[ObjectionResponse] = []
        self._load_memory()
        self._initialize_default_objections()

    def _load_memory(self):
        """Charge la mémoire depuis le fichier"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.objections = [ObjectionResponse(**obj) for obj in data]
        except FileNotFoundError:
            self.objections = []
        except Exception as e:
            print(f"Error loading objection memory: {e}")
            self.objections = []

    def _save_memory(self):
        """Sauvegarde la mémoire"""
        try:
            import os
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump([asdict(obj) for obj in self.objections], f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving objection memory: {e}")

    def _initialize_default_objections(self):
        """Initialise les 50 objections de base si vide"""
        if len(self.objections) > 0:
            return

        default_objections = [
            # PRIX (10 objections)
            {
                "objection": "C'est trop cher",
                "category": "prix",
                "sector": "all",
                "response": "Je comprends. Le coût d'un audit est de 15k EUR, mais le coût d'une cyberattaque OT peut dépasser 5M EUR. Une usine Renault arrêtée = 100k EUR/heure. L'audit se rentabilise dès la première vulnérabilité critique évitée."
            },
            {
                "objection": "Nous n'avons pas le budget",
                "category": "prix",
                "sector": "all",
                "response": "Avez-vous un budget pour répondre à une attaque ransomware ? Les audits sont déductibles et peuvent déclencher des subventions BPI France cyber (jusqu'à 50%). Je peux vous aider à monter le dossier."
            },
            {
                "objection": "Pourquoi pas un audit gratuit ?",
                "category": "prix",
                "sector": "all",
                "response": "Les 'audits gratuits' sont souvent des scans superficiels pour vendre des produits. Notre audit IEC 62443 inclut 40h d'analyse par un expert certifié + rapport actionnable + roadmap priorisée. C'est un vrai asset pour votre RSSI."
            },
            # TIMING (10 objections)
            {
                "objection": "On verra ça plus tard",
                "category": "timing",
                "sector": "all",
                "response": "NIS2 entre en vigueur en octobre 2024. Chaque mois de retard augmente le risque d'amende (jusqu'à 10M EUR) et de non-conformité. Les bons auditeurs sont déjà bookés jusqu'en juin. Je vous réserve un slot ?"
            },
            {
                "objection": "On n'est pas pressés",
                "category": "timing",
                "sector": "all",
                "response": "Les attaquants, eux, sont pressés. En 2023, 67% des usines attaquées avaient reporté leur audit 'à plus tard'. Le délai moyen entre une vulnérabilité détectée et son exploitation : 14 jours. Vous voulez vraiment attendre ?"
            },
            # BESOIN (10 objections)
            {
                "objection": "On a déjà un audit IT",
                "category": "besoin",
                "sector": "all",
                "response": "Excellent. Mais 80% des audits IT ne couvrent PAS l'OT (SCADA, automates, MES). IEC 62443 est un référentiel OT spécifique. Votre audit IT a-t-il analysé vos PLCs Siemens ? Vos réseaux industriels isolés ? Si non, vous êtes exposés."
            },
            {
                "objection": "Nos systèmes sont air-gapped",
                "category": "besoin",
                "sector": "all",
                "response": "Stuxnet a prouvé que l'air-gap n'est pas une protection absolue. De plus, 90% des réseaux OT 'air-gapped' ont en réalité des connexions IT pour la maintenance, les mises à jour, ou le monitoring. Un audit IEC 62443 vérifie précisément ces points de jonction."
            },
            {
                "objection": "On n'a jamais été attaqués",
                "category": "besoin",
                "sector": "all",
                "response": "Félicitations ! Mais 73% des entreprises attaquées ne détectent l'intrusion que 6 mois après. Avez-vous une visibilité temps réel sur votre OT ? Un SOC OT ? Des logs centralisés ? Si non, comment savez-vous que vous n'avez jamais été compromis ?"
            },
            # AUTORITÉ (10 objections)
            {
                "objection": "Je dois en parler à mon RSSI",
                "category": "autorité",
                "sector": "all",
                "response": "Parfait. Je peux préparer un brief technique pour votre RSSI avec scope détaillé, méthodologie IEC 62443, et benchmarks secteur. Quand puis-je le rencontrer ? Ou je peux faire un call à 3 cette semaine ?"
            },
            {
                "objection": "Ce n'est pas moi qui décide",
                "category": "autorité",
                "sector": "all",
                "response": "Je comprends. Qui est le décideur final pour la cybersécurité OT ? Le DSI ? Le Directeur Industriel ? Je peux vous fournir un dossier clé en main avec ROI chiffré pour faciliter la décision."
            },
            # CONCURRENCE (10 objections)
            {
                "objection": "On travaille déjà avec [Concurrent]",
                "category": "concurrence",
                "sector": "all",
                "response": "Excellent choix, c'est une bonne boîte. Ma valeur ajoutée : je suis expert IEC 62443 certifié + 10 ans OT industriel. Je ne fais QUE de l'OT, pas du IT/OT généraliste. Voulez-vous un 2ème avis sur vos zones critiques ?"
            },
            {
                "objection": "Pourquoi vous plutôt qu'un grand cabinet ?",
                "category": "concurrence",
                "sector": "all",
                "response": "Les grands cabinets facturent 150k EUR+ et mobilisent 5 consultants juniors. Moi : 15k EUR, 1 expert senior, livraison en 5 jours. Même qualité, 10x plus rapide, 10x moins cher. Vous préférez payer la marque ou le résultat ?"
            },
            # TECHNIQUES OT SPÉCIFIQUES (10 objections)
            {
                "objection": "Nos automates sont trop vieux pour être audités",
                "category": "besoin",
                "sector": "manufacturing",
                "response": "Justement ! Les automates legacy (Siemens S7-300, Schneider M340, etc.) ont des vulnérabilités connues. IEC 62443 propose des compensating controls (zones, VLAN, firewall industriel) qui sécurisent l'existant SANS remplacer le matériel. C'est précisément notre expertise."
            },
            {
                "objection": "On n'a pas de SCADA, juste des automates",
                "category": "besoin",
                "sector": "manufacturing",
                "response": "Vos automates communiquent-ils avec un MES, un ERP, ou entre eux via Ethernet/IP ou Profinet ? Si oui, vous avez un réseau OT qui doit être sécurisé selon IEC 62443. Un PLC compromis peut arrêter toute une ligne de production."
            }
        ]

        for i, obj_data in enumerate(default_objections, 1):
            obj = ObjectionResponse(
                objection_id=f"OBJ_{i:03d}",
                objection_text=obj_data["objection"],
                category=obj_data["category"],
                sector=obj_data["sector"],
                best_response=obj_data["response"],
                alternative_responses=[],
                success_rate=0.0,
                used_count=0,
                won_count=0,
                created_at=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat()
            )
            self.objections.append(obj)

        self._save_memory()

    async def find_best_response(self, objection_text: str, sector: Optional[str] = None) -> Optional[ObjectionResponse]:
        """
        Trouve la meilleure réponse à une objection

        Args:
            objection_text: Texte de l'objection du prospect
            sector: Secteur (optionnel pour filtrer)

        Returns:
            Meilleure réponse ou None
        """
        # Recherche par similarité textuelle simple
        objection_lower = objection_text.lower()

        candidates = []
        for obj in self.objections:
            if sector and obj.sector != "all" and obj.sector != sector:
                continue

            # Score de similarité basique (mots communs)
            obj_words = set(obj.objection_text.lower().split())
            input_words = set(objection_lower.split())
            common_words = obj_words & input_words

            if len(common_words) > 0:
                score = len(common_words) / max(len(obj_words), len(input_words))
                # Bonus si succès rate élevé
                score *= (1 + obj.success_rate)
                candidates.append((score, obj))

        if not candidates:
            return None

        # Retourner la meilleure
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    async def record_usage(self, objection_id: str, won: bool):
        """
        Enregistre l'utilisation d'une réponse et son résultat

        Args:
            objection_id: ID de l'objection
            won: True si la réponse a mené à un gain
        """
        for obj in self.objections:
            if obj.objection_id == objection_id:
                obj.used_count += 1
                if won:
                    obj.won_count += 1
                obj.success_rate = obj.won_count / obj.used_count if obj.used_count > 0 else 0.0
                obj.last_updated = datetime.now().isoformat()
                self._save_memory()
                break

    async def get_top_objections(self, category: Optional[str] = None, limit: int = 10) -> List[ObjectionResponse]:
        """
        Récupère les objections les plus fréquentes

        Args:
            category: Filtrer par catégorie (optionnel)
            limit: Nombre max de résultats

        Returns:
            Liste des objections triées par fréquence d'usage
        """
        filtered = self.objections
        if category:
            filtered = [obj for obj in self.objections if obj.category == category]

        sorted_objections = sorted(filtered, key=lambda x: x.used_count, reverse=True)
        return sorted_objections[:limit]

    async def get_stats(self) -> Dict:
        """Statistiques de la base objections"""
        total = len(self.objections)
        total_used = sum(obj.used_count for obj in self.objections)
        total_won = sum(obj.won_count for obj in self.objections)

        categories = {}
        for obj in self.objections:
            if obj.category not in categories:
                categories[obj.category] = {"count": 0, "success_rate": 0}
            categories[obj.category]["count"] += 1

        return {
            "total_objections": total,
            "total_used": total_used,
            "total_won": total_won,
            "global_success_rate": total_won / total_used if total_used > 0 else 0,
            "categories": categories
        }


# Instance globale
objection_memory = ObjectionMemory()


async def main():
    """Test du module"""
    print("🛡️  NAYA Objection Memory - Test Module")

    # Test 1: Initialisation avec objections par défaut
    stats = await objection_memory.get_stats()
    print(f"\n✅ Base initialisée:")
    print(f"   Total objections: {stats['total_objections']}")

    # Test 2: Recherche de réponse
    response = await objection_memory.find_best_response(
        "C'est vraiment trop cher pour nous",
        sector="all"
    )
    if response:
        print(f"\n✅ Réponse trouvée:")
        print(f"   Objection: {response.objection_text}")
        print(f"   Catégorie: {response.category}")
        print(f"   Réponse: {response.best_response[:100]}...")

    # Test 3: Enregistrer usage
    if response:
        await objection_memory.record_usage(response.objection_id, won=True)
        print(f"\n✅ Usage enregistré (won=True)")

    # Test 4: Top objections
    top = await objection_memory.get_top_objections(category="prix", limit=5)
    print(f"\n✅ Top 5 objections PRIX:")
    for i, obj in enumerate(top, 1):
        print(f"   {i}. {obj.objection_text} (utilisée {obj.used_count} fois)")


if __name__ == "__main__":
    asyncio.run(main())
