"""
NAYA SUPREME V19 — SECRETS MODULE
Auto-chargement de TOUTES les clés API au boot
"""
from .secrets_loader import (
    load_all_secrets,
    get_secret,
    is_configured,
    get_status,
    validate_all_keys,
    validate_production_secrets,
    print_diagnostic_report,
    auto_load_on_import,
)

__all__ = [
    "load_all_secrets",
    "get_secret",
    "is_configured",
    "get_status",
    "validate_all_keys",
    "validate_production_secrets",
    "print_diagnostic_report",
]

# 🔐 AUTO-CHARGEMENT DES SECRETS AU BOOT
# Charge automatiquement toutes les clés dès l'import de ce module
auto_load_on_import()
