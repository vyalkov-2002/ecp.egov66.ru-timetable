# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2025 Matvey Vyalkov
# No warranty

"""
Клиент для сетевых запросов.
"""

import json
import logging
import random
import string
import uuid
from collections import defaultdict
from typing import Literal, NoReturn
from urllib.parse import ParseResult as URLParseResult, urlparse

import httpx
from bs4 import BeautifulSoup

from egov66_timetable.exceptions import InitialDataNotFound
from egov66_timetable.types import (
    Lesson,
    LessonData,
    Timetable,
)
from egov66_timetable.types.livewire import (
    Events,
    LessonDict,
    LivewireData,
)
from egov66_timetable.types.settings import (
    Alias,
    Settings,
)
from egov66_timetable.utils import (
    get_csrf_token,
    get_type_adapter,
)

logger = logging.getLogger(__name__)


class Client:

    SCHEDULE_PAGE = "/schedule/groups"
    SCHEDULE_ENDPOINT = "/livewire/message/schedule-group-grid"

    settings: Settings
    instance: URLParseResult

    _csrf_token: str | None
    _data: LivewireData | None
    _params_hash: int
    _has_timetable: bool

    # {(classroom, discipline): rename}
    _aliases: dict[Literal["by_classroom", "by_teacher"],
                   dict[tuple[str | None, str], str]]

    def __init__(self, settings: Settings):
        """
        :param settings: настройки
        """

        self.settings = settings
        self.instance = urlparse(self.settings["instance"])

        self._csrf_token = None
        self._data = None
        self._params_hash = 0
        self._has_timetable = True

        self._load_aliases()

    def _compute_params_hash(self, *, search: str | None = None,
                             offset: int | None = None) -> int:
        return (
            hash(search or self._current_search)
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

    def _get_data(self) -> LivewireData:
        """
        :returns: текущие данные
        """

        if self._data is None:
            self._fetch_initial_data()
            assert self._data is not None
        return self._data

    @property
    def _current_search(self) -> str:
        return self._get_data()["serverMemo"]["data"]["group"] or ""

    @property
    def _current_offset(self) -> int:
        data = self._get_data()["serverMemo"]["data"]
        return (data.get("addNumWeek") or 0) - (data.get("minusNumWeek") or 0)

    def _load_aliases(self) -> None:
        self._aliases = {
            "by_classroom": {},
            "by_teacher": {},
        }

        alias: Alias
        for alias in self.settings.get("aliases", []):
            discipline = alias.get("discipline")
            teacher = alias.get("teacher")
            classroom = alias.get("classroom")
            rename = alias.get("rename")
            match (discipline, rename):
                case (str(), str()):
                    self._aliases["by_classroom"][(classroom, discipline)] = rename
                    self._aliases["by_teacher"][(teacher, discipline)] = rename
                case _:
                    logger.warning("Некорректное переименование: %s", alias)

    def _call_livewire_method(self, method: str, *params: str) -> LivewireData:
        endpoint = self.instance._replace(path=self.SCHEDULE_ENDPOINT).geturl()
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

    def _set_search(self, search: str) -> None:
        self._perform_data_update("set", search)

    def _go_back(self) -> None:
        self._perform_data_update("minusWeek")

    def _go_forward(self) -> None:
        self._perform_data_update("addWeek")

    def _fetch_initial_data(self) -> None:
        schedule_url = self.instance._replace(path=self.SCHEDULE_PAGE).geturl()
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

    def fetch_timetable(self, search: str, *, offset: int = 0) -> None:
        """
        Скачивает страницу с расписанием, выбирает нужную группу и неделю.

        :param search: номер группы или преподавателя
        :param offset: смещение относительно текущей недели (``-1`` — предыдущая
            неделя, ``+1`` — следующая)
        """

        if self._data is None:
            self._fetch_initial_data()

        if self._current_search != search:
            self._set_search(search)
        for _ in range(offset - self._current_offset, 0):  # offset < 0
            self._go_back()
        for _ in range(offset - self._current_offset):  # offset > 0
            self._go_forward()

        self._params_hash = self._compute_params_hash()

    def _guess_teacher(self, lesson: LessonDict) -> list[str]:
        teachers: list[str] = []
        search: str | None = None  # Фамилия И.О.
        for teacher in lesson.get("teachers", {}).values():
            if isinstance(teacher, str):
                search = teacher
            elif (fio := teacher.get("fio")) is not None:
                teachers.append(fio)

        if search is None:
            return teachers

        for fio in teachers:
            f, *io = fio.split(" ")
            abbr = f + " " + "".join(name[0] + "." for name in io)
            if abbr == search:
                return [fio]

        logger.error("Не удалось найти преподавателя '%s' в %s",
                     search, teachers)
        return []

    def _guess_lesson_name(self, lesson: LessonDict, classroom: str) -> str:
        name = lesson.get("discipline") or ""
        if (rename := lesson.get("comment")) is not None:
            # Если в возвращенных данных уже есть комментарий, используем
            # его в качестве названия и пропускаем алиасы.
            return rename

        for fio in self._guess_teacher(lesson):
            if (rename := self._aliases["by_teacher"].get((fio, name))) is not None:
                # Специфичное переименование: требует совпадения ФИО преподавателя и
                # названия учебной дисциплины.
                return rename
        if (rename := self._aliases["by_classroom"].get((classroom, name))) is not None:
            # Специфичное переименование: требует совпадения аудитории и
            # названия учебной дисциплины.
            return rename
        if (rename := self._aliases["by_classroom"].get((None, name))) is not None:
            # Общее переименование: достаточно лишь названия.
            return rename

        return name

    def _guess_lesson_classroom(self, lesson: LessonDict) -> str:
        classroom = (
            lesson.get("place") or lesson.get("classroom") or ""
        ).split(" ")[0]

        if len(classroom) > 3:
            classroom = ""

        return classroom

    def _make_lesson(self, lesson: LessonDict) -> Lesson:
        classroom = self._guess_lesson_classroom(lesson)
        name = self._guess_lesson_name(lesson, classroom)

        return Lesson(lesson["id"], LessonData(classroom, name))

    def _fetch_events(self, search: str, *, offset: int) -> Events:
        if self._compute_params_hash(search=search, offset=offset) != self._params_hash:
            self.fetch_timetable(search, offset=offset)

        events = {}
        if self._has_timetable:
            events = self._get_data()["serverMemo"]["data"]["events"]
        return get_type_adapter(Events).validate_python(events)

    def make_timetable(self, group: str, *, offset: int = 0) -> Timetable[Lesson]:
        """
        Составляет расписание на неделю.

        :param group: номер группы
        :param offset: смещение относительно текущей недели (``-1`` — предыдущая
            неделя, ``+1`` — следующая)
        :returns: отсортированное расписание
        """

        result: Timetable[Lesson] = [{} for _ in range(7)]

        events = self._fetch_events(group, offset=offset)
        for cell in events:
            lesson = events[cell][0]
            day_num = lesson["dayWeekNum"]
            lesson_num = abs(lesson["numberPair"] - 1)

            if len(events[cell]) == 1:
                result[day_num][lesson_num] = self._make_lesson(lesson)
            else:
                result[day_num][lesson_num] = Lesson(
                    str(uuid.uuid4()),
                    LessonData("?", "Ошибка в расписании: "
                                    "Несколько пар в одно и то же время")
                )

        # Если на выходных ничего нет, удаляем лишние дни.
        for _ in range(2):
            if len(result[-1]) > 0:
                break
            del result[-1]

        return result


class TeacherClient(Client):

    SCHEDULE_PAGE = "/schedule/teachers"
    SCHEDULE_ENDPOINT = "/livewire/message/schedule-teacher-grid"

    @property
    def _current_search(self) -> str:
        return self._get_data()["serverMemo"]["data"]["teacher"] or ""

    def _make_teacher_lesson(self, lesson: LessonDict) -> Lesson:
        classroom = self._guess_lesson_classroom(lesson)
        name = self._guess_lesson_name(lesson, classroom)

        return Lesson(
            lesson["id"],
            LessonData(lesson.get("group") or "", name)
        )

    def make_teacher_timetable(self, teacher: str, *, offset: int = 0) -> Timetable[list[Lesson]]:
        """
        Составляет расписание на неделю.

        :param teacher: номер учителя (UUID)
        :param offset: смещение относительно текущей недели (``-1`` — предыдущая
            неделя, ``+1`` — следующая)
        :returns: отсортированное расписание
        """

        result: Timetable[list[Lesson]] = [defaultdict(list) for _ in range(7)]

        events = self._fetch_events(teacher, offset=offset)
        for cell in events:
            for lesson in events[cell]:
                day_num = lesson["dayWeekNum"]
                lesson_num = abs(lesson["numberPair"] - 1)
                result[day_num][lesson_num].append(self._make_teacher_lesson(lesson))

        # Если на выходных ничего нет, удаляем лишние дни.
        for _ in range(2):
            if len(result[-1]) > 0:
                break
            del result[-1]

        return result

    def make_timetable(self, *args: object, **kwargs: object) -> NoReturn:  # type: ignore[override]
        raise NotImplementedError
