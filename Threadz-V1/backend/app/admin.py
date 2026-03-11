"""
Admin Dashboard API for Threadz Application
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, desc, and_, or_
from pydantic import BaseModel

from . import models, auth
from .database import get_db
from .security_hardening import validate_secure_input
from .sentry_config import sentry_manager

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

# Pydantic models for admin responses
class UserStats(BaseModel):
    total_users: int
    active_users: int
    new_users_today: int
    new_users_week: int
    verified_users: int

class DesignStats(BaseModel):
    total_designs: int
    public_designs: int
    ai_generated_designs: int
    uploaded_designs: int
    designs_today: int

class OrderStats(BaseModel):
    total_orders: int
    orders_today: int
    orders_week: int
    total_revenue: float
    revenue_today: float
    revenue_week: float
    pending_orders: int
    completed_orders: int

class SystemStats(BaseModel):
    user_stats: UserStats
    design_stats: DesignStats
    order_stats: OrderStats
    storage_used_mb: float
    ai_generations_today: int

class AdminUserResponse(BaseModel):
    user_id: str
    email: str
    full_name: Optional[str]
    is_email_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    design_count: int
    order_count: int
    total_spent: float
    status: str

class AdminDesignResponse(BaseModel):
    design_id: str
    design_name: str
    user_email: str
    design_source: str
    is_public: bool
    created_at: datetime
    status: str
    moderation_status: str
    reports_count: int

class AdminOrderResponse(BaseModel):
    order_id: str
    user_email: str
    total_amount: float
    status: str
    created_at: str
    payment_status: str
    items_count: int

def require_admin(current_user: models.User = Depends(auth.get_current_user)):
    """Require admin role for admin endpoints"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

@router.get("/stats", response_model=SystemStats)
async def get_system_stats(
    db: AsyncSession = Depends(get_db),
    admin_user: models.User = Depends(require_admin)
):
    """Get comprehensive system statistics"""
    try:
        # User statistics
        total_users_result = await db.execute(select(func.count(models.User.user_id)))
        total_users = total_users_result.scalar() or 0
        
        active_users_result = await db.execute(
            select(func.count(models.User.user_id))
            .where(models.User.last_login >= datetime.utcnow() - timedelta(days=30))
        )
        active_users = active_users_result.scalar() or 0
        
        new_users_today_result = await db.execute(
            select(func.count(models.User.user_id))
            .where(models.User.created_at >= datetime.utcnow().date())
        )
        new_users_today = new_users_today_result.scalar() or 0
        
        new_users_week_result = await db.execute(
            select(func.count(models.User.user_id))
            .where(models.User.created_at >= datetime.utcnow() - timedelta(days=7))
        )
        new_users_week = new_users_week_result.scalar() or 0
        
        verified_users_result = await db.execute(
            select(func.count(models.User.user_id))
            .where(models.User.is_email_verified == True)
        )
        verified_users = verified_users_result.scalar() or 0
        
        # Design statistics
        total_designs_result = await db.execute(select(func.count(models.Design.design_id)))
        total_designs = total_designs_result.scalar() or 0
        
        public_designs_result = await db.execute(
            select(func.count(models.Design.design_id))
            .where(models.Design.is_public == True)
        )
        public_designs = public_designs_result.scalar() or 0
        
        ai_generated_designs_result = await db.execute(
            select(func.count(models.Design.design_id))
            .where(models.Design.design_source == "ai")
        )
        ai_generated_designs = ai_generated_designs_result.scalar() or 0
        
        uploaded_designs_result = await db.execute(
            select(func.count(models.Design.design_id))
            .where(models.Design.design_source == "upload")
        )
        uploaded_designs = uploaded_designs_result.scalar() or 0
        
        designs_today_result = await db.execute(
            select(func.count(models.Design.design_id))
            .where(models.Design.created_at >= datetime.utcnow().date())
        )
        designs_today = designs_today_result.scalar() or 0
        
        # Order statistics
        total_orders_result = await db.execute(select(func.count(models.Order.order_id)))
        total_orders = total_orders_result.scalar() or 0
        
        orders_today_result = await db.execute(
            select(func.count(models.Order.order_id))
            .where(models.Order.created_at >= datetime.utcnow().date())
        )
        orders_today = orders_today_result.scalar() or 0
        
        orders_week_result = await db.execute(
            select(func.count(models.Order.order_id))
            .where(models.Order.created_at >= datetime.utcnow() - timedelta(days=7))
        )
        orders_week = orders_week_result.scalar() or 0
        
        total_revenue_result = await db.execute(select(func.coalesce(func.sum(models.Order.total_amount), 0)))
        total_revenue = float(total_revenue_result.scalar() or 0)
        
        revenue_today_result = await db.execute(
            select(func.coalesce(func.sum(models.Order.total_amount), 0))
            .where(models.Order.created_at >= datetime.utcnow().date())
        )
        revenue_today = float(revenue_today_result.scalar() or 0)
        
        revenue_week_result = await db.execute(
            select(func.coalesce(func.sum(models.Order.total_amount), 0))
            .where(models.Order.created_at >= datetime.utcnow() - timedelta(days=7))
        )
        revenue_week = float(revenue_week_result.scalar() or 0)
        
        pending_orders_result = await db.execute(
            select(func.count(models.Order.order_id))
            .where(models.Order.status == "Pending")
        )
        pending_orders = pending_orders_result.scalar() or 0
        
        completed_orders_result = await db.execute(
            select(func.count(models.Order.order_id))
            .where(models.Order.status == "Completed")
        )
        completed_orders = completed_orders_result.scalar() or 0
        
        # Storage statistics (mock - would integrate with S3 in production)
        storage_used_mb = 1024.5  # Mock value
        
        # AI generations today (mock - would track from job queue)
        ai_generations_today = 25  # Mock value
        
        return SystemStats(
            user_stats=UserStats(
                total_users=total_users,
                active_users=active_users,
                new_users_today=new_users_today,
                new_users_week=new_users_week,
                verified_users=verified_users
            ),
            design_stats=DesignStats(
                total_designs=total_designs,
                public_designs=public_designs,
                ai_generated_designs=ai_generated_designs,
                uploaded_designs=uploaded_designs,
                designs_today=designs_today
            ),
            order_stats=OrderStats(
                total_orders=total_orders,
                orders_today=orders_today,
                orders_week=orders_week,
                total_revenue=total_revenue,
                revenue_today=revenue_today,
                revenue_week=revenue_week,
                pending_orders=pending_orders,
                completed_orders=completed_orders
            ),
            storage_used_mb=storage_used_mb,
            ai_generations_today=ai_generations_today
        )
        
    except Exception as e:
        sentry_manager.capture_exception(e, {"action": "get_admin_stats"})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch system statistics"
        )

@router.get("/users", response_model=List[AdminUserResponse])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    admin_user: models.User = Depends(require_admin)
):
    """Get users with filtering and pagination"""
    try:
        query = select(models.User).options(
            selectinload(models.User.designs),
            selectinload(models.User.orders)
        )
        
        # Apply search filter
        if search:
            search_term = f"%{validate_secure_input(search)}%"
            query = query.where(
                or_(
                    models.User.email.ilike(search_term),
                    models.User.full_name.ilike(search_term)
                )
            )
        
        # Apply status filter
        if status_filter:
            if status_filter == "verified":
                query = query.where(models.User.is_email_verified == True)
            elif status_filter == "unverified":
                query = query.where(models.User.is_email_verified == False)
            elif status_filter == "active":
                query = query.where(
                    models.User.last_login >= datetime.utcnow() - timedelta(days=30)
                )
        
        # Apply pagination and ordering
        query = query.order_by(desc(models.User.created_at)).offset(skip).limit(limit)
        
        result = await db.execute(query)
        users = result.scalars().all()
        
        admin_users = []
        for user in users:
            design_count = len(user.designs) if user.designs else 0
            order_count = len(user.orders) if user.orders else 0
            total_spent = sum(order.total_amount for order in user.orders) if user.orders else 0
            
            status = "active" if user.last_login and user.last_login >= datetime.utcnow() - timedelta(days=30) else "inactive"
            if not user.is_email_verified:
                status = "unverified"
            
            admin_users.append(AdminUserResponse(
                user_id=user.user_id,
                email=user.email,
                full_name=user.full_name,
                is_email_verified=user.is_email_verified,
                created_at=user.created_at,
                last_login=user.last_login,
                design_count=design_count,
                order_count=order_count,
                total_spent=total_spent,
                status=status
            ))
        
        return admin_users
        
    except Exception as e:
        sentry_manager.capture_exception(e, {"action": "get_admin_users"})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users"
        )

@router.get("/designs", response_model=List[AdminDesignResponse])
async def get_designs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    admin_user: models.User = Depends(require_admin)
):
    """Get designs with filtering and pagination"""
    try:
        query = select(models.Design).options(selectinload(models.Design.user))
        
        # Apply search filter
        if search:
            search_term = f"%{validate_secure_input(search)}%"
            query = query.where(models.Design.design_name.ilike(search_term))
        
        # Apply status filter
        if status_filter:
            if status_filter == "public":
                query = query.where(models.Design.is_public == True)
            elif status_filter == "private":
                query = query.where(models.Design.is_public == False)
            elif status_filter == "ai_generated":
                query = query.where(models.Design.design_source == "ai")
            elif status_filter == "uploaded":
                query = query.where(models.Design.design_source == "upload")
        
        # Apply pagination and ordering
        query = query.order_by(desc(models.Design.created_at)).offset(skip).limit(limit)
        
        result = await db.execute(query)
        designs = result.scalars().all()
        
        admin_designs = []
        for design in designs:
            # Determine status
            status = "active"
            moderation_status = "approved"
            
            # Check for reports (mock - would implement reporting system)
            reports_count = 0
            
            admin_designs.append(AdminDesignResponse(
                design_id=design.design_id,
                design_name=design.design_name,
                user_email=design.user.email if design.user else "Unknown",
                design_source=design.design_source,
                is_public=design.is_public,
                created_at=design.created_at,
                status=status,
                moderation_status=moderation_status,
                reports_count=reports_count
            ))
        
        return admin_designs
        
    except Exception as e:
        sentry_manager.capture_exception(e, {"action": "get_admin_designs"})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch designs"
        )

@router.get("/orders", response_model=List[AdminOrderResponse])
async def get_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    admin_user: models.User = Depends(require_admin)
):
    """Get orders with filtering and pagination"""
    try:
        query = select(models.Order).options(
            selectinload(models.Order.user),
            selectinload(models.Order.items)
        )
        
        # Apply status filter
        if status_filter:
            query = query.where(models.Order.status == status_filter)
        
        # Apply pagination and ordering
        query = query.order_by(desc(models.Order.created_at)).offset(skip).limit(limit)
        
        result = await db.execute(query)
        orders = result.scalars().all()
        
        admin_orders = []
        for order in orders:
            items_count = len(order.items) if order.items else 0
            payment_status = "completed" if order.status == "Paid" else "pending"
            
            admin_orders.append(AdminOrderResponse(
                order_id=order.order_id,
                user_email=order.user.email if order.user else "Unknown",
                total_amount=order.total_amount,
                status=order.status,
                created_at=order.created_at.isoformat(),
                payment_status=payment_status,
                items_count=items_count
            ))
        
        return admin_orders
        
    except Exception as e:
        sentry_manager.capture_exception(e, {"action": "get_admin_orders"})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch orders"
        )

@router.post("/users/{user_id}/ban")
async def ban_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: models.User = Depends(require_admin)
):
    """Ban a user"""
    try:
        # Get user
        result = await db.execute(select(models.User).where(models.User.user_id == user_id))
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.is_admin:
            raise HTTPException(status_code=400, detail="Cannot ban admin user")
        
        # Ban user (set is_active flag - would need to add this to model)
        user.is_active = False
        await db.commit()
        
        sentry_manager.add_tag("admin_action", "user_banned")
        sentry_manager.add_extra("banned_user_id", user_id)
        sentry_manager.add_extra("banned_by", admin_user.user_id)
        
        return {"message": "User banned successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        sentry_manager.capture_exception(e, {"action": "ban_user", "user_id": user_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ban user"
        )

@router.post("/designs/{design_id}/moderate")
async def moderate_design(
    design_id: str,
    action: str,  # "approve", "reject", "remove"
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    admin_user: models.User = Depends(require_admin)
):
    """Moderate a design"""
    try:
        # Get design
        result = await db.execute(select(models.Design).where(models.Design.design_id == design_id))
        design = result.scalars().first()
        
        if not design:
            raise HTTPException(status_code=404, detail="Design not found")
        
        # Apply moderation action
        if action == "approve":
            design.is_public = True
            design.moderation_status = "approved"
        elif action == "reject":
            design.is_public = False
            design.moderation_status = "rejected"
        elif action == "remove":
            await db.delete(design)
        else:
            raise HTTPException(status_code=400, detail="Invalid moderation action")
        
        # Add moderation note (would need to add moderation_log table)
        await db.commit()
        
        sentry_manager.add_tag("admin_action", "design_moderated")
        sentry_manager.add_extra("design_id", design_id)
        sentry_manager.add_extra("moderation_action", action)
        sentry_manager.add_extra("moderated_by", admin_user.user_id)
        
        return {"message": f"Design {action}d successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        sentry_manager.capture_exception(e, {"action": "moderate_design", "design_id": design_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to moderate design"
        )

@router.get("/analytics/revenue")
async def get_revenue_analytics(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    admin_user: models.User = Depends(require_admin)
):
    """Get revenue analytics for the specified period"""
    try:
        # Get daily revenue for the specified period
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # This would be enhanced with proper date truncation in production
        revenue_query = select(
            func.date(models.Order.created_at).label('date'),
            func.sum(models.Order.total_amount).label('revenue'),
            func.count(models.Order.order_id).label('orders')
        ).where(
            models.Order.created_at >= start_date,
            models.Order.status == "Paid"
        ).group_by(func.date(models.Order.created_at)).order_by(func.date(models.Order.created_at))
        
        result = await db.execute(revenue_query)
        revenue_data = result.all()
        
        analytics = [
            {
                "date": str(row.date),
                "revenue": float(row.revenue or 0),
                "orders": row.orders or 0
            }
            for row in revenue_data
        ]
        
        return {"analytics": analytics, "period_days": days}
        
    except Exception as e:
        sentry_manager.capture_exception(e, {"action": "get_revenue_analytics"})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch revenue analytics"
        )
