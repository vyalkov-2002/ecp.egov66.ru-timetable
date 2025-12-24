# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2025 Matvey Vyalkov
# No warranty

from typing import TypedDict, NotRequired

from pydantic import ConfigDict, with_config

from egov66_timetable.types import HttpUrlStr, PathStr


@with_config(ConfigDict(extra="forbid", validate_assignment=True))
class Alias(TypedDict):
    """
    Настройка, которая позволяет дать более короткое имя учебной дисциплине.
    """

    #: Название учебной дисциплины как в личном кабинете.
    discipline: str

    #: ФИО преподавателя.
    teacher: NotRequired[str]

    #: Номер аудитории.
    classroom: NotRequired[str]

    #: Новое название.
    rename: str


@with_config(ConfigDict(extra="allow", validate_assignment=True))
class Settings(TypedDict):
    """
    Настройки в формате JSON.
    """

    #: Адрес сайта личного кабинета.
    instance: HttpUrlStr

    #: Cookie-файлы.
    cookies: dict[str, str]

    #: Путь, по которому браузер будет запрашивать таблицу стилей.
    css_path: NotRequired[PathStr]

    #: Список переименований.
    aliases: NotRequired[list[Alias]]
