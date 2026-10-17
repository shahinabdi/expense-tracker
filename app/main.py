import json
import math
import os
from datetime import datetime

from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Expense Tracker")

BASE = os.path.dirname(__file__)
app.mount("/static", StaticFiles(directory=os.path.join(BASE, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE, "templates"))

CATEGORIES = ["Food", "Transport", "Housing", "Entertainment", "Health", "Other"]


def get_file():
    # tests set this env var so they don't touch the real data
    return os.environ.get("EXPENSES_FILE", os.path.join(BASE, "data", "expenses.json"))


def load():
    f = open(get_file())
    data = json.load(f)
    f.close()
    return data


def save(data):
    f = open(get_file(), "w")
    json.dump(data, f, indent=2)
    f.close()


@app.get("/")
def home(request: Request):
    data = load()

    # total
    total = 0
    for d in data:
        total = total + d["amount"]
    total = round(total, 2)

    count = len(data)
    if count > 0:
        average = round(total / count, 2)
    else:
        average = 0

    biggest = None
    for d in data:
        if biggest is None or d["amount"] > biggest["amount"]:
            biggest = d

    # categories
    cats = {}
    for d in data:
        if d["category"] in cats:
            cats[d["category"]] = cats[d["category"]] + d["amount"]
        else:
            cats[d["category"]] = d["amount"]
    cat_list = []
    for c in cats:
        if total > 0:
            p = round(cats[c] / total * 100, 1)
        else:
            p = 0
        cat_list.append({"name": c, "total": round(cats[c], 2), "percent": p})
    cat_list.sort(key=lambda x: x["total"], reverse=True)

    # months
    m = {}
    for d in data:
        k = d["date"][:7]
        if k in m:
            m[k] = m[k] + d["amount"]
        else:
            m[k] = d["amount"]
    biggest_month = 0
    for k in m:
        if m[k] > biggest_month:
            biggest_month = m[k]
    month_list = []
    for k in sorted(m.keys()):
        h = int(m[k] / biggest_month * 120)
        month_list.append({"month": k, "total": round(m[k], 2), "height": h})

    # budget
    budget = 3000
    budget_percent = round(total / budget * 100, 1)
    if total > budget:
        budget_status = "over"
    elif total >= budget * 0.8:
        budget_status = "warning"
    else:
        budget_status = "ok"

    # last 5
    recent = sorted(data, key=lambda x: (x["date"], x["id"]), reverse=True)[:5]

    return templates.TemplateResponse(request, "dashboard.html", {
        "total": total,
        "count": count,
        "average": average,
        "biggest": biggest,
        "categories": cat_list,
        "months": month_list,
        "budget": budget,
        "budget_percent": budget_percent,
        "budget_status": budget_status,
        "recent": recent,
    })


@app.get("/expenses")
def expenses_page(request: Request, category: str = "", month: str = "", search: str = "",
                  min_amount: str = "", sort: str = "date_desc"):
    data = load()

    result = []
    for d in data:
        if category != "" and d["category"] != category:
            continue
        if month != "" and not d["date"].startswith(month):
            continue
        if search != "" and search.lower() not in d["description"].lower():
            continue
        if min_amount != "":
            try:
                if d["amount"] < float(min_amount):
                    continue
            except ValueError:
                pass
        result.append(d)

    if sort == "date_asc":
        result.sort(key=lambda x: (x["date"], x["id"]))
    elif sort == "amount_desc":
        result.sort(key=lambda x: x["amount"], reverse=True)
    elif sort == "amount_asc":
        result.sort(key=lambda x: x["amount"])
    else:
        sort = "date_desc"
        result.sort(key=lambda x: (x["date"], x["id"]), reverse=True)

    t = 0
    for r in result:
        t = t + r["amount"]

    return templates.TemplateResponse(request, "expenses.html", {
        "expenses": result,
        "all_categories": CATEGORIES,
        "selected_category": category,
        "selected_month": month,
        "search": search,
        "min_amount": min_amount,
        "sort": sort,
        "filtered_total": round(t, 2),
        "filtered_count": len(result),
        "error": None,
        "form": {"description": "", "amount": "", "category": "Food", "date": ""},
    })


@app.post("/expenses")
def add_expense(request: Request, description: str = Form(""), amount: str = Form(""),
                category: str = Form("Other"), date: str = Form("")):
    description = description.strip()
    error = None

    if description == "":
        error = "Description is required"
    elif len(description) > 100:
        error = "Description is too long (max 100 characters)"

    value = 0
    if error is None:
        try:
            value = float(amount)
            if not math.isfinite(value):
                error = "Amount must be a number"
            elif value <= 0:
                error = "Amount must be greater than 0"
        except ValueError:
            error = "Amount must be a number"

    if error is None:
        if category not in CATEGORIES:
            error = "Unknown category"

    if error is None:
        if date == "":
            date = datetime.now().strftime("%Y-%m-%d")
        else:
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                error = "Date must be YYYY-MM-DD"

    data = load()

    if error is not None:
        # show the page again with the error
        result = sorted(data, key=lambda x: (x["date"], x["id"]), reverse=True)
        t = 0
        for r in result:
            t = t + r["amount"]
        return templates.TemplateResponse(request, "expenses.html", {
            "expenses": result,
            "all_categories": CATEGORIES,
            "selected_category": "",
            "selected_month": "",
            "search": "",
            "min_amount": "",
            "sort": "date_desc",
            "filtered_total": round(t, 2),
            "filtered_count": len(result),
            "error": error,
            "form": {"description": description, "amount": amount, "category": category, "date": date},
        }, status_code=400)

    new_id = 1
    for d in data:
        if d["id"] >= new_id:
            new_id = d["id"] + 1
    data.append({"id": new_id, "description": description, "amount": round(value, 2),
                 "category": category, "date": date})
    save(data)
    return RedirectResponse("/expenses", status_code=303)


@app.get("/api/expenses")
def api_expenses(category: str = "", month: str = "", search: str = "", min_amount: str = ""):
    data = load()
    result = []
    for d in data:
        if category != "" and d["category"] != category:
            continue
        if month != "" and not d["date"].startswith(month):
            continue
        if search != "" and search.lower() not in d["description"].lower():
            continue
        if min_amount != "":
            try:
                if d["amount"] < float(min_amount):
                    continue
            except ValueError:
                pass
        result.append(d)
    return result


@app.get("/api/stats")
def api_stats():
    data = load()
    total = 0
    for d in data:
        total = total + d["amount"]
    total = round(total, 2)
    count = len(data)
    if count > 0:
        average = round(total / count, 2)
    else:
        average = 0
    biggest = None
    for d in data:
        if biggest is None or d["amount"] > biggest["amount"]:
            biggest = d
    cats = {}
    for d in data:
        if d["category"] in cats:
            cats[d["category"]] = cats[d["category"]] + d["amount"]
        else:
            cats[d["category"]] = d["amount"]
    for c in cats:
        cats[c] = round(cats[c], 2)
    budget = 3000
    if total > budget:
        status = "over"
    elif total >= budget * 0.8:
        status = "warning"
    else:
        status = "ok"
    return {
        "total": total,
        "count": count,
        "average": average,
        "biggest": biggest,
        "by_category": cats,
        "budget_percent": round(total / budget * 100, 1),
        "budget_status": status,
    }
