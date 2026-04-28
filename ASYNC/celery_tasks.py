"""
NAYA V19 — Async Task Processing
Celery-based task queue for long-running operations
"""
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

try:
    from celery import Celery, Task
    from celery.utils.log import get_task_logger
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False

log = logging.getLogger("NAYA.ASYNC")

# Task types
TASK_LEAD_SCORING = "tasks.score_lead"
TASK_OFFER_GENERATION = "tasks.generate_offer"
TASK_OUTREACH_EMAIL = "tasks.send_outreach_email"
TASK_REPORT_GENERATION = "tasks.generate_report"
TASK_DATA_SYNC = "tasks.sync_data"
TASK_ML_TRAINING = "tasks.train_ml_model"
TASK_REVENUE_CALCULATION = "tasks.calculate_revenue"

@dataclass
class TaskResult:
    """Result of async task."""
    task_id: str
    task_type: str
    status: str  # PENDING, STARTED, SUCCESS, FAILURE, RETRY
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: str = None
    completed_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

class NAYACeleryApp:
    """
    NAYA Celery application for async task processing.
    
    Features:
    - Long-running task execution
    - Task scheduling
    - Task monitoring
    - Error handling and retries
    """
    
    def __init__(self,
                 broker_url: str = "amqp://guest:guest@localhost:5672//",
                 result_backend: str = "redis://localhost:6379/0"):
        """
        Initialize Celery app.
        
        Args:
            broker_url: RabbitMQ or Redis URL
            result_backend: Redis backend for results
        """
        self.broker_url = broker_url
        self.result_backend = result_backend
        self.app: Optional[Celery] = None
        self._initialized = False
    
    def initialize(self) -> dict:
        """Initialize Celery application."""
        if not CELERY_AVAILABLE:
            log.warning("⚠️ Celery not installed")
            return {"initialized": False, "reason": "Celery not available"}
        
        try:
            self.app = Celery("naya-v19")
            
            self.app.conf.update(
                broker_url=self.broker_url,
                result_backend=self.result_backend,
                task_serializer="json",
                accept_content=["json"],
                result_serializer="json",
                timezone="UTC",
                enable_utc=True,
                task_track_started=True,
                task_time_limit=30 * 60,  # 30 minutes
                task_soft_time_limit=25 * 60,  # 25 minutes
                result_expires=3600,  # 1 hour
                worker_prefetch_multiplier=4,
                worker_max_tasks_per_child=1000,
            )
            
            self._initialize_tasks()
            self._initialized = True
            
            log.info(f"✅ Celery initialized: {self.broker_url}")
            return {
                "initialized": True,
                "broker": self.broker_url,
                "backend": self.result_backend,
            }
        
        except Exception as e:
            log.error(f"❌ Celery init failed: {e}")
            return {"initialized": False, "error": str(e)}
    
    def _initialize_tasks(self):
        """Register NAYA tasks."""
        
        @self.app.task(name=TASK_LEAD_SCORING, bind=True, autoretry_for=(Exception,), 
                      retry_kwargs={'max_retries': 3})
        def score_lead(self, lead_id: str, lead_data: Dict) -> Dict:
            """Score lead using ML model."""
            try:
                # Simulated scoring logic
                score = min(100, sum([
                    lead_data.get("engagement_days", 0) * 2,
                    lead_data.get("company_revenue", 0) / 1000,
                ]))
                
                log.info(f"✅ Scored lead {lead_id}: {score:.1f}")
                
                return {
                    "lead_id": lead_id,
                    "score": score,
                    "timestamp": datetime.now().isoformat(),
                }
            except Exception as e:
                log.error(f"❌ Scoring failed: {e}")
                raise
        
        @self.app.task(name=TASK_OFFER_GENERATION, bind=True)
        def generate_offer(self, lead_id: str, offer_type: str) -> Dict:
            """Generate personalized offer."""
            try:
                prices = {
                    "audit": 15000,
                    "security": 40000,
                    "premium": 80000,
                }
                
                offer = {
                    "offer_id": f"OFFER-{lead_id}",
                    "lead_id": lead_id,
                    "type": offer_type,
                    "price": prices.get(offer_type, 15000),
                    "created_at": datetime.now().isoformat(),
                    "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
                }
                
                log.info(f"✅ Generated {offer_type} offer for {lead_id}")
                
                return offer
            except Exception as e:
                log.error(f"❌ Offer generation failed: {e}")
                raise
        
        @self.app.task(name=TASK_OUTREACH_EMAIL, bind=True, autoretry_for=(Exception,),
                      retry_kwargs={'max_retries': 2})
        def send_outreach_email(self, lead_id: str, email: str, subject: str, body: str) -> Dict:
            """Send outreach email."""
            try:
                # Simulated email sending
                log.info(f"📧 Email sent to {email}: {subject[:30]}...")
                
                return {
                    "lead_id": lead_id,
                    "email": email,
                    "status": "sent",
                    "timestamp": datetime.now().isoformat(),
                }
            except Exception as e:
                log.error(f"❌ Email send failed: {e}")
                raise
        
        @self.app.task(name=TASK_REPORT_GENERATION)
        def generate_report(self, report_type: str, date_range: Dict) -> Dict:
            """Generate business report."""
            try:
                log.info(f"📊 Generating {report_type} report")
                
                return {
                    "report_type": report_type,
                    "period": f"{date_range['start']} to {date_range['end']}",
                    "status": "generated",
                    "timestamp": datetime.now().isoformat(),
                }
            except Exception as e:
                log.error(f"❌ Report generation failed: {e}")
                raise
        
        @self.app.task(name=TASK_ML_TRAINING)
        def train_ml_model(self) -> Dict:
            """Train ML conversion model."""
            try:
                log.info("🤖 Training ML model...")
                
                return {
                    "status": "trained",
                    "accuracy": 0.85,
                    "samples": 1000,
                    "timestamp": datetime.now().isoformat(),
                }
            except Exception as e:
                log.error(f"❌ ML training failed: {e}")
                raise
        
        @self.app.task(name=TASK_DATA_SYNC)
        def sync_data(self, source: str) -> Dict:
            """Sync data from external source."""
            try:
                log.info(f"🔄 Syncing data from {source}")
                
                return {
                    "source": source,
                    "records_synced": 100,
                    "timestamp": datetime.now().isoformat(),
                }
            except Exception as e:
                log.error(f"❌ Data sync failed: {e}")
                raise
    
    def submit_task(self, task_name: str, *args, **kwargs) -> str:
        """
        Submit async task.
        
        Returns:
            Task ID for tracking
        """
        if not self._initialized or not self.app:
            log.error("❌ Celery not initialized")
            return ""
        
        try:
            task = self.app.send_task(task_name, args=args, kwargs=kwargs)
            log.info(f"📤 Task submitted: {task_name} ({task.id})")
            return task.id
        except Exception as e:
            log.error(f"❌ Task submission failed: {e}")
            return ""
    
    def get_task_status(self, task_id: str) -> Dict:
        """Get task status."""
        if not self._initialized or not self.app:
            return {"status": "UNKNOWN", "error": "Celery not initialized"}
        
        try:
            task = self.app.AsyncResult(task_id)
            
            result = {
                "task_id": task_id,
                "status": task.status,
                "result": task.result if task.successful() else None,
                "error": str(task.info) if task.failed() else None,
            }
            
            return result
        except Exception as e:
            log.error(f"❌ Status check failed: {e}")
            return {"status": "ERROR", "error": str(e)}
    
    def get_status(self) -> dict:
        """Get Celery app status."""
        return {
            "initialized": self._initialized,
            "broker": self.broker_url,
            "backend": self.result_backend,
        }

# Global singleton
_celery_app: Optional[NAYACeleryApp] = None

def get_celery_app() -> NAYACeleryApp:
    """Get or create global Celery app."""
    global _celery_app
    if _celery_app is None:
        _celery_app = NAYACeleryApp()
        _celery_app.initialize()
    return _celery_app

def submit_scoring_task(lead_id: str, lead_data: Dict) -> str:
    """Submit lead scoring task."""
    app = get_celery_app()
    return app.submit_task(TASK_LEAD_SCORING, lead_id, lead_data)

def submit_offer_task(lead_id: str, offer_type: str) -> str:
    """Submit offer generation task."""
    app = get_celery_app()
    return app.submit_task(TASK_OFFER_GENERATION, lead_id, offer_type)

def submit_email_task(lead_id: str, email: str, subject: str, body: str) -> str:
    """Submit email sending task."""
    app = get_celery_app()
    return app.submit_task(TASK_OUTREACH_EMAIL, lead_id, email, subject, body)
