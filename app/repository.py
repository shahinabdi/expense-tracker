import json
from dataclasses import asdict

from .config import get_data_file
from .models import Expense


def load_expenses() -> list[Expense]:
    with open(get_data_file()) as file:
        return [Expense(**item) for item in json.load(file)]


def save_expenses(expenses: list[Expense]) -> None:
    with open(get_data_file(), "w") as file:
        json.dump([asdict(expense) for expense in expenses], file, indent=2)


def next_expense_id(expenses: list[Expense]) -> int:
    return max((expense.id for expense in expenses), default=0) + 1
