from fastapi import APIRouter

from .users import router as users_router
from .auth import router as auth_router
from .complaints import router as complaints_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(complaints_router, prefix="/complaints", tags=["complaints"])
