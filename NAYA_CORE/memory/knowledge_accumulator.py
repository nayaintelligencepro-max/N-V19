#!/usr/bin/env python3
"""
NAYA MEMORY - Knowledge Accumulator
Capitalisation continue des connaissances cross-agents
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class KnowledgeEntry:
    """Entrée de connaissance accumulée"""
    knowledge_id: str
    category: str  # technique, marché, commercial, pattern, insight
    title: str
    description: str
    source: str  # agent_name ou external
    confidence_score: float  # 0.0-1.0
    validated: bool
    impact_score: int  # 0-100 (impact business potentiel)
    usage_count: int
    created_at: str
    last_used: Optional[str]
    metadata: Dict


class KnowledgeAccumulator:
    """
    Accumulation continue de connaissances cross-agents
    Permet aux agents d'apprendre les uns des autres
    """

    def __init__(self, storage_path: str = "data/memory/knowledge.json"):
        self.storage_path = storage_path
        self.knowledge_base: List[KnowledgeEntry] = []
        self._load_memory()

    def _load_memory(self):
        """Charge la base de connaissance"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.knowledge_base = [KnowledgeEntry(**entry) for entry in data]
        except FileNotFoundError:
            self.knowledge_base = []
        except Exception as e:
            print(f"Error loading knowledge base: {e}")
            self.knowledge_base = []

    def _save_memory(self):
        """Sauvegarde la base de connaissance"""
        try:
            import os
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump([asdict(entry) for entry in self.knowledge_base], f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving knowledge base: {e}")

    async def add_knowledge(
        self,
        category: str,
        title: str,
        description: str,
        source: str,
        confidence_score: float = 0.8,
        impact_score: int = 50,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Ajoute une nouvelle connaissance

        Args:
            category: Catégorie (technique, marché, commercial, pattern, insight)
            title: Titre court de la connaissance
            description: Description détaillée
            source: Source (nom de l'agent ou externe)
            confidence_score: Niveau de confiance (0.0-1.0)
            impact_score: Impact business potentiel (0-100)
            metadata: Métadonnées additionnelles

        Returns:
            knowledge_id généré
        """
        knowledge_id = f"K_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.knowledge_base)+1}"

        entry = KnowledgeEntry(
            knowledge_id=knowledge_id,
            category=category,
            title=title,
            description=description,
            source=source,
            confidence_score=min(1.0, max(0.0, confidence_score)),
            validated=confidence_score >= 0.9,
            impact_score=min(100, max(0, impact_score)),
            usage_count=0,
            created_at=datetime.now().isoformat(),
            last_used=None,
            metadata=metadata or {}
        )

        self.knowledge_base.append(entry)
        self._save_memory()

        return knowledge_id

    async def search_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        min_confidence: float = 0.5,
        limit: int = 5
    ) -> List[KnowledgeEntry]:
        """
        Recherche dans la base de connaissance

        Args:
            query: Requête de recherche
            category: Filtrer par catégorie (optionnel)
            min_confidence: Score de confiance minimum
            limit: Nombre maximum de résultats

        Returns:
            Liste des connaissances pertinentes
        """
        query_lower = query.lower()
        results = []

        for entry in self.knowledge_base:
            if entry.confidence_score < min_confidence:
                continue
            if category and entry.category != category:
                continue

            # Score de pertinence simple (mots communs)
            title_lower = entry.title.lower()
            desc_lower = entry.description.lower()

            score = 0
            if query_lower in title_lower:
                score += 50
            if query_lower in desc_lower:
                score += 30

            # Bonus pour impact élevé
            score += entry.impact_score * 0.2

            # Bonus pour usage fréquent
            score += min(20, entry.usage_count)

            if score > 0:
                results.append((score, entry))

        # Trier par score et retourner top N
        results.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in results[:limit]]

    async def record_usage(self, knowledge_id: str):
        """
        Enregistre l'utilisation d'une connaissance

        Args:
            knowledge_id: ID de la connaissance utilisée
        """
        for entry in self.knowledge_base:
            if entry.knowledge_id == knowledge_id:
                entry.usage_count += 1
                entry.last_used = datetime.now().isoformat()
                self._save_memory()
                break

    async def get_top_knowledge(self, category: Optional[str] = None, limit: int = 10) -> List[KnowledgeEntry]:
        """
        Récupère les connaissances les plus utilisées/impactantes

        Args:
            category: Filtrer par catégorie (optionnel)
            limit: Nombre maximum de résultats

        Returns:
            Liste des top connaissances
        """
        filtered = self.knowledge_base
        if category:
            filtered = [entry for entry in self.knowledge_base if entry.category == category]

        # Trier par score composite (usage + impact)
        scored = [(entry.usage_count + entry.impact_score, entry) for entry in filtered]
        scored.sort(key=lambda x: x[0], reverse=True)

        return [entry for _, entry in scored[:limit]]

    async def get_stats(self) -> Dict:
        """Statistiques de la base de connaissance"""
        total = len(self.knowledge_base)
        if total == 0:
            return {"total": 0, "by_category": {}, "validated": 0}

        by_category = {}
        by_source = {}
        validated = 0

        for entry in self.knowledge_base:
            by_category[entry.category] = by_category.get(entry.category, 0) + 1
            by_source[entry.source] = by_source.get(entry.source, 0) + 1
            if entry.validated:
                validated += 1

        return {
            "total": total,
            "validated": validated,
            "by_category": by_category,
            "by_source": by_source,
            "avg_confidence": sum(e.confidence_score for e in self.knowledge_base) / total,
            "avg_impact": sum(e.impact_score for e in self.knowledge_base) / total,
            "total_usage": sum(e.usage_count for e in self.knowledge_base)
        }


# Instance globale
knowledge_accumulator = KnowledgeAccumulator()
