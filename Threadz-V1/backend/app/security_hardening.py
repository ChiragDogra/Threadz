"""
Security Hardening Module for Threadz Application
"""
import os
import re
import hashlib
import secrets
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import clamd
from PIL import Image
import io

from .config import settings
from .sentry_config import sentry_manager

class SecurityHardening:
    """Advanced security features for production hardening"""
    
    def __init__(self):
        self.clamav_scanner = None
        self._initialize_clamav()
    
    def _initialize_clamav(self):
        """Initialize ClamAV virus scanner"""
        try:
            self.clamav_scanner = clamd.ClamdUnixSocket()
            self.clamav_scanner.ping()
            print("✅ ClamAV virus scanner initialized")
        except Exception as e:
            print(f"⚠️ ClamAV not available: {e}")
            self.clamav_scanner = None
    
    def validate_input_comprehensive(self, input_data: str, input_type: str = "text") -> bool:
        """Comprehensive input validation"""
        if not input_data:
            return False
        
        # Length validation
        max_lengths = {
            "text": 10000,
            "name": 255,
            "email": 254,
            "prompt": 1000,
            "description": 5000
        }
        
        max_len = max_lengths.get(input_type, 1000)
        if len(input_data) > max_len:
            return False
        
        # Content validation based on type
        if input_type == "email":
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return re.match(email_pattern, input_data) is not None
        
        elif input_type == "name":
            # Allow only letters, numbers, spaces, and basic punctuation
            name_pattern = r'^[a-zA-Z0-9\s\-_.,()&]+$'
            return re.match(name_pattern, input_data) is not None
        
        elif input_type == "prompt":
            # Allow creative prompts but block dangerous patterns
            dangerous_patterns = [
                r'<script.*?>.*?</script>',
                r'javascript:',
                r'vbscript:',
                r'onload=',
                r'onerror=',
                r'eval(',
                r'exec(',
                r'system(',
                r'base64_decode',
                r'unserialize('
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, input_data, re.IGNORECASE):
                    return False
        
        else:  # Generic text
            # Block script tags and JS URLs
            script_pattern = r'<script.*?>.*?</script>'
            js_pattern = r'javascript:'
            
            if re.search(script_pattern, input_data, re.IGNORECASE):
                return False
            if re.search(js_pattern, input_data, re.IGNORECASE):
                return False
        
        return True
    
    async def scan_file_for_viruses(self, file_content: bytes) -> bool:
        """Scan uploaded file for viruses"""
        if not self.clamav_scanner:
            # If ClamAV is not available, log and allow
            sentry_manager.add_tag("virus_scan", "unavailable")
            return True
        
        try:
            # Scan file
            scan_result = self.clamav_scanner.instream(io.BytesIO(file_content))
            
            if scan_result[0] == 'FOUND':
                sentry_manager.add_tag("virus_detected", True)
                sentry_manager.add_extra("virus_name", scan_result[1])
                return False
            else:
                sentry_manager.add_tag("virus_scan", "clean")
                return True
                
        except Exception as e:
            sentry_manager.capture_exception(e, {"action": "virus_scan"})
            # Fail open - allow file if scan fails
            return True
    
    def validate_image_security(self, image_bytes: bytes) -> Dict[str, Any]:
        """Validate image for security threats"""
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                # Check for image bombs (extremely large dimensions)
                if img.width > 10000 or img.height > 10000:
                    raise ValueError("Image dimensions too large")
                
                # Check for suspicious file signatures
                if len(image_bytes) > 50 * 1024 * 1024:  # 50MB limit
                    raise ValueError("File size too large")
                
                # Validate image format
                allowed_formats = ['JPEG', 'PNG', 'GIF', 'WEBP']
                if img.format not in allowed_formats:
                    raise ValueError(f"Unsupported image format: {img.format}")
                
                # Check for embedded scripts in metadata
                if hasattr(img, 'text'):
                    dangerous_keywords = ['<script', 'javascript:', 'vbscript:']
                    for key, value in (img.text or {}).items():
                        if isinstance(value, str):
                            for keyword in dangerous_keywords:
                                if keyword.lower() in value.lower():
                                    raise ValueError("Suspicious content in image metadata")
                
                return {
                    "valid": True,
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "size_bytes": len(image_bytes)
                }
                
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    def generate_csrf_token(self) -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)
    
    def validate_csrf_token(self, token: str, session_token: str) -> bool:
        """Validate CSRF token"""
        return secrets.compare_digest(token, session_token)
    
    def hash_sensitive_data(self, data: str) -> str:
        """Hash sensitive data for storage"""
        salt = secrets.token_bytes(32)
        hash_obj = hashlib.pbkdf2_hmac('sha256', data.encode(), salt, 100000)
        return f"pbkdf2_sha256${hash_obj.hex()}${salt.hex()}"
    
    def verify_sensitive_data_hash(self, data: str, hashed: str) -> bool:
        """Verify sensitive data hash"""
        try:
            algorithm, hash_hex, salt_hex = hashed.split('$')
            salt = bytes.fromhex(salt_hex)
            expected_hash = hashlib.pbkdf2_hmac('sha256', data.encode(), salt, 100000)
            return secrets.compare_digest(expected_hash.hex(), hash_hex)
        except:
            return False
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal"""
        # Remove path separators
        filename = filename.replace('/', '_').replace('\\', '_')
        
        # Remove dangerous characters
        filename = re.sub(r'[<>:"|?*]', '', filename)
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        # Ensure it's not empty
        if not filename or filename.startswith('.'):
            filename = "file_" + filename
        
        return filename
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key format and strength"""
        if not api_key or len(api_key) < 32:
            return False
        
        # Check for sufficient entropy (basic check)
        unique_chars = len(set(api_key))
        if unique_chars < len(api_key) * 0.3:  # At least 30% unique characters
            return False
        
        return True
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get comprehensive security headers"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": self._get_csp_header(),
            "Permissions-Policy": self._get_permissions_policy(),
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin"
        }
    
    def _get_csp_header(self) -> str:
        """Generate Content Security Policy header"""
        directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Required for Next.js
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self' https://api.razorpay.com https://stability.ai https://api.openai.com",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "upgrade-insecure-requests"
        ]
        
        return "; ".join(directives)
    
    def _get_permissions_policy(self) -> str:
        """Generate Permissions Policy header"""
        permissions = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=()",
            "usb=()",
            "magnetometer=()",
            "gyroscope=()",
            "accelerometer=()",
            "ambient-light-sensor=()",
            "autoplay=(self)",
            "clipboard-read=(self)",
            "clipboard-write=(self)"
        ]
        
        return ", ".join(permissions)
    
    def detect_sql_injection_attempt(self, input_data: str) -> bool:
        """Detect potential SQL injection attempts"""
        sql_patterns = [
            r"(\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(['\"]).*(['\"]).*\1.*\2",
            r"(\/\*)",
            r"(\*\/)",
            r"(--)",
            r"(;)",
            r"(\b(SCRIPT|JAVASCRIPT|VBSCRIPT|ONLOAD|ONERROR)\b)",
            r"(xp_|sp_|fn_)"
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                sentry_manager.add_tag("sql_injection_attempt", True)
                sentry_manager.add_extra("suspicious_input", input_data[:100])
                return True
        
        return False
    
    def detect_xss_attempt(self, input_data: str) -> bool:
        """Detect potential XSS attempts"""
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"vbscript:",
            r"onload\s*=",
            r"onerror\s*=",
            r"onclick\s*=",
            r"onmouseover\s*=",
            r"onfocus\s*=",
            r"onblur\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"<link[^>]*>",
            r"<meta[^>]*>",
            r"eval\s*\(",
            r"alert\s*\(",
            r"confirm\s*\(",
            r"prompt\s*\("
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                sentry_manager.add_tag("xss_attempt", True)
                sentry_manager.add_extra("suspicious_input", input_data[:100])
                return True
        
        return False
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security events"""
        sentry_manager.add_tag("security_event", event_type)
        for key, value in details.items():
            sentry_manager.add_extra(f"security_{key}", value)
        
        # In production, you might want to send this to a SIEM system
        if settings.ENVIRONMENT == "production":
            print(f"🚨 SECURITY EVENT: {event_type} - {details}")

# Global security hardening instance
security_hardening = SecurityHardening()

# Security middleware
async def security_middleware(request: Request, call_next):
    """Security middleware for all requests"""
    
    # Add security headers
    response = await call_next(request)
    
    headers = security_hardening.get_security_headers()
    for key, value in headers.items():
        response.headers[key] = value
    
    return response

# Rate limiting with security context
security_limiter = Limiter(key_func=get_remote_address)

@security_limiter.limit("100/minute")
async def rate_limit_with_security(request: Request):
    """Rate limiting with security monitoring"""
    # Log rate limit events
    security_hardening.log_security_event("rate_limit_check", {
        "ip": get_remote_address(request),
        "path": request.url.path,
        "method": request.method
    })

# Input validation decorator
def validate_secure_input(input_type: str = "text"):
    """Decorator for input validation"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Find input data in kwargs
            for key, value in kwargs.items():
                if isinstance(value, str):
                    if not security_hardening.validate_input_comprehensive(value, input_type):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid input for field: {key}"
                        )
                    
                    # Check for security threats
                    if security_hardening.detect_sql_injection_attempt(value):
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Suspicious input detected"
                        )
                    
                    if security_hardening.detect_xss_attempt(value):
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Suspicious input detected"
                        )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
