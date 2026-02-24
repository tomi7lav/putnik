from fastapi import APIRouter

from app.api.v1.endpoints import auth, conversations, whatsapp

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(whatsapp.router, prefix="/webhooks/whatsapp", tags=["whatsapp"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
