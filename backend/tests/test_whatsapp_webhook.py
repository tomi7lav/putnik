import hashlib
import hmac

import pytest


def _sign(payload: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


@pytest.mark.asyncio
async def test_webhook_get_verification_success(client):
    response = await client.get(
        "/api/v1/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "test-verify-token",
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
            "hub.verify_token": "test-verify-token",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_webhook_post_valid_signature(client):
    payload = b'{"entry":[{"id":"1"}]}'
    signature = _sign(payload, "test-app-secret")
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
