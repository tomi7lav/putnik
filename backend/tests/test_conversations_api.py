from uuid import UUID
from typing import Tuple

import pytest
from sqlalchemy import select

from app.models.conversation import Conversation
from app.models.tenant import Tenant


def _sign(payload: bytes, secret: str) -> str:
    import hashlib
    import hmac

    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


async def _create_tenant_and_token(client, slug: str, email: str) -> Tuple[UUID, str]:
    register = await client.post(
        "/api/v1/auth/register-tenant",
        json={
            "tenant_name": f"{slug} Agency",
            "tenant_slug": slug,
            "full_name": "Owner",
            "email": email,
            "password": "supersecure123",
        },
    )
    assert register.status_code == 201
    return UUID(register.json()["tenant_id"]), register.json()["access_token"]


@pytest.mark.asyncio
async def test_list_conversations_returns_tenant_scoped_results(client, db_session):
    tenant_id, token = await _create_tenant_and_token(client, "conv-tenant-a", "a@agency.com")
    tenant = await db_session.scalar(select(Tenant).where(Tenant.id == tenant_id))
    tenant.whatsapp_phone_number_id = "pnid-a"
    await db_session.commit()

    payload = (
        b'{"entry":[{"changes":[{"value":{"metadata":{"phone_number_id":"pnid-a"},'
        b'"contacts":[{"wa_id":"15550000001","profile":{"name":"Alex"}}],'
        b'"messages":[{"id":"wamid-conv-a","from":"15550000001"}]}}]}]}'
    )
    signature = _sign(payload, "test-app-secret")
    webhook = await client.post(
        "/api/v1/webhooks/whatsapp",
        content=payload,
        headers={"X-Hub-Signature-256": signature, "Content-Type": "application/json"},
    )
    assert webhook.status_code == 200

    response = await client.get("/api/v1/conversations", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["phone_number"] == "15550000001"
    assert data[0]["contact_name"] == "Alex"


@pytest.mark.asyncio
async def test_list_conversation_events_returns_events_for_tenant_conversation(client, db_session):
    tenant_id, token = await _create_tenant_and_token(client, "conv-tenant-b", "b@agency.com")
    tenant = await db_session.scalar(select(Tenant).where(Tenant.id == tenant_id))
    tenant.whatsapp_phone_number_id = "pnid-b"
    await db_session.commit()

    payload = (
        b'{"entry":[{"changes":[{"value":{"metadata":{"phone_number_id":"pnid-b"},'
        b'"contacts":[{"wa_id":"15550000002","profile":{"name":"Blair"}}],'
        b'"messages":[{"id":"wamid-conv-b","from":"15550000002"}]}}]}]}'
    )
    signature = _sign(payload, "test-app-secret")
    webhook = await client.post(
        "/api/v1/webhooks/whatsapp",
        content=payload,
        headers={"X-Hub-Signature-256": signature, "Content-Type": "application/json"},
    )
    assert webhook.status_code == 200

    conversation = await db_session.scalar(select(Conversation).where(Conversation.tenant_id == tenant_id))
    assert conversation is not None

    events = await client.get(
        f"/api/v1/conversations/{conversation.id}/events",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert events.status_code == 200
    body = events.json()
    assert len(body) == 1
    assert body[0]["external_event_id"] == "wamid-conv-b"


@pytest.mark.asyncio
async def test_list_conversation_events_is_tenant_isolated(client, db_session):
    tenant_a_id, token_a = await _create_tenant_and_token(client, "conv-tenant-c1", "c1@agency.com")
    tenant_b_id, token_b = await _create_tenant_and_token(client, "conv-tenant-c2", "c2@agency.com")

    tenant_a = await db_session.scalar(select(Tenant).where(Tenant.id == tenant_a_id))
    tenant_b = await db_session.scalar(select(Tenant).where(Tenant.id == tenant_b_id))
    tenant_a.whatsapp_phone_number_id = "pnid-c1"
    tenant_b.whatsapp_phone_number_id = "pnid-c2"
    await db_session.commit()

    payload_a = (
        b'{"entry":[{"changes":[{"value":{"metadata":{"phone_number_id":"pnid-c1"},'
        b'"contacts":[{"wa_id":"15550000003","profile":{"name":"Casey"}}],'
        b'"messages":[{"id":"wamid-conv-c1","from":"15550000003"}]}}]}]}'
    )
    signature_a = _sign(payload_a, "test-app-secret")
    webhook_a = await client.post(
        "/api/v1/webhooks/whatsapp",
        content=payload_a,
        headers={"X-Hub-Signature-256": signature_a, "Content-Type": "application/json"},
    )
    assert webhook_a.status_code == 200

    conversation_a = await db_session.scalar(select(Conversation).where(Conversation.tenant_id == tenant_a_id))
    assert conversation_a is not None

    own = await client.get(
        f"/api/v1/conversations/{conversation_a.id}/events",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert own.status_code == 200

    other_tenant = await client.get(
        f"/api/v1/conversations/{conversation_a.id}/events",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert other_tenant.status_code == 404
