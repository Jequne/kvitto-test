from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from kvitto_test.schemas.enums import PaymentStatus


class PaymentWebhookRequest(BaseModel):
    payment_id: UUID
    status: PaymentStatus


class PaymentWebhookResponse(BaseModel):
    result: Literal["ok"]


class InvalidTransitionResponse(BaseModel):
    error: Literal["invalid_transition"]
