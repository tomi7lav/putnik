from __future__ import annotations

import json
import hashlib
import hmac
from typing import Optional

from app.core.config import get_settings

settings = get_settings()


class WhatsAppService:
    @staticmethod
    def verify_subscription_token(mode: Optional[str], verify_token: Optional[str]) -> bool:
        return mode == "subscribe" and verify_token == settings.whatsapp_verify_token

    @staticmethod
    def verify_signature(raw_body: bytes, signature_header: Optional[str]) -> bool:
        if not signature_header or not signature_header.startswith("sha256="):
            return False
        expected = hmac.new(settings.whatsapp_app_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
        provided = signature_header.split("sha256=", maxsplit=1)[1]
        return hmac.compare_digest(expected, provided)

    @staticmethod
    def parse_payload(raw_body: bytes) -> dict:
        try:
            return json.loads(raw_body.decode("utf-8"))
        except Exception:
            return {"_raw": raw_body.decode("utf-8", errors="replace")}

    @staticmethod
    def extract_external_event_id(payload: dict) -> Optional[str]:
        try:
            entries = payload.get("entry", [])
            for entry in entries:
                changes = entry.get("changes", [])
                for change in changes:
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    if messages and messages[0].get("id"):
                        return messages[0]["id"]
                if entry.get("id"):
                    return str(entry["id"])
        except Exception:
            return None
        return None

    @staticmethod
    def build_idempotency_key(payload: dict) -> str:
        external_id = WhatsAppService.extract_external_event_id(payload)
        if external_id:
            return f"whatsapp:{external_id}"
        payload_digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
        return f"whatsapp:hash:{payload_digest}"


whatsapp_service = WhatsAppService()
