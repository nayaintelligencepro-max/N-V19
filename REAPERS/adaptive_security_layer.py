# REAPERS/adaptive_security_layer.py

import logging
import threading

log = logging.getLogger("NAYA.REAPERS.security")
from datetime import datetime, timezone


class AdaptiveSecurityLayer:
    """
    Dynamically adjusts security posture based on system signals.
    """

    def __init__(self) -> None:
        self._security_level = 1  # 1 = Normal, 2 = Elevated, 3 = Critical
        self._last_update = datetime.now(timezone.utc)
        self._lock = threading.Lock()

    # ---------------------------------------------------------
    # SECURITY LEVEL CONTROL
    # ---------------------------------------------------------

    def set_level(self, level: int) -> None:
        with self._lock:
            if level < 1:
                level = 1
            if level > 3:
                level = 3

            self._security_level = level
            self._last_update = datetime.now(timezone.utc)

            log.warning(f"[REAPERS] Security level set to {self._security_level}")

    def get_level(self) -> int:
        with self._lock:
            return self._security_level

    def last_update(self):
        return self._last_update

    # ---------------------------------------------------------
    # AUTO-ADAPTATION
    # ---------------------------------------------------------

    def evaluate_threat(
        self,
        integrity_breach: bool,
        debugger_detected: bool,
        repeated_failures: bool
    ) -> None:

        with self._lock:

            if integrity_breach or debugger_detected:
                self._security_level = 3

            elif repeated_failures:
                self._security_level = 2

            else:
                self._security_level = 1

            self._last_update = datetime.now(timezone.utc)

    # ---------------------------------------------------------
    # SECURITY BEHAVIOR FLAGS
    # ---------------------------------------------------------

    def require_strict_monitoring(self) -> bool:
        return self.get_level() >= 2

    def require_runtime_restriction(self) -> bool:
        return self.get_level() == 3
