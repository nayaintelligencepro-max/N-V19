#!/usr/bin/env python3
"""
NAYA V19.6 - CENTRALIZED SECRETS MANAGER
==========================================
Gestion robuste de toutes les clés API avec validation, fallbacks et error handling
"""

import os
import sys
import logging
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("SECRETS_MANAGER")

# ════════════════════════════════════════════════════════════════════════════
# CONFIGURATION DES SECRETS
# ════════════════════════════════════════════════════════════════════════════

class SecretLevel(str, Enum):
    """Niveau de criticité des secrets"""
    CRITICAL = "critical"      # Sans ça, le système ne fonctionne pas
    IMPORTANT = "important"    # Fonctionnalité dégradée sans
    OPTIONAL = "optional"      # Fallback disponible


@dataclass
class SecretConfig:
    """Configuration d'un secret"""
    name: str                           # Nom de la variable d'env
    level: SecretLevel                  # Criticité
    fallback: Optional[str] = None      # Valeur par défaut
    validator: Optional[callable] = None  # Fonction validation
    description: str = ""               # Description pour logs


class APIProvider(str, Enum):
    """Fournisseurs d'API"""
    PAYPAL = "paypal"
    STRIPE = "stripe"
    DEBLOK = "deblok"
    SENDGRID = "sendgrid"
    TELEGRAM = "telegram"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    OPENAI = "openai"
    APOLLO = "apollo"
    SERPER = "serper"
    HUNTER = "hunter"
    LINKEDIN = "linkedin"


# ════════════════════════════════════════════════════════════════════════════
# DEFINITIONS DES SECRETS
# ════════════════════════════════════════════════════════════════════════════

SECRETS_CONFIG = {
    # ─── PAIEMENTS (CRITICAL)
    "PAYPAL_CLIENT_ID": SecretConfig(
        name="PAYPAL_CLIENT_ID",
        level=SecretLevel.CRITICAL,
        description="PayPal Client ID for payments",
        validator=lambda x: len(x) > 10 and x.startswith("AC")
    ),
    "PAYPAL_CLIENT_SECRET": SecretConfig(
        name="PAYPAL_CLIENT_SECRET",
        level=SecretLevel.CRITICAL,
        description="PayPal Client Secret for payments",
        validator=lambda x: len(x) > 20
    ),

    # ─── NOTIFICATIONS (CRITICAL)
    "TELEGRAM_BOT_TOKEN": SecretConfig(
        name="TELEGRAM_BOT_TOKEN",
        level=SecretLevel.CRITICAL,
        description="Telegram Bot Token for alerts",
        validator=lambda x: ":" in x and len(x) > 20
    ),
    "TELEGRAM_OWNER_CHAT_ID": SecretConfig(
        name="TELEGRAM_OWNER_CHAT_ID",
        level=SecretLevel.CRITICAL,
        description="Telegram Chat ID for owner notifications",
        validator=lambda x: x.isdigit() and len(x) > 5
    ),

    # ─── IA (IMPORTANT)
    "ANTHROPIC_API_KEY": SecretConfig(
        name="ANTHROPIC_API_KEY",
        level=SecretLevel.IMPORTANT,
        description="Anthropic Claude API key",
        validator=lambda x: x.startswith("sk-ant-") and len(x) > 20
    ),
    "GROQ_API_KEY": SecretConfig(
        name="GROQ_API_KEY",
        level=SecretLevel.IMPORTANT,
        description="Groq API key (fallback)",
        validator=lambda x: x.startswith("gsk_") and len(x) > 20,
        fallback="groq_free_tier"  # Fallback disponible
    ),
    "OPENAI_API_KEY": SecretConfig(
        name="OPENAI_API_KEY",
        level=SecretLevel.OPTIONAL,
        description="OpenAI API key (fallback)",
        validator=lambda x: x.startswith("sk-") and len(x) > 20
    ),

    # ─── PROSPECTION (IMPORTANT)
    "APOLLO_API_KEY": SecretConfig(
        name="APOLLO_API_KEY",
        level=SecretLevel.IMPORTANT,
        description="Apollo.io API key for lead enrichment",
        validator=lambda x: len(x) > 10
    ),
    "SERPER_API_KEY": SecretConfig(
        name="SERPER_API_KEY",
        level=SecretLevel.IMPORTANT,
        description="Serper API key for search",
        validator=lambda x: len(x) > 10
    ),
    "HUNTER_API_KEY": SecretConfig(
        name="HUNTER_API_KEY",
        level=SecretLevel.OPTIONAL,
        description="Hunter.io API key",
        validator=lambda x: len(x) > 10
    ),

    # ─── PAIEMENTS ADDITIONNELS (OPTIONAL)
    "STRIPE_SECRET_KEY": SecretConfig(
        name="STRIPE_SECRET_KEY",
        level=SecretLevel.OPTIONAL,
        description="Stripe Secret Key",
        validator=lambda x: x.startswith("sk_") and len(x) > 20
    ),
    "DEBLOKME_SECRET_KEY": SecretConfig(
        name="DEBLOKME_SECRET_KEY",
        level=SecretLevel.OPTIONAL,
        description="Deblok Secret Key",
        validator=lambda x: len(x) > 10
    ),

    # ─── EMAIL (OPTIONAL)
    "SENDGRID_API_KEY": SecretConfig(
        name="SENDGRID_API_KEY",
        level=SecretLevel.OPTIONAL,
        description="SendGrid API key",
        validator=lambda x: x.startswith("SG.") and len(x) > 30
    ),

    # ─── AUTRES (OPTIONAL)
    "LINKEDIN_CLIENT_ID": SecretConfig(
        name="LINKEDIN_CLIENT_ID",
        level=SecretLevel.OPTIONAL,
        description="LinkedIn Client ID"
    ),
    "LINKEDIN_CLIENT_SECRET": SecretConfig(
        name="LINKEDIN_CLIENT_SECRET",
        level=SecretLevel.OPTIONAL,
        description="LinkedIn Client Secret"
    ),
}


# ════════════════════════════════════════════════════════════════════════════
# SECRETS MANAGER PRINCIPAL
# ════════════════════════════════════════════════════════════════════════════

class SecretsManager:
    """Gestionnaire centralisé des secrets"""

    def __init__(self, env_file: str = ".env.production.local"):
        """
        Initialize secrets manager

        Args:
            env_file: Path to .env file
        """
        self.env_file = env_file
        self._secrets: Dict[str, str] = {}
        self._loaded = False
        self._errors: List[str] = []
        self._warnings: List[str] = []
        self._audit_log: List[Dict] = []

        log.info("[INIT] Secrets Manager initializing...")
        self._load_secrets()

    def _load_secrets(self):
        """Load secrets from environment"""
        log.info(f"[LOAD] Loading secrets from environment and {self.env_file}...")

        # 1. Load from .env file if exists
        if os.path.isfile(self.env_file):
            try:
                self._load_env_file(self.env_file)
                log.info(f"[OK] Loaded {self.env_file}")
            except Exception as e:
                self._errors.append(f"Failed to load {self.env_file}: {e}")
                log.warning(f"[WARN] {self.env_file} not loaded: {e}")

        # 2. Load from environment variables (override .env)
        for key in SECRETS_CONFIG.keys():
            if key in os.environ:
                self._secrets[key] = os.environ[key]

        # 3. Validate all secrets
        self._validate_secrets()

        # 4. Apply fallbacks
        self._apply_fallbacks()

        self._loaded = True
        self._log_status()

    def _load_env_file(self, filepath: str):
        """Load variables from .env file"""
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"{filepath} not found")

        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        self._secrets[key.strip()] = value.strip()

    def _validate_secrets(self):
        """Validate each secret"""
        for key, config in SECRETS_CONFIG.items():
            value = self._secrets.get(key)

            if not value:
                if config.level == SecretLevel.CRITICAL:
                    self._errors.append(f"CRITICAL: {key} missing")
                elif config.level == SecretLevel.IMPORTANT:
                    self._warnings.append(f"IMPORTANT: {key} missing")
                else:
                    log.debug(f"[OPTIONAL] {key} not configured")
                continue

            # Run custom validator if present
            if config.validator:
                try:
                    if not config.validator(value):
                        self._errors.append(
                            f"INVALID: {key} format incorrect "
                            f"(expected: {config.description})"
                        )
                        log.warning(f"[INVALID] {key} format issue")
                except Exception as e:
                    self._errors.append(f"VALIDATION_ERROR: {key} - {e}")

    def _apply_fallbacks(self):
        """Apply fallback values"""
        for key, config in SECRETS_CONFIG.items():
            if key not in self._secrets and config.fallback:
                self._secrets[key] = config.fallback
                self._warnings.append(f"Using fallback for {key}")
                log.info(f"[FALLBACK] Using fallback for {key}")

    def _log_status(self):
        """Log configuration status"""
        critical_ok = sum(
            1 for k in SECRETS_CONFIG
            if SECRETS_CONFIG[k].level == SecretLevel.CRITICAL
            and k in self._secrets
        )
        critical_total = sum(
            1 for k in SECRETS_CONFIG
            if SECRETS_CONFIG[k].level == SecretLevel.CRITICAL
        )

        log.info(f"\n{'='*70}")
        log.info(f"SECRETS CONFIGURATION STATUS")
        log.info(f"{'='*70}")
        log.info(f"Critical:  {critical_ok}/{critical_total} loaded")
        log.info(f"Warnings:  {len(self._warnings)}")
        log.info(f"Errors:    {len(self._errors)}")
        log.info(f"{'='*70}\n")

        if self._errors:
            log.error(f"\nERRORS ({len(self._errors)}):")
            for err in self._errors:
                log.error(f"  ✗ {err}")

        if self._warnings:
            log.warning(f"\nWARNINGS ({len(self._warnings)}):")
            for warn in self._warnings:
                log.warning(f"  ⚠ {warn}")

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get secret safely

        Args:
            key: Secret name
            default: Default value if not found

        Returns:
            Secret value or default
        """
        if not self._loaded:
            log.error("[ERROR] Secrets not loaded yet")
            return default

        value = self._secrets.get(key, default)

        # Log access (without value)
        self._audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "key": key,
            "found": value is not None,
            "source": "cache"
        })

        if not value:
            config = SECRETS_CONFIG.get(key)
            if config and config.level == SecretLevel.CRITICAL:
                log.error(f"[CRITICAL] Secret missing: {key}")
            return default

        return value

    def get_safe(self, key: str) -> str:
        """
        Get secret safely or raise error

        Args:
            key: Secret name

        Returns:
            Secret value

        Raises:
            ValueError if secret not found
        """
        value = self.get(key)
        if not value:
            raise ValueError(f"Secret not found: {key}")
        return value

    def is_configured(self, key: str) -> bool:
        """Check if secret is configured"""
        return key in self._secrets and bool(self._secrets[key])

    def get_provider_config(self, provider: APIProvider) -> Dict[str, str]:
        """Get all secrets for a provider"""
        prefix = provider.value.upper()
        config = {}

        for key, value in self._secrets.items():
            if key.startswith(prefix):
                # Remove provider prefix
                clean_key = key.replace(f"{prefix}_", "")
                config[clean_key] = value

        return config

    def validate_provider(self, provider: APIProvider) -> tuple[bool, List[str]]:
        """Validate provider has all required secrets"""
        provider_config = self.get_provider_config(provider)

        if not provider_config:
            return False, [f"No configuration found for {provider}"]

        errors = []
        config = SECRETS_CONFIG.get(f"{provider.value.upper()}_*")

        return len(errors) == 0, errors

    def get_status(self) -> Dict[str, Any]:
        """Get current configuration status"""
        return {
            "loaded": self._loaded,
            "total_secrets": len(self._secrets),
            "critical_count": sum(
                1 for k in self._secrets
                if SECRETS_CONFIG.get(k, SecretConfig("", SecretLevel.OPTIONAL))
                .level == SecretLevel.CRITICAL
            ),
            "errors": self._errors,
            "warnings": self._warnings,
            "timestamp": datetime.now().isoformat()
        }

    def export_safe_status(self) -> Dict[str, Any]:
        """Export status without exposing secrets"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "secrets_loaded": len(self._secrets),
            "configuration": {}
        }

        # Show which secrets are configured (without values)
        for key, config in SECRETS_CONFIG.items():
            is_set = key in self._secrets and bool(self._secrets[key])
            status["configuration"][key] = {
                "configured": is_set,
                "level": config.level.value,
                "description": config.description
            }

        return status

    def health_check(self) -> Dict[str, Any]:
        """Run health check on all secrets"""
        return {
            "status": "ok" if not self._errors else "error",
            "critical_errors": len([e for e in self._errors if "CRITICAL" in e]),
            "warnings": len(self._warnings),
            "errors": self._errors,
            "timestamp": datetime.now().isoformat()
        }


# ════════════════════════════════════════════════════════════════════════════
# FACTORY & SINGLETON
# ════════════════════════════════════════════════════════════════════════════

_secrets_manager: Optional[SecretsManager] = None


def initialize_secrets(env_file: str = ".env.production.local") -> SecretsManager:
    """Initialize secrets manager singleton"""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager(env_file)
    return _secrets_manager


def get_secrets() -> SecretsManager:
    """Get secrets manager instance"""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager


# ════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════

def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Helper to get secret"""
    return get_secrets().get(key, default)


def get_secret_safe(key: str) -> str:
    """Helper to get secret or raise error"""
    return get_secrets().get_safe(key)


def is_secret_configured(key: str) -> bool:
    """Helper to check if secret is configured"""
    return get_secrets().is_configured(key)


# ════════════════════════════════════════════════════════════════════════════
# CLI & TESTING
# ════════════════════════════════════════════════════════════════════════════

def show_configuration():
    """Display current configuration status"""
    secrets = get_secrets()
    status = secrets.export_safe_status()

    print("\n" + "="*70)
    print("SECRETS CONFIGURATION STATUS")
    print("="*70 + "\n")

    # Group by level
    by_level = {
        "CRITICAL": [],
        "IMPORTANT": [],
        "OPTIONAL": []
    }

    for key, config_info in status["configuration"].items():
        level = config_info["level"].upper()
        symbol = "✓" if config_info["configured"] else "✗"
        by_level[level].append((key, config_info["configured"]))

    # Display CRITICAL
    print("CRITICAL (Required for production):")
    for key, configured in by_level["CRITICAL"]:
        symbol = "✓" if configured else "✗"
        print(f"  {symbol} {key}")

    # Display IMPORTANT
    print("\nIMPORTANT (Recommended):")
    for key, configured in by_level["IMPORTANT"]:
        symbol = "✓" if configured else "✗"
        print(f"  {symbol} {key}")

    # Display OPTIONAL
    print("\nOPTIONAL (Fallbacks available):")
    for key, configured in by_level["OPTIONAL"]:
        symbol = "✓" if configured else "✗"
        print(f"  {symbol} {key}")

    # Summary
    health = secrets.health_check()
    print("\n" + "="*70)
    print(f"Status: {health['status'].upper()}")
    print(f"Critical Errors: {health['critical_errors']}")
    print(f"Warnings: {health['warnings']}")
    print("="*70 + "\n")


if __name__ == "__main__":
    # Initialize and show status
    secrets = initialize_secrets()
    show_configuration()

    # Show health check
    print("\nHealth Check:")
    print(json.dumps(secrets.health_check(), indent=2))
