from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, RegisterTenantRequest


class AuthService:
    async def register_tenant_admin(self, db: AsyncSession, payload: RegisterTenantRequest) -> AuthResponse:
        tenant_exists = await db.scalar(select(Tenant).where(Tenant.slug == payload.tenant_slug.lower()))
        if tenant_exists:
            raise ValueError("Tenant slug already exists")

        tenant = Tenant(name=payload.tenant_name.strip(), slug=payload.tenant_slug.lower().strip())
        db.add(tenant)
        await db.flush()

        user = User(
            tenant_id=tenant.id,
            email=payload.email.lower().strip(),
            full_name=payload.full_name.strip(),
            hashed_password=get_password_hash(payload.password),
            role="admin",
        )
        db.add(user)
        await db.flush()

        token = create_access_token(subject=str(user.id), tenant_id=str(tenant.id))
        return AuthResponse(access_token=token, tenant_id=tenant.id, user_id=user.id)

    async def login(self, db: AsyncSession, payload: LoginRequest) -> AuthResponse:
        tenant = await db.scalar(select(Tenant).where(Tenant.slug == payload.tenant_slug.lower().strip()))
        if not tenant:
            raise ValueError("Invalid credentials")

        user = await db.scalar(
            select(User).where(
                User.tenant_id == tenant.id,
                User.email == payload.email.lower().strip(),
                User.status == "active",
            )
        )
        if not user:
            raise ValueError("Invalid credentials")

        if not verify_password(payload.password, user.hashed_password):
            raise ValueError("Invalid credentials")

        token = create_access_token(subject=str(user.id), tenant_id=str(tenant.id))
        return AuthResponse(access_token=token, tenant_id=tenant.id, user_id=user.id)

    async def get_user_for_token(self, db: AsyncSession, user_id: UUID, tenant_id: UUID) -> Optional[User]:
        return await db.scalar(select(User).where(User.id == user_id, User.tenant_id == tenant_id, User.status == "active"))


auth_service = AuthService()
