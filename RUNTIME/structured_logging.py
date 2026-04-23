"""
NAYA SUPREME - Structured Logging Module
═════════════════════════════════════════════════════════════════════════════════

Logging structuré (JSON) pour production.
Sortie fichier + console avec rotation automatique.
"""

import logging
import logging.handlers
import json
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import sys

# ════════════════════════════════════════════════════════════════════════════════
# CUSTOM JSON FORMATTER
# ════════════════════════════════════════════════════════════════════════════════

class JSONFormatter(logging.Formatter):
    """Custom formatter pour logs en JSON structuré"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.now(timezone.utc).isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'custom_fields'):
            log_data.update(record.custom_fields)
        
        return json.dumps(log_data, default=str)


# ════════════════════════════════════════════════════════════════════════════════
# SETUP LOGGING
# ════════════════════════════════════════════════════════════════════════════════

def setup_logging(
    name: str,
    log_level: str = "INFO",
    log_dir: str = "./logs",
    enable_file: bool = True,
    enable_console: bool = True,
    enable_json: bool = True,
) -> logging.Logger:
    """
    Setup complète du logging structuré
    
    Args:
        name: Nom du logger
        log_level: Niveau de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Répertoire des logs
        enable_file: Activer logs dans fichier
        enable_console: Activer logs en console
        enable_json: Utiliser format JSON
    
    Returns:
        Logger configuré
    """
    
    # Créer le logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Créer le répertoire si nécessaire
    if enable_file and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Formatter
    if enable_json:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '[%(asctime)s] [%(name)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    if enable_file:
        log_file = os.path.join(log_dir, f"{name}.log")
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=100 * 1024 * 1024,  # 100 MB
            backupCount=10
        )
        file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# ════════════════════════════════════════════════════════════════════════════════
# CUSTOM LOGGING FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════════

def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    **context
):
    """
    Log avec contexte structuré
    
    Args:
        logger: Logger instance
        level: Log level (INFO, WARNING, ERROR, etc)
        message: Message de log
        **context: Champs contexte supplémentaires
    """
    
    log_method = getattr(logger, level.lower(), logger.info)
    
    # Créer un enregistrement custom
    record = logger.makeRecord(
        logger.name,
        getattr(logging, level.upper()),
        "",
        0,
        message,
        (),
        None
    )
    
    # Ajouter les champs contexte
    record.custom_fields = context
    
    log_method(message, extra={'custom_fields': context})


def log_api_call(
    logger: logging.Logger,
    method: str,
    endpoint: str,
    status_code: int,
    duration_ms: float,
    **extra
):
    """Log d'appel API"""
    log_with_context(
        logger,
        'INFO',
        f'API: {method} {endpoint}',
        method=method,
        endpoint=endpoint,
        status_code=status_code,
        duration_ms=duration_ms,
        **extra
    )


def log_business_event(
    logger: logging.Logger,
    event_type: str,
    business_id: str,
    **details
):
    """Log d'événement métier"""
    log_with_context(
        logger,
        'INFO',
        f'Business Event: {event_type}',
        event_type=event_type,
        business_id=business_id,
        **details
    )


def log_error_with_context(
    logger: logging.Logger,
    error: Exception,
    context: str = "",
    **extra
):
    """Log d'erreur avec contexte"""
    log_with_context(
        logger,
        'ERROR',
        f'Error: {str(error)}',
        error_type=type(error).__name__,
        error_message=str(error),
        context=context,
        **extra
    )


# ════════════════════════════════════════════════════════════════════════════════
# METRICS LOGGING
# ════════════════════════════════════════════════════════════════════════════════

def log_performance_metrics(
    logger: logging.Logger,
    operation: str,
    duration_ms: float,
    success: bool = True,
    **metrics
):
    """Log de performance"""
    level = 'INFO' if success else 'WARNING'
    log_with_context(
        logger,
        level,
        f'Performance: {operation}',
        operation=operation,
        duration_ms=duration_ms,
        success=success,
        **metrics
    )


def log_business_metrics(
    logger: logging.Logger,
    metric_name: str,
    value: float,
    unit: str = "",
    **tags
):
    """Log de métriques métier"""
    log_with_context(
        logger,
        'INFO',
        f'Metric: {metric_name}',
        metric_name=metric_name,
        value=value,
        unit=unit,
        **tags
    )


# ════════════════════════════════════════════════════════════════════════════════
# GLOBAL LOGGER SETUP
# ════════════════════════════════════════════════════════════════════════════════

def initialize_logging_system(log_level: str = "INFO", log_dir: str = "./logs"):
    """Initialiser le système de logging global"""
    
    # Main app logger
    app_logger = setup_logging(
        "naya",
        log_level=log_level,
        log_dir=log_dir,
        enable_json=True
    )
    
    # Sub-module loggers
    api_logger = setup_logging(
        "naya.api",
        log_level=log_level,
        log_dir=log_dir,
        enable_json=True
    )
    
    db_logger = setup_logging(
        "naya.db",
        log_level=log_level,
        log_dir=log_dir,
        enable_json=True
    )
    
    cache_logger = setup_logging(
        "naya.cache",
        log_level=log_level,
        log_dir=log_dir,
        enable_json=True
    )
    
    return {
        'app': app_logger,
        'api': api_logger,
        'db': db_logger,
        'cache': cache_logger,
    }
