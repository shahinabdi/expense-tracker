from dataclasses import dataclass

from .config import DEFAULT_SORT
from .models import Expense

SORT_OPTIONS = {
    "date_desc": (lambda e: (e.date, e.id), True),
    "date_asc": (lambda e: (e.date, e.id), False),
    "amount_desc":(lambda e: e.amount, True),
    "amount_asc":(lambda e: e.amount, False),
}

@dataclass
class ExpenseFilter:
    category: str=""
    month: str=""
    search: str=""
    min_amount: str="" #raw query-string value; number -> ignored

def parse_min_amount(raw: str) -> float | None:
    try:
        return float(raw)
    except ValueError:
        return None

def matches(expense: Expense, criteria: ExpenseFilter, min_amount: float | None) -> bool:
    if criteria.category and expense.category != criteria.category:
        return False
    if criteria.month and not expense.date.startswith(criteria.month):
        return False
    if criteria.search and criteria.search.lower() not in expense.description.lower():
        return False
    if min_amount is not None and expense.amount < min_amount:
        return False
    return True

def filter_expenses(expenses: list[Expense],criteria: ExpenseFilter) -> list[Expense]:
    min_amount = parse_min_amount(criteria.min_amount) if criteria.min_amount else None
    return [e for e in expenses if matches(e, criteria, min_amount)]

def normalize_sort(sort: str)-> str:
    return sort if sort in SORT_OPTIONS else DEFAULT_SORT

def sort_expenses(expenses: list[Expense], sort:str) -> list[Expense]:
    key, reverse = SORT_OPTIONS[normalize_sort(sort)]
    return sorted(expenses, key=key, reverse=reverse)