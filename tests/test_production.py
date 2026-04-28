"""
NAYA SUPREME - Unit Tests
═════════════════════════════════════════════════════════════════════════════════

Suite de tests pytest pour validation complète du système.
Coverage: Models, API, Business logic, Error handling.
"""

import sys
import os
from pathlib import Path

# Ajouter la racine du projet au chemin de recherche
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from RUNTIME.pydantic_models import (
    PainSignalRequest,
    ServiceOfferRequest,
    BusinessProfile,
    ContactInfo,
    PaymentIntent,
)


# ════════════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS TESTS
# ════════════════════════════════════════════════════════════════════════════════

class TestPainSignalValidation:
    """Test PainSignalRequest validation"""
    
    def test_valid_pain_signal(self):
        """Test valid pain signal"""
        data = {
            "business_id": "biz_123",
            "pain_type": "financial",
            "description": "Cash flow problems affecting business operations",
            "severity": 8
        }
        signal = PainSignalRequest(**data)
        assert signal.business_id == "biz_123"
        assert signal.severity == 8
    
    def test_invalid_pain_signal_missing_required(self):
        """Test missing required field"""
        data = {
            "business_id": "biz_123",
            "pain_type": "financial"
            # Missing description
        }
        with pytest.raises(ValueError):
            PainSignalRequest(**data)
    
    def test_invalid_pain_signal_short_description(self):
        """Test description too short"""
        data = {
            "business_id": "biz_123",
            "pain_type": "financial",
            "description": "Short",  # Too short
            "severity": 5
        }
        with pytest.raises(ValueError):
            PainSignalRequest(**data)
    
    def test_invalid_severity_out_of_range(self):
        """Test severity outside valid range"""
        data = {
            "business_id": "biz_123",
            "pain_type": "financial",
            "description": "Valid description with enough characters",
            "severity": 15  # Out of range
        }
        with pytest.raises(ValueError):
            PainSignalRequest(**data)


class TestServiceOfferValidation:
    """Test ServiceOfferRequest validation"""
    
    def test_valid_service_offer(self):
        """Test valid service offer"""
        data = {
            "title": "Premium Consulting",
            "description": "Full-service business consulting and optimization",
            "price_tier": "premium",
            "delivery_days": 30
        }
        offer = ServiceOfferRequest(**data)
        assert offer.price_tier == "premium"
    
    def test_invalid_price_tier(self):
        """Test invalid price tier"""
        data = {
            "title": "Premium Consulting",
            "description": "Full-service business consulting and optimization",
            "price_tier": "invalid_tier",
            "delivery_days": 30
        }
        with pytest.raises(ValueError):
            ServiceOfferRequest(**data)
    
    def test_invalid_delivery_days(self):
        """Test invalid delivery days"""
        data = {
            "title": "Premium Consulting",
            "description": "Full-service business consulting and optimization",
            "price_tier": "premium",
            "delivery_days": 400  # Too high
        }
        with pytest.raises(ValueError):
            ServiceOfferRequest(**data)


class TestBusinessProfileValidation:
    """Test BusinessProfile validation"""
    
    def test_valid_profile(self):
        """Test valid business profile"""
        contact = ContactInfo(
            email="contact@techcorp.com",
            phone="+14155552671"
        )
        data = {
            "name": "TechCorp Inc",
            "industry": "technology",
            "size": "mid-market",
            "contact": contact
        }
        profile = BusinessProfile(**data)
        assert profile.name == "TechCorp Inc"
    
    def test_invalid_company_size(self):
        """Test invalid company size"""
        contact = ContactInfo(email="contact@techcorp.com")
        data = {
            "name": "TechCorp Inc",
            "industry": "technology",
            "size": "unknown_size",
            "contact": contact
        }
        with pytest.raises(ValueError):
            BusinessProfile(**data)


# ════════════════════════════════════════════════════════════════════════════════
# PROMETHEUS METRICS TESTS
# ════════════════════════════════════════════════════════════════════════════════

class TestPrometheusMetrics:
    """Test Prometheus metrics collection"""
    
    @pytest.fixture
    def metrics_module(self):
        """Import metrics module"""
        from RUNTIME.prometheus_metrics import (
            pain_signals_detected,
            service_offers_generated,
            leads_generated
        )
        return {
            'pain_signals': pain_signals_detected,
            'service_offers': service_offers_generated,
            'leads': leads_generated
        }
    
    def test_track_pain_signal(self, metrics_module):
        """Test tracking pain signal"""
        initial_value = metrics_module['pain_signals'].labels(
            industry='tech',
            pain_type='financial'
        )._value.get()
        
        metrics_module['pain_signals'].labels(
            industry='tech',
            pain_type='financial'
        ).inc()
        
        final_value = metrics_module['pain_signals'].labels(
            industry='tech',
            pain_type='financial'
        )._value.get()
        
        assert final_value > initial_value
    
    def test_track_service_offer(self, metrics_module):
        """Test tracking service offer"""
        initial_value = metrics_module['service_offers'].labels(
            tier='premium',
            industry='tech'
        )._value.get()
        
        metrics_module['service_offers'].labels(
            tier='premium',
            industry='tech'
        ).inc()
        
        final_value = metrics_module['service_offers'].labels(
            tier='premium',
            industry='tech'
        )._value.get()
        
        assert final_value > initial_value


# ════════════════════════════════════════════════════════════════════════════════
# REDIS RATE LIMITING TESTS
# ════════════════════════════════════════════════════════════════════════════════

class TestRedisRateLimiting:
    """Test Redis rate limiting (mocked)"""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        with patch('redis.from_url') as mock:
            mock.return_value.ping.return_value = True
            yield mock.return_value
    
    def test_rate_limiter_init(self, mock_redis):
        """Test rate limiter initialization"""
        from RUNTIME.redis_rate_limiting import RedisRateLimiter
        
        limiter = RedisRateLimiter("redis://localhost:6379/0")
        assert limiter.redis is not None
    
    def test_check_rate_limit_allowed(self, mock_redis):
        """Test rate limit check when allowed"""
        mock_redis.zcard.return_value = 5
        mock_redis.zremrangebyscore.return_value = None
        mock_redis.zadd.return_value = 1
        
        from RUNTIME.redis_rate_limiting import RedisRateLimiter
        limiter = RedisRateLimiter("redis://localhost:6379/0")
        
        result = limiter.check_rate_limit("test_key", 10, 60)
        assert result["allowed"] == True  # zcard returns 5, limit is 10 → 5 < 10 → allowed


# ════════════════════════════════════════════════════════════════════════════════
# STRUCTURED LOGGING TESTS
# ════════════════════════════════════════════════════════════════════════════════

class TestStructuredLogging:
    """Test structured logging functionality"""
    
    def test_logger_initialization(self):
        """Test logger initialization"""
        from RUNTIME.structured_logging import setup_logging
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_logging(
                "test_logger",
                log_level="INFO",
                log_dir=tmpdir,
                enable_json=True
            )
            assert logger is not None
            assert logger.name == "test_logger"
    
    def test_log_with_context(self):
        """Test logging with context"""
        from RUNTIME.structured_logging import log_with_context
        import tempfile
        from RUNTIME.structured_logging import setup_logging
        
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_logging(
                "test_context",
                log_dir=tmpdir,
                enable_json=False  # Disable JSON for this test
            )
            
            # Should not raise
            log_with_context(
                logger,
                "INFO",
                "Test message",
                user_id="123",
                action="test"
            )


# ════════════════════════════════════════════════════════════════════════════════
# PAYMENT MODELS TESTS
# ════════════════════════════════════════════════════════════════════════════════

class TestPaymentValidation:
    """Test payment models validation"""
    
    def test_valid_payment_intent(self):
        """Test valid payment intent"""
        data = {
            "amount": 999.99,
            "currency": "USD",
            "service_id": "service_123",
            "client_id": "client_456"
        }
        intent = PaymentIntent(**data)
        assert intent.amount == 999.99
        assert intent.currency == "USD"
    
    def test_invalid_payment_amount_zero(self):
        """Test payment with zero amount"""
        data = {
            "amount": 0,
            "currency": "USD",
            "service_id": "service_123",
            "client_id": "client_456"
        }
        with pytest.raises(ValueError):
            PaymentIntent(**data)
    
    def test_invalid_payment_amount_negative(self):
        """Test payment with negative amount"""
        data = {
            "amount": -100.0,
            "currency": "USD",
            "service_id": "service_123",
            "client_id": "client_456"
        }
        with pytest.raises(ValueError):
            PaymentIntent(**data)
    
    def test_invalid_currency_format(self):
        """Test invalid currency code"""
        data = {
            "amount": 100.0,
            "currency": "INVALID",
            "service_id": "service_123",
            "client_id": "client_456"
        }
        with pytest.raises(ValueError):
            PaymentIntent(**data)


# ════════════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS
# ════════════════════════════════════════════════════════════════════════════════

class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_pain_signal_to_offer_workflow(self):
        """Test workflow: pain signal -> service offer"""
        # Create pain signal
        pain = PainSignalRequest(
            business_id="biz_test",
            pain_type="financial",
            description="Testing pain signal workflow creation",
            severity=7
        )
        
        assert pain.business_id == "biz_test"
        
        # Create matching offer
        offer = ServiceOfferRequest(
            title="Financial Optimization",
            description="Complete financial restructuring and optimization service",
            price_tier="enterprise",
            delivery_days=45,
            business_id=pain.business_id
        )
        
        assert offer.business_id == pain.business_id
        assert offer.price_tier == "enterprise"


# ════════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ════════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def test_config():
    """Test configuration"""
    return {
        "test_db_url": "sqlite:///./test_naya.db",
        "test_redis_url": "redis://localhost:6379/1",
        "test_log_dir": "./test_logs"
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=RUNTIME", "--cov-report=html"])
