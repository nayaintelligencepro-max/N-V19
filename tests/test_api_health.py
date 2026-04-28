"""Tests for NAYA API health and endpoints."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


def test_fastapi_app_creates():
    from NAYA_CORE.api.main import app
    assert app is not None
    assert app.title == "NAYA SUPREME V21"


def test_root_endpoint():
    from NAYA_CORE.api.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert "docs" in data
    assert "health" in data


def test_health_endpoint():
    from NAYA_CORE.api.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "python" in data


def test_docs_endpoint():
    from NAYA_CORE.api.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/docs")
    assert response.status_code == 200


def test_config_endpoint():
    from NAYA_CORE.api.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/api/v1/config")
    assert response.status_code == 200
    data = response.json()
    assert "log_level" in data
