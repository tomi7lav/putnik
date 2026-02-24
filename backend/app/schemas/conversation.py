from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ConversationListItemResponse(BaseModel):
    id: UUID
    contact_id: UUID
    contact_name: Optional[str] = None
    phone_number: str
    channel: str
    status: str
    external_thread_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class MessageEventListItemResponse(BaseModel):
    id: UUID
    provider: str
    direction: str
    event_type: str
    external_event_id: Optional[str] = None
    idempotency_key: str
    payload_json: dict
    received_at: datetime
    created_at: datetime
