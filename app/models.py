from dataclasses import dataclass


@dataclass
class Expense:
    id: int
    description: str
    amount: float
    category: str
    date: str  # YYYY-MM-DD


@dataclass
class CategorySummary:
    name: str
    total: float
    percent: float


@dataclass
class MonthSummary:
    month: str
    total: str
    height: str
