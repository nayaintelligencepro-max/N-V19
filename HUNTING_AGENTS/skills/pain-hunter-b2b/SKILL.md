---
name: pain-hunter-b2b
description: Agent autonome de chasse de douleurs réelles B2B, B2A et gouvernementales. Déclencher TOUJOURS quand l'utilisateur parle de chasser des douleurs, détecter des problèmes d'entreprise, trouver des opportunités B2B, prospecter, identifier des besoins discrets, chercher des clients en difficulté, scanner des secteurs, ou quand il mentionne cash rapide, moyen terme, long terme, pipeline commercial, douleurs cachées, signaux faibles, ou toute forme de détection d'opportunité business. Utiliser aussi quand l'utilisateur veut enrichir des contacts, trouver des décisionnaires, ou qualifier des prospects. Fonctionne avec LinkedIn, Crunchbase, Apollo, Hunter.io, Pappers, Google News.
---

# Pain Hunter B2B — Agent de Chasse de Douleurs

## Ce que fait cet agent

Détecte autonomement les douleurs RÉELLES, discrètes et confidentielles des entreprises B2B, administrations (B2A) et entités gouvernementales, puis les transforme en opportunités commerciales classées en 3 catégories:

| Catégorie | Délai | Valeur | Description |
|-----------|-------|--------|-------------|
| CASH_RAPIDE | 24h-7j | 10k-150k€ | Douleur critique, résolution immédiate |
| MOYEN_TERME | 7j-30j | 50k-500k€ | Douleur forte, projet structuré |
| LONG_TERME | 30j+/abo | 100k-2M€/an | Transformation, abonnement récurrent |

## Sources API réelles

- **LinkedIn Sales Navigator** (via RapidAPI) — postes urgents = signal douleur
- **Crunchbase** — levées de dette, pivots, layoffs
- **Apollo.io** — enrichissement contacts décisionnaires
- **Hunter.io** — vérification emails
- **Pappers** — procédures collectives, bilans, tribunaux de commerce
- **Google News** (via SerpAPI) — alertes sectorielles

## Cycle de chasse

1. **COLLECT** — Récolte signaux depuis toutes les sources API
2. **QUALIFY** — Filtre le bruit, qualifie les vraies douleurs
3. **CLASSIFY** — Classe en CASH_RAPIDE / MOYEN_TERME / LONG_TERME
4. **BUILD OFFER** — Construit une offre irrésistible (prix basé sur la douleur)
5. **ENRICH** — Trouve le décisionnaire (nom, email, LinkedIn, téléphone)
6. **PERSIST** — Sauvegarde en DB + injecte dans le cash engine NAYA
7. **STREAM** — Diffuse vers TORI en temps réel

## Intégration NAYA

```python
from HUNTING_AGENTS import PainHunterB2B

hunter = PainHunterB2B()
hunter.set_database(db)
hunter.set_cash_engine(cash_engine)
hunter.set_discretion(discretion_protocol)

# Cycle manuel
result = hunter.hunt_cycle(sectors=["pme_b2b", "finance_banque"])

# Mode autonome (toutes les heures)
hunter.start_autonomous(interval_seconds=3600)

# Requêtes
cash = hunter.get_cash_rapide()
top = hunter.get_top_opportunities(10)
stats = hunter.get_stats()
```

## Variables d'environnement requises

```
RAPIDAPI_KEY=...          # LinkedIn via RapidAPI
CRUNCHBASE_API_KEY=...    # Crunchbase
APOLLO_API_KEY=...        # Apollo.io
HUNTER_IO_API_KEY=...     # Hunter.io
PAPPERS_API_KEY=...       # Pappers.fr
SERP_API_KEY=...          # SerpAPI (Google News)
```

## Fichier source
`HUNTING_AGENTS/pain_hunter_b2b.py`
