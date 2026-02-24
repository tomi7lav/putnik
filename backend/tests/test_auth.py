import pytest


@pytest.mark.asyncio
async def test_register_tenant_success(client):
    response = await client.post(
        "/api/v1/auth/register-tenant",
        json={
            "tenant_name": "Acme Travel",
            "tenant_slug": "acme-travel",
            "full_name": "Alex Agent",
            "email": "alex@acme.com",
            "password": "supersecure123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["token_type"] == "bearer"
    assert "access_token" in data
    assert "tenant_id" in data
    assert "user_id" in data


@pytest.mark.asyncio
async def test_register_duplicate_tenant_slug_rejected(client):
    payload = {
        "tenant_name": "Acme Travel",
        "tenant_slug": "dup-tenant",
        "full_name": "Alex Agent",
        "email": "alex@acme.com",
        "password": "supersecure123",
    }
    first = await client.post("/api/v1/auth/register-tenant", json=payload)
    second = await client.post(
        "/api/v1/auth/register-tenant",
        json={**payload, "email": "another@acme.com"},
    )

    assert first.status_code == 201
    assert second.status_code == 400
    assert second.json()["detail"] == "Tenant slug already exists"


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post(
        "/api/v1/auth/register-tenant",
        json={
            "tenant_name": "Orbit Trips",
            "tenant_slug": "orbit-trips",
            "full_name": "Owner",
            "email": "owner@orbit.com",
            "password": "supersecure123",
        },
    )

    login = await client.post(
        "/api/v1/auth/login",
        json={
            "tenant_slug": "orbit-trips",
            "email": "owner@orbit.com",
            "password": "supersecure123",
        },
    )
    assert login.status_code == 200
    data = login.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]


@pytest.mark.asyncio
async def test_login_wrong_password_rejected(client):
    await client.post(
        "/api/v1/auth/register-tenant",
        json={
            "tenant_name": "Zen Travel",
            "tenant_slug": "zen-travel",
            "full_name": "Owner",
            "email": "owner@zen.com",
            "password": "supersecure123",
        },
    )

    login = await client.post(
        "/api/v1/auth/login",
        json={
            "tenant_slug": "zen-travel",
            "email": "owner@zen.com",
            "password": "wrong-pass-123",
        },
    )
    assert login.status_code == 401
    assert login.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_same_email_allowed_across_different_tenants(client):
    first = await client.post(
        "/api/v1/auth/register-tenant",
        json={
            "tenant_name": "North Travel",
            "tenant_slug": "north-travel",
            "full_name": "Owner One",
            "email": "shared@example.com",
            "password": "supersecure123",
        },
    )
    second = await client.post(
        "/api/v1/auth/register-tenant",
        json={
            "tenant_name": "South Travel",
            "tenant_slug": "south-travel",
            "full_name": "Owner Two",
            "email": "shared@example.com",
            "password": "supersecure123",
        },
    )

    assert first.status_code == 201
    assert second.status_code == 201
