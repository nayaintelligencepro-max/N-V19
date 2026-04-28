"""NAYA V19 - Dual Bootstrap - Boot kernel + system registry."""
import logging, json, time
from pathlib import Path
log = logging.getLogger("NAYA.KERNEL.BOOT")

class DualBootstrap:
    def __init__(self):
        self._boot_log: list = []

    def boot(self) -> dict:
        results = {}
        try:
            from NAYA_CORE.core.engine_master import EngineMaster
            core = EngineMaster()
            results["core"] = "ok"
        except Exception as e:
            results["core"] = str(e)[:50]
        try:
            from SYSTEM_REGISTRY.module_registry import ModuleRegistry
            registry = ModuleRegistry()
            results["registry"] = f"{len(registry._modules)} modules"
        except Exception as e:
            results["registry"] = str(e)[:50]
        self._boot_log.append({"ts": time.time(), "results": results})
        return results

if __name__ == "__main__":
    import logging; logging.basicConfig(level=logging.INFO)
    print(DualBootstrap().boot())
