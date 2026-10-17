from dataclasses import dataclass
from typing import Protocol
from uuid import UUID, uuid4

from kvitto_test.domain.payment import (
    Payment,
    PaymentMethod,
    PaymentStatus,
    PromoCode,
    calculate_discount,
    can_transition,
    installment_schedule,
)
from kvitto_test.domain.tariff import Tariff


@dataclass(frozen=True, slots=True)
class CreatePaymentCommand:
    tariff_id: UUID
    email: str
    method: PaymentMethod
    installment_months: int | None
    promo_code: str | None
    idempotency_key: str | None


@dataclass(frozen=True, slots=True)
class CreatePaymentResult:
    payment: Payment
    created: bool


class PaymentRepository(Protocol):
    async def get_tariff(self, tariff_id: UUID) -> Tariff | None: ...

    async def get_promo_code(self, code: str) -> PromoCode | None: ...

    async def get_by_id(self, payment_id: UUID) -> Payment | None: ...

    async def list_payments(
        self, email: str | None, status: PaymentStatus | None
    ) -> list[Payment]: ...

    async def get_by_key(self, key: str) -> Payment | None: ...

    async def add(self, payment: Payment, key: str | None) -> Payment | None: ...

    async def update_status(
        self, payment_id: UUID, current: PaymentStatus, target: PaymentStatus
    ) -> bool: ...


class PaymentNotFoundError(Exception):
    pass


class InvalidPromoCodeError(Exception):
    pass


class InvalidAmountError(Exception):
    pass


class InvalidTransitionError(Exception):
    pass


class PaymentService:
    def __init__(self, repository: PaymentRepository) -> None:
        self._repository = repository

    async def create(self, command: CreatePaymentCommand) -> CreatePaymentResult:
        if command.idempotency_key is not None:
            existing = await self._repository.get_by_key(command.idempotency_key)
            if existing is not None:
                return CreatePaymentResult(payment=existing, created=False)

        tariff = await self._repository.get_tariff(command.tariff_id)
        if tariff is None:
            raise PaymentNotFoundError

        promo = None
        if command.promo_code is not None:
            promo = await self._repository.get_promo_code(
                command.promo_code.strip().upper()
            )
            if promo is None:
                raise InvalidPromoCodeError

        discount = calculate_discount(
            tariff.price, promo.discount_percent if promo is not None else 0
        )
        amount = tariff.price - discount
        if amount <= 0:
            raise InvalidAmountError

        try:
            schedule = (
                installment_schedule(amount, command.installment_months)
                if command.installment_months is not None
                else None
            )
        except ValueError as exc:
            raise InvalidAmountError from exc

        payment = Payment(
            id=uuid4(),
            tariff_id=tariff.id,
            promo_code_id=promo.id if promo is not None else None,
            email=command.email,
            method=command.method,
            status=PaymentStatus.PENDING,
            amount=amount,
            discount=discount,
            installment_months=command.installment_months,
            schedule=schedule,
        )
        saved = await self._repository.add(payment, command.idempotency_key)
        if saved is not None:
            return CreatePaymentResult(payment=saved, created=True)

        assert command.idempotency_key is not None
        existing = await self._repository.get_by_key(command.idempotency_key)
        if existing is None:
            raise RuntimeError("Payment disappeared after idempotency conflict")
        return CreatePaymentResult(payment=existing, created=False)

    async def get(self, payment_id: UUID) -> Payment:
        payment = await self._repository.get_by_id(payment_id)
        if payment is None:
            raise PaymentNotFoundError
        return payment

    async def list_payments(
        self, email: str | None = None, status: PaymentStatus | None = None
    ) -> list[Payment]:
        return await self._repository.list_payments(email, status)

    async def change_status(self, payment_id: UUID, target: PaymentStatus) -> None:
        payment = await self.get(payment_id)
        if not can_transition(payment.status, target):
            raise InvalidTransitionError
        updated = await self._repository.update_status(
            payment_id, payment.status, target
        )
        if not updated:
            raise InvalidTransitionError
