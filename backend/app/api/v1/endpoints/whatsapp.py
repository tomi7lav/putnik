from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Header, HTTPException, Query, Request, status

from app.schemas.whatsapp import WebhookAckResponse
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
) -> WebhookAckResponse:
    payload = await request.body()
    if not whatsapp_service.verify_signature(payload, x_hub_signature_256):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")

    # Week 1: acknowledge and keep raw payload in memory only.
    # Week 2 will persist message events and invoke PydanticAI orchestration.
    _ = payload
    return WebhookAckResponse(received=True)
