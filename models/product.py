from dataclasses import dataclass, field
from typing import List


@dataclass
class ProductUnit:
    id: int
    product_id: int
    unit_name: str
    conversion_to_base: float
    is_default_purchase: bool
    is_default_sale: bool


@dataclass
class Product:
    id: int
    name: str
    category: str
    base_unit: str
    low_stock_threshold: float
    is_active: bool
    created_at: str
    units: List[ProductUnit] = field(default_factory=list)
    current_stock_base: float = 0.0

    def stock_in_unit(self, unit: ProductUnit) -> float:
        """Return current stock expressed in the given unit."""
        if unit.conversion_to_base == 0:
            return 0.0
        return self.current_stock_base / unit.conversion_to_base

    @property
    def default_sale_unit(self) -> ProductUnit | None:
        for u in self.units:
            if u.is_default_sale:
                return u
        return self.units[0] if self.units else None

    @property
    def default_purchase_unit(self) -> ProductUnit | None:
        for u in self.units:
            if u.is_default_purchase:
                return u
        return self.units[0] if self.units else None
