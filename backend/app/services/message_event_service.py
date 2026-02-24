from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message_event import MessageEvent


class MessageEventService:
    async def exists_by_idempotency_key(self, db: AsyncSession, idempotency_key: str) -> bool:
        existing = await db.scalar(select(MessageEvent.id).where(MessageEvent.idempotency_key == idempotency_key))
        return existing is not None

    async def create_inbound_whatsapp_event(
        self,
        db: AsyncSession,
        payload_json: dict,
        idempotency_key: str,
        external_event_id: Optional[str],
        tenant_id: Optional[UUID] = None,
        conversation_id: Optional[UUID] = None,
    ) -> MessageEvent:
        event = MessageEvent(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            provider="whatsapp",
            direction="inbound",
            event_type="webhook",
            external_event_id=external_event_id,
            idempotency_key=idempotency_key,
            payload_json=payload_json,
        )
        db.add(event)
        await db.flush()
        await db.refresh(event)
        return event


message_event_service = MessageEventService()
