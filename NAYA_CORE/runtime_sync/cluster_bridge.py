"""
NAYA_CORE — Runtime Sync Cluster Bridge
==========================================
Synchronise l'état entre les nœuds du cluster en temps réel.
"""
import json, time, logging, threading
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timezone

log = logging.getLogger("NAYA.CLUSTER_BRIDGE")

class ClusterBridge:
    """
    Pont de synchronisation cluster.
    Gère la réplication d'état entre nœuds NAYA.
    """

    def __init__(self, node_id: str = "node-primary"):
        self.node_id = node_id
        self._peers: Dict[str, Dict] = {}
        self._sync_handlers: List[Callable] = []
        self._state_version: int = 0
        self._last_sync: Optional[float] = None
        self._lock = threading.Lock()

    def register_peer(self, peer_id: str, endpoint: str) -> None:
        self._peers[peer_id] = {"id": peer_id, "endpoint": endpoint,
                                 "status": "CONNECTING", "last_seen": time.time()}
        log.info(f"Peer registered: {peer_id} @ {endpoint}")

    def sync_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self._state_version += 1
            self._last_sync = time.time()

        sync_payload = {
            "source_node": self.node_id,
            "version": self._state_version,
            "state": state,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "peers_notified": list(self._peers.keys()),
        }

        for handler in self._sync_handlers:
            try: handler(sync_payload)
            except Exception as e: log.error(f"Sync handler error: {e}")

        log.debug(f"State synced v{self._state_version} -> {len(self._peers)} peers")
        return sync_payload

    def on_sync(self, handler: Callable) -> None:
        self._sync_handlers.append(handler)

    def get_cluster_health(self) -> Dict[str, Any]:
        now = time.time()
        healthy_peers = [p for p in self._peers.values()
                         if now - p.get("last_seen", 0) < 30]
        return {
            "node_id": self.node_id,
            "total_peers": len(self._peers),
            "healthy_peers": len(healthy_peers),
            "state_version": self._state_version,
            "last_sync": self._last_sync,
            "sync_age_seconds": round(now - self._last_sync, 1) if self._last_sync else None,
            "cluster_healthy": len(healthy_peers) >= len(self._peers) * 0.6,
        }

    def heartbeat(self) -> Dict[str, Any]:
        return {"node_id": self.node_id, "ts": time.time(),
                "state_version": self._state_version, "status": "ALIVE"}


_BRIDGE: Optional[ClusterBridge] = None

def get_cluster_bridge(node_id: str = "node-primary") -> ClusterBridge:
    global _BRIDGE
    if _BRIDGE is None: _BRIDGE = ClusterBridge(node_id)
    return _BRIDGE

__all__ = ["ClusterBridge", "get_cluster_bridge"]
