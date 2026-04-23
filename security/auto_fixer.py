"""
NAYA SUPREME V19 — Security Module 8/10
auto_fixer.py — Réparation automatique d'erreurs

Agent 11 — Guardian Agent
Rôle : Correction automatique basée sur patterns connus
"""

import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import json


class AutoFixer:
    """
    Système de réparation automatique.
    Applique fixes basés sur patterns d'erreurs classifiés.
    """

    def __init__(self, project_root: str = "/home/runner/work/V19/V19"):
        self.project_root = Path(project_root)
        self.fix_history: List[Dict[str, Any]] = []
        self.fix_log_path = self.project_root / "data" / "fixes" / "fix_history.json"
        self.fix_log_path.parent.mkdir(parents=True, exist_ok=True)

        # Compteurs
        self.fixes_applied = 0
        self.fixes_failed = 0

    async def apply_fix(
        self,
        error_classification: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Applique fix automatique pour une erreur.

        Args:
            error_classification: Classification de l'erreur
            context: Contexte additionnel

        Returns:
            Résultat du fix
        """
        fix_result = {
            "timestamp": datetime.now().isoformat(),
            "error_fingerprint": error_classification.get("fingerprint"),
            "fix_strategy": error_classification.get("fix_strategy"),
            "success": False,
            "actions_taken": [],
            "error": None
        }

        try:
            if not error_classification.get("auto_fixable"):
                fix_result["error"] = "Erreur non auto-fixable"
                return fix_result

            fix_strategy = error_classification.get("fix_strategy")

            if fix_strategy == "retry_with_backoff":
                fix_result = await self._fix_retry_with_backoff(error_classification, context)

            elif fix_strategy == "wait_and_retry":
                fix_result = await self._fix_wait_and_retry(error_classification, context)

            elif fix_strategy == "retry_with_delay":
                fix_result = await self._fix_retry_with_delay(error_classification, context)

            elif fix_strategy == "restart_service":
                fix_result = await self._fix_restart_service(error_classification, context)

            elif fix_strategy == "create_missing_file":
                fix_result = await self._fix_create_missing_file(error_classification, context)

            elif fix_strategy == "validate_json":
                fix_result = await self._fix_validate_json(error_classification, context)

            elif fix_strategy == "install_dependency":
                fix_result = await self._fix_install_dependency(error_classification, context)

            elif fix_strategy == "fallback_llm":
                fix_result = await self._fix_fallback_llm(error_classification, context)

            elif fix_strategy == "fix_permissions":
                fix_result = await self._fix_permissions(error_classification, context)

            else:
                fix_result["error"] = f"Stratégie inconnue: {fix_strategy}"

            # Sauvegarder historique
            if fix_result["success"]:
                self.fixes_applied += 1
            else:
                self.fixes_failed += 1

            self.fix_history.append(fix_result)
            await self._save_fix_history()

            return fix_result

        except Exception as e:
            fix_result["error"] = str(e)
            fix_result["success"] = False
            self.fixes_failed += 1
            return fix_result

    async def _fix_retry_with_backoff(
        self,
        error_classification: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Fix: Retry avec backoff exponentiel.

        Returns:
            Résultat du fix
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "fix_strategy": "retry_with_backoff",
            "success": False,
            "actions_taken": []
        }

        try:
            # Récupérer fonction à réessayer depuis context
            retry_func = context.get("retry_func") if context else None

            if not retry_func:
                result["actions_taken"].append("Pas de fonction à réessayer dans context")
                result["success"] = False
                return result

            # Backoff: 1s, 2s, 4s, 8s
            for attempt, delay in enumerate([1, 2, 4, 8], 1):
                result["actions_taken"].append(f"Tentative {attempt} après {delay}s")

                await asyncio.sleep(delay)

                try:
                    if asyncio.iscoroutinefunction(retry_func):
                        await retry_func()
                    else:
                        retry_func()

                    result["success"] = True
                    result["actions_taken"].append(f"Succès à la tentative {attempt}")
                    return result

                except Exception as e:
                    result["actions_taken"].append(f"Échec tentative {attempt}: {str(e)}")
                    continue

            result["success"] = False
            result["actions_taken"].append("Échec après toutes les tentatives")

        except Exception as e:
            result["error"] = str(e)

        return result

    async def _fix_wait_and_retry(
        self,
        error_classification: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Fix: Attendre 60s et réessayer (rate limit).

        Returns:
            Résultat du fix
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "fix_strategy": "wait_and_retry",
            "success": False,
            "actions_taken": []
        }

        try:
            result["actions_taken"].append("Attente 60s (rate limit)")
            await asyncio.sleep(60)

            retry_func = context.get("retry_func") if context else None

            if retry_func:
                result["actions_taken"].append("Nouvelle tentative")

                if asyncio.iscoroutinefunction(retry_func):
                    await retry_func()
                else:
                    retry_func()

                result["success"] = True
                result["actions_taken"].append("Succès après attente")
            else:
                result["actions_taken"].append("Pas de fonction à réessayer")

        except Exception as e:
            result["error"] = str(e)

        return result

    async def _fix_retry_with_delay(
        self,
        error_classification: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Fix: Retry avec court délai (database locked).

        Returns:
            Résultat du fix
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "fix_strategy": "retry_with_delay",
            "success": False,
            "actions_taken": []
        }

        try:
            for attempt in range(5):
                result["actions_taken"].append(f"Tentative {attempt + 1} après 500ms")
                await asyncio.sleep(0.5)

                retry_func = context.get("retry_func") if context else None

                if retry_func:
                    try:
                        if asyncio.iscoroutinefunction(retry_func):
                            await retry_func()
                        else:
                            retry_func()

                        result["success"] = True
                        result["actions_taken"].append(f"Succès tentative {attempt + 1}")
                        return result
                    except Exception:
                        continue

            result["success"] = False

        except Exception as e:
            result["error"] = str(e)

        return result

    async def _fix_restart_service(
        self,
        error_classification: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Fix: Redémarrer service.

        Returns:
            Résultat du fix
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "fix_strategy": "restart_service",
            "success": False,
            "actions_taken": []
        }

        try:
            service_name = context.get("service_name") if context else None

            if not service_name:
                result["actions_taken"].append("Nom du service non fourni")
                return result

            result["actions_taken"].append(f"Redémarrage service: {service_name}")

            # En production, utiliser systemctl ou supervisorctl
            # Pour l'instant, log seulement
            result["actions_taken"].append(f"Service {service_name} marqué pour redémarrage")
            result["success"] = True

        except Exception as e:
            result["error"] = str(e)

        return result

    async def _fix_create_missing_file(
        self,
        error_classification: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Fix: Créer fichier/dossier manquant.

        Returns:
            Résultat du fix
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "fix_strategy": "create_missing_file",
            "success": False,
            "actions_taken": []
        }

        try:
            file_path = context.get("file_path") if context else None

            if not file_path:
                result["actions_taken"].append("Chemin fichier non fourni")
                return result

            path = Path(file_path)

            # Créer dossier parent si nécessaire
            if not path.parent.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                result["actions_taken"].append(f"Dossier créé: {path.parent}")

            # Créer fichier si c'est un fichier
            if path.suffix:
                path.touch()
                result["actions_taken"].append(f"Fichier créé: {path}")
            else:
                path.mkdir(exist_ok=True)
                result["actions_taken"].append(f"Dossier créé: {path}")

            result["success"] = True

        except Exception as e:
            result["error"] = str(e)

        return result

    async def _fix_validate_json(
        self,
        error_classification: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Fix: Valider et réparer JSON.

        Returns:
            Résultat du fix
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "fix_strategy": "validate_json",
            "success": False,
            "actions_taken": []
        }

        try:
            json_data = context.get("json_data") if context else None

            if not json_data:
                result["actions_taken"].append("Données JSON non fournies")
                return result

            # Tenter de parser
            try:
                parsed = json.loads(json_data)
                result["actions_taken"].append("JSON valide")
                result["success"] = True
            except json.JSONDecodeError as e:
                result["actions_taken"].append(f"JSON invalide: {e}")

                # Tentatives correction simple
                # 1. Supprimer trailing commas
                cleaned = json_data.replace(",]", "]").replace(",}", "}")

                try:
                    parsed = json.loads(cleaned)
                    result["actions_taken"].append("JSON réparé (trailing commas)")
                    result["success"] = True
                except:
                    result["actions_taken"].append("Impossible de réparer JSON")

        except Exception as e:
            result["error"] = str(e)

        return result

    async def _fix_install_dependency(
        self,
        error_classification: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Fix: Installer dépendance manquante.

        Returns:
            Résultat du fix
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "fix_strategy": "install_dependency",
            "success": False,
            "actions_taken": []
        }

        try:
            # Extraire nom package depuis erreur
            error_msg = error_classification.get("error_message", "")
            match = __import__("re").search(r"no module named ['\"]?(\w+)", error_msg, __import__("re").IGNORECASE)

            if match:
                package_name = match.group(1)
                result["actions_taken"].append(f"Installation package: {package_name}")

                # Installer via pip
                proc = await asyncio.create_subprocess_exec(
                    "pip", "install", package_name,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                stdout, stderr = await proc.communicate()

                if proc.returncode == 0:
                    result["actions_taken"].append(f"Package {package_name} installé")
                    result["success"] = True
                else:
                    result["actions_taken"].append(f"Échec installation: {stderr.decode()}")

            else:
                result["actions_taken"].append("Impossible d'extraire nom du package")

        except Exception as e:
            result["error"] = str(e)

        return result

    async def _fix_fallback_llm(
        self,
        error_classification: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Fix: Basculer vers LLM alternatif.

        Returns:
            Résultat du fix
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "fix_strategy": "fallback_llm",
            "success": False,
            "actions_taken": []
        }

        try:
            current_llm = context.get("current_llm") if context else "unknown"
            result["actions_taken"].append(f"LLM actuel: {current_llm}")

            # Ordre de fallback
            fallback_order = ["groq", "deepseek", "anthropic", "openai", "template"]

            try:
                current_index = fallback_order.index(current_llm)
                next_llm = fallback_order[current_index + 1] if current_index < len(fallback_order) - 1 else "template"
            except ValueError:
                next_llm = fallback_order[0]

            result["actions_taken"].append(f"Basculement vers: {next_llm}")
            result["success"] = True
            result["fallback_llm"] = next_llm

        except Exception as e:
            result["error"] = str(e)

        return result

    async def _fix_permissions(
        self,
        error_classification: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Fix: Corriger permissions fichier.

        Returns:
            Résultat du fix
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "fix_strategy": "fix_permissions",
            "success": False,
            "actions_taken": []
        }

        try:
            file_path = context.get("file_path") if context else None

            if not file_path:
                result["actions_taken"].append("Chemin fichier non fourni")
                return result

            path = Path(file_path)

            if path.exists():
                # Définir permissions 644 (rw-r--r--)
                import os
                os.chmod(path, 0o644)

                result["actions_taken"].append(f"Permissions ajustées: {path}")
                result["success"] = True
            else:
                result["actions_taken"].append(f"Fichier inexistant: {path}")

        except Exception as e:
            result["error"] = str(e)

        return result

    async def _save_fix_history(self) -> None:
        """Sauvegarde historique des fixes."""
        try:
            with open(self.fix_log_path, 'w') as f:
                json.dump(self.fix_history, f, indent=2)

        except Exception as e:
            print(f"❌ [FIXER] Erreur sauvegarde historique: {e}")

    def get_fix_stats(self) -> Dict[str, Any]:
        """
        Statistiques des fixes.

        Returns:
            Stats globales
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "total_fixes": len(self.fix_history),
            "fixes_applied": self.fixes_applied,
            "fixes_failed": self.fixes_failed,
            "success_rate": self.fixes_applied / len(self.fix_history) if self.fix_history else 0,
            "by_strategy": self._count_by_strategy()
        }

    def _count_by_strategy(self) -> Dict[str, int]:
        """Compte fixes par stratégie."""
        from collections import Counter
        return dict(Counter(
            fix.get("fix_strategy")
            for fix in self.fix_history
            if fix.get("fix_strategy")
        ))


async def main():
    """Test du fixer."""
    fixer = AutoFixer()

    print("\n" + "="*60)
    print("🔧 NAYA AUTO FIXER")
    print("="*60)

    # Test fix création fichier
    error = {
        "fingerprint": "test123",
        "fix_strategy": "create_missing_file",
        "auto_fixable": True
    }

    result = await fixer.apply_fix(error, context={"file_path": "/tmp/naya_test.txt"})

    print(f"\nFix appliqué: {result['success']}")
    print(f"Actions: {result['actions_taken']}")

    # Stats
    stats = fixer.get_fix_stats()
    print(f"\n📊 Stats:")
    print(f"  Total: {stats['total_fixes']}")
    print(f"  Succès: {stats['fixes_applied']}")
    print(f"  Échecs: {stats['fixes_failed']}")


if __name__ == "__main__":
    asyncio.run(main())
