"""
Email Service for Threadz Application using SendGrid
"""
import os
import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from jinja2 import Template
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import aiosmtplib
from email.message import EmailMessage

from .config import settings
from .auth import create_access_token
from .sentry_config import sentry_manager

class EmailService:
    """Email service for user verification, notifications, and password reset"""
    
    def __init__(self):
        self.smtp_config = None
        self.fastmail = None
        
        # Initialize SendGrid/FastAPI-Mail if configured
        if settings.SENDGRID_API_KEY and settings.SENDGRID_FROM_EMAIL:
            try:
                self.smtp_config = ConnectionConfig(
                    MAIL_USERNAME=settings.SENDGRID_API_KEY,
                    MAIL_PASSWORD=settings.SENDGRID_API_KEY,
                    MAIL_FROM=settings.SENDGRID_FROM_EMAIL,
                    MAIL_PORT=settings.SMTP_PORT,
                    MAIL_SERVER=settings.SMTP_HOST,
                    MAIL_STARTTLS=True,
                    MAIL_SSL_TLS=False,
                    USE_CREDENTIALS=True,
                    VALIDATE_CERTS=True,
                )
                self.fastmail = FastMail(self.smtp_config)
                print("✅ Email service initialized with SendGrid")
            except Exception as e:
                print(f"❌ Email service initialization failed: {e}")
        else:
            print("⚠️ Email service not configured")
    
    async def send_verification_email(self, user_email: str, user_id: str) -> bool:
        """Send email verification email"""
        try:
            # Generate verification token (24 hour expiry)
            verification_token = create_access_token(
                data={"sub": user_id, "type": "email_verification"},
                expires_delta=timedelta(hours=24)
            )
            
            # Create verification URL
            verification_url = f"{self._get_base_url()}/verify-email?token={verification_token}"
            
            # Email template
            html_content = self._render_verification_template(
                user_email=user_email,
                verification_url=verification_url
            )
            
            # Send email
            message = MessageSchema(
                subject="Verify your Threadz account",
                recipients=[user_email],
                body=html_content,
                subtype="html"
            )
            
            if self.fastmail:
                await self.fastmail.send_message(message)
                sentry_manager.add_tag("email_action", "verification_sent")
                return True
            else:
                print("⚠️ Email service not available")
                return False
                
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "send_verification_email",
                "user_email": user_email
            })
            return False
    
    async def send_password_reset_email(self, user_email: str, user_id: str) -> bool:
        """Send password reset email"""
        try:
            # Generate reset token (1 hour expiry)
            reset_token = create_access_token(
                data={"sub": user_id, "type": "password_reset"},
                expires_delta=timedelta(hours=1)
            )
            
            # Create reset URL
            reset_url = f"{self._get_base_url()}/reset-password?token={reset_token}"
            
            # Email template
            html_content = self._render_password_reset_template(
                user_email=user_email,
                reset_url=reset_url
            )
            
            # Send email
            message = MessageSchema(
                subject="Reset your Threadz password",
                recipients=[user_email],
                body=html_content,
                subtype="html"
            )
            
            if self.fastmail:
                await self.fastmail.send_message(message)
                sentry_manager.add_tag("email_action", "password_reset_sent")
                return True
            else:
                print("⚠️ Email service not available")
                return False
                
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "send_password_reset_email",
                "user_email": user_email
            })
            return False
    
    async def send_order_confirmation_email(self, user_email: str, order_data: Dict[str, Any]) -> bool:
        """Send order confirmation email"""
        try:
            # Email template
            html_content = self._render_order_confirmation_template(
                user_email=user_email,
                order_data=order_data
            )
            
            # Send email
            message = MessageSchema(
                subject=f"Order Confirmation - Threadz #{order_data.get('order_id', '')}",
                recipients=[user_email],
                body=html_content,
                subtype="html"
            )
            
            if self.fastmail:
                await self.fastmail.send_message(message)
                sentry_manager.add_tag("email_action", "order_confirmation_sent")
                return True
            else:
                print("⚠️ Email service not available")
                return False
                
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "send_order_confirmation_email",
                "user_email": user_email,
                "order_id": order_data.get('order_id')
            })
            return False
    
    async def send_payment_confirmation_email(self, user_email: str, payment_data: Dict[str, Any]) -> bool:
        """Send payment confirmation email"""
        try:
            # Email template
            html_content = self._render_payment_confirmation_template(
                user_email=user_email,
                payment_data=payment_data
            )
            
            # Send email
            message = MessageSchema(
                subject=f"Payment Confirmation - Threadz",
                recipients=[user_email],
                body=html_content,
                subtype="html"
            )
            
            if self.fastmail:
                await self.fastmail.send_message(message)
                sentry_manager.add_tag("email_action", "payment_confirmation_sent")
                return True
            else:
                print("⚠️ Email service not available")
                return False
                
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "send_payment_confirmation_email",
                "user_email": user_email
            })
            return False
    
    def _get_base_url(self) -> str:
        """Get base URL for email links"""
        if settings.ENVIRONMENT == "production":
            # Extract domain from ALLOWED_ORIGINS
            origins = settings.ALLOWED_ORIGINS.split(",")
            return origins[0] if origins else "https://threadz.app"
        else:
            return "http://localhost:3000"
    
    def _render_verification_template(self, user_email: str, verification_url: str) -> str:
        """Render email verification template"""
        template_str = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Verify Your Threadz Account</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #000; color: white; padding: 20px; text-align: center; }
        .content { padding: 30px 20px; background: #f9f9f9; }
        .button { display: inline-block; background: #000; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Threadz</h1>
            <p>Custom Fashion Platform</p>
        </div>
        <div class="content">
            <h2>Welcome to Threadz!</h2>
            <p>Hi {{ user_email }},</p>
            <p>Thank you for signing up for Threadz! Please verify your email address to activate your account.</p>
            <p><a href="{{ verification_url }}" class="button">Verify Email Address</a></p>
            <p><small>This link will expire in 24 hours.</small></p>
            <p>If you didn't create an account, you can safely ignore this email.</p>
        </div>
        <div class="footer">
            <p>&copy; 2024 Threadz. All rights reserved.</p>
            <p>This is an automated message, please do not reply.</p>
        </div>
    </div>
</body>
</html>
        """
        
        template = Template(template_str)
        return template.render(user_email=user_email, verification_url=verification_url)
    
    def _render_password_reset_template(self, user_email: str, reset_url: str) -> str:
        """Render password reset template"""
        template_str = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Reset Your Threadz Password</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #000; color: white; padding: 20px; text-align: center; }
        .content { padding: 30px 20px; background: #f9f9f9; }
        .button { display: inline-block; background: #000; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
        .warning { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Threadz</h1>
            <p>Custom Fashion Platform</p>
        </div>
        <div class="content">
            <h2>Reset Your Password</h2>
            <p>Hi {{ user_email }},</p>
            <p>We received a request to reset your password for your Threadz account.</p>
            <p><a href="{{ reset_url }}" class="button">Reset Password</a></p>
            <div class="warning">
                <p><strong>Important:</strong> This link will expire in 1 hour for security reasons.</p>
            </div>
            <p>If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.</p>
        </div>
        <div class="footer">
            <p>&copy; 2024 Threadz. All rights reserved.</p>
            <p>This is an automated message, please do not reply.</p>
        </div>
    </div>
</body>
</html>
        """
        
        template = Template(template_str)
        return template.render(user_email=user_email, reset_url=reset_url)
    
    def _render_order_confirmation_template(self, user_email: str, order_data: Dict[str, Any]) -> str:
        """Render order confirmation template"""
        template_str = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Order Confirmation - Threadz</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #000; color: white; padding: 20px; text-align: center; }
        .content { padding: 30px 20px; background: #f9f9f9; }
        .order-details { background: white; padding: 20px; border-radius: 5px; margin: 20px 0; }
        .total { font-size: 18px; font-weight: bold; color: #000; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Threadz</h1>
            <p>Custom Fashion Platform</p>
        </div>
        <div class="content">
            <h2>Order Confirmed!</h2>
            <p>Hi {{ user_email }},</p>
            <p>Thank you for your order! We've received your order and it's now being processed.</p>
            
            <div class="order-details">
                <h3>Order Details</h3>
                <p><strong>Order ID:</strong> #{{ order_data.order_id }}</p>
                <p><strong>Date:</strong> {{ order_data.created_at }}</p>
                <p><strong>Status:</strong> {{ order_data.status }}</p>
                
                <h4>Items:</h4>
                {% for item in order_data.items %}
                <p>{{ item.quantity }}x {{ item.product_name }} - ₹{{ item.unit_price }}</p>
                {% endfor %}
                
                <p class="total">Total: ₹{{ order_data.total_amount }}</p>
            </div>
            
            <p>We'll send you another email when your order ships.</p>
        </div>
        <div class="footer">
            <p>&copy; 2024 Threadz. All rights reserved.</p>
            <p>This is an automated message, please do not reply.</p>
        </div>
    </div>
</body>
</html>
        """
        
        template = Template(template_str)
        return template.render(user_email=user_email, order_data=order_data)
    
    def _render_payment_confirmation_template(self, user_email: str, payment_data: Dict[str, Any]) -> str:
        """Render payment confirmation template"""
        template_str = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Payment Confirmation - Threadz</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #000; color: white; padding: 20px; text-align: center; }
        .content { padding: 30px 20px; background: #f9f9f9; }
        .payment-details { background: white; padding: 20px; border-radius: 5px; margin: 20px 0; }
        .success { background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 5px; margin: 20px 0; color: #155724; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Threadz</h1>
            <p>Custom Fashion Platform</p>
        </div>
        <div class="content">
            <h2>Payment Successful!</h2>
            <p>Hi {{ user_email }},</p>
            
            <div class="success">
                <p><strong>✓ Your payment has been successfully processed.</strong></p>
            </div>
            
            <div class="payment-details">
                <h3>Payment Details</h3>
                <p><strong>Payment ID:</strong> {{ payment_data.payment_id }}</p>
                <p><strong>Order ID:</strong> #{{ payment_data.order_id }}</p>
                <p><strong>Amount:</strong> ₹{{ payment_data.amount }}</p>
                <p><strong>Method:</strong> {{ payment_data.method }}</p>
                <p><strong>Date:</strong> {{ payment_data.created_at }}</p>
            </div>
            
            <p>Your order is now being processed and you'll receive shipping confirmation soon.</p>
        </div>
        <div class="footer">
            <p>&copy; 2024 Threadz. All rights reserved.</p>
            <p>This is an automated message, please do not reply.</p>
        </div>
    </div>
</body>
</html>
        """
        
        template = Template(template_str)
        return template.render(user_email=user_email, payment_data=payment_data)
    
    def is_available(self) -> bool:
        """Check if email service is available"""
        return self.fastmail is not None

# Global email service instance
email_service = EmailService()
