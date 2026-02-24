from __future__ import annotations

from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.models.conversation import Conversation
from app.models.tenant import Tenant


class ConversationService:
    @staticmethod
    def _extract_value(payload: dict) -> dict:
        entries = payload.get("entry", [])
        if not entries:
            return {}
        changes = entries[0].get("changes", [])
        if not changes:
            return {}
        return changes[0].get("value", {}) or {}

    def extract_phone_number_id(self, payload: dict) -> Optional[str]:
        value = self._extract_value(payload)
        metadata = value.get("metadata", {}) or {}
        phone_number_id = metadata.get("phone_number_id")
        return str(phone_number_id) if phone_number_id else None

    def extract_sender_data(self, payload: dict) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        value = self._extract_value(payload)
        sender_phone = None
        sender_wa_id = None
        sender_name = None

        contacts = value.get("contacts", []) or []
        if contacts:
            sender_wa_id = contacts[0].get("wa_id")
            profile = contacts[0].get("profile", {}) or {}
            sender_name = profile.get("name")

        messages = value.get("messages", []) or []
        if messages and messages[0].get("from"):
            sender_phone = str(messages[0].get("from"))
        elif sender_wa_id:
            sender_phone = str(sender_wa_id)

        if sender_wa_id is not None:
            sender_wa_id = str(sender_wa_id)
        if sender_name is not None:
            sender_name = str(sender_name)
        return sender_phone, sender_wa_id, sender_name

    async def resolve_inbound_context(self, db: AsyncSession, payload: dict) -> Tuple[Optional[UUID], Optional[UUID]]:
        phone_number_id = self.extract_phone_number_id(payload)
        if not phone_number_id:
            return None, None

        tenant = await db.scalar(
            select(Tenant).where(Tenant.whatsapp_phone_number_id == phone_number_id, Tenant.status == "active")
        )
        if not tenant:
            return None, None

        sender_phone, sender_wa_id, sender_name = self.extract_sender_data(payload)
        if not sender_phone:
            return tenant.id, None

        contact = await db.scalar(
            select(Contact).where(Contact.tenant_id == tenant.id, Contact.phone_number == sender_phone)
        )
        if not contact:
            contact = Contact(
                tenant_id=tenant.id,
                phone_number=sender_phone,
                wa_contact_id=sender_wa_id,
                full_name=sender_name,
            )
            db.add(contact)
            await db.flush()
        else:
            changed = False
            if sender_wa_id and not contact.wa_contact_id:
                contact.wa_contact_id = sender_wa_id
                changed = True
            if sender_name and not contact.full_name:
                contact.full_name = sender_name
                changed = True
            if changed:
                await db.flush()

        conversation = await db.scalar(
            select(Conversation).where(
                Conversation.tenant_id == tenant.id,
                Conversation.contact_id == contact.id,
                Conversation.channel == "whatsapp",
                Conversation.status == "active",
            )
        )
        if not conversation:
            external_thread_id = sender_wa_id or sender_phone
            conversation = Conversation(
                tenant_id=tenant.id,
                contact_id=contact.id,
                channel="whatsapp",
                status="active",
                external_thread_id=external_thread_id,
            )
            db.add(conversation)
            await db.flush()

        return tenant.id, conversation.id


conversation_service = ConversationService()
