#!/usr/bin/env python3
"""
NAYA V19.6 - GLOBAL API KEYS IMPORTER
======================================
Solution unique pour importer TOUTES les clés API partout dans le système
Fonctionnne sans erreurs répétitives
"""

import os
import sys
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
from datetime import datetime

# ════════════════════════════════════════════════════════════════════════════
# STEP 1: LOAD FROM .ENV FILE (UTF-8 SAFE)
# ════════════════════════════════════════════════════════════════════════════

def load_env_file_safe(filepath: str = ".env.production.local") -> Dict[str, str]:
    """Load .env file safely with UTF-8 encoding"""
    env_vars = {}

    if not os.path.isfile(filepath):
        return env_vars

    try:
        # Try UTF-8 first
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            # Fallback to latin-1
            with open(filepath, 'r', encoding='latin-1') as f:
                content = f.read()
        except:
            # Last resort: binary read and decode
            with open(filepath, 'rb') as f:
                content = f.read().decode('utf-8', errors='ignore')

    # Parse lines
    for line in content.split('\n'):
        line = line.strip()

        # Skip comments and empty lines
        if not line or line.startswith('#'):
            continue

        # Parse KEY=VALUE
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()

            # Remove quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]

            if key and value:
                env_vars[key] = value

    return env_vars


# ════════════════════════════════════════════════════════════════════════════
# STEP 2: GLOBAL API KEYS MANAGER
# ════════════════════════════════════════════════════════════════════════════

class GlobalAPIKeysManager:
    """Gestionnaire global unique pour TOUTES les clés API"""

    _instance = None
    _initialized = False

    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize (only once)"""
        if GlobalAPIKeysManager._initialized:
            return

        self.keys: Dict[str, str] = {}
        self.loaded_from: List[str] = []
        self.errors: List[str] = []

        self._load_all_keys()
        GlobalAPIKeysManager._initialized = True

    def _load_all_keys(self):
        """Load keys from all sources"""

        # 1. Load from .env file
        env_file = ".env.production.local"
        file_keys = load_env_file_safe(env_file)
        self.keys.update(file_keys)
        if file_keys:
            self.loaded_from.append(f".env file ({len(file_keys)} keys)")

        # 2. Override with system environment variables
        env_keys = os.environ.copy()
        self.keys.update(env_keys)
        if env_keys:
            self.loaded_from.append(f"Environment ({len(env_keys)} keys)")

        # 3. Validate critical keys
        self._validate_critical_keys()

    def _validate_critical_keys(self):
        """Validate all critical keys are present"""
        critical = [
            'PAYPAL_CLIENT_ID',
            'PAYPAL_CLIENT_SECRET',
            'TELEGRAM_BOT_TOKEN',
            'TELEGRAM_OWNER_CHAT_ID'
        ]

        missing = [k for k in critical if k not in self.keys or not self.keys[k]]
        if missing:
            for key in missing:
                self.errors.append(f"CRITICAL: {key} not configured")

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get key safely"""
        return self.keys.get(key, default)

    def get_safe(self, key: str) -> str:
        """Get key or raise error"""
        value = self.keys.get(key)
        if not value:
            raise KeyError(f"API key not found: {key}")
        return value

    def get_all(self) -> Dict[str, str]:
        """Get all keys (safe - returns copy)"""
        return self.keys.copy()

    def is_configured(self, key: str) -> bool:
        """Check if key is configured"""
        return key in self.keys and bool(self.keys[key])

    def get_group(self, prefix: str) -> Dict[str, str]:
        """Get all keys with prefix"""
        return {
            k: v for k, v in self.keys.items()
            if k.startswith(prefix)
        }

    def show_status(self):
        """Display status"""
        print("\n" + "="*70)
        print("GLOBAL API KEYS MANAGER STATUS")
        print("="*70)
        print(f"\nLoaded from: {', '.join(self.loaded_from)}")
        print(f"Total keys: {len(self.keys)}")

        # Show critical
        print("\nCRITICAL KEYS:")
        critical = ['PAYPAL_CLIENT_ID', 'PAYPAL_CLIENT_SECRET',
                   'TELEGRAM_BOT_TOKEN', 'TELEGRAM_OWNER_CHAT_ID']
        for key in critical:
            configured = self.is_configured(key)
            symbol = "✓" if configured else "✗"
            print(f"  {symbol} {key}")

        # Show important
        print("\nIMPORTANT KEYS:")
        important = ['ANTHROPIC_API_KEY', 'GROQ_API_KEY',
                    'APOLLO_API_KEY', 'SERPER_API_KEY']
        for key in important:
            configured = self.is_configured(key)
            symbol = "✓" if configured else "✗"
            print(f"  {symbol} {key}")

        # Errors
        if self.errors:
            print("\nERRORS:")
            for error in self.errors:
                print(f"  ✗ {error}")

        print("="*70 + "\n")

        return len(self.errors) == 0


# ════════════════════════════════════════════════════════════════════════════
# STEP 3: GLOBAL SHORTCUTS (IMPORT ANYWHERE)
# ════════════════════════════════════════════════════════════════════════════

def init_api_keys() -> GlobalAPIKeysManager:
    """Initialize and return API keys manager"""
    return GlobalAPIKeysManager()


def get_api_key(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get API key globally"""
    manager = GlobalAPIKeysManager()
    return manager.get(key, default)


def get_api_key_safe(key: str) -> str:
    """Get API key or raise error"""
    manager = GlobalAPIKeysManager()
    return manager.get_safe(key)


def is_api_key_set(key: str) -> bool:
    """Check if API key is set"""
    manager = GlobalAPIKeysManager()
    return manager.is_configured(key)


# ════════════════════════════════════════════════════════════════════════════
# STEP 4: PAYMENT APIs
# ════════════════════════════════════════════════════════════════════════════

class PaymentAPIs:
    """All payment APIs accessible globally"""

    @staticmethod
    def paypal_client_id() -> str:
        return get_api_key_safe('PAYPAL_CLIENT_ID')

    @staticmethod
    def paypal_client_secret() -> str:
        return get_api_key_safe('PAYPAL_CLIENT_SECRET')

    @staticmethod
    def stripe_secret_key() -> Optional[str]:
        return get_api_key('STRIPE_SECRET_KEY')

    @staticmethod
    def deblok_secret_key() -> Optional[str]:
        return get_api_key('DEBLOKME_SECRET_KEY')

    @staticmethod
    def get_all() -> Dict[str, str]:
        manager = GlobalAPIKeysManager()
        return {
            'paypal_id': manager.get('PAYPAL_CLIENT_ID'),
            'paypal_secret': manager.get('PAYPAL_CLIENT_SECRET'),
            'stripe_key': manager.get('STRIPE_SECRET_KEY'),
            'deblok_key': manager.get('DEBLOKME_SECRET_KEY'),
        }


# ════════════════════════════════════════════════════════════════════════════
# STEP 5: NOTIFICATION APIs
# ════════════════════════════════════════════════════════════════════════════

class NotificationAPIs:
    """All notification APIs accessible globally"""

    @staticmethod
    def telegram_bot_token() -> str:
        return get_api_key_safe('TELEGRAM_BOT_TOKEN')

    @staticmethod
    def telegram_chat_id() -> str:
        return get_api_key_safe('TELEGRAM_OWNER_CHAT_ID')

    @staticmethod
    def sendgrid_api_key() -> Optional[str]:
        return get_api_key('SENDGRID_API_KEY')

    @staticmethod
    def get_all() -> Dict[str, str]:
        manager = GlobalAPIKeysManager()
        return {
            'telegram_token': manager.get('TELEGRAM_BOT_TOKEN'),
            'telegram_chat_id': manager.get('TELEGRAM_OWNER_CHAT_ID'),
            'sendgrid_key': manager.get('SENDGRID_API_KEY'),
        }


# ════════════════════════════════════════════════════════════════════════════
# STEP 6: LLM APIs
# ════════════════════════════════════════════════════════════════════════════

class LLMAPIS:
    """All LLM APIs accessible globally"""

    @staticmethod
    def anthropic_key() -> Optional[str]:
        return get_api_key('ANTHROPIC_API_KEY')

    @staticmethod
    def groq_key() -> Optional[str]:
        return get_api_key('GROQ_API_KEY')

    @staticmethod
    def openai_key() -> Optional[str]:
        return get_api_key('OPENAI_API_KEY')

    @staticmethod
    def get_priority_list() -> list:
        """Get LLM providers in priority order"""
        providers = []

        if LLMAPIS.anthropic_key():
            providers.append(('anthropic', LLMAPIS.anthropic_key()))
        if LLMAPIS.groq_key():
            providers.append(('groq', LLMAPIS.groq_key()))
        if LLMAPIS.openai_key():
            providers.append(('openai', LLMAPIS.openai_key()))

        return providers

    @staticmethod
    def get_primary() -> tuple:
        """Get primary LLM provider"""
        providers = LLMAPIS.get_priority_list()
        return providers[0] if providers else (None, None)


# ════════════════════════════════════════════════════════════════════════════
# STEP 7: PROSPECTION APIs
# ════════════════════════════════════════════════════════════════════════════

class ProspectionAPIs:
    """All prospection APIs accessible globally"""

    @staticmethod
    def apollo_key() -> Optional[str]:
        return get_api_key('APOLLO_API_KEY')

    @staticmethod
    def serper_key() -> Optional[str]:
        return get_api_key('SERPER_API_KEY')

    @staticmethod
    def hunter_key() -> Optional[str]:
        return get_api_key('HUNTER_API_KEY')

    @staticmethod
    def linkedin_id() -> Optional[str]:
        return get_api_key('LINKEDIN_CLIENT_ID')

    @staticmethod
    def linkedin_secret() -> Optional[str]:
        return get_api_key('LINKEDIN_CLIENT_SECRET')

    @staticmethod
    def get_all() -> Dict[str, str]:
        return {
            'apollo': ProspectionAPIs.apollo_key(),
            'serper': ProspectionAPIs.serper_key(),
            'hunter': ProspectionAPIs.hunter_key(),
            'linkedin_id': ProspectionAPIs.linkedin_id(),
            'linkedin_secret': ProspectionAPIs.linkedin_secret(),
        }


# ════════════════════════════════════════════════════════════════════════════
# STEP 8: BOOTSTRAP & INITIALIZATION
# ════════════════════════════════════════════════════════════════════════════

def bootstrap_api_keys():
    """Bootstrap function - call at app startup"""
    manager = init_api_keys()
    is_valid = manager.show_status()

    if not is_valid:
        print("\n⚠️  WARNING: Some critical API keys are missing!")
        print("Add them to .env.production.local before production use.\n")

    return is_valid


# ════════════════════════════════════════════════════════════════════════════
# USAGE EXAMPLE & TEST
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "="*70)
    print("GLOBAL API KEYS IMPORTER - TEST")
    print("="*70)

    # Initialize
    is_valid = bootstrap_api_keys()

    # Show how to use
    print("\nUSAGE EXAMPLES:")
    print("─" * 70)
    print("""
# Anywhere in your code:

# Option 1: Direct global import
from core.global_api_keys import (
    get_api_key,
    get_api_key_safe,
    PaymentAPIs,
    NotificationAPIs,
    LLMAPIS,
    ProspectionAPIs
)

# Get keys directly
paypal_id = get_api_key_safe('PAYPAL_CLIENT_ID')
stripe_key = get_api_key('STRIPE_SECRET_KEY')

# Use organized APIs
telegram_token = NotificationAPIs.telegram_bot_token()
anthropic_key = LLMAPIS.anthropic_key()
apollo_key = ProspectionAPIs.apollo_key()

# Get all keys of a type
payment_apis = PaymentAPIs.get_all()
notification_apis = NotificationAPIs.get_all()

# Get LLM in priority order
llm_providers = LLMAPIS.get_priority_list()

# Option 2: Manager instance
from core.global_api_keys import GlobalAPIKeysManager

manager = GlobalAPIKeysManager()
paypal = manager.get('PAYPAL_CLIENT_ID')
all_keys = manager.get_all()
    """)

    print("─" * 70)

    if is_valid:
        print("\n✓ Ready to use global API keys!")
    else:
        print("\n✗ Fix missing API keys in .env.production.local")

    print("\n" + "="*70 + "\n")
