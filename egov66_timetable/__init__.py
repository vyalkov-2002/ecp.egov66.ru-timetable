# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2025 Matvey Vyalkov
# No warranty

"""
Просмотр расписания колледжей и техникумов Свердловской области
"""

import locale
from datetime import timedelta
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from egov66_timetable.client import Client
from egov66_timetable.types import Settings
from egov66_timetable.utils import get_current_week

__version__ = "0.0.0"


def write_timetable(group: str, *, settings: Settings, offset: int = 0) -> None:
    """
    Получает и сохраняет расписание на неделю в HTML-файл.

    :param group: номер группы
    :param settings: настройки
    :param offset: смещение относительно текущей недели (``-1`` — предыдущая
        неделя, ``+1`` — следующая)
    """

    # Выводить дни недели в русской локали
    locale.setlocale(locale.LC_TIME, "ru_RU.utf8")

    jinja_env = Environment(
        loader=PackageLoader("egov66_timetable"),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = jinja_env.get_template("week.html.jinja")

    week = get_current_week() + offset
    out_file = Path(group) / f"{week.week_id}.html"
    out_file.parent.mkdir(exist_ok=True)

    client = Client(group, settings=settings, offset=offset)
    timetable = client.make_timetable()

    html = template.render(
        css_path=settings.get("css_path", "../egov66_timetable/static/styles.css"),
        group=group,
        timetable=timetable,
        week=week,
        timedelta=timedelta,
    )
    with open(out_file, "w") as out:
        out.write(html)
