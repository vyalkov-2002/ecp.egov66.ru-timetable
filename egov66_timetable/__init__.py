# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2025 Matvey Vyalkov
# No warranty

"""
Просмотр расписания колледжей и техникумов Свердловской области
"""

import locale
from datetime import timedelta
from pathlib import Path

import jinja2

from egov66_timetable.client import Client
from egov66_timetable.types import Settings, Timetable
from egov66_timetable.utils import get_current_week

__version__ = "0.0.0"

# classroom, name, rowspan
type CollapsedTimetable = list[list[tuple[str, str, int]]]


def load_template() -> jinja2.Template:
    """
    :returns: шаблон расписания
    """

    jinja_env = jinja2.Environment(
        loader=jinja2.PackageLoader("egov66_timetable"),
        autoescape=jinja2.select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    return jinja_env.get_template("week.html.jinja")


def collapse_timetable(timetable: Timetable) -> CollapsedTimetable:
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
                this_lesson = timetable[day].get(lesson_num)
                classroom, name = this_lesson or ["нет", ""]

                if (
                    # если это первая итерация
                    len(result[day]) == 0
                    # если вместо пары "окно"
                    or this_lesson is None
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


def write_timetable(group: str, *, settings: Settings, offset: int = 0,
                    template: jinja2.Template | None = None,
                    **template_args: object) -> None:
    """
    Получает и сохраняет расписание на неделю в HTML-файл.

    :param group: номер группы
    :param settings: настройки
    :param offset: смещение относительно текущей недели (``-1`` — предыдущая
        неделя, ``+1`` — следующая)
    :param template_args: дополнительные параметры для шаблона
    """

    if template is None:
        template = load_template()

    # Выводить дни недели в русской локали
    locale.setlocale(locale.LC_TIME, "ru_RU.utf8")

    week = get_current_week() + offset
    out_file = Path(group) / f"{week.week_id}.html"
    out_file.parent.mkdir(exist_ok=True)

    client = Client(group, settings=settings, offset=offset)
    timetable = client.make_timetable()

    html = template.render(
        css_path=settings.get("css_path", "../egov66_timetable/static/styles.css"),
        group=group,
        timetable=collapse_timetable(timetable),
        week=week,
        timedelta=timedelta,
        **template_args,
    ).lstrip()
    with open(out_file, "w") as out:
        out.write(html)
