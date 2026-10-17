from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException

from kvitto_test.schemas.payment import PaymentCreateRequest, PaymentResponse


router = APIRouter()


@router.post(
    "/payments",
    status_code=201,
    response_model=PaymentResponse,
    responses={
        200: {
            "model": PaymentResponse,
            "description": "Existing payment returned for a repeated idempotency key",
        },
        501: {"description": "Payment creation is not implemented"},
    },
)
async def create_payment(
    request: PaymentCreateRequest,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> PaymentResponse:
    raise HTTPException(status_code=501, detail="Payment creation is not implemented")


@router.get(
    "/payments/{id}",
    status_code=200,
    response_model=PaymentResponse,
    responses={
        404: {"description": "Payment not found"},
        501: {"description": "Payment lookup is not implemented"},
    },
)
async def get_payment(id: UUID) -> PaymentResponse:
    raise HTTPException(status_code=501, detail="Payment lookup is not implemented")
