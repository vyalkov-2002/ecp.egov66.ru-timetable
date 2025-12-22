# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2025 Matvey Vyalkov
# No warranty

"""
Просмотр расписания колледжей и техникумов Свердловской области
"""

import locale
import logging
from collections.abc import Callable

from egov66_timetable.client import Client, TeacherClient
from egov66_timetable.types import (
    Lesson,
    Settings,
    Teacher,
    Timetable,
    Week,
)
from egov66_timetable.utils import get_current_week

__version__ = "0.0.0"

# timetable, group, week
type TimetableCallback = Callable[[Timetable[Lesson], str, Week], None]
type TeacherTimetableCallback = Callable[[Timetable[list[Lesson]], Teacher, Week], None]

logger = logging.getLogger(__name__)


def get_timetable(groups: str | list[str], callbacks: list[TimetableCallback],
                  *, settings: Settings, offset_range: range = range(1)) -> None:
    """
    Получает расписание и вызывает коллбэк-функции.

    :param groups: номера групп
    :param callbacks: функции обратного вызова
    :param settings: настройки
    :param offset_range: интервал смещений относительно текущей недели (``-1`` —
        предыдущая неделя, ``+1`` — следующая)
    """

    # Выводить дни недели в русской локали
    locale.setlocale(locale.LC_TIME, "ru_RU.utf8")

    if isinstance(groups, str):
        groups = [groups]

    current_week = get_current_week()
    client = Client(settings)
    for offset in offset_range:
        week = current_week + offset
        for group in groups:
            logger.info("Загрузка расписания для группы %s на неделю %s",
                        group, week.week_id)
            timetable = client.make_timetable(group, offset=offset)
            for callback in callbacks:
                callback(timetable, group, week)


def get_teacher_timetable(teachers: Teacher | list[Teacher],
                          callbacks: list[TeacherTimetableCallback], *,
                          settings: Settings,
                          offset_range: range = range(1)) -> None:
    """
    Получает расписание и вызывает коллбэк-функции.

    :param teachers: список преподавателей
    :param callbacks: функции обратного вызова
    :param settings: настройки
    :param offset_range: интервал смещений относительно текущей недели (``-1`` —
        предыдущая неделя, ``+1`` — следующая)
    """

    # Выводить дни недели в русской локали
    locale.setlocale(locale.LC_TIME, "ru_RU.utf8")

    if isinstance(teachers, Teacher):
        teachers = [teachers]

    current_week = get_current_week()
    client = TeacherClient(settings)
    for offset in offset_range:
        week = current_week + offset
        for teacher in teachers:
            logger.info("Загрузка расписания для %s на неделю %s",
                        teacher.initials, week.week_id)
            timetable = client.make_teacher_timetable(teacher.id, offset=offset)
            for callback in callbacks:
                callback(timetable, teacher, week)


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
