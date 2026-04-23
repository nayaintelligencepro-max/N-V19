"""
NAYA SECURITY LAYER v1
JWT tokens, RBAC, audit logging, encryption
Enterprise-grade security without compromising speed
"""

import os, json, logging, hashlib, secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Any
from enum import Enum
import jwt
from functools import wraps

log = logging.getLogger("NAYA.SECURITY")

# ═══════════════════════════════════════════════════════════════════════════
# 1. ROLE & PERMISSION SYSTEM
# ═══════════════════════════════════════════════════════════════════════════

class Role(Enum):
    ADMIN = "admin"              # Full access
    MANAGER = "manager"          # Campaign + revenue access
    AGENT = "agent"              # Limited to assigned campaigns
    ANALYST = "analyst"          # Read-only access
    VENDOR = "vendor"            # External API partner
    GUEST = "guest"              # Minimal access

class Permission(Enum):
    # Hunting
    HUNTING_READ = "hunting:read"
    HUNTING_CREATE = "hunting:create"
    HUNTING_EXECUTE = "hunting:execute"
    
    # Revenue
    REVENUE_READ = "revenue:read"
    REVENUE_CREATE = "revenue:create"
    REVENUE_WITHDRAW = "revenue:withdraw"
    
    # Projects
    PROJECT_READ = "project:read"
    PROJECT_CREATE = "project:create"
    PROJECT_DELETE = "project:delete"
    
    # Security
    SECURITY_READ = "security:read"
    SECURITY_AUDIT = "security:audit"
    
    # Admin
    USER_MANAGE = "user:manage"
    CONFIG_MANAGE = "config:manage"

ROLE_PERMISSIONS = {
    Role.ADMIN: list(Permission),
    Role.MANAGER: [
        Permission.HUNTING_READ, Permission.HUNTING_CREATE,
        Permission.REVENUE_READ, Permission.REVENUE_CREATE,
        Permission.PROJECT_READ, Permission.PROJECT_CREATE
    ],
    Role.AGENT: [
        Permission.HUNTING_READ, Permission.HUNTING_EXECUTE,
        Permission.PROJECT_READ, Permission.REVENUE_READ
    ],
    Role.ANALYST: [
        Permission.HUNTING_READ, Permission.REVENUE_READ,
        Permission.PROJECT_READ, Permission.SECURITY_READ
    ],
    Role.VENDOR: [Permission.HUNTING_READ, Permission.REVENUE_READ],
    Role.GUEST: [Permission.HUNTING_READ]
}

# ═══════════════════════════════════════════════════════════════════════════
# 2. JWT TOKEN MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class JWTManager:
    """Generate and validate JWT tokens"""
    
    def __init__(self):
        self.secret = os.getenv("JWT_SECRET", secrets.token_urlsafe(32))
        self.algorithm = "HS256"
        self.access_token_expire = 3600      # 1 hour
        self.refresh_token_expire = 2592000  # 30 days
    
    def create_access_token(self, user_id: str, role: Role, email: str) -> str:
        """Generate access token (short-lived)"""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(seconds=self.access_token_expire)
        
        payload = {
            "sub": user_id,
            "email": email,
            "role": role.value,
            "iat": now,
            "exp": expire,
            "type": "access"
        }
        
        token = jwt.encode(payload, self.secret, algorithm=self.algorithm)
        log.info(f"✅ Access token created for {email} ({role.value})")
        return token
    
    def create_refresh_token(self, user_id: str) -> str:
        """Generate refresh token (long-lived)"""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(seconds=self.refresh_token_expire)
        
        payload = {
            "sub": user_id,
            "iat": now,
            "exp": expire,
            "type": "refresh",
            "jti": secrets.token_urlsafe(16)  # Token ID for revocation
        }
        
        token = jwt.encode(payload, self.secret, algorithm=self.algorithm)
        return token
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode token"""
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            log.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            log.warning(f"Invalid token: {e}")
            return None
    
    def create_api_key(self, name: str, vendor_id: str) -> Tuple[str, str]:
        """Create long-lived API key for external integrations"""
        key = f"naya_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        payload = {
            "vendor_id": vendor_id,
            "key_name": name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "type": "api_key"
        }
        
        return key, key_hash  # Return key once, store hash

# ═══════════════════════════════════════════════════════════════════════════
# 3. RBAC CONTROLLER
# ═══════════════════════════════════════════════════════════════════════════

class RBACController:
    """Role-based access control enforcement"""
    
    def __init__(self):
        self.user_roles: Dict[str, Role] = {}
        self.user_permissions: Dict[str, List[Permission]] = {}
    
    def assign_role(self, user_id: str, role: Role):
        """Assign role to user"""
        self.user_roles[user_id] = role
        self.user_permissions[user_id] = ROLE_PERMISSIONS[role]
        log.info(f"🔐 Role assigned: {user_id} → {role.value}")
    
    def has_permission(self, user_id: str, permission: Permission) -> bool:
        """Check if user has permission"""
        permissions = self.user_permissions.get(user_id, [])
        return permission in permissions
    
    def enforce(self, user_id: str, permission: Permission) -> bool:
        """Enforce permission - raise if denied"""
        if not self.has_permission(user_id, permission):
            log.warning(f"❌ Access denied: {user_id} for {permission.value}")
            raise PermissionError(f"Insufficient permissions for {permission.value}")
        return True

# ═══════════════════════════════════════════════════════════════════════════
# 4. AUDIT LOGGER
# ═══════════════════════════════════════════════════════════════════════════

class AuditEvent:
    """Single audit event"""
    def __init__(self, user_id: str, action: str, resource: str, 
                 status: str, details: Optional[Dict] = None):
        self.user_id = user_id
        self.action = action
        self.resource = resource
        self.status = status
        self.details = details or {}
        self.timestamp = datetime.now(timezone.utc)
        self.ip_address = None
        self.user_agent = None

class AuditLogger:
    """Comprehensive audit logging for compliance"""
    
    def __init__(self):
        self.events: List[AuditEvent] = []
        self.max_events = 100000
    
    def log_event(self, user_id: str, action: str, resource: str, 
                  status: str, details: Optional[Dict] = None) -> AuditEvent:
        """Log single event"""
        event = AuditEvent(user_id, action, resource, status, details)
        self.events.append(event)
        
        # Rotate if too many events
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]
        
        log.info(f"📝 AUDIT: {user_id} {action} {resource} [{status}]")
        return event
    
    def log_login(self, user_id: str, email: str, success: bool):
        self.log_event(user_id, "LOGIN", "auth", 
                      "success" if success else "failed",
                      {"email": email})
    
    def log_api_call(self, user_id: str, endpoint: str, method: str, 
                    status_code: int, response_time_ms: int):
        self.log_event(user_id, "API_CALL", endpoint,
                      "success" if 200 <= status_code < 300 else "error",
                      {"method": method, "status": status_code, 
                       "response_time_ms": response_time_ms})
    
    def log_data_access(self, user_id: str, resource_type: str, 
                       record_count: int):
        self.log_event(user_id, "DATA_ACCESS", resource_type, "success",
                      {"records_accessed": record_count})
    
    def log_privileged_action(self, user_id: str, action: str, 
                             target: str, details: Dict):
        self.log_event(user_id, f"PRIVILEGED_{action}", target, "executed",
                      details)
    
    def get_user_history(self, user_id: str, days: int = 30) -> List[Dict]:
        """Get audit history for user"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        user_events = [e for e in self.events 
                      if e.user_id == user_id and e.timestamp > cutoff]
        return [{
            "timestamp": e.timestamp.isoformat(),
            "action": e.action,
            "resource": e.resource,
            "status": e.status,
            "details": e.details
        } for e in user_events]
    
    def get_suspicious_activity(self, failed_login_threshold: int = 5) -> List[Dict]:
        """Detect suspicious patterns"""
        from collections import defaultdict
        failed_logins = defaultdict(int)
        
        for event in self.events:
            if event.action == "LOGIN" and event.status == "failed":
                failed_logins[event.user_id] += 1
        
        suspicious = []
        for user_id, count in failed_logins.items():
            if count >= failed_login_threshold:
                suspicious.append({
                    "user_id": user_id,
                    "failed_logins": count,
                    "severity": "HIGH" if count > 10 else "MEDIUM"
                })
        
        return suspicious

# ═══════════════════════════════════════════════════════════════════════════
# 5. REQUEST AUTHENTICATION MIDDLEWARE
# ═══════════════════════════════════════════════════════════════════════════

def require_auth(permissions: Optional[List[Permission]] = None):
    """Decorator to protect endpoints"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request=None, **kwargs):
            # Extract token from header
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                raise ValueError("Missing or invalid Authorization header")
            
            token = auth_header.split(" ")[1]
            payload = jwt_manager.verify_token(token)
            if not payload:
                raise ValueError("Invalid or expired token")
            
            user_id = payload.get("sub")
            
            # Check permissions if required
            if permissions:
                for perm in permissions:
                    rbac.enforce(user_id, perm)
            
            # Log API call
            audit.log_api_call(user_id, request.url.path, 
                             request.method, 200, 0)
            
            # Inject user_id into function
            kwargs["user_id"] = user_id
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# ═══════════════════════════════════════════════════════════════════════════
# 6. RATE LIMITING & DDoS PROTECTION
# ═══════════════════════════════════════════════════════════════════════════

class RateLimiter:
    """Prevent abuse and DDoS"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.limits = {
            Role.ADMIN: 10000,      # 10k req/hour
            Role.MANAGER: 5000,     # 5k req/hour
            Role.AGENT: 2000,       # 2k req/hour
            Role.ANALYST: 1000,
            Role.VENDOR: 500,
            Role.GUEST: 100
        }
    
    async def check_rate_limit(self, user_id: str, role: Role) -> Tuple[bool, int]:
        """Check if user exceeded rate limit"""
        limit = self.limits[role]
        
        if self.redis:
            key = f"ratelimit:{user_id}"
            current = await self.redis.incr(key)
            if current == 1:
                await self.redis.expire(key, 3600)
            
            if current > limit:
                log.warning(f"⚠️ Rate limit exceeded: {user_id}")
                return False, current
            
            return True, current
        
        return True, 0  # Fallback: no limiting

# ═══════════════════════════════════════════════════════════════════════════
# 7. UNIFIED SECURITY MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class SecurityManager:
    """Central security orchestration"""
    
    def __init__(self, redis_client=None):
        self.jwt = JWTManager()
        self.rbac = RBACController()
        self.audit = AuditLogger()
        self.rate_limiter = RateLimiter(redis_client)
    
    async def authenticate(self, email: str, password: str, stored_hash: Optional[str] = None, user_role: Optional[Role] = None) -> Optional[Dict]:
        """
        Authenticate user with bcrypt password verification.
        V19.3 FIX: Real bcrypt verification (plus de mock).

        Args:
            email: user email
            password: plaintext password (vérifié puis jeté)
            stored_hash: bcrypt hash from DB (passé depuis user repository)
            user_role: role from DB
        """
        # Import lazy pour éviter dépendance obligatoire au boot
        try:
            import bcrypt
        except ImportError:
            raise RuntimeError(
                "bcrypt requis pour authentification production. "
                "Installer: pip install bcrypt>=4.0.0"
            )

        # Production: vérifier avec bcrypt
        if stored_hash is None:
            # Pas d'utilisateur → log tentative + fail
            self.audit.log_login(
                hashlib.sha256(email.encode()).hexdigest()[:16],
                email, False
            )
            return None

        # bcrypt.checkpw résiste aux timing attacks
        try:
            if not bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                self.audit.log_login(
                    hashlib.sha256(email.encode()).hexdigest()[:16],
                    email, False
                )
                return None
        except (ValueError, TypeError) as e:
            # Hash malformé
            self.audit.log_login(
                hashlib.sha256(email.encode()).hexdigest()[:16],
                email, False
            )
            return None

        user_id = hashlib.sha256(email.encode()).hexdigest()[:16]
        role = user_role or Role.MANAGER

        access_token = self.jwt.create_access_token(user_id, role, email)
        refresh_token = self.jwt.create_refresh_token(user_id)

        self.audit.log_login(user_id, email, True)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user_id": user_id,
            "role": role.value,
            "expires_in": self.jwt.access_token_expire
        }

    @staticmethod
    def hash_password(password: str, rounds: int = 12) -> str:
        """
        Hash a password with bcrypt (pour registration).
        V19.3: rounds=12 recommandé production (plus lent mais plus sûr).
        """
        try:
            import bcrypt
        except ImportError:
            raise RuntimeError("bcrypt requis: pip install bcrypt>=4.0.0")
        return bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt(rounds=rounds)
        ).decode('utf-8')
    
    def get_audit_report(self, user_id: str) -> Dict:
        return {
            "user_history": self.audit.get_user_history(user_id),
            "suspicious_activity": self.audit.get_suspicious_activity()
        }

# ═══════════════════════════════════════════════════════════════════════════
# 8. SINGLETONS
# ═══════════════════════════════════════════════════════════════════════════

jwt_manager = JWTManager()
rbac = RBACController()
audit = AuditLogger()

def get_security_manager(redis_client=None) -> SecurityManager:
    return SecurityManager(redis_client)
