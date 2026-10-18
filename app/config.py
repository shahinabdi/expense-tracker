import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
CATEGORIES = ["Food", "Transport", "Housing", "Entertainment", "Health", "Other"]
DEFAULT_CATEGORY = "Other"

BUDGET = 3000
BUDGET_WARNING_RATIO = 0.8

CHART_MAX_HEIGHT_PX = 120
RECENT_EXPENSES_LIMIT = 5
MAX_DESCRIPTION_LENGTH = 100

DEFAULT_SORT = "date_desc"
DATE_FORMAT = "%Y-%m-%d"


def get_data_file() -> Path:
    override = os.environ.get("EXPENSES_FILE")
    return Path(override) if override else BASE_DIR / "data" / "expenses.json"
