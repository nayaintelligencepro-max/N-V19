"""
NAYA SUPREME V19 — Security Module 6/10
health_monitor.py — Monitoring santé système 24/7

Agent 11 — Guardian Agent
Rôle : Health checks, métriques, alertes
"""

import asyncio
import psutil
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json


class HealthMonitor:
    """
    Monitoring santé système 24/7.
    Vérifie tous les modules, métriques système, latences API.
    """

    def __init__(
        self,
        project_root: str = "/home/runner/work/V19/V19",
        check_interval_minutes: int = 15
    ):
        self.project_root = Path(project_root)
        self.check_interval_minutes = check_interval_minutes

        # État des composants
        self.component_status: Dict[str, Dict[str, Any]] = {}

        # Historique métriques
        self.metrics_history: List[Dict[str, Any]] = []

        # Seuils d'alerte
        self.thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_percent": 90.0,
            "api_latency_ms": 5000,
            "error_rate_percent": 5.0
        }

        # Fichiers monitoring
        self.monitoring_dir = self.project_root / "data" / "monitoring"
        self.monitoring_dir.mkdir(parents=True, exist_ok=True)

        # Composants à surveiller
        self.monitored_components = [
            "pain_hunter_agent",
            "researcher_agent",
            "offer_writer_agent",
            "outreach_agent",
            "closer_agent",
            "audit_agent",
            "content_agent",
            "contract_generator_agent",
            "revenue_tracker_agent",
            "parallel_pipeline_agent",
            "guardian_agent"
        ]

    async def run_health_check(self) -> Dict[str, Any]:
        """
        Exécute health check complet.

        Returns:
            Rapport de santé global
        """
        print(f"🏥 [HEALTH] Health check — {datetime.now().isoformat()}")

        health_report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "UNKNOWN",
            "system_metrics": {},
            "components": {},
            "alerts": [],
            "recommendations": []
        }

        try:
            # 1. Métriques système
            health_report["system_metrics"] = await self._check_system_metrics()

            # 2. État composants
            health_report["components"] = await self._check_components()

            # 3. Performance API (si disponible)
            health_report["api_performance"] = await self._check_api_performance()

            # 4. Database
            health_report["database"] = await self._check_database()

            # 5. Stockage
            health_report["storage"] = await self._check_storage()

            # 6. Déterminer status global
            health_report["overall_status"] = self._determine_overall_status(health_report)

            # 7. Générer alertes
            health_report["alerts"] = self._generate_alerts(health_report)

            # 8. Recommandations
            health_report["recommendations"] = self._generate_recommendations(health_report)

            # 9. Sauvegarder rapport
            await self._save_health_report(health_report)

            # 10. Historique métriques
            self._update_metrics_history(health_report)

            print(f"✅ [HEALTH] Status: {health_report['overall_status']}")

            return health_report

        except Exception as e:
            health_report["error"] = str(e)
            health_report["overall_status"] = "ERROR"
            return health_report

    async def _check_system_metrics(self) -> Dict[str, Any]:
        """
        Vérifie métriques système.

        Returns:
            Métriques CPU, RAM, disque
        """
        metrics = {
            "cpu": {
                "percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count(),
                "per_cpu": psutil.cpu_percent(interval=1, percpu=True)
            },
            "memory": {
                "total_gb": psutil.virtual_memory().total / (1024**3),
                "available_gb": psutil.virtual_memory().available / (1024**3),
                "percent": psutil.virtual_memory().percent,
                "used_gb": psutil.virtual_memory().used / (1024**3)
            },
            "disk": {
                "total_gb": psutil.disk_usage('/').total / (1024**3),
                "used_gb": psutil.disk_usage('/').used / (1024**3),
                "free_gb": psutil.disk_usage('/').free / (1024**3),
                "percent": psutil.disk_usage('/').percent
            },
            "network": {
                "bytes_sent": psutil.net_io_counters().bytes_sent,
                "bytes_recv": psutil.net_io_counters().bytes_recv
            }
        }

        return metrics

    async def _check_components(self) -> Dict[str, Dict[str, Any]]:
        """
        Vérifie état de chaque composant.

        Returns:
            État des composants
        """
        components = {}

        for component_name in self.monitored_components:
            status = {
                "name": component_name,
                "status": "UNKNOWN",
                "last_check": datetime.now().isoformat(),
                "errors": []
            }

            try:
                # Vérifier si module existe
                module_path = self.project_root / "agents" / f"{component_name}.py"

                if module_path.exists():
                    status["status"] = "EXISTS"

                    # Vérifier dernière activité (si logs disponibles)
                    last_activity = await self._check_component_activity(component_name)
                    if last_activity:
                        status["last_activity"] = last_activity
                        status["status"] = "ACTIVE"
                else:
                    status["status"] = "MISSING"
                    status["errors"].append(f"Module {component_name}.py non trouvé")

            except Exception as e:
                status["status"] = "ERROR"
                status["errors"].append(str(e))

            components[component_name] = status

        return components

    async def _check_component_activity(self, component_name: str) -> Optional[str]:
        """
        Vérifie dernière activité d'un composant.

        Args:
            component_name: Nom du composant

        Returns:
            Timestamp dernière activité ou None
        """
        try:
            # Chercher dans logs (simplifié)
            log_dir = self.project_root / "data" / "logs"
            if log_dir.exists():
                component_log = log_dir / f"{component_name}.log"
                if component_log.exists():
                    stat = component_log.stat()
                    return datetime.fromtimestamp(stat.st_mtime).isoformat()

            return None

        except Exception:
            return None

    async def _check_api_performance(self) -> Dict[str, Any]:
        """
        Vérifie performance des API externes.

        Returns:
            Latences et disponibilité API
        """
        api_performance = {}

        # APIs critiques à tester
        apis_to_test = {
            "groq": "https://api.groq.com",
            "anthropic": "https://api.anthropic.com",
            "serper": "https://google.serper.dev"
        }

        for api_name, api_url in apis_to_test.items():
            try:
                start_time = time.time()

                # Simple ping (à améliorer avec vraie requête)
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        latency_ms = (time.time() - start_time) * 1000

                        api_performance[api_name] = {
                            "status": "UP" if response.status < 500 else "DOWN",
                            "latency_ms": round(latency_ms, 2),
                            "status_code": response.status
                        }

            except asyncio.TimeoutError:
                api_performance[api_name] = {
                    "status": "TIMEOUT",
                    "latency_ms": 5000,
                    "error": "Timeout"
                }
            except Exception as e:
                api_performance[api_name] = {
                    "status": "ERROR",
                    "error": str(e)
                }

        return api_performance

    async def _check_database(self) -> Dict[str, Any]:
        """
        Vérifie santé de la database.

        Returns:
            État database
        """
        db_status = {
            "status": "UNKNOWN",
            "size_mb": 0,
            "tables": 0
        }

        try:
            db_path = self.project_root / "data" / "naya.db"

            if db_path.exists():
                db_status["status"] = "EXISTS"
                db_status["size_mb"] = db_path.stat().st_size / (1024 * 1024)

                # Compter tables (simplifié)
                try:
                    import sqlite3
                    conn = sqlite3.connect(str(db_path))
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    db_status["tables"] = len(tables)
                    db_status["table_names"] = [t[0] for t in tables]
                    conn.close()
                    db_status["status"] = "HEALTHY"
                except Exception as e:
                    db_status["status"] = "ERROR"
                    db_status["error"] = str(e)
            else:
                db_status["status"] = "NOT_FOUND"

        except Exception as e:
            db_status["status"] = "ERROR"
            db_status["error"] = str(e)

        return db_status

    async def _check_storage(self) -> Dict[str, Any]:
        """
        Vérifie espace de stockage du projet.

        Returns:
            État stockage
        """
        storage = {
            "total_mb": 0,
            "directories": {}
        }

        try:
            # Taille dossiers principaux
            important_dirs = [
                "data",
                "SECRETS",
                "agents",
                "workflows",
                "memory"
            ]

            for dir_name in important_dirs:
                dir_path = self.project_root / dir_name
                if dir_path.exists():
                    size = sum(
                        f.stat().st_size
                        for f in dir_path.rglob('*')
                        if f.is_file()
                    )
                    storage["directories"][dir_name] = {
                        "size_mb": size / (1024 * 1024),
                        "files": len(list(dir_path.rglob('*')))
                    }
                    storage["total_mb"] += size / (1024 * 1024)

        except Exception as e:
            storage["error"] = str(e)

        return storage

    def _determine_overall_status(self, health_report: Dict[str, Any]) -> str:
        """
        Détermine status global du système.

        Args:
            health_report: Rapport de santé

        Returns:
            HEALTHY, DEGRADED, CRITICAL, ou ERROR
        """
        try:
            # Vérifier métriques système
            system = health_report.get("system_metrics", {})

            if system.get("cpu", {}).get("percent", 0) > self.thresholds["cpu_percent"]:
                return "DEGRADED"

            if system.get("memory", {}).get("percent", 0) > self.thresholds["memory_percent"]:
                return "DEGRADED"

            if system.get("disk", {}).get("percent", 0) > self.thresholds["disk_percent"]:
                return "CRITICAL"

            # Vérifier composants
            components = health_report.get("components", {})
            missing = sum(1 for c in components.values() if c["status"] == "MISSING")
            errors = sum(1 for c in components.values() if c["status"] == "ERROR")

            if missing > 3 or errors > 3:
                return "CRITICAL"
            elif missing > 0 or errors > 0:
                return "DEGRADED"

            return "HEALTHY"

        except Exception:
            return "ERROR"

    def _generate_alerts(self, health_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Génère alertes basées sur rapport de santé.

        Args:
            health_report: Rapport de santé

        Returns:
            Liste des alertes
        """
        alerts = []

        try:
            system = health_report.get("system_metrics", {})

            # CPU
            cpu_percent = system.get("cpu", {}).get("percent", 0)
            if cpu_percent > self.thresholds["cpu_percent"]:
                alerts.append({
                    "type": "high_cpu",
                    "severity": "HIGH" if cpu_percent > 90 else "MEDIUM",
                    "message": f"CPU élevé: {cpu_percent}%",
                    "threshold": self.thresholds["cpu_percent"]
                })

            # Memory
            mem_percent = system.get("memory", {}).get("percent", 0)
            if mem_percent > self.thresholds["memory_percent"]:
                alerts.append({
                    "type": "high_memory",
                    "severity": "HIGH" if mem_percent > 95 else "MEDIUM",
                    "message": f"Mémoire élevée: {mem_percent}%",
                    "threshold": self.thresholds["memory_percent"]
                })

            # Disk
            disk_percent = system.get("disk", {}).get("percent", 0)
            if disk_percent > self.thresholds["disk_percent"]:
                alerts.append({
                    "type": "low_disk_space",
                    "severity": "CRITICAL" if disk_percent > 95 else "HIGH",
                    "message": f"Espace disque faible: {disk_percent}%",
                    "threshold": self.thresholds["disk_percent"]
                })

            # Composants manquants
            components = health_report.get("components", {})
            for name, status in components.items():
                if status["status"] in ["MISSING", "ERROR"]:
                    alerts.append({
                        "type": "component_issue",
                        "severity": "HIGH",
                        "message": f"Composant {name}: {status['status']}",
                        "component": name
                    })

        except Exception as e:
            alerts.append({
                "type": "monitoring_error",
                "severity": "MEDIUM",
                "message": f"Erreur génération alertes: {e}"
            })

        return alerts

    def _generate_recommendations(self, health_report: Dict[str, Any]) -> List[str]:
        """Génère recommandations d'optimisation."""
        recommendations = []

        try:
            system = health_report.get("system_metrics", {})

            if system.get("cpu", {}).get("percent", 0) > 70:
                recommendations.append("Optimiser processus gourmands en CPU")

            if system.get("memory", {}).get("percent", 0) > 80:
                recommendations.append("Nettoyer cache mémoire ou augmenter RAM")

            if system.get("disk", {}).get("percent", 0) > 85:
                recommendations.append("Archiver anciens logs et données")

            if not recommendations:
                recommendations.append("Système sain — aucune action requise")

        except Exception:
            recommendations.append("Erreur analyse — vérifier logs")

        return recommendations

    async def _save_health_report(self, report: Dict[str, Any]) -> None:
        """Sauvegarde rapport de santé."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = self.monitoring_dir / f"health_{timestamp}.json"

            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)

            # Dernier rapport
            latest_path = self.monitoring_dir / "health_latest.json"
            with open(latest_path, 'w') as f:
                json.dump(report, f, indent=2)

        except Exception as e:
            print(f"❌ [HEALTH] Erreur sauvegarde: {e}")

    def _update_metrics_history(self, report: Dict[str, Any]) -> None:
        """Met à jour historique métriques."""
        self.metrics_history.append({
            "timestamp": report["timestamp"],
            "cpu_percent": report["system_metrics"]["cpu"]["percent"],
            "memory_percent": report["system_metrics"]["memory"]["percent"],
            "disk_percent": report["system_metrics"]["disk"]["percent"]
        })

        # Garder 24h d'historique
        if len(self.metrics_history) > 96:  # 24h avec checks toutes les 15min
            self.metrics_history = self.metrics_history[-96:]

    def get_metrics_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Récupère historique métriques."""
        cutoff = datetime.now() - timedelta(hours=hours)

        return [
            m for m in self.metrics_history
            if datetime.fromisoformat(m["timestamp"]) > cutoff
        ]


async def main():
    """Test du health monitor."""
    monitor = HealthMonitor()

    print("\n" + "="*60)
    print("🏥 NAYA HEALTH MONITOR")
    print("="*60)

    report = await monitor.run_health_check()

    print(f"\nStatus global: {report['overall_status']}")
    print(f"CPU: {report['system_metrics']['cpu']['percent']}%")
    print(f"Memory: {report['system_metrics']['memory']['percent']}%")
    print(f"Disk: {report['system_metrics']['disk']['percent']}%")
    print(f"\nAlertes: {len(report['alerts'])}")
    for alert in report['alerts']:
        print(f"  - [{alert['severity']}] {alert['message']}")


if __name__ == "__main__":
    asyncio.run(main())
