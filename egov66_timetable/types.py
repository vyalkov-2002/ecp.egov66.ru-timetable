# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2025 Matvey Vyalkov
# No warranty

from dataclasses import dataclass
from datetime import date, timedelta
from typing import TypedDict, Required

type Timetable = list[dict[int, tuple[str, str]]]


@dataclass(frozen=True)
class Week:
    """
    Неделя.
    """

    # Понедельник, полночь.
    monday: date

    # Воскресенье, полночь.
    sunday: date

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


class Lesson(TypedDict, total=False):
    """
    Пара в расписании.
    """

    #: Название аудитории.
    classroom: str

    #: Номер аудитории.
    place: str

    #: Название учебной дисциплины.
    discipline: str

    #: Номер недели, начиная с нуля.
    dayWeekNum: Required[int]

    #: Номер пары, начиная с единицы.
    numberPair: Required[int]


class Settings(TypedDict, total=False):
    """
    Настройки в формате JSON.
    """

    #: Адрес сайта личного кабинета.
    instance: Required[str]

    #: Идентификатор сеанса в личном кабинете (из cookie).
    session_id: str

    #: Путь, по которому браузер будет запрашивать таблицу стилей.
    css_path: str
