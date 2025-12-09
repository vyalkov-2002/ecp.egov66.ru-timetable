# SPDX-License-Identifier: EUPL-1.2
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
from egov66_timetable.types import (
    Alias,
    Lesson,
    LessonDict,
    Settings,
    Timetable
)
from egov66_timetable.utils import get_csrf_token


class Client:

    settings: Settings

    _csrf_token: str | None
    _data: dict | None
    _params_hash: int
    _has_timetable: bool

    # {(classroom, discipline): rename}
    _aliases: dict[tuple[str | None, str], str]

    def __init__(self, settings: Settings):
        """
        :param settings: настройки
        """

        self.settings = settings

        self._csrf_token = None
        self._data = None
        self._params_hash = 0
        self._has_timetable = True

        self._load_aliases()

    def _compute_params_hash(self, *, group: str | None = None,
                             offset: int | None = None) -> int:
        return (
            hash(group or self._current_group)
            + hash(offset or self._current_offset)
            + hash(self.settings["instance"])
            + hash(tuple(sorted(self.settings["cookies"].items())))
        )

    @property
    def csrf_token(self) -> str:
        """
        Токен CSRF для запроса.
        """

        if self._csrf_token is None:
            self._fetch_initial_data()
            assert self._csrf_token is not None
        return self._csrf_token

    def _get_data(self) -> dict:
        """
        :returns: текущие данные
        """

        if self._data is None:
            self._fetch_initial_data()
            assert self._data is not None
        return self._data

    @property
    def _current_group(self) -> str:
        return self._get_data()["serverMemo"]["data"]["group"]

    @property
    def _current_offset(self) -> int:
        data: dict = self._get_data()["serverMemo"]["data"]
        return data.get("addNumWeek", 0) - data.get("minusNumWeek", 0)

    def _load_aliases(self) -> None:
        self._aliases = {}

        alias: Alias
        for alias in self.settings.get("aliases", []):
            discipline = alias.get("discipline")
            classroom = alias.get("classroom")
            rename = alias.get("rename")
            match (discipline, rename):
                case (str(), str()):
                    self._aliases[(classroom, discipline)] = rename

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
            "fingerprint": self._get_data()["fingerprint"],
            "serverMemo": self._get_data()["serverMemo"],
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
        self._get_data()["serverMemo"]["data"].update(
            diff["serverMemo"]["data"]
        )

        for key in ("checksum", "htmlHash"):
            if key in diff["serverMemo"]:
                self._get_data()["serverMemo"][key] = diff["serverMemo"][key]

        self._has_timetable = "events" in diff["serverMemo"]["data"]

    def _set_group(self, group: str) -> None:
        self._perform_data_update("set", group)

    def _go_back(self) -> None:
        self._perform_data_update("minusWeek")

    def _go_forward(self) -> None:
        self._perform_data_update("addWeek")

    def _fetch_initial_data(self) -> None:
        schedule_url = self.settings["instance"] + "/schedule/groups"
        response = (
            httpx.get(schedule_url,
                      cookies=self.settings["cookies"]).raise_for_status()
        )

        self.settings["cookies"]["edinyi_lk_session"] = (
            response.cookies["edinyi_lk_session"]
        )

        soup = BeautifulSoup(response.text, "lxml")
        self._csrf_token = get_csrf_token(soup)

        for tag in soup.find_all("div", attrs={"wire:initial-data": True}):
            if isinstance(attr := tag.attrs.get("wire:initial-data"), str):
                if "scheduleGridWeekType" in attr:
                    self._data = json.loads(attr)
                    break
        else:
            raise InitialDataNotFound

    def fetch_timetable(self, group: str, *, offset: int = 0) -> None:
        """
        Скачивает страницу с расписанием, выбирает нужную группу и неделю.

        :param group: номер группы
        :param offset: смещение относительно текущей недели (``-1`` — предыдущая
            неделя, ``+1`` — следующая)
        """

        self._fetch_initial_data()
        if self._current_group != group:
            self._set_group(group)
        for _ in range(offset, 0):  # offset < 0
            self._go_back()
        for _ in range(offset):  # offset > 0
            self._go_forward()

        self._params_hash = self._compute_params_hash()

    def _make_lesson(self, lesson: LessonDict) -> Lesson:
        name = lesson.get("discipline") or ""
        classroom = (
            lesson.get("place") or lesson.get("classroom") or ""
        ).split(" ")[0]

        if len(classroom) > 3:
            classroom = ""

        if (rename := lesson.get("comment")) is not None:
            # Если в возвращенных данных уже есть комментарий, используем
            # его в качестве названия и пропускаем алиасы.
            name = rename
        elif (rename := self._aliases.get((classroom, name))) is not None:
            # Специфичное переименование: требует совпадения аудитории и
            # названия учебной дисциплины.
            name = rename
        elif (rename := self._aliases.get((None, name))) is not None:
            # Общее переименование: достаточно лишь названия.
            name = rename

        return (lesson["id"], (classroom, name))

    def make_timetable(self, group: str, *, offset: int = 0) -> Timetable:
        """
        Составляет расписание на неделю.

        :param group: номер группы
        :param offset: смещение относительно текущей недели (``-1`` — предыдущая
            неделя, ``+1`` — следующая)
        :returns: отсортированное расписание
        """

        result: Timetable = [{} for _ in range(7)]

        if self._compute_params_hash(group=group, offset=offset) != self._params_hash:
            self.fetch_timetable(group, offset=offset)

        events: dict[str, list[LessonDict]] = {}
        if self._has_timetable:
            events = self._get_data()["serverMemo"]["data"]["events"]

        for cell in events:
            lesson = events[cell][0]
            day_num = lesson["dayWeekNum"]
            lesson_num = abs(lesson["numberPair"] - 1)

            result[day_num][lesson_num] = self._make_lesson(lesson)

        # Если на выходных ничего нет, удаляем лишние дни.
        for _ in range(2):
            if len(result[-1]) > 0:
                break
            del result[-1]

        return result
