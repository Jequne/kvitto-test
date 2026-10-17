import hashlib  # noqa: F401 - used by the disabled signature check below
import hmac  # noqa: F401 - used by the disabled signature check below
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from kvitto_test.api.routes.payments import get_payment_service
from kvitto_test.application.payments import (
    InvalidTransitionError,
    PaymentNotFoundError,
    PaymentService,
)
from kvitto_test.core.config import settings  # noqa: F401 - used below
from kvitto_test.schemas.webhook import (
    InvalidTransitionResponse,
    PaymentWebhookRequest,
    PaymentWebhookResponse,
)

router = APIRouter()


@router.post(
    "/webhooks/bank",
    status_code=200,
    response_model=PaymentWebhookResponse,
    responses={
        404: {"description": "Payment not found"},
        409: {
            "model": InvalidTransitionResponse,
            "description": "Invalid payment status transition",
        },
        401: {"description": "Invalid webhook signature"},
        503: {"description": "Webhook secret is not configured"},
    },
)
async def handle_bank_webhook(
    request: PaymentWebhookRequest,
    raw_request: Request,
    service: Annotated[PaymentService, Depends(get_payment_service, scope="function")],
    signature: Annotated[str | None, Header(alias="X-Signature")] = None,
) -> PaymentWebhookResponse | JSONResponse:

    # Можно вынести в отдельную функцию -----------------------------------------
    # if not settings.webhook_secret:
    #     raise HTTPException(status_code=503, detail="Webhook secret is not configured")

    # expected = hmac.new(
    #     settings.webhook_secret.encode("utf-8"),
    #     await raw_request.body(),
    #     hashlib.sha256,
    # ).hexdigest()
    # if signature is None or not hmac.compare_digest(signature, expected):
    #     raise HTTPException(status_code=401, detail="Invalid webhook signature")
    # ---------------------------------------------------------------------------

    try:
        await service.change_status(request.payment_id, request.status)
    except PaymentNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Payment not found") from exc
    except InvalidTransitionError:
        return JSONResponse(status_code=409, content={"error": "invalid_transition"})

    return PaymentWebhookResponse(result="ok")
