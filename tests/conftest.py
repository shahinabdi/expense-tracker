import json

import pytest
from fastapi.testclient import TestClient

from app.main import app

SAMPLE_EXPENSES = [
    {"id": 1, "description": "Rent", "amount": 1000.0, "category": "Housing", "date": "2026-01-01"},
    {"id": 2, "description": "Groceries", "amount": 100.5, "category": "Food", "date": "2026-01-10"},
    {"id": 3, "description": "Bus ticket", "amount": 20.0, "category": "Transport", "date": "2026-01-15"},
    {"id": 4, "description": "Dinner out", "amount": 59.5, "category": "Food", "date": "2026-02-03"},
    {"id": 5, "description": "Cinema", "amount": 30.0, "category": "Entertainment", "date": "2026-02-10"},
]


@pytest.fixture
def expenses_file(tmp_path, monkeypatch):
    """A temporary JSON file with known data, wired into the app."""
    path = tmp_path / "expenses.json"
    path.write_text(json.dumps(SAMPLE_EXPENSES))
    monkeypatch.setenv("EXPENSES_FILE", str(path))
    return path


@pytest.fixture
def client(expenses_file):
    return TestClient(app)


@pytest.fixture
def set_expenses(expenses_file):
    def _set(expenses):
        expenses_file.write_text(json.dumps(expenses))

    return _set
