from fastapi import APIRouter

from kvitto_test.api.routes.payments import router as payments_router
from kvitto_test.api.routes.tariffs import router as tariffs_router
from kvitto_test.api.routes.webhooks import router as webhooks_router

api_router = APIRouter()
api_router.include_router(tariffs_router)
api_router.include_router(payments_router)
api_router.include_router(webhooks_router)
