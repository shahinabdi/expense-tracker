from dataclasses import asdict

from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import stats
from .config import BASE_DIR, BUDGET, CATEGORIES, DEFAULT_CATEGORY, DEFAULT_SORT
from .filters import ExpenseFilter, filter_expenses, normalize_sort, sort_expenses
from .models import Expense
from .repository import load_expenses, next_expense_id, save_expenses
from .validation import ValidationError, validate_new_expense

app = FastAPI(title="Expense Tracker")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def expenses_page_context(
    expenses: list[Expense],
    criteria: ExpenseFilter,
    sort: str,
    error: str | None = None,
    form: dict[str, str] | None = None,
) -> dict:
    return {
        "expenses": expenses,
        "all_categories": CATEGORIES,
        "selected_category": criteria.category,
        "selected_month": criteria.month,
        "search": criteria.search,
        "min_amount": criteria.min_amount,
        "sort": sort,
        "filtered_total": stats.total_amount(expenses),
        "filtered_count": len(expenses),
        "error": error,
        "form": form
        or {"description": "", "amount": "", "category": "Food", "date": ""},
    }


@app.get("/")
def home(request: Request):
    expenses = load_expenses()
    total = stats.total_amount(expenses)
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "total": total,
            "count": len(expenses),
            "average": stats.average_amount(expenses),
            "biggest": stats.biggest_expense(expenses),
            "categories": stats.category_breakdown(expenses),
            "months": stats.monthly_breakdown(expenses),
            "budget": BUDGET,
            "budget_percent": stats.budget_percent(total),
            "budget_status": stats.budget_status(total),
            "recent": stats.recent_expenses(expenses),
        },
    )


@app.get("/expenses")
def expenses_page(
    request: Request,
    category: str = "",
    month: str = "",
    search: str = "",
    min_amount: str = "",
    sort: str = DEFAULT_SORT,
):
    criteria = ExpenseFilter(category, month, search, min_amount)
    sort = normalize_sort(sort)
    expenses = sort_expenses(filter_expenses(load_expenses(), criteria), sort)
    return templates.TemplateResponse(
        request, "expenses.html", expenses_page_context(expenses, criteria, sort)
    )


@app.post("/expenses")
def add_expense(
    request: Request,
    description: str = Form(""),
    amount: str = Form(""),
    category: str = Form(DEFAULT_CATEGORY),
    date: str = Form(""),
):
    expenses = load_expenses()
    try:
        valid = validate_new_expense(description, amount, category, date)
    except ValidationError as error:
        form = {
            "description": description.strip(),
            "amount": amount,
            "category": category,
            "date": date,
        }
        context = expenses_page_context(
            sort_expenses(expenses, DEFAULT_SORT),
            ExpenseFilter(),
            DEFAULT_SORT,
            str(error),
            form,
        )
        return templates.TemplateResponse(
            request, "expenses.html", context, status_code=400
        )
    expenses.append(
        Expense(
            next_expense_id(expenses),
            valid.description,
            valid.amount,
            valid.category,
            valid.date,
        )
    )
    save_expenses(expenses)
    return RedirectResponse("/expenses", status_code=303)


@app.get("/api/expenses")
def api_expenses(
    category: str = "", month: str = "", search: str = "", min_amount: str = ""
):
    criteria = ExpenseFilter(category, month, search, min_amount)
    return [asdict(e) for e in filter_expenses(load_expenses(), criteria)]


@app.get("/api/stats")
def api_stats():
    expenses = load_expenses()
    total = stats.total_amount(expenses)
    biggest = stats.biggest_expense(expenses)
    return {
        "total": total,
        "count": len(expenses),
        "average": stats.average_amount(expenses),
        "biggest": asdict(biggest) if biggest else None,
        "by_category": stats.totals_by_category(expenses),
        "budget_percent": stats.budget_percent(total),
        "budget_status": stats.budget_status(total),
    }
