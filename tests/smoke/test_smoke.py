import os
import urllib.request

import pytest

BASE_URL = os.environ.get("BASE_URL")

pytestmark = pytest.mark.skipif(not BASE_URL, reason="BASE_URL not set")


def _status(url):
    with urllib.request.urlopen(url, timeout=10) as r:
        return r.status


def test_dashboard_up():
    assert _status(f"{BASE_URL}/") == 200


def test_expenses_page_up():
    assert _status(f"{BASE_URL}/expenses") == 200


def test_static_served():
    assert _status(f"{BASE_URL}/static/style.css") == 200
