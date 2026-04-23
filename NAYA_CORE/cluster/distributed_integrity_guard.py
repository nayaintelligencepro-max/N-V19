"""
NAYA V19 — Distributed Integrity Guard
Vérifie l'intégrité des données distribuées entre les nœuds du cluster.
Détecte les corruptions, les désynchronisations et les altérations non autorisées.
"""
import hashlib
import time
import logging
import threading
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

log = logging.getLogger("NAYA.CLUSTER.INTEGRITY")


@dataclass
class IntegrityCheckpoint:
    node_id: str
    data_hash: str
    timestamp: float
    version: int
    status: str = "valid"


@dataclass
class IntegrityViolation:
    node_id: str
    expected_hash: str
    actual_hash: str
    detected_at: float
    severity: str = "warning"
    resolved: bool = False


class DistributedIntegrityGuard:
    """
    Garde d'intégrité distribuée.
    Vérifie que toutes les copies de données à travers le cluster sont identiques.
    Détecte et signale toute corruption ou divergence.
    """

    CHECK_INTERVAL = 120  # Vérification toutes les 2 minutes

    def __init__(self):
        self._checkpoints: Dict[str, IntegrityCheckpoint] = {}
        self._violations: List[IntegrityViolation] = []
        self._lock = threading.RLock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._reference_hashes: Dict[str, str] = {}
        self._total_checks = 0
        self._total_violations = 0

    def compute_hash(self, data: bytes) -> str:
        """Calcule le hash SHA-256 des données pour vérification d'intégrité."""
        return hashlib.sha256(data).hexdigest()

    def register_checkpoint(self, node_id: str, data: bytes, version: int = 1) -> IntegrityCheckpoint:
        """Enregistre un checkpoint d'intégrité pour un nœud."""
        data_hash = self.compute_hash(data)
        checkpoint = IntegrityCheckpoint(
            node_id=node_id,
            data_hash=data_hash,
            timestamp=time.time(),
            version=version
        )
        with self._lock:
            self._checkpoints[node_id] = checkpoint
            if node_id not in self._reference_hashes:
                self._reference_hashes[node_id] = data_hash
        log.debug(f"[INTEGRITY] Checkpoint enregistré: {node_id} v{version}")
        return checkpoint

    def verify_node(self, node_id: str, current_data: bytes) -> Tuple[bool, Optional[IntegrityViolation]]:
        """Vérifie l'intégrité des données d'un nœud contre le hash de référence."""
        current_hash = self.compute_hash(current_data)
        self._total_checks += 1

        with self._lock:
            ref_hash = self._reference_hashes.get(node_id)

        if ref_hash is None:
            self.register_checkpoint(node_id, current_data)
            return True, None

        if current_hash == ref_hash:
            return True, None

        violation = IntegrityViolation(
            node_id=node_id,
            expected_hash=ref_hash,
            actual_hash=current_hash,
            detected_at=time.time(),
            severity="critical" if node_id.startswith("core") else "warning"
        )
        with self._lock:
            self._violations.append(violation)
            self._total_violations += 1
            if len(self._violations) > 1000:
                self._violations = self._violations[-500:]

        log.warning(f"[INTEGRITY] VIOLATION détectée sur {node_id}: attendu={ref_hash[:12]}... obtenu={current_hash[:12]}...")
        return False, violation

    def verify_cluster_consensus(self, node_data: Dict[str, bytes]) -> Dict:
        """Vérifie que tous les nœuds ont des données cohérentes."""
        hashes = {}
        for node_id, data in node_data.items():
            hashes[node_id] = self.compute_hash(data)

        unique_hashes = set(hashes.values())
        consensus = len(unique_hashes) == 1

        if not consensus:
            majority_hash = max(set(hashes.values()), key=list(hashes.values()).count)
            divergent = [nid for nid, h in hashes.items() if h != majority_hash]
            log.warning(f"[INTEGRITY] Consensus échoué: {len(divergent)} nœuds divergents sur {len(node_data)}")
            return {
                "consensus": False,
                "majority_hash": majority_hash,
                "divergent_nodes": divergent,
                "total_nodes": len(node_data)
            }

        return {"consensus": True, "hash": list(unique_hashes)[0], "total_nodes": len(node_data)}

    def update_reference(self, node_id: str, new_data: bytes) -> None:
        """Met à jour le hash de référence après une modification légitime."""
        new_hash = self.compute_hash(new_data)
        with self._lock:
            self._reference_hashes[node_id] = new_hash
            if node_id in self._checkpoints:
                self._checkpoints[node_id].data_hash = new_hash
                self._checkpoints[node_id].timestamp = time.time()
                self._checkpoints[node_id].version += 1

    def resolve_violation(self, node_id: str) -> int:
        """Marque toutes les violations d'un nœud comme résolues."""
        resolved = 0
        with self._lock:
            for v in self._violations:
                if v.node_id == node_id and not v.resolved:
                    v.resolved = True
                    resolved += 1
        return resolved

    def start(self):
        """Démarre la vérification d'intégrité périodique."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._check_loop, name="INTEGRITY-GUARD", daemon=True)
        self._thread.start()
        log.info("[INTEGRITY] Garde d'intégrité démarrée")

    def stop(self):
        """Arrête la vérification périodique."""
        self._running = False

    def _check_loop(self):
        """Boucle de vérification périodique des checkpoints."""
        time.sleep(30)
        while self._running:
            try:
                with self._lock:
                    stale = []
                    now = time.time()
                    for nid, cp in self._checkpoints.items():
                        age = now - cp.timestamp
                        if age > self.CHECK_INTERVAL * 3:
                            stale.append(nid)
                            cp.status = "stale"
                    if stale:
                        log.warning(f"[INTEGRITY] {len(stale)} checkpoints périmés: {stale}")
            except Exception as e:
                log.error(f"[INTEGRITY] Erreur vérification: {e}")
            time.sleep(self.CHECK_INTERVAL)

    def get_unresolved_violations(self) -> List[IntegrityViolation]:
        """Retourne les violations non résolues."""
        with self._lock:
            return [v for v in self._violations if not v.resolved]

    def get_stats(self) -> Dict:
        """Retourne les statistiques d'intégrité."""
        with self._lock:
            unresolved = sum(1 for v in self._violations if not v.resolved)
            return {
                "total_checks": self._total_checks,
                "total_violations": self._total_violations,
                "unresolved_violations": unresolved,
                "monitored_nodes": len(self._checkpoints),
                "reference_hashes": len(self._reference_hashes),
                "running": self._running
            }


_guard = None
_guard_lock = threading.Lock()

def get_integrity_guard() -> DistributedIntegrityGuard:
    global _guard
    if _guard is None:
        with _guard_lock:
            if _guard is None:
                _guard = DistributedIntegrityGuard()
    return _guard
