from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    SmallInteger,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kvitto_test.models.base import Base

if TYPE_CHECKING:
    from kvitto_test.models.payment import Payment


class PaymentInstallment(Base):
    __tablename__ = "payment_installments"
    __table_args__ = (
        CheckConstraint(
            "sequence > 0", name="ck_payment_installments_sequence_positive"
        ),
        CheckConstraint("amount > 0", name="ck_payment_installments_amount_positive"),
        UniqueConstraint(
            "payment_id", "sequence", name="uq_payment_installments_payment_sequence"
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    payment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("payments.id"), nullable=False
    )
    sequence: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)

    payment: Mapped[Payment] = relationship(back_populates="installments")
