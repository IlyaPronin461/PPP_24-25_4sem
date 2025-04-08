from fastapi import APIRouter
from .endpoints import auth, encode

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(encode.router, prefix="/encode", tags=["encode"])

__all__ = ["router"]