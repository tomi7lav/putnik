from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.contact import Contact
from app.models.conversation import Conversation
from app.models.message_event import MessageEvent
from app.models.user import User
from app.schemas.conversation import ConversationListItemResponse, MessageEventListItemResponse

router = APIRouter()


@router.get("", response_model=List[ConversationListItemResponse])
async def list_conversations(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    phone: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ConversationListItemResponse]:
    query = (
        select(Conversation, Contact)
        .join(Contact, Contact.id == Conversation.contact_id)
        .where(Conversation.tenant_id == current_user.tenant_id)
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )

    if status_filter:
        query = query.where(Conversation.status == status_filter)
    if phone:
        query = query.where(Contact.phone_number == phone)

    rows = (await db.execute(query)).all()
    return [
        ConversationListItemResponse(
            id=conversation.id,
            contact_id=conversation.contact_id,
            contact_name=contact.full_name,
            phone_number=contact.phone_number,
            channel=conversation.channel,
            status=conversation.status,
            external_thread_id=conversation.external_thread_id,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )
        for conversation, contact in rows
    ]


@router.get("/{conversation_id}/events", response_model=List[MessageEventListItemResponse])
async def list_conversation_events(
    conversation_id: UUID,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[MessageEventListItemResponse]:
    conversation = await db.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.tenant_id == current_user.tenant_id,
        )
    )
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    events = (
        await db.execute(
            select(MessageEvent)
            .where(
                MessageEvent.conversation_id == conversation_id,
                MessageEvent.tenant_id == current_user.tenant_id,
            )
            .order_by(MessageEvent.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    ).scalars()

    return [
        MessageEventListItemResponse(
            id=event.id,
            provider=event.provider,
            direction=event.direction,
            event_type=event.event_type,
            external_event_id=event.external_event_id,
            idempotency_key=event.idempotency_key,
            payload_json=event.payload_json,
            received_at=event.received_at,
            created_at=event.created_at,
        )
        for event in events
    ]
