"""
Razorpay Payment Integration for Threadz Application
"""
import os
import hashlib
import hmac
import uuid
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import razorpay
import httpx

from . import models, schemas_order
from .database import get_db
from .config import settings
from .sentry_config import sentry_manager

class RazorpayService:
    """Enhanced Razorpay service with comprehensive payment handling"""
    
    def __init__(self):
        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            print("⚠️ Razorpay credentials not configured")
            self.client = None
        else:
            try:
                self.client = razorpay.Client(
                    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
                )
                self.webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
                print("✅ Razorpay client initialized")
            except Exception as e:
                print(f"❌ Razorpay initialization failed: {e}")
                self.client = None
    
    def create_order(self, amount: int, currency: str = "INR", receipt: str = None, notes: Dict = None) -> Dict[str, Any]:
        """Create Razorpay order with enhanced configuration"""
        if not self.client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Payment service not available"
            )
        
        try:
            order_data = {
                "amount": amount,  # Amount in paise (INR)
                "currency": currency,
                "receipt": receipt or f"order_{uuid.uuid4().hex[:12]}",
                "payment_capture": 1,  # Auto-capture
                "notes": {
                    "threadz_order": True,
                    "platform": "threadz_api",
                    **(notes or {})
                }
            }
            
            order = self.client.order.create(data=order_data)
            
            # Log order creation
            sentry_manager.add_tag("razorpay_action", "order_created")
            sentry_manager.add_extra("razorpay_order_id", order.get("id"))
            
            return order
            
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "create_order",
                "amount": amount,
                "currency": currency
            })
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create payment order: {str(e)}"
            )
    
    def verify_payment_signature(
        self, 
        razorpay_order_id: str, 
        razorpay_payment_id: str, 
        razorpay_signature: str
    ) -> bool:
        """Verify Razorpay payment signature with enhanced security"""
        if not self.client:
            return False
        
        try:
            # Generate signature string
            signature_string = f"{razorpay_order_id}|{razorpay_payment_id}"
            
            # Use webhook secret if available, otherwise use key secret
            secret_key = self.webhook_secret or settings.RAZORPAY_KEY_SECRET
            
            # Generate expected signature
            expected_signature = hmac.new(
                secret_key.encode(),
                signature_string.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures securely
            is_valid = hmac.compare_digest(expected_signature, razorpay_signature)
            
            # Log verification attempt
            sentry_manager.add_tag("razorpay_action", "signature_verification")
            sentry_manager.add_extra("verification_result", is_valid)
            
            return is_valid
            
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "verify_signature",
                "order_id": razorpay_order_id,
                "payment_id": razorpay_payment_id
            })
            return False
    
    def capture_payment(self, razorpay_payment_id: str, amount: int) -> Dict[str, Any]:
        """Capture payment after authorization (for manual capture flow)"""
        if not self.client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Payment service not available"
            )
        
        try:
            payment = self.client.payment.capture(
                razorpay_payment_id,
                amount,
                {"currency": "INR"}
            )
            
            sentry_manager.add_tag("razorpay_action", "payment_captured")
            return payment
            
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "capture_payment",
                "payment_id": razorpay_payment_id,
                "amount": amount
            })
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to capture payment: {str(e)}"
            )
    
    def get_payment_details(self, razorpay_payment_id: str) -> Dict[str, Any]:
        """Get comprehensive payment details"""
        if not self.client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Payment service not available"
            )
        
        try:
            payment = self.client.payment.fetch(razorpay_payment_id)
            
            sentry_manager.add_tag("razorpay_action", "payment_details_fetched")
            return payment
            
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "get_payment_details",
                "payment_id": razorpay_payment_id
            })
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment not found: {str(e)}"
            )
    
    def refund_payment(self, razorpay_payment_id: str, amount: Optional[int] = None) -> Dict[str, Any]:
        """Process payment refund"""
        if not self.client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Payment service not available"
            )
        
        try:
            refund_data = {"payment_id": razorpay_payment_id}
            if amount:
                refund_data["amount"] = amount
            
            refund = self.client.payment.refund(razorpay_payment_id, refund_data)
            
            sentry_manager.add_tag("razorpay_action", "payment_refunded")
            return refund
            
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "refund_payment",
                "payment_id": razorpay_payment_id,
                "amount": amount
            })
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process refund: {str(e)}"
            )
    
    def process_webhook(self, webhook_body: bytes, razorpay_signature: str) -> bool:
        """Process Razorpay webhook with enhanced validation"""
        if not self.client:
            return False
        
        try:
            # Verify webhook signature
            if not self.webhook_secret:
                print("⚠️ Webhook secret not configured")
                return False
            
            expected_signature = hmac.new(
                self.webhook_secret.encode(),
                webhook_body,
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(expected_signature, razorpay_signature):
                sentry_manager.add_tag("razorpay_action", "webhook_signature_invalid")
                return False
            
            sentry_manager.add_tag("razorpay_action", "webhook_processed")
            return True
            
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "process_webhook",
                "webhook_length": len(webhook_body)
            })
            return False
    
    def get_payment_methods(self) -> Dict[str, Any]:
        """Get available payment methods"""
        if not self.client:
            return {"methods": [], "error": "Payment service not available"}
        
        try:
            # This is a placeholder - Razorpay doesn't have a direct API for this
            # In production, you would configure this based on your Razorpay dashboard
            methods = {
                "upi": {"name": "UPI", "available": True},
                "card": {"name": "Credit/Debit Card", "available": True},
                "netbanking": {"name": "Net Banking", "available": True},
                "wallet": {"name": "Wallet", "available": True},
                "emi": {"name": "EMI", "available": True}
            }
            
            return {"methods": methods}
            
        except Exception as e:
            sentry_manager.capture_exception(e, {"action": "get_payment_methods"})
            return {"methods": [], "error": str(e)}
    
    def validate_order_amount(self, amount: int) -> bool:
        """Validate order amount (in paise)"""
        # Razorpay minimum amount is 100 paise (₹1)
        if amount < 100:
            return False
        
        # Maximum amount (₹10,00,000)
        if amount > 100000000:
            return False
        
        return True
    
    def calculate_order_amount(self, items: list, shipping_cost: int = 0) -> int:
        """Calculate total order amount in paise"""
        total = 0
        
        for item in items:
            total += item.get("unit_price", 0) * item.get("quantity", 1)
        
        total += shipping_cost
        
        # Convert to paise (assuming input is in rupees)
        return total * 100

# Global Razorpay service instance
razorpay_service = RazorpayService()
