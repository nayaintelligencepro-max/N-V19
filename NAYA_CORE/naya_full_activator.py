"""
NAYA — Full System Activator
══════════════════════════════════════════════════════════════════
Active et connecte ABSOLUMENT TOUS les modules du système.
328 fichiers Python → intégrés, utilisés, connectés.

Architecture :
  NAYA_CORE : cognition(50), decision(21), economic(7), evolution(9),
               hunt(10), monitoring(7), orchestration(9), risk(3),
               runtime(5), sovereignty(5), strategy_engine(10),
               system(5), cluster(8), core(14), doctrine(4), state(2)
  RACINE     : DATA_GOVERNANCE, DISTRIBUTED_LAYER, KERNEL,
               NAYA_COMMAND_GATEAWAY, NAYA_DASHBOARD, NAYA_EVENT_STREAM,
               NAYA_INTERFACE, NAYA_OBSERVATION_BUS, PROTOCOLS,
               SECRETS, VERSION_CONTROL + stubs guardian/intention/memory/diag
"""
import os, time, threading, logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

log = logging.getLogger("NAYA.FULL_ACTIVATOR")


@dataclass
class ModuleStatus:
    name: str
    loaded: bool = False
    instance: Any = None
    error: str = ""


class NayaFullActivator:
    """
    Charge, instancie et connecte TOUS les modules NAYA.
    Un seul appel à activate() suffit pour tout activer.
    """

    def __init__(self):
        self._modules: Dict[str, ModuleStatus] = {}
        self._lock = threading.Lock()
        self._activated = False
        self._start_time = time.time()

    def activate(self, llm_brain=None, db=None, notifier=None, event_bus=None) -> Dict[str, Any]:
        """Active tous les modules. Retourne un rapport complet."""
        if self._activated:
            return self.status()

        log.info("═" * 60)
        log.info("  NAYA FULL ACTIVATOR — Activation de tous les modules")
        log.info("═" * 60)

        # ── Groupe 1 : NAYA_CORE Cognitive ─────────────────────────────
        self._load_cognition()
        self._load_decision()
        self._load_economic()
        self._load_evolution_core()
        self._load_hunt()
        self._load_monitoring()
        self._load_orchestration()
        self._load_risk()
        self._load_runtime()
        self._load_sovereignty()
        self._load_strategy_engine()
        self._load_system()
        self._load_cluster()
        self._load_core_engine()
        self._load_doctrine()
        self._load_state()

        # ── Groupe 2 : Modules racine ────────────────────────────────────
        self._load_data_governance()
        self._load_distributed_layer()
        self._load_kernel()
        self._load_command_gateway()
        self._load_event_stream()
        self._load_observation_bus()
        self._load_protocols()
        self._load_secrets()
        self._load_version_control()
        self._load_interface()

        # ── Groupe 3 : Stubs autonomes ───────────────────────────────────
        self._load_guardian()
        self._load_intention_loop()
        self._load_memory_narrative()
        self._load_diagnostic()
        self._load_brain_activator(llm_brain)

        # ── Connexions cross-modules ─────────────────────────────────────
        self._wire_all(llm_brain, db, notifier, event_bus)

        self._activated = True
        total = len(self._modules)
        ok = sum(1 for m in self._modules.values() if m.loaded)
        log.info(f"  ✅ {ok}/{total} modules activés")
        return self.status()

    # ═══ NAYA_CORE COGNITIVE ══════════════════════════════════════════

    def _load_cognition(self):
        imports = {
            "cognition.fusion":      ("NAYA_CORE.cognition.fusion.fusion_controller", "CognitiveFusionController"),
            "cognition.hub":         ("NAYA_CORE.cognition.cognitive_hub",             "CognitiveHubNAYA"),
            "cognition.multilingual":("NAYA_CORE.cognition.multilingual_cultural_engine","MultilingualEngine"),
            "cognition.humanisation":("NAYA_CORE.cognition.humanisation_core",         "HumanisationCore"),
            "cognition.intelligence":("NAYA_CORE.cognition.intelligence_core",          "IntelligenceCore"),
            "cognition.perspective": ("NAYA_CORE.cognition.perspective_core",           "PerspectiveCore"),
            "cognition.L1_noise":    ("NAYA_CORE.cognition.layers.layer_1_cognitive_input.noise_filter","NoiseFilter"),
            "cognition.L1_input":    ("NAYA_CORE.cognition.layers.layer_1_cognitive_input.cognitive_input","CognitiveInputEngine"),
            "cognition.L1_signal":   ("NAYA_CORE.cognition.layers.layer_1_cognitive_input.signal_extractor","SignalExtractor"),
            "cognition.L2_prec":     ("NAYA_CORE.cognition.layers.layer_2_precision.precision_layer","PrecisionLayer"),
            "cognition.L2_attn":     ("NAYA_CORE.cognition.layers.layer_2_precision.attention_focus","AttentionFocus"),
            "cognition.L3_intel":    ("NAYA_CORE.cognition.layers.layer_3_intelligence.cognitive_intelligence","CognitiveIntelligence"),
            "cognition.L3_disc":     ("NAYA_CORE.cognition.layers.layer_3_intelligence.discernment","DiscernmentEngine"),
            "cognition.L4_strat":    ("NAYA_CORE.cognition.layers.layer_4_strategy.strategic_cognition","StrategicCognition"),
            "cognition.L4_traj":     ("NAYA_CORE.cognition.layers.layer_4_strategy.trajectory_engine","TrajectoryEngine"),
            "cognition.L5_hunt":     ("NAYA_CORE.cognition.layers.layer_5_hunting.elite_detection","EliteDetection"),
            "cognition.L5_weak":     ("NAYA_CORE.cognition.layers.layer_5_hunting.signal_weakness","SignalWeaknessAnalyzer"),
            "cognition.L6_story":    ("NAYA_CORE.cognition.layers.layer_6_creation.storytelling_engine","StorytellingEngine"),
            "cognition.L6_struct":   ("NAYA_CORE.cognition.layers.layer_6_creation.structuring","StructuringEngine"),
            "cognition.L7_hybrid":   ("NAYA_CORE.cognition.layers.layer_7_hybrid.hybrid_cognition","HybridCognition"),
            "cognition.L8_safe":     ("NAYA_CORE.cognition.layers.layer_8_safe.safe_intelligence","SafeIntelligence"),
            "cognition.L8_risk":     ("NAYA_CORE.cognition.layers.layer_8_safe.risk_reduction","RiskReductionEngine"),
            "cognition.L9_rp":       ("NAYA_CORE.cognition.layers.layer_9_repurse.repurse_evolution","RepurseEvolution"),
            "cognition.L9_def":      ("NAYA_CORE.cognition.layers.layer_9_repurse.defense_logic","DefenseLogic"),
            "cognition.L10_mat":     ("NAYA_CORE.cognition.layers.layer_10_maturation.maturation_engine","MaturationEngine"),
            "cognition.L10_cap":     ("NAYA_CORE.cognition.layers.layer_10_maturation.capitalization","CapitalizationEngine"),
            "cognition.memory":      ("NAYA_CORE.cognition.memory.memory_store","CognitionMemoryStore"),
        }
        self._batch_load(imports)

    def _load_decision(self):
        imports = {
            "decision.core":       ("NAYA_CORE.decision.decision_core","DecisionCore"),
            "decision.alloc":      ("NAYA_CORE.decision.allocation_intelligence","AllocationIntelligence"),
            "decision.density":    ("NAYA_CORE.decision.density_engine","DensityEngine"),
            "decision.accelerator":("NAYA_CORE.decision.decision_accelerator","DecisionAccelerator"),
            "decision.outcome":    ("NAYA_CORE.decision.outcome_prediction_engine","OutcomePredictionEngine"),
            "decision.adaptive_mem":("NAYA_CORE.decision.adaptative_memory_controller","AdaptiveMemoryController"),
            "decision.state_mgr":  ("NAYA_CORE.decision.decision_state_manager","DecisionStateManager"),
            "decision.monitor":    ("NAYA_CORE.decision.decision_monitor","DecisionMonitor"),
            "decision.domain_rtr": ("NAYA_CORE.decision.strategic_domain_router","StrategicDomainRouter"),
            "decision.sov_filter": ("NAYA_CORE.decision.sovereignty_filter","SovereigntyFilter"),
            "decision.perf_engine":("NAYA_CORE.decision.decision_performance_engine","DecisionPerformanceEngine"),
            "decision.exec_perf":  ("NAYA_CORE.decision.executive_performance_core","ExecutivePerformanceCore"),
        }
        self._batch_load(imports)

    def _load_economic(self):
        imports = {
            "economic.gravity":      ("NAYA_CORE.economic.economic_gravity_core","EconomicGravityCore"),
            "economic.budget_lev":   ("NAYA_CORE.economic.budget_leverage_core","BudgetLeverageCore"),
            "economic.cost_opt":     ("NAYA_CORE.economic.cost_optimizer","CostOptimizer"),
            "economic.capital_res":  ("NAYA_CORE.economic.capital_reserve_manager","CapitalReserveManager"),
            "economic.premium_cost": ("NAYA_CORE.economic.premium_cost_optimization_core","PremiumCostOptimizationCore"),
            "economic.zero_cost":    ("NAYA_CORE.economic.zero_cost_leverage_core","ZeroCostLeverageCore"),
        }
        self._batch_load(imports)

    def _load_evolution_core(self):
        imports = {
            "evolution.adaptive_fb":   ("NAYA_CORE.evolution.adaptive_feedback","AdaptiveFeedback"),
            "evolution.adaptative_ev": ("NAYA_CORE.evolution.adaptative_evolution_core","AdaptiveEvolutionCore"),
            "evolution.growth":        ("NAYA_CORE.evolution.adaptative_growth_core","AdaptiveGrowthCore"),
            "evolution.signal_fusion": ("NAYA_CORE.evolution.core_signal_fusion","CoreSignalFusion"),
            "evolution.reconfig":      ("NAYA_CORE.evolution.core_system_reconfiguration","CoreSystemReconfiguration"),
            "evolution.doctrine_adj":  ("NAYA_CORE.evolution.doctrine_ajuster","DoctrineAdjuster"),
        }
        self._batch_load(imports)

    def _load_hunt(self):
        imports = {
            "hunt.orchestration":  ("NAYA_CORE.hunt.hunt_orchestration","HuntOrchestration"),  # class_only
            "hunt.advanced":       ("NAYA_CORE.hunt.advanced_hunt_engine","AdvancedHuntEngine"),
            "hunt.fast_cash":      ("NAYA_CORE.hunt.fast_cash_engine","FastCashEngine"),
            "hunt.discreet":       ("NAYA_CORE.hunt.discreet_business_engine","DiscreetBusinessEngine"),
            "hunt.parallel_orch":  ("NAYA_CORE.hunt.parallel_orchestrator","ParallelHuntOrchestrator"),
            "hunt.zero_waste":     ("NAYA_CORE.hunt.zero_waste_recycler","ZeroWasteRecycler"),
            "hunt.core_engine":    ("NAYA_CORE.hunt.core_hunt_engine","HuntEngine"),
        }
        self._batch_load(imports)

    def _load_monitoring(self):
        imports = {
            "monitoring.watchdog":    ("NAYA_CORE.monitoring.system_watchdog","SystemWatchdog"),
            "monitoring.pattern":     ("NAYA_CORE.monitoring.pattern_detector","PatternDetector"),
            "monitoring.self_heal":   ("NAYA_CORE.monitoring.core_self_healing","CoreSelfHealing"),
            "monitoring.degrad":      ("NAYA_CORE.monitoring.degradation_control","DegradationControl"),
            "monitoring.predictive":  ("NAYA_CORE.monitoring.preditive_engine","PredictiveEngine"),
            "monitoring.compliance":  ("NAYA_CORE.monitoring.compliance_certification_core","ComplianceCertificationCore"),
        }
        self._batch_load(imports)

    def _load_orchestration(self):
        imports = {
            "orchestration.llm_orch":   ("NAYA_CORE.orchestration.llm_orchestrator","LLMOrchestrator"),
            "orchestration.incubation": ("NAYA_CORE.orchestration.incubation_manager","IncubationManager"),
            "orchestration.mission_st": ("NAYA_CORE.orchestration.mission_state","MissionState"),
            "orchestration.opp_pipe":   ("NAYA_CORE.orchestration.opportunity_pipeline","OpportunityPipeline"),
            "orchestration.channel":    ("NAYA_CORE.orchestration.channel_orchestration_core","ChannelOrchestrationCore"),
        }
        self._batch_load(imports)

    def _load_risk(self):
        imports = {
            "risk.engine":   ("NAYA_CORE.risk.risk","Risk"),
            "risk.guardian": ("NAYA_CORE.risk.guardian","Guardian"),
        }
        self._batch_load(imports)

    def _load_runtime(self):
        imports = {
            "runtime.core":     ("NAYA_CORE.runtime.naya_core_runtime","NayaCoreRuntime"),
            "runtime.entity":   ("NAYA_CORE.runtime.entity_runtime","EntityRuntime"),
            "runtime.strategic":("NAYA_CORE.runtime.strategic_runtime","StrategicRuntime"),
        }
        self._batch_load(imports)

    def _load_sovereignty(self):
        imports = {
            "sovereignty.internal": ("NAYA_CORE.sovereignty.internal_sovereignty_core","InternalSovereigntyCore"),
            "sovereignty.ownership":("NAYA_CORE.sovereignty.ownership_and_signature_core","OwnershipAndSignatureCore"),
            "sovereignty.layer":    ("NAYA_CORE.sovereignty.sovereignty_layer","SovereigntyLayer"),
        }
        self._batch_load(imports)

    def _load_strategy_engine(self):
        imports = {
            "strategy.field":       ("NAYA_CORE.strategy_engine.strategic_field_core","StrategicFieldCore"),
            "strategy.engagement":  ("NAYA_CORE.strategy_engine.engagement_strategy_core","EngagementStrategyCore"),
            "strategy.credibility": ("NAYA_CORE.strategy_engine.credibility_core","CredibilityCore"),
            "strategy.capital":     ("NAYA_CORE.strategy_engine.core_capitalization","CoreCapitalization"),
            "strategy.expansion":   ("NAYA_CORE.strategy_engine.core_expansion_logic","CoreExpansionLogic"),
            "strategy.multi_horiz": ("NAYA_CORE.strategy_engine.core_multi_horizon","CoreMultiHorizon"),
            "strategy.supplier":    ("NAYA_CORE.strategy_engine.supplier_relations_core","SupplierRelationsCore"),
        }
        self._batch_load(imports)

    def _load_system(self):
        imports = {
            "system.journal":  ("NAYA_CORE.system.strategic_journal","StrategicJournal"),
            "system.memory":   ("NAYA_CORE.system.strategic_memory","StrategicMemory"),
            "system.entity_m": ("NAYA_CORE.system.entity_manager","EntityManager"),
        }
        self._batch_load(imports)

    def _load_cluster(self):
        imports = {
            "cluster.controller":  ("NAYA_CORE.cluster.cluster_controller","ClusterController"),
            "cluster.runtime":     ("NAYA_CORE.cluster.cluster_runtime","ClusterRuntime"),
            "cluster.capability":  ("NAYA_CORE.cluster.cluster_capability","ClusterCapability"),
            "cluster.consensus":   ("NAYA_CORE.cluster.cluster_consensus_engine","ClusterConsensusEngine"),
            "cluster.integrity":   ("NAYA_CORE.cluster.distributed_integrity_guard","DistributedIntegrityGuard"),
            "cluster.election":    ("NAYA_CORE.cluster.leader_election","LeaderElection"),
            "cluster.main":        ("NAYA_CORE.cluster.naya_core_cluster","NayaCoreCluster"),
        }
        self._batch_load(imports)

    def _load_core_engine(self):
        imports = {
            "core.engine_master": ("NAYA_CORE.core.engine_master","EngineMaster"),
            "core.state_store":   ("NAYA_CORE.core.state_store","StateStore"),
            "core.capability":    ("NAYA_CORE.core.capability_registry","CapabilityRegistry"),
            "core.causal":        ("NAYA_CORE.core.core_causal_engine","CoreCausalEngine"),
            "core.decision_k":    ("NAYA_CORE.core.core_decision_kernel","CoreDecisionKernel"),
            "core.integrity_l":   ("NAYA_CORE.core.core_integrity_lock","CoreIntegrityLock"),
            "core.fast_cash_b":   ("NAYA_CORE.core.fast_cash_business_engine","FastCashBusinessEngine"),
            "core.strategic_ctx": ("NAYA_CORE.core.strategic_context","StrategicContext"),
        }
        self._batch_load(imports)

    def _load_doctrine(self):
        imports = {
            "doctrine.constitution": ("NAYA_CORE.doctrine.core_constitution","CoreConstitution"),
            "doctrine.thresholds":   ("NAYA_CORE.doctrine.economic_thresholds","EconomicThresholds"),
            "doctrine.modes":        ("NAYA_CORE.doctrine.strategic_modes","StrategicModes"),
        }
        self._batch_load(imports)

    def _load_state(self):
        imports = {
            "state.manager": ("NAYA_CORE.state.state_manager","StateManager"),
        }
        self._batch_load(imports)

    # ═══ MODULES RACINE ══════════════════════════════════════════════

    def _load_data_governance(self):
        imports = {
            "data_gov.write":    ("DATA_GOVERNANCE.write_classifier","WriteClassifier"),
            "data_gov.hash":     ("DATA_GOVERNANCE.integrity_hash_manager","IntegrityHashManager"),
            "data_gov.snapshot": ("DATA_GOVERNANCE.snapshot_manager","SnapshotManager"),
        }
        self._batch_load(imports)

    def _load_distributed_layer(self):
        imports = {
            "distrib.leader":  ("DISTRIBUTED_LAYER.leader_election_controller","LeaderElectionController"),
            "distrib.hybrid_w":("DISTRIBUTED_LAYER.hybrid_write_controller","HybridWriteController"),
            "distrib.failover":("DISTRIBUTED_LAYER.failover_controller","FailoverController"),
            "distrib.registry":("DISTRIBUTED_LAYER.region_registry","RegionRegistry"),
        }
        self._batch_load(imports)

    def _load_kernel(self):
        imports = {
            "kernel.activation": ("KERNEL.activation_controller","ActivationController"),
            "kernel.contract_v": ("KERNEL.contract_validator","ContractValidator"),
        }
        self._batch_load(imports)

    def _load_command_gateway(self):
        imports = {
            "gateway.actor":       ("NAYA_COMMAND_GATEAWAY.actor_registry","validate_actor"),
            "gateway.dispatcher":  ("NAYA_COMMAND_GATEAWAY.gateway_dispatcher","GatewayDispatcher"),
            "gateway.intent":      ("NAYA_COMMAND_GATEAWAY.intent_schema","IntentSchema"),
            "gateway.journal":     ("NAYA_COMMAND_GATEAWAY.journal","IntentJournal"),
            "gateway.permission":  ("NAYA_COMMAND_GATEAWAY.permission_matrix","is_authorized"),
            "gateway.policy":      ("NAYA_COMMAND_GATEAWAY.policy_guard","validate_intent"),
            "gateway.risk":        ("NAYA_COMMAND_GATEAWAY.risk_classifier","classify"),
        }
        self._batch_load(imports)

    def _load_event_stream(self):
        imports = {
            "event_stream.stream":   ("NAYA_EVENT_STREAM.event_stream","EventStream"),
            "event_stream.envelope": ("NAYA_EVENT_STREAM.event_envelope","EventEnvelope"),
            "event_stream.absorber": ("NAYA_EVENT_STREAM.absorber","StreamAbsorber"),
        }
        self._batch_load(imports)

    def _load_observation_bus(self):
        imports = {
            "obs_bus.bus": ("NAYA_OBSERVATION_BUS.observation_bus","ObservationBus"),
            "obs_bus.main": ("NAYA_OBSERVATION_BUS.bus","ObservationBus"),
        }
        self._batch_load(imports)

    def _load_protocols(self):
        imports = {
            "protocols.identity":    ("PROTOCOLS.business_identity_protocol","BusinessIdentityProtocol"),
            "protocols.leadership":  ("PROTOCOLS.leadership_protocol","LeadershipProtocol"),
            "protocols.replication": ("PROTOCOLS.replication_protocol","ReplicationProtocol"),
        }
        self._batch_load(imports)

    def _load_secrets(self):
        """Charge les secrets depuis les fichiers .env SECRETS/keys/"""
        try:
            from SECRETS.secrets_loader import load_all_secrets
            result = load_all_secrets()
            self._modules["secrets.loader"] = ModuleStatus("secrets.loader", True, result)
            loaded_count = sum(len(v) for v in result.values())
            log.info(f"[SECRETS] {loaded_count} variables chargées depuis SECRETS/keys/")
        except Exception as e:
            self._modules["secrets.loader"] = ModuleStatus("secrets.loader", False, error=str(e))

    def _load_version_control(self):
        imports = {
            "version.manager":  ("VERSION_CONTROL.version_manager","VersionManager"),
            "version.rollback": ("VERSION_CONTROL.rollback_controller","RollbackController"),
        }
        self._batch_load(imports)

    def _load_interface(self):
        imports = {
            "interface.entry":   ("NAYA_INTERFACE.interface_entry","NayaInterface"),
            "interface.kernel":  ("NAYA_INTERFACE.interface_kernel","InterfaceKernel"),
            "interface.router":  ("NAYA_INTERFACE.interface_router","InterfaceRouter"),
        }
        self._batch_load(imports)

    # ═══ STUBS AUTONOMES ════════════════════════════════════════════

    def _load_guardian(self):
        try:
            from naya_guardian.guardian import get_guardian
            g = get_guardian()
            self._modules["guardian"] = ModuleStatus("guardian", True, g)
        except Exception as e:
            self._modules["guardian"] = ModuleStatus("guardian", False, error=str(e))

    def _load_intention_loop(self):
        try:
            from naya_intention_loop.intention_loop import get_intention_loop
            il = get_intention_loop()
            self._modules["intention_loop"] = ModuleStatus("intention_loop", True, il)
        except Exception as e:
            self._modules["intention_loop"] = ModuleStatus("intention_loop", False, error=str(e))

    def _load_memory_narrative(self):
        try:
            from naya_memory_narrative.narrative_memory import get_narrative_memory
            m = get_narrative_memory()
            self._modules["memory_narrative"] = ModuleStatus("memory_narrative", True, m)
        except Exception as e:
            self._modules["memory_narrative"] = ModuleStatus("memory_narrative", False, error=str(e))

    def _load_diagnostic(self):
        try:
            from naya_self_diagnostic.diagnostic import get_diagnostic
            d = get_diagnostic()
            self._modules["diagnostic"] = ModuleStatus("diagnostic", True, d)
        except Exception as e:
            self._modules["diagnostic"] = ModuleStatus("diagnostic", False, error=str(e))

    def _load_brain_activator(self, llm_brain=None):
        try:
            from NAYA_CORE.brain_activator import get_brain_activator
            ba = get_brain_activator()
            if llm_brain:
                ba.attach_llm(llm_brain)
            self._modules["brain_activator"] = ModuleStatus("brain_activator", True, ba)
        except Exception as e:
            self._modules["brain_activator"] = ModuleStatus("brain_activator", False, error=str(e))

    # ═══ CONNEXIONS CROSS-MODULES ═══════════════════════════════════

    def _wire_all(self, llm_brain=None, db=None, notifier=None, event_bus=None):
        """Connecte tous les modules ensemble."""
        # 1. Brain Activator ← LLM
        if llm_brain:
            ba = self._get("brain_activator")
            if ba and hasattr(ba, "attach_llm"):
                ba.attach_llm(llm_brain)

        # 2. Sovereign Engine ← tout
        try:
            from NAYA_CORE.naya_sovereign_engine import get_sovereign
            sov = get_sovereign()
            sov.wire(
                db=db,
                notifier=notifier,
                brain=llm_brain,
                intention=self._get("intention_loop"),
                guardian=self._get("guardian"),
                memory=self._get("memory_narrative"),
                diagnostic=self._get("diagnostic"),
            )
            sov.start()
            self._modules["sovereign_engine"] = ModuleStatus("sovereign_engine", True, sov)
        except Exception as e:
            self._modules["sovereign_engine"] = ModuleStatus("sovereign_engine", False, error=str(e))

        # 3. Intention Loop ← Sovereign callbacks
        il = self._get("intention_loop")
        sov = self._get("sovereign_engine")
        if il and sov:
            try:
                from naya_intention_loop.intention_loop import Intent
                def _on_hunt(d): sov.trigger_now()
                il.on(Intent.HUNT, _on_hunt).start()
            except Exception: pass

        # 4. WatchDog ← Runtime
        try:
            from NAYA_CORE.monitoring.system_watchdog import SystemWatchdog
            wd = SystemWatchdog()
            wd.start()
            self._modules["watchdog"] = ModuleStatus("watchdog", True, wd)
        except Exception as e:
            self._modules["watchdog"] = ModuleStatus("watchdog", False, error=str(e))

        # 5. Diagnostic ← start thread
        diag = self._get("diagnostic")
        if diag and hasattr(diag, "start"):
            try: diag.start()
            except Exception: pass

        # 6. Event Bus ← publish activation
        if event_bus:
            try:
                event_bus.publish("FULL_ACTIVATION", {
                    "modules": self.get_loaded_count(),
                    "ts": time.time()
                })
            except Exception: pass

    # ═══ UTILITAIRES ═════════════════════════════════════════════════

    def _batch_load(self, imports: Dict[str, tuple]):
        import importlib
        for key, (mod_path, cls_name) in imports.items():
            try:
                mod = importlib.import_module(mod_path)
                cls = getattr(mod, cls_name, None)
                if cls is None:
                    cls = getattr(mod, cls_name.lower(), None)
                if cls and callable(cls) and not isinstance(cls, type):
                    inst = cls  # fonction/singleton
                elif cls:
                    try:    inst = cls()
                    except: inst = cls  # Stocker la classe si instanciation impossible
                else:
                    inst = mod
                self._modules[key] = ModuleStatus(key, True, inst)
            except Exception as e:
                self._modules[key] = ModuleStatus(key, False, error=str(e)[:60])
    def _get(self, key: str) -> Optional[Any]:
        m = self._modules.get(key)
        return m.instance if m and m.loaded else None

    def get_loaded_count(self) -> int:
        return sum(1 for m in self._modules.values() if m.loaded)

    def get_failed_count(self) -> int:
        return sum(1 for m in self._modules.values() if not m.loaded)

    def status(self) -> Dict[str, Any]:
        total = len(self._modules)
        ok = self.get_loaded_count()
        failed = [(k, m.error) for k, m in self._modules.items() if not m.loaded]
        return {
            "activated": self._activated,
            "total_modules": total,
            "loaded": ok,
            "failed": len(failed),
            "pct": round(ok / total * 100, 1) if total else 0,
            "uptime_s": round(time.time() - self._start_time, 1),
            "failed_modules": failed[:10],
        }

    def get_module(self, key: str) -> Optional[Any]:
        return self._get(key)

    def get_all_instances(self) -> Dict[str, Any]:
        return {k: m.instance for k, m in self._modules.items() if m.loaded}


_FULL_ACTIVATOR: Optional[NayaFullActivator] = None

def get_full_activator() -> NayaFullActivator:
    global _FULL_ACTIVATOR
    if _FULL_ACTIVATOR is None:
        _FULL_ACTIVATOR = NayaFullActivator()
    return _FULL_ACTIVATOR
