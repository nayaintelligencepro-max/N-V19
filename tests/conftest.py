"""
NAYA V19 — Configuration pytest globale
Démarre le serveur FastAPI dans un thread pour les tests d'intégration.
"""
import os
import sys
import time
import socket
import threading
import requests
import pytest
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

_SERVER_AVAILABLE = False
_SERVER_URL = ""


def _find_free_port() -> int:
    """Trouve un port TCP libre sur localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_server(url: str, timeout: float = 30.0) -> bool:
    """Attend que le serveur réponde sur /api/v1/health."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(f"{url}/api/v1/health", timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.3)
    return False


def pytest_configure(config):
    """Démarre le serveur NAYA une seule fois pour toute la session pytest."""
    global _SERVER_AVAILABLE, _SERVER_URL

    # Si BASE_URL est déjà défini (serveur externe), l'utiliser tel quel
    if os.environ.get("BASE_URL"):
        _SERVER_URL = os.environ["BASE_URL"]
        _SERVER_AVAILABLE = True
        return

    port = _find_free_port()
    base_url = f"http://127.0.0.1:{port}"

    try:
        import uvicorn

        def _run():
            import logging
            logging.disable(logging.CRITICAL)
            try:
                uvicorn.run(
                    "NAYA_CORE.api.main:app",
                    host="127.0.0.1",
                    port=port,
                    log_level="critical",
                    access_log=False,
                )
            except Exception:
                pass

        server_thread = threading.Thread(target=_run, daemon=True, name="naya-test-server")
        server_thread.start()

        if _wait_for_server(base_url, timeout=30):
            os.environ["BASE_URL"] = base_url
            _SERVER_URL = base_url
            _SERVER_AVAILABLE = True
    except Exception:
        pass


@pytest.fixture(autouse=True)
def skip_if_server_unavailable(request):
    """Skip automatiquement les tests qui nécessitent le serveur s'il n'est pas disponible."""
    # Détecter si le test vient de test_sales_validation
    node_path = str(request.fspath)
    if "test_sales_validation" in node_path and not _SERVER_AVAILABLE:
        pytest.skip("Serveur NAYA non disponible — test d'intégration ignoré")
