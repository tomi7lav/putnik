from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.booking import Booking
from app.models.booking_item import BookingItem
from app.models.conversation import Conversation


class BookingService:
    async def get_for_conversation(self, db: AsyncSession, tenant_id: UUID, conversation_id: UUID) -> Optional[Booking]:
        return await db.scalar(
            select(Booking)
            .where(Booking.tenant_id == tenant_id, Booking.conversation_id == conversation_id)
            .options(selectinload(Booking.items))
        )

    async def get_by_id(self, db: AsyncSession, tenant_id: UUID, booking_id: UUID) -> Optional[Booking]:
        return await db.scalar(
            select(Booking)
            .where(Booking.tenant_id == tenant_id, Booking.id == booking_id)
            .options(selectinload(Booking.items))
        )

    async def create_for_conversation(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        conversation_id: UUID,
        title: Optional[str],
        currency: str,
    ) -> Booking:
        existing = await self.get_for_conversation(db, tenant_id, conversation_id)
        if existing:
            return existing

        conversation = await db.scalar(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.tenant_id == tenant_id,
            )
        )
        if not conversation:
            raise ValueError("Conversation not found")

        booking = Booking(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            contact_id=conversation.contact_id,
            title=title,
            currency=currency.upper(),
            status="draft",
            subtotal_cents=0,
            total_cents=0,
        )
        db.add(booking)
        await db.flush()
        await db.refresh(booking)
        return booking

    async def add_item(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        booking_id: UUID,
        item_type: str,
        name: str,
        quantity: int,
        unit_price_cents: int,
    ) -> Booking:
        booking = await self.get_by_id(db, tenant_id, booking_id)
        if not booking:
            raise ValueError("Booking not found")

        total_price_cents = quantity * unit_price_cents
        item = BookingItem(
            tenant_id=tenant_id,
            booking_id=booking.id,
            item_type=item_type,
            name=name,
            quantity=quantity,
            unit_price_cents=unit_price_cents,
            total_price_cents=total_price_cents,
        )
        db.add(item)
        await db.flush()

        await self._recalculate_totals(db, booking)
        await db.refresh(booking)
        booking = await self.get_by_id(db, tenant_id, booking_id)
        return booking  # type: ignore[return-value]

    async def _recalculate_totals(self, db: AsyncSession, booking: Booking) -> None:
        rows = (
            await db.execute(select(BookingItem.total_price_cents).where(BookingItem.booking_id == booking.id))
        ).scalars()
        subtotal = sum(rows)
        booking.subtotal_cents = subtotal
        booking.total_cents = subtotal
        await db.flush()


booking_service = BookingService()
