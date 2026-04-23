"""
NAYA SUPREME V19 — Security Module 5/10
threat_detector.py — Détection de menaces et comportements suspects

Agent 11 — Guardian Agent
Rôle : Détection patterns d'attaque, brute force, exfiltration
"""

import asyncio
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict
import json


class ThreatDetector:
    """
    Détecteur de menaces en temps réel.
    Analyse patterns d'accès, tentatives brute force, comportements suspects.
    """

    def __init__(
        self,
        project_root: str = "/home/runner/work/V19/V19",
        max_requests_per_minute: int = 10,
        block_duration_minutes: int = 60
    ):
        self.project_root = Path(project_root)
        self.max_requests_per_minute = max_requests_per_minute
        self.block_duration_minutes = block_duration_minutes

        # Tracking des requêtes par IP
        self.request_history: Dict[str, List[datetime]] = defaultdict(list)

        # IPs bloquées
        self.blocked_ips: Dict[str, datetime] = {}

        # Patterns suspects
        self.suspicious_patterns = self._load_attack_patterns()

        # Alertes actives
        self.active_alerts: List[Dict[str, Any]] = []

        # Fichiers de tracking
        self.threat_log_dir = self.project_root / "data" / "threats"
        self.threat_log_dir.mkdir(parents=True, exist_ok=True)

    def _load_attack_patterns(self) -> Dict[str, List[str]]:
        """
        Charge patterns d'attaque connus.

        Returns:
            Dict des patterns par type d'attaque
        """
        return {
            "sql_injection": [
                r"(\bunion\b.*\bselect\b)",
                r"(;.*drop\s+table)",
                r"(\bor\b\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+)",
                r"(--\s*$)",
                r"(/\*.*\*/)",
            ],
            "xss": [
                r"(<script[^>]*>)",
                r"(javascript:)",
                r"(onerror\s*=)",
                r"(onload\s*=)",
                r"(<iframe[^>]*>)",
            ],
            "path_traversal": [
                r"(\.\.\/)",
                r"(\.\.\\)",
                r"(%2e%2e%2f)",
                r"(%252e%252e%252f)",
            ],
            "command_injection": [
                r"(;\s*cat\s+\/etc\/passwd)",
                r"(;\s*ls\s+-la)",
                r"(\|\s*nc\s+)",
                r"(&&\s*whoami)",
            ],
            "brute_force": [
                r"(admin|root|test|user|password)",
                r"(\d{6,})",  # Multiple passwords attempts
            ],
            "data_exfiltration": [
                r"(base64.*decode)",
                r"(curl.*http)",
                r"(wget.*http)",
                r"(nc\s+-l)",
            ]
        }

    async def analyze_request(
        self,
        ip_address: str,
        endpoint: str,
        payload: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Analyse une requête pour détecter menaces.

        Args:
            ip_address: IP source
            endpoint: Endpoint appelé
            payload: Payload de la requête
            headers: Headers HTTP

        Returns:
            Résultat d'analyse avec niveau de menace
        """
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "ip_address": ip_address,
            "endpoint": endpoint,
            "threat_level": "SAFE",
            "threats_detected": [],
            "blocked": False
        }

        # 1. Vérifier si IP est déjà bloquée
        if self._is_blocked(ip_address):
            analysis["blocked"] = True
            analysis["threat_level"] = "BLOCKED"
            analysis["threats_detected"].append({
                "type": "blocked_ip",
                "severity": "HIGH",
                "message": "IP précédemment bloquée"
            })
            return analysis

        # 2. Vérifier rate limiting
        rate_limit_check = await self._check_rate_limit(ip_address)
        if rate_limit_check["exceeded"]:
            analysis["threats_detected"].append({
                "type": "rate_limit_exceeded",
                "severity": "MEDIUM",
                "message": f"Limite dépassée: {rate_limit_check['count']} req/min",
                "details": rate_limit_check
            })

            # Bloquer si trop de requêtes
            if rate_limit_check["count"] > self.max_requests_per_minute * 2:
                await self._block_ip(ip_address, reason="rate_limit_abuse")
                analysis["blocked"] = True
                analysis["threat_level"] = "HIGH"

        # 3. Analyser payload pour patterns d'attaque
        if payload:
            payload_threats = self._scan_payload(payload)
            if payload_threats:
                analysis["threats_detected"].extend(payload_threats)
                analysis["threat_level"] = "HIGH"

                # Bloquer si injection détectée
                critical_attacks = ["sql_injection", "command_injection"]
                if any(t["type"] in critical_attacks for t in payload_threats):
                    await self._block_ip(ip_address, reason="injection_attempt")
                    analysis["blocked"] = True

        # 4. Analyser headers suspects
        if headers:
            header_threats = self._scan_headers(headers)
            if header_threats:
                analysis["threats_detected"].extend(header_threats)
                if analysis["threat_level"] == "SAFE":
                    analysis["threat_level"] = "MEDIUM"

        # 5. Enregistrer événement si menace détectée
        if analysis["threats_detected"]:
            await self._log_threat(analysis)

        return analysis

    async def _check_rate_limit(self, ip_address: str) -> Dict[str, Any]:
        """
        Vérifie rate limiting pour une IP.

        Args:
            ip_address: IP à vérifier

        Returns:
            Résultat du check
        """
        now = datetime.now()
        cutoff = now - timedelta(minutes=1)

        # Nettoyer ancien historique
        self.request_history[ip_address] = [
            ts for ts in self.request_history[ip_address]
            if ts > cutoff
        ]

        # Ajouter requête actuelle
        self.request_history[ip_address].append(now)

        count = len(self.request_history[ip_address])

        return {
            "ip": ip_address,
            "count": count,
            "limit": self.max_requests_per_minute,
            "exceeded": count > self.max_requests_per_minute,
            "window": "1 minute"
        }

    def _scan_payload(self, payload: str) -> List[Dict[str, Any]]:
        """
        Scanne payload pour patterns d'attaque.

        Args:
            payload: Contenu à scanner

        Returns:
            Liste des menaces détectées
        """
        threats = []

        for attack_type, patterns in self.suspicious_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, payload, re.IGNORECASE)
                for match in matches:
                    threats.append({
                        "type": attack_type,
                        "severity": self._get_attack_severity(attack_type),
                        "pattern": pattern,
                        "matched": match.group(0),
                        "position": match.start()
                    })

        return threats

    def _scan_headers(self, headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Scanne headers HTTP suspects.

        Args:
            headers: Headers à analyser

        Returns:
            Liste des menaces détectées
        """
        threats = []

        suspicious_user_agents = [
            "sqlmap", "nikto", "nmap", "masscan", "metasploit",
            "burpsuite", "acunetix", "nessus", "w3af"
        ]

        user_agent = headers.get("User-Agent", "").lower()
        for tool in suspicious_user_agents:
            if tool in user_agent:
                threats.append({
                    "type": "suspicious_user_agent",
                    "severity": "MEDIUM",
                    "tool": tool,
                    "message": f"Scanner détecté: {tool}"
                })

        # Vérifier headers suspects
        if "X-Forwarded-For" in headers and "," in headers["X-Forwarded-For"]:
            threats.append({
                "type": "proxy_chain",
                "severity": "LOW",
                "message": "Chaîne de proxies détectée"
            })

        return threats

    def _get_attack_severity(self, attack_type: str) -> str:
        """Détermine sévérité d'un type d'attaque."""
        critical = {"sql_injection", "command_injection"}
        high = {"xss", "path_traversal", "data_exfiltration"}

        if attack_type in critical:
            return "CRITICAL"
        elif attack_type in high:
            return "HIGH"
        else:
            return "MEDIUM"

    def _is_blocked(self, ip_address: str) -> bool:
        """Vérifie si une IP est bloquée."""
        if ip_address not in self.blocked_ips:
            return False

        # Vérifier si le blocage a expiré
        block_time = self.blocked_ips[ip_address]
        expiry = block_time + timedelta(minutes=self.block_duration_minutes)

        if datetime.now() > expiry:
            # Débloquer
            del self.blocked_ips[ip_address]
            return False

        return True

    async def _block_ip(self, ip_address: str, reason: str) -> None:
        """
        Bloque une IP.

        Args:
            ip_address: IP à bloquer
            reason: Raison du blocage
        """
        self.blocked_ips[ip_address] = datetime.now()

        alert = {
            "timestamp": datetime.now().isoformat(),
            "type": "ip_blocked",
            "ip_address": ip_address,
            "reason": reason,
            "duration_minutes": self.block_duration_minutes
        }

        self.active_alerts.append(alert)

        print(f"🚫 [THREAT] IP bloquée: {ip_address} — Raison: {reason}")

        # Sauvegarder
        await self._save_blocked_ips()

    async def _log_threat(self, analysis: Dict[str, Any]) -> None:
        """
        Enregistre une menace détectée.

        Args:
            analysis: Analyse de menace
        """
        try:
            today = datetime.now().strftime("%Y%m%d")
            threat_file = self.threat_log_dir / f"threats_{today}.jsonl"

            with open(threat_file, 'a') as f:
                f.write(json.dumps(analysis) + '\n')

        except Exception as e:
            print(f"❌ [THREAT] Erreur log menace: {e}")

    async def _save_blocked_ips(self) -> None:
        """Sauvegarde liste IPs bloquées."""
        try:
            blocked_file = self.threat_log_dir / "blocked_ips.json"

            blocked_data = {
                ip: block_time.isoformat()
                for ip, block_time in self.blocked_ips.items()
            }

            with open(blocked_file, 'w') as f:
                json.dump(blocked_data, f, indent=2)

        except Exception as e:
            print(f"❌ [THREAT] Erreur sauvegarde IPs bloquées: {e}")

    def get_blocked_ips(self) -> List[Dict[str, Any]]:
        """
        Liste des IPs bloquées.

        Returns:
            Liste des IPs bloquées avec détails
        """
        blocked = []

        for ip, block_time in self.blocked_ips.items():
            expiry = block_time + timedelta(minutes=self.block_duration_minutes)
            remaining = (expiry - datetime.now()).total_seconds() / 60

            blocked.append({
                "ip": ip,
                "blocked_at": block_time.isoformat(),
                "expires_at": expiry.isoformat(),
                "minutes_remaining": max(0, int(remaining))
            })

        return blocked

    def get_threat_stats(self) -> Dict[str, Any]:
        """
        Statistiques des menaces.

        Returns:
            Stats globales
        """
        stats = {
            "timestamp": datetime.now().isoformat(),
            "blocked_ips": len(self.blocked_ips),
            "active_alerts": len(self.active_alerts),
            "threats_by_type": defaultdict(int),
            "threats_by_severity": defaultdict(int),
            "top_attackers": []
        }

        # Analyser logs du jour
        today = datetime.now().strftime("%Y%m%d")
        threat_file = self.threat_log_dir / f"threats_{today}.jsonl"

        if threat_file.exists():
            ip_counts = defaultdict(int)

            with open(threat_file, 'r') as f:
                for line in f:
                    threat = json.loads(line)

                    # Par type
                    for detected in threat.get("threats_detected", []):
                        threat_type = detected.get("type", "unknown")
                        stats["threats_by_type"][threat_type] += 1

                        severity = detected.get("severity", "UNKNOWN")
                        stats["threats_by_severity"][severity] += 1

                    # Compter par IP
                    ip = threat.get("ip_address")
                    if ip:
                        ip_counts[ip] += 1

            # Top attackers
            stats["top_attackers"] = [
                {"ip": ip, "threat_count": count}
                for ip, count in sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            ]

        # Convertir defaultdict en dict normal
        stats["threats_by_type"] = dict(stats["threats_by_type"])
        stats["threats_by_severity"] = dict(stats["threats_by_severity"])

        return stats

    async def unblock_ip(self, ip_address: str) -> bool:
        """
        Débloque manuellement une IP.

        Args:
            ip_address: IP à débloquer

        Returns:
            True si succès
        """
        if ip_address in self.blocked_ips:
            del self.blocked_ips[ip_address]
            await self._save_blocked_ips()

            print(f"✅ [THREAT] IP débloquée: {ip_address}")
            return True

        return False

    def clear_expired_blocks(self) -> int:
        """
        Nettoie les blocages expirés.

        Returns:
            Nombre d'IPs débloquées
        """
        expired = []

        for ip_address in list(self.blocked_ips.keys()):
            if not self._is_blocked(ip_address):
                expired.append(ip_address)

        return len(expired)


async def main():
    """Test du threat detector."""
    detector = ThreatDetector(max_requests_per_minute=5)

    print("\n" + "="*60)
    print("🛡️ NAYA THREAT DETECTOR")
    print("="*60)

    # Test requête normale
    result1 = await detector.analyze_request("192.168.1.100", "/api/v1/prospects")
    print(f"\nRequête normale: {result1['threat_level']}")

    # Test SQL injection
    result2 = await detector.analyze_request(
        "10.0.0.50",
        "/api/v1/login",
        payload="username=admin' OR '1'='1"
    )
    print(f"SQL injection: {result2['threat_level']} — {len(result2['threats_detected'])} menaces")

    # Test rate limiting
    for i in range(15):
        await detector.analyze_request("192.168.1.200", "/api/v1/data")

    result3 = await detector.analyze_request("192.168.1.200", "/api/v1/data")
    print(f"\nRate limit: {result3['threat_level']} — Bloqué: {result3['blocked']}")

    # Stats
    stats = detector.get_threat_stats()
    print(f"\nStats:")
    print(f"  IPs bloquées: {stats['blocked_ips']}")
    print(f"  Alertes actives: {stats['active_alerts']}")
    print(f"  Menaces par type: {stats['threats_by_type']}")


if __name__ == "__main__":
    asyncio.run(main())
