# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2025 Matvey Vyalkov
# No warranty

"""
Клиент для сетевых запросов.
"""

import json
import os
import random
import string

import httpx
from bs4 import BeautifulSoup

from egov66_timetable.exceptions import InitialDataNotFound
from egov66_timetable.types import Lesson, Timetable
from egov66_timetable.utils import get_csrf_token


class Client:

    group: str
    offset: int

    _instance: str
    _cookies: dict[str, str]
    _csrf_token: str | None = None
    _data: dict | None = None

    def __init__(self, group: str, *, offset: int = 0):
        """
        :param group: номер группы
        :param offset: смещение относительно текущей недели (``-1`` — предыдущая
            неделя, ``+1`` — следующая)
        """

        self.group = group
        self.offset = offset

        self._instance = os.environ["ECP_EGOV66_INSTANCE"]
        self._cookies = {
            "edinyi_lk_session": os.environ["ECP_EGOV66_SESSION_ID"]
        }

    def _call_livewire_method(self, method: str, *params: str) -> dict:
        if self._data is None or self._csrf_token is None:
            raise ValueError("Initial data has not been fetched")

        endpoint = f"{self._instance}/livewire/message/schedule-group-grid"
        signature = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=4)
        )
        headers: dict[str, str] = {
            "X-CSRF-TOKEN": self._csrf_token,
            "X-Livewire": "true",
        }
        payload = {
            "fingerprint": self._data["fingerprint"],
            "serverMemo": self._data["serverMemo"],
            "updates": [{
                "type": "callMethod",
                "payload": {
                    "id": signature,
                    "method": method,
                    "params": list(params)
                }
            }]
        }

        return httpx.post(endpoint,
            cookies=self._cookies,
            headers=headers,
            json=payload
        ).raise_for_status().json()

    def _perform_data_update(self, method: str, *params: str) -> None:
        if self._data is None:
            raise ValueError("Initial data has not been fetched")

        diff = self._call_livewire_method(method, *params)
        self._data["serverMemo"]["data"].update(
            diff["serverMemo"]["data"]
        )
        self._data["serverMemo"]["checksum"] = diff["serverMemo"]["checksum"]
        self._data["serverMemo"]["htmlHash"] = diff["serverMemo"]["htmlHash"]

    def _set_group(self) -> None:
        self._perform_data_update("set", self.group)

    def _go_back(self) -> None:
        self._perform_data_update("minusWeek")

    def _go_forward(self) -> None:
        self._perform_data_update("addWeek")

    def _fetch_initial_data(self) -> None:
        schedule_url = f"{self._instance}/schedule/groups"
        page_html = httpx.get(schedule_url,
            cookies=self._cookies
        ).raise_for_status().text

        soup = BeautifulSoup(page_html, "lxml")
        self._csrf_token = get_csrf_token(soup)

        for tag in soup.find_all("div", attrs={"wire:initial-data": True}):
            if isinstance(attr := tag.attrs.get("wire:initial-data"), str):
                if "scheduleGridWeekType" in attr:
                    self._data = json.loads(attr)
                    break
        else:
            raise InitialDataNotFound

    def fetch_timetable(self) -> None:
        """
        Скачивает страницу с расписанием, выбирает нужную группу и неделю.
        """

        self._fetch_initial_data()
        self._set_group()
        for _ in range(self.offset, 0):  # offset < 0
            self._go_back()
        for _ in range(self.offset):  # offset > 0
            self._go_forward()

    def make_timetable(self) -> Timetable:
        """
        Составляет расписание на неделю.

        :returns: отсортированное расписание
        """

        if self._data is None:
            self.fetch_timetable()
            assert self._data is not None

        result: Timetable = [{} for _ in range(7)]

        events: dict[str, list[Lesson]]
        events = self._data["serverMemo"]["data"]["events"]
        for cell in events:
            lesson = events[cell][0]

            name = lesson.get("discipline") or ""
            classroom = (
                lesson.get("place") or lesson.get("classroom") or ""
            ).split(" ")[0]
            if len(classroom) > 3:
                classroom = ""

            day_num = lesson["dayWeekNum"]
            lesson_num = abs(lesson["numberPair"] - 1)

            result[day_num][lesson_num] = (classroom, name)

        # Если на выходных ничего нет, удаляем лишние дни.
        for _ in range(2):
            if len(result[-1]) > 0:
                break
            del result[-1]

        return result
