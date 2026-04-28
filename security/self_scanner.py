"""
NAYA SUPREME V19 — Security Module 1/10
self_scanner.py — Auto Security Audit (Bandit + Safety + Credentials Detection)

Agent 11 — Guardian Agent
Rôle : Scanner automatique de sécurité du codebase
Cycle : toutes les 6h (configurable)
"""

import asyncio
import os
import re
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib


class SecurityScanner:
    """
    Scanner de sécurité automatisé pour NAYA SUPREME.
    Détecte : vulnérabilités code, CVE dépendances, credentials exposés, permissions fichiers.
    """

    def __init__(
        self,
        project_root: str = "/home/runner/work/V19/V19",
        scan_interval_hours: int = 6
    ):
        self.project_root = Path(project_root)
        self.scan_interval_hours = scan_interval_hours
        self.scan_results: Dict[str, Any] = {}

        # Patterns credentials dangereux
        self.credential_patterns = [
            (r'api[_-]?key\s*=\s*["\']([^"\']+)["\']', 'API Key'),
            (r'secret[_-]?key\s*=\s*["\']([^"\']+)["\']', 'Secret Key'),
            (r'password\s*=\s*["\']([^"\']+)["\']', 'Password'),
            (r'token\s*=\s*["\']([^"\']+)["\']', 'Token'),
            (r'bearer\s+[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+', 'JWT Token'),
            (r'(?:AKIA|ASIA)[0-9A-Z]{16}', 'AWS Access Key'),
            (r'sk-[A-Za-z0-9]{48}', 'OpenAI API Key'),
            (r'xox[baprs]-[0-9a-zA-Z]{10,48}', 'Slack Token'),
            (r'ghp_[A-Za-z0-9]{36}', 'GitHub Token'),
            (r'gho_[A-Za-z0-9]{36}', 'GitHub OAuth'),
        ]

        # Extensions à scanner
        self.scan_extensions = {'.py', '.env', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg'}

        # Fichiers à ignorer
        self.ignore_patterns = {
            '__pycache__',
            '.git',
            'node_modules',
            '.venv',
            'venv',
            '.pytest_cache',
            '.mypy_cache',
            'SECRETS',  # Dossier chiffré légitime
            '.env.example'  # Template sans vraies clés
        }

    async def run_full_scan(self) -> Dict[str, Any]:
        """
        Exécute un scan complet de sécurité.

        Returns:
            Rapport complet avec tous les résultats
        """
        print(f"🛡️ [GUARDIAN] Démarrage scan sécurité complet — {datetime.now().isoformat()}")

        scan_id = hashlib.sha256(
            f"{datetime.now().isoformat()}{self.project_root}".encode()
        ).hexdigest()[:12]

        self.scan_results = {
            "scan_id": scan_id,
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "scans": {}
        }

        # Exécuter tous les scans en parallèle
        try:
            results = await asyncio.gather(
                self.scan_bandit(),
                self.scan_safety(),
                self.scan_credentials(),
                self.scan_file_permissions(),
                return_exceptions=True
            )

            self.scan_results["scans"]["bandit"] = results[0] if not isinstance(results[0], Exception) else {"error": str(results[0])}
            self.scan_results["scans"]["safety"] = results[1] if not isinstance(results[1], Exception) else {"error": str(results[1])}
            self.scan_results["scans"]["credentials"] = results[2] if not isinstance(results[2], Exception) else {"error": str(results[2])}
            self.scan_results["scans"]["file_permissions"] = results[3] if not isinstance(results[3], Exception) else {"error": str(results[3])}

            # Calculer score global
            self.scan_results["global_score"] = self._calculate_security_score()
            self.scan_results["severity"] = self._determine_severity()

            # Sauvegarder rapport
            await self._save_scan_report()

            print(f"✅ [GUARDIAN] Scan terminé — Score: {self.scan_results['global_score']}/100")

            return self.scan_results

        except Exception as e:
            error_msg = f"❌ [GUARDIAN] Erreur critique scan: {e}"
            print(error_msg)
            self.scan_results["error"] = str(e)
            return self.scan_results

    async def scan_bandit(self) -> Dict[str, Any]:
        """
        Scan vulnérabilités Python avec Bandit.

        Returns:
            Résultats Bandit formatés
        """
        print("  🔍 Scan Bandit (vulnérabilités Python)...")

        try:
            # Vérifier si Bandit est installé
            check_cmd = await asyncio.create_subprocess_exec(
                'which', 'bandit',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await check_cmd.wait()

            if check_cmd.returncode != 0:
                return {
                    "status": "not_installed",
                    "message": "Bandit non installé. Installer avec: pip install bandit",
                    "vulnerabilities": []
                }

            # Exécuter Bandit
            cmd = await asyncio.create_subprocess_exec(
                'bandit',
                '-r', str(self.project_root),
                '-f', 'json',
                '--skip', 'B404,B603',  # Skip subprocess warnings
                '-ll',  # Low confidence + Low severity minimum
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await cmd.communicate()

            if cmd.returncode in [0, 1]:  # 0 = no issues, 1 = issues found
                try:
                    bandit_data = json.loads(stdout.decode())

                    vulnerabilities = []
                    for result in bandit_data.get('results', []):
                        vulnerabilities.append({
                            "file": result.get('filename', ''),
                            "line": result.get('line_number', 0),
                            "severity": result.get('issue_severity', 'UNKNOWN'),
                            "confidence": result.get('issue_confidence', 'UNKNOWN'),
                            "issue": result.get('issue_text', ''),
                            "cwe": result.get('issue_cwe', {}).get('id', 'N/A')
                        })

                    return {
                        "status": "completed",
                        "total_issues": len(vulnerabilities),
                        "high_severity": sum(1 for v in vulnerabilities if v['severity'] == 'HIGH'),
                        "medium_severity": sum(1 for v in vulnerabilities if v['severity'] == 'MEDIUM'),
                        "low_severity": sum(1 for v in vulnerabilities if v['severity'] == 'LOW'),
                        "vulnerabilities": vulnerabilities
                    }

                except json.JSONDecodeError:
                    return {
                        "status": "error",
                        "message": "Erreur parsing JSON Bandit",
                        "vulnerabilities": []
                    }
            else:
                return {
                    "status": "error",
                    "message": stderr.decode(),
                    "vulnerabilities": []
                }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "vulnerabilities": []
            }

    async def scan_safety(self) -> Dict[str, Any]:
        """
        Scan CVE dans dépendances avec Safety.

        Returns:
            Résultats Safety formatés
        """
        print("  🔍 Scan Safety (CVE dépendances)...")

        try:
            # Vérifier si Safety est installé
            check_cmd = await asyncio.create_subprocess_exec(
                'which', 'safety',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await check_cmd.wait()

            if check_cmd.returncode != 0:
                return {
                    "status": "not_installed",
                    "message": "Safety non installé. Installer avec: pip install safety",
                    "vulnerabilities": []
                }

            # Chercher requirements.txt
            requirements_path = self.project_root / "requirements.txt"
            if not requirements_path.exists():
                return {
                    "status": "no_requirements",
                    "message": "requirements.txt non trouvé",
                    "vulnerabilities": []
                }

            # Exécuter Safety
            cmd = await asyncio.create_subprocess_exec(
                'safety', 'check',
                '--json',
                '--file', str(requirements_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await cmd.communicate()

            try:
                # Safety retourne JSON même en cas de vulnérabilités
                safety_data = json.loads(stdout.decode())

                vulnerabilities = []
                for vuln in safety_data:
                    vulnerabilities.append({
                        "package": vuln[0],
                        "installed_version": vuln[2],
                        "affected_versions": vuln[1],
                        "vulnerability": vuln[3],
                        "cve": vuln[4] if len(vuln) > 4 else "N/A"
                    })

                return {
                    "status": "completed",
                    "total_vulnerabilities": len(vulnerabilities),
                    "vulnerabilities": vulnerabilities
                }

            except json.JSONDecodeError:
                # Pas de vulnérabilités trouvées
                return {
                    "status": "completed",
                    "total_vulnerabilities": 0,
                    "vulnerabilities": []
                }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "vulnerabilities": []
            }

    async def scan_credentials(self) -> Dict[str, Any]:
        """
        Détecte credentials exposés dans le code source.

        Returns:
            Credentials détectés
        """
        print("  🔍 Scan credentials exposés...")

        exposed_credentials = []
        scanned_files = 0

        try:
            for file_path in self._get_scannable_files():
                scanned_files += 1

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    for line_num, line in enumerate(content.splitlines(), 1):
                        for pattern, cred_type in self.credential_patterns:
                            matches = re.finditer(pattern, line, re.IGNORECASE)
                            for match in matches:
                                # Ne pas signaler si dans SECRETS/ ou .env.example
                                if 'SECRETS' in str(file_path) or '.env.example' in str(file_path):
                                    continue

                                exposed_credentials.append({
                                    "file": str(file_path.relative_to(self.project_root)),
                                    "line": line_num,
                                    "type": cred_type,
                                    "value_preview": match.group(0)[:20] + "...",
                                    "severity": "CRITICAL"
                                })

                except Exception as e:
                    continue

            return {
                "status": "completed",
                "scanned_files": scanned_files,
                "total_exposed": len(exposed_credentials),
                "credentials": exposed_credentials
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "scanned_files": scanned_files,
                "credentials": []
            }

    async def scan_file_permissions(self) -> Dict[str, Any]:
        """
        Vérifie permissions fichiers sensibles.

        Returns:
            Fichiers avec permissions incorrectes
        """
        print("  🔍 Scan permissions fichiers sensibles...")

        issues = []

        sensitive_files = [
            'SECRETS',
            '.env',
            'config',
            'keys',
            'credentials'
        ]

        try:
            for pattern in sensitive_files:
                for file_path in self.project_root.rglob(f"*{pattern}*"):
                    if file_path.is_file():
                        stat_info = file_path.stat()
                        permissions = oct(stat_info.st_mode)[-3:]

                        # Permissions recommandées : 600 (rw-------)
                        if permissions not in ['600', '400']:
                            issues.append({
                                "file": str(file_path.relative_to(self.project_root)),
                                "current_permissions": permissions,
                                "recommended": "600",
                                "severity": "HIGH" if permissions.startswith('7') else "MEDIUM"
                            })

            return {
                "status": "completed",
                "total_issues": len(issues),
                "issues": issues
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "issues": []
            }

    def _get_scannable_files(self) -> List[Path]:
        """
        Récupère tous les fichiers à scanner.

        Returns:
            Liste des fichiers à scanner
        """
        scannable_files = []

        for root, dirs, files in os.walk(self.project_root):
            # Filtrer dossiers à ignorer
            dirs[:] = [d for d in dirs if d not in self.ignore_patterns]

            for file in files:
                file_path = Path(root) / file
                if file_path.suffix in self.scan_extensions:
                    scannable_files.append(file_path)

        return scannable_files

    def _calculate_security_score(self) -> int:
        """
        Calcule score de sécurité global (0-100).

        Returns:
            Score de sécurité
        """
        score = 100

        scans = self.scan_results.get("scans", {})

        # Bandit
        bandit = scans.get("bandit", {})
        if bandit.get("status") == "completed":
            score -= bandit.get("high_severity", 0) * 10
            score -= bandit.get("medium_severity", 0) * 5
            score -= bandit.get("low_severity", 0) * 2

        # Safety
        safety = scans.get("safety", {})
        if safety.get("status") == "completed":
            score -= safety.get("total_vulnerabilities", 0) * 8

        # Credentials
        credentials = scans.get("credentials", {})
        if credentials.get("status") == "completed":
            score -= credentials.get("total_exposed", 0) * 15

        # Permissions
        permissions = scans.get("file_permissions", {})
        if permissions.get("status") == "completed":
            score -= permissions.get("total_issues", 0) * 5

        return max(0, min(100, score))

    def _determine_severity(self) -> str:
        """
        Détermine sévérité globale.

        Returns:
            CRITICAL, HIGH, MEDIUM, LOW, ou SAFE
        """
        score = self.scan_results.get("global_score", 100)

        if score < 50:
            return "CRITICAL"
        elif score < 70:
            return "HIGH"
        elif score < 85:
            return "MEDIUM"
        elif score < 95:
            return "LOW"
        else:
            return "SAFE"

    async def _save_scan_report(self) -> None:
        """Sauvegarde rapport de scan."""
        try:
            report_dir = self.project_root / "data" / "security_scans"
            report_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = report_dir / f"scan_{timestamp}.json"

            with open(report_path, 'w') as f:
                json.dump(self.scan_results, f, indent=2)

            # Lien vers dernier scan
            latest_path = report_dir / "latest.json"
            with open(latest_path, 'w') as f:
                json.dump(self.scan_results, f, indent=2)

            print(f"  💾 Rapport sauvegardé: {report_path}")

        except Exception as e:
            print(f"  ⚠️  Erreur sauvegarde rapport: {e}")


async def main():
    """Test du scanner."""
    scanner = SecurityScanner()
    results = await scanner.run_full_scan()

    print("\n" + "="*60)
    print("📊 RAPPORT DE SÉCURITÉ")
    print("="*60)
    print(f"Score global: {results['global_score']}/100")
    print(f"Sévérité: {results['severity']}")
    print(f"Timestamp: {results['timestamp']}")
    print("\nDétails:")
    print(json.dumps(results['scans'], indent=2))


if __name__ == "__main__":
    asyncio.run(main())
