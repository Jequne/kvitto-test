from datetime import datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, model_validator

from kvitto_test.schemas.enums import PaymentMethod, PaymentStatus


class PaymentCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tariff_id: UUID
    email: EmailStr
    method: PaymentMethod
    installment_months: Literal[3, 6, 12] | None = None
    promo_code: str | None = None

    @model_validator(mode="after")
    def validate_installment_months(self) -> Self:
        if self.method == PaymentMethod.INSTALLMENT:
            if self.installment_months is None:
                raise ValueError("installment_months is required for installment")
        elif self.installment_months is not None:
            raise ValueError("installment_months is only allowed for installment")
        return self


class PaymentResponse(BaseModel):
    id: UUID
    status: PaymentStatus
    tariff_id: UUID
    amount: int
    discount: int
    method: PaymentMethod
    installment_months: int | None
    schedule: list[int] | None
    email: EmailStr
    created_at: datetime
