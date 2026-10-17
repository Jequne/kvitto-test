from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from kvitto_test.application.payments import (
    CreatePaymentCommand,
    InvalidAmountError,
    InvalidPromoCodeError,
    PaymentNotFoundError,
    PaymentService,
)
from kvitto_test.core.database import get_session
from kvitto_test.domain.payment import PaymentStatus
from kvitto_test.repositories.payment import SqlAlchemyPaymentRepository
from kvitto_test.schemas.payment import PaymentCreateRequest, PaymentResponse


router = APIRouter()


def get_payment_service(
    session: Annotated[AsyncSession, Depends(get_session, scope="function")],
) -> PaymentService:
    return PaymentService(SqlAlchemyPaymentRepository(session))


@router.post(
    "/payments",
    status_code=201,
    response_model=PaymentResponse,
    responses={
        200: {
            "model": PaymentResponse,
            "description": "Existing payment returned for a repeated idempotency key",
        },
    },
)
async def create_payment(
    request: PaymentCreateRequest,
    response: Response,
    service: Annotated[PaymentService, Depends(get_payment_service, scope="function")],
    idempotency_key: Annotated[
        str | None, Header(alias="Idempotency-Key", min_length=1, max_length=255)
    ] = None,
) -> PaymentResponse:
    try:
        result = await service.create(
            CreatePaymentCommand(
                tariff_id=request.tariff_id,
                email=request.email,
                method=request.method,
                installment_months=request.installment_months,
                promo_code=request.promo_code,
                idempotency_key=idempotency_key,
            )
        )
    except PaymentNotFoundError as exc:
        raise HTTPException(status_code=422, detail="Unknown tariff") from exc
    except InvalidPromoCodeError as exc:
        raise HTTPException(status_code=422, detail="Unknown promo code") from exc
    except InvalidAmountError as exc:
        raise HTTPException(status_code=422, detail="Invalid payment amount") from exc
    response.status_code = 201 if result.created else 200
    return PaymentResponse.model_validate(result.payment, from_attributes=True)


@router.get("/payments", status_code=200, response_model=list[PaymentResponse])
async def list_payments(
    service: Annotated[PaymentService, Depends(get_payment_service, scope="function")],
    email: EmailStr | None = None,
    status: PaymentStatus | None = None,
) -> list[PaymentResponse]:
    payments = await service.list_payments(email=email, status=status)
    return [
        PaymentResponse.model_validate(payment, from_attributes=True)
        for payment in payments
    ]


@router.get(
    "/payments/{id}",
    status_code=200,
    response_model=PaymentResponse,
    responses={
        404: {"description": "Payment not found"},
    },
)
async def get_payment(
    id: UUID,
    service: Annotated[PaymentService, Depends(get_payment_service, scope="function")],
) -> PaymentResponse:
    try:
        payment = await service.get(id)
    except PaymentNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Payment not found") from exc
    return PaymentResponse.model_validate(payment, from_attributes=True)
