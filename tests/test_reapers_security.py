"""
Tests REAPERS — sécurité, autoscan, autoréparation, cybersécurité.

Couvre :
  - ThreatMemory (record / record_threat / backward compat)
  - RuntimeWatchdog (bool return, no false positives)
  - BootAuthority (authorize returns bool)
  - IntegrityGuard (wrapper vs alias)
  - SnapshotManager (create / list / restore)
  - IsolationEngine (quarantine / reintegrate)
  - ReapersRepair (full repair cycle)
  - AdaptiveSecurityLayer (threat evaluation, level control)
  - AntiCloneGuard (register / verify)
  - AntiExfiltrationGuard (validate / validate_dict / regex tightness)
  - AutoScanner (secrets scan, report structure, no false positives on legit code)
  - ReapersKernel (instantiation + component wiring)
  - security_engine (ReapersSecurityEngine renamed, EncryptionManager)
  - CrashPredictor (risk scoring)
  - SurvivalMode (activate / deactivate)
"""

import hashlib
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# THREAT MEMORY
# ---------------------------------------------------------------------------

class TestThreatMemory:
    def setup_method(self):
        from REAPERS.threat_memory import ThreatMemory
        self.tm = ThreatMemory()

    def test_record_threat_basic(self):
        t = self.tm.record_threat("brute_force", source="ip:1.2.3.4", severity=0.9)
        assert t["type"] == "brute_force"
        assert t["severity"] == 0.9

    def test_record_backward_compat_alias(self):
        """record() alias must work without extra args."""
        t = self.tm.record("integrity_breach")
        assert t["type"] == "integrity_breach"

    def test_record_alias_with_args(self):
        t = self.tm.record("scan", source="guardian", severity=0.3, details="test")
        assert t["source"] == "guardian"

    def test_is_known_threat(self):
        self.tm.record_threat("ransomware", source="x", severity=1.0)
        assert self.tm.is_known_threat("ransomware")
        assert not self.tm.is_known_threat("unknown_threat_xyz")

    def test_get_top_threats(self):
        # Record type_a more than type_b in this test
        for _ in range(5):
            self.tm.record_threat("type_unique_a", source="s", severity=0.5)
        for _ in range(2):
            self.tm.record_threat("type_unique_b", source="s", severity=0.5)
        top = self.tm.get_top_threats(10)
        names = [t["type"] for t in top]
        # type_unique_a must rank above type_unique_b
        assert names.index("type_unique_a") < names.index("type_unique_b")

    def test_anticipate_returns_list(self):
        for _ in range(4):
            self.tm.record_threat("persistent", source="s", severity=0.5)
        result = self.tm.anticipate()
        assert isinstance(result, list)
        assert any(r["threat"] == "persistent" for r in result)

    def test_get_stats(self):
        self.tm.record_threat("t", source="s", severity=0.1)
        stats = self.tm.get_stats()
        assert "total_threats" in stats
        assert stats["total_threats"] >= 1


# ---------------------------------------------------------------------------
# RUNTIME WATCHDOG
# ---------------------------------------------------------------------------

class TestRuntimeWatchdog:
    def setup_method(self):
        from REAPERS.runtime_watchdog import RuntimeWatchdog
        self.wdog = RuntimeWatchdog()

    def test_debugger_detected_returns_bool(self):
        result = self.wdog.debugger_detected()
        assert isinstance(result, bool)

    def test_suspicious_environment_returns_bool(self):
        result = self.wdog.suspicious_environment()
        assert isinstance(result, bool)

    def test_no_false_positive_in_clean_env(self):
        """In a clean test environment without debugger vars, should return False."""
        # Remove known debugger env vars for this test
        safe_env = {k: v for k, v in os.environ.items()
                    if k not in ("PYDEVD_USE_FRAME_EVAL", "PYCHARM_DEBUG", "VSCODE_DEBUGGER")}
        with patch.dict(os.environ, safe_env, clear=True):
            from REAPERS.runtime_watchdog import RuntimeWatchdog
            wdog = RuntimeWatchdog()
            # suspicious_environment checks LD_PRELOAD / FAKETIME — not set in CI
            assert wdog.suspicious_environment() is False

    def test_debugger_detected_with_pycharm_var(self):
        with patch.dict(os.environ, {"PYCHARM_DEBUG": "1"}):
            from REAPERS.runtime_watchdog import RuntimeWatchdog
            wdog = RuntimeWatchdog()
            assert wdog.debugger_detected() is True

    def test_get_stats_structure(self):
        self.wdog.debugger_detected()
        stats = self.wdog.get_stats()
        assert stats["operations"] >= 1
        assert "healthy" in stats


# ---------------------------------------------------------------------------
# BOOT AUTHORITY
# ---------------------------------------------------------------------------

class TestBootAuthority:
    def setup_method(self):
        from REAPERS.boot_authority import BootAuthority
        self.ba = BootAuthority()

    def test_authorize_returns_bool(self):
        result = self.ba.authorize()
        assert isinstance(result, bool)

    def test_authorize_returns_true(self):
        """Boot authority in silent recovery mode always allows."""
        assert self.ba.authorize() is True


# ---------------------------------------------------------------------------
# INTEGRITY GUARD
# ---------------------------------------------------------------------------

class TestIntegrityGuard:
    def test_wrapper_class_not_overwritten(self):
        """IntegrityGuard at module top should be the wrapper, NOT ReapersIntegrityGuard."""
        import REAPERS.integrity_guard as ig_module
        # The wrapper class defined at line ~11 should NOT have been replaced by the alias
        assert ig_module.IntegrityGuard is not ig_module.ReapersIntegrityGuard

    def test_create_baseline_and_check(self):
        from REAPERS.integrity_guard import IntegrityGuard
        ig = IntegrityGuard()
        ig.create_baseline()
        results = ig.check_integrity()
        assert isinstance(results, dict)
        # All monitored files that exist should show True (valid)
        for name, is_valid in results.items():
            assert isinstance(is_valid, bool)

    def test_wrapper_delegates_to_inner_guard(self):
        from REAPERS.integrity_guard import IntegrityGuard
        ig = IntegrityGuard({"test_key": "nonexistent_file.py"})
        results = ig.check_integrity()
        # nonexistent file won't be in baselines, so results may be empty
        assert isinstance(results, dict)


# ---------------------------------------------------------------------------
# SNAPSHOT MANAGER
# ---------------------------------------------------------------------------

class TestSnapshotManager:
    def test_create_and_list(self, tmp_path):
        from REAPERS.snapshot_manager import ReapersSnapshotManager
        sm = ReapersSnapshotManager.__new__(ReapersSnapshotManager)
        from pathlib import Path
        import REAPERS.snapshot_manager as sm_module
        original = sm_module.SNAPSHOT_DIR
        sm_module.SNAPSHOT_DIR = tmp_path / "snapshots"
        sm_module.SNAPSHOT_DIR.mkdir()
        sm._snapshots = []
        snap = sm.create_snapshot("test")
        assert "id" in snap
        assert len(sm.list_snapshots()) == 1
        sm_module.SNAPSHOT_DIR = original

    def test_alias_works(self):
        from REAPERS.snapshot_manager import SnapshotManager, ReapersSnapshotManager
        assert SnapshotManager is ReapersSnapshotManager


# ---------------------------------------------------------------------------
# ISOLATION ENGINE
# ---------------------------------------------------------------------------

class TestIsolationEngine:
    def setup_method(self):
        from REAPERS.isolation_engine import IsolationEngine
        self.ie = IsolationEngine()

    def test_quarantine_and_check(self):
        self.ie.quarantine("module_x")
        assert self.ie.is_quarantined("module_x")

    def test_reintegrate(self):
        self.ie.quarantine("module_y")
        self.ie.reintegrate("module_y")
        assert not self.ie.is_quarantined("module_y")

    def test_double_quarantine_safe(self):
        self.ie.quarantine("mod")
        self.ie.quarantine("mod")  # should not raise
        assert self.ie.is_quarantined("mod")

    def test_reset_all(self):
        self.ie.quarantine("a")
        self.ie.quarantine("b")
        self.ie.reset_all()
        assert not self.ie.is_quarantined("a")
        assert not self.ie.is_quarantined("b")


# ---------------------------------------------------------------------------
# REAPERS REPAIR
# ---------------------------------------------------------------------------

class TestReapersRepair:
    def setup_method(self):
        from REAPERS.reapers_repair import ReapersRepair
        from REAPERS.snapshot_manager import SnapshotManager
        from REAPERS.isolation_engine import IsolationEngine
        from REAPERS.threat_memory import ThreatMemory
        self.repair = ReapersRepair(
            snapshot_manager=SnapshotManager(),
            isolation_engine=IsolationEngine(),
            threat_memory=ThreatMemory(),
        )

    def test_restore_module_runs_without_error(self):
        """restore_module must not crash (snapshot may not exist but graceful)."""
        try:
            self.repair.restore_module("test_module", "nonexistent/path.py")
        except Exception as e:
            pytest.fail(f"restore_module raised: {e}")

    def test_repair_history_tracked(self):
        self.repair.restore_module("mod_a", "some/path.py")
        hist = self.repair.repair_history()
        assert "mod_a" in hist

    def test_threat_memory_called(self):
        """record_threat must be called during restore_module."""
        mock_tm = MagicMock()
        from REAPERS.reapers_repair import ReapersRepair
        from REAPERS.snapshot_manager import SnapshotManager
        from REAPERS.isolation_engine import IsolationEngine
        repair = ReapersRepair(
            snapshot_manager=SnapshotManager(),
            isolation_engine=IsolationEngine(),
            threat_memory=mock_tm,
        )
        repair.restore_module("test", "path.py")
        mock_tm.record_threat.assert_called_once()


# ---------------------------------------------------------------------------
# ADAPTIVE SECURITY LAYER
# ---------------------------------------------------------------------------

class TestAdaptiveSecurityLayer:
    def setup_method(self):
        from REAPERS.adaptive_security_layer import AdaptiveSecurityLayer
        self.asl = AdaptiveSecurityLayer()

    def test_default_level_is_normal(self):
        assert self.asl.get_level() == 1

    def test_set_level(self):
        self.asl.set_level(2)
        assert self.asl.get_level() == 2

    def test_level_clamped(self):
        self.asl.set_level(0)
        assert self.asl.get_level() == 1
        self.asl.set_level(99)
        assert self.asl.get_level() == 3

    def test_debugger_raises_to_critical(self):
        self.asl.evaluate_threat(integrity_breach=False, debugger_detected=True, repeated_failures=False)
        assert self.asl.get_level() == 3

    def test_integrity_breach_raises_to_critical(self):
        self.asl.evaluate_threat(integrity_breach=True, debugger_detected=False, repeated_failures=False)
        assert self.asl.get_level() == 3

    def test_repeated_failures_elevates(self):
        self.asl.evaluate_threat(integrity_breach=False, debugger_detected=False, repeated_failures=True)
        assert self.asl.get_level() == 2

    def test_clean_state_resets_to_normal(self):
        self.asl.set_level(3)
        self.asl.evaluate_threat(integrity_breach=False, debugger_detected=False, repeated_failures=False)
        assert self.asl.get_level() == 1

    def test_require_strict_monitoring(self):
        self.asl.set_level(2)
        assert self.asl.require_strict_monitoring()

    def test_require_runtime_restriction_only_at_3(self):
        self.asl.set_level(2)
        assert not self.asl.require_runtime_restriction()
        self.asl.set_level(3)
        assert self.asl.require_runtime_restriction()


# ---------------------------------------------------------------------------
# ANTI-CLONE GUARD
# ---------------------------------------------------------------------------

class TestAntiCloneGuard:
    def setup_method(self):
        from REAPERS.anti_clone_guard import AntiCloneGuard
        self.acg = AntiCloneGuard()

    def test_verify_legitimate_machine(self):
        result = self.acg.verify_not_clone()
        # Current machine is auto-registered in __init__
        assert result["legitimate"] is True

    def test_register_machine(self):
        mid = self.acg.register_machine("test_machine_abc")
        assert mid == "test_machine_abc"

    def test_get_stats(self):
        stats = self.acg.get_stats()
        assert "registered" in stats
        assert stats["registered"] >= 1


# ---------------------------------------------------------------------------
# ANTI-EXFILTRATION GUARD
# ---------------------------------------------------------------------------

class TestAntiExfiltrationGuard:
    def setup_method(self):
        from REAPERS.anti_exfiltration import AntiExfiltrationGuard
        self.guard = AntiExfiltrationGuard()

    def test_valid_payload_passes(self):
        assert self.guard.validate("This is a normal business message about IEC 62443 compliance.") is True

    def test_payload_with_secret_key_blocked(self):
        assert self.guard.validate("API_KEY = 'abcdef1234567890abcdef'") is False

    def test_private_key_blocked(self):
        assert self.guard.validate("-----BEGIN RSA PRIVATE KEY-----") is False

    def test_normal_long_string_not_blocked(self):
        """A normal sentence over 32 chars should NOT be blocked by the tightened regex."""
        payload = "Le module REAPERS surveille l'integrite du systeme NAYA en continu."
        assert self.guard.validate(payload) is True

    def test_uuid_not_blocked(self):
        """UUIDs must not be blocked — they are normal identifiers."""
        payload = "prospect_id: 550e8400-e29b-41d4-a716-446655440000"
        assert self.guard.validate(payload) is True

    def test_hash_in_text_not_blocked(self):
        """A SHA256 hash in a report sentence must not be blocked."""
        h = hashlib.sha256(b"test").hexdigest()
        payload = f"Integrity hash verified: {h}"
        assert self.guard.validate(payload) is True

    def test_oversized_payload_blocked(self):
        assert self.guard.validate("x" * 60000) is False

    def test_validate_dict_redacts_sensitive_keys(self):
        data = {"email": "user@example.com", "api_key": "supersecret123", "name": "ACME Corp"}
        result = self.guard.validate_dict(data)
        assert result["api_key"] == "***REDACTED***"
        assert result["email"] == "user@example.com"  # Not in sensitive_keys by default
        assert result["name"] == "ACME Corp"

    def test_whitelist_payload(self):
        payload = "API_KEY=known_safe_system_token"
        self.guard.whitelist_payload(payload)
        assert self.guard.validate(payload) is True

    def test_stats(self):
        self.guard.validate("-----BEGIN RSA PRIVATE KEY-----")
        stats = self.guard.stats
        assert stats["blocked_count"] >= 1


# ---------------------------------------------------------------------------
# AUTO SCANNER
# ---------------------------------------------------------------------------

class TestAutoScanner:
    def setup_method(self):
        from REAPERS.auto_scanner import AutoScanner
        self.scanner = AutoScanner(root_path=os.getcwd())

    def test_scan_report_structure(self, tmp_path):
        from REAPERS.auto_scanner import AutoScanner
        scanner = AutoScanner(root_path=str(tmp_path))
        # Create a clean Python file
        (tmp_path / "clean.py").write_text('def hello():\n    return "world"\n')
        report = scanner.run_full_scan()
        assert report.scan_id.startswith("SCAN_")
        assert report.finished_at >= report.started_at
        assert isinstance(report.secrets_found, list)
        assert isinstance(report.bandit_issues, list)
        assert isinstance(report.safety_issues, list)

    def test_no_secrets_in_clean_file(self, tmp_path):
        from REAPERS.auto_scanner import AutoScanner
        scanner = AutoScanner(root_path=str(tmp_path))
        (tmp_path / "safe.py").write_text('x = 1\nprint("hello naya")\n')
        report = scanner.run_full_scan()
        assert len(report.secrets_found) == 0

    def test_detects_hardcoded_api_key(self, tmp_path):
        from REAPERS.auto_scanner import AutoScanner
        scanner = AutoScanner(root_path=str(tmp_path))
        # Write a file with a clearly hardcoded secret
        (tmp_path / "bad.py").write_text("api_key = 'sk-abcdefghijklmnopqrstuvwxyz123456789012345678'\n")
        report = scanner.run_full_scan()
        assert len(report.secrets_found) >= 1

    def test_detects_private_key_block(self, tmp_path):
        from REAPERS.auto_scanner import AutoScanner
        scanner = AutoScanner(root_path=str(tmp_path))
        (tmp_path / "priv.txt").write_text("-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAK\n")
        report = scanner.run_full_scan()
        assert any(f.pattern_name == "Private Key Block" for f in report.secrets_found)

    def test_env_example_skipped(self, tmp_path):
        """Template files (.env.example) should not generate secret findings."""
        from REAPERS.auto_scanner import AutoScanner
        scanner = AutoScanner(root_path=str(tmp_path))
        (tmp_path / ".env.example").write_text("API_KEY=your_api_key_here\nPASSWORD=your_password\n")
        report = scanner.run_full_scan()
        assert len(report.secrets_found) == 0

    def test_to_dict_serializable(self, tmp_path):
        import json
        from REAPERS.auto_scanner import AutoScanner
        scanner = AutoScanner(root_path=str(tmp_path))
        report = scanner.run_full_scan()
        d = report.to_dict()
        assert json.dumps(d)  # must be JSON serializable

    def test_is_clean_property(self, tmp_path):
        from REAPERS.auto_scanner import AutoScanner
        scanner = AutoScanner(root_path=str(tmp_path))
        (tmp_path / "empty.py").write_text("")
        report = scanner.run_full_scan()
        assert report.is_clean is True

    def test_get_stats(self, tmp_path):
        from REAPERS.auto_scanner import AutoScanner
        scanner = AutoScanner(root_path=str(tmp_path))
        scanner.run_full_scan()
        stats = scanner.get_stats()
        assert stats["total_scans"] == 1


# ---------------------------------------------------------------------------
# REAPERS KERNEL — instantiation
# ---------------------------------------------------------------------------

class TestReapersKernel:
    def test_kernel_instantiation(self):
        from REAPERS.reapers_core import ReapersKernel
        k = ReapersKernel()
        assert k.integrity_guard is not None
        assert k.runtime_watchdog is not None
        assert k.adaptive_security is not None
        assert k.anti_clone_guard is not None
        assert k.anti_exfiltration is not None
        assert k.auto_scanner is not None
        assert k.repair_engine is not None

    def test_all_components_wired(self):
        from REAPERS.reapers_core import ReapersKernel
        k = ReapersKernel()
        attrs = [
            "snapshot_manager", "integrity_guard", "boot_authority",
            "crash_predictor", "runtime_watchdog", "isolation_engine",
            "adaptive_security", "anti_clone_guard", "anti_exfiltration",
            "auto_scanner", "repair_engine",
        ]
        for attr in attrs:
            assert hasattr(k, attr), f"Missing component: {attr}"


# ---------------------------------------------------------------------------
# SECURITY ENGINE
# ---------------------------------------------------------------------------

class TestReapersSecurityEngine:
    def test_class_name_is_correct(self):
        """Class must be ReapersSecurityEngine, not RapersSecurityEngine."""
        from REAPERS.security_engine import ReapersSecurityEngine
        assert ReapersSecurityEngine.__name__ == "ReapersSecurityEngine"

    def test_rapers_typo_not_in_module(self):
        import REAPERS.security_engine as se_module
        assert not hasattr(se_module, "RapersSecurityEngine"), "Typo class must be removed"

    def test_encryption_manager_encrypt(self):
        from REAPERS.security_engine import EncryptionManager
        em = EncryptionManager()
        result = em.encrypt("sensitive_data")
        assert isinstance(result, str)
        assert result != "sensitive_data"  # must not return plaintext

    def test_encryption_manager_decrypt_no_key(self):
        """Without ENCRYPTION_KEY, decrypt returns the masked value."""
        from REAPERS.security_engine import EncryptionManager
        em = EncryptionManager()
        encrypted = em.encrypt("test_data")
        result = em.decrypt(encrypted)
        assert isinstance(result, str)

    def test_security_engine_instantiates(self):
        from REAPERS.security_engine import ReapersSecurityEngine
        engine = ReapersSecurityEngine()
        assert engine is not None

    def test_verify_integrity(self):
        from REAPERS.security_engine import ReapersSecurityEngine
        engine = ReapersSecurityEngine()
        data = {"key": "value", "number": 42}
        h = engine.integrity_verifier.compute_hash(data)
        assert engine.verify_integrity(data, h) is True
        assert engine.verify_integrity(data, "wrong_hash") is False

    def test_detect_threat_brute_force(self):
        from REAPERS.security_engine import ReapersSecurityEngine
        engine = ReapersSecurityEngine()
        is_threat, t_type = engine.detect_threat({"failed_logins": 10})
        assert is_threat is True
        assert t_type == "BRUTE_FORCE_ATTACK"

    def test_audit_trail(self):
        from REAPERS.security_engine import ReapersSecurityEngine
        engine = ReapersSecurityEngine()
        engine.authenticate_user("user1", {"password": "pass"})
        trail = engine.get_audit_trail()
        assert len(trail) >= 1


# ---------------------------------------------------------------------------
# CRASH PREDICTOR
# ---------------------------------------------------------------------------

class TestCrashPredictor:
    def setup_method(self):
        from REAPERS.crash_predictor import CrashPredictor
        self.cp = CrashPredictor()

    def test_predict_clean(self):
        result = self.cp.predict()
        assert "risk_score" in result
        assert result["crash_imminent"] is False

    def test_predict_high_error_rate(self):
        for i in range(20):
            self.cp.record_metric("error_rate", 0.01 if i < 10 else 0.9)
        result = self.cp.predict()
        assert result["risk_score"] > 0

    def test_predict_high_latency(self):
        for _ in range(15):
            self.cp.record_metric("latency", 10.0)
        result = self.cp.predict()
        assert "high_latency" in result["factors"]

    def test_predict_memory_pressure(self):
        for _ in range(10):
            self.cp.record_metric("memory_usage", 0.9)
        result = self.cp.predict()
        assert "memory_pressure" in result["factors"]

    def test_prevented_crashes(self):
        self.cp.record_prevented()
        stats = self.cp.get_stats()
        assert stats["prevented_crashes"] == 1


# ---------------------------------------------------------------------------
# SURVIVAL MODE
# ---------------------------------------------------------------------------

class TestSurvivalMode:
    def setup_method(self):
        from REAPERS.survival_mode import SurvivalMode
        self.sm = SurvivalMode()

    def test_not_active_by_default(self):
        assert self.sm.is_active() is False

    def test_activate(self):
        self.sm.activate("test reason")
        assert self.sm.is_active() is True
        assert self.sm.activated_at() is not None

    def test_deactivate(self):
        self.sm.activate("x")
        self.sm.deactivate()
        assert self.sm.is_active() is False

    def test_double_activate_safe(self):
        self.sm.activate("first")
        ts1 = self.sm.activated_at()
        self.sm.activate("second")  # should be no-op
        assert self.sm.activated_at() == ts1

    def test_restrict_execution(self):
        assert self.sm.restrict_execution() is False
        self.sm.activate("critical")
        assert self.sm.restrict_execution() is True


# ---------------------------------------------------------------------------
# REAPERS __init__ EXPORTS
# ---------------------------------------------------------------------------

class TestReapersInitExports:
    """All key classes must be importable directly from REAPERS."""

    EXPECTED = [
        "ReapersKernel", "ReapersSentinel", "ReapersShield", "ReapersSecurity",
        "ReapersReport", "ReapersRepair", "IntegrityGuard", "ReapersIntegrityGuard",
        "ThreatMemory", "SnapshotManager", "IsolationEngine", "AdaptiveSecurityLayer",
        "AntiCloneGuard", "AntiExfiltrationGuard", "AutoScanner", "ScanReport",
        "RuntimeWatchdog", "CrashPredictor", "SurvivalMode", "BootAuthority",
        "ReapersSecurityEngine",
    ]

    def test_all_exports_present(self):
        import REAPERS
        for name in self.EXPECTED:
            assert hasattr(REAPERS, name), f"REAPERS.{name} not exported"

    def test_no_rapers_typo_in_exports(self):
        import REAPERS
        assert not hasattr(REAPERS, "RapersSecurityEngine")
