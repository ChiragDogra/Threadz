import uuid
import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from . import models, schemas_order, auth
from .database import get_db
from .payment import razorpay_service

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])

@router.post("/", response_model=schemas_order.OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_in: schemas_order.OrderCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    user = current_user

    # Create Razorpay order
    try:
        razorpay_order = razorpay_service.create_order(
            amount=order_in.total_amount,
            receipt=f"order_{uuid.uuid4().hex[:12]}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment order: {str(e)}"
        )

    # Create local order record
    new_order = models.Order(
        user_id=user.user_id,
        total_amount=order_in.total_amount,
        shipping_address_id=order_in.shipping_address_id,
        status="Pending",
        razorpay_order_id=razorpay_order["id"]
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

    # Add Razorpay order details to response
    populated_order.razorpay_key_id = os.getenv("RAZORPAY_KEY_ID")
    populated_order.razorpay_order_id = razorpay_order["id"]
    populated_order.amount = razorpay_order["amount"]
    populated_order.currency = razorpay_order["currency"]

    return populated_order

@router.post("/verify")
async def verify_payment(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Verify payment signature
        is_valid = razorpay_service.verify_payment_signature(
            razorpay_order_id,
            razorpay_payment_id,
            razorpay_signature
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payment signature"
            )
        
        # Get payment details
        payment_details = razorpay_service.get_payment_details(razorpay_payment_id)
        
        # Find and update order
        query = select(models.Order).where(models.Order.razorpay_order_id == razorpay_order_id)
        result = await db.execute(query)
        order = result.scalars().first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Update order status based on payment status
        if payment_details["status"] == "captured":
            order.status = "Paid"
        elif payment_details["status"] == "authorized":
            order.status = "Authorized"
        else:
            order.status = "Payment Failed"
        
        await db.commit()
        
        return {
            "message": "Payment verified successfully", 
            "order_id": order.order_id,
            "payment_status": payment_details["status"],
            "order_status": order.status
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        return {"detail": str(e), "traceback": traceback.format_exc()}

@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle Razorpay webhooks"""
    try:
        webhook_body = await request.body()
        razorpay_signature = request.headers.get("X-Razorpay-Signature")
        
        if not razorpay_signature:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing signature"
            )
        
        # Verify webhook
        if not razorpay_service.process_webhook(webhook_body, razorpay_signature):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook signature"
            )
        
        # Process webhook event (you can expand this based on your needs)
        import json
        webhook_data = json.loads(webhook_body.decode())
        
        # Handle payment.captured event
        if webhook_data.get("event") == "payment.captured":
            payment_entity = webhook_data["payload"]["payment"]["entity"]
            razorpay_order_id = payment_entity["order_id"]
            
            # Update order status
            query = select(models.Order).where(models.Order.razorpay_order_id == razorpay_order_id)
            result = await db.execute(query)
            order = result.scalars().first()
            
            if order:
                order.status = "Paid"
                await db.commit()
        
        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )

@router.get("/my-orders", response_model=List[schemas_order.OrderResponse])
async def get_my_orders(
    current_user: models.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Get orders for current user only
    query = select(models.Order).where(models.Order.user_id == current_user.user_id).options(selectinload(models.Order.items))
    result = await db.execute(query)
    return result.scalars().all()
