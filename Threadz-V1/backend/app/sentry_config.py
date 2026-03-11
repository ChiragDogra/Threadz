"""
Sentry Error Tracking Configuration for Threadz Application
"""
import os
import logging
from typing import Optional
from sentry_sdk import init, configure_scope, capture_exception, capture_message
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from .config import settings

class SentryManager:
    """Manages Sentry error tracking and monitoring"""
    
    def __init__(self):
        self.enabled = False
        self.dsn = settings.SENTRY_DSN
        self.environment = settings.ENVIRONMENT
        self.release = settings.VERSION
        
        if self.dsn and self.environment != "development":
            self._initialize_sentry()
    
    def _initialize_sentry(self):
        """Initialize Sentry SDK with appropriate integrations"""
        try:
            # Configure logging integration
            logging_integration = LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR
            )
            
            # Initialize Sentry
            init(
                dsn=self.dsn,
                integrations=[
                    FastApiIntegration(auto_enabling_integrations=False),
                    SqlalchemyIntegration(),
                    RedisIntegration(),
                    logging_integration,
                ],
                environment=self.environment,
                release=self.release,
                traces_sample_rate=0.1 if self.environment == "production" else 1.0,
                send_default_pii=False,
                before_send=self._before_send,
                before_breadcrumb=self._before_breadcrumb
            )
            
            self.enabled = True
            print(f"✅ Sentry initialized for {self.environment} environment")
            
        except Exception as e:
            print(f"❌ Failed to initialize Sentry: {e}")
    
    def _before_send(self, event, hint):
        """Filter events before sending to Sentry"""
        # Filter out sensitive data
        if event.get("request", {}).get("headers"):
            headers = event["request"]["headers"]
            # Remove sensitive headers
            sensitive_headers = ["authorization", "cookie", "x-api-key"]
            event["request"]["headers"] = {
                k: v for k, v in headers.items() 
                if k.lower() not in sensitive_headers
            }
        
        # Add custom context
        with configure_scope() as scope:
            scope.set_tag("service", "threadz-api")
            scope.set_tag("environment", self.environment)
            scope.set_extra("app_version", self.release)
        
        return event
    
    def _before_breadcrumb(self, breadcrumb, hint):
        """Filter breadcrumbs before sending to Sentry"""
        # Filter out sensitive breadcrumb data
        if breadcrumb.get("category") == "http":
            if breadcrumb.get("data", {}).get("url"):
                # Remove query parameters from URLs
                url = breadcrumb["data"]["url"]
                if "?" in url:
                    breadcrumb["data"]["url"] = url.split("?")[0]
        
        return breadcrumb
    
    def capture_exception(self, exception, extra=None):
        """Capture exception with additional context"""
        if not self.enabled:
            return
        
        with configure_scope() as scope:
            if extra:
                for key, value in extra.items():
                    scope.set_extra(key, value)
            
            scope.set_tag("error_type", type(exception).__name__)
        
        capture_exception(exception)
    
    def capture_message(self, message, level="info"):
        """Capture a message event"""
        if not self.enabled:
            return
        
        capture_message(message, level=level)
    
    def set_user_context(self, user_id=None, email=None, username=None):
        """Set user context for error tracking"""
        if not self.enabled:
            return
        
        with configure_scope() as scope:
            scope.set_user({
                "id": user_id,
                "email": email,
                "username": username
            })
    
    def add_tag(self, key, value):
        """Add a tag to the current scope"""
        if not self.enabled:
            return
        
        with configure_scope() as scope:
            scope.set_tag(key, value)
    
    def add_extra(self, key, value):
        """Add extra data to the current scope"""
        if not self.enabled:
            return
        
        with configure_scope() as scope:
            scope.set_extra(key, value)

# Global Sentry manager instance
sentry_manager = SentryManager()

# Decorator for automatic error tracking
def track_errors(operation_name=None):
    """Decorator to automatically track function errors"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Add operation context
                extra = {
                    "operation": operation_name or func.__name__,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys()) if kwargs else []
                }
                sentry_manager.capture_exception(e, extra)
                raise
        return wrapper
    return decorator

# Context manager for operation tracking
class OperationTracker:
    """Context manager for tracking operations"""
    
    def __init__(self, operation_name, **extra):
        self.operation_name = operation_name
        self.extra = extra
    
    def __enter__(self):
        sentry_manager.add_tag("operation", self.operation_name)
        for key, value in self.extra.items():
            sentry_manager.add_extra(key, value)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            sentry_manager.capture_exception(exc_val, {
                "operation": self.operation_name,
                **self.extra
            })
        return False  # Don't suppress exceptions
