from .config import (
    BUDGET,
    BUDGET_WARNING_RATIO,
    CHART_MAX_HEIGHT_PX,
    DEFAULT_SORT,
    RECENT_EXPENSES_LIMIT,
)
from .filters import sort_expenses
from .models import CategorySummary, Expense, MonthSummary


def total_amount(expenses: list[Expense]) -> float:
    return round(sum(e.amount for e in expenses), 2)


def average_amount(expenses: list[Expense]) -> float:
    if not expenses:
        return 0
    return round(total_amount(expenses) / len(expenses), 2)


def biggest_expense(expenses: list[Expense]) -> Expense | None:
    return max(expenses, key=lambda e: e.amount, default=None)


def _sum_by(expenses: list[Expense], key) -> dict[str, float]:
    totals: dict[str, float] = {}
    for expense in expenses:
        totals[key(expense)] = totals.get(key(expense), 0) + expense.amount
    return totals


def totals_by_category(expenses: list[Expense]) -> dict[str, float]:
    return {
        name: round(total, 2)
        for name, total in _sum_by(expenses, lambda e: e.category).items()
    }


def category_breakdown(expenses: list[Expense]) -> list[CategorySummary]:
    grand_total = total_amount(expenses)
    summaries = [
        CategorySummary(
            name=name,
            total=round(amount, 2),
            percent=round(amount / grand_total * 100, 1) if grand_total > 0 else 0,
        )
        for name, amount in _sum_by(expenses, lambda e: e.category).items()
    ]
    return sorted(summaries, key=lambda s: s.total, reverse=True)


def monthly_breakdown(expenses: list[Expense]) -> list[MonthSummary]:
    by_month = _sum_by(expenses, lambda e: e.date[:7])
    biggest_month = max(by_month.values(), default=0)
    return [
        MonthSummary(
            month=month,
            total=round(by_month[month], 2),
            height=int(by_month[month] / biggest_month * CHART_MAX_HEIGHT_PX)
            if biggest_month
            else 0,
        )
        for month in sorted(by_month)
    ]


def budget_percent(total: float) -> float:
    return round(total / BUDGET * 100, 1)


def budget_status(total: float) -> str:
    if total > BUDGET:
        return "over"
    elif total >= BUDGET * BUDGET_WARNING_RATIO:
        return "warning"
    else:
        return "ok"


def recent_expenses(expenses: list[Expense]) -> list[Expense]:
    return sort_expenses(expenses, DEFAULT_SORT)[:RECENT_EXPENSES_LIMIT]
