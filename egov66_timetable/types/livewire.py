# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2025 Matvey Vyalkov
# No warranty

from typing import TypedDict

from pydantic import ConfigDict, JsonValue, with_config

from egov66_timetable.types import UUID4Str

type JsonObject = dict[str, JsonValue]


@with_config(ConfigDict(frozen=True))
class TeacherDict(TypedDict):
    """
    Преподаватель в данных расписания.
    """

    #: UUID объекта.
    id: UUID4Str

    #: Фамилия Имя Отчество
    fio: str | None


@with_config(ConfigDict(frozen=True))
class LessonDict(TypedDict):
    """
    Пара в данных расписания.
    """

    #: UUID объекта.
    id: UUID4Str

    #: Название аудитории.
    classroom: str | None

    #: Номер группы.
    group: str | None

    #: Номер аудитории.
    place: str | None

    #: Название учебной дисциплины.
    discipline: str | None

    #: Комментарий (например, боле конкретное название предмета).
    comment: str | None

    #: Преподаватели.
    teachers: dict[UUID4Str, TeacherDict]

    #: Номер недели, начиная с нуля.
    dayWeekNum: int

    #: Номер пары, начиная с единицы.
    numberPair: int


#: Данные расписания в виде таблицы (матрицы).
type Events = dict[str, list[LessonDict]]


@with_config(ConfigDict(frozen=True))
class LivewireServerMemoData(TypedDict):
    group: str | None
    teacher: UUID4Str | None
    addNumWeek: int | None
    minusNumWeek: int | None
    events: Events


@with_config(ConfigDict(frozen=True))
class LivewireServerMemo(TypedDict):
    checksum: str
    htmlHash: str
    data: LivewireServerMemoData


@with_config(ConfigDict(frozen=True))
class LivewireData(TypedDict):
    fingerprint: JsonObject
    serverMemo: LivewireServerMemo
