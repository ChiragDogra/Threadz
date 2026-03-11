"""
Analytics Dashboard and Data Analysis for Threadz Application
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, and_, or_, extract
from fastapi import HTTPException, status, Query
from pydantic import BaseModel
from enum import Enum

from . import models, auth
from .database import get_db
from .sentry_config import sentry_manager

class AnalyticsPeriod(str, Enum):
    """Analytics time periods"""
    TODAY = "today"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    ALL_TIME = "all_time"

class MetricType(str, Enum):
    """Types of analytics metrics"""
    USERS = "users"
    DESIGNS = "designs"
    ORDERS = "orders"
    REVENUE = "revenue"
    ENGAGEMENT = "engagement"
    PERFORMANCE = "performance"

# Pydantic models
class AnalyticsOverview(BaseModel):
    total_users: int
    active_users: int
    new_users: int
    total_designs: int
    public_designs: int
    total_orders: int
    total_revenue: float
    avg_order_value: float
    conversion_rate: float

class TrendData(BaseModel):
    date: str
    value: float
    change_percent: Optional[float]

class UserAnalytics(BaseModel):
    total_users: int
    new_users: int
    active_users: int
    verified_users: int
    user_growth_rate: float
    retention_rate: float
    demographics: Dict[str, Any]

class DesignAnalytics(BaseModel):
    total_designs: int
    public_designs: int
    ai_generated: int
    uploaded: int
    avg_designs_per_user: float
    popular_categories: List[Dict[str, Any]]
    design_trends: List[TrendData]

class OrderAnalytics(BaseModel):
    total_orders: int
    completed_orders: int
    pending_orders: int
    total_revenue: float
    avg_order_value: float
    revenue_trends: List[TrendData]
    popular_products: List[Dict[str, Any]]

class EngagementAnalytics(BaseModel):
    avg_session_duration: float
    page_views: int
    unique_visitors: int
    bounce_rate: float
    engagement_score: float
    top_pages: List[Dict[str, Any]]

class AnalyticsService:
    """Comprehensive analytics service for Threadz"""
    
    def __init__(self):
        self.cache_ttl = 300  # 5 minutes
        self.cache = {}
    
    def _get_date_range(self, period: AnalyticsPeriod) -> tuple:
        """Get date range for analytics period"""
        now = datetime.utcnow()
        
        if period == AnalyticsPeriod.TODAY:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == AnalyticsPeriod.WEEK:
            start = now - timedelta(days=7)
        elif period == AnalyticsPeriod.MONTH:
            start = now - timedelta(days=30)
        elif period == AnalyticsPeriod.QUARTER:
            start = now - timedelta(days=90)
        elif period == AnalyticsPeriod.YEAR:
            start = now - timedelta(days=365)
        else:  # ALL_TIME
            start = datetime(2020, 1, 1)  # App launch date
        
        return start, now
    
    async def get_overview(
        self,
        db: AsyncSession,
        period: AnalyticsPeriod = AnalyticsPeriod.MONTH
    ) -> AnalyticsOverview:
        """Get analytics overview"""
        try:
            start_date, end_date = self._get_date_range(period)
            
            # User metrics
            total_users_result = await db.execute(select(func.count(models.User.user_id)))
            total_users = total_users_result.scalar() or 0
            
            new_users_result = await db.execute(
                select(func.count(models.User.user_id))
                .where(models.User.created_at >= start_date)
            )
            new_users = new_users_result.scalar() or 0
            
            active_users_result = await db.execute(
                select(func.count(models.User.user_id))
                .where(models.User.last_login >= start_date)
            )
            active_users = active_users_result.scalar() or 0
            
            # Design metrics
            total_designs_result = await db.execute(select(func.count(models.Design.design_id)))
            total_designs = total_designs_result.scalar() or 0
            
            public_designs_result = await db.execute(
                select(func.count(models.Design.design_id))
                .where(models.Design.is_public == True)
            )
            public_designs = public_designs_result.scalar() or 0
            
            # Order metrics
            total_orders_result = await db.execute(
                select(func.count(models.Order.order_id))
                .where(models.Order.created_at >= start_date)
            )
            total_orders = total_orders_result.scalar() or 0
            
            revenue_result = await db.execute(
                select(func.coalesce(func.sum(models.Order.total_amount), 0))
                .where(models.Order.created_at >= start_date, models.Order.status == "Paid")
            )
            total_revenue = float(revenue_result.scalar() or 0)
            
            avg_order_value = total_revenue / max(total_orders, 1)
            
            # Conversion rate (users who made at least one order)
            if total_users > 0:
                users_with_orders_result = await db.execute(
                    select(func.count(func.distinct(models.Order.user_id)))
                    .where(models.Order.created_at >= start_date)
                )
                users_with_orders = users_with_orders_result.scalar() or 0
                conversion_rate = (users_with_orders / total_users) * 100
            else:
                conversion_rate = 0
            
            return AnalyticsOverview(
                total_users=total_users,
                active_users=active_users,
                new_users=new_users,
                total_designs=total_designs,
                public_designs=public_designs,
                total_orders=total_orders,
                total_revenue=total_revenue,
                avg_order_value=avg_order_value,
                conversion_rate=conversion_rate
            )
            
        except Exception as e:
            sentry_manager.capture_exception(e, {"action": "get_overview"})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch analytics overview"
            )
    
    async def get_user_analytics(
        self,
        db: AsyncSession,
        period: AnalyticsPeriod = AnalyticsPeriod.MONTH
    ) -> UserAnalytics:
        """Get user analytics"""
        try:
            start_date, end_date = self._get_date_range(period)
            
            # Basic user metrics
            total_users_result = await db.execute(select(func.count(models.User.user_id)))
            total_users = total_users_result.scalar() or 0
            
            new_users_result = await db.execute(
                select(func.count(models.User.user_id))
                .where(models.User.created_at >= start_date)
            )
            new_users = new_users_result.scalar() or 0
            
            active_users_result = await db.execute(
                select(func.count(models.User.user_id))
                .where(models.User.last_login >= start_date)
            )
            active_users = active_users_result.scalar() or 0
            
            verified_users_result = await db.execute(
                select(func.count(models.User.user_id))
                .where(models.User.is_email_verified == True)
            )
            verified_users = verified_users_result.scalar() or 0
            
            # Growth rate
            if period != AnalyticsPeriod.ALL_TIME:
                prev_start = start_date - (end_date - start_date)
                prev_new_users_result = await db.execute(
                    select(func.count(models.User.user_id))
                    .where(models.User.created_at.between(prev_start, start_date))
                )
                prev_new_users = prev_new_users_result.scalar() or 0
                user_growth_rate = ((new_users - prev_new_users) / max(prev_new_users, 1)) * 100
            else:
                user_growth_rate = 0
            
            # Retention rate (simplified - users who returned after 7 days)
            retention_cutoff = end_date - timedelta(days=7)
            retained_users_result = await db.execute(
                select(func.count(func.distinct(models.User.user_id)))
                .where(
                    models.User.created_at <= retention_cutoff,
                    models.User.last_login >= retention_cutoff
                )
            )
            retained_users = retained_users_result.scalar() or 0
            
            eligible_users_result = await db.execute(
                select(func.count(models.User.user_id))
                .where(models.User.created_at <= retention_cutoff)
            )
            eligible_users = eligible_users_result.scalar() or 0
            
            retention_rate = (retained_users / max(eligible_users, 1)) * 100
            
            # Demographics (mock - would need additional fields in User model)
            demographics = {
                "signup_sources": ["direct", "social", "referral"],
                "device_types": ["desktop", "mobile", "tablet"],
                "locations": ["India", "USA", "UK", "Other"]
            }
            
            return UserAnalytics(
                total_users=total_users,
                new_users=new_users,
                active_users=active_users,
                verified_users=verified_users,
                user_growth_rate=user_growth_rate,
                retention_rate=retention_rate,
                demographics=demographics
            )
            
        except Exception as e:
            sentry_manager.capture_exception(e, {"action": "get_user_analytics"})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch user analytics"
            )
    
    async def get_design_analytics(
        self,
        db: AsyncSession,
        period: AnalyticsPeriod = AnalyticsPeriod.MONTH
    ) -> DesignAnalytics:
        """Get design analytics"""
        try:
            start_date, end_date = self._get_date_range(period)
            
            # Basic design metrics
            total_designs_result = await db.execute(
                select(func.count(models.Design.design_id))
                .where(models.Design.created_at >= start_date)
            )
            total_designs = total_designs_result.scalar() or 0
            
            public_designs_result = await db.execute(
                select(func.count(models.Design.design_id))
                .where(
                    models.Design.created_at >= start_date,
                    models.Design.is_public == True
                )
            )
            public_designs = public_designs_result.scalar() or 0
            
            ai_generated_result = await db.execute(
                select(func.count(models.Design.design_id))
                .where(
                    models.Design.created_at >= start_date,
                    models.Design.design_source == "ai"
                )
            )
            ai_generated = ai_generated_result.scalar() or 0
            
            uploaded_result = await db.execute(
                select(func.count(models.Design.design_id))
                .where(
                    models.Design.created_at >= start_date,
                    models.Design.design_source == "upload"
                )
            )
            uploaded = uploaded_result.scalar() or 0
            
            # Avg designs per user
            active_users_result = await db.execute(
                select(func.count(models.User.user_id))
                .where(models.User.created_at >= start_date)
            )
            active_users = active_users_result.scalar() or 1
            avg_designs_per_user = total_designs / active_users
            
            # Popular categories (mock - would need category field)
            popular_categories = [
                {"category": "t-shirt", "count": 150},
                {"category": "hoodie", "count": 85},
                {"category": "phone-case", "count": 62},
                {"category": "poster", "count": 45}
            ]
            
            # Design trends (daily counts)
            design_trends = []
            for i in range(30):
                date = (end_date - timedelta(days=i)).date()
                designs_on_date_result = await db.execute(
                    select(func.count(models.Design.design_id))
                    .where(
                        func.date(models.Design.created_at) == date
                    )
                )
                count = designs_on_date_result.scalar() or 0
                design_trends.append(TrendData(date=str(date), value=count))
            
            design_trends.reverse()
            
            return DesignAnalytics(
                total_designs=total_designs,
                public_designs=public_designs,
                ai_generated=ai_generated,
                uploaded=uploaded,
                avg_designs_per_user=avg_designs_per_user,
                popular_categories=popular_categories,
                design_trends=design_trends
            )
            
        except Exception as e:
            sentry_manager.capture_exception(e, {"action": "get_design_analytics"})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch design analytics"
            )
    
    async def get_order_analytics(
        self,
        db: AsyncSession,
        period: AnalyticsPeriod = AnalyticsPeriod.MONTH
    ) -> OrderAnalytics:
        """Get order analytics"""
        try:
            start_date, end_date = self._get_date_range(period)
            
            # Basic order metrics
            total_orders_result = await db.execute(
                select(func.count(models.Order.order_id))
                .where(models.Order.created_at >= start_date)
            )
            total_orders = total_orders_result.scalar() or 0
            
            completed_orders_result = await db.execute(
                select(func.count(models.Order.order_id))
                .where(
                    models.Order.created_at >= start_date,
                    models.Order.status == "Completed"
                )
            )
            completed_orders = completed_orders_result.scalar() or 0
            
            pending_orders_result = await db.execute(
                select(func.count(models.Order.order_id))
                .where(
                    models.Order.created_at >= start_date,
                    models.Order.status == "Pending"
                )
            )
            pending_orders = pending_orders_result.scalar() or 0
            
            # Revenue metrics
            revenue_result = await db.execute(
                select(func.coalesce(func.sum(models.Order.total_amount), 0))
                .where(
                    models.Order.created_at >= start_date,
                    models.Order.status == "Paid"
                )
            )
            total_revenue = float(revenue_result.scalar() or 0)
            
            avg_order_value = total_revenue / max(total_orders, 1)
            
            # Revenue trends
            revenue_trends = []
            for i in range(30):
                date = (end_date - timedelta(days=i)).date()
                revenue_on_date_result = await db.execute(
                    select(func.coalesce(func.sum(models.Order.total_amount), 0))
                    .where(
                        func.date(models.Order.created_at) == date,
                        models.Order.status == "Paid"
                    )
                )
                revenue = float(revenue_on_date_result.scalar() or 0)
                revenue_trends.append(TrendData(date=str(date), value=revenue))
            
            revenue_trends.reverse()
            
            # Popular products (mock - would need product association)
            popular_products = [
                {"product": "Custom T-Shirt", "orders": 125, "revenue": 7500.0},
                {"product": "Custom Hoodie", "orders": 85, "revenue": 6800.0},
                {"product": "Phone Case", "orders": 62, "revenue": 1860.0}
            ]
            
            return OrderAnalytics(
                total_orders=total_orders,
                completed_orders=completed_orders,
                pending_orders=pending_orders,
                total_revenue=total_revenue,
                avg_order_value=avg_order_value,
                revenue_trends=revenue_trends,
                popular_products=popular_products
            )
            
        except Exception as e:
            sentry_manager.capture_exception(e, {"action": "get_order_analytics"})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch order analytics"
            )
    
    async def get_engagement_analytics(
        self,
        db: AsyncSession,
        period: AnalyticsPeriod = AnalyticsPeriod.MONTH
    ) -> EngagementAnalytics:
        """Get engagement analytics"""
        try:
            # Mock engagement data - would integrate with analytics service
            return EngagementAnalytics(
                avg_session_duration=245.5,  # seconds
                page_views=15420,
                unique_visitors=3240,
                bounce_rate=32.5,  # percentage
                engagement_score=78.2,  # out of 100
                top_pages=[
                    {"page": "/designs", "views": 5420, "avg_duration": 180.5},
                    {"page": "/", "views": 3200, "avg_duration": 120.0},
                    {"page": "/products", "views": 2800, "avg_duration": 200.5},
                    {"page": "/designs/create", "views": 2100, "avg_duration": 420.0}
                ]
            )
            
        except Exception as e:
            sentry_manager.capture_exception(e, {"action": "get_engagement_analytics"})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch engagement analytics"
            )
    
    async def export_analytics(
        self,
        db: AsyncSession,
        format: str = "json",
        period: AnalyticsPeriod = AnalyticsPeriod.MONTH
    ) -> Dict[str, Any]:
        """Export analytics data"""
        try:
            # Get all analytics data
            overview = await self.get_overview(db, period)
            user_analytics = await self.get_user_analytics(db, period)
            design_analytics = await self.get_design_analytics(db, period)
            order_analytics = await self.get_order_analytics(db, period)
            engagement_analytics = await self.get_engagement_analytics(db, period)
            
            export_data = {
                "period": period.value,
                "generated_at": datetime.utcnow().isoformat(),
                "overview": overview.dict(),
                "users": user_analytics.dict(),
                "designs": design_analytics.dict(),
                "orders": order_analytics.dict(),
                "engagement": engagement_analytics.dict()
            }
            
            if format == "csv":
                # Convert to CSV format (simplified)
                return {"format": "csv", "data": "CSV data would be generated here"}
            
            return {"format": "json", "data": export_data}
            
        except Exception as e:
            sentry_manager.capture_exception(e, {"action": "export_analytics"})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to export analytics"
            )

# Global analytics service instance
analytics_service = AnalyticsService()
