# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2025 Matvey Vyalkov
# No warranty

from datetime import date, timedelta
from functools import cached_property
from pathlib import Path
from typing import Annotated, NamedTuple

import iuliia
from pydantic import (
    BeforeValidator,
    HttpUrl,
    TypeAdapter,
    UUID4,
)
from pydantic.dataclasses import dataclass

type Timetable[T] = list[dict[int, T]]

http_url_adapter: TypeAdapter[HttpUrl] = TypeAdapter(HttpUrl)
uuid4_adapter: TypeAdapter[UUID4] = TypeAdapter(UUID4)
path_adapter: TypeAdapter[Path] = TypeAdapter(Path)

HttpUrlStr = Annotated[
    str,
    BeforeValidator(lambda value: str(http_url_adapter.validate_python(value)))
]
UUID4Str = Annotated[
    str,
    BeforeValidator(lambda value: str(uuid4_adapter.validate_python(value)))
]
PathStr = Annotated[
    str,
    BeforeValidator(lambda value: str(path_adapter.validate_python(value)))
]


@dataclass(frozen=True)
class Teacher:

    #: UUID объекта.
    id: UUID4Str

    #: Фамилия.
    surname: str

    #: Имя.
    given_name: str

    #: Отчество.
    patronymic: str

    @property
    def initials(self) -> str:
        """
        Фамилия и инициалы преподавателя (через неразрывный пробел).

        >>> from uuid import uuid4
        >>> Teacher(str(uuid4()), "Менделеев", "Дмитрий", "Иванович").initials
        'Менделеев\xa0Д.\xa0И.'
        """

        nbsp = "\xa0"
        return nbsp.join(
            [self.surname, self.given_name[0] + ".", self.patronymic[0] + "."]
        )

    @property
    def translit(self) -> str:
        """
        Транслителированная фамилия и инициалы преподавателя.

        >>> from uuid import uuid4
        >>> Teacher(str(uuid4()), "Менделеев", "Дмитрий", "Иванович").translit
        'mendeleev_d_i'
        """

        cyrillic = f"{self.surname}_{self.given_name[0]}_{self.patronymic[0]}"
        return iuliia.MOSMETRO.translate(cyrillic.lower())


class LessonData(NamedTuple):

    #: Номер аудитории или группы.
    where: str

    #: Название предмета.
    name: str


class Lesson(NamedTuple):

    #: UUID объекта.
    id: UUID4Str

    #: Данные.
    lesson_data: LessonData


@dataclass
class Week:
    """
    Неделя.

    :param monday: понедельник
    """

    monday: date

    @cached_property
    def sunday(self) -> date:
        return self.monday + timedelta(days=6)

    @cached_property
    def week_id(self) -> str:
        """
        Год и номер недели в году (пример: 1970-48).
        """

        iso_week = self.monday.isocalendar()
        return f"{iso_week.year}-{iso_week.week}"

    def __add__(self, other: object) -> "Week":
        if isinstance(other, int):
            return Week(self.monday + timedelta(weeks=other))
        raise NotImplementedError

    def __sub__(self, other: object) -> "Week":
        if isinstance(other, int):
            return self + -other
        raise NotImplementedError
