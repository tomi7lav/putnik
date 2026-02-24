# Travel SaaS Build Plan (WhatsApp-First)

## Vision

Build a single-thread travel experience where the entire customer journey runs in one WhatsApp conversation:

- lead capture and trip selection
- customization and upsells
- payments (individual + group)
- passport/flight logistics
- post-sales support

Target outcome: a "headless travel agency" with a clean operator dashboard and strong automation.

---

## MVP Scope (Must-Haves)

1. WhatsApp webhook + PydanticAI logic
2. Multi-tenant Postgres schema (Supabase)
3. Passport OCR pipeline
4. Stripe payment links

Tech stack:

- Backend: FastAPI + async SQLAlchemy + Alembic
- Database: Supabase Postgres
- Frontend: React + Next.js
- Messaging: WhatsApp Cloud API

---

## Product Lifecycle in One Chat Thread

### Phase 1: Registration and Trip Selection

- User enters from QR/deep link (campaign metadata)
- Agent sends curated package choices via buttons/media
- User selects package and initial booking object is created

### Phase 2: Customization and Upsell

- User requests changes (for example private pool)
- Agent quotes delta price and asks confirmation
- On confirmation, booking object updates and audit event is logged

### Phase 3: Payment Closing

- Agent generates Stripe payment link
- Group travel flow:
  - create invite links or traveler entries
  - track payment states per traveler
  - show agency progress (for example 2/4 paid)

### Phase 4: Flight Booking and Logistics

- Collect passport image in chat
- OCR extracts key fields (name, DOB, expiry, doc number)
- User verifies extracted data
- Agent offers flight options from provider APIs
- Ticket/boarding docs sent back to chat

### Phase 5: Post-Sales Support

- Contract and travel docs delivered in thread
- Real-time support in same conversation (driver lookup, GPS pin, etc.)

---

## System Architecture

### Backend (FastAPI)

- API routes under `app/api/v1`
- Service layer for business logic
- Repository/data access layer
- Agent orchestration layer for PydanticAI tool calls
- Background jobs for OCR, provider polling, document generation

### Database (Supabase/Postgres)

- Multi-tenant schema with strict `tenant_id` isolation
- Row Level Security (RLS) policies
- Idempotency tables for external webhook deduplication

### Frontend (Next.js)

- Operator dashboard:
  - conversation/inbox view
  - booking details
  - group payment progress
  - OCR/manual review queue
  - escalation/support queue

### Integrations

- WhatsApp Cloud API (inbound webhook + outbound templates/buttons)
- Stripe (payment link generation + webhook reconciliation)
- OCR provider (or local OCR service abstraction)
- Flight API provider abstraction

---

## Data Model (Initial)

Core tables:

- `tenants`
- `users`
- `contacts`
- `conversations`
- `bookings`
- `booking_items`
- `travelers`
- `group_invites`
- `payments`
- `documents`
- `flights`
- `message_events`
- `agent_actions`

Key design rules:

- Every business table includes `tenant_id`
- Unique constraints are tenant-scoped where relevant
- All external events are stored raw + normalized for audits/debugging
- Keep one flexible `booking_snapshot_json` for conversational agility

---

## API Surface (MVP)

### Auth and Tenant

- `POST /api/v1/auth/register-tenant`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me` (next step)

### WhatsApp

- `GET /api/v1/webhooks/whatsapp` (Meta verification)
- `POST /api/v1/webhooks/whatsapp` (signature-verified receiver)

### Booking and Payments (next increments)

- `POST /api/v1/bookings`
- `POST /api/v1/bookings/{id}/upsells`
- `POST /api/v1/bookings/{id}/payment-link`
- `POST /api/v1/bookings/{id}/group-invites`
- `POST /api/v1/webhooks/stripe`

### Documents and OCR (next increments)

- `POST /api/v1/documents/passport/ingest`
- `POST /api/v1/documents/contract/generate`
- `POST /api/v1/documents/ticket/issue`

---

## Security and Reliability Requirements

- Verify Meta webhook signatures (`X-Hub-Signature-256`)
- Verify Stripe webhook signatures
- Idempotency keys and deduplication for all webhook consumers
- JWT auth with tenant context in token claims
- Enforce tenant isolation server-side and in DB policies
- Encrypt/highly restrict PII fields and document access
- Full audit trail for agent decisions and human overrides

---

## Delivery Timeline (6 Weeks)

## Week 1 (In Progress)

- FastAPI scaffold and project structure
- Tenant + user schema and migrations
- JWT auth (register/login)
- WhatsApp verification and signature validation
- Baseline tests and CI

## Week 2

- Conversation state model (`contacts`, `conversations`, `message_events`)
- Booking object model (`bookings`, `booking_items`)
- Basic PydanticAI orchestration with safe tool calls
- Persist inbound/outbound message events

## Week 3

- Stripe payment links integration
- Group traveler/invite/payment tracking
- Dashboard API for group progress status
- Payment webhook reconciliation and retries

## Week 4

- Passport OCR ingestion flow
- Extraction confidence and human confirmation loop
- Traveler profile enrichment from OCR output

## Week 5

- Flight option retrieval and selection flow
- Ticket/boarding document generation and delivery
- Operational status transitions and alerting hooks

## Week 6

- Hardening and observability
- RLS policies and authz validation
- Retries, dead-letter strategy, and idempotency audits
- QA/UAT pass and release checklist

---

## Testing Strategy

### Unit Tests

- service-layer business rules
- signature verification helpers
- token encode/decode helpers

### Integration Tests

- auth flows
- webhook verification/signature flows
- payment webhook reconciliation
- OCR ingest endpoints

### E2E (later)

- WhatsApp simulated event -> booking update -> payment -> status update

---

## Operator Dashboard MVP (Next.js)

Initial pages:

- Inbox + booking side panel
- Booking detail timeline
- Group payment progress board
- OCR review queue
- Tenant settings

---

## Immediate Next Tasks

1. Add `auth/me` endpoint and role checks
2. Add `message_events` table and webhook event persistence
3. Add webhook idempotency storage and dedupe logic
4. Add Stripe service skeleton and webhook endpoint scaffolding
5. Add `contacts` + `conversations` schema migration
