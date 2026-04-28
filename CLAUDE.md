# CLAUDE.md — NAYA SUPREME V19
# Fichier de contexte souverain — Racine du projet
# Colle ce fichier à la racine et dis à Claude Code : "continue V19"
# Version : 19.0.0 | Propriétaire : Stéphanie MAMA | Territoire : Polynésie française → Global
# Stack : Python 3.11+ | FastAPI | LangGraph | CrewAI | Vector Memory | Multi-Agent | Pipeline Parallèle
# Philosophie : 10x meilleur que tout ce qui existe. Souverain. Transmissible. Réel. Vivant.

# ============================================================
# SECTION 1 — IDENTITÉ ET MISSION
# ============================================================

## IDENTITÉ DU SYSTÈME

NAYA SUPREME est un actif souverain, autonome,automatiser ,hybrid , performant , puissant , efficace , rapide ,capable de creer
 tous types de business générant réellement de l'argent , creer tous types de services répondant aux douleurs, problématiques, besoins discret 
voir trés discretes de différents entreprises , petites ,moyens ,grandes , entreprises infrastructure ou gouvernements ,réellement 
solvables a hautes valeurs a partir du plancher prémium absolue et tous les paliers au dessus .non-vendable et transmissible aux enfants.
Ce n'est pas un prototype. Ce n'est pas un POC. C'est un système vivant en production
qui génère de l'argent réel solvable 

### Mission fondamentale
Détecter des douleurs économiques solvables DISCRÈTES sur les marchés globaux,
générer des offres commerciales sur-mesure, exécuter l'outreach, signer, collecter.

### Ticket cible
- Minimum absolu : 1 000 EUR par contrat (PLANCHER INVIOLABLE)
- Maximum : illimité
- Modèles revenus actifs simultanément : 4+ streams

### Marchés primaires
| Secteur               | Cible                       | Douleur                              | Ticket moyen  |
|-----------------------|-----------------------------|--------------------------------------|---------------|
| Transport & Logistique| DSI, RSSI, Directeurs Ops   | Conformité NIS2, vulnérabilités OT   | 15–40k EUR    |
| Énergie & Utilities   | Responsables SCADA, OT Mgrs | Cyberattaques infrastructure critique| 40–80k EUR    |
| Manufacturing         | Directeurs Usine, CTO       | Downtime, ransomware automates       | 15–40k EUR    |
| IEC 62443 Compliance  | RSSI, Auditeurs              | Gaps conformité réglementaire        | 15–80k EUR    |

Géographie : Polynésie française → Europe, Moyen-Orient, Amérique du Nord, Afrique francophone
Langues : Français, Anglais, Espagnol, Portugais, Arabe, Wolof

# ============================================================
# SECTION 2 — 11 AGENTS IA AUTONOMES
# ============================================================
# Chaque agent est un module Python indépendant, async, production-ready.
# Tous les agents héritent de NayaBaseAgent. Zéro placeholder. Zéro pass.
# Tous les agents tournent en parallèle via le MultiAgentOrchestrator.

## AGENT 1 — PAIN HUNTER AGENT
# Fichier : agents/pain_hunter_agent.py
# Rôle : Scanner en continu les marchés pour détecter des douleurs solvables avec budget ≥ 1 000 EUR
# Sources : offres d'emploi RSSI, actualités cyberattaques, appels d'offres, LinkedIn, Serper
# Déclenchement : toutes les 60 minutes
# Output : liste de Pain(sector, company, decision_maker, signal_source, budget_estimate, score)
# Score ≥ 70/100 → alimente automatiquement le ProspectionWorkflow

PAIN_SIGNALS = {
    "job_offers": ["RSSI OT", "IEC 62443", "OT Security Engineer", "SCADA Security", "Responsable cybersécurité industrielle"],
    "news_triggers": ["cyberattaque usine", "ransomware industriel", "conformité NIS2", "audit OT", "incident SCADA"],
    "linkedin_signals": ["poste ouvert cybersécurité OT", "changement de RSSI", "nouveau DSI"],
    "regulatory": ["deadline NIS2", "audit certification", "renouvellement ISO 27001"]
}

SCORING_GRID = {
    "budget_estime_gte_1000": 25,
    "decideur_identifie_contactable": 20,
    "signal_recent_30j": 20,
    "secteur_prioritaire": 15,
    "douleur_discrete_peu_concurrence": 10,
    "connexion_linkedin_commune": 10
}

## AGENT 2 — RESEARCHER AGENT
# Fichier : agents/researcher_agent.py
# Rôle : Enrichir chaque prospect détecté par PainHunterAgent
# Sources : Apollo.io, Hunter.io, Serper, scraping web, LinkedIn
# Input : Pain object
# Output : EnrichedProspect(name, email, phone, linkedin_url, company_size, revenue, tech_stack, ot_signals)
# Règle : si email non trouvé après 3 sources → marquer "manual_required" et alerter Telegram

## AGENT 3 — OFFER WRITER AGENT
# Fichier : agents/offer_writer_agent.py
# Rôle : Générer des offres commerciales ultra-personnalisées (PDF + email + LinkedIn)
# Input : EnrichedProspect + catalogue services + mémoire vectorielle offres gagnantes
# Output : Offer(pdf_path, email_subject, email_body, linkedin_message, price_eur, tier)
# Règle : Consulter offer_memory avant chaque génération pour apprendre des victoires passées
# Tiers : TIER1=1k-5k | TIER2=5k-20k | TIER3=20k-100k | TIER4=100k+

## AGENT 4 — OUTREACH AGENT
# Fichier : agents/outreach_agent.py
# Rôle : Exécuter les séquences multi-touch automatisées (7 touches sur 21 jours)
# Canaux : Email (SendGrid), LinkedIn, WhatsApp Business, Telegram (si B2B tech)
# Séquence obligatoire :
#   Touch 1 — J0  : Email personnalisé accroche signal détecté
#   Touch 2 — J2  : LinkedIn connection + message court
#   Touch 3 — J5  : Email 2 angle valeur (cas anonymisé)
#   Touch 4 — J8  : LinkedIn message question ouverte
#   Touch 5 — J12 : Email 3 objection anticipée + preuve sociale
#   Touch 6 — J16 : Video message 60s (Loom automatisé)
#   Touch 7 — J21 : Email final fermeture bienveillante
# Réponse positive → meeting_booker.py
# Réponse négative → CloserAgent
# Silence total → ZeroWasteEngine recycle le contenu

## AGENT 5 — CLOSER AGENT
# Fichier : agents/closer_agent.py
# Rôle : Gérer les réponses, objections, négociations et closing
# Input : reply_text + prospect_profile + offer_sent
# Output : response_message + recommended_action (relance / escompte / escalade humaine)
# Base objections : 50 objections OT/IEC62443 avec réponses testées
# Règle : décision financière > 500 EUR → validation Telegram avant envoi
# Succès closing → déclencher ContractGeneratorAgent

## AGENT 6 — AUDIT AGENT
# Fichier : agents/audit_agent.py
# Rôle : Générer automatiquement des audits IEC 62443 / NIS2 professionnels (5k–20k EUR)
# Input : company_name + sector + signal_data
# Output : audit_pdf (rapport 20–40 pages) + recommendations + upsell_proposal
# Sections du rapport :
#   - Cartographie OT existante (données publiques + enrichissement)
#   - Gap analysis IEC 62443 par niveaux SL-1 à SL-4
#   - Score conformité NIS2 (0–100)
#   - Roadmap corrective priorisée (quick wins + projets longs)
#   - Estimation budget remédiation
#   - Proposition mission remédiation (upsell automatique)
# Template : professional PDF via reportlab/weasyprint

## AGENT 7 — CONTENT AGENT
# Fichier : agents/content_agent.py
# Rôle : Produire du contenu B2B récurrent (3k–15k EUR/mois abonnement)
# Types : articles LinkedIn, whitepapers OT, newsletters sectorielles, études de cas, posts
# Planification : content_strategy.py génère un calendrier 4 semaines
# Distribution : LinkedIn (API), newsletter (SendGrid), blog (webhook)
# Recycling : chaque contenu produit → versionnée dans ZeroWasteEngine
# Déclenchement : quotidien à 6h00 UTC

## AGENT 8 — CONTRACT GENERATOR AGENT
# Fichier : agents/contract_generator_agent.py
# Rôle : Générer des contrats PDF signables automatiquement après accord client
# Input : offer_accepted + client_data + legal_template
# Output : contract_pdf (signable) + invoice_pdf + payment_link (Deblok.me / PayPal.me)
# Templates : contrat prestation, contrat abonnement SaaS, NDA, lettre de mission
# Règle : toute génération de contrat → log immuable SHA-256 dans audit_logger.py
# Intégration paiement : DeblokEngine + PayPalEngine avec webhook confirmation

## AGENT 9 — REVENUE TRACKER AGENT
# Fichier : agents/revenue_tracker_agent.py
# Rôle : Tracker les 4 streams de revenus en temps réel + projection OODA
# Streams :
#   Stream 1 — Outreach deals (1k–20k EUR/deal)
#   Stream 2 — Audits automatisés (5k–20k EUR/audit)
#   Stream 3 — Contenu B2B récurrent (3k–15k EUR/mois)
#   Stream 4 — SaaS NIS2 Checker (500–2k EUR/mois/client)
# Objectifs OODA M1→M12 (voir section ROADMAP)
# Déclenchement : toutes les 30 minutes
# Output Telegram quotidien 8h00 : briefing complet avec décisions requises

## AGENT 10 — PARALLEL PIPELINE AGENT
# Fichier : agents/parallel_pipeline_agent.py
# Rôle : Gérer 4 slots de projets/deals simultanés avec rechargement automatique
# Slots actifs V19 :
#   SLOT 0 : Catalogue OT Transport (15k EUR)
#   SLOT 1 : IEC62443 Energie NIS2 (40k EUR)
#   SLOT 2 : Formation OT cash 48h (5k EUR)
#   SLOT 3 : Upsell clients actifs (3k EUR MRR)
# Règle : slot libéré → rechargement auto depuis queue triée par score
# Règle : projet fermé → recyclé en v+1 avec objectif +30%
# MAX_PARALLEL_PROJECTS = 4 (configurable)

## AGENT 11 — GUARDIAN AGENT (AUTOSCAN / AUTOCYBERSÉCURITÉ / AUTORÉPARATION)
# Fichier : agents/guardian_agent.py
# Rôle CRITIQUE : Sécurité totale + auto-réparation + surveillance système 24/7
# Cycle : toutes les 6h (configurable via GUARDIAN_SCAN_INTERVAL_H)
# Capacités :

### 11.1 — AUTOSCAN SÉCURITÉ
#   - Audit Bandit (vulnérabilités code Python)
#   - Scan dépendances Safety (CVE connues)
#   - Détection credentials exposés dans le code (regex patterns)
#   - Vérification permissions fichiers sensibles
#   - Analyse logs pour patterns suspects (brute force, exfiltration)
#   - Rotation automatique tokens exposés (SendGrid, Apollo, Telegram)

### 11.2 — AUTOCYBERSÉCURITÉ
#   - Rate limiting toutes les API externes (protection quota)
#   - Isolation automatique module compromis → mode dégradé
#   - Blocage IP suspectes (> 10 appels/minute non autorisés)
#   - Chiffrement AES-256 données prospects et contrats au repos
#   - Log immuable SHA-256 toutes opérations financières
#   - Vault chiffré rotation automatique 30 jours

### 11.3 — AUTORÉPARATION
#   - Détection erreurs récurrentes par pattern (error_classifier.py)
#   - Correction automatique si pattern connu → auto_fixer.py
#   - Redémarrage module KO avec backoff exponentiel
#   - Fallback LLM automatique : Groq → DeepSeek → Anthropic → Templates
#   - Mode dégradé si composant critique KO (degraded_mode.py)
#   - Alerte Telegram si intervention humaine requise

### 11.4 — MONITORING CONTINU
#   - Health check tous modules toutes les 15 minutes
#   - Métriques : latence API, taux d'erreur, file d'attente jobs
#   - Snapshot système toutes les heures (export JSON)
#   - Rapport hebdomadaire PDF envoyé par email

# ============================================================
# SECTION 3 — ARCHITECTURE V19 COMPLÈTE
# ============================================================

```
naya_supreme/                          # Racine du projet
│
├── CLAUDE.md                          # CE FICHIER — contexte souverain
├── main.py                            # Point d'entrée : boot tous les agents
├── requirements.txt                   # Dépendances Python
├── Dockerfile                         # Image production
├── docker-compose.yml                 # Stack complète locale
├── railway.toml                       # Config déploiement Railway
├── .env.example                       # Template variables (jamais de vraies clés ici)
│
├── SECRETS/                           # Clés API chiffrées (NE JAMAIS COMMITTER)
│   └── keys/                          # Fichiers .env.enc chiffrés AES-256
│
├── agents/                            # 11 AGENTS IA AUTONOMES
│   ├── base_agent.py                  # Classe mère NayaBaseAgent
│   ├── pain_hunter_agent.py           # Agent 1 — Détection douleurs marché
│   ├── researcher_agent.py            # Agent 2 — Enrichissement prospects
│   ├── offer_writer_agent.py          # Agent 3 — Génération offres premium
│   ├── outreach_agent.py              # Agent 4 — Séquences multi-touch 7 touches
│   ├── closer_agent.py                # Agent 5 — Closing et objections
│   ├── audit_agent.py                 # Agent 6 — Audits IEC 62443 / NIS2
│   ├── content_agent.py               # Agent 7 — Contenu B2B récurrent
│   ├── contract_generator_agent.py    # Agent 8 — Contrats + facturation
│   ├── revenue_tracker_agent.py       # Agent 9 — Tracking 4 streams revenus
│   ├── parallel_pipeline_agent.py     # Agent 10 — 4 slots projets parallèles
│   └── guardian_agent.py              # Agent 11 — Sécurité / scan / réparation
│
├── workflows/                         # LangGraph stateful workflows
│   ├── state_manager.py               # État persistant (TypedDict)
│   ├── prospection_workflow.py        # pain → enrichissement → offre → séquence → contrat
│   ├── audit_workflow.py              # signal → audit IEC62443 → rapport → upsell
│   ├── content_workflow.py            # brief → article → distribution → recycling
│   ├── closing_workflow.py            # réponse → objection → négociation → signature
│   └── node_registry.py              # Registre nœuds LangGraph
│
├── memory/                            # Mémoire vectorielle persistante
│   ├── vector_store.py                # Store hybride ChromaDB local + Pinecone cloud
│   ├── prospect_memory.py             # Chaque interaction prospect mémorisée
│   ├── offer_memory.py                # Offres gagnantes mémorisées (learning)
│   ├── objection_memory.py            # 50+ objections + réponses gagnantes
│   ├── market_memory.py               # Patterns marché accumulés
│   └── knowledge_accumulator.py      # Capitalisation continue cross-agents
│
├── core/                              # Moteur central
│   ├── engine.py                      # Orchestrateur async principal
│   ├── scheduler.py                   # 20 jobs autonomes planifiés (APScheduler)
│   ├── multi_agent_orchestrator.py    # Lance les 11 agents en parallèle
│   ├── pipeline_manager.py            # Gestion 4 slots parallèles
│   ├── resilience_engine.py           # Fallback modes FULL/HYBRID/CLOUD/OFFLINE
│   └── llm_router.py                  # Groq→DeepSeek→Anthropic→HuggingFace→Templates
│
├── intelligence/                      # Intelligence marché
│   ├── pain_detector.py               # Scan douleurs discrètes B2B
│   ├── signal_scanner.py              # Signaux faibles (news, jobs, LinkedIn)
│   ├── qualifier.py                   # Lead scoring 0–100
│   ├── objection_handler.py           # 50 objections + réponses IA
│   ├── ab_testing.py                  # A/B testing messages et offres
│   ├── pricing_intelligence.py        # Pricing dynamique contextuel
│   └── competitor_monitor.py          # Veille concurrents
│
├── hunting/                           # Moteur de chasse (10x Clay.com)
│   ├── apollo_agent.py                # Enrichissement Apollo.io
│   ├── linkedin_agent.py              # Prospection LinkedIn Sales Nav
│   ├── web_scraper.py                 # Scraping signaux faibles
│   ├── job_offer_scanner.py           # Offres emploi RSSI = douleur détectée
│   ├── news_scanner.py                # Actualités sectorielles
│   ├── email_finder.py                # Recherche emails décideurs
│   ├── contact_enricher.py            # Enrichissement multi-source
│   └── auto_hunt_seeder.py            # Chasse automatique horaire
│
├── outreach/                          # Séquenceur (10x Instantly.ai)
│   ├── sequence_engine.py             # Moteur séquences multi-touch
│   ├── email_personalizer.py          # Personnalisation IA niveau individuel
│   ├── followup_sequencer.py          # Relances J+2/J+5/J+10 adaptatives
│   ├── linkedin_messenger.py          # Outreach LinkedIn automatisé
│   ├── whatsapp_agent.py              # Outreach WhatsApp Business
│   ├── ab_sequence_tester.py          # A/B testing séquences complètes
│   ├── reply_handler.py               # Gestion réponses automatique
│   └── meeting_booker.py              # Prise de RDV automatique (Calendly API)
│
├── audit/                             # Moteur d'audit automatisé
│   ├── iec62443_auditor.py            # Audit IEC 62443 automatisé
│   ├── nis2_checker.py                # Checklist conformité NIS2 (SaaS MVP M6)
│   ├── ot_vulnerability_scanner.py    # Scanner vulnérabilités OT
│   ├── report_generator.py            # Rapport PDF professionnel (reportlab)
│   ├── recommendation_engine.py       # Recommandations personnalisées
│   └── audit_pricing.py               # Tarification selon scope détecté
│
├── content/                           # Moteur contenu B2B
│   ├── content_strategy.py            # Stratégie contenu par secteur
│   ├── article_generator.py           # Articles LinkedIn / blog
│   ├── whitepaper_generator.py        # Whitepapers techniques OT
│   ├── case_study_generator.py        # Études de cas anonymisées
│   ├── newsletter_engine.py           # Newsletter sectorielle auto
│   └── content_distributor.py         # Distribution multi-canal
│
├── revenue/                           # Moteur revenus
│   ├── deblokme_integration.py        # Paiements Deblok.me (Polynésie)
│   ├── paypalme_integration.py        # Paiements PayPal.me
│   ├── stripe_integration.py          # Paiements Stripe diriger vers les liens paypal.me et déblok.me
│   ├── revenue_tracker.py             # Tracking 4 streams temps réel
│   ├── contract_generator.py          # Contrats auto PDF signables
│   ├── invoice_engine.py              # Facturation automatique
│   ├── subscription_manager.py        # Gestion abonnements SaaS
│   └── cashflow_projector.py          # Projection cashflow 90 jours
│
├── security/                          # Sécurité & auto-réparation (Guardian)
│   ├── self_scanner.py                # Audit sécurité auto (Bandit + Safety)
│   ├── vulnerability_patcher.py       # Auto-correction failles connues
│   ├── secrets_manager.py             # Gestion clés API chiffrées (AES-256)
│   ├── audit_logger.py                # Log immuable SHA-256
│   ├── threat_detector.py             # Détection comportements suspects
│   ├── health_monitor.py              # Monitoring santé tous modules
│   ├── error_classifier.py            # Classification erreurs par pattern
│   ├── auto_fixer.py                  # Réparation automatique si pattern connu
│   ├── degraded_mode.py               # Mode dégradé si composant KO
│   └── self_optimizer.py              # Optimisation continue performances
│
├── catalogue/                         # Catalogue OT
│   ├── service_catalogue.py           # 400+ services IEC 62443 documentés
│   ├── pricing_engine.py              # Pricing dynamique contextuel
│   ├── offer_sizer.py                 # Calibration taille offre
│   └── vertical_saas_engine.py        # Moteur SaaS vertical niche
│
├── dashboard/                         # Supervision 2h/jour
│   ├── telegram_bot.py                # Interface contrôle Telegram
│   ├── daily_briefing.py              # Briefing quotidien 8h00 Polynésie
│   ├── decision_queue.py              # File décisions > 500 EUR à valider
│   ├── performance_report.py          # KPIs temps réel
│   └── action_validator.py            # Validation actions critiques
│
├── projects/                          # 7 projets moteurs revenus
│   ├── project_executor.py
│   ├── project_registry.py
│   ├── parallel_runner.py
│   └── registered/
│       ├── ot_audit_sprint.py         # Audit OT flash 5k EUR en 5 jours
│       ├── iec62443_compliance.py     # Mission conformité 15k–50k EUR
│       ├── content_agency.py          # Agence contenu B2B 3k/mois
│       ├── nis2_saas.py               # SaaS NIS2 checker 500 EUR/mois/client
│       ├── ot_training_program.py     # Programme formation OT 8k EUR
│       ├── botanica_engine.py         # E-commerce cosmétiques naturels
│       └── tiny_house_engine.py       # Maisons modulaires tropicales
│
├── database/
│   ├── models.py                      # SQLAlchemy models
│   ├── migrations/                    # Alembic
│   └── repositories/                  # Pattern Repository
│
├── assets/
│   ├── asset_recycler.py              # Zéro-déchet : réutilisation assets
│   └── knowledge_base.py              # Base connaissance accumulative
│
├── config/
│   ├── settings.py                    # Configuration globale
│   ├── api_keys.py                    # Wizard configuration API
│   └── deployment.py                  # Config Railway/Render/Cloud Run
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
└── scripts/
    ├── deploy_railway.sh
    ├── health_check.py
    └── setup_wizard.py
```

# ============================================================
# SECTION 4 — RÈGLES ABSOLUES POUR CLAUDE CODE
# ============================================================

## RÈGLE 1 — CODE PRODUCTION-READY, ZÉRO COMPROMIS
# ZÉRO placeholder. ZÉRO "# TODO". ZÉRO "pass" dans une méthode métier.
# ZÉRO credential hardcodé. JAMAIS.
# Chaque fonction : docstring + type hints + gestion d'erreur explicite.
# Si méthode stub trouvée → compléter immédiatement ou signaler.

## RÈGLE 2 — STRUCTURE AGENT OBLIGATOIRE
```python
from agents.base_agent import NayaBaseAgent
from typing import TypedDict
import asyncio

class PainHunterAgent(NayaBaseAgent):
    """
    Agent 1 — Détecte les douleurs économiques solvables sur les marchés B2B OT.
    Déclenchement : toutes les 60 minutes via scheduler.
    Output : list[Pain] avec score ≥ 70 pour activer ProspectionWorkflow.
    """
    
    async def run(self) -> list[dict]:
        try:
            signals = await asyncio.gather(
                self.scan_job_offers(),
                self.scan_news(),
                self.scan_linkedin()
            )
            pains = self.score_and_filter(signals)
            await self.memory.save_pains(pains)
            await self.notify_if_high_score(pains)
            return pains
        except Exception as e:
            await self.audit_logger.log_critical(e, context=locals())
            await self.resilience_engine.handle_agent_failure("pain_hunter")
            raise
```

## RÈGLE 3 — LANGGRAPH WORKFLOWS STATEFUL
```python
from langgraph.graph import StateGraph
from typing import TypedDict

class ProspectionState(TypedDict):
    prospect_id: str
    enrichment_data: dict
    offer: dict
    sequence_step: int
    last_response: str
    score: float
    deal_value_eur: float

workflow = StateGraph(ProspectionState)
workflow.add_node("enrich", researcher_agent.run)
workflow.add_node("score", qualifier.score)
workflow.add_node("generate_offer", offer_writer_agent.run)
workflow.add_node("send_outreach", outreach_agent.run)
workflow.add_node("handle_reply", closer_agent.run)
workflow.add_node("generate_contract", contract_generator_agent.run)
workflow.add_conditional_edges("score", route_by_score)
```

## RÈGLE 4 — MÉMOIRE VECTORIELLE AVANT CHAQUE OFFRE
```python
from memory.vector_store import NayaVectorStore

store = NayaVectorStore()

# TOUJOURS consulter les victoires passées avant de générer une offre
similar_wins = await store.search_similar_wins(prospect_profile)
objection_responses = await store.get_best_objection_responses(sector)
offer = await offer_writer_agent.generate(prospect, context=similar_wins)

# TOUJOURS mémoriser chaque interaction
await store.save_interaction({
    "type": "offer_sent",
    "sector": prospect.sector,
    "offer_value": offer.price_eur,
    "message_variant": "A",
    "prospect_profile": prospect.to_dict()
})
```

## RÈGLE 5 — ASYNC PARTOUT OÙ C'EST PERTINENT
```python
# CORRECT
async def hunt_prospects(sector: str) -> list:
    async with asyncio.TaskGroup() as tg:
        apollo_task = tg.create_task(apollo_agent.search(sector))
        serper_task = tg.create_task(serper_hunter.search(sector))
        job_task = tg.create_task(job_offer_scanner.scan(sector))

# INTERDIT — bloquant = mort du pipeline
def scan_market_pain(sector: str):
    response = requests.get(...)
```

## RÈGLE 6 — MULTI-LLM FALLBACK ROUTER
```python
LLM_PRIORITY = [
    "groq/llama-3.3-70b",             # Rapide et gratuit (premier choix)
    "anthropic/claude-sonnet-4-6",     # Raisonnement complexe
    "openai/gpt-4o",                   # Polyvalent
    "deepseek/deepseek-chat",          # Économique
    "openai/gpt-4o-mini",              # Fallback ultra-économique
    "template"                         # Zéro API — templates statiques
]
# Basculement automatique si quota/erreur/latence > 10s
# Toutes les clés dans SECRETS/keys/
```

## RÈGLE 7 — SECRETS — RÈGLE ABSOLUE
# JAMAIS de clé API, mot de passe, token dans le code source.
# TOUJOURS via os.environ.get() ou secrets_manager.get()
# TOUTES LES CLÉS API SONT DANS LE DOSSIER SECRETS/
# .env.example toujours à jour avec chaque nouvelle variable

## RÈGLE 8 — GESTION D'ERREURS EXPLICITE ET RÉSILIENCE
```python
try:
    result = await external_api_call()
except APIRateLimitError:
    await resilience_engine.switch_fallback("api_name")
    result = await fallback_call()
except NetworkError as e:
    await degraded_mode.activate("api_name")
    await telegram_notifier.alert(f"API down: {e}")
except Exception as e:
    await audit_logger.log_critical(e, context=locals())
    raise
```

## RÈGLE 9 — PARALLÉLISME 4 PROJETS SIMULTANÉS
```python
async def run_parallel_agents():
    async with asyncio.TaskGroup() as tg:
        tg.create_task(pain_hunter_agent.run())
        tg.create_task(researcher_agent.run())
        tg.create_task(outreach_agent.run())
        tg.create_task(content_agent.run())
        tg.create_task(revenue_tracker_agent.run())
        tg.create_task(guardian_agent.run())  # toujours actif
```

## RÈGLE 10 — PLANCHER 1 000 EUR INVIOLABLE
```python
MIN_CONTRACT_VALUE_EUR = 1000

def validate_offer_price(price: float) -> float:
    if price < MIN_CONTRACT_VALUE_EUR:
        raise ValueError(f"Prix {price} EUR inférieur au plancher {MIN_CONTRACT_VALUE_EUR} EUR. INTERDIT.")
    return price
```

# ============================================================
# SECTION 5 — ROADMAP OODA M1 → M12
# ============================================================

# Basée sur : Pack Audit Express 15k EUR | taux conv. 35% | pipeline 7j
# OODA = Observe → Orient → Decide → Act

ROADMAP = {
    "M1":  {"target": 5000,   "max": 12000,  "focus": "OBSERVE — cartographier 50 prospects OT"},
    "M2":  {"target": 15000,  "max": 25000,  "focus": "ORIENT — qualifier top 10, pitcher Audit Express"},
    "M3":  {"target": 25000,  "max": 40000,  "focus": "DECIDE — 3 deals chauds, closing calls"},
    "M4":  {"target": 35000,  "max": 50000,  "focus": "ACT — convertir one-shot en récurrents"},
    "M5":  {"target": 45000,  "max": 60000,  "focus": "OBSERVE — partenariats Siemens/ABB + upsell"},
    "M6":  {"target": 60000,  "max": 80000,  "focus": "ORIENT — lancer SaaS NIS2 MVP + MRR"},
    "M7":  {"target": 70000,  "max": 90000,  "focus": "DECIDE — 3 grands comptes CAC40 OT"},
    "M8":  {"target": 80000,  "max": 100000, "focus": "ACT — MRR 10k EUR + deal Premium 80k EUR"},
    "M9":  {"target": 85000,  "max": 110000, "focus": "OBSERVE — analyser conv par secteur"},
    "M10": {"target": 90000,  "max": 115000, "focus": "ORIENT — upsell 100% clients existants +30%"},
    "M11": {"target": 95000,  "max": 120000, "focus": "DECIDE — contrats annuels avant clôture budgets"},
    "M12": {"target": 100000, "max": 130000, "focus": "ACT — 2 consultants OT + MRR > 20k EUR"}
}

# Total objectif annuel : ~705 000 EUR | Max annuel : ~932 000 EUR

# ============================================================
# SECTION 6 — CATALOGUE OT V19
# ============================================================

PACKS_COMMERCIAUX = {
    "Pack Audit Express":   {"prix": 15000, "taux_conv": 0.35, "pipeline_j": 7,  "secteur": "Transport, Industrie"},
    "Pack Securite Avancee":{"prix": 40000, "taux_conv": 0.22, "pipeline_j": 14, "secteur": "Energie, OIV"},
    "Pack Premium Full":    {"prix": 80000, "taux_conv": 0.12, "pipeline_j": 21, "secteur": "CAC40, Grands comptes"}
}

# 400 services IEC 62443 répartis sur 4 secteurs
SECTEURS_CATALOGUE = [
    "IEC62443 Standard (100 prix réels extraits PDF, moy. 39 681 EUR)",
    "Energie / Infra Critiques (EDF, Enedis, RTE, GRTgaz)",
    "Transport / Logistique (SNCF, RATP, CMA CGM, ADP)",
    "Industrie / Usine (Airbus, Michelin, Renault, Alstom)"
]

TIERS_SERVICE = {
    "TIER1_QUICK_WINS":       {"min": 1000,   "max": 5000},
    "TIER2_PROJETS_COURTS":   {"min": 5000,   "max": 20000},
    "TIER3_CONTRATS_LONGS":   {"min": 20000,  "max": 100000},
    "TIER4_RETAINERS":        {"min": 100000, "max": None}
}

# ============================================================
# SECTION 7 — COMMANDES TELEGRAM V19
# ============================================================

TELEGRAM_COMMANDS = """
/status          → État global complet (tous les 11 agents)
/revenue         → Dashboard revenus temps réel (4 streams)
/pipeline        → 4 slots + métriques
/targets         → Objectifs OODA du mois + actions du jour
/agents          → État de chacun des 11 agents
/validate [id]   → Valider action en attente (> 500 EUR)
/hunt [secteur]  → Lancer chasse manuelle
/offer [lead_id] → Générer offre pour un lead spécifique
/audit [company] → Lancer audit IEC 62443 automatisé
/content [theme] → Générer contenu B2B
/cashflow        → Projection cashflow 90 jours
/scan            → Lancer scan sécurité Guardian (Agent 11)
/repair          → Lancer auto-réparation Guardian
/logs [n]        → Derniers n logs critiques
/pause           → Pause outreach
/resume          → Reprendre
/ooda            → Prochaine action OODA recommandée par le système
"""

# Briefing quotidien automatique 8h00 Polynésie (UTC-10)
DAILY_BRIEFING_TEMPLATE = """
📊 NAYA BRIEFING — {date}

💰 REVENUS
├── Hier        : {revenue_yesterday} EUR
├── Ce mois     : {revenue_month} EUR
└── Objectif M{month} : {target_month} EUR ({pct_achieved}% atteint)

🤖 AGENTS (11/11)
{agents_status}

🎯 PIPELINE
├── Prospects en séquence  : {prospects_in_sequence}
├── Deals en négociation   : {deals_in_negotiation}
└── Contrats à signer      : {contracts_pending}

⚡ DÉCISIONS REQUISES (> 500 EUR)
{decisions_pending}

🛡️ GUARDIAN (Agent 11)
├── Dernier scan    : {last_scan}
├── Vulnérabilités  : {vulns_found}
└── Auto-réparations: {repairs_done}

🔧 SANTÉ SYSTÈME : {health_status}
"""

# ============================================================
# SECTION 8 — STACK TECHNIQUE V19
# ============================================================

STACK = {
    "backend":       "Python 3.11+ / FastAPI / SQLite / SQLAlchemy / aiohttp",
    "agents":        "CrewAI + LangGraph stateful workflows",
    "memory":        "ChromaDB (local) + Pinecone (cloud) hybride",
    "llm_chain":     "Groq → DeepSeek → Anthropic → OpenAI → HuggingFace → Templates",
    "paiements":     "Deblok.me + PayPal.me + Stripe (Polynésie française)",
    "notifications": "Telegram Bot (commandes + briefing quotidien 8h)",
    "prospection":   "Serper.dev + Apollo.io + Hunter.io + LinkedIn",
    "infra":         "Docker + Railway (primaire) + Render (backup) + Cloud Run",
    "dashboard":     "TORI_APP React PWA + Telegram",
    "securite":      "AES-256 + Bandit + Safety + audit_logger SHA-256"
}

APIS_EXTERNES = {
    "CRITIQUE": ["Apollo.io", "SendGrid", "Deblok.me", "Telegram Bot API"],
    "HAUTE":    ["Anthropic Claude", "OpenAI GPT-4o", "Serper.dev", "Pinecone", "Calendly"],
    "MOYENNE":  ["Mistral", "Hunter.io", "LinkedIn", "Instantly.ai", "PayPal.me"]
}

# ============================================================
# SECTION 9 — VARIABLES D'ENVIRONNEMENT
# ============================================================
# TOUTES LES CLÉS SONT DANS SECRETS/keys/ — JAMAIS DANS LE CODE

ENV_REQUIRED = """
# === LLM ===
ANTHROPIC_API_KEY=
GROQ_API_KEY=
DEEPSEEK_API_KEY=
OPENAI_API_KEY=
MISTRAL_API_KEY=

# === PROSPECTION ===
APOLLO_API_KEY=
SERPER_API_KEY=
HUNTER_API_KEY=
LINKEDIN_CLIENT_ID=
LINKEDIN_CLIENT_SECRET=
LINKEDIN_ACCESS_TOKEN=

# === OUTREACH ===
SENDGRID_API_KEY=
GMAIL_OAUTH=
INSTANTLY_API_KEY=
CALENDLY_API_KEY=

# === MÉMOIRE VECTORIELLE ===
PINECONE_API_KEY=
PINECONE_ENVIRONMENT=
CHROMA_HOST=localhost

# === PAIEMENTS (Polynésie française) ===
DEBLOKME_SECRET_KEY=
DEBLOKME_WEBHOOK_SECRET=
PAYPALME_CLIENT_URL=
PAYPAL_CLIENT_ID=
PAYPAL_CLIENT_SECRET=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=

# === SUPERVISION ===
TELEGRAM_BOT_TOKEN=
TELEGRAM_OWNER_CHAT_ID=
TORI_APP=DASHBOARD CENTRE DE COMMANDE_ ECHANGE AVEC LE SYSTEME DE SIGNATURE DE CONTRAT ET AUTRES 
# === BASE DE DONNÉES ===
DATABASE_URL=sqlite:///data/naya.db
REDIS_URL=

# === SÉCURITÉ ===
ENCRYPTION_KEY=
JWT_SECRET=
VAULT_KEY=

# === CONFIG ===
ENVIRONMENT=production
TIMEZONE=Pacific/Tahiti
MIN_CONTRACT_VALUE=1000
DECISION_THRESHOLD_EUR=500
MAX_PARALLEL_PROJECTS=4
DAILY_BRIEFING_HOUR=8
GUARDIAN_SCAN_INTERVAL_H=6
LLM_TIMEOUT_S=10
LOG_LEVEL=INFO
"""

# ============================================================
# SECTION 10 — RÉSISTANCE ET MODES DE SURVIE
# ============================================================

RESILIENCE_MODES = {
    "FULL":    "Python OK — 100% autonome, tous les 11 agents actifs",
    "HYBRID":  "Python partiel — Webhooks Make.com/Zapier en backup",
    "CLOUD":   "Python down — Bot Telegram indépendant opérationnel",
    "OFFLINE": "Tout down — SURVIVAL_GUIDE.md + scripts bash manuels"
}

# Exports automatiques toutes les heures
HOURLY_EXPORTS = [
    "data/exports/naya_snapshot_LATEST.json",
    "data/exports/catalogue_ot_COMPLET.csv",
    "data/exports/pipeline_actif.csv",
    "data/exports/agents_status.json",
    "SURVIVAL_GUIDE.md",
    "data/exports/naya_survival.sh"
]

# ============================================================
# SECTION 11 — PROCHAINES PRIORITÉS DE DÉVELOPPEMENT
# ============================================================

PRIORITIES = {
    "CRITIQUE_SESSION_IMMEDIATE": [
        "1. Compléter tous les stubs pass dans les 11 agents",
        "2. Multi-agent CrewAI — 11 agents spécialisés complets",
        "3. LangGraph workflows — prospection_workflow + audit_workflow",
        "4. Vector memory — prospect_memory + offer_memory opérationnels",
        "5. Apollo hunting — pipeline complet signal → prospect enrichi",
        "6. Guardian Agent 11 — autoscan + autoréparation + monitoring"
    ],
    "IMPORTANT_CETTE_SEMAINE": [
        "7. Séquenceur 7 touches — reply_handler + objection_handler",
        "8. Audit engine IEC 62443 — rapport PDF professionnel générable",
        "9. Content engine — article + whitepaper automatisés",
        "10. Meeting booker — intégration Calendly",
        "11. Daily briefing — Telegram 8h00 automatique"
    ],
    "AMELIORATION_SEMAINE_SUIVANTE": [
        "12. SaaS NIS2 checker MVP — objectif M6",
        "13. Self-optimizer — optimisation continue basée sur données",
        "14. Cashflow projector — projection 90 jours",
        "15. A/B testing complet",
        "16. Multi-langue outreach — 6 langues opérationnelles",
        "17. Déploiement Railway — 5 minutes avec Dockerfile prêt",
        "18. Webhook Make.com — backup résilience niveau 2"
    ]
}

# ============================================================
# SECTION 12 — 7 LOIS SOUVERAINES (NE JAMAIS VIOLER)
# ============================================================

LOIS_SOUVERAINES = """
1. L'argent valide tout. Un contrat signé > 10 000 lignes de code théorique.
2. La mémoire est le moat. Plus NAYA accumule des données sur ce qui fonctionne, plus il devient imbattable.
3. OODA sur tout. Observer avant d'agir. Toute action sans observation préalable est du bruit.
4. 10x meilleur. Chaque module dépasse Clay, Instantly, n8n sur son domaine.
5. 2h de supervision max. Tout ce qui dépasse 2h/jour doit être automatisé.
6. Zéro déchet. Chaque email, rapport, contact, code = réutilisé et versionné.
7. Transmissible. Le système doit tourner sans son créateur. Documenté, autonome, vivant.
"""

# PRINCIPES TECHNIQUES DIRECTEURS
PRINCIPES_TECHNIQUES = """
P1. NAYA est souverain. Aucun outil loué ne peut le remplacer ou le couper.
P2. Code production-ready uniquement. Zéro POC, zéro placeholder.
P3. Async partout pour les I/O. Jamais de requests.get() bloquant dans le pipeline.
P4. Mémoire vectorielle = avantage concurrentiel. Chaque interaction apprend.
P5. Réalisme absolu. Vrais clients, vrais paiements, vrais contrats.
P6. 11 agents en parallèle. L'orchestration est le moteur, pas les agents individuels.
P7. Guardian toujours actif. La sécurité n'est jamais optionnelle.
"""

# ============================================================
# FIN DU FICHIER
# ============================================================
# CLAUDE.md V19 — Document vivant. Mettre à jour à chaque changement majeur.
# Propriétaire : Stéphanie MAMA | Système : NAYA SUPREME | Horizon : 15 ans
# Territoire : Polynésie française → Global | Objectif annuel : 705 000 EUR
