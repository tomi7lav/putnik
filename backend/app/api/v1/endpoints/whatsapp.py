from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.whatsapp import WebhookAckResponse
from app.services.message_event_service import message_event_service
from app.services.whatsapp_service import whatsapp_service

router = APIRouter()


@router.get("")
async def verify_webhook(
    mode: Optional[str] = Query(default=None, alias="hub.mode"),
    token: Optional[str] = Query(default=None, alias="hub.verify_token"),
    challenge: Optional[str] = Query(default=None, alias="hub.challenge"),
) -> str:
    if not whatsapp_service.verify_subscription_token(mode=mode, verify_token=token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Webhook verification failed")
    if challenge is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing hub.challenge")
    return challenge


@router.post("", response_model=WebhookAckResponse, status_code=status.HTTP_200_OK)
async def receive_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(default=None, alias="X-Hub-Signature-256"),
    db: AsyncSession = Depends(get_db),
) -> WebhookAckResponse:
    raw_payload = await request.body()
    if not whatsapp_service.verify_signature(raw_payload, x_hub_signature_256):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")

    payload_json = whatsapp_service.parse_payload(raw_payload)
    idempotency_key = whatsapp_service.build_idempotency_key(payload_json)
    external_event_id = whatsapp_service.extract_external_event_id(payload_json)

    if await message_event_service.exists_by_idempotency_key(db, idempotency_key):
        return WebhookAckResponse(received=True)

    await message_event_service.create_inbound_whatsapp_event(
        db=db,
        payload_json=payload_json,
        idempotency_key=idempotency_key,
        external_event_id=external_event_id,
    )
    return WebhookAckResponse(received=True)
