import math
from dataclasses import dataclass
from datetime import datetime

from .config import CATEGORIES, DATE_FORMAT, MAX_DESCRIPTION_LENGTH


class ValidationError(Exception):
    """Raise with a user-facing message"""


@dataclass
class ValidExpense:
    description: str
    amount: float
    category: str
    date: str


def parse_amount(raw: str) -> float:
    try:
        value = float(raw)
    except ValueError:
        raise ValidationError("Amount must be a number") from None
    if not math.isfinite(value):
        raise ValidationError("Amount must be a number")
    if value <= 0:
        raise ValidationError("Amount must be greater than 0")
    return value


def parse_date(raw: str) -> str:
    if raw == "":
        return datetime.now().strftime(DATE_FORMAT)
    try:
        datetime.strptime(raw, DATE_FORMAT)
    except ValueError:
        raise ValidationError("Date must be YYYY-MM-DD") from None
    return raw


def validate_new_expense(
    description: str, amount: str, category: str, date: str
) -> ValidExpense:
    description = description.strip()
    if description == "":
        raise ValidationError("Description is required")
    if len(description) > MAX_DESCRIPTION_LENGTH:
        raise ValidationError(
            f"Description is too long (max {MAX_DESCRIPTION_LENGTH} characters)"
        )

    value = parse_amount(amount)
    if category not in CATEGORIES:
        raise ValidationError("Unknown category")

    return ValidExpense(description, round(value, 2), category, parse_date(date))
