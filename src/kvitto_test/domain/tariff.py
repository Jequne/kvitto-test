from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Tariff:
    id: UUID
    code: str
    title: str
    price: int
