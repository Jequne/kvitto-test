from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kvitto_test.domain.tariff import Tariff as DomainTariff
from kvitto_test.models.tariff import Tariff


class SqlAlchemyTariffRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[DomainTariff]:
        result = await self._session.scalars(select(Tariff).order_by(Tariff.code))
        return [
            DomainTariff(id=row.id, code=row.code, title=row.title, price=row.price)
            for row in result
        ]
