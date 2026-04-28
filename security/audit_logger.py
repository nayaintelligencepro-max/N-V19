"""
NAYA SUPREME V19 — Security Module 4/10
audit_logger.py — Logs immuables avec chaînage SHA-256

Agent 11 — Guardian Agent
Rôle : Logging immuable de toutes opérations critiques
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
from enum import Enum


class LogLevel(Enum):
    """Niveaux de log."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    FINANCIAL = "FINANCIAL"  # Opérations financières
    SECURITY = "SECURITY"    # Événements sécurité


class AuditLogger:
    """
    Logger immuable avec chaînage SHA-256.
    Chaque log contient hash du log précédent → blockchain-like.
    """

    def __init__(
        self,
        project_root: str = "/home/runner/work/V19/V19",
        log_dir: Optional[str] = None
    ):
        self.project_root = Path(project_root)
        self.log_dir = Path(log_dir) if log_dir else self.project_root / "data" / "audit_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Fichier log actuel
        today = datetime.now().strftime("%Y%m%d")
        self.current_log_file = self.log_dir / f"audit_{today}.jsonl"

        # Hash du dernier log (chaînage)
        self.last_hash = self._load_last_hash()

        # Lock pour écriture concurrente
        self.write_lock = asyncio.Lock()

    def _load_last_hash(self) -> str:
        """
        Charge le hash du dernier log enregistré.

        Returns:
            Hash du dernier log ou hash initial
        """
        try:
            if self.current_log_file.exists():
                # Lire dernière ligne
                with open(self.current_log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        last_log = json.loads(lines[-1])
                        return last_log.get("hash", self._genesis_hash())

            return self._genesis_hash()

        except Exception:
            return self._genesis_hash()

    def _genesis_hash(self) -> str:
        """Hash initial pour le premier log."""
        return hashlib.sha256(b"NAYA_SUPREME_V19_GENESIS").hexdigest()

    def _calculate_hash(self, log_entry: Dict[str, Any]) -> str:
        """
        Calcule hash SHA-256 d'un log.

        Args:
            log_entry: Entrée de log

        Returns:
            Hash SHA-256
        """
        # Créer représentation canonique
        canonical = json.dumps(log_entry, sort_keys=True)

        # Hash = SHA256(previous_hash + current_log)
        combined = f"{self.last_hash}{canonical}"

        return hashlib.sha256(combined.encode()).hexdigest()

    async def log(
        self,
        level: LogLevel,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Enregistre un log immuable.

        Args:
            level: Niveau de log
            message: Message principal
            context: Contexte additionnel
            tags: Tags pour filtrage

        Returns:
            Hash du log créé
        """
        async with self.write_lock:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": level.value,
                "message": message,
                "context": context or {},
                "tags": tags or [],
                "previous_hash": self.last_hash,
                "sequence": self._get_next_sequence()
            }

            # Calculer hash
            log_hash = self._calculate_hash(log_entry)
            log_entry["hash"] = log_hash

            # Écrire log
            await self._write_log(log_entry)

            # Mettre à jour dernier hash
            self.last_hash = log_hash

            return log_hash

    async def _write_log(self, log_entry: Dict[str, Any]) -> None:
        """
        Écrit log dans fichier JSONL.

        Args:
            log_entry: Entrée de log
        """
        try:
            with open(self.current_log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')

        except Exception as e:
            print(f"❌ [AUDIT] Erreur écriture log: {e}")

    def _get_next_sequence(self) -> int:
        """
        Obtient numéro de séquence suivant.

        Returns:
            Numéro de séquence
        """
        try:
            if self.current_log_file.exists():
                with open(self.current_log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        last_log = json.loads(lines[-1])
                        return last_log.get("sequence", 0) + 1

            return 1

        except Exception:
            return 1

    async def log_financial(
        self,
        operation: str,
        amount_eur: float,
        details: Dict[str, Any]
    ) -> str:
        """
        Log opération financière.

        Args:
            operation: Type d'opération (payment, invoice, contract)
            amount_eur: Montant en EUR
            details: Détails de l'opération

        Returns:
            Hash du log
        """
        context = {
            "operation": operation,
            "amount_eur": amount_eur,
            "currency": "EUR",
            **details
        }

        return await self.log(
            LogLevel.FINANCIAL,
            f"Opération financière: {operation} — {amount_eur} EUR",
            context=context,
            tags=["financial", operation]
        )

    async def log_security(
        self,
        event: str,
        severity: str,
        details: Dict[str, Any]
    ) -> str:
        """
        Log événement de sécurité.

        Args:
            event: Type d'événement
            severity: Sévérité (LOW, MEDIUM, HIGH, CRITICAL)
            details: Détails de l'événement

        Returns:
            Hash du log
        """
        context = {
            "event": event,
            "severity": severity,
            **details
        }

        return await self.log(
            LogLevel.SECURITY,
            f"Événement sécurité: {event} [{severity}]",
            context=context,
            tags=["security", event, severity.lower()]
        )

    async def log_critical(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log erreur critique.

        Args:
            error: Exception levée
            context: Contexte d'exécution

        Returns:
            Hash du log
        """
        import traceback

        error_context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            **(context or {})
        }

        return await self.log(
            LogLevel.CRITICAL,
            f"Erreur critique: {type(error).__name__}",
            context=error_context,
            tags=["error", "critical"]
        )

    def verify_chain(self) -> Dict[str, Any]:
        """
        Vérifie intégrité de la chaîne de logs.

        Returns:
            Rapport de vérification
        """
        print("🔍 [AUDIT] Vérification intégrité chaîne...")

        report = {
            "timestamp": datetime.now().isoformat(),
            "file": str(self.current_log_file),
            "total_logs": 0,
            "verified_logs": 0,
            "corrupted_logs": [],
            "status": "UNKNOWN"
        }

        try:
            if not self.current_log_file.exists():
                report["status"] = "NO_LOGS"
                return report

            with open(self.current_log_file, 'r') as f:
                logs = [json.loads(line) for line in f]

            report["total_logs"] = len(logs)

            # Vérifier chaînage
            previous_hash = self._genesis_hash()

            for idx, log_entry in enumerate(logs):
                # Vérifier hash précédent
                if log_entry.get("previous_hash") != previous_hash:
                    report["corrupted_logs"].append({
                        "sequence": log_entry.get("sequence"),
                        "expected_previous": previous_hash,
                        "actual_previous": log_entry.get("previous_hash")
                    })
                else:
                    # Vérifier hash du log
                    stored_hash = log_entry.pop("hash")
                    calculated_hash = self._calculate_hash(log_entry)
                    log_entry["hash"] = stored_hash

                    if calculated_hash == stored_hash:
                        report["verified_logs"] += 1
                    else:
                        report["corrupted_logs"].append({
                            "sequence": log_entry.get("sequence"),
                            "hash_mismatch": True
                        })

                previous_hash = log_entry.get("hash")

            # Status final
            if report["corrupted_logs"]:
                report["status"] = "CORRUPTED"
            else:
                report["status"] = "VERIFIED"

            print(f"✅ [AUDIT] {report['verified_logs']}/{report['total_logs']} logs vérifiés")

            return report

        except Exception as e:
            report["status"] = "ERROR"
            report["error"] = str(e)
            return report

    def query_logs(
        self,
        level: Optional[LogLevel] = None,
        tags: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Recherche dans les logs.

        Args:
            level: Filtrer par niveau
            tags: Filtrer par tags
            start_date: Date de début
            end_date: Date de fin
            limit: Nombre max de résultats

        Returns:
            Liste des logs correspondants
        """
        results = []

        try:
            if not self.current_log_file.exists():
                return results

            with open(self.current_log_file, 'r') as f:
                for line in f:
                    log_entry = json.loads(line)

                    # Filtrer par niveau
                    if level and log_entry.get("level") != level.value:
                        continue

                    # Filtrer par tags
                    if tags:
                        log_tags = set(log_entry.get("tags", []))
                        if not any(tag in log_tags for tag in tags):
                            continue

                    # Filtrer par date
                    log_date = datetime.fromisoformat(log_entry["timestamp"])
                    if start_date and log_date < start_date:
                        continue
                    if end_date and log_date > end_date:
                        continue

                    results.append(log_entry)

                    if len(results) >= limit:
                        break

            return results

        except Exception as e:
            print(f"❌ [AUDIT] Erreur recherche logs: {e}")
            return []

    def rotate_logs(self, keep_days: int = 90) -> Dict[str, Any]:
        """
        Archive et compresse anciens logs.

        Args:
            keep_days: Nombre de jours à conserver

        Returns:
            Rapport de rotation
        """
        import gzip
        from datetime import timedelta

        print(f"🔄 [AUDIT] Rotation logs (conserver {keep_days}j)...")

        report = {
            "timestamp": datetime.now().isoformat(),
            "archived": 0,
            "deleted": 0,
            "errors": []
        }

        try:
            cutoff_date = datetime.now() - timedelta(days=keep_days)

            for log_file in self.log_dir.glob("audit_*.jsonl"):
                # Parser date du fichier
                date_str = log_file.stem.replace("audit_", "")
                try:
                    file_date = datetime.strptime(date_str, "%Y%m%d")

                    if file_date < cutoff_date:
                        # Compresser
                        archive_path = log_file.with_suffix('.jsonl.gz')

                        with open(log_file, 'rb') as f_in:
                            with gzip.open(archive_path, 'wb') as f_out:
                                f_out.write(f_in.read())

                        # Supprimer original
                        log_file.unlink()

                        report["archived"] += 1

                except ValueError:
                    report["errors"].append(f"Date invalide: {log_file.name}")

            print(f"✅ [AUDIT] {report['archived']} fichiers archivés")

            return report

        except Exception as e:
            report["error"] = str(e)
            return report

    def get_stats(self) -> Dict[str, Any]:
        """
        Statistiques des logs.

        Returns:
            Stats globales
        """
        stats = {
            "current_log_file": str(self.current_log_file),
            "total_logs": 0,
            "by_level": {},
            "by_tag": {},
            "chain_status": "unknown",
            "file_size_mb": 0
        }

        try:
            if self.current_log_file.exists():
                stats["file_size_mb"] = self.current_log_file.stat().st_size / (1024 * 1024)

                with open(self.current_log_file, 'r') as f:
                    for line in f:
                        log_entry = json.loads(line)
                        stats["total_logs"] += 1

                        # Par niveau
                        level = log_entry.get("level", "UNKNOWN")
                        stats["by_level"][level] = stats["by_level"].get(level, 0) + 1

                        # Par tag
                        for tag in log_entry.get("tags", []):
                            stats["by_tag"][tag] = stats["by_tag"].get(tag, 0) + 1

                # Vérifier intégrité
                verify_result = self.verify_chain()
                stats["chain_status"] = verify_result["status"]

            return stats

        except Exception as e:
            stats["error"] = str(e)
            return stats


async def main():
    """Test de l'audit logger."""
    logger = AuditLogger()

    print("\n" + "="*60)
    print("📝 NAYA AUDIT LOGGER")
    print("="*60)

    # Test logs divers
    await logger.log(LogLevel.INFO, "Démarrage système")
    await logger.log(LogLevel.DEBUG, "Test debug", context={"user": "test"})

    # Log financier
    await logger.log_financial(
        "payment_received",
        15000.0,
        {"client": "Test Corp", "invoice_id": "INV-001"}
    )

    # Log sécurité
    await logger.log_security(
        "scan_completed",
        "MEDIUM",
        {"vulnerabilities_found": 3}
    )

    # Vérifier chaîne
    verification = logger.verify_chain()
    print(f"\nVérification: {verification['status']}")
    print(f"Logs vérifiés: {verification['verified_logs']}/{verification['total_logs']}")

    # Stats
    stats = logger.get_stats()
    print(f"\nStats:")
    print(f"  Total logs: {stats['total_logs']}")
    print(f"  Taille: {stats['file_size_mb']:.2f} MB")
    print(f"  Par niveau: {stats['by_level']}")


if __name__ == "__main__":
    asyncio.run(main())
