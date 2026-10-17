from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from uuid import UUID


class PaymentMethod(str, Enum):
    CARD = "card"
    SBP = "sbp"
    INSTALLMENT = "installment"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


ALLOWED_STATUS_TRANSITIONS: dict[PaymentStatus, frozenset[PaymentStatus]] = {
    PaymentStatus.PENDING: frozenset({PaymentStatus.SUCCEEDED, PaymentStatus.FAILED}),
    PaymentStatus.SUCCEEDED: frozenset({PaymentStatus.REFUNDED}),
}


def can_transition(current: PaymentStatus, target: PaymentStatus) -> bool:
    return target in ALLOWED_STATUS_TRANSITIONS.get(current, frozenset())


@dataclass(frozen=True, slots=True)
class PromoCode:
    id: UUID
    discount_percent: int


@dataclass(frozen=True, slots=True)
class Payment:
    id: UUID
    tariff_id: UUID
    promo_code_id: UUID | None
    email: str
    method: PaymentMethod
    status: PaymentStatus
    amount: int
    discount: int
    installment_months: int | None
    schedule: list[int] | None
    created_at: datetime | None = None


def calculate_discount(price: int, percent: int) -> int:
    return int(
        (Decimal(price) * Decimal(percent) / 100).quantize(
            Decimal(1), rounding=ROUND_HALF_UP
        )
    )


def installment_schedule(amount: int, months: int) -> list[int]:
    if amount < months:
        raise ValueError("Installment amount must be at least one kopeck per month")
    base, remainder = divmod(amount, months)
    return [base + (index < remainder) for index in range(months)]
