# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2025 Matvey Vyalkov
# No warranty

from dataclasses import dataclass
from datetime import date, timedelta
from typing import TypedDict, NotRequired

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


class Lesson(TypedDict):
    """
    Пара в расписании.
    """

    #: Название аудитории.
    classroom: str | None

    #: Номер аудитории.
    place: str | None

    #: Название учебной дисциплины.
    discipline: str | None

    #: Комментарий (например, боле конкретное название предмета).
    comment: str | None

    #: Номер недели, начиная с нуля.
    dayWeekNum: int

    #: Номер пары, начиная с единицы.
    numberPair: int


class Alias(TypedDict):
    """
    Настройка, которая позволяет дать более короткое имя учебной дисциплине.
    """

    #: Название учебной дисциплины как в личном кабинете.
    discipline: str

    #: Номер аудитории.
    classroom: NotRequired[str]

    #: Новое название.
    rename: str


class Settings(TypedDict):
    """
    Настройки в формате JSON.
    """

    #: Адрес сайта личного кабинета.
    instance: str

    #: Cookie-файлы.
    cookies: dict[str, str]

    #: Путь, по которому браузер будет запрашивать таблицу стилей.
    css_path: NotRequired[str]

    #: Список переименований.
    aliases: NotRequired[list[Alias]]
