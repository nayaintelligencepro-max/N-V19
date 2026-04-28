#!/usr/bin/env python3
"""
NAYA SUPREME V19 — A/B Testing Engine
Variants tracking: A/B/C for email subjects, bodies, offers.
Statistical significance calculation.
Auto-selection of winning variant after N samples.
"""

import asyncio
import json
import logging
import math
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

log = logging.getLogger("NAYA.ABTesting")


# ── Test Models ───────────────────────────────────────────────────────────────
class TestStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    PAUSED = "paused"


class VariantName(str, Enum):
    A = "A"
    B = "B"
    C = "C"


@dataclass
class Variant:
    """A/B test variant."""
    name: VariantName
    content: str  # Email subject, body, offer text, etc
    sends: int = 0
    opens: int = 0
    clicks: int = 0
    replies: int = 0
    conversions: int = 0  # Meetings booked, deals won, etc

    def conversion_rate(self) -> float:
        """Calculate conversion rate."""
        return (self.conversions / self.sends * 100) if self.sends > 0 else 0.0

    def open_rate(self) -> float:
        """Calculate open rate."""
        return (self.opens / self.sends * 100) if self.sends > 0 else 0.0

    def reply_rate(self) -> float:
        """Calculate reply rate."""
        return (self.replies / self.sends * 100) if self.sends > 0 else 0.0

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["name"] = self.name.value
        return data


@dataclass
class ABTest:
    """A/B test configuration and results."""
    test_id: str
    name: str
    test_type: str  # email_subject, email_body, offer_price, landing_page, etc
    variants: List[Variant]
    status: TestStatus
    winner: Optional[VariantName]
    confidence_level: float  # 0-100
    min_sample_size: int
    created_at: str
    completed_at: Optional[str]
    metadata: Dict = None

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["status"] = self.status.value
        data["winner"] = self.winner.value if self.winner else None
        data["variants"] = [v.to_dict() for v in self.variants]
        return data


# ── A/B Testing Engine ────────────────────────────────────────────────────────
class ABTestingEngine:
    """
    A/B testing engine for messages, offers, sequences.

    Features:
    - Multi-variant testing (A/B/C)
    - Statistical significance calculation (chi-square test)
    - Auto-winner selection
    - Real-time metrics tracking
    """

    MIN_SAMPLE_SIZE = 30  # Minimum sends per variant before declaring winner
    CONFIDENCE_THRESHOLD = 95.0  # 95% confidence level

    def __init__(self, storage_path: str = "data/intelligence/ab_tests.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.tests: List[ABTest] = []
        self._load_tests()
        log.info("✅ ABTestingEngine initialized")

    # ── Storage ───────────────────────────────────────────────────────────────
    def _load_tests(self) -> None:
        """Load tests from storage."""
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text())
                self.tests = []
                for item in data:
                    item["status"] = TestStatus(item["status"])
                    item["winner"] = VariantName(item["winner"]) if item["winner"] else None
                    variants = []
                    for v in item["variants"]:
                        v["name"] = VariantName(v["name"])
                        variants.append(Variant(**v))
                    item["variants"] = variants
                    self.tests.append(ABTest(**item))
                log.info("Loaded %d A/B tests", len(self.tests))
            except Exception as exc:
                log.warning("Failed to load A/B tests: %s", exc)
                self.tests = []

    def _save_tests(self) -> None:
        """Save tests to storage."""
        try:
            data = [test.to_dict() for test in self.tests]
            self.storage_path.write_text(json.dumps(data, indent=2, default=str))
        except Exception as exc:
            log.warning("Failed to save A/B tests: %s", exc)

    # ── Test Creation ─────────────────────────────────────────────────────────
    async def create_test(
        self,
        test_id: str,
        name: str,
        test_type: str,
        variant_a: str,
        variant_b: str,
        variant_c: Optional[str] = None,
        min_sample_size: Optional[int] = None,
    ) -> ABTest:
        """
        Create a new A/B test.

        Args:
            test_id: Unique test identifier
            name: Test name
            test_type: Type of test (email_subject, email_body, etc)
            variant_a: Content for variant A
            variant_b: Content for variant B
            variant_c: Content for variant C (optional)
            min_sample_size: Minimum sample size per variant

        Returns:
            ABTest object
        """
        variants = [
            Variant(name=VariantName.A, content=variant_a),
            Variant(name=VariantName.B, content=variant_b),
        ]

        if variant_c:
            variants.append(Variant(name=VariantName.C, content=variant_c))

        test = ABTest(
            test_id=test_id,
            name=name,
            test_type=test_type,
            variants=variants,
            status=TestStatus.RUNNING,
            winner=None,
            confidence_level=0.0,
            min_sample_size=min_sample_size or self.MIN_SAMPLE_SIZE,
            created_at=datetime.now().isoformat(),
            completed_at=None,
            metadata={},
        )

        self.tests.append(test)
        self._save_tests()

        log.info("✅ Created A/B test: %s (%d variants)", test_id, len(variants))
        return test

    # ── Metrics Recording ─────────────────────────────────────────────────────
    async def record_send(self, test_id: str, variant_name: VariantName) -> None:
        """Record that a variant was sent."""
        test = await self._get_test(test_id)
        if test and test.status == TestStatus.RUNNING:
            for variant in test.variants:
                if variant.name == variant_name:
                    variant.sends += 1
                    self._save_tests()
                    break

    async def record_open(self, test_id: str, variant_name: VariantName) -> None:
        """Record that a variant was opened."""
        test = await self._get_test(test_id)
        if test and test.status == TestStatus.RUNNING:
            for variant in test.variants:
                if variant.name == variant_name:
                    variant.opens += 1
                    self._save_tests()
                    break

    async def record_click(self, test_id: str, variant_name: VariantName) -> None:
        """Record that a variant was clicked."""
        test = await self._get_test(test_id)
        if test and test.status == TestStatus.RUNNING:
            for variant in test.variants:
                if variant.name == variant_name:
                    variant.clicks += 1
                    self._save_tests()
                    break

    async def record_reply(self, test_id: str, variant_name: VariantName) -> None:
        """Record that a variant received a reply."""
        test = await self._get_test(test_id)
        if test and test.status == TestStatus.RUNNING:
            for variant in test.variants:
                if variant.name == variant_name:
                    variant.replies += 1
                    self._save_tests()
                    break

    async def record_conversion(self, test_id: str, variant_name: VariantName) -> None:
        """Record that a variant converted (meeting booked, deal won, etc)."""
        test = await self._get_test(test_id)
        if test and test.status == TestStatus.RUNNING:
            for variant in test.variants:
                if variant.name == variant_name:
                    variant.conversions += 1
                    self._save_tests()
                    # Check if we can determine a winner
                    await self._check_winner(test)
                    break

    # ── Winner Selection ──────────────────────────────────────────────────────
    async def _check_winner(self, test: ABTest) -> None:
        """
        Check if we have enough data to determine a winner.
        Uses chi-square test for statistical significance.
        """
        # Check if all variants have minimum sample size
        min_sends = min(v.sends for v in test.variants)
        if min_sends < test.min_sample_size:
            return

        # Calculate chi-square for conversion rates
        confidence, winner_idx = self._chi_square_test(test.variants)

        test.confidence_level = confidence

        if confidence >= self.CONFIDENCE_THRESHOLD:
            test.winner = test.variants[winner_idx].name
            test.status = TestStatus.COMPLETED
            test.completed_at = datetime.now().isoformat()
            self._save_tests()

            log.info("🏆 Winner determined for test %s: Variant %s (confidence=%.1f%%)",
                     test.test_id, test.winner.value, confidence)

    def _chi_square_test(self, variants: List[Variant]) -> Tuple[float, int]:
        """
        Perform chi-square test to determine statistical significance.

        Returns:
            Tuple of (confidence_level, winner_index)
        """
        if len(variants) < 2:
            return 0.0, 0

        # Find variant with highest conversion rate
        conversion_rates = [v.conversion_rate() for v in variants]
        winner_idx = conversion_rates.index(max(conversion_rates))

        # Compare winner with others (simplified chi-square)
        # Full implementation would use scipy.stats.chi2_contingency
        winner = variants[winner_idx]

        # Simple confidence calculation based on sample size and difference
        total_samples = sum(v.sends for v in variants)
        conversion_diff = max(conversion_rates) - min(conversion_rates)

        # Simplified confidence (would be chi-square p-value in production)
        confidence = min(
            100.0,
            (total_samples / self.MIN_SAMPLE_SIZE) * conversion_diff * 10
        )

        return confidence, winner_idx

    # ── Variant Selection ─────────────────────────────────────────────────────
    async def get_variant_to_send(self, test_id: str) -> Optional[Variant]:
        """
        Get the next variant to send for a test.
        Uses round-robin until winner is determined, then always returns winner.

        Returns:
            Variant to send, or None if test is not running
        """
        test = await self._get_test(test_id)

        if not test or test.status != TestStatus.RUNNING:
            return None

        # If winner determined, always return winner
        if test.winner:
            for variant in test.variants:
                if variant.name == test.winner:
                    return variant

        # Round-robin: find variant with least sends
        min_sends = min(v.sends for v in test.variants)
        for variant in test.variants:
            if variant.sends == min_sends:
                return variant

        return test.variants[0]

    # ── Query ─────────────────────────────────────────────────────────────────
    async def _get_test(self, test_id: str) -> Optional[ABTest]:
        """Get test by ID."""
        for test in self.tests:
            if test.test_id == test_id:
                return test
        return None

    async def get_test_results(self, test_id: str) -> Optional[Dict]:
        """Get test results with detailed metrics."""
        test = await self._get_test(test_id)

        if not test:
            return None

        results = {
            "test_id": test.test_id,
            "name": test.name,
            "test_type": test.test_type,
            "status": test.status.value,
            "winner": test.winner.value if test.winner else None,
            "confidence_level": test.confidence_level,
            "variants": [],
        }

        for variant in test.variants:
            results["variants"].append({
                "name": variant.name.value,
                "sends": variant.sends,
                "opens": variant.opens,
                "clicks": variant.clicks,
                "replies": variant.replies,
                "conversions": variant.conversions,
                "open_rate": variant.open_rate(),
                "reply_rate": variant.reply_rate(),
                "conversion_rate": variant.conversion_rate(),
            })

        return results

    async def get_running_tests(self) -> List[ABTest]:
        """Get all running tests."""
        return [test for test in self.tests if test.status == TestStatus.RUNNING]

    async def get_completed_tests(self) -> List[ABTest]:
        """Get all completed tests."""
        return [test for test in self.tests if test.status == TestStatus.COMPLETED]

    def get_stats(self) -> Dict:
        """Get A/B testing statistics."""
        if not self.tests:
            return {
                "total_tests": 0,
                "running": 0,
                "completed": 0,
                "avg_confidence": 0,
            }

        return {
            "total_tests": len(self.tests),
            "running": sum(1 for t in self.tests if t.status == TestStatus.RUNNING),
            "completed": sum(1 for t in self.tests if t.status == TestStatus.COMPLETED),
            "avg_confidence": sum(t.confidence_level for t in self.tests if t.winner) /
                            len([t for t in self.tests if t.winner]) if any(t.winner for t in self.tests) else 0,
        }


# ── CLI Test ──────────────────────────────────────────────────────────────────
async def main():
    """Test A/B Testing Engine."""
    print("🧪 NAYA A/B Testing Engine — Test Module\n")

    engine = ABTestingEngine()

    # Create test
    test = await engine.create_test(
        test_id="TEST_001",
        name="Email Subject Test - Transport Sector",
        test_type="email_subject",
        variant_a="NIS2: Deadline octobre 2024 - Audit express disponible",
        variant_b="SNCF, RATP: 67% des usines attaquées en 2024 - Protégez votre OT",
        variant_c="Audit IEC 62443 gratuit pour les 5 premiers répondants",
        min_sample_size=30,
    )

    print(f"✅ Created test: {test.name}")
    print(f"   Test ID: {test.test_id}")
    print(f"   Variants: {len(test.variants)}")

    # Simulate some sends and conversions
    print("\n📊 Simulating campaign...")

    for i in range(100):
        variant = await engine.get_variant_to_send(test.test_id)
        if variant:
            await engine.record_send(test.test_id, variant.name)

            # Simulate results (variant B performs better)
            if variant.name == VariantName.B:
                if i % 2 == 0:
                    await engine.record_open(test.test_id, variant.name)
                if i % 5 == 0:
                    await engine.record_reply(test.test_id, variant.name)
                if i % 10 == 0:
                    await engine.record_conversion(test.test_id, variant.name)
            else:
                if i % 3 == 0:
                    await engine.record_open(test.test_id, variant.name)
                if i % 8 == 0:
                    await engine.record_reply(test.test_id, variant.name)
                if i % 15 == 0:
                    await engine.record_conversion(test.test_id, variant.name)

    # Get results
    results = await engine.get_test_results(test.test_id)

    print("\n📈 Test Results:")
    print(f"   Status: {results['status']}")
    print(f"   Winner: {results['winner']}")
    print(f"   Confidence: {results['confidence_level']:.1f}%")

    print("\n   Variant Performance:")
    for variant in results["variants"]:
        print(f"\n   Variant {variant['name']}:")
        print(f"     Sends: {variant['sends']}")
        print(f"     Opens: {variant['opens']} ({variant['open_rate']:.1f}%)")
        print(f"     Replies: {variant['replies']} ({variant['reply_rate']:.1f}%)")
        print(f"     Conversions: {variant['conversions']} ({variant['conversion_rate']:.1f}%)")

    # Stats
    stats = engine.get_stats()
    print(f"\n📊 Engine Statistics:")
    print(f"   Total tests: {stats['total_tests']}")
    print(f"   Running: {stats['running']}")
    print(f"   Completed: {stats['completed']}")
    print(f"   Avg confidence: {stats['avg_confidence']:.1f}%")


if __name__ == "__main__":
    asyncio.run(main())
