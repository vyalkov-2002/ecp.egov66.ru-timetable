# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2025 Matvey Vyalkov
# No warranty

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from bs4 import BeautifulSoup

import egov66_timetable.utils
from egov66_timetable.exceptions import SessionExpired
from egov66_timetable.utils import (
    get_csrf_token,
    get_current_week,
)


@pytest.fixture
def soup(request: pytest.FixtureRequest) -> BeautifulSoup:
    file = Path(__file__).parent / "data" / f"{request.function.__name__}.html"
    return BeautifulSoup(file.read_text(), "lxml")


def test_get_current_week(monkeypatch: pytest.MonkeyPatch):
    date_mock = MagicMock(wraps=date)
    date_mock.today.return_value = date.fromisocalendar(2000, 2, 3)

    monkeypatch.setattr(egov66_timetable.utils, "date", date_mock)

    week = get_current_week()
    assert week.monday == date.fromisocalendar(2000, 2, 1)
    assert week.sunday == date.fromisocalendar(2000, 2, 7)


def test_get_csrf_token(soup: BeautifulSoup):
    assert get_csrf_token(soup) == "secret!"


def test_get_csrf_token_expired(soup: BeautifulSoup):
    with pytest.raises(SessionExpired):
        get_csrf_token(soup)
