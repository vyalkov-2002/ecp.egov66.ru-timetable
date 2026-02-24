# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2025 Matvey Vyalkov
# No warranty

"""
Просмотр расписания колледжей и техникумов Свердловской области
"""

import locale
import logging
from collections import defaultdict
from collections.abc import Callable

from egov66_timetable.client import Client, TeacherClient
from egov66_timetable.exceptions import NetworkError
from egov66_timetable.types import (
    Lesson,
    Teacher,
    Timetable,
    Week,
)
from egov66_timetable.types.settings import Settings
from egov66_timetable.utils import get_current_week

__version__ = "0.0.0"

# timetable, group, week
type TimetableCallback = Callable[[Timetable[Lesson], str, Week], None]
type TeacherTimetableCallback = Callable[[Timetable[list[Lesson]], Teacher, Week], None]

logger = logging.getLogger(__name__)


def get_timetable(
    groups: str | list[str], callbacks: list[TimetableCallback], *,
    settings: Settings, offset_range: range = range(1)
) -> dict[int, list[str]]:
    """
    Получает расписание и вызывает коллбэк-функции.

    :param groups: номера групп
    :param callbacks: функции обратного вызова
    :param settings: настройки
    :param offset_range: интервал смещений относительно текущей недели (``-1`` —
        предыдущая неделя, ``+1`` — следующая)
    :returns: входные параметры, которые не были обработаны из-за ошибок, в виде
        словаря, где ключ — смещение, а значение — список групп.
    """

    # Выводить дни недели в русской локали
    locale.setlocale(locale.LC_TIME, "ru_RU.utf8")

    if isinstance(groups, str):
        groups = [groups]

    current_week = get_current_week()
    client = Client(settings)
    failures: defaultdict[int, list[str]] = defaultdict(list)
    for offset in offset_range:
        week = current_week + offset
        for group in groups:
            logger.info("Загрузка расписания для группы %s на неделю %s",
                        group, week.week_id)
            try:
                timetable = client.make_timetable(group, offset=offset)
            except NetworkError:
                logger.error("Ошибка сети")
                failures[offset].append(group)
                continue

            for callback in callbacks:
                callback(timetable, group, week)

    return failures


def get_teacher_timetable(teachers: Teacher | list[Teacher],
                          callbacks: list[TeacherTimetableCallback], *,
                          settings: Settings,
                          offset_range: range = range(1)) -> dict[int, list[Teacher]]:
    """
    Получает расписание и вызывает коллбэк-функции.

    :param teachers: список преподавателей
    :param callbacks: функции обратного вызова
    :param settings: настройки
    :param offset_range: интервал смещений относительно текущей недели (``-1`` —
        предыдущая неделя, ``+1`` — следующая)
    :returns: входные параметры, которые не были обработаны из-за ошибок, в виде
        словаря, где ключ — смещение, а значение — список преподавателей.
    """

    # Выводить дни недели в русской локали
    locale.setlocale(locale.LC_TIME, "ru_RU.utf8")

    if isinstance(teachers, Teacher):
        teachers = [teachers]

    current_week = get_current_week()
    client = TeacherClient(settings)
    failures: defaultdict[int, list[Teacher]] = defaultdict(list)
    for offset in offset_range:
        week = current_week + offset
        for teacher in teachers:
            logger.info("Загрузка расписания для %s на неделю %s",
                        teacher.initials, week.week_id)
            try:
                timetable = client.make_teacher_timetable(teacher.id, offset=offset)
            except NetworkError:
                logger.error("Ошибка сети")
                failures[offset].append(teacher)
                continue

            for callback in callbacks:
                callback(timetable, teacher, week)

    return failures


def write_timetable(groups: str | list[str], *,
                    settings: Settings, offset_range: range = range(1)) -> None:
    """
    Получает расписание и записывает его в HTML-файлы.

    :param groups: номера групп
    :param callbacks: функции обратного вызова
    :param settings: настройки
    :param offset_range: интервал смещений относительно текущей недели (``-1`` —
        предыдущая неделя, ``+1`` — следующая)
    """

    from egov66_timetable.callbacks.html import html_callback

    get_timetable(groups, [html_callback(settings)],
                  settings=settings, offset_range=offset_range)
