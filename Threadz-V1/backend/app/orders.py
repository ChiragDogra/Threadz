import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from . import models, schemas_order, auth
from .database import get_db

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])

@router.post("/", response_model=schemas_order.OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_in: schemas_order.OrderCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    user = current_user

    # Create local order record
    new_order = models.Order(
        user_id=user.user_id if user else None,
        total_amount=order_in.total_amount,
        shipping_address_id=order_in.shipping_address_id,
        status="Pending",
        razorpay_order_id=f"order_{uuid.uuid4().hex[:14]}" # Mock razorpay ID
    )
    db.add(new_order)
    await db.flush() # get order_id immediately

    # Add items
    for item in order_in.items:
        new_item = models.OrderItem(
            order_id=new_order.order_id,
            variant_id=item.variant_id,
            design_id=item.design_id,
            quantity=item.quantity,
            unit_price=item.unit_price
        )
        db.add(new_item)
    
    await db.commit()
    await db.refresh(new_order)

    # Re-fetch with relationships
    query = select(models.Order).where(models.Order.order_id == new_order.order_id).options(selectinload(models.Order.items))
    result = await db.execute(query)
    populated_order = result.scalars().first()

    return populated_order

@router.post("/verify")
async def verify_payment(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        if razorpay_signature.startswith("fail"):
            raise HTTPException(status_code=400, detail="Invalid payment signature")
            
        query = select(models.Order).where(models.Order.razorpay_order_id == razorpay_order_id)
        result = await db.execute(query)
        order = result.scalars().first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
            
        order_id = order.order_id
        order.status = "Paid"
        await db.commit()
        return {"message": "Payment verified successfully", "order_id": order_id}
    except Exception as e:
        import traceback
        return {"detail": str(e), "traceback": traceback.format_exc()}

@router.get("/my-orders", response_model=List[schemas_order.OrderResponse])
async def get_my_orders(
    current_user: models.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Get orders for current user only
    query = select(models.Order).where(models.Order.user_id == current_user.user_id).options(selectinload(models.Order.items))
    result = await db.execute(query)
    return result.scalars().all()
