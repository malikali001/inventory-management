from dataclasses import dataclass, field
from typing import List


@dataclass
class SaleItem:
    id: int
    sale_id: int
    product_id: int
    product_name: str
    unit_id: int
    unit_name: str
    quantity: float
    price_per_unit: float
    quantity_base: float

    @property
    def total(self) -> float:
        return self.quantity * self.price_per_unit


@dataclass
class Sale:
    id: int
    date: str
    notes: str
    created_at: str
    items: List[SaleItem] = field(default_factory=list)

    @property
    def total(self) -> float:
        return sum(i.total for i in self.items)
