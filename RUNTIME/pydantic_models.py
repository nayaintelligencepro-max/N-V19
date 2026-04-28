"""
NAYA SUPREME - Pydantic Validation Models
═════════════════════════════════════════════════════════════════════════════════

Production-grade input validation pour tous les endpoints FastAPI.
Centralisé, réutilisable, avec messages d'erreur clairs.
Compatible Pydantic v2.
"""

from pydantic import BaseModel, Field, HttpUrl, field_validator, ConfigDict, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ════════════════════════════════════════════════════════════════════════════════
# BUSINESS REQUEST MODELS
# ════════════════════════════════════════════════════════════════════════════════

class PainType(str, Enum):
    """Types de pain points acceptés"""
    OPERATIONAL = "operational"
    FINANCIAL = "financial"
    MARKET = "market"
    TECHNICAL = "technical"
    STRATEGIC = "strategic"


class PainSignalRequest(BaseModel):
    """Modèle pour un signal de pain détecté"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "business_id": "business_123",
                "pain_type": "financial",
                "description": "Cash flow issues affecting operations",
                "severity": 8,
                "context": {"industry": "retail"}
            }
        }
    )

    business_id: str = Field(..., min_length=1, max_length=255)
    pain_type: PainType
    description: str = Field(..., min_length=10, max_length=5000)
    severity: int = Field(..., ge=1, le=10)
    context: Optional[Dict[str, Any]] = None


class ServiceOfferRequest(BaseModel):
    """Modèle pour une offre de service"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Cash Flow Optimization Service",
                "description": "Complete financial restructuring and optimization",
                "price_tier": "enterprise",
                "delivery_days": 30
            }
        }
    )

    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=20, max_length=2000)
    price_tier: str = Field(..., pattern="^(premium|enterprise|custom)$")
    delivery_days: int = Field(..., ge=1, le=365)
    business_id: Optional[str] = None


class PublicationRequest(BaseModel):
    """Modèle pour une publication sur canal"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "channel": "linkedin",
                "content": "Introducing our latest financial optimization solution...",
                "scheduled_time": None
            }
        }
    )

    channel: str = Field(..., pattern="^(linkedin|twitter|telegram|email|whatsapp)$")
    content: str = Field(..., min_length=5, max_length=3000)
    scheduled_time: Optional[datetime] = None
    target_audience: Optional[List[str]] = None


# ════════════════════════════════════════════════════════════════════════════════
# BUSINESS ENTITY MODELS
# ════════════════════════════════════════════════════════════════════════════════

class ContactInfo(BaseModel):
    """Information de contact"""
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern="^\\+?[0-9]{10,15}$")
    linkedin: Optional[HttpUrl] = None
    website: Optional[HttpUrl] = None


class BusinessProfile(BaseModel):
    """Profil métier complet"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "TechCorp Inc",
                "industry": "technology",
                "size": "mid-market",
                "revenue_range": "10M-50M",
                "contact": {
                    "email": "contact@techcorp.com",
                    "linkedin": "https://linkedin.com/company/techcorp"
                },
                "location": "San Francisco, CA"
            }
        }
    )

    name: str = Field(..., min_length=2, max_length=255)
    industry: str = Field(..., min_length=2, max_length=100)
    size: str = Field(..., pattern="^(startup|sme|mid-market|enterprise)$")
    revenue_range: Optional[str] = None
    contact: ContactInfo
    location: Optional[str] = None


# ════════════════════════════════════════════════════════════════════════════════
# HUNTING & INTELLIGENCE MODELS
# ════════════════════════════════════════════════════════════════════════════════

class HuntingQuery(BaseModel):
    """Requête de hunting (recherche de leads)"""
    keywords: List[str] = Field(..., min_length=1, max_length=20)
    industries: Optional[List[str]] = None
    regions: Optional[List[str]] = None
    company_size: Optional[str] = None
    limit: int = Field(10, ge=1, le=100)

    @field_validator('keywords')
    @classmethod
    def validate_keywords(cls, v: List[str]) -> List[str]:
        for keyword in v:
            if len(keyword) < 2 or len(keyword) > 100:
                raise ValueError("Each keyword must be 2-100 characters")
        return v


class IntelligenceReport(BaseModel):
    """Rapport d'intelligence métier"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "business_id": "biz_456",
                "insights": ["Strong market demand", "Weak supply"],
                "recommendations": ["Expand team", "Invest in marketing"],
                "confidence_score": 0.85
            }
        }
    )

    business_id: str = Field(..., min_length=1)
    insights: List[str] = Field(..., min_length=1)
    recommendations: List[str]
    confidence_score: float = Field(..., ge=0.0, le=1.0)


# ════════════════════════════════════════════════════════════════════════════════
# REVENUE & TRANSACTION MODELS
# ════════════════════════════════════════════════════════════════════════════════

class PaymentIntent(BaseModel):
    """Intention de paiement"""
    amount: float = Field(..., gt=0.0, le=999999.99)
    currency: str = Field("USD", pattern="^[A-Z]{3}$")
    service_id: str = Field(..., min_length=1)
    client_id: str = Field(..., min_length=1)
    description: Optional[str] = None


class TransactionRecord(BaseModel):
    """Enregistrement de transaction"""
    transaction_id: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0.0)
    status: str = Field(..., pattern="^(pending|completed|failed|refunded)$")
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class RevenueTarget(BaseModel):
    """Cible de revenue"""
    project_id: str = Field(..., min_length=1)
    target_amount: float = Field(..., gt=0.0)
    deadline: datetime
    channels: List[str] = Field(..., min_length=1)

    @field_validator('deadline')
    @classmethod
    def validate_deadline(cls, v: datetime) -> datetime:
        if v <= datetime.now():
            raise ValueError("Deadline must be in the future")
        return v


# ════════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION & SECURITY MODELS
# ════════════════════════════════════════════════════════════════════════════════

class AuthCredentials(BaseModel):
    """Credentials d'authentification"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=255)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain digit")
        return v


class APIKeyRequest(BaseModel):
    """Demande de clé API"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Integration API Key",
                "scopes": ["read:leads", "write:offers"]
            }
        }
    )

    name: str = Field(..., min_length=3, max_length=100)
    scopes: List[str] = Field(..., min_length=1)


# ════════════════════════════════════════════════════════════════════════════════
# RESPONSE MODELS
# ════════════════════════════════════════════════════════════════════════════════

class SuccessResponse(BaseModel):
    """Réponse de succès standardisée"""
    status: str = "success"
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseModel):
    """Réponse d'erreur standardisée"""
    status: str = "error"
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class PaginatedResponse(BaseModel):
    """Réponse paginée"""
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int
