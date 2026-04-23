"""
NAYA SUPREME V8 — Cloud Run Entry Point
Démarre le vrai système NAYA via le main.py racine.
Ce fichier est l'entrypoint pour Google Cloud Run.
"""
import os
import sys
from pathlib import Path

# Ajouter le parent (racine du projet) au PYTHONPATH
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Forcer l'environnement Cloud Run
os.environ.setdefault("NAYA_ENV", "cloud_run")
os.environ.setdefault("PORT", "8080")

# Importer et lancer le vrai main.py NAYA
if __name__ == "__main__":
    # Exécuter main.py racine
    import runpy
    runpy.run_path(str(ROOT / "main.py"), run_name="__main__")
else:
    # Mode import (pour Cloud Run qui fait `from main import app`)
    # On charge le système complet et on expose l'app FastAPI
    import importlib.util
    spec = importlib.util.spec_from_file_location("naya_main", ROOT / "main.py")
    naya_main = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(naya_main)

    # Exposer l'app FastAPI pour uvicorn/gunicorn
    if hasattr(naya_main, "api"):
        app = naya_main.api
    else:
        from fastapi import FastAPI
        app = FastAPI(title="NAYA SUPREME V8")

        @app.get("/health")
        def health():
            return {"status": "ok"}
