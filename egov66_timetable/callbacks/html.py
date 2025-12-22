# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2025 Matvey Vyalkov
# No warranty

"""
Вывод расписания в HTML-файлы.
"""

import logging
from datetime import timedelta
from pathlib import Path

import jinja2

from egov66_timetable import (
    TeacherTimetableCallback,
    TimetableCallback,
)
from egov66_timetable.types import (
    Lesson,
    Settings,
    Teacher,
    Timetable,
    Week,
)

# classroom, name, rowspan
type CollapsedTimetable = list[list[tuple[str, str, int]]]

# group, name
type CollapsedTeacherTimetable = list[list[list[tuple[str, str]]]]

logger = logging.getLogger(__name__)

jinja_env = jinja2.Environment(
    loader=jinja2.PackageLoader("egov66_timetable"),
    autoescape=jinja2.select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True,
)


def load_template() -> jinja2.Template:
    """
    :returns: шаблон расписания
    """
    return jinja_env.get_template("week.html.jinja")


def load_teacher_template() -> jinja2.Template:
    """
    :returns: шаблон расписания
    """
    return jinja_env.get_template("teacher_week.html.jinja")


def collapse_timetable(timetable: Timetable[Lesson]) -> CollapsedTimetable:
    """
    Преобразует расписание в пригодное для рендеринга в формате таблицы, а
    именно переводит его из формата ``{номер_пары: (аудитория, предмет)}`` в
    формат ``(аудитория, предмет, число_повторов)``.

    Если расписания на день нет, вставляет вместо него три пустые строки.

    :param timetable: исходное расписание
    """

    result: CollapsedTimetable = [[] for _ in range(len(timetable))]
    # pylint: disable=consider-using-enumerate
    for day in range(len(timetable)):
        if len(timetable[day]) != 0:
            for lesson_num in range(max(timetable[day]) + 1):
                this_lesson = timetable[day].get(lesson_num) or (None, ("нет", ""))
                classroom, name = this_lesson[1]

                if (
                    # если это первая итерация
                    len(result[day]) == 0
                    # если вместо пары "окно"
                    or this_lesson[0] is None
                    # если эта пара такая же, как прошлая
                    or (classroom, name) != result[day][-1][:2]
                ):
                    result[day].append(
                        (classroom, name, 1)
                    )
                else:
                    # Увеличиваем rowspan на 1
                    result[day][-1] = (
                        *result[day][-1][:2], result[day][-1][2] + 1
                    )
        else:
            # Расписания еще нет, добавляем 3 пустые строки.
            result[day].extend([("", "", 1)] * 3)

    return result


def collapse_teacher_timetable(timetable: Timetable[list[Lesson]]) -> CollapsedTeacherTimetable:
    """
    Преобразует расписание в пригодное для рендеринга в формате таблицы, а
    именно переводит его из формата ``{номер_пары: [(группа, предмет), ...]}`` в
    формат ``(группа, предмет)``.

    Если расписания на день нет, вставляет вместо него три пустые строки.

    :param timetable: исходное расписание
    """

    result: CollapsedTeacherTimetable = [[] for _ in range(len(timetable))]
    # pylint: disable=consider-using-enumerate
    for day in range(len(timetable)):
        if len(timetable[day]) != 0:
            for lesson_num in range(max(timetable[day]) + 1):
                time_slot = timetable[day].get(lesson_num, [])
                if len(time_slot) > 0:
                    # если вместо пары "окно"
                    result[day].append([lesson[1] for lesson in time_slot])
                else:
                    result[day].append([("нет", "")])
        else:
            # Расписания еще нет, добавляем 3 пустые строки.
            result[day].extend([[("", "")]] * 3)

    return result


def _html_callback(settings: Settings, *, template: jinja2.Template,
                   out_file: Path, **template_args: object) -> None:

    out_file.parent.mkdir(exist_ok=True)
    css_path = settings.get("css_path", "../egov66_timetable/static/styles.css")

    logger.info("Вывод расписания в файл %s", out_file)
    html = template.render(
        timedelta=timedelta,
        css_path=css_path,
        **template_args,
    ).lstrip()
    with open(out_file, "w") as out:
        out.write(html)


def html_callback(settings: Settings, *,
                  template: jinja2.Template | None = None,
                  **template_args: object) -> TimetableCallback:
    """
    Записывает расписание студента в HTML-файлы.

    :param settings: настройки
    :param template: свой шаблон Jinja2
    :param template_args: дополнительные параметры для шаблона
    """

    if template is None:
        template = load_template()

    def callback(timetable: Timetable[Lesson], group: str, week: Week) -> None:
        out_file = Path(group) / f"{week.week_id}.html"
        _html_callback(settings, template=template, out_file=out_file,
                       group=group, week=week,
                       timetable=collapse_timetable(timetable),
                       **template_args)

    return callback


def html_teacher_callback(settings: Settings, *,
                          template: jinja2.Template | None = None,
                          **template_args: object) -> TeacherTimetableCallback:
    """
    Записывает расписание преподавателя в HTML-файлы.

    :param settings: настройки
    :param template: свой шаблон Jinja2
    :param template_args: дополнительные параметры для шаблона
    """

    if template is None:
        template = load_teacher_template()

    def callback(timetable: Timetable[list[Lesson]], teacher: Teacher, week: Week) -> None:
        out_file = Path(teacher.translit) / f"{week.week_id}.html"
        _html_callback(settings, template=template, out_file=out_file,
                       teacher=teacher, week=week,
                       timetable=collapse_teacher_timetable(timetable),
                       **template_args)

    return callback
