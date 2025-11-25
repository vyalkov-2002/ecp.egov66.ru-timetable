#!/usr/bin/env python

# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2025 Matvey Vyalkov
# No warranty

"""
Просмотр расписания колледжей и техникумов Свердловской области
"""

import locale
import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader, select_autoescape

__version__ = "0.0.0"

INSTANCE: str
SESSION_ID: str
if not TYPE_CHECKING:
    INSTANCE = os.environ["ECP_EGOV66_INSTANCE"]
    SESSION_ID = os.environ["ECP_EGOV66_SESSION_ID"]

DASHBOARD_URL = f"https://{INSTANCE}/dashboard"
ENDPOINT = f"https://{INSTANCE}/schedule/calendar/events/groups"
SESSION_COOKIE_NAME = "edinyi_lk_session"

# Выводить дни недели в русской локали
locale.setlocale(locale.LC_TIME, "ru_RU.utf8")


class SessionExpired(Exception):
    """
    Эта ошибка означает, что сеанс завершен и нужно получить новый
    cookie-файл edinyi_lk_session.
    """


class CSRFTokenNotFound(Exception):
    """
    Эта ошибка означает, что на странице не удалось найти CSRF-токен.
    """


@dataclass(frozen=True)
class Week:
    """
    Неделя.
    """

    # Понедельник, полночь.
    monday: datetime

    # Воскресенье, полночь.
    sunday: datetime

    @property
    def week_id(self) -> str:
        """
        Год и номер недели в году (пример: 1970-48).
        """

        iso_week = self.monday.isocalendar()
        return f"{iso_week.year}-{iso_week.week}"

    def __add__(self, other: object) -> "Week":
        if isinstance(other, int):
            return Week(
                monday=self.monday + timedelta(weeks=other),
                sunday=self.sunday + timedelta(weeks=other),
            )
        raise NotImplementedError

    def __sub__(self, other: object) -> "Week":
        if isinstance(other, int):
            return self + -other
        raise NotImplementedError


@dataclass(frozen=True)
class Course:
    """
    Пара в расписании.
    """

    #: Название предмета.
    name: str

    #: Аудитория.
    classroom: str

    #: Дата и время начала пары.
    start: datetime

    #: Дата и время окончания пары.
    end: datetime

    def __lt__(self, other: object) -> bool:
        if hasattr(other, "start") and isinstance(other.start, datetime):
            return self.start < other.start
        raise NotImplementedError


type Timetable = list[list[Course]]


def get_week_dates(offset: int = 0) -> Week:
    """
    :param offset: смещение относительно текущей недели (``-1`` — предыдущая
        неделя, ``+1`` — следующая)
    """

    midnight = datetime.min.time()

    today = date.today()
    monday = today + timedelta(days=-today.weekday(), weeks=offset)
    sunday = monday + timedelta(days=6)

    return Week(
        monday=datetime.combine(monday, midnight),
        sunday=datetime.combine(sunday, midnight),
    )


def get_csrf_token() -> str:
    """
    :returns: CSRF-токен из кода страницы
    :raises SessionExpired: если сеанс завершен
    :raises CSRFTokenNotFound: если токен не найден
    """

    cookies = {
        SESSION_COOKIE_NAME: SESSION_ID
    }
    page_html = httpx.get(DASHBOARD_URL, cookies=cookies).text

    soup = BeautifulSoup(page_html, "lxml")
    if soup.head is not None:
        meta_csrf_token = soup.head.find(attrs={"name": "csrf-token"})
        if meta_csrf_token is not None:
            csrf_token = meta_csrf_token.attrs.get("content")
            if isinstance(csrf_token, str):
                return csrf_token
        if soup.head.find(attrs={"http-equiv": "refresh"}):
            raise SessionExpired

    raise CSRFTokenNotFound


def fetch(group: str, *, week: Week) -> list[dict]:
    """
    Получает расписание на неделю для группы.

    :param group: номер группы
    :param week: неделя, на которую нужно получить расписание
    :returns: данные, полученные из API
    """

    params = {
        "info[startStr]": week.monday.isoformat(),
        "info[endStr]": week.sunday.isoformat(),
        "valueSearch": group
    }
    headers = {
        "X-CSRF-TOKEN": get_csrf_token()
    }
    cookies = {
        SESSION_COOKIE_NAME: SESSION_ID
    }

    return httpx.post(ENDPOINT,
                      data=params,
                      headers=headers,
                      cookies=cookies).json()


def parse_title_html(title_html: str) -> tuple[str, str]:
    """
    :returns: название предмета и номер аудитории
    """

    name: str = "Н/Д"
    classroom: str = ""

    soup = BeautifulSoup(title_html, "lxml")
    if soup.div is not None:
        name = "".join(
            soup.div.find_all(string=True, recursive=False)
        ).rstrip(" ()")
        if soup.div.span is not None:
            if soup.div.span.string is not None:
                classroom = soup.div.span.string.split()[0]

    return (name, classroom if len(classroom) <= 3 else "")


def make_timetable(data: list[dict], *, week: Week) -> Timetable:
    """
    Составляет расписание на неделю.

    :param data: "сырые" данные из API
    :returns: отсортированное расписание
    """

    result: Timetable = [[] for _ in range(7)]

    for item in data:
        name, classroom = parse_title_html(item["title"]["html"])
        start = datetime.strptime(item["start"], "%Y-%m-%d %H:%M")
        end = datetime.strptime(item["end"], "%Y-%m-%d %H:%M")

        index = (start - week.monday).days
        result[index].append(Course(name, classroom, start, end))

    # Если на выходных ничего нет, удаляем лишние дни.
    for _ in range(2):
        if len(result[-1]) > 0:
            break
        del result[-1]

    return result


def write_timetable(group: str, *, offset: int = 0) -> None:
    """
    Получает и сохраняет расписание на неделю в HTML-файл.

    :param group: номер группы
    :param offset: смещение относительно текущей недели (``-1`` — предыдущая
        неделя, ``+1`` — следующая)
    """

    jinja_env = Environment(
        loader=FileSystemLoader("src/templates"),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = jinja_env.get_template("week.html.jinja")

    week = get_week_dates(offset)
    out_file = Path(group) / f"{week.week_id}.html"
    out_file.parent.mkdir(exist_ok=True)

    data = fetch(group, week=week)
    timetable = make_timetable(data, week=week)

    html = template.render(
        group=group,
        timetable=timetable,
        week=week,
        timedelta=timedelta,
    )
    with open(out_file, "w") as out:
        out.write(html)


if __name__ == "__main__":
    write_timetable("441-22", offset=-1)
