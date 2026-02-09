from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from backend.database import get_db
from backend.auth.models import User
from backend.auth.schemas import UserCreate, UserLogin, UserOut
from backend.auth.auth_utils import (
    hash_password,
    verify_password,
    create_access_token
)
from backend.auth.dependencies import get_current_user
from backend.services.whatsapp_service import whatsapp_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(400, "Email already registered")
    
    if db.query(User).filter(User.phone_number == user.phone_number).first():
        raise HTTPException(400, "Phone number already registered")

    new_user = User(
        username=user.username,
        email=user.email,
        phone_number=user.phone_number,
        interested_programs=user.interested_programs,
        hashed_password=hash_password(user.password),
        whatsapp_notifications_enabled=user.whatsapp_notifications_enabled
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Send WhatsApp welcome message only if enabled
    try:
        if user.phone_number and user.whatsapp_notifications_enabled:
            success = whatsapp_service.send_welcome_message(
                user.phone_number,
                user.username
            )
            if success:
                logger.info(f"WhatsApp welcome message sent to {user.phone_number}")
    except Exception as e:
        logger.error(f"Failed to send welcome message: {e}")
    
    return new_user


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(
        user.password, db_user.hashed_password
    ):
        raise HTTPException(401, "Invalid credentials")

    db_user.last_login = datetime.utcnow()
    db.commit()

    token = create_access_token({"sub": str(db_user.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/users", response_model=list[UserOut])
def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(403, "Admins only")
    return db.query(User).all()
