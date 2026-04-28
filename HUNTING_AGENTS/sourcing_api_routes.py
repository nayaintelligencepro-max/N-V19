"""
NAYA SUPREME — Sourcing Agent API Routes
"""
from fastapi import APIRouter, HTTPException
from typing import Optional, List
import logging

log = logging.getLogger("NAYA.API.SOURCING")
router = APIRouter(prefix="/api/sourcing", tags=["sourcing-agent"])

_agent = None

def set_sourcing_agent(agent):
    global _agent
    _agent = agent

def _get():
    if not _agent: raise HTTPException(503, "Sourcing Agent not booted")
    return _agent


@router.get("/stats")
async def sourcing_stats():
    return _get().get_stats()

# ── BOTANICA ─────────────────────────────────────────────────────────────────

@router.post("/botanica/search")
async def search_botanica():
    """Lance une recherche complète de fournisseurs BOTANICA."""
    return _get().search_botanica_suppliers()

@router.get("/botanica/suppliers")
async def get_botanica_suppliers(n: int = 10):
    return {"suppliers": _get().get_botanica_suppliers(n)}

@router.get("/botanica/shipping")
async def botanica_shipping():
    return _get().get_shipping_estimate_botanica()

# ── TINY HOUSE ───────────────────────────────────────────────────────────────

@router.post("/tiny-house/search")
async def search_tiny_house():
    """Lance une recherche complète de fournisseurs TINY HOUSE."""
    return _get().search_tiny_house_suppliers()

@router.get("/tiny-house/suppliers")
async def get_tiny_house_suppliers(n: int = 10):
    return {"suppliers": _get().get_tiny_house_suppliers(n)}

@router.get("/tiny-house/shipping")
async def tiny_house_shipping(units: int = 1):
    return _get().get_shipping_estimate_tiny_house(units)

# ── GENERIC PROJECT ──────────────────────────────────────────────────────────

@router.post("/search")
async def search_generic(project_name: str, queries: str):
    """Recherche fournisseurs pour tout projet. queries=query1,query2,..."""
    return _get().search_for_project(project_name, queries.split(","))

# ── SAMPLES ──────────────────────────────────────────────────────────────────

@router.get("/samples")
async def list_samples():
    return {"samples": _get().get_all_samples()}

@router.post("/samples/request")
async def request_sample(supplier_id: str, project: str, products: str):
    """Demande un échantillon. products=product1,product2,..."""
    return _get().request_sample(supplier_id, project, products.split(","))

@router.put("/samples/{sample_id}/status")
async def update_sample(sample_id: str, status: str, tracking: str = ""):
    return _get().update_sample_status(sample_id, status, tracking)

# ── NEGOTIATION ──────────────────────────────────────────────────────────────

@router.get("/negotiate/{supplier_id}")
async def negotiate(supplier_id: str, target_price: float = 0, volume: int = 1):
    return _get().get_negotiation_strategy(supplier_id, target_price, volume)

# ── ORDERS ───────────────────────────────────────────────────────────────────

@router.get("/orders")
async def list_orders():
    return {"orders": _get().get_all_orders()}
