"""
REAPERS — AutoScanner

Autoscan automatique du code source et des dépendances NAYA.
Capacités :
  1. Scan secrets/credentials hardcodés (regex — sans dépendance externe)
  2. Analyse statique Bandit si disponible (subprocess)
  3. Scan CVE dépendances Safety si disponible (subprocess)
  4. Rapport JSON + alertes Telegram optionnelles

Déclenchement :
  - Au boot via ReapersKernel.start()
  - Périodiquement via scheduler (toutes les 6h par défaut)
  - Manuel via /scan (Telegram)
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.REAPERS.AUTOSCAN")

# ---------------------------------------------------------------------------
# Secret patterns — covers common credential formats
# ---------------------------------------------------------------------------
SECRET_PATTERNS: List[Dict] = [
    {"name": "AWS Access Key",       "pattern": r"AKIA[0-9A-Z]{16}"},
    {"name": "AWS Secret Key",       "pattern": r"(?i)aws_secret[_\s]*=\s*['\"][0-9a-zA-Z/+=]{40}['\"]"},
    {"name": "Generic API Key",      "pattern": r"(?i)(api[_\-]?key|apikey)\s*=\s*['\"][A-Za-z0-9_\-]{20,}['\"]"},
    {"name": "SendGrid API Key",     "pattern": r"SG\.[A-Za-z0-9_\-]{22}\.[A-Za-z0-9_\-]{43}"},
    {"name": "Telegram Bot Token",   "pattern": r"\d{9,10}:[A-Za-z0-9_\-]{35}"},
    {"name": "Stripe Secret Key",    "pattern": r"sk_(live|test)_[A-Za-z0-9]{24,}"},
    {"name": "PayPal Client Secret", "pattern": r"(?i)paypal.*secret\s*=\s*['\"][A-Za-z0-9_\-]{20,}['\"]"},
    {"name": "Anthropic API Key",    "pattern": r"sk-ant-[A-Za-z0-9_\-]{40,}"},
    {"name": "OpenAI API Key",       "pattern": r"sk-[A-Za-z0-9]{48}"},
    {"name": "Groq API Key",         "pattern": r"gsk_[A-Za-z0-9]{50,}"},
    {"name": "Private Key Block",    "pattern": r"-----BEGIN\s+(RSA\s+)?PRIVATE KEY-----"},
    {"name": "Hardcoded password",   "pattern": r"(?i)password\s*=\s*['\"][^'\"]{6,}['\"]"},
    {"name": "Bearer Token",         "pattern": r"(?i)bearer\s+[A-Za-z0-9_\-\.]{40,}"},
    {"name": "Pinecone API Key",     "pattern": r"(?i)pinecone.*key\s*=\s*['\"][A-Za-z0-9_\-]{30,}['\"]"},
    {"name": "Apollo API Key",       "pattern": r"(?i)apollo.*key\s*=\s*['\"][A-Za-z0-9_\-]{30,}['\"]"},
]

# Directories to exclude from scan (vendor, cache, .git, etc.)
EXCLUDE_DIRS = {
    ".git", "__pycache__", ".venv", "venv", "env", "node_modules",
    ".pytest_cache", "dist", "build", "data", "SECRETS",
}

# File extensions to scan
INCLUDE_EXTENSIONS = {".py", ".env", ".yml", ".yaml", ".json", ".toml", ".sh", ".txt", ".cfg", ".ini"}

# Report output path
REPORT_PATH = Path("data/cache/reapers_scan_report.json")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class SecretFinding:
    file: str
    line: int
    pattern_name: str
    line_preview: str  # redacted excerpt


@dataclass
class ScanReport:
    scan_id: str
    started_at: float
    finished_at: float
    secrets_found: List[SecretFinding] = field(default_factory=list)
    bandit_issues: List[Dict] = field(default_factory=list)
    safety_issues: List[Dict] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def total_issues(self) -> int:
        return len(self.secrets_found) + len(self.bandit_issues) + len(self.safety_issues)

    @property
    def is_clean(self) -> bool:
        return self.total_issues == 0

    def to_dict(self) -> Dict:
        return {
            "scan_id": self.scan_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_s": round(self.finished_at - self.started_at, 2),
            "is_clean": self.is_clean,
            "total_issues": self.total_issues,
            "secrets_found": [
                {
                    "file": f.file, "line": f.line,
                    "pattern": f.pattern_name,
                    "preview": f.line_preview,
                }
                for f in self.secrets_found
            ],
            "bandit_issues": self.bandit_issues,
            "safety_issues": self.safety_issues,
            "errors": self.errors,
        }


# ---------------------------------------------------------------------------
# AutoScanner
# ---------------------------------------------------------------------------

class AutoScanner:
    """
    REAPERS AutoScanner — Autoscan code + dépendances.

    Usage::
        scanner = AutoScanner(root_path=".")
        report = scanner.run_full_scan()
        print(report.to_dict())
    """

    def __init__(self, root_path: str = "."):
        self._root = Path(root_path).resolve()
        self._compiled_patterns = [
            (p["name"], re.compile(p["pattern"]))
            for p in SECRET_PATTERNS
        ]
        self._scan_history: List[Dict] = []

    # ------------------------------------------------------------------
    # FULL SCAN
    # ------------------------------------------------------------------

    def run_full_scan(self) -> ScanReport:
        """Run all scans and return a consolidated report."""
        scan_id = f"SCAN_{int(time.time())}"
        started = time.time()
        log.info(f"[AUTOSCAN] Starting scan {scan_id}")

        report = ScanReport(scan_id=scan_id, started_at=started, finished_at=started)

        # 1 — Secrets scan
        try:
            secrets = self._scan_secrets()
            report.secrets_found = secrets
            if secrets:
                log.warning(f"[AUTOSCAN] {len(secrets)} potential secret(s) found")
        except Exception as e:
            report.errors.append(f"secrets_scan: {e}")

        # 2 — Bandit static analysis
        try:
            bandit_issues = self._run_bandit()
            report.bandit_issues = bandit_issues
            if bandit_issues:
                log.warning(f"[AUTOSCAN] Bandit: {len(bandit_issues)} issue(s)")
        except Exception as e:
            report.errors.append(f"bandit: {e}")

        # 3 — Safety dependency CVE scan
        try:
            safety_issues = self._run_safety()
            report.safety_issues = safety_issues
            if safety_issues:
                log.warning(f"[AUTOSCAN] Safety: {len(safety_issues)} CVE(s)")
        except Exception as e:
            report.errors.append(f"safety: {e}")

        report.finished_at = time.time()

        if report.is_clean:
            log.info(f"[AUTOSCAN] ✅ Clean — no issues found (scan_id={scan_id})")
        else:
            log.warning(
                f"[AUTOSCAN] ⚠️ {report.total_issues} issue(s) found "
                f"(secrets={len(report.secrets_found)}, "
                f"bandit={len(report.bandit_issues)}, "
                f"safety={len(report.safety_issues)})"
            )

        self._save_report(report)
        self._scan_history.append({"scan_id": scan_id, "ts": started, "issues": report.total_issues})
        if len(self._scan_history) > 100:
            self._scan_history = self._scan_history[-50:]

        return report

    # ------------------------------------------------------------------
    # 1 — SECRETS SCAN
    # ------------------------------------------------------------------

    def _scan_secrets(self) -> List[SecretFinding]:
        """Scan all text files for hardcoded secrets using regex patterns."""
        findings: List[SecretFinding] = []

        for file_path in self._iter_source_files():
            try:
                lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
            except Exception:
                continue

            rel_path = str(file_path.relative_to(self._root))

            for lineno, line in enumerate(lines, start=1):
                # Skip obvious comment-only lines that document env vars
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                # Skip .env.example — these are templates, not real secrets
                if ".env.example" in rel_path:
                    continue

                for pattern_name, compiled in self._compiled_patterns:
                    if compiled.search(line):
                        # Redact the line for the report
                        preview = (stripped[:80] + "…") if len(stripped) > 80 else stripped
                        preview = re.sub(r"['\"][^'\"]{8,}['\"]", "'***REDACTED***'", preview)
                        findings.append(SecretFinding(
                            file=rel_path,
                            line=lineno,
                            pattern_name=pattern_name,
                            line_preview=preview,
                        ))
                        break  # one finding per line max

        return findings

    def _iter_source_files(self):
        """Yield all source files to scan, excluding ignored dirs."""
        for path in self._root.rglob("*"):
            if not path.is_file():
                continue
            # Check excluded directories
            parts = set(path.relative_to(self._root).parts)
            if parts & EXCLUDE_DIRS:
                continue
            if path.suffix in INCLUDE_EXTENSIONS:
                yield path

    # ------------------------------------------------------------------
    # 2 — BANDIT STATIC ANALYSIS
    # ------------------------------------------------------------------

    def _run_bandit(self) -> List[Dict]:
        """Run Bandit static analysis on Python source. Returns list of issues."""
        try:
            result = subprocess.run(
                ["bandit", "-r", str(self._root), "-f", "json",
                 "--exclude", ",".join([str(self._root / d) for d in EXCLUDE_DIRS if (self._root / d).exists()]),
                 "-ll"],  # only medium+ severity
                capture_output=True, text=True, timeout=120
            )
            if result.stdout:
                data = json.loads(result.stdout)
                return data.get("results", [])
        except FileNotFoundError:
            log.debug("[AUTOSCAN] Bandit not installed — skipping static analysis")
        except subprocess.TimeoutExpired:
            log.warning("[AUTOSCAN] Bandit timed out")
        except json.JSONDecodeError:
            pass
        return []

    # ------------------------------------------------------------------
    # 3 — SAFETY DEPENDENCY SCAN
    # ------------------------------------------------------------------

    def _run_safety(self) -> List[Dict]:
        """Run Safety to check dependencies for known CVEs."""
        try:
            result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True, text=True, timeout=60,
                cwd=str(self._root)
            )
            output = result.stdout or result.stderr
            if output:
                try:
                    data = json.loads(output)
                    # Safety returns a list of vulnerability dicts
                    if isinstance(data, list):
                        return [
                            {
                                "package": v[0] if len(v) > 0 else "?",
                                "affected_versions": v[1] if len(v) > 1 else "?",
                                "installed_version": v[2] if len(v) > 2 else "?",
                                "description": v[3] if len(v) > 3 else "?",
                                "cve": v[4] if len(v) > 4 else "?",
                            }
                            for v in data
                        ]
                except json.JSONDecodeError:
                    pass
        except FileNotFoundError:
            log.debug("[AUTOSCAN] Safety not installed — skipping CVE scan")
        except subprocess.TimeoutExpired:
            log.warning("[AUTOSCAN] Safety timed out")
        return []

    # ------------------------------------------------------------------
    # REPORT PERSISTENCE
    # ------------------------------------------------------------------

    def _save_report(self, report: ScanReport) -> None:
        """Save scan report to disk."""
        try:
            REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
            REPORT_PATH.write_text(json.dumps(report.to_dict(), indent=2, default=str))
            log.debug(f"[AUTOSCAN] Report saved: {REPORT_PATH}")
        except Exception as e:
            log.warning(f"[AUTOSCAN] Could not save report: {e}")

    def get_last_report(self) -> Optional[Dict]:
        """Return the last saved report as dict."""
        try:
            if REPORT_PATH.exists():
                return json.loads(REPORT_PATH.read_text())
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------
    # STATS
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict:
        return {
            "total_scans": len(self._scan_history),
            "last_scan": self._scan_history[-1] if self._scan_history else None,
            "root": str(self._root),
        }

    def __repr__(self):
        return f"<AutoScanner root={self._root} scans={len(self._scan_history)}>"
