from fastapi import APIRouter, HTTPException

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
        501: {"description": "Webhook handling is not implemented"},
    },
)
async def handle_bank_webhook(request: PaymentWebhookRequest) -> PaymentWebhookResponse:
    raise HTTPException(status_code=501, detail="Webhook handling is not implemented")
