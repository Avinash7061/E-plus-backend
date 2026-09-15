from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class RegisterRequest(BaseModel):
    """Schema for user registration request"""
    phone_number: str
    full_name: Optional[str] = None
    role: str = "patient"

class LoginRequest(BaseModel):
    """Schema for user login request"""
    phone_number: str
    password: Optional[str] = "Prahari@2026"
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    """Schema for user data response"""
    id: str
    phone_number: str
    full_name: Optional[str] = None
    role: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class EmailLoginRequest(BaseModel):
    email: str
    password: Optional[str] = "Prahari@2026"
    full_name: Optional[str] = None
