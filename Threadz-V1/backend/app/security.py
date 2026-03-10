"""
Security utilities for Threadz application
"""
import re
import html
from typing import Optional

def sanitize_input(input_string: str) -> str:
    """
    Sanitize user input to prevent XSS attacks
    """
    if not input_string:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = html.escape(input_string)
    
    # Remove any remaining script tags or javascript: URLs
    sanitized = re.sub(r'<script.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
    
    return sanitized.strip()

def validate_design_name(name: str) -> bool:
    """
    Validate design name for security and format
    """
    if not name or len(name) < 1 or len(name) > 255:
        return False
    
    # Allow only alphanumeric, spaces, and basic punctuation
    allowed_pattern = r'^[a-zA-Z0-9\s\-_.,()&]+$'
    return re.match(allowed_pattern, name) is not None

def generate_secure_filename(original_filename: str) -> str:
    """
    Generate a secure filename to prevent directory traversal
    """
    import uuid
    import os
    
    # Extract extension safely
    if '.' not in original_filename:
        return str(uuid.uuid4())
    
    extension = os.path.splitext(original_filename)[1].lower()
    
    # Only allow safe extensions
    safe_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    if extension not in safe_extensions:
        raise ValueError(f"Unsafe file extension: {extension}")
    
    return f"{uuid.uuid4()}{extension}"
