from __future__ import annotations

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


whatsapp_service = WhatsAppService()
