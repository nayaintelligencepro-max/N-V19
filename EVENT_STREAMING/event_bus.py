"""
NAYA V19 — Event Streaming
RabbitMQ-based event publishing/consumption for decoupled services
"""
import json
import logging
from typing import Callable, Optional, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

try:
    import pika
    PIKA_AVAILABLE = True
except ImportError:
    PIKA_AVAILABLE = False

log = logging.getLogger("NAYA.EVENT_STREAMING")

class EventType(Enum):
    """NAYA event types."""
    LEAD_CREATED = "lead.created"
    LEAD_SCORED = "lead.scored"
    OFFER_GENERATED = "offer.generated"
    OFFER_ACCEPTED = "offer.accepted"
    OFFER_REJECTED = "offer.rejected"
    CONVERSION_COMPLETED = "conversion.completed"
    REVENUE_RECORDED = "revenue.recorded"
    ERROR_OCCURRED = "error.occurred"
    SYSTEM_HEALTH = "system.health"

@dataclass
class Event:
    """Event data structure."""
    event_type: EventType
    timestamp: str
    source_service: str
    data: Dict[str, Any]
    event_id: Optional[str] = None
    correlation_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.event_id is None:
            import uuid
            self.event_id = str(uuid.uuid4())
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps({
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "source_service": self.source_service,
            "event_id": self.event_id,
            "correlation_id": self.correlation_id,
            "data": self.data,
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> "Event":
        """Deserialize from JSON."""
        data = json.loads(json_str)
        return cls(
            event_type=EventType(data["event_type"]),
            timestamp=data["timestamp"],
            source_service=data["source_service"],
            event_id=data.get("event_id"),
            correlation_id=data.get("correlation_id"),
            data=data["data"],
        )

class EventBus:
    """
    Event bus for publishing and subscribing to events.
    
    Decouples services through asynchronous messaging.
    """
    
    def __init__(self,
                 rabbitmq_host: str = "localhost",
                 rabbitmq_port: int = 5672,
                 rabbitmq_user: str = "guest",
                 rabbitmq_password: str = "guest"):
        """Initialize event bus."""
        self.rabbitmq_host = rabbitmq_host
        self.rabbitmq_port = rabbitmq_port
        self.rabbitmq_user = rabbitmq_user
        self.rabbitmq_password = rabbitmq_password
        
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.adapters.blocking_connection.BlockingChannel] = None
        self._subscriptions: Dict[EventType, list] = {}
        self._initialized = False
    
    def initialize(self) -> dict:
        """Initialize RabbitMQ connection."""
        if not PIKA_AVAILABLE:
            log.warning("⚠️ pika not installed, using fallback")
            return {"initialized": False, "reason": "pika not available"}
        
        try:
            credentials = pika.PlainCredentials(
                self.rabbitmq_user,
                self.rabbitmq_password
            )
            
            parameters = pika.ConnectionParameters(
                host=self.rabbitmq_host,
                port=self.rabbitmq_port,
                credentials=credentials,
                connection_attempts=3,
                retry_delay=2,
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare exchange
            self.channel.exchange_declare(
                exchange="naya-events",
                exchange_type="topic",
                durable=True,
            )
            
            self._initialized = True
            log.info(f"✅ Event bus initialized: {self.rabbitmq_host}:{self.rabbitmq_port}")
            
            return {
                "initialized": True,
                "host": self.rabbitmq_host,
                "port": self.rabbitmq_port,
            }
        
        except Exception as e:
            log.error(f"❌ Event bus init failed: {e}", exc_info=True)
            return {"initialized": False, "error": str(e)}
    
    def publish(self, event: Event) -> bool:
        """
        Publish event to bus.
        
        Args:
            event: Event to publish
            
        Returns:
            True if published successfully
        """
        if not self._initialized or not self.channel:
            log.warning("⚠️ Event bus not initialized, queueing locally")
            return False
        
        try:
            routing_key = f"naya.{event.event_type.value}"
            
            self.channel.basic_publish(
                exchange="naya-events",
                routing_key=routing_key,
                body=event.to_json(),
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=2,  # Persistent
                    headers={
                        "event_id": event.event_id,
                        "correlation_id": event.correlation_id,
                    }
                ),
            )
            
            log.debug(f"📤 Event published: {event.event_type.value} ({event.event_id})")
            return True
        
        except Exception as e:
            log.error(f"❌ Publish failed: {e}")
            return False
    
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """
        Subscribe to event type.
        
        Args:
            event_type: EventType to subscribe to
            callback: Function to call when event received
        """
        if event_type not in self._subscriptions:
            self._subscriptions[event_type] = []
        
        self._subscriptions[event_type].append(callback)
        log.info(f"📥 Subscribed to {event_type.value}")
    
    def start_consuming(self):
        """Start consuming events from subscribed topics."""
        if not self._initialized or not self.channel:
            log.error("❌ Event bus not initialized")
            return
        
        try:
            for event_type in self._subscriptions:
                routing_key = f"naya.{event_type.value}"
                
                # Declare queue
                queue_name = f"naya-{event_type.value}"
                self.channel.queue_declare(
                    queue=queue_name,
                    durable=True,
                )
                
                # Bind to exchange
                self.channel.queue_bind(
                    exchange="naya-events",
                    queue=queue_name,
                    routing_key=routing_key,
                )
            
            # Start consuming
            self.channel.basic_consume(
                queue=list(self._subscriptions.keys())[0].value if self._subscriptions else "",
                on_message_callback=self._on_message,
                auto_ack=True,
            )
            
            log.info("🔄 Started consuming events...")
            self.channel.start_consuming()
        
        except Exception as e:
            log.error(f"❌ Consumption failed: {e}")
    
    def _on_message(self, ch, method, properties, body):
        """Handle incoming message."""
        try:
            event = Event.from_json(body.decode())
            
            # Find and execute callbacks
            for callback in self._subscriptions.get(event.event_type, []):
                try:
                    callback(event)
                except Exception as e:
                    log.error(f"❌ Callback failed: {e}")
        
        except Exception as e:
            log.error(f"❌ Message processing failed: {e}")
    
    def close(self):
        """Close connection."""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            log.info("✅ Event bus closed")
    
    def get_status(self) -> dict:
        """Get event bus status."""
        return {
            "initialized": self._initialized,
            "connected": self.connection is not None and not self.connection.is_closed,
            "subscriptions": len(self._subscriptions),
            "event_types": [et.value for et in self._subscriptions.keys()],
        }

# Global singleton
_event_bus: Optional[EventBus] = None

def get_event_bus() -> EventBus:
    """Get or create global event bus."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
        _event_bus.initialize()
    return _event_bus

def publish_event(event_type: EventType, 
                 source_service: str,
                 data: Dict[str, Any],
                 correlation_id: Optional[str] = None) -> bool:
    """Convenience function to publish event."""
    bus = get_event_bus()
    event = Event(
        event_type=event_type,
        timestamp=datetime.now().isoformat(),
        source_service=source_service,
        data=data,
        correlation_id=correlation_id,
    )
    return bus.publish(event)
