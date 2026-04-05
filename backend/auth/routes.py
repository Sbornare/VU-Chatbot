from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from backend.database import get_db, get_next_sequence
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
def register(user: UserCreate, db=Depends(get_db)):
    users = db.users

    if users.find_one({"email": user.email}):
        raise HTTPException(400, "Email already registered")
    
    if users.find_one({"phone_number": user.phone_number}):
        raise HTTPException(400, "Phone number already registered")

    user_id = get_next_sequence("users")

    new_user = {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "phone_number": user.phone_number,
        "role": "student",
        "interested_programs": user.interested_programs,
        "hashed_password": hash_password(user.password),
        "whatsapp_notifications_enabled": user.whatsapp_notifications_enabled,
        "created_at": datetime.utcnow(),
        "last_login": None,
    }

    users.insert_one(new_user)
    
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
    
    new_user.pop("hashed_password", None)
    return new_user


@router.post("/login")
def login(user: UserLogin, db=Depends(get_db)):
    db_user = db.users.find_one({"email": user.email})
    if not db_user or not verify_password(
        user.password, db_user.get("hashed_password", "")
    ):
        raise HTTPException(401, "Invalid credentials")

    db.users.update_one(
        {"id": db_user["id"]},
        {"$set": {"last_login": datetime.utcnow()}},
    )

    token = create_access_token({"sub": str(db_user["id"])})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
def get_current_user_info(current_user=Depends(get_current_user)):
    return current_user


@router.get("/users", response_model=list[UserOut])
def list_users(
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.get("role") != "admin":
        raise HTTPException(403, "Admins only")

    users = list(db.users.find({}, {"_id": 0, "hashed_password": 0}))
    return users
