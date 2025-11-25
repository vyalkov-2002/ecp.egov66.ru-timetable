# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2025 Matvey Vyalkov
# No warranty

from datetime import date, timedelta

from bs4 import BeautifulSoup

from egov66_timetable.exceptions import (
    CSRFTokenNotFound,
    SessionExpired,
)
from egov66_timetable.types import Week


def get_csrf_token(soup: BeautifulSoup) -> str:
    """
    :param soup: разобранный HTML-код страницы
    :returns: CSRF-токен из кода страницы
    :raises SessionExpired: если сеанс завершен
    :raises CSRFTokenNotFound: если токен не найден
    """

    if soup.head is not None:
        meta_csrf_token = soup.head.find("meta", attrs={"name": "csrf-token"})
        if meta_csrf_token is not None:
            csrf_token = meta_csrf_token.attrs.get("content")
            if isinstance(csrf_token, str):
                return csrf_token
        if soup.head.find("meta", attrs={"http-equiv": "refresh"}):
            raise SessionExpired

    raise CSRFTokenNotFound


def get_week_dates() -> Week:
    """
    :returns: текущая неделя
    """

    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)

    return Week(monday, sunday)
