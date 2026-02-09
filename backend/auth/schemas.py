from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    phone_number: str
    interested_programs: Optional[str] = None
    whatsapp_notifications_enabled: bool = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    phone_number: Optional[str]
    role: str
    interested_programs: Optional[str]
    whatsapp_notifications_enabled: bool

    class Config:
        from_attributes = True
