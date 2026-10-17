import asyncio
import hashlib
import hmac
import json
from dataclasses import replace
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient, Response

from kvitto_test.api.routes.payments import get_payment_service, router
from kvitto_test.api.routes.webhooks import router as webhook_router
from kvitto_test.application.payments import PaymentService
from kvitto_test.core.config import settings
from kvitto_test.domain.payment import Payment, PaymentStatus, PromoCode
from kvitto_test.domain.tariff import Tariff


TARIFF_ID = UUID("00000000-0000-0000-0000-000000000001")
TARIFF_PRICE = 1_990_000
PROMO_CODE_ID = UUID("00000000-0000-0000-0000-000000000002")
WEBHOOK_SECRET = "test-webhook-secret"


class FakePaymentRepository:
    def __init__(self) -> None:
        self.tariff = Tariff(
            id=TARIFF_ID,
            code="test",
            title="Test tariff",
            price=TARIFF_PRICE,
        )
        self.payments_by_key: dict[str, Payment] = {}
        self.payments_by_id: dict[UUID, Payment] = {}
        self.add_count = 0

    async def get_tariff(self, tariff_id: UUID) -> Tariff | None:
        return self.tariff if tariff_id == self.tariff.id else None

    async def get_promo_code(self, code: str) -> PromoCode | None:
        if code == "KVITTO10":
            return PromoCode(id=PROMO_CODE_ID, discount_percent=10)
        return None

    async def get_by_key(self, key: str) -> Payment | None:
        return self.payments_by_key.get(key)

    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        return self.payments_by_id.get(payment_id)

    async def add(self, payment: Payment, key: str | None) -> Payment:
        saved = replace(payment, created_at=datetime.now(timezone.utc))
        self.add_count += 1
        self.payments_by_id[saved.id] = saved
        if key is not None:
            self.payments_by_key[key] = saved
        return saved

    async def update_status(
        self, payment_id: UUID, current: PaymentStatus, target: PaymentStatus
    ) -> bool:
        payment = self.payments_by_id.get(payment_id)
        if payment is None or payment.status != current:
            return False
        updated = replace(payment, status=target)
        self.payments_by_id[payment_id] = updated
        for key, saved in self.payments_by_key.items():
            if saved.id == payment_id:
                self.payments_by_key[key] = updated
        return True


@pytest.fixture
def payment_repository() -> FakePaymentRepository:
    return FakePaymentRepository()


@pytest.fixture
def payment_client(payment_repository: FakePaymentRepository) -> AsyncClient:
    app = FastAPI()
    app.include_router(router)
    app.include_router(webhook_router)
    app.dependency_overrides[get_payment_service] = lambda: PaymentService(
        payment_repository
    )
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture
def webhook_client(
    payment_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> AsyncClient:
    monkeypatch.setattr(settings, "webhook_secret", WEBHOOK_SECRET)
    return payment_client


async def send_webhook(client: AsyncClient, payment_id: UUID, status: str) -> Response:
    body = json.dumps({"payment_id": str(payment_id), "status": status}).encode()
    signature = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return await client.post(
        "/webhooks/bank",
        content=body,
        headers={"Content-Type": "application/json", "X-Signature": signature},
    )


async def create_test_payment(client: AsyncClient) -> UUID:
    response = await client.post(
        "/payments",
        json={
            "tariff_id": str(TARIFF_ID),
            "email": "buyer@example.com",
            "method": "card",
        },
    )
    assert response.status_code == 201
    return UUID(response.json()["id"])


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


@pytest.mark.anyio
async def test_webhook_rejects_invalid_transition_without_changing_status(
    webhook_client: AsyncClient,
    payment_repository: FakePaymentRepository,
) -> None:
    async with webhook_client as client:
        payment_id = await create_test_payment(client)
        response = await send_webhook(client, payment_id, "refunded")

    assert response.status_code == 409
    assert response.json() == {"error": "invalid_transition"}
    assert payment_repository.payments_by_id[payment_id].status == PaymentStatus.PENDING


@pytest.mark.anyio
async def test_webhook_returns_404_for_unknown_payment(
    webhook_client: AsyncClient,
) -> None:
    async with webhook_client as client:
        response = await send_webhook(client, uuid4(), "succeeded")

    assert response.status_code == 404
