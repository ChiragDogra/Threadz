from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class TokenData(BaseModel):
    email: Optional[str] = None

# --- User Auth Schemas ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ForgotPassword(BaseModel):
    email: EmailStr

class UserResponse(BaseModel):
    user_id: str
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    email_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
