"""
Performance Monitoring and Analytics for Threadz Application
"""
import time
import psutil
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from dataclasses import dataclass
import json

from . import models
from .database import get_db
from .sentry_config import sentry_manager
from .config import settings

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    response_time: float
    memory_usage: float
    cpu_usage: float
    endpoint: str
    method: str
    status_code: int
    user_id: Optional[str] = None
    timestamp: datetime = None

class PerformanceMonitor:
    """Advanced performance monitoring system"""
    
    def __init__(self):
        self.metrics_buffer: List[PerformanceMetrics] = []
        self.buffer_size = 1000
        self.collection_interval = 60  # seconds
        self.alert_thresholds = {
            "response_time": 2.0,  # seconds
            "memory_usage": 80.0,   # percentage
            "cpu_usage": 80.0      # percentage
        }
        
        # Performance stats
        self.request_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
        self.slow_requests = []
        
    def record_request(
        self,
        request: Request,
        response_time: float,
        status_code: int,
        user_id: Optional[str] = None
    ):
        """Record a request for performance monitoring"""
        try:
            # Get system metrics
            memory_usage = psutil.virtual_memory().percent
            cpu_usage = psutil.cpu_percent()
            
            # Create metrics
            metrics = PerformanceMetrics(
                response_time=response_time,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                endpoint=request.url.path,
                method=request.method,
                status_code=status_code,
                user_id=user_id,
                timestamp=datetime.utcnow()
            )
            
            # Add to buffer
            self.metrics_buffer.append(metrics)
            
            # Update stats
            self.request_count += 1
            self.total_response_time += response_time
            
            if status_code >= 400:
                self.error_count += 1
            
            if response_time > self.alert_thresholds["response_time"]:
                self.slow_requests.append({
                    "endpoint": request.url.path,
                    "method": request.method,
                    "response_time": response_time,
                    "timestamp": datetime.utcnow(),
                    "user_id": user_id
                })
            
            # Check for alerts
            self._check_alerts(metrics)
            
            # Maintain buffer size
            if len(self.metrics_buffer) > self.buffer_size:
                self.metrics_buffer = self.metrics_buffer[-self.buffer_size:]
                
        except Exception as e:
            sentry_manager.capture_exception(e, {"action": "record_request"})
    
    def _check_alerts(self, metrics: PerformanceMetrics):
        """Check for performance alerts"""
        alerts = []
        
        if metrics.response_time > self.alert_thresholds["response_time"]:
            alerts.append({
                "type": "slow_response",
                "value": metrics.response_time,
                "threshold": self.alert_thresholds["response_time"],
                "endpoint": metrics.endpoint
            })
        
        if metrics.memory_usage > self.alert_thresholds["memory_usage"]:
            alerts.append({
                "type": "high_memory",
                "value": metrics.memory_usage,
                "threshold": self.alert_thresholds["memory_usage"]
            })
        
        if metrics.cpu_usage > self.alert_thresholds["cpu_usage"]:
            alerts.append({
                "type": "high_cpu",
                "value": metrics.cpu_usage,
                "threshold": self.alert_thresholds["cpu_usage"]
            })
        
        # Send alerts to Sentry
        for alert in alerts:
            sentry_manager.add_tag("performance_alert", alert["type"])
            sentry_manager.add_extra("alert_data", alert)
            
            if alert["type"] == "slow_response":
                sentry_manager.capture_message(
                    f"Slow response detected: {alert['value']:.2f}s for {alert['endpoint']}",
                    level="warning"
                )
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        try:
            # System metrics
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=1)
            disk = psutil.disk_usage('/')
            
            # Request metrics
            avg_response_time = self.total_response_time / max(self.request_count, 1)
            error_rate = (self.error_count / max(self.request_count, 1)) * 100
            
            return {
                "system": {
                    "memory_usage": memory.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "cpu_usage": cpu,
                    "disk_usage": disk.percent,
                    "disk_free_gb": disk.free / (1024**3)
                },
                "requests": {
                    "total_requests": self.request_count,
                    "error_count": self.error_count,
                    "error_rate": error_rate,
                    "avg_response_time": avg_response_time,
                    "slow_requests_count": len(self.slow_requests)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            sentry_manager.capture_exception(e, {"action": "get_current_metrics"})
            return {}
    
    def get_endpoint_performance(self, minutes: int = 60) -> Dict[str, Any]:
        """Get performance metrics by endpoint"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
            
            # Filter metrics by time
            recent_metrics = [
                m for m in self.metrics_buffer 
                if m.timestamp and m.timestamp >= cutoff_time
            ]
            
            # Group by endpoint
            endpoint_stats = {}
            for metric in recent_metrics:
                endpoint = metric.endpoint
                if endpoint not in endpoint_stats:
                    endpoint_stats[endpoint] = {
                        "count": 0,
                        "total_response_time": 0.0,
                        "error_count": 0,
                        "avg_response_time": 0.0,
                        "error_rate": 0.0,
                        "max_response_time": 0.0,
                        "min_response_time": float('inf')
                    }
                
                stats = endpoint_stats[endpoint]
                stats["count"] += 1
                stats["total_response_time"] += metric.response_time
                stats["max_response_time"] = max(stats["max_response_time"], metric.response_time)
                stats["min_response_time"] = min(stats["min_response_time"], metric.response_time)
                
                if metric.status_code >= 400:
                    stats["error_count"] += 1
            
            # Calculate averages and rates
            for endpoint, stats in endpoint_stats.items():
                if stats["count"] > 0:
                    stats["avg_response_time"] = stats["total_response_time"] / stats["count"]
                    stats["error_rate"] = (stats["error_count"] / stats["count"]) * 100
                    if stats["min_response_time"] == float('inf'):
                        stats["min_response_time"] = 0.0
            
            return {
                "endpoint_stats": endpoint_stats,
                "period_minutes": minutes,
                "total_requests": len(recent_metrics)
            }
            
        except Exception as e:
            sentry_manager.capture_exception(e, {"action": "get_endpoint_performance"})
            return {}
    
    def get_user_performance(self, user_id: str, minutes: int = 60) -> Dict[str, Any]:
        """Get performance metrics for a specific user"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
            
            # Filter metrics by user and time
            user_metrics = [
                m for m in self.metrics_buffer 
                if m.user_id == user_id and m.timestamp and m.timestamp >= cutoff_time
            ]
            
            if not user_metrics:
                return {
                    "user_id": user_id,
                    "period_minutes": minutes,
                    "total_requests": 0,
                    "avg_response_time": 0.0,
                    "error_count": 0,
                    "error_rate": 0.0
                }
            
            total_response_time = sum(m.response_time for m in user_metrics)
            error_count = sum(1 for m in user_metrics if m.status_code >= 400)
            avg_response_time = total_response_time / len(user_metrics)
            error_rate = (error_count / len(user_metrics)) * 100
            
            return {
                "user_id": user_id,
                "period_minutes": minutes,
                "total_requests": len(user_metrics),
                "avg_response_time": avg_response_time,
                "error_count": error_count,
                "error_rate": error_rate,
                "endpoints": list(set(m.endpoint for m in user_metrics))
            }
            
        except Exception as e:
            sentry_manager.capture_exception(e, {"action": "get_user_performance"})
            return {}
    
    async def get_database_performance(self, db: AsyncSession) -> Dict[str, Any]:
        """Get database performance metrics"""
        try:
            # Get table sizes
            table_stats = {}
            
            # Users table
            users_result = await db.execute(select(func.count(models.User.user_id)))
            table_stats["users"] = users_result.scalar() or 0
            
            # Designs table
            designs_result = await db.execute(select(func.count(models.Design.design_id)))
            table_stats["designs"] = designs_result.scalar() or 0
            
            # Orders table
            orders_result = await db.execute(select(func.count(models.Order.order_id)))
            table_stats["orders"] = orders_result.scalar() or 0
            
            # Products table
            products_result = await db.execute(select(func.count(models.Product.product_id)))
            table_stats["products"] = products_result.scalar() or 0
            
            return {
                "table_counts": table_stats,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            sentry_manager.capture_exception(e, {"action": "get_database_performance"})
            return {}
    
    def get_slow_requests(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get list of slow requests"""
        return sorted(
            self.slow_requests,
            key=lambda x: x["response_time"],
            reverse=True
        )[:limit]
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics_buffer.clear()
        self.request_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
        self.slow_requests.clear()

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Middleware for performance monitoring
async def performance_middleware(request: Request, call_next):
    """Middleware to monitor request performance"""
    start_time = time.time()
    
    # Get user ID from request (if available)
    user_id = None
    if hasattr(request.state, 'user'):
        user_id = request.state.user.user_id
    
    # Process request
    response = await call_next(request)
    
    # Calculate response time
    response_time = time.time() - start_time
    
    # Record metrics
    performance_monitor.record_request(
        request=request,
        response_time=response_time,
        status_code=response.status_code,
        user_id=user_id
    )
    
    # Add performance headers
    response.headers["X-Response-Time"] = f"{response_time:.3f}s"
    
    return response

# Performance monitoring endpoints
async def get_performance_stats(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get comprehensive performance statistics"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        current_metrics = performance_monitor.get_current_metrics()
        endpoint_performance = performance_monitor.get_endpoint_performance()
        database_performance = await performance_monitor.get_database_performance(db)
        slow_requests = performance_monitor.get_slow_requests(20)
        
        return {
            "current_metrics": current_metrics,
            "endpoint_performance": endpoint_performance,
            "database_performance": database_performance,
            "slow_requests": slow_requests
        }
        
    except Exception as e:
        sentry_manager.capture_exception(e, {"action": "get_performance_stats"})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch performance stats"
        )

async def get_user_performance_stats(
    user_id: str,
    minutes: int = 60,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get performance statistics for a specific user"""
    # Users can only see their own stats, admins can see any
    if current_user.user_id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        user_performance = performance_monitor.get_user_performance(user_id, minutes)
        return user_performance
        
    except Exception as e:
        sentry_manager.capture_exception(e, {"action": "get_user_performance_stats"})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user performance stats"
        )

# Background task to clean up old metrics
async def cleanup_old_metrics():
    """Clean up old performance metrics"""
    while True:
        try:
            # Keep only last 24 hours of metrics
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            performance_monitor.metrics_buffer = [
                m for m in performance_monitor.metrics_buffer 
                if m.timestamp and m.timestamp >= cutoff_time
            ]
            
            # Keep only last 100 slow requests
            if len(performance_monitor.slow_requests) > 100:
                performance_monitor.slow_requests = performance_monitor.slow_requests[-100:]
            
            await asyncio.sleep(3600)  # Run every hour
            
        except Exception as e:
            sentry_manager.capture_exception(e, {"action": "cleanup_old_metrics"})
            await asyncio.sleep(300)  # Retry after 5 minutes
