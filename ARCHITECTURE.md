# ARCHITECTURE NAYA SUPREME V19 — Mapping Canonique
# Propriétaire : Stéphanie MAMA | Mis à jour : 2026-04-21

## Vue d'ensemble : deux couches distinctes

```
COUCHE MÉTIER / APPLICATION (racine)       COUCHE NOYAU / INFRASTRUCTURE (NAYA_CORE/)
─────────────────────────────────────      ──────────────────────────────────────────
agents/          → agents métier LangGraph  NAYA_CORE/agents/      → protocoles agent de base
api/             → API FastAPI publique      NAYA_CORE/api/         → routes internes kernel
core/            → orchestrateur principal  NAYA_CORE/core/        → moteur exécution bas niveau
memory/          → mémoire vectorielle app  NAYA_CORE/memory/      → store vectoriel natif
monitoring/      → dashboard + alertes      NAYA_CORE/monitoring/  → métriques kernel
workflows/       → workflows LangGraph      NAYA_CORE/workflows/   → graphes état nœuds
```

> **Règle canonique** : Jamais supprimer un dossier en doublon de nom sans vérifier sa couche.
> Les doublons de noms sont intentionnels — ce sont des couches, pas des duplications.

---

## Structure complète des dossiers racine

### Couche Application (racine /)

| Dossier | Rôle | Clé d'entrée |
|---------|------|-------------|
| `agents/` | 11 agents IA (pain hunter, researcher, offer writer, etc.) | `base_agent.py` |
| `api/` | Endpoints FastAPI publics (webhooks, REST clients) | `main_router.py` |
| `audit/` | Moteur d'audit IEC 62443 + NIS2 | `iec62443_auditor.py` |
| `catalogue/` | 400+ services OT, pricing dynamique | `service_catalogue.py` |
| `content/` | Contenu B2B automatisé (articles, whitepapers) | `content_strategy.py` |
| `contracts/` | Génération contrats PDF signables | `contract_generator.py` |
| `data/` | Données runtime (cache, exports, pain_state) | — |
| `docs/` | Documentation technique | — |
| `hunting/` | Chasseurs prospects (Apollo, Serper, LinkedIn) | `auto_hunt_seeder.py` |
| `intelligence/` | Scoring prospects, A/B testing, pricing intel | `qualifier.py` |
| `memory/` | Mémoire vectorielle ChromaDB + Pinecone (couche app) | `vector_store.py` |
| `monitoring/` | Dashboard + alertes + health checks (couche app) | `health_monitor.py` |
| `OUTREACH/` | Séquenceur 7 touches, email/LinkedIn/WhatsApp | `sequence_engine.py` |
| `projects/` | 7 projets moteurs revenus (ot_audit, nis2_saas, etc.) | `project_executor.py` |
| `workflows/` | Workflows LangGraph stateful (couche app) | `prospection_workflow.py` |

### Couche Infrastructure (NAYA_CORE/)

| Module | Rôle |
|--------|------|
| `naya_sovereign_engine.py` | Moteur souverain principal — boot, cycle, fallback |
| `hybrid_autonomy_kernel.py` | Orchestration hybride : 5 slots, 14 langues, 9 canaux, tiers cash |
| `llm_router.py` | Fallback LLM : Groq → DeepSeek → Anthropic → OpenAI → Templates |
| `pipeline_manager.py` | Gestion 4 slots projets parallèles |
| `resilience_engine.py` | Modes FULL / HYBRID / CLOUD / OFFLINE |
| `composite_scorer_v2.py` | Score prospect composite (7 dimensions) |
| `ooda_speed_layer.py` | Boucle OODA accélérée |
| `regulatory_trigger_engine.py` | Triggers réglementaires NIS2 / IEC62443 |
| `warm_path_orchestrator.py` | Chemins chauds (connexions communes) |
| `deal_risk_scorer.py` | Température deals, alertes deals froids |
| `integrations/` | Telegram, Apollo, Serper, Deblok, SendGrid |

### Couche Interface (NAYA_INTERFACE/)

| Module | Rôle |
|--------|------|
| `tori_app_bridge.py` | Bridge FastAPI TORI_APP — 12 endpoints `/tori/*` |
| `telegram_bot.py` | Bot Telegram commandes (15+ commandes `/status`, `/hybrid`, etc.) |

### Couche Moteurs Spécialisés

| Dossier | Description |
|---------|-------------|
| `NAYA_PROJECT_ENGINE/` | Moteur projets business (pain engine, zero waste, mission 10j) |
| `NAYA_REVENUE_ENGINE/` | Tracking 4 streams revenus, Deblok, PayPal, Stripe |
| `NAYA_SCHEDULER/` | 25+ jobs autonomes planifiés (APScheduler) |
| `NAYA_ACCELERATION/` | BlitzHunter 15min, FlashOffer, SalesVelocity |
| `EVOLUTION_SYSTEM/` | Auto-évolution, régression guard, anticipation |
| `NAYA_DASHBOARD/` | Dashboard révenu temps réel |
| `NAYA_COMMAND_GATEWAY/` | Gateway commandes Telegram → NAYA |
| `NAYA_ORCHESTRATION/` | Orchestrateur multi-agents CrewAI |
| `ML_ENGINE/` | Modèles ML scoring et optimisation |
| `HUNTING_AGENTS/` | Agents chasseurs autonomes |
| `CHANNEL_INTELLIGENCE/` | Intelligence canal (email, LinkedIn, WhatsApp) |
| `BUSINESS_ENGINES/` | Moteurs business verticaux (Botanica, TinyHouse, etc.) |
| `EXECUTIVE_ARCHITECTURE/` | Architecture exécutive décisions |
| `NAYA_REAL_SALES/` | Pipeline ventes réelles, contrats, paiements |
| `NAYA_TELEMETRY/` | Télémétrie et observabilité |
| `NAYA_EVENT_STREAM/` | Bus événements async |
| `REAPERS/` | Agents récupération leads abandonnés |
| `PROTOCOLS/` | Protocoles communication inter-agents |
| `PARALLEL_ENGINE/` | Moteur exécution parallèle 4 slots |
| `PERSISTENCE/` | Couche persistance SQLAlchemy + migrations |
| `CONSTITUTION/` | Règles souveraines du système |
| `CLIENT_PORTAL/` | Portail client sécurisé |
| `CATALOGUE_OT/` | Catalogue OT complet (400+ services) |

---

## Règles d'architecture

1. **Séparation des couches** : le code métier (racine) ne dépend jamais du code kernel (NAYA_CORE) directement — il passe par les interfaces (`llm_router`, `pipeline_manager`, `resilience_engine`).

2. **Import order** : `NAYA_CORE` → `NAYA_PROJECT_ENGINE` → `agents/` → `api/`

3. **Secrets** : toujours via `os.environ.get()` ou `NAYA_CORE.integrations.secrets_manager`. Jamais hardcodé.

4. **Async** : toute I/O externe = `async def`. Les jobs scheduler utilisent `asyncio.run()` pour wrapper les coroutines.

5. **Floor 1 000 EUR** : `MIN_CONTRACT_VALUE_EUR = 1000` — validé dans `hybrid_autonomy_kernel.py` et `contract_generator.py`.

6. **Plancher parallèle** : `MAX_PARALLEL_PROJECTS = 4` (configurable via ENV). Géré par `pipeline_manager` et `hybrid_autonomy_kernel`.

---

## Point d'entrée système

```
main.py  →  commandes CLI
           ├── status       → NayaSovereignEngine.status()
           ├── cycle        → NayaSovereignEngine.run_cycle()
           ├── daemon       → NayaSovereignEngine.run_daemon()
           ├── hybrid       → hybrid_autonomy_kernel.daily_autonomous_brief()
           ├── regulatory   → regulatory_trigger_engine.scan()
           ├── ooda         → ooda_speed_layer.run()
           ├── score        → composite_scorer_v2.score()
           ├── warmpath     → warm_path_orchestrator.run()
           ├── tori         → tori_bridge.*
           └── dashboard    → NAYA_DASHBOARD.*
```

---

## Flux principal ProspectionWorkflow

```
PainHunterAgent  →  score ≥ 70
        ↓
ResearcherAgent  →  EnrichedProspect
        ↓
HybridAutonomyKernel → slot + channel + offer (tier 24h/48h/72h)
        ↓
OutreachAgent    →  7 touches sur 21 jours
        ↓
CloserAgent      →  objections + négociation
        ↓
ContractGeneratorAgent → PDF signable + lien paiement
        ↓
RevenueTracker   →  4 streams + projection cashflow
```
