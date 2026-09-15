from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from app.core.supabase_client import get_supabase
from app.schemas.user import RegisterRequest, LoginRequest, EmailLoginRequest
from app.core.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
def register(request: RegisterRequest, db: Client = Depends(get_supabase)):
    """Registers a new user, returning an access token and user profile"""
    existing = db.table("users").select("id").eq("phone_number", request.phone_number).execute()
    if existing.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number already registered")
    
    new_user_data = {
        "phone_number": request.phone_number,
        "full_name": request.full_name,
        "role": request.role
    }
    response = db.table("users").insert(new_user_data).execute()
    
    if not response.data:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user")
        
    user = response.data[0]
    access_token = create_access_token(user_id=user["id"])
    
    return {"access_token": access_token, "user": user}

@router.post("/login")
def login(request: LoginRequest, db: Client = Depends(get_supabase)):
    """Logs in an existing user or creates a new one via phone number with password verification"""
    req_pass = (request.password or "").strip()
    if not req_pass:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password is required")

    clean_phone = request.phone_number.strip().replace(" ", "")
    response = db.table("users").select("*").eq("phone_number", clean_phone).execute()
    
    if response.data:
        user = response.data[0]
        stored_hash = user.get("password_hash")
        if stored_hash:
            if not verify_password(req_pass, stored_hash):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
        else:
            # Set initial password for existing account
            new_hash = hash_password(req_pass)
            db.table("users").update({"password_hash": new_hash}).eq("id", user["id"]).execute()
            user["password_hash"] = new_hash
    else:
        name = request.full_name or f"User {clean_phone[-4:]}"
        new_hash = hash_password(req_pass)
        insert_res = db.table("users").insert({
            "phone_number": clean_phone,
            "full_name": name,
            "password_hash": new_hash,
            "role": "patient"
        }).execute()
        if not insert_res.data:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user")
        user = insert_res.data[0]
        
    access_token = create_access_token(user_id=user["id"])
    return {"access_token": access_token, "user": user}

@router.post("/email-login")
def email_login(request: EmailLoginRequest, db: Client = Depends(get_supabase)):
    """Logs in an existing user or registers a new user with required password verification"""
    req_pass = (request.password or "").strip()
    if not req_pass:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password is required")

    clean_email = request.email.strip().lower()
    response = db.table("users").select("*").eq("email", clean_email).execute()
    
    if response.data:
        user = response.data[0]
        stored_hash = user.get("password_hash")
        if stored_hash:
            if not verify_password(req_pass, stored_hash):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
        else:
            # Set initial password for existing account
            new_hash = hash_password(req_pass)
            db.table("users").update({"password_hash": new_hash}).eq("id", user["id"]).execute()
            user["password_hash"] = new_hash
    else:
        import time
        name = request.full_name or clean_email.split("@")[0].replace(".", " ").title()
        fallback_phone = f"+91-99900{str(int(time.time()))[-5:]}"
        new_hash = hash_password(req_pass)
        insert_res = db.table("users").insert({
            "email": clean_email,
            "full_name": name,
            "phone_number": fallback_phone,
            "password_hash": new_hash,
            "role": "patient"
        }).execute()
        
        if not insert_res.data:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user")
        user = insert_res.data[0]
        
    access_token = create_access_token(user_id=user["id"])
    return {"access_token": access_token, "user": user}
