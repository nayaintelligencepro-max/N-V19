---
name: mega-project-hunter
description: Agent autonome de chasse de projets innovants vendables 15M-40M€+ aux GAFAM et grandes infrastructures. Déclencher TOUJOURS quand l'utilisateur parle de gros projets, projets à vendre, acquisitions tech, GAFAM, vendre une startup, exit strategy, projets innovants, M&A, corporate development, brevets, propriété intellectuelle, ou quand il veut créer un produit tech pour le vendre à Google/Microsoft/Amazon/Salesforce/etc. Utiliser aussi pour analyser les gaps technologiques des grandes entreprises, trouver des acquéreurs potentiels, ou construire un pitch deck de vente.
---

# Mega Project Hunter — Projets Innovants 15M-40M€

## Ce que fait cet agent

Détecte les gaps technologiques des GAFAM et grandes infrastructures, conçoit des projets innovants qui comblent ces gaps, et prépare tout pour la vente (15M-40M€+).

## Cibles acquéreurs

- **GAFAM**: Google, Microsoft, Apple, Amazon, Meta
- **Cloud/Infra**: AWS, Azure, GCP, Oracle, Salesforce, SAP
- **Défense/Aéro**: Thales, Airbus, Safran, Dassault
- **Énergie**: EDF, Engie, TotalEnergies
- **Finance**: BNP, Société Générale, AXA
- **Santé**: Sanofi, Roche, Novartis

## Domaines tech couverts

AI/ML, Cybersecurity, Quantum, Edge Computing, Biotech, Cleantech, Fintech, Healthtech, SpaceTech, Web3, Robotics, AR/VR, IoT, SaaS B2B, Data Infrastructure, DevTools

## Cycle de chasse

1. **DETECT** — Identifier gaps via patterns connus + recherche live (SERP API)
2. **BUILD** — Concevoir le projet (nom, tech stack, coût, équipe, moat)
3. **SCORE** — Innovation score + Acquisition fit + Timing
4. **CONTACT** — Trouver les décideurs M&A/Corp Dev (via Apollo)
5. **PERSIST** — Sauvegarder + diffuser vers TORI

## Intégration NAYA

```python
from HUNTING_AGENTS import MegaProjectHunter

hunter = MegaProjectHunter()
hunter.set_database(db)
result = hunter.hunt_cycle()
top = hunter.get_top_projects(5)
```

## Fichier source
`HUNTING_AGENTS/mega_project_hunter.py`
