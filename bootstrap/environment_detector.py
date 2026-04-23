"""NAYA V19 - Environment Detector - Detecte l environnement d execution."""
import os, logging, platform
from typing import Dict

log = logging.getLogger("NAYA.BOOT.ENV")

class EnvironmentDetector:
    """Detecte automatiquement l environnement: local, Docker, Cloud Run, VM."""

    def detect(self) -> Dict:
        env = os.getenv("NAYA_ENV", "local")
        is_docker = os.path.exists("/.dockerenv")
        is_cloudrun = bool(os.getenv("K_SERVICE"))
        is_vm = bool(os.getenv("VM_HOST"))

        if is_cloudrun:
            detected = "cloud_run"
        elif is_docker:
            detected = "docker"
        elif is_vm:
            detected = "vm"
        else:
            detected = "local"

        return {
            "environment": detected,
            "configured_env": env,
            "is_docker": is_docker,
            "is_cloud_run": is_cloudrun,
            "is_vm": is_vm,
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
            "cpu_count": os.cpu_count()
        }

    def get_deployment_config(self) -> Dict:
        env = self.detect()
        configs = {
            "local": {"workers": 1, "reload": True, "debug": True},
            "docker": {"workers": 2, "reload": False, "debug": False},
            "cloud_run": {"workers": 4, "reload": False, "debug": False},
            "vm": {"workers": 2, "reload": False, "debug": False},
        }
        return configs.get(env["environment"], configs["local"])

    def get_stats(self) -> Dict:
        return self.detect()
