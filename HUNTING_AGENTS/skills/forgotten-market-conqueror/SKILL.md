---
name: forgotten-market-conqueror
description: Agent autonome de détection et conquête des marchés oubliés — niches ignorées, populations sous-servies, secteurs sans concurrence. Déclencher TOUJOURS quand l'utilisateur parle de marchés oubliés, niches, blue ocean, marchés sous-servis, populations ignorées, diaspora, seniors, zones rurales, secteurs sans concurrence, marchés de niche, opportunités cachées, ou quand il veut conquérir un nouveau marché, lancer un service pour une population mal servie, ou trouver des marchés sans concurrence. Utiliser aussi pour la stratégie de conquête de marché, l'analyse de niches, ou la création d'offres pour des segments ignorés.
---

# Forgotten Market Conqueror — Marchés Oubliés

## Ce que fait cet agent

Scanne, identifie et conquiert les marchés que personne ne sert — zéro concurrence = marge maximale.

## 10 marchés oubliés identifiés (bibliothèque interne)

1. **Digitalisation cabinets d'huissiers** — TAM 48M€, 0 concurrent dédié
2. **Services financiers diaspora africaine** — TAM 4.5Mds€, frais 7-12%
3. **Formation digitale seniors isolés** — TAM 2.4Mds€, 4M de personnes
4. **Marketplace artisans métiers d'art** — TAM 840M€, 80% sans web
5. **Comptabilité micro-entreprises rurales** — TAM 720M€
6. **Recyclage B2B matériaux spécialisés** — TAM 3Mds€
7. **Tourisme médical francophone** — TAM 2.5Mds€
8. **Experts judiciaires gestion cabinet** — TAM 60M€, 0 concurrent
9. **Gestion locative courte durée DOM-TOM** — TAM 375M€
10. **Permaculture / agriculture régénérative SaaS** — TAM 150M€

## Stratégies de conquête

| Stratégie | Description |
|-----------|-------------|
| FIRST_MOVER | Arriver premier, dominer |
| AGGREGATOR | Agréger offres fragmentées |
| BRIDGE | Pont entre deux mondes |
| DIGITIZER | Numériser un process papier |
| LOCALIZER | Adapter un produit existant |
| UNBUNDLER | Extraire un service d'un bundle |

## Intégration NAYA

```python
from HUNTING_AGENTS import ForgottenMarketConqueror

conqueror = ForgottenMarketConqueror()
conqueror.set_database(db)
result = conqueror.hunt_cycle()
quick_wins = conqueror.get_quick_wins()  # < 30j, fort ROI
```

## Fichier source
`HUNTING_AGENTS/forgotten_market_conqueror.py`
