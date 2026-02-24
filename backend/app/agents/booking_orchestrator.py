from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.booking_service import booking_service


class BookingOrchestrator:
    """
    Week 2 orchestration skeleton.

    This keeps agent-facing actions constrained to safe, explicit tools.
    """

    async def get_conversation_booking(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        conversation_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        booking = await booking_service.get_for_conversation(db, tenant_id, conversation_id)
        if not booking:
            return None
        return {
            "booking_id": str(booking.id),
            "conversation_id": str(booking.conversation_id),
            "status": booking.status,
            "currency": booking.currency,
            "total_cents": booking.total_cents,
        }

    async def create_booking(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        conversation_id: UUID,
        title: Optional[str],
        currency: str,
    ) -> Dict[str, Any]:
        booking = await booking_service.create_for_conversation(
            db=db,
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            title=title,
            currency=currency,
        )
        return {
            "booking_id": str(booking.id),
            "status": booking.status,
            "currency": booking.currency,
            "total_cents": booking.total_cents,
        }

    async def add_booking_item(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        booking_id: UUID,
        item_type: str,
        name: str,
        quantity: int,
        unit_price_cents: int,
    ) -> Dict[str, Any]:
        booking = await booking_service.add_item(
            db=db,
            tenant_id=tenant_id,
            booking_id=booking_id,
            item_type=item_type,
            name=name,
            quantity=quantity,
            unit_price_cents=unit_price_cents,
        )
        return {
            "booking_id": str(booking.id),
            "item_count": len(booking.items),
            "subtotal_cents": booking.subtotal_cents,
            "total_cents": booking.total_cents,
        }


booking_orchestrator = BookingOrchestrator()
