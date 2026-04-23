"""
NAYA V19 — HUGGINGFACE MULTI-CLÉS PROVIDER
Rotation automatique sur 4 clés HuggingFace pour éviter les rate limits.
Modèles: Mistral-7B, Zephyr-7B, Phi-3, Llama3 (gratuit, inference API).

4 clés → 4x plus de capacité, rotation cyclique automatique.
"""

import os
import json
import time
import logging
import urllib.request
from typing import Dict, Any, Optional, List

log = logging.getLogger("NAYA.LLM.HF.MULTI")


def _gs(key: str, default: str = "") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(key, default) or default
    except Exception:
        return os.environ.get(key, default)


class HuggingFaceMultiKeyProvider:
    """
    HuggingFace Inference API avec rotation automatique de 4 clés.
    Évite les rate limits: quand une clé est throttlée → passe à la suivante.
    Gratuit: ~30 000 req/jour total avec 4 clés.
    """

    # Modèles par ordre de qualité (essaie dans l'ordre)
    MODELS = [
        "mistralai/Mistral-7B-Instruct-v0.3",
        "HuggingFaceH4/zephyr-7b-beta",
        "microsoft/Phi-3-mini-4k-instruct",
        "meta-llama/Meta-Llama-3-8B-Instruct",
        "tiiuae/falcon-7b-instruct",
    ]
    BASE_URL = "https://api-inference.huggingface.co/models/"

    def __init__(self):
        # Charger les 4 clés disponibles
        self._keys = self._load_keys()
        self._current_key_idx = 0
        self._key_errors: Dict[str, int] = {}
        self._calls = 0
        self._success = 0

        if self._keys:
            log.info(f"✅ HuggingFace multi-clés: {len(self._keys)} clé(s) chargée(s)")
        else:
            log.debug("HuggingFace: aucune clé configurée")

    def _load_keys(self) -> List[str]:
        """Charge toutes les clés HF disponibles."""
        keys = []
        # Sources: variables individuelles + principale
        sources = [
            "HUGGINGFACE_API_KEY", "HF_API_KEY",
            "HF_API_KEY_1", "HF_API_KEY_2",
            "HF_API_KEY_3", "HF_API_KEY_4",
        ]
        for src in sources:
            key = _gs(src)
            if key and key.startswith("hf_") and len(key) > 20 and key not in keys:
                keys.append(key)
        return keys

    @property
    def available(self) -> bool:
        return len(self._keys) > 0

    def _get_next_key(self) -> Optional[str]:
        """Retourne la prochaine clé disponible (rotation round-robin)."""
        if not self._keys:
            return None

        # Trouver une clé avec moins de 3 erreurs consécutives
        for _ in range(len(self._keys)):
            key = self._keys[self._current_key_idx % len(self._keys)]
            self._current_key_idx += 1
            if self._key_errors.get(key, 0) < 3:
                return key

        # Toutes les clés en erreur → reset et réessayer
        self._key_errors.clear()
        return self._keys[0]

    def execute(self, prompt: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self.available:
            return {"provider": "huggingface", "error": "No keys configured", "text": None}

        params = params or {}
        system = params.get("system", "Tu es NAYA SUPREME, assistant business expert et stratège.")
        max_tokens = min(params.get("max_tokens", 1024), 2048)
        temperature = params.get("temperature", 0.4)

        # Formater prompt selon le format Mistral/Zephyr
        formatted_prompt = f"<s>[INST] {system}\n\n{prompt} [/INST]"

        self._calls += 1

        # Essayer chaque modèle avec rotation des clés
        for model_idx, model in enumerate(self.MODELS[:3]):
            api_key = self._get_next_key()
            if not api_key:
                break

            try:
                payload = json.dumps({
                    "inputs": formatted_prompt,
                    "parameters": {
                        "max_new_tokens": max_tokens,
                        "temperature": temperature,
                        "do_sample": True,
                        "return_full_text": False,
                        "repetition_penalty": 1.1,
                    }
                }).encode("utf-8")

                req = urllib.request.Request(
                    self.BASE_URL + model,
                    data=payload,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    method="POST"
                )

                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))

                if isinstance(data, list) and data:
                    text = data[0].get("generated_text", "").strip()
                    if text:
                        # Reset erreurs pour cette clé
                        self._key_errors[api_key] = 0
                        self._success += 1
                        return {
                            "provider": "huggingface",
                            "model": model,
                            "key_index": self._keys.index(api_key) + 1,
                            "text": text,
                            "free": True,
                        }

                elif isinstance(data, dict) and data.get("error"):
                    err = data["error"]
                    if "loading" in err.lower():
                        # Modèle en cours de chargement → attendre et réessayer
                        time.sleep(3)
                        continue
                    if "rate limit" in err.lower() or "429" in err:
                        self._key_errors[api_key] = self._key_errors.get(api_key, 0) + 1
                        continue

            except urllib.error.HTTPError as e:
                if e.code == 429:
                    # Rate limit → marquer cette clé, passer à la suivante
                    self._key_errors[api_key] = self._key_errors.get(api_key, 0) + 1
                    log.debug(f"[HF] Rate limit sur clé {self._keys.index(api_key)+1}, rotation")
                    continue
                elif e.code == 503:
                    # Modèle pas chargé → essayer le suivant
                    continue
                log.debug(f"[HF] HTTP {e.code} sur {model}")
                continue

            except Exception as e:
                log.debug(f"[HF] {model}: {e}")
                continue

        return {"provider": "huggingface", "error": "All models/keys failed", "text": None}

    def think(self, task: str, context: Dict = None) -> str:
        """Pensée rapide."""
        ctx = f"\nContexte: {context}" if context else ""
        result = self.execute(task + ctx)
        return result.get("text") or ""

    def get_stats(self) -> Dict:
        return {
            "provider": "huggingface_multi",
            "available": self.available,
            "keys_count": len(self._keys),
            "key_health": {
                f"key_{i+1}": {
                    "errors": self._key_errors.get(k, 0),
                    "healthy": self._key_errors.get(k, 0) < 3,
                }
                for i, k in enumerate(self._keys)
            },
            "calls_total": self._calls,
            "success_total": self._success,
            "models_available": self.MODELS[:3],
        }
