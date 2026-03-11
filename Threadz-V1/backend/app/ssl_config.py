"""
SSL/HTTPS Configuration for Threadz Application
"""
import os
from fastapi import FastAPI
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https://api.razorpay.com; "
            "frame-ancestors 'none';"
        )
        
        return response

def setup_ssl_and_security(app: FastAPI):
    """Setup SSL and security middleware"""
    
    # Only add HTTPS redirect in production
    if os.getenv("ENVIRONMENT") == "production":
        app.add_middleware(HTTPSRedirectMiddleware)
    
    # Trusted hosts middleware
    trusted_hosts = os.getenv("TRUSTED_HOSTS", "localhost,127.0.0.1").split(",")
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=trusted_hosts
    )
    
    # Security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Gzip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

# SSL Configuration for development (self-signed certificate)
def get_ssl_context():
    """Get SSL context for development"""
    if os.getenv("ENVIRONMENT") == "production":
        # In production, use Let's Encrypt or managed certificates
        return None
    else:
        # For development, you can generate self-signed certificates
        ssl_cert = os.getenv("SSL_CERT_PATH", "/etc/ssl/certs/localhost.crt")
        ssl_key = os.getenv("SSL_KEY_PATH", "/etc/ssl/private/localhost.key")
        
        if os.path.exists(ssl_cert) and os.path.exists(ssl_key):
            return {
                "ssl_certfile": ssl_cert,
                "ssl_keyfile": ssl_key
            }
        return None
