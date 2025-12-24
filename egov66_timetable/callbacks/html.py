# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2025 Matvey Vyalkov
# No warranty

"""
Вывод расписания в HTML-файлы.
"""

import logging
from collections import defaultdict
from datetime import timedelta
from pathlib import Path

import jinja2

from egov66_timetable import (
    TeacherTimetableCallback,
    TimetableCallback,
)
from egov66_timetable.types import (
    Lesson,
    Teacher,
    Timetable,
    Week,
)
from egov66_timetable.types.settings import Settings

# classroom, name, rowspan
type CollapsedTimetable = list[list[tuple[str, str, int]]]

# group, name, rowspan
type CollapsedTeacherTimetable = list[list[list[tuple[str, str, int]]]]

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
        if len(timetable[day]) == 0:
            # Расписания еще нет, добавляем 3 пустые строки.
            result[day].extend([("", "", 1)] * 3)
            continue

        for lesson_num in range(max(timetable[day]) + 1):
            this_lesson = timetable[day].get(lesson_num) or (None, ("нет", ""))
            classroom, name = this_lesson[1]

            if (
                # если это первая итерация
                len(result[day]) == 0
                # если вместо пары "окно"
                or this_lesson[0] is None
                # если эта пара не такая же, как прошлая
                or (classroom, name) != result[day][-1][:2]
            ):
                # Добавляем новую строку
                result[day].append(
                    (classroom, name, 1)
                )
            else:
                # Увеличиваем rowspan на 1
                current_rowspan = result[day][-1][2]
                result[day][-1] = (
                    classroom, name, current_rowspan + 1
                )

    return result


def collapse_teacher_timetable(timetable: Timetable[list[Lesson]]) -> CollapsedTeacherTimetable:
    """
    Преобразует расписание в пригодное для рендеринга в формате таблицы, а
    именно переводит его из формата ``{номер_пары: [(группа, предмет), ...]}`` в
    формат ``(группа, предмет, число_повторов)``.

    ``число_повторов``:

    * **>0:** если одна и та же группа занимается одним и тем же предметом
        несколько пар подряд
    * **<0:** если у нескольких групп один и тот же предмет в одно и то же время
        (указывается только один раз)
    * **=0:** если у нескольких групп один и тот же предмет (указывается при
        повторах, в этом случае ``предмет`` - пустая строка)

    Если расписания на день нет, вставляет вместо него три пустые строки.

    :param timetable: исходное расписание
    """

    result: CollapsedTeacherTimetable = [[] for _ in range(len(timetable))]
    # pylint: disable=consider-using-enumerate
    for day in range(len(timetable)):
        if len(timetable[day]) == 0:
            # Расписания еще нет, добавляем 3 пустые строки.
            result[day].extend([[("", "", 1)]] * 3)
            continue

        for lesson_num in range(max(timetable[day]) + 1):
            time_slot = timetable[day].get(lesson_num, [])

            if len(time_slot) == 0:
                # если вместо пары "окно"
                result[day].append([("нет", "", 1)])
                continue

            if len(time_slot) == 1:
                group, name = time_slot[0][1]
                if (
                    # если это первая итерация
                    len(result[day]) == 0
                    # если прошлая пара была совмещенной у нескольких групп
                    or len(result[day][-1]) != 1
                    # если эта пара не такая же, как прошлая
                    or (group, name) != result[day][-1][0][:2]
                ):
                    # Добавляем новую строку
                    result[day].append([(group, name, 1)])
                else:
                    # Увеличиваем rowspan на 1
                    current_rowspan = result[day][-1][0][2]
                    result[day][-1] = [
                        (group, name, current_rowspan + 1)
                    ]
                continue

            time_slot_collapsed: dict[str, list[str]] = defaultdict(list)
            for (_, (group, name)) in time_slot:
                time_slot_collapsed[name].append(group)

            result[day].append([])
            for name in sorted(time_slot_collapsed):
                groups = time_slot_collapsed[name]
                head, *tail = sorted(groups)
                result[day][-1].append(
                    (head, name, -len(groups))
                )
                for group in tail:
                    result[day][-1].append(
                        (group, "", 0)
                    )

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
