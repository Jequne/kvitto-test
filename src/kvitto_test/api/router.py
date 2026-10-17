from fastapi import APIRouter

from kvitto_test.api.routes.tariffs import router as tariffs_router


api_router = APIRouter()
api_router.include_router(tariffs_router)
