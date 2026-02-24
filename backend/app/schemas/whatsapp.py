from pydantic import BaseModel, ConfigDict


class WebhookVerificationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    challenge: str


class WebhookAckResponse(BaseModel):
    received: bool = True
