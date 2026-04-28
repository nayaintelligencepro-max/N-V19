"""
NAYA SUPREME V6 — Parallel Orchestrator
Lance 2/3/4 missions simultanées sur tous les projets.
Orchestration maximale — rien ne dort, tout avance en parallèle.
"""
import time, uuid, threading, logging, json
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from enum import Enum

log = logging.getLogger("NAYA.PARALLEL")


class WorkerMode(Enum):
    AGGRESSIVE   = "aggressive"   # Max 6 workers — tout en parallèle
    BALANCED     = "balanced"     # 4 workers — équilibré
    CONSERVATIVE = "conservative" # 2 workers — économique


@dataclass
class ParallelTask:
    id: str = field(default_factory=lambda: f"T_{uuid.uuid4().hex[:8].upper()}")
    project_id: str = ""
    mission_type: str = ""
    payload: Dict = field(default_factory=dict)
    priority: int = 5
    fn: Optional[Callable] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: float = 0
    ended_at: float = 0

    @property
    def duration_ms(self) -> float:
        if self.ended_at and self.started_at:
            return (self.ended_at - self.started_at) * 1000
        return 0


@dataclass
class BatchResult:
    batch_id: str
    tasks: List[ParallelTask]
    started_at: float
    ended_at: float = 0

    @property
    def success_count(self) -> int: return sum(1 for t in self.tasks if not t.error)
    @property
    def fail_count(self) -> int: return sum(1 for t in self.tasks if t.error)
    @property
    def duration_ms(self) -> float: return (self.ended_at - self.started_at) * 1000
    @property
    def results(self) -> List[Dict]:
        return [{"id": t.id, "project": t.project_id, "type": t.mission_type,
                 "result": t.result, "error": t.error, "duration_ms": t.duration_ms}
                for t in self.tasks]


class ParallelOrchestrator:
    """
    Orchestre l'exécution parallèle de missions sur les 6 projets.
    Mode AGGRESSIVE = tout en même temps.
    Chaque projet avance en permanence sans bloquer les autres.
    """

    def __init__(self, mode: WorkerMode = WorkerMode.BALANCED):
        self.mode = mode
        self._max_workers = {"aggressive": 6, "balanced": 4, "conservative": 2}[mode.value]
        self._executor = ThreadPoolExecutor(max_workers=self._max_workers, thread_name_prefix="NAYA-WORKER")
        self._db = None
        self._autonomous = None
        self._factory = None
        self._brain = None
        self._batches: Dict[str, BatchResult] = {}
        self._lock = threading.Lock()
        self.stats = {
            "total_batches": 0, "total_tasks": 0,
            "success": 0, "failed": 0, "total_duration_ms": 0
        }
        log.info(f"[PARALLEL] Initialized — {self._max_workers} workers — mode {mode.value}")

    def init(self, db=None, autonomous=None, factory=None, brain=None):
        self._db = db
        self._autonomous = autonomous
        self._factory = factory
        self._brain = brain

    # ── Core execution ────────────────────────────────────────────────────────
    def run_batch(self, tasks: List[ParallelTask]) -> BatchResult:
        """Lance un batch de tâches en parallèle et attend la fin."""
        batch_id = f"BATCH_{uuid.uuid4().hex[:10].upper()}"
        batch = BatchResult(batch_id=batch_id, tasks=tasks, started_at=time.time())

        # Trie par priorité
        tasks_sorted = sorted(tasks, key=lambda t: t.priority)

        futures: Dict[Future, ParallelTask] = {}
        for task in tasks_sorted:
            if task.fn:
                task.started_at = time.time()
                f = self._executor.submit(self._safe_execute, task)
                futures[f] = task

        for future in as_completed(futures, timeout=120):
            task = futures[future]
            try:
                task.result = future.result()
            except Exception as e:
                task.error = str(e)
            finally:
                task.ended_at = time.time()

        batch.ended_at = time.time()

        # Persiste en DB
        if self._db:
            try:
                ex_list = [{"mission_type": t.mission_type, "project_id": t.project_id,
                             "worker_id": t.id} for t in tasks]
                eids = self._db.start_parallel_batch(batch_id, ex_list)
                for eid, task in zip(eids, tasks):
                    self._db.complete_parallel_execution(
                        eid,
                        "SUCCESS" if not task.error else "FAILED",
                        str(task.result)[:500] if task.result else None,
                        task.error
                    )
            except Exception as e:
                log.debug(f"[PARALLEL] DB persist error: {e}")

        # Stats
        with self._lock:
            self._batches[batch_id] = batch
            self.stats["total_batches"] += 1
            self.stats["total_tasks"] += len(tasks)
            self.stats["success"] += batch.success_count
            self.stats["failed"] += batch.fail_count
            self.stats["total_duration_ms"] += batch.duration_ms

        log.info(f"[PARALLEL] Batch {batch_id} done — {batch.success_count}/{len(tasks)} OK — {batch.duration_ms:.0f}ms")
        return batch

    def _safe_execute(self, task: ParallelTask) -> Any:
        try:
            return task.fn(task.payload)
        except Exception as e:
            raise RuntimeError(f"Task {task.id} ({task.mission_type}): {e}")

    # ── Orchestrations prédéfinies ────────────────────────────────────────────
    def hunt_all_projects(self) -> BatchResult:
        """Lance une chasse simultanée sur les 6 projets."""
        projects = [
            ("P01", "PME trésorerie urgente"),
            ("P02", "Entreprise XR déploiement"),
            ("P03", "Cosmétiques naturels peaux sensibles"),
            ("P04", "Tiny house off-grid"),
            ("P05", "Marchés sous-servis immigrants entrepreneurs"),
            ("P06", "Immobilier sous-évalué IDF"),
        ]
        tasks = []
        for project_id, sector in projects:
            task = ParallelTask(
                project_id=project_id,
                mission_type="HUNT_OPPORTUNITIES",
                payload={"sector": sector, "project_id": project_id},
                priority=2,
                fn=self._hunt_fn,
            )
            tasks.append(task)
        log.info(f"[PARALLEL] 🎯 Hunt all 6 projects simultaneously")
        return self.run_batch(tasks)

    def generate_content_all_channels(self, project_id: str = None) -> BatchResult:
        """Génère du contenu sur 4 canaux en parallèle."""
        channels = [
            ("linkedin", "post", "professional"),
            ("instagram", "post", "visual_punchy"),
            ("twitter", "post", "concise"),
            ("email", "newsletter", "personal"),
        ]
        tasks = []
        for channel, ctype, tone in channels:
            task = ParallelTask(
                project_id=project_id or "GLOBAL",
                mission_type="GENERATE_CONTENT",
                payload={"channel": channel, "content_type": ctype, "tone": tone,
                          "project_id": project_id},
                priority=4,
                fn=self._content_fn,
            )
            tasks.append(task)
        log.info(f"[PARALLEL] 📝 Content gen — 4 channels simultaneously")
        return self.run_batch(tasks)

    def evaluate_pipeline_batch(self) -> BatchResult:
        """Évalue et avance tous les leads pipeline en parallèle."""
        if not self._db:
            return BatchResult(f"BATCH_EMPTY", [], time.time())
        signals = self._db.fetch_all(
            "SELECT * FROM naya_pipeline WHERE stage IN ('SIGNAL','QUALIFIED') LIMIT 20"
        )
        tasks = [
            ParallelTask(
                project_id=s["project_id"],
                mission_type="PIPELINE_EVALUATE",
                payload=dict(s),
                priority=3,
                fn=self._pipeline_eval_fn,
            )
            for s in signals
        ]
        if not tasks:
            return BatchResult(f"BATCH_EMPTY", [], time.time())
        log.info(f"[PARALLEL] 🔄 Evaluating {len(tasks)} pipeline leads")
        return self.run_batch(tasks)

    def create_business_parallel(self, briefs: List[Dict]) -> BatchResult:
        """Crée plusieurs business plans en parallèle."""
        tasks = [
            ParallelTask(
                project_id=b.get("project_id", "NEW"),
                mission_type="CREATE_BUSINESS",
                payload=b,
                priority=2,
                fn=self._create_fn,
            )
            for b in briefs
        ]
        log.info(f"[PARALLEL] 🏗 Creating {len(tasks)} business plans simultaneously")
        return self.run_batch(tasks)

    # ── Task functions ────────────────────────────────────────────────────────
    def _hunt_fn(self, payload: Dict) -> Dict:
        if self._autonomous:
            try:
                from NAYA_CORE.autonomous_engine import MissionType
                m = self._autonomous.submit(
                    MissionType.HUNT_OPPORTUNITIES, payload, priority=2
                )
                return {"mission_id": m.id, "status": m.status.value}
            except Exception as e:
                log.debug(f"[PARALLEL] Hunt via autonomous: {e}")

        # Fallback: factory directe
        if self._factory:
            try:
                sector = payload.get("sector", "PME")
                bps = self._factory.hunt_and_create(sector)
                # Sauvegarde pipeline
                if self._db and bps:
                    for bp in bps:
                        self._db.save_pipeline_signal(
                            payload.get("project_id", "P01"),
                            bp.id,
                            pain_score=0.75,
                            solvability=0.80,
                            price_floor=1000,
                            price_target=bp.price_recommended,
                            lead_sector=sector,
                            source="autonomous_hunt",
                        )
                return {"hunted": len(bps), "sector": sector}
            except Exception as e:
                return {"error": str(e), "sector": payload.get("sector")}
        return {"status": "no_engine", "payload": payload}

    def _content_fn(self, payload: Dict) -> Dict:
        if self._autonomous:
            try:
                from NAYA_CORE.autonomous_engine import MissionType
                m = self._autonomous.submit(
                    MissionType.GENERATE_CONTENT, payload, priority=4
                )
                return {"mission_id": m.id}
            except Exception as e:
                log.debug(f"[PARALLEL] Content via autonomous: {e}")

        # Fallback: génère un post générique
        if self._db:
            body = f"[Auto-content] {payload.get('channel','linkedin')} post for {payload.get('project_id','NAYA')}"
            cid = self._db.save_content(
                channel=payload.get("channel", "linkedin"),
                content_type=payload.get("content_type", "post"),
                body=body,
                project_id=payload.get("project_id"),
                tone=payload.get("tone", "professional"),
            )
            return {"content_id": cid}
        return {"status": "no_engine"}

    def _pipeline_eval_fn(self, payload: Dict) -> Dict:
        if not self._db: return {}
        pid = payload.get("id")
        score = payload.get("pain_score", 0.5)
        stage = payload.get("stage", "SIGNAL")
        new_stage = None
        if stage == "SIGNAL" and score >= 0.7:
            new_stage = "QUALIFIED"
        elif stage == "QUALIFIED" and score >= 0.85:
            new_stage = "CONTACTED"
        if new_stage and pid:
            self._db.advance_pipeline(pid, new_stage, f"Auto-avancé score={score:.2f}")
            return {"id": pid, "advanced_to": new_stage}
        return {"id": pid, "no_change": True}

    def _create_fn(self, payload: Dict) -> Dict:
        if self._factory:
            try:
                bp = self._factory.create_from_brief(
                    payload.get("brief", ""),
                    payload.get("category", "consulting")
                )
                if self._db:
                    self._db.save_business(bp.to_dict())
                return {"business_id": bp.id, "name": bp.name, "price": bp.price_recommended}
            except Exception as e:
                return {"error": str(e)}
        return {"status": "no_factory"}

    # ── Status ────────────────────────────────────────────────────────────────
    def get_status(self) -> Dict:
        with self._lock:
            recent = list(self._batches.values())[-5:]
        return {
            "mode": self.mode.value,
            "max_workers": self._max_workers,
            "stats": self.stats,
            "recent_batches": [
                {"id": b.batch_id, "tasks": len(b.tasks),
                 "success": b.success_count, "fail": b.fail_count,
                 "duration_ms": b.duration_ms}
                for b in recent
            ]
        }

    def shutdown(self):
        self._executor.shutdown(wait=False)


# ── Singleton ─────────────────────────────────────────────────────────────────
_orchestrator: Optional[ParallelOrchestrator] = None

def get_parallel_orchestrator(mode: str = "balanced") -> ParallelOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        try: m = WorkerMode(mode)
        except: m = WorkerMode.BALANCED
        _orchestrator = ParallelOrchestrator(m)
    return _orchestrator


# ── Extension: run_parallel_hunts ─────────────────────────────────────────────

def run_parallel_hunts_helper(sectors: list, mode: str = "balanced") -> dict:
    """
    Lance des hunts parallèles sur plusieurs secteurs en même temps.
    Utilisé par l'endpoint /orchestrate/parallel.
    Retourne un dict {secteur: résultats}.
    """
    from NAYA_CORE.naya_sovereign_engine import get_sovereign
    orch = get_parallel_orchestrator(mode)

    results = {}

    def hunt_sector(sector: str) -> dict:
        try:
            sov = get_sovereign()
            sov.add_sector(sector, [], 500000)
            cycle = sov.run_full_cycle()
            d = cycle.to_dict() if hasattr(cycle, "to_dict") else {}
            return {
                "sector": sector,
                "count": len(d.get("deals_detected", [])),
                "revenue_potential_eur": d.get("revenue_potential_eur", 0),
                "status": "completed",
            }
        except Exception as e:
            return {"sector": sector, "count": 0, "status": "error", "error": str(e)[:80]}

    # Créer les tâches parallèles
    from concurrent.futures import ThreadPoolExecutor, as_completed
    with ThreadPoolExecutor(max_workers=min(len(sectors), 4)) as ex:
        futures = {ex.submit(hunt_sector, s): s for s in sectors}
        for fut in as_completed(futures, timeout=120):
            sector = futures[fut]
            try:
                results[sector] = fut.result()
            except Exception as e:
                results[sector] = {"sector": sector, "count": 0, "status": "timeout", "error": str(e)[:60]}

    return results


# Monkey-patch sur la classe pour un accès naturel
ParallelOrchestrator.run_parallel_hunts = lambda self, sectors, mode="balanced": \
    run_parallel_hunts_helper(sectors, mode)
