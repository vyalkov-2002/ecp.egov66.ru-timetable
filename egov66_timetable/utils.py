# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2025 Matvey Vyalkov
# No warranty

import functools
import json
from collections.abc import Sequence
from datetime import date, timedelta
from pathlib import Path

from bs4 import BeautifulSoup
from pydantic import TypeAdapter

from egov66_timetable.exceptions import (
    CSRFTokenNotFound,
    SessionExpired,
)
from egov66_timetable.types import Week
from egov66_timetable.types.settings import Settings

type NestedSequence = Sequence[object | NestedSequence]


@functools.cache
def get_type_adapter[T](t: type[T]) -> TypeAdapter[T]:
    """
    Создает и кэширует экземпляр :class:`TypeAdapter`.
    """

    return TypeAdapter(t)


def flatten(seq: NestedSequence) -> list[object]:
    """
    Превращает последовательность с несколькими уровнями вложенности в
    одноуровневый список.

    :param seq: последовательность
    :returns: одноуровневый список

    >>> flatten([1, (2, 3)])
    [1, 2, 3]
    >>> flatten(['1', (2, 3)])
    ['1', 2, 3]
    >>> flatten([1, 2, []])
    [1, 2]
    >>> flatten([])
    []
    >>> flatten([1, {2, 3}])
    [1, {2, 3}]
    >>> flatten([{1, 2}, 3])
    [{1, 2}, 3]
    """

    err_msg = "'{0.__name__}' не является последовательностью"
    if not isinstance(seq, Sequence):
        raise TypeError(err_msg.format(type(seq)))

    match seq:
        case []:
            return []
        case [[*head], *tail]:
            return [*flatten(head), *flatten(tail)]
        case [head, *tail]:
            return [head, *flatten(tail)]
        case _:
            raise ValueError


def get_csrf_token(soup: BeautifulSoup) -> str:
    """
    :param soup: разобранный HTML-код страницы
    :returns: CSRF-токен из кода страницы
    :raises SessionExpired: если сеанс завершен
    :raises CSRFTokenNotFound: если токен не найден
    """

    if soup.head is not None:
        meta_csrf_token = soup.head.find("meta", attrs={"name": "csrf-token"})
        if meta_csrf_token is not None:
            csrf_token = meta_csrf_token.attrs.get("content")
            if isinstance(csrf_token, str):
                return csrf_token
        if soup.head.find("meta", attrs={"http-equiv": "refresh"}):
            raise SessionExpired

    raise CSRFTokenNotFound


def get_current_week() -> Week:
    """
    :returns: текущая неделя
    """

    today = date.today()
    monday = today - timedelta(days=today.weekday())

    return Week(monday)


def read_settings() -> Settings:
    """
    Читает настройки из файла settings.json.

    :returns: настройки
    :raises FileNotFoundError: если файл settings.json не найден
    """

    file = Path("settings.json")
    if not file.is_file():
        raise FileNotFoundError("Файл settings.json не найден")

    return get_type_adapter(Settings).validate_json(file.read_bytes())


def write_settings(settings: Settings) -> None:
    """
    Записывает настройки в файл settings.json.

    :param settings: настройки
    """

    with open("settings.json", "w") as file:
        json.dump(settings, file, indent=2, ensure_ascii=False)
