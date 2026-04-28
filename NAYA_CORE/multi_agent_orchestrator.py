"""
NAYA SUPREME V19.2 — MULTI-AGENT ORCHESTRATOR
Orchestrateur principal pour tous les 11 agents IA
Synchronisation, dépendances, failover, logging immuable
Entry point pour démarrer le système complet
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

# Importer tous les agents
try:
    from NAYA_CORE.agents.pain_hunter import pain_hunter
    from NAYA_CORE.agents.researcher import researcher
    from NAYA_CORE.agents.offer_writer_advanced import offer_writer
    from NAYA_CORE.agents.closer_advanced import closer
    from NAYA_CORE.agents.audit_generator import audit_generator
    from NAYA_CORE.agents.content_engine_advanced import content_engine
    from NAYA_CORE.agents.parallel_pipeline_orchestrator import orchestrator
    from NAYA_CORE.agents.guardian_security import guardian
    # V19.3 — 3 agents manquants maintenant branchés
    from NAYA_CORE.agents.outreach_agent import outreach_agent
    from NAYA_CORE.agents.contract_generator_agent import contract_generator_agent
    from NAYA_CORE.agents.revenue_tracker_agent import revenue_tracker_agent
    # V19.2 SUPREME ENGINE — Détection marchés invisibles
    from NAYA_CORE.v19_2_supreme_engine import get_v192_engine, run_autonomous_quantum_hunt
except ImportError as e:
    print(f"Agent import error: {e}")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class SystemPhase(Enum):
    DETECTION = "detection"
    ENRICHMENT = "enrichment"
    OFFER_GENERATION = "offer_generation"
    OUTREACH = "outreach"
    MONITORING = "monitoring"
    CLOSING = "closing"
    EXECUTION = "execution"
    QUANTUM_HUNT = "quantum_hunt"  # V19.2 — Chasse marchés invisibles

@dataclass
class SystemMetrics:
    """Métriques du système global"""
    phase: SystemPhase
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    agents_active: int = 0
    total_prospects_in_flight: int = 0
    total_revenue_generated: int = 0
    errors_count: int = 0
    
    def to_dict(self):
        return {
            'phase': self.phase.value,
            'timestamp': self.timestamp.isoformat(),
            'agents_active': self.agents_active,
            'total_prospects_in_flight': self.total_prospects_in_flight,
            'total_revenue_generated': self.total_revenue_generated,
            'errors_count': self.errors_count,
        }

class MultiAgentOrchestrator:
    """
    NAYA SUPREME V19.2 — ORCHESTRATEUR PRINCIPAL
    
    Les 11 agents autonomes:
    1. Pain Hunter Agent — Détection pain signals
    2. Researcher Agent — Enrichissement prospect
    3. Offer Writer Agent — Génération offres
    4. Outreach Agent — Séquence 7-touch (dans REVENUE_ENGINE.outreach_sequence_engine)
    5. Closer Agent — Gestion objections + closing
    6. Audit Generator Agent — Rapports IEC 62443
    7. Content Engine Agent — Production contenu LinkedIn
    8. Contract Generator Agent — (dans REVENUE_ENGINE)
    9. Revenue Tracker Agent — Tracking + OODA projections
    10. Parallel Pipeline Agent — Orchestration 4 streams
    11. Guardian Agent — Sécurité + Compliance
    """
    
    def __init__(self):
        self.agents = {
            'pain_hunter': pain_hunter,
            'researcher': researcher,
            'offer_writer': offer_writer,
            'closer': closer,
            'audit_generator': audit_generator,
            'content_engine': content_engine,
            'orchestrator': orchestrator,
            'guardian': guardian,
        }

        # V19.2 SUPREME ENGINE
        self.v192_engine = get_v192_engine()

        self.metrics = SystemMetrics(phase=SystemPhase.DETECTION)
        self.run_count = 0
        self.cycle_history: List[Dict] = []
        self.quantum_opportunities: List[Dict] = []  # Opportunités invisibles détectées
    
    async def run_detection_phase(self) -> Dict:
        """PHASE 1: Pain Hunter détecte les opportunities"""
        logger.info("=== PHASE 1: DETECTION ===")
        self.metrics.phase = SystemPhase.DETECTION
        
        try:
            result = await pain_hunter.run_cycle()
            self.metrics.total_prospects_in_flight = result['auto_advance_count']
            return result
        except Exception as e:
            logger.error(f"Detection phase error: {e}")
            self.metrics.errors_count += 1
            return {'error': str(e)}
    
    async def run_enrichment_phase(self, pains: List[Dict]) -> Dict:
        """PHASE 2: Researcher enrichit les prospects"""
        logger.info("=== PHASE 2: ENRICHMENT ===")
        self.metrics.phase = SystemPhase.ENRICHMENT
        
        try:
            result = await researcher.run_cycle(pains)
            return result
        except Exception as e:
            logger.error(f"Enrichment phase error: {e}")
            self.metrics.errors_count += 1
            return {'error': str(e)}
    
    async def run_offer_phase(self, prospects: List[Dict], budgets: List[int], sectors: List[str]) -> Dict:
        """PHASE 3: Offer Writer génère offres"""
        logger.info("=== PHASE 3: OFFER GENERATION ===")
        self.metrics.phase = SystemPhase.OFFER_GENERATION
        
        try:
            result = await offer_writer.run_cycle(prospects, budgets, sectors)
            potential_revenue = result.get('total_revenue_potential', 0)
            self.metrics.total_revenue_generated = potential_revenue
            return result
        except Exception as e:
            logger.error(f"Offer phase error: {e}")
            self.metrics.errors_count += 1
            return {'error': str(e)}
    
    async def run_outreach_phase(self, enriched_prospects: List[Dict] = None,
                                  offers: List[Dict] = None) -> Dict:
        """PHASE 4: Outreach réel via outreach_agent (7-touch sequences)
                   + parallel_pipeline_orchestrator pour les 4 streams
        """
        logger.info("=== PHASE 4: OUTREACH (réel) ===")
        self.metrics.phase = SystemPhase.OUTREACH

        enriched_prospects = enriched_prospects or []
        offers = offers or []

        try:
            # 1. Outreach agent réel - démarre séquences 7-touch + traite touches planifiées
            outreach_result = await outreach_agent.run_cycle(
                prospects=enriched_prospects,
                offers=offers,
            )

            # 2. Parallel pipeline - orchestration 4 streams parallèles
            prospect_data = {
                'prospects': enriched_prospects or [{'prospect_id': f'p{i}'} for i in range(3)],
                'topics': ['IEC 62443', 'NIS2', 'SCADA Security'],
                'accepted_offers': offers,
            }
            parallel_result = await orchestrator.run_all_streams(prospect_data)

            # Fusion des résultats
            return {
                **outreach_result,
                'parallel_streams': parallel_result,
                'total_revenue_cycle': (
                    outreach_result.get('total_revenue_cycle', 0)
                    + parallel_result.get('total_revenue_cycle', 0)
                ),
            }
        except Exception as e:
            logger.error(f"Outreach phase error: {e}")
            self.metrics.errors_count += 1
            return {'error': str(e)}

    async def run_contract_phase(self, signed_deals: List[Dict]) -> Dict:
        """PHASE 7: Génération contrats + factures + liens paiement (PayPal/Deblock)"""
        logger.info("=== PHASE 7: CONTRACT GENERATION ===")
        try:
            result = await contract_generator_agent.run_cycle(signed_deals=signed_deals)
            return result
        except Exception as e:
            logger.error(f"Contract phase error: {e}")
            self.metrics.errors_count += 1
            return {'error': str(e)}

    async def run_revenue_phase(self, received_payments: List[Dict] = None) -> Dict:
        """PHASE 8: Tracking revenue (4 streams) + briefing quotidien Telegram"""
        logger.info("=== PHASE 8: REVENUE TRACKING ===")
        try:
            result = await revenue_tracker_agent.run_cycle(
                received_payments=received_payments or []
            )
            return result
        except Exception as e:
            logger.error(f"Revenue phase error: {e}")
            self.metrics.errors_count += 1
            return {'error': str(e)}
    
    async def run_monitoring_phase(self) -> Dict:
        """PHASE 5: Guardian monitoring"""
        logger.info("=== PHASE 5: MONITORING ===")
        self.metrics.phase = SystemPhase.MONITORING
        
        try:
            result = await guardian.run_full_scan()
            return result
        except Exception as e:
            logger.error(f"Monitoring phase error: {e}")
            self.metrics.errors_count += 1
            return {'error': str(e)}
    
    async def run_closing_phase(self, replies: List[Dict]) -> Dict:
        """PHASE 6: Closer traite les réponses"""
        logger.info("=== PHASE 6: CLOSING ===")
        self.metrics.phase = SystemPhase.CLOSING

        try:
            result = await closer.run_cycle(replies)
            return result
        except Exception as e:
            logger.error(f"Closing phase error: {e}")
            self.metrics.errors_count += 1
            return {'error': str(e)}

    async def run_quantum_hunt_phase(self) -> Dict:
        """
        PHASE V19.2: QUANTUM HUNT — Détection marchés invisibles
        Scanne les marchés oubliés, besoins ultra-discrets, opportunités cross-sectorielles.
        Va là où AUCUNE autre IA ne va.
        """
        logger.info("=== PHASE V19.2: QUANTUM HUNT ===")
        self.metrics.phase = SystemPhase.QUANTUM_HUNT

        try:
            result = await run_autonomous_quantum_hunt()

            # Stocker les opportunités invisibles détectées
            if result.get('outreach_plans'):
                self.quantum_opportunities.extend(result['outreach_plans'])

            logger.info(f"[V19.2] ✅ {result['opportunities_detected']} opportunités invisibles | "
                       f"{result['total_value_eur']:,.0f} EUR | "
                       f"Cognition: NIVEAU {result['cognition_level']}")

            return result
        except Exception as e:
            logger.error(f"Quantum Hunt phase error: {e}")
            self.metrics.errors_count += 1
            return {'error': str(e), 'opportunities_detected': 0, 'total_value_eur': 0}
    
    async def run_full_cycle(self) -> Dict:
        """CYCLE COMPLET: Toutes les phases en séquence + orchestration parallèle"""
        self.run_count += 1
        
        logger.info(f"\n{'='*70}")
        logger.info(f"NAYA SUPREME V19.2 — CYCLE #{self.run_count}")
        logger.info(f"{'='*70}\n")
        
        cycle_start = datetime.now(timezone.utc)
        
        # PHASE 1: DETECTION
        detection_result = await self.run_detection_phase()
        auto_advance_pains = detection_result.get('auto_advance_pains', [])
        
        # PHASE 2: ENRICHMENT
        enrichment_result = await self.run_enrichment_phase(auto_advance_pains)
        enriched_prospects = enrichment_result.get('enriched_prospects', [])
        
        # PHASE 3: OFFER GENERATION
        budgets = [p.get('budget_estimate_eur', 10000) for p in enriched_prospects]
        sectors = ['Manufacturing'] * len(enriched_prospects)
        offer_result = await self.run_offer_phase(enriched_prospects, budgets, sectors)
        offers_created = offer_result.get('offers', []) if isinstance(offer_result, dict) else []

        # PHASE 4: OUTREACH (agent réel branché V19.3)
        outreach_result = await self.run_outreach_phase(
            enriched_prospects=enriched_prospects,
            offers=offers_created,
        )

        # PHASE 5: MONITORING
        monitoring_result = await self.run_monitoring_phase()

        # PHASE 6: CLOSING (traite les réponses réelles reçues par outreach_agent)
        real_replies = []
        try:
            # Récupère les réponses positives/négatives stockées dans outreach_agent
            for p in outreach_agent.active_prospects.values():
                if p.status.value in ('positive_reply', 'negative_reply'):
                    real_replies.append({
                        'prospect_id': p.prospect_id,
                        'message': getattr(p, 'last_reply_text', ''),
                        'offer_price': float(getattr(p, 'offer_price_eur', 0) or 0),
                        'sentiment': 'positive' if p.status.value == 'positive_reply' else 'negative',
                    })
        except Exception as e:
            logger.warning(f"[cycle] No real replies yet: {e}")
        closing_result = await self.run_closing_phase(real_replies)

        # PHASE 7: CONTRACT GENERATION (V19.3 — agent branché)
        signed_deals = closing_result.get('signed_deals', []) if isinstance(closing_result, dict) else []
        contract_result = await self.run_contract_phase(signed_deals)

        # PHASE 8: AUDIT GENERATION (parallèle)
        audit_result = await audit_generator.run_cycle(enriched_prospects[:3])

        # PHASE 9: CONTENT GENERATION (parallèle)
        content_result = await content_engine.run_cycle()

        # PHASE 10: REVENUE TRACKING (V19.3 — agent branché)
        # Paiements reçus depuis le dernier cycle (via webhook ou réconciliation)
        received_payments = []
        try:
            from NAYA_REVENUE_ENGINE.payment_engine import PaymentEngine
            pe = PaymentEngine()
            # Les paiements confirmés sont lus depuis la DB (revenue reconciliation engine)
            if hasattr(pe, 'get_confirmed_payments_since_last_cycle'):
                received_payments = pe.get_confirmed_payments_since_last_cycle()
        except Exception as e:
            logger.debug(f"[cycle] No confirmed payments to track: {e}")
        revenue_result = await self.run_revenue_phase(received_payments)

        # PHASE V19.2: QUANTUM HUNT — Marchés invisibles
        quantum_result = await self.run_quantum_hunt_phase()

        cycle_end = datetime.now(timezone.utc)
        elapsed = (cycle_end - cycle_start).total_seconds()
        
        # Compile results
        full_result = {
            'cycle': self.run_count,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'elapsed_seconds': elapsed,
            'metrics': self.metrics.to_dict(),
            'phases': {
                'detection': detection_result.get('total_detected', 0),
                'enrichment': enrichment_result.get('total_enriched', 0),
                'offers': offer_result.get('total_created', 0),
                'outreach': outreach_result.get('total_revenue_cycle', 0),
                'monitoring': monitoring_result.get('total_events', 0),
                'closing': closing_result.get('total_processed', 0),
                'contracts': contract_result.get('total_generated', 0),  # V19.3
                'audits': audit_result.get('total_generated', 0),
                'content': content_result.get('total_generated', 0),
                'revenue': {  # V19.3
                    'total_tracked': revenue_result.get('total_tracked', 0),
                    'total_revenue_eur': revenue_result.get('total_revenue_eur', 0),
                    'mrr_eur': revenue_result.get('current_mrr_eur', 0),
                    'month_progress_pct': revenue_result.get('month_target_progress_pct', 0),
                },
                'quantum_hunt_v192': {
                    'opportunities': quantum_result.get('opportunities_detected', 0),
                    'value_eur': quantum_result.get('total_value_eur', 0),
                    'markets': quantum_result.get('markets_scanned', []),
                    'languages': quantum_result.get('languages_active', []),
                    'priority_opps': len(quantum_result.get('outreach_plans', [])),
                },
            },
            'agent_stats': {
                'pain_hunter': pain_hunter.get_stats(),
                'researcher': researcher.get_stats(),
                'offer_writer': offer_writer.get_stats(),
                'outreach_agent': outreach_agent.get_stats(),  # V19.3
                'closer': closer.get_stats(),
                'audit_generator': audit_generator.get_stats(),
                'content_engine': content_engine.get_stats(),
                'contract_generator_agent': contract_generator_agent.get_stats(),  # V19.3
                'revenue_tracker_agent': revenue_tracker_agent.get_stats(),  # V19.3
                'orchestrator': orchestrator.get_stats(),
                'guardian': guardian.get_stats(),
                'v192_supreme_engine': self.v192_engine.get_stats(),
            }
        }
        
        self.cycle_history.append(full_result)

        logger.info(f"\n{'='*70}")
        logger.info(f"CYCLE #{self.run_count} COMPLETE")
        logger.info(f"Total prospects in flight: {self.metrics.total_prospects_in_flight}")
        logger.info(f"Revenue potential this cycle: {outreach_result.get('total_revenue_cycle', 0)} EUR")
        logger.info(f"Elapsed: {elapsed:.2f}s")
        logger.info(f"{'='*70}\n")

        # V19.3: Push au dashboard OODA (si connecté)
        try:
            from NAYA_DASHBOARD.ooda_dashboard import push_cycle_update
            await push_cycle_update()
        except Exception as e:
            logger.debug(f"Dashboard push skipped: {e}")

        return full_result
    
    async def start_daemon(self, interval_seconds: int = 3600):
        """Démarrer le daemon principal (1h par défaut)"""
        logger.info("NAYA SUPREME V19.2 Daemon started")
        logger.info(f"Running cycle every {interval_seconds}s (infinite loop)")
        
        while True:
            try:
                await self.run_full_cycle()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Daemon error: {e}")
                await asyncio.sleep(60)
    
    def get_global_stats(self) -> Dict:
        """Stats globales du système"""
        return {
            'total_cycles': self.run_count,
            'total_cycle_revenue': sum(
                c.get('phases', {}).get('outreach', 0) 
                for c in self.cycle_history
            ),
            'error_count': self.metrics.errors_count,
            'last_cycle': self.cycle_history[-1] if self.cycle_history else None,
        }

# Instance globale
multi_agent_orchestrator = MultiAgentOrchestrator()

async def main():
    """Test function"""
    result = await multi_agent_orchestrator.run_full_cycle()
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())
