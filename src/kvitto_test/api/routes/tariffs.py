from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from kvitto_test.application.tariffs import list_tariffs
from kvitto_test.core.database import get_session
from kvitto_test.repositories.tariff import SqlAlchemyTariffRepository
from kvitto_test.schemas.tariff import TariffResponse

router = APIRouter()


@router.get("/tariffs", status_code=200, response_model=list[TariffResponse])
async def get_tariffs(
    session: Annotated[AsyncSession, Depends(get_session, scope="function")],
) -> list[TariffResponse]:
    tariffs = await list_tariffs(SqlAlchemyTariffRepository(session))
    return [TariffResponse.model_validate(tariff) for tariff in tariffs]
