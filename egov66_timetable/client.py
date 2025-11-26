# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2025 Matvey Vyalkov
# No warranty

"""
Клиент для сетевых запросов.
"""

import json
import random
import string

import httpx
from bs4 import BeautifulSoup

from egov66_timetable.exceptions import InitialDataNotFound
from egov66_timetable.types import Lesson, Settings, Timetable
from egov66_timetable.utils import get_csrf_token


class Client:

    group: str
    offset: int
    settings: Settings

    _csrf_token: str | None
    _data: dict | None
    _params_hash: int

    def __init__(self, group: str, *, settings: Settings, offset: int = 0):
        """
        :param group: номер группы
        :param settings: настройки
        :param offset: смещение относительно текущей недели (``-1`` — предыдущая
            неделя, ``+1`` — следующая)
        """

        self.group = group
        self.settings = settings
        self.offset = offset

        self._csrf_token = None
        self._data = None
        self._params_hash = 0

    @property
    def dirty(self) -> bool:
        """
        Полученные данные не соответствуют текущим параметрам.
        """

        current = self._compute_params_hash()
        return current != self._params_hash

    @property
    def csrf_token(self) -> str:
        """
        Токен CSRF для запроса.
        """

        if self._csrf_token is None:
            self._fetch_initial_data()
            assert self._csrf_token is not None
        return self._csrf_token

    @property
    def data(self) -> dict:
        """
        Полученные данные.
        """

        if self._data is None:
            self._fetch_initial_data()
            assert self._data is not None
        return self._data

    def _compute_params_hash(self) -> int:
        return (
            hash(self.group)
            + hash(self.offset)
            + hash(tuple(sorted(self.settings["cookies"].items())))
        )

    def _call_livewire_method(self, method: str, *params: str) -> dict:
        endpoint = (
            self.settings["instance"]
            + "/livewire/message/schedule-group-grid"
        )
        signature = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=4)
        )
        headers: dict[str, str] = {
            "X-CSRF-TOKEN": self.csrf_token,
            "X-Livewire": "true",
        }
        payload = {
            "fingerprint": self.data["fingerprint"],
            "serverMemo": self.data["serverMemo"],
            "updates": [{
                "type": "callMethod",
                "payload": {
                    "id": signature,
                    "method": method,
                    "params": list(params)
                }
            }]
        }

        return (
            httpx.post(endpoint, headers=headers, json=payload,
                       cookies=self.settings["cookies"])
                 .raise_for_status()
                 .json()
        )

    def _perform_data_update(self, method: str, *params: str) -> None:
        diff = self._call_livewire_method(method, *params)
        self.data["serverMemo"]["data"].update(
            diff["serverMemo"]["data"]
        )
        self.data["serverMemo"]["checksum"] = diff["serverMemo"]["checksum"]
        self.data["serverMemo"]["htmlHash"] = diff["serverMemo"]["htmlHash"]

    def _set_group(self) -> None:
        self._perform_data_update("set", self.group)

    def _go_back(self) -> None:
        self._perform_data_update("minusWeek")

    def _go_forward(self) -> None:
        self._perform_data_update("addWeek")

    def _fetch_initial_data(self) -> None:
        schedule_url = self.settings["instance"] + "/schedule/groups"
        page_html= (
            httpx.get(schedule_url, cookies=self.settings["cookies"])
                 .raise_for_status()
                 .text
        )

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
        if self.data["serverMemo"]["data"]["group"] != self.group:
            self._set_group()
        for _ in range(self.offset, 0):  # offset < 0
            self._go_back()
        for _ in range(self.offset):  # offset > 0
            self._go_forward()

        self._params_hash = self._compute_params_hash()

    def make_timetable(self) -> Timetable:
        """
        Составляет расписание на неделю.

        :returns: отсортированное расписание
        """

        result: Timetable = [{} for _ in range(7)]

        if self.dirty:
            self.fetch_timetable()

        events: dict[str, list[Lesson]]
        events = self.data["serverMemo"]["data"]["events"]
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
