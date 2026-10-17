from dataclasses import replace
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from kvitto_test.domain.payment import (
    Payment as DomainPayment,
)
from kvitto_test.domain.payment import (
    PaymentMethod,
    PaymentStatus,
)
from kvitto_test.domain.payment import (
    PromoCode as DomainPromoCode,
)
from kvitto_test.domain.tariff import Tariff as DomainTariff
from kvitto_test.models.payment import Payment
from kvitto_test.models.payment_installment import PaymentInstallment
from kvitto_test.models.promo_code import PromoCode
from kvitto_test.models.tariff import Tariff


class SqlAlchemyPaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_tariff(self, tariff_id: UUID) -> DomainTariff | None:
        row = await self._session.get(Tariff, tariff_id)
        if row is None:
            return None
        return DomainTariff(
            id=row.id, code=row.code, title=row.title, price=row.price
        )

    async def get_promo_code(self, code: str) -> DomainPromoCode | None:
        row = await self._session.scalar(
            select(PromoCode).where(
                func.upper(PromoCode.code) == code, PromoCode.is_active
            )
        )
        if row is None:
            return None
        return DomainPromoCode(id=row.id, discount_percent=row.discount_percent)

    async def get_by_id(self, payment_id: UUID) -> DomainPayment | None:
        row = await self._session.scalar(
            select(Payment)
            .options(selectinload(Payment.installments))
            .where(Payment.id == payment_id)
        )
        return self._to_domain(row) if row is not None else None

    async def list_payments(
        self, email: str | None, status: PaymentStatus | None
    ) -> list[DomainPayment]:
        statement = select(Payment).options(selectinload(Payment.installments))
        if email is not None:
            statement = statement.where(Payment.email == email)
        if status is not None:
            statement = statement.where(Payment.status == status.value)
        statement = statement.order_by(Payment.created_at.desc(), Payment.id.desc())
        rows = (await self._session.scalars(statement)).all()
        return [self._to_domain(row) for row in rows]

    async def get_by_key(self, key: str) -> DomainPayment | None:
        row = await self._session.scalar(
            select(Payment)
            .options(selectinload(Payment.installments))
            .where(Payment.idempotency_key == key)
        )
        return self._to_domain(row) if row is not None else None

    async def add(
        self, payment: DomainPayment, key: str | None
    ) -> DomainPayment | None:
        statement = insert(Payment).values(
            id=payment.id,
            tariff_id=payment.tariff_id,
            promo_code_id=payment.promo_code_id,
            email=payment.email,
            method=payment.method.value,
            status=payment.status.value,
            amount=payment.amount,
            discount=payment.discount,
            installment_months=payment.installment_months,
            idempotency_key=key,
        )
        if key is not None:
            statement = statement.on_conflict_do_nothing(
                constraint="payments_idempotency_key_key"
            )
        created_at = await self._session.scalar(
            statement.returning(Payment.created_at)
        )
        if created_at is None:
            return None
        if payment.schedule is not None:
            self._session.add_all(
                PaymentInstallment(
                    payment_id=payment.id, sequence=index, amount=amount
                )
                for index, amount in enumerate(payment.schedule, start=1)
            )
            await self._session.flush()
        return replace(payment, created_at=created_at)

    async def update_status(
        self, payment_id: UUID, current: PaymentStatus, target: PaymentStatus
    ) -> bool:
        updated_id = await self._session.scalar(
            update(Payment)
            .where(Payment.id == payment_id, Payment.status == current.value)
            .values(status=target.value)
            .returning(Payment.id)
        )
        return updated_id is not None

    @staticmethod
    def _to_domain(row: Payment) -> DomainPayment:
        return DomainPayment(
            id=row.id,
            tariff_id=row.tariff_id,
            promo_code_id=row.promo_code_id,
            email=row.email,
            method=PaymentMethod(row.method),
            status=PaymentStatus(row.status),
            amount=row.amount,
            discount=row.discount,
            installment_months=row.installment_months,
            schedule=(
                [
                    item.amount
                    for item in sorted(row.installments, key=lambda x: x.sequence)
                ]
                if row.installment_months is not None
                else None
            ),
            created_at=row.created_at,
        )
