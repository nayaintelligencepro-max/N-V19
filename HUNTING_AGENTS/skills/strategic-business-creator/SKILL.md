---
name: strategic-business-creator
description: Agent stratégique business — transforme les opportunités détectées par les 3 autres agents en business models complets exécutables avec canvas, projections financières, go-to-market, pricing, risques et roadmap. Déclencher TOUJOURS quand l'utilisateur parle de créer un business, business model, business plan, stratégie business, business canvas, projections financières, go-to-market, pricing strategy, roadmap d'exécution, lancer une entreprise, construire un empire, créer un service, modèle économique, ou quand il veut transformer une idée en business concret. Utiliser aussi pour l'analyse de viabilité, la comparaison de business models, ou la planification stratégique.
---

# Strategic Business Creator — Stratège & Créateur d'Empires

## Ce que fait cet agent

Consomme les outputs des 3 autres agents (PainHunter, MegaProject, ForgottenMarket) et les transforme en **BusinessBlueprints** complets prêts à exécuter.

## Chaque blueprint contient

- **Business Model Canvas** complet (value prop, segments, channels, revenue streams, resources, activities, partners, costs)
- **Projections financières** 12-36 mois (revenue, costs, profit, MRR, churn, CAC, LTV)
- **Go-to-Market plan** (canaux, stratégie acquisition, content, partnerships, milestones, KPIs, budget)
- **Pricing strategy** (value-based, market-based, ou acquisition-based)
- **Risk matrix** (probabilité × impact × mitigation)
- **Execution roadmap** (phases, durées, actions)
- **Scoring 4 axes**: Viabilité, Scalabilité, Profitabilité, Exécution

## Revenue models supportés

ONE_TIME_SERVICE, RECURRING_SAAS, COMMISSION, LICENSING, FREEMIUM, MARKETPLACE, CONSULTING_RETAINER, PROJECT_BASED, HYBRID

## Intégration NAYA

```python
from HUNTING_AGENTS import StrategicBusinessCreator

creator = StrategicBusinessCreator()
creator.set_pain_hunter(pain_hunter)
creator.set_mega_hunter(mega_hunter)
creator.set_market_conqueror(market_conqueror)
creator.set_database(db)

result = creator.strategic_cycle()
cash = creator.get_cash_businesses()      # Break-even < 3 mois
empires = creator.get_empire_candidates() # Scalability > 70
```

## Fichier source
`HUNTING_AGENTS/strategic_business_creator.py`
