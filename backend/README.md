# Putnik Backend (Week 1)

FastAPI scaffold with:

- multi-tenant auth foundations (`tenants`, `users`)
- JWT login/register tenant admin
- WhatsApp webhook verification (`hub.challenge`)
- WhatsApp webhook signature validation (`X-Hub-Signature-256`)

## Quick start

From repo root, you can also use:

```bash
make backend-venv
make backend-install
make backend-test
```

Or run API/migrations:

```bash
make backend-run
make backend-migrate
```

1. Create venv and install:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Set env vars:

```bash
cp .env.example .env
```

3. Run migrations:

```bash
alembic upgrade head
```

4. Start API:

```bash
uvicorn app.main:app --reload
```

## Auth endpoints

- `POST /api/v1/auth/register-tenant`
- `POST /api/v1/auth/login`

## WhatsApp endpoints

- `GET /api/v1/webhooks/whatsapp` (Meta verification)
- `POST /api/v1/webhooks/whatsapp` (signature verified event receiver)
