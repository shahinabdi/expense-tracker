import json
import re

import pytest


def descriptions_in_table(html):
    """Descriptions shown in the expenses table, in display order."""
    return re.findall(r"<tr>\s*<td>[\d-]+</td>\s*<td>(.*?)</td>", html)


def make_expense(id, amount, category="Other", date="2026-01-01"):
    return {"id": id, "description": f"Item {id}", "amount": amount, "category": category, "date": date}


# ---------- calculations ----------

def test_stats_total_count_and_average(client):
    stats = client.get("/api/stats").json()

    assert stats["total"] == 1210.0
    assert stats["count"] == 5
    assert stats["average"] == 242.0


def test_stats_biggest_expense(client):
    stats = client.get("/api/stats").json()

    assert stats["biggest"]["description"] == "Rent"
    assert stats["biggest"]["amount"] == 1000.0


def test_stats_totals_by_category(client):
    stats = client.get("/api/stats").json()

    assert stats["by_category"] == {
        "Housing": 1000.0,
        "Food": 160.0,
        "Transport": 20.0,
        "Entertainment": 30.0,
    }


def test_stats_with_no_expenses(client, set_expenses):
    set_expenses([])

    stats = client.get("/api/stats").json()

    assert stats["total"] == 0
    assert stats["count"] == 0
    assert stats["average"] == 0
    assert stats["biggest"] is None
    assert stats["by_category"] == {}


@pytest.mark.parametrize(
    "amount, expected_status, expected_percent",
    [
        (1000, "ok", 33.3),
        (2400, "warning", 80.0),
        (3000.01, "over", 100.0),
    ],
)
def test_budget_status(client, set_expenses, amount, expected_status, expected_percent):
    set_expenses([make_expense(1, amount)])

    stats = client.get("/api/stats").json()

    assert stats["budget_status"] == expected_status
    assert stats["budget_percent"] == expected_percent


# ---------- filtering ----------

def test_filter_by_category(client):
    response = client.get("/api/expenses", params={"category": "Food"})

    assert [e["description"] for e in response.json()] == ["Groceries", "Dinner out"]


def test_filter_by_month(client):
    response = client.get("/api/expenses", params={"month": "2026-02"})

    assert [e["id"] for e in response.json()] == [4, 5]


def test_search_is_case_insensitive(client):
    response = client.get("/api/expenses", params={"search": "GROCER"})

    assert [e["id"] for e in response.json()] == [2]


def test_min_amount_filter_ignores_invalid_values(client):
    big = client.get("/api/expenses", params={"min_amount": "50"}).json()
    invalid = client.get("/api/expenses", params={"min_amount": "abc"}).json()

    assert [e["id"] for e in big] == [1, 2, 4]
    assert len(invalid) == 5


def test_filters_can_be_combined(client):
    response = client.get("/api/expenses", params={"category": "Food", "month": "2026-01"})

    assert [e["id"] for e in response.json()] == [2]


# ---------- pages ----------

def test_dashboard_shows_statistics(client):
    response = client.get("/")

    assert response.status_code == 200
    html = response.text
    assert 'id="stat-total">1210.00<' in html
    assert 'id="stat-count">5<' in html
    assert 'id="stat-average">242.00<' in html
    assert "40.3% used" in html
    assert "You are within budget." in html


def test_expenses_page_sorting_and_totals(client):
    newest_first = client.get("/expenses").text
    highest_amount = client.get("/expenses", params={"sort": "amount_desc"}).text
    food_only = client.get("/expenses", params={"category": "Food"}).text

    assert descriptions_in_table(newest_first) == ["Cinema", "Dinner out", "Bus ticket", "Groceries", "Rent"]
    assert descriptions_in_table(highest_amount)[:2] == ["Rent", "Groceries"]
    assert 'id="result-count">2<' in food_only
    assert 'id="result-total">160.00<' in food_only


def test_static_stylesheet_is_served(client):
    assert client.get("/static/style.css").status_code == 200


# ---------- adding expenses ----------

def test_add_expense_saves_and_redirects(client, expenses_file):
    response = client.post(
        "/expenses",
        data={"description": "  Coffee  ", "amount": "3.456", "category": "Food", "date": "2026-03-01"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/expenses"
    saved = json.loads(expenses_file.read_text())
    assert saved[-1] == {
        "id": 6,
        "description": "Coffee",
        "amount": 3.46,
        "category": "Food",
        "date": "2026-03-01",
    }


@pytest.mark.parametrize(
    "form, message",
    [
        ({"description": "", "amount": "5", "category": "Food"}, "Description is required"),
        ({"description": "x" * 101, "amount": "5", "category": "Food"}, "Description is too long"),
        ({"description": "Tea", "amount": "abc", "category": "Food"}, "Amount must be a number"),
        ({"description": "Tea", "amount": "nan", "category": "Food"}, "Amount must be a number"),
        ({"description": "Tea", "amount": "0", "category": "Food"}, "Amount must be greater than 0"),
        ({"description": "Tea", "amount": "5", "category": "Pets"}, "Unknown category"),
        ({"description": "Tea", "amount": "5", "category": "Food", "date": "01/02/2026"}, "Date must be YYYY-MM-DD"),
    ],
)
def test_add_expense_validation_errors(client, expenses_file, form, message):
    before = expenses_file.read_text()

    response = client.post("/expenses", data=form)

    assert response.status_code == 400
    assert message in response.text
    assert expenses_file.read_text() == before
