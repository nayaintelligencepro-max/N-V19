"""
NAYA V19 — ML Revenue Engine
Self-learning conversion prediction and offer optimization
"""
import logging
import json
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import statistics

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    import numpy as np
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

log = logging.getLogger("NAYA.ML_ENGINE")

@dataclass
class ConversionDataPoint:
    """Single conversion data point."""
    lead_id: str
    lead_score: float
    offer_price: float
    offer_type: str
    industry: str
    company_size: str  # "small", "medium", "large"
    engagement_days: int
    email_opens: int
    email_clicks: int
    converted: bool  # Target variable
    conversion_value: float = 0.0
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_features(self) -> list:
        """Convert to feature vector."""
        return [
            self.lead_score,
            float(self.offer_price),
            self._encode_offer_type(),
            self._encode_industry(),
            self._encode_company_size(),
            float(self.engagement_days),
            float(self.email_opens),
            float(self.email_clicks),
        ]
    
    def _encode_offer_type(self) -> float:
        """Encode offer type."""
        mapping = {"audit": 0.0, "security": 1.0, "premium": 2.0}
        return mapping.get(self.offer_type, 0.0)
    
    def _encode_industry(self) -> float:
        """Encode industry."""
        mapping = {"energy": 0.0, "transport": 1.0, "industrial": 2.0, "other": 3.0}
        return mapping.get(self.industry, 3.0)
    
    def _encode_company_size(self) -> float:
        """Encode company size."""
        mapping = {"small": 0.0, "medium": 1.0, "large": 2.0}
        return mapping.get(self.company_size, 0.0)

class ConversionPredictor:
    """
    ML model for conversion prediction.
    
    Predicts likelihood of lead converting based on:
    - Lead quality score
    - Offer price/type
    - Industry/company size
    - Engagement metrics
    """
    
    def __init__(self, model_type: str = "random_forest"):
        """Initialize predictor."""
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler() if ML_AVAILABLE else None
        self.training_data: List[ConversionDataPoint] = []
        self.is_trained = False
        
        if ML_AVAILABLE:
            self.model = RandomForestClassifier(
                n_estimators=50,
                max_depth=10,
                random_state=42
            )
    
    def add_training_data(self, data_point: ConversionDataPoint):
        """Add training data point."""
        self.training_data.append(data_point)
        
        if len(self.training_data) % 10 == 0:
            log.info(f"📊 Training data: {len(self.training_data)} points collected")
    
    def train(self) -> dict:
        """Train model on collected data."""
        if not ML_AVAILABLE:
            log.warning("⚠️ sklearn not available, using fallback")
            return {"trained": False, "reason": "ML not available"}
        
        if len(self.training_data) < 10:
            log.warning(f"⚠️ Not enough training data ({len(self.training_data)} < 10)")
            return {"trained": False, "reason": "Not enough data"}
        
        try:
            # Prepare features and target
            X = np.array([dp.to_features() for dp in self.training_data])
            y = np.array([int(dp.converted) for dp in self.training_data])
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.model.fit(X_scaled, y)
            self.is_trained = True
            
            # Calculate accuracy
            accuracy = self.model.score(X_scaled, y)
            
            log.info(f"✅ Model trained: {len(self.training_data)} samples, accuracy={accuracy:.2%}")
            
            return {
                "trained": True,
                "accuracy": accuracy,
                "samples": len(self.training_data),
                "features": 8,
            }
        
        except Exception as e:
            log.error(f"❌ Training failed: {e}", exc_info=True)
            return {"trained": False, "error": str(e)}
    
    def predict(self, data_point: ConversionDataPoint) -> Dict[str, float]:
        """
        Predict conversion probability.
        
        Returns:
            {
                "probability": 0.0-1.0,
                "converted": bool,
                "confidence": 0.0-1.0,
            }
        """
        if not ML_AVAILABLE:
            # Fallback: simple heuristic
            return self._heuristic_predict(data_point)
        
        if not self.is_trained or self.model is None:
            # Use heuristic if model not trained
            return self._heuristic_predict(data_point)
        
        try:
            X = np.array([data_point.to_features()])
            X_scaled = self.scaler.transform(X)
            
            probability = self.model.predict_proba(X_scaled)[0][1]
            
            return {
                "probability": float(probability),
                "converted": probability > 0.5,
                "confidence": abs(probability - 0.5) * 2,  # 0-1, higher = more confident
            }
        except Exception as e:
            log.warning(f"⚠️ Prediction failed: {e}, using heuristic")
            return self._heuristic_predict(data_point)
    
    def _heuristic_predict(self, data_point: ConversionDataPoint) -> Dict[str, float]:
        """Fallback heuristic prediction."""
        # Simple scoring: lead_score (40%) + engagement (60%)
        engagement_score = (
            data_point.email_opens * 0.5 +
            data_point.email_clicks * 1.0 +
            data_point.engagement_days * 0.1
        ) / 100
        
        prob = (
            0.4 * (data_point.lead_score / 100) +
            0.6 * min(engagement_score, 1.0)
        )
        
        return {
            "probability": float(prob),
            "converted": prob > 0.5,
            "confidence": 0.3,  # Low confidence with heuristic
        }
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from trained model."""
        if not self.is_trained or not hasattr(self.model, 'feature_importances_'):
            return {}
        
        feature_names = [
            "lead_score",
            "offer_price",
            "offer_type",
            "industry",
            "company_size",
            "engagement_days",
            "email_opens",
            "email_clicks",
        ]
        
        importances = self.model.feature_importances_
        return {
            name: float(importance)
            for name, importance in zip(feature_names, importances)
        }

class OfferOptimizer:
    """
    Dynamic offer optimization using ML feedback.
    
    Optimizes:
    - Offer price based on lead quality
    - Offer type (audit/security/premium)
    - Messaging personalization
    """
    
    def __init__(self, base_prices: Dict[str, float] = None):
        """Initialize optimizer."""
        self.base_prices = base_prices or {
            "audit": 15000.0,
            "security": 40000.0,
            "premium": 80000.0,
        }
        
        self.conversion_predictor = ConversionPredictor()
        self.price_history: List[Tuple[str, float, bool]] = []  # (offer_type, price, converted)
    
    def optimize_offer(self, lead_data: Dict) -> Dict:
        """
        Generate optimized offer for lead.
        
        Returns:
            {
                "offer_type": "audit|security|premium",
                "base_price": float,
                "optimized_price": float,
                "discount": float,
                "conversion_probability": float,
                "confidence": float,
            }
        """
        # Determine best offer type
        offer_type = self._select_offer_type(lead_data)
        base_price = self.base_prices[offer_type]
        
        # Create data point for prediction
        data_point = ConversionDataPoint(
            lead_id=lead_data.get("lead_id", "unknown"),
            lead_score=lead_data.get("lead_score", 50.0),
            offer_price=base_price,
            offer_type=offer_type,
            industry=lead_data.get("industry", "other"),
            company_size=lead_data.get("company_size", "small"),
            engagement_days=lead_data.get("engagement_days", 0),
            email_opens=lead_data.get("email_opens", 0),
            email_clicks=lead_data.get("email_clicks", 0),
            converted=False,  # Prediction will tell us
        )
        
        # Predict conversion
        prediction = self.conversion_predictor.predict(data_point)
        
        # Optimize price based on probability
        optimized_price = self._optimize_price(
            base_price,
            prediction["probability"],
            lead_data.get("company_size", "small")
        )
        
        discount = (base_price - optimized_price) / base_price * 100
        
        return {
            "offer_type": offer_type,
            "base_price": base_price,
            "optimized_price": optimized_price,
            "discount": round(discount, 1),
            "conversion_probability": round(prediction["probability"], 3),
            "confidence": round(prediction["confidence"], 3),
            "recommendation": "HIGH PRIORITY" if prediction["probability"] > 0.7 else "NORMAL"
        }
    
    def _select_offer_type(self, lead_data: Dict) -> str:
        """Select best offer type for lead."""
        lead_score = lead_data.get("lead_score", 50.0)
        company_size = lead_data.get("company_size", "small")
        
        if lead_score >= 80 and company_size == "large":
            return "premium"
        elif lead_score >= 60:
            return "security"
        else:
            return "audit"
    
    def _optimize_price(self, base_price: float, 
                       conversion_prob: float,
                       company_size: str) -> float:
        """Optimize price based on conversion probability."""
        # Higher conversion prob = we can charge more (up to base)
        # Lower conversion prob = discount needed
        
        company_multiplier = {
            "small": 0.8,
            "medium": 1.0,
            "large": 1.2,
        }.get(company_size, 1.0)
        
        # If high conversion probability, maintain/increase price
        if conversion_prob > 0.7:
            return base_price * company_multiplier
        # If medium probability, apply small discount
        elif conversion_prob > 0.4:
            return base_price * company_multiplier * 0.9
        # If low probability, apply significant discount
        else:
            return base_price * company_multiplier * 0.7
    
    def record_outcome(self, offer_data: Dict, converted: bool, 
                      actual_value: Optional[float] = None):
        """Record offer outcome for feedback loop."""
        data_point = ConversionDataPoint(
            lead_id=offer_data.get("lead_id", "unknown"),
            lead_score=offer_data.get("lead_score", 50.0),
            offer_price=offer_data.get("offer_price", 0.0),
            offer_type=offer_data.get("offer_type", "audit"),
            industry=offer_data.get("industry", "other"),
            company_size=offer_data.get("company_size", "small"),
            engagement_days=offer_data.get("engagement_days", 0),
            email_opens=offer_data.get("email_opens", 0),
            email_clicks=offer_data.get("email_clicks", 0),
            converted=converted,
            conversion_value=actual_value or 0.0,
        )
        
        self.conversion_predictor.add_training_data(data_point)
        self.price_history.append((offer_data.get("offer_type"), 
                                   offer_data.get("offer_price"), 
                                   converted))
        
        # Re-train if enough new data
        if len(self.conversion_predictor.training_data) % 20 == 0:
            self.conversion_predictor.train()
    
    def get_analytics(self) -> Dict:
        """Get optimization analytics."""
        if not self.price_history:
            return {"conversions": 0, "conversion_rate": 0.0}
        
        conversions = sum(1 for _, _, converted in self.price_history if converted)
        conversion_rate = conversions / len(self.price_history)
        
        # Average price by outcome
        converted_prices = [p for _, p, c in self.price_history if c]
        avg_converted_price = statistics.mean(converted_prices) if converted_prices else 0
        
        return {
            "total_offers": len(self.price_history),
            "conversions": conversions,
            "conversion_rate": round(conversion_rate, 3),
            "avg_converted_price": round(avg_converted_price, 2),
            "total_revenue": sum(p for _, p, c in self.price_history if c),
        }
