# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2025 Matvey Vyalkov
# No warranty

import json
from datetime import date, timedelta
from pathlib import Path

from bs4 import BeautifulSoup

from egov66_timetable.exceptions import (
    CSRFTokenNotFound,
    SessionExpired,
)
from egov66_timetable.types import Settings, Week


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


def get_current_week() -> Week:
    """
    :returns: текущая неделя
    """

    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)

    return Week(monday, sunday)


def read_settings() -> Settings:
    """
    Читает настройки из файла settings.json.

    :returns: настройки
    :raises FileNotFoundError: если файл settings.json не найден
    """

    file = Path("settings.json")
    if not file.is_file():
        raise FileNotFoundError("Файл settings.json не найден")

    return json.loads(file.read_text())


def write_settings(settings: Settings) -> None:
    """
    Записывает настройки в файл settings.json.

    :param settings: настройки
    """

    with open("settings.json", "w") as file:
        json.dump(settings, file, indent=2, ensure_ascii=False)
