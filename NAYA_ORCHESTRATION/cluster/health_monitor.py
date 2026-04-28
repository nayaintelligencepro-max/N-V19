"""NAYA — Cluster Health Monitor."""
import time,threading,logging
from dataclasses import dataclass,field
from typing import Dict,Callable,Optional
from enum import Enum

log=logging.getLogger("NAYA.ORCHESTRATION.HEALTH")

class HealthStatus(Enum):
    HEALTHY="healthy"; DEGRADED="degraded"; UNHEALTHY="unhealthy"; UNKNOWN="unknown"

@dataclass
class ComponentHealth:
    name: str; status: HealthStatus=HealthStatus.UNKNOWN
    last_check: float=0.0; failures: int=0; response_ms: float=0.0; message: str=""
    def to_dict(self): return {"name":self.name,"status":self.status.value,"failures":self.failures,"response_ms":round(self.response_ms,1),"message":self.message}

class HealthMonitor:
    CHECK_INTERVAL=30
    def __init__(self):
        self._comps: Dict[str,ComponentHealth]={}; self._checkers: Dict[str,Callable]={}
        self._lock=threading.RLock(); self._running=False; self._thread: Optional[threading.Thread]=None
    def register(self, name: str, checker: Callable=None):
        with self._lock: self._comps[name]=ComponentHealth(name=name)
        if checker: self._checkers[name]=checker
    def report(self, name,healthy,message="",ms=0.0):
        with self._lock:
            if name not in self._comps: self._comps[name]=ComponentHealth(name=name)
            c=self._comps[name]; c.last_check=time.time(); c.response_ms=ms; c.message=message
            if healthy: c.status=HealthStatus.HEALTHY; c.failures=0
            else: c.failures+=1; c.status=HealthStatus.UNHEALTHY if c.failures>=3 else HealthStatus.DEGRADED
    def start(self):
        if self._running: return
        self._running=True
        self._thread=threading.Thread(target=self._loop,daemon=True,name="NAYA-HEALTH")
        self._thread.start()
    def _loop(self):
        while self._running:
            for name,checker in dict(self._checkers).items():
                try:
                    t=time.time(); ok=checker(); ms=(time.time()-t)*1000; self.report(name,bool(ok),ms=ms)
                except Exception as e: self.report(name,False,str(e))
            time.sleep(self.CHECK_INTERVAL)
    def get_status(self) -> Dict:
        with self._lock: comps={n:c.to_dict() for n,c in self._comps.items()}
        h=sum(1 for c in comps.values() if c["status"]=="healthy"); t=len(comps)
        overall="healthy" if h==t and t>0 else "degraded" if h>0 else "unhealthy"
        return {"overall":overall,"healthy":h,"total":t,"components":comps}
    def is_healthy(self) -> bool:
        with self._lock: return all(c.status==HealthStatus.HEALTHY for c in self._comps.values())

_monitor=HealthMonitor()
def get_health_monitor() -> HealthMonitor: return _monitor
