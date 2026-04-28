"""
NAYA SUPREME V19 — Security Module 7/10
error_classifier.py — Classification patterns d'erreurs

Agent 11 — Guardian Agent
Rôle : Classifier erreurs par pattern ML pour auto-réparation
"""

import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict, Counter
import hashlib


class ErrorClassifier:
    """
    Classificateur d'erreurs par pattern.
    Utilise ML simple (pattern matching + fréquence) pour identifier erreurs récurrentes.
    """

    def __init__(self, project_root: str = "/home/runner/work/V19/V19"):
        self.project_root = Path(project_root)
        self.errors_db_path = self.project_root / "data" / "errors" / "error_patterns.json"
        self.errors_db_path.parent.mkdir(parents=True, exist_ok=True)

        # Base de patterns connus
        self.known_patterns = self._load_known_patterns()

        # Erreurs détectées (session actuelle)
        self.detected_errors: List[Dict[str, Any]] = []

        # Stats erreurs
        self.error_stats = defaultdict(int)

    def _load_known_patterns(self) -> Dict[str, Dict[str, Any]]:
        """
        Charge patterns d'erreurs connus.

        Returns:
            Dict des patterns
        """
        if self.errors_db_path.exists():
            try:
                with open(self.errors_db_path, 'r') as f:
                    return json.load(f)
            except Exception:
                pass

        # Patterns par défaut
        return {
            "network_timeout": {
                "patterns": [
                    r"timeout",
                    r"timed out",
                    r"connection timeout",
                    r"read timeout"
                ],
                "category": "network",
                "severity": "MEDIUM",
                "auto_fixable": True,
                "fix_strategy": "retry_with_backoff",
                "description": "Timeout réseau lors d'appel API"
            },
            "rate_limit": {
                "patterns": [
                    r"rate limit",
                    r"429",
                    r"too many requests",
                    r"quota exceeded"
                ],
                "category": "api",
                "severity": "MEDIUM",
                "auto_fixable": True,
                "fix_strategy": "wait_and_retry",
                "description": "Limite de taux API dépassée"
            },
            "authentication_failed": {
                "patterns": [
                    r"authentication failed",
                    r"invalid api key",
                    r"unauthorized",
                    r"401"
                ],
                "category": "auth",
                "severity": "HIGH",
                "auto_fixable": False,
                "fix_strategy": "manual_key_rotation",
                "description": "Échec authentification API"
            },
            "database_locked": {
                "patterns": [
                    r"database is locked",
                    r"sqlite.*locked",
                    r"unable to open database"
                ],
                "category": "database",
                "severity": "HIGH",
                "auto_fixable": True,
                "fix_strategy": "retry_with_delay",
                "description": "Base de données verrouillée"
            },
            "out_of_memory": {
                "patterns": [
                    r"out of memory",
                    r"memory error",
                    r"cannot allocate memory"
                ],
                "category": "system",
                "severity": "CRITICAL",
                "auto_fixable": False,
                "fix_strategy": "restart_service",
                "description": "Mémoire insuffisante"
            },
            "file_not_found": {
                "patterns": [
                    r"file not found",
                    r"no such file",
                    r"filenotfounderror"
                ],
                "category": "filesystem",
                "severity": "MEDIUM",
                "auto_fixable": True,
                "fix_strategy": "create_missing_file",
                "description": "Fichier manquant"
            },
            "json_decode_error": {
                "patterns": [
                    r"json.*decode",
                    r"invalid json",
                    r"expecting value"
                ],
                "category": "parsing",
                "severity": "MEDIUM",
                "auto_fixable": True,
                "fix_strategy": "validate_json",
                "description": "Erreur décodage JSON"
            },
            "import_error": {
                "patterns": [
                    r"importerror",
                    r"no module named",
                    r"cannot import"
                ],
                "category": "dependency",
                "severity": "HIGH",
                "auto_fixable": True,
                "fix_strategy": "install_dependency",
                "description": "Module Python manquant"
            },
            "llm_api_error": {
                "patterns": [
                    r"anthropic.*error",
                    r"openai.*error",
                    r"model not found",
                    r"invalid request"
                ],
                "category": "llm",
                "severity": "HIGH",
                "auto_fixable": True,
                "fix_strategy": "fallback_llm",
                "description": "Erreur API LLM"
            },
            "permission_denied": {
                "patterns": [
                    r"permission denied",
                    r"access denied",
                    r"forbidden"
                ],
                "category": "permissions",
                "severity": "HIGH",
                "auto_fixable": True,
                "fix_strategy": "fix_permissions",
                "description": "Permissions insuffisantes"
            }
        }

    def classify_error(
        self,
        error_message: str,
        error_type: Optional[str] = None,
        stacktrace: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Classifie une erreur.

        Args:
            error_message: Message d'erreur
            error_type: Type d'exception
            stacktrace: Stack trace complète
            context: Contexte d'exécution

        Returns:
            Classification de l'erreur
        """
        classification = {
            "timestamp": datetime.now().isoformat(),
            "error_message": error_message,
            "error_type": error_type,
            "pattern_match": None,
            "category": "unknown",
            "severity": "MEDIUM",
            "auto_fixable": False,
            "fix_strategy": None,
            "confidence": 0.0,
            "fingerprint": self._generate_fingerprint(error_message, error_type),
            "context": context or {}
        }

        # Chercher pattern correspondant
        best_match = None
        best_confidence = 0.0

        combined_text = f"{error_message} {error_type or ''} {stacktrace or ''}".lower()

        for pattern_name, pattern_info in self.known_patterns.items():
            confidence = 0.0
            matches = 0

            for pattern in pattern_info["patterns"]:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    matches += 1

            if matches > 0:
                confidence = matches / len(pattern_info["patterns"])

                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = pattern_name

        # Appliquer meilleur match
        if best_match and best_confidence >= 0.5:
            pattern_info = self.known_patterns[best_match]
            classification.update({
                "pattern_match": best_match,
                "category": pattern_info["category"],
                "severity": pattern_info["severity"],
                "auto_fixable": pattern_info["auto_fixable"],
                "fix_strategy": pattern_info["fix_strategy"],
                "confidence": best_confidence,
                "description": pattern_info["description"]
            })

        # Sauvegarder erreur
        self.detected_errors.append(classification)
        self.error_stats[classification["category"]] += 1

        return classification

    def _generate_fingerprint(self, error_message: str, error_type: Optional[str]) -> str:
        """
        Génère fingerprint unique pour l'erreur.

        Args:
            error_message: Message d'erreur
            error_type: Type d'erreur

        Returns:
            Fingerprint SHA-256
        """
        # Normaliser message (supprimer nombres, timestamps, etc.)
        normalized = re.sub(r'\d+', 'N', error_message)
        normalized = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', 'UUID', normalized)

        combined = f"{error_type or 'unknown'}:{normalized}"

        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def detect_recurring_errors(self, threshold: int = 3) -> List[Dict[str, Any]]:
        """
        Détecte erreurs récurrentes.

        Args:
            threshold: Nombre minimum d'occurrences

        Returns:
            Liste des erreurs récurrentes
        """
        fingerprint_counts = Counter(
            error["fingerprint"]
            for error in self.detected_errors
        )

        recurring = []

        for fingerprint, count in fingerprint_counts.items():
            if count >= threshold:
                # Trouver exemple d'erreur
                example = next(
                    e for e in self.detected_errors
                    if e["fingerprint"] == fingerprint
                )

                recurring.append({
                    "fingerprint": fingerprint,
                    "count": count,
                    "pattern_match": example.get("pattern_match"),
                    "category": example.get("category"),
                    "severity": example.get("severity"),
                    "auto_fixable": example.get("auto_fixable"),
                    "fix_strategy": example.get("fix_strategy"),
                    "example_message": example["error_message"]
                })

        return sorted(recurring, key=lambda x: x["count"], reverse=True)

    def suggest_fixes(self, error_classification: Dict[str, Any]) -> List[str]:
        """
        Suggère corrections pour une erreur.

        Args:
            error_classification: Classification de l'erreur

        Returns:
            Liste de suggestions
        """
        suggestions = []

        fix_strategy = error_classification.get("fix_strategy")

        if fix_strategy == "retry_with_backoff":
            suggestions.append("Réessayer avec backoff exponentiel (1s, 2s, 4s, 8s)")
            suggestions.append("Augmenter timeout de base")

        elif fix_strategy == "wait_and_retry":
            suggestions.append("Attendre 60 secondes avant nouvelle tentative")
            suggestions.append("Utiliser API alternative si disponible")

        elif fix_strategy == "manual_key_rotation":
            suggestions.append("Vérifier validité clé API")
            suggestions.append("Régénérer clé API si expirée")
            suggestions.append("Vérifier permissions de la clé")

        elif fix_strategy == "retry_with_delay":
            suggestions.append("Attendre 500ms et réessayer")
            suggestions.append("Utiliser WAL mode pour SQLite")

        elif fix_strategy == "restart_service":
            suggestions.append("Redémarrer service concerné")
            suggestions.append("Augmenter limite mémoire")

        elif fix_strategy == "create_missing_file":
            suggestions.append("Créer fichier/dossier manquant")
            suggestions.append("Vérifier permissions d'écriture")

        elif fix_strategy == "validate_json":
            suggestions.append("Valider format JSON avant parsing")
            suggestions.append("Ajouter gestion erreur décodage")

        elif fix_strategy == "install_dependency":
            suggestions.append("Installer dépendance manquante: pip install <package>")
            suggestions.append("Vérifier requirements.txt")

        elif fix_strategy == "fallback_llm":
            suggestions.append("Basculer vers LLM alternatif (Groq → DeepSeek)")
            suggestions.append("Réduire taille du prompt")

        elif fix_strategy == "fix_permissions":
            suggestions.append("Ajuster permissions: chmod 644 <file>")
            suggestions.append("Vérifier ownership: chown user:group <file>")

        if not suggestions:
            suggestions.append("Erreur non auto-fixable — Intervention manuelle requise")

        return suggestions

    def get_error_stats(self) -> Dict[str, Any]:
        """
        Statistiques des erreurs.

        Returns:
            Stats globales
        """
        stats = {
            "timestamp": datetime.now().isoformat(),
            "total_errors": len(self.detected_errors),
            "by_category": dict(self.error_stats),
            "by_severity": {},
            "auto_fixable": 0,
            "recurring": len(self.detect_recurring_errors())
        }

        # Par sévérité
        for error in self.detected_errors:
            severity = error.get("severity", "UNKNOWN")
            stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1

        # Auto-fixables
        stats["auto_fixable"] = sum(
            1 for e in self.detected_errors
            if e.get("auto_fixable", False)
        )

        return stats

    def export_patterns(self) -> bool:
        """
        Exporte patterns d'erreurs.

        Returns:
            True si succès
        """
        try:
            with open(self.errors_db_path, 'w') as f:
                json.dump(self.known_patterns, f, indent=2)

            print(f"✅ [CLASSIFIER] Patterns exportés: {self.errors_db_path}")
            return True

        except Exception as e:
            print(f"❌ [CLASSIFIER] Erreur export: {e}")
            return False

    def learn_from_error(
        self,
        error_classification: Dict[str, Any],
        was_fixed: bool,
        fix_applied: Optional[str] = None
    ) -> None:
        """
        Apprend d'une erreur résolue.

        Args:
            error_classification: Classification de l'erreur
            was_fixed: Si l'erreur a été résolue
            fix_applied: Fix appliqué
        """
        fingerprint = error_classification["fingerprint"]

        # Créer nouveau pattern si récurrent et fixé
        if was_fixed and fix_applied:
            pattern_name = f"learned_{fingerprint}"

            if pattern_name not in self.known_patterns:
                self.known_patterns[pattern_name] = {
                    "patterns": [error_classification["error_message"][:50]],
                    "category": error_classification.get("category", "learned"),
                    "severity": error_classification.get("severity", "MEDIUM"),
                    "auto_fixable": True,
                    "fix_strategy": fix_applied,
                    "description": f"Pattern appris: {fingerprint}",
                    "learned_at": datetime.now().isoformat()
                }

                self.export_patterns()
                print(f"📚 [CLASSIFIER] Nouveau pattern appris: {pattern_name}")


async def main():
    """Test du classifier."""
    classifier = ErrorClassifier()

    print("\n" + "="*60)
    print("🔍 NAYA ERROR CLASSIFIER")
    print("="*60)

    # Test classification
    test_errors = [
        ("Connection timeout after 30s", "TimeoutError", None),
        ("API rate limit exceeded", "HTTPError", None),
        ("Invalid API key provided", "AuthenticationError", None),
        ("Database is locked", "sqlite3.OperationalError", None),
        ("Out of memory", "MemoryError", None)
    ]

    for error_msg, error_type, stacktrace in test_errors:
        classification = classifier.classify_error(error_msg, error_type, stacktrace)
        print(f"\nErreur: {error_msg}")
        print(f"  Catégorie: {classification['category']}")
        print(f"  Sévérité: {classification['severity']}")
        print(f"  Auto-fixable: {classification['auto_fixable']}")
        print(f"  Confiance: {classification['confidence']:.2f}")

        suggestions = classifier.suggest_fixes(classification)
        print(f"  Suggestions:")
        for suggestion in suggestions:
            print(f"    - {suggestion}")

    # Stats
    stats = classifier.get_error_stats()
    print(f"\n📊 Stats:")
    print(f"  Total erreurs: {stats['total_errors']}")
    print(f"  Par catégorie: {stats['by_category']}")
    print(f"  Auto-fixables: {stats['auto_fixable']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
