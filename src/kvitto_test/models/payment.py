from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    SmallInteger,
    String,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kvitto_test.domain.payment import PaymentStatus
from kvitto_test.models.base import Base

if TYPE_CHECKING:
    from kvitto_test.models.payment_installment import PaymentInstallment
    from kvitto_test.models.promo_code import PromoCode
    from kvitto_test.models.tariff import Tariff


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint(
            "method IN ('card', 'sbp', 'installment')",
            name="ck_payments_method_valid",
        ),
        CheckConstraint(
            "status IN ('pending', 'succeeded', 'failed', 'refunded')",
            name="ck_payments_status_valid",
        ),
        CheckConstraint("amount > 0", name="ck_payments_amount_positive"),
        CheckConstraint("discount >= 0", name="ck_payments_discount_nonnegative"),
        CheckConstraint(
            "installment_months IS NULL OR installment_months IN (3, 6, 12)",
            name="ck_payments_installment_months_valid",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    tariff_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tariffs.id"), nullable=False
    )
    promo_code_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("promo_codes.id"), nullable=True
    )
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    method: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=PaymentStatus.PENDING.value,
        server_default=text("'pending'"),
    )
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    discount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    installment_months: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True
    )
    idempotency_key: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    tariff: Mapped[Tariff] = relationship(back_populates="payments")
    promo_code: Mapped[PromoCode | None] = relationship(back_populates="payments")
    installments: Mapped[list[PaymentInstallment]] = relationship(
        back_populates="payment"
    )
