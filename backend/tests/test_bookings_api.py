from uuid import UUID
import os

import pytest
from sqlalchemy import select

from app.models.conversation import Conversation
from app.models.tenant import Tenant

WHATSAPP_APP_SECRET = os.getenv("WHATSAPP_APP_SECRET", "test-app-secret")


def _sign(payload: bytes, secret: str) -> str:
    import hashlib
    import hmac

    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


async def _create_tenant_and_conversation(client, db_session, tenant_slug: str, email: str, phone_number_id: str):
    register = await client.post(
        "/api/v1/auth/register-tenant",
        json={
            "tenant_name": f"{tenant_slug} Agency",
            "tenant_slug": tenant_slug,
            "full_name": "Owner",
            "email": email,
            "password": "supersecure123",
        },
    )
    assert register.status_code == 201
    tenant_id = UUID(register.json()["tenant_id"])
    token = register.json()["access_token"]

    tenant = await db_session.scalar(select(Tenant).where(Tenant.id == tenant_id))
    tenant.whatsapp_phone_number_id = phone_number_id
    await db_session.commit()

    payload = (
        b'{"entry":[{"changes":[{"value":{"metadata":{"phone_number_id":"'
        + phone_number_id.encode("utf-8")
        + b'"},"contacts":[{"wa_id":"15557770000","profile":{"name":"Traveler"}}],'
        + b'"messages":[{"id":"wamid-booking-'
        + tenant_slug.encode("utf-8")
        + b'","from":"15557770000"}]}}]}]}'
    )
    webhook = await client.post(
        "/api/v1/webhooks/whatsapp",
        content=payload,
        headers={"X-Hub-Signature-256": _sign(payload, WHATSAPP_APP_SECRET), "Content-Type": "application/json"},
    )
    assert webhook.status_code == 200

    conversation = await db_session.scalar(select(Conversation).where(Conversation.tenant_id == tenant_id))
    assert conversation is not None
    return token, tenant_id, conversation.id


@pytest.mark.asyncio
async def test_create_booking_for_conversation(client, db_session):
    token, _tenant_id, conversation_id = await _create_tenant_and_conversation(
        client, db_session, "booking-tenant-1", "one@agency.com", "pnid-booking-1"
    )

    response = await client.post(
        "/api/v1/bookings",
        headers={"Authorization": f"Bearer {token}"},
        json={"conversation_id": str(conversation_id), "title": "Bali Escape", "currency": "USD"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["conversation_id"] == str(conversation_id)
    assert data["title"] == "Bali Escape"
    assert data["subtotal_cents"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_add_booking_item_recalculates_totals(client, db_session):
    token, _tenant_id, conversation_id = await _create_tenant_and_conversation(
        client, db_session, "booking-tenant-2", "two@agency.com", "pnid-booking-2"
    )
    created = await client.post(
        "/api/v1/bookings",
        headers={"Authorization": f"Bearer {token}"},
        json={"conversation_id": str(conversation_id), "title": "Bali Adventure", "currency": "USD"},
    )
    booking_id = created.json()["id"]

    add_item = await client.post(
        f"/api/v1/bookings/{booking_id}/items",
        headers={"Authorization": f"Bearer {token}"},
        json={"item_type": "upgrade", "name": "Private Pool Upgrade", "quantity": 2, "unit_price_cents": 20000},
    )
    assert add_item.status_code == 200
    data = add_item.json()
    assert data["subtotal_cents"] == 40000
    assert data["total_cents"] == 40000
    assert len(data["items"]) == 1
    assert data["items"][0]["total_price_cents"] == 40000


@pytest.mark.asyncio
async def test_booking_access_is_tenant_isolated(client, db_session):
    token_a, _tenant_a_id, conversation_a_id = await _create_tenant_and_conversation(
        client, db_session, "booking-tenant-3a", "threea@agency.com", "pnid-booking-3a"
    )
    token_b, _tenant_b_id, _conversation_b_id = await _create_tenant_and_conversation(
        client, db_session, "booking-tenant-3b", "threeb@agency.com", "pnid-booking-3b"
    )

    created = await client.post(
        "/api/v1/bookings",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"conversation_id": str(conversation_a_id), "title": "Tenant A Booking", "currency": "USD"},
    )
    assert created.status_code == 201
    booking_id = created.json()["id"]

    forbidden = await client.get(f"/api/v1/bookings/{booking_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert forbidden.status_code == 404
