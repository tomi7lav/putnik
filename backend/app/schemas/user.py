from uuid import UUID

from pydantic import BaseModel, EmailStr


class CurrentUserResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    email: EmailStr
    full_name: str
    role: str
    status: str
