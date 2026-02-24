import hashlib
import hmac
import os
from uuid import UUID

import pytest
from sqlalchemy import select

from app.models.contact import Contact
from app.models.conversation import Conversation
from app.models.message_event import MessageEvent
from app.models.tenant import Tenant

WHATSAPP_APP_SECRET = os.getenv("WHATSAPP_APP_SECRET", "test-app-secret")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "test-verify-token")


def _sign(payload: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


@pytest.mark.asyncio
async def test_webhook_get_verification_success(client):
    response = await client.get(
        "/api/v1/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": WHATSAPP_VERIFY_TOKEN,
            "hub.challenge": "12345",
        },
    )
    assert response.status_code == 200
    assert response.text == '"12345"'


@pytest.mark.asyncio
async def test_webhook_get_verification_wrong_token(client):
    response = await client.get(
        "/api/v1/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong-token",
            "hub.challenge": "12345",
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_webhook_get_verification_missing_challenge(client):
    response = await client.get(
        "/api/v1/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": WHATSAPP_VERIFY_TOKEN,
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_webhook_post_valid_signature(client):
    payload = b'{"entry":[{"id":"entry-1"}]}'
    signature = _sign(payload, WHATSAPP_APP_SECRET)
    response = await client.post(
        "/api/v1/webhooks/whatsapp",
        content=payload,
        headers={"X-Hub-Signature-256": signature, "Content-Type": "application/json"},
    )
    assert response.status_code == 200
    assert response.json() == {"received": True}


@pytest.mark.asyncio
async def test_webhook_post_missing_signature_rejected(client):
    payload = b'{"entry":[{"id":"1"}]}'
    response = await client.post("/api/v1/webhooks/whatsapp", content=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_webhook_post_invalid_signature_rejected(client):
    payload = b'{"entry":[{"id":"1"}]}'
    response = await client.post(
        "/api/v1/webhooks/whatsapp",
        content=payload,
        headers={"X-Hub-Signature-256": "sha256=notavalidsignature"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_webhook_post_persists_message_event(client, db_session):
    payload = b'{"entry":[{"changes":[{"value":{"messages":[{"id":"wamid-A"}]}}]}]}'
    signature = _sign(payload, WHATSAPP_APP_SECRET)
    response = await client.post(
        "/api/v1/webhooks/whatsapp",
        content=payload,
        headers={"X-Hub-Signature-256": signature, "Content-Type": "application/json"},
    )
    assert response.status_code == 200

    events = (await db_session.execute(select(MessageEvent))).scalars().all()
    assert len(events) == 1
    assert events[0].external_event_id == "wamid-A"


@pytest.mark.asyncio
async def test_webhook_post_deduplicates_by_event_id(client, db_session):
    payload = b'{"entry":[{"changes":[{"value":{"messages":[{"id":"wamid-dup"}]}}]}]}'
    signature = _sign(payload, WHATSAPP_APP_SECRET)

    first = await client.post(
        "/api/v1/webhooks/whatsapp",
        content=payload,
        headers={"X-Hub-Signature-256": signature, "Content-Type": "application/json"},
    )
    second = await client.post(
        "/api/v1/webhooks/whatsapp",
        content=payload,
        headers={"X-Hub-Signature-256": signature, "Content-Type": "application/json"},
    )
    assert first.status_code == 200
    assert second.status_code == 200

    events = (await db_session.execute(select(MessageEvent))).scalars().all()
    assert len(events) == 1
    assert events[0].idempotency_key == "whatsapp:wamid-dup"


@pytest.mark.asyncio
async def test_webhook_post_resolves_tenant_contact_and_conversation(client, db_session):
    register = await client.post(
        "/api/v1/auth/register-tenant",
        json={
            "tenant_name": "Webhook Agency",
            "tenant_slug": "webhook-agency",
            "full_name": "Owner",
            "email": "owner@agency.com",
            "password": "supersecure123",
        },
    )
    assert register.status_code == 201
    tenant_id = UUID(register.json()["tenant_id"])

    tenant = await db_session.scalar(select(Tenant).where(Tenant.id == tenant_id))
    tenant.whatsapp_phone_number_id = "pnid-123"
    await db_session.commit()

    payload = (
        b'{"entry":[{"changes":[{"value":{"metadata":{"phone_number_id":"pnid-123"},'
        b'"contacts":[{"wa_id":"15551234567","profile":{"name":"Alex"}}],'
        b'"messages":[{"id":"wamid-contact-1","from":"15551234567"}]}}]}]}'
    )
    signature = _sign(payload, WHATSAPP_APP_SECRET)
    response = await client.post(
        "/api/v1/webhooks/whatsapp",
        content=payload,
        headers={"X-Hub-Signature-256": signature, "Content-Type": "application/json"},
    )
    assert response.status_code == 200

    contact = await db_session.scalar(
        select(Contact).where(Contact.tenant_id == tenant_id, Contact.phone_number == "15551234567")
    )
    assert contact is not None
    assert contact.full_name == "Alex"

    conversation = await db_session.scalar(
        select(Conversation).where(
            Conversation.tenant_id == tenant_id,
            Conversation.contact_id == contact.id,
            Conversation.channel == "whatsapp",
        )
    )
    assert conversation is not None

    event = await db_session.scalar(select(MessageEvent).where(MessageEvent.external_event_id == "wamid-contact-1"))
    assert event is not None
    assert event.tenant_id == tenant_id
    assert event.conversation_id == conversation.id
