from typing import Protocol

from kvitto_test.domain.tariff import Tariff


class TariffRepository(Protocol):
    async def list_all(self) -> list[Tariff]: ...


async def list_tariffs(repository: TariffRepository) -> list[Tariff]:
    return await repository.list_all()
