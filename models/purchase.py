from dataclasses import dataclass, field
from typing import List


@dataclass
class PurchaseItem:
    id: int
    purchase_id: int
    product_id: int
    product_name: str
    unit_id: int
    unit_name: str
    quantity: float
    price_per_unit: float
    quantity_base: float
    final_cost_per_unit: float | None = None

    @property
    def total(self) -> float:
        return self.quantity * self.price_per_unit

    @property
    def final_total(self) -> float:
        """Total using final cost (with additional costs distributed)."""
        if self.final_cost_per_unit is not None:
            return self.quantity * self.final_cost_per_unit
        return self.total


@dataclass
class AdditionalCost:
    id: int
    purchase_id: int
    cost_name: str
    amount: float


@dataclass
class Purchase:
    id: int
    date: str
    notes: str
    created_at: str
    items: List[PurchaseItem] = field(default_factory=list)
    additional_costs: List[AdditionalCost] = field(default_factory=list)

    @property
    def total(self) -> float:
        return sum(i.total for i in self.items)

    @property
    def additional_costs_total(self) -> float:
        return sum(c.amount for c in self.additional_costs)

    @property
    def final_total(self) -> float:
        """Total including additional costs."""
        return sum(i.final_total for i in self.items)
