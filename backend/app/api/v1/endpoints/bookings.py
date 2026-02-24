from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.booking import Booking
from app.models.user import User
from app.schemas.booking import BookingCreateRequest, BookingItemCreateRequest, BookingResponse
from app.services.booking_service import booking_service

router = APIRouter()


def _to_response(booking: Booking) -> BookingResponse:
    return BookingResponse(
        id=booking.id,
        tenant_id=booking.tenant_id,
        conversation_id=booking.conversation_id,
        contact_id=booking.contact_id,
        title=booking.title,
        status=booking.status,
        currency=booking.currency,
        subtotal_cents=booking.subtotal_cents,
        total_cents=booking.total_cents,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
        items=[
            {
                "id": item.id,
                "item_type": item.item_type,
                "name": item.name,
                "quantity": item.quantity,
                "unit_price_cents": item.unit_price_cents,
                "total_price_cents": item.total_price_cents,
                "created_at": item.created_at,
            }
            for item in booking.items
        ],
    )


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    payload: BookingCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BookingResponse:
    try:
        booking = await booking_service.create_for_conversation(
            db=db,
            tenant_id=current_user.tenant_id,
            conversation_id=payload.conversation_id,
            title=payload.title,
            currency=payload.currency,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    booking = await booking_service.get_by_id(db, current_user.tenant_id, booking.id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return _to_response(booking)


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BookingResponse:
    booking = await booking_service.get_by_id(db, current_user.tenant_id, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return _to_response(booking)


@router.get("/conversation/{conversation_id}", response_model=Optional[BookingResponse])
async def get_booking_by_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Optional[BookingResponse]:
    booking = await booking_service.get_for_conversation(db, current_user.tenant_id, conversation_id)
    if not booking:
        return None
    return _to_response(booking)


@router.post("/{booking_id}/items", response_model=BookingResponse)
async def add_booking_item(
    booking_id: UUID,
    payload: BookingItemCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BookingResponse:
    try:
        booking = await booking_service.add_item(
            db=db,
            tenant_id=current_user.tenant_id,
            booking_id=booking_id,
            item_type=payload.item_type,
            name=payload.name,
            quantity=payload.quantity,
            unit_price_cents=payload.unit_price_cents,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _to_response(booking)
