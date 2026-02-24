from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.auth import AuthResponse, LoginRequest, RegisterTenantRequest
from app.services.auth_service import auth_service

router = APIRouter()


@router.post("/register-tenant", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register_tenant(payload: RegisterTenantRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    try:
        return await auth_service.register_tenant_admin(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    try:
        return await auth_service.login(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
