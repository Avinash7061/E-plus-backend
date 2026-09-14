from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    """Returns the currently authenticated user's profile"""
    return current_user
