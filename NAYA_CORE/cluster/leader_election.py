"""NAYA V19 — Leader Election (Bully Algorithm simplified)"""
import time, logging, threading, hashlib
from typing import Dict, Optional, List
log = logging.getLogger("NAYA.CLUSTER.LEADER")

class LeaderElection:
    """Élection de leader dans le cluster — algorithme Bully simplifié."""
    ELECTION_TIMEOUT = 15.0
    HEARTBEAT_INTERVAL = 30.0
    
    def __init__(self, node_id: str = "primary", priority: int = 100):
        self.node_id = node_id
        self.priority = priority
        self._leader: Optional[str] = node_id  # Auto-leader en single mode
        self._candidates: Dict[str, int] = {node_id: priority}
        self._lock = threading.RLock()
        self._election_in_progress = False
        self._last_heartbeat: Dict[str, float] = {node_id: time.time()}
        self._election_count = 0
    
    def add_candidate(self, node_id: str, priority: int):
        with self._lock:
            self._candidates[node_id] = priority
            self._last_heartbeat[node_id] = time.time()
            log.info(f"[LEADER] Candidat ajouté: {node_id} (prio={priority})")
    
    def remove_candidate(self, node_id: str):
        with self._lock:
            self._candidates.pop(node_id, None)
            self._last_heartbeat.pop(node_id, None)
            if self._leader == node_id:
                self._trigger_election()
    
    def _trigger_election(self):
        """Lance une élection de leader."""
        self._election_in_progress = True
        self._election_count += 1
        now = time.time()
        
        # Filtrer les nœuds vivants
        alive = {nid: prio for nid, prio in self._candidates.items()
                 if now - self._last_heartbeat.get(nid, 0) < self.ELECTION_TIMEOUT * 3}
        
        if not alive:
            self._leader = self.node_id
        else:
            # Le nœud avec la plus haute priorité gagne
            winner = max(alive.items(), key=lambda x: x[1])
            self._leader = winner[0]
        
        self._election_in_progress = False
        log.info(f"[LEADER] Élu: {self._leader} (élection #{self._election_count})")
    
    def elect(self) -> str:
        with self._lock:
            self._trigger_election()
            return self._leader
    
    def heartbeat(self, node_id: str):
        with self._lock:
            self._last_heartbeat[node_id] = time.time()
    
    @property
    def leader(self) -> str:
        return self._leader or self.node_id
    
    @property
    def is_leader(self) -> bool:
        return self._leader == self.node_id
    
    def check_leader_alive(self) -> bool:
        if not self._leader: return False
        last = self._last_heartbeat.get(self._leader, 0)
        alive = (time.time() - last) < self.HEARTBEAT_INTERVAL * 2
        if not alive:
            log.warning(f"[LEADER] Leader {self._leader} non responsive — nouvelle élection")
            self.elect()
        return alive
    
    def get_status(self) -> Dict:
        with self._lock:
            return {
                "current_leader": self._leader, "is_leader": self.is_leader,
                "node_id": self.node_id, "candidates": len(self._candidates),
                "election_count": self._election_count,
                "election_in_progress": self._election_in_progress,
            }
