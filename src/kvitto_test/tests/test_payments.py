import asyncio
from dataclasses import replace
from datetime import datetime, timezone
from uuid import UUID

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient, Response

from kvitto_test.api.routes.payments import get_payment_service, router
from kvitto_test.application.payments import PaymentService
from kvitto_test.domain.payment import Payment, PromoCode
from kvitto_test.domain.tariff import Tariff


TARIFF_ID = UUID("00000000-0000-0000-0000-000000000001")
TARIFF_PRICE = 1_990_000
PROMO_CODE_ID = UUID("00000000-0000-0000-0000-000000000002")


class FakePaymentRepository:
    def __init__(self) -> None:
        self.tariff = Tariff(
            id=TARIFF_ID,
            code="test",
            title="Test tariff",
            price=TARIFF_PRICE,
        )
        self.payments_by_key: dict[str, Payment] = {}
        self.add_count = 0

    async def get_tariff(self, tariff_id: UUID) -> Tariff | None:
        return self.tariff if tariff_id == self.tariff.id else None

    async def get_promo_code(self, code: str) -> PromoCode | None:
        if code == "KVITTO10":
            return PromoCode(id=PROMO_CODE_ID, discount_percent=10)
        return None

    async def get_by_key(self, key: str) -> Payment | None:
        return self.payments_by_key.get(key)

    async def add(self, payment: Payment, key: str | None) -> Payment:
        saved = replace(payment, created_at=datetime.now(timezone.utc))
        self.add_count += 1
        if key is not None:
            self.payments_by_key[key] = saved
        return saved


@pytest.fixture
def payment_repository() -> FakePaymentRepository:
    return FakePaymentRepository()


@pytest.fixture
def payment_client(payment_repository: FakePaymentRepository) -> AsyncClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_payment_service] = lambda: PaymentService(
        payment_repository
    )
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.parametrize("months", [3, 6, 12])
def test_installment_schedule_sums_to_payment_amount(
    payment_client: AsyncClient, months: int
) -> None:
    async def create_payment() -> dict:
        async with payment_client as client:
            response = await client.post(
                "/payments",
                json={
                    "tariff_id": str(TARIFF_ID),
                    "email": "buyer@example.com",
                    "method": "installment",
                    "installment_months": months,
                },
            )
        assert response.status_code == 201
        return response.json()

    payment = asyncio.run(create_payment())
    schedule = payment["schedule"]

    assert payment["amount"] == TARIFF_PRICE
    assert payment["installment_months"] == months
    assert len(schedule) == months
    assert all(isinstance(amount, int) and amount > 0 for amount in schedule)
    assert sum(schedule) == payment["amount"]


@pytest.mark.parametrize(
    ("tariff_price", "promo_code", "expected_discount", "expected_amount"),
    [
        (990_000, None, 0, 990_000),
        (990_000, "KVITTO10", 99_000, 891_000),
        (990_000, "kvitto10", 99_000, 891_000),
        (1_990_000, None, 0, 1_990_000),
        (1_990_000, "KVITTO10", 199_000, 1_791_000),
        (1_990_000, "kvitto10", 199_000, 1_791_000),
        (2_990_000, None, 0, 2_990_000),
        (2_990_000, "KVITTO10", 299_000, 2_691_000),
        (2_990_000, "kvitto10", 299_000, 2_691_000),
        (999_995, "KVITTO10", 100_000, 899_995),
    ],
)
def test_payment_amount_with_and_without_promo_code(
    payment_client: AsyncClient,
    payment_repository: FakePaymentRepository,
    tariff_price: int,
    promo_code: str | None,
    expected_discount: int,
    expected_amount: int,
) -> None:
    payment_repository.tariff = replace(payment_repository.tariff, price=tariff_price)
    request = {
        "tariff_id": str(TARIFF_ID),
        "email": "buyer@example.com",
        "method": "card",
    }
    if promo_code is not None:
        request["promo_code"] = promo_code

    async def create_payment() -> Response:
        async with payment_client as client:
            return await client.post("/payments", json=request)

    response = asyncio.run(create_payment())

    assert response.status_code == 201
    payment = response.json()
    assert payment["amount"] == expected_amount
    assert payment["discount"] == expected_discount
    assert payment["amount"] + payment["discount"] == tariff_price
    if promo_code is not None:
        assert payment["discount"] == (tariff_price * 10 + 50) // 100


def test_repeated_idempotency_key_does_not_create_second_payment(
    payment_client: AsyncClient, payment_repository: FakePaymentRepository
) -> None:
    request = {
        "tariff_id": str(TARIFF_ID),
        "email": "buyer@example.com",
        "method": "card",
    }
    headers = {"Idempotency-Key": "payment-request-1"}

    async def create_twice() -> tuple[Response, Response]:
        async with payment_client as client:
            first = await client.post("/payments", json=request, headers=headers)
            second = await client.post("/payments", json=request, headers=headers)
        return first, second

    first, second = asyncio.run(create_twice())

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json() == first.json()
    assert payment_repository.add_count == 1
