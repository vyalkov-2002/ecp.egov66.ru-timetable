# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2025 Matvey Vyalkov
# No warranty

import locale
import os
import sys
from datetime import timedelta
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

import egov66_timetable
from egov66_timetable.client import Client
from egov66_timetable.utils import get_current_week

# Выводить дни недели в русской локали
locale.setlocale(locale.LC_TIME, "ru_RU.utf8")


def write_timetable(group: str, *, offset: int = 0) -> None:
    """
    Получает и сохраняет расписание на неделю в HTML-файл.

    :param group: номер группы
    :param offset: смещение относительно текущей недели (``-1`` — предыдущая
        неделя, ``+1`` — следующая)
    """

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

    client = Client(group, offset=offset)
    timetable = client.make_timetable()

    html = template.render(
        css_path=os.getenv("ECP_EGOV66_STYLESHEET",
                           "../egov66_timetable/static/styles.css"),
        group=group,
        timetable=timetable,
        week=week,
        timedelta=timedelta,
    )
    with open(out_file, "w") as out:
        out.write(html)


def main() -> None:
    args = sys.argv[1:]
    if not 1 <= len(args) <= 2:
        print("usage: ecp-egov66-timetable group [offset]")
        sys.exit(1)

    group = args[0]
    offset = int(args[1]) if len(args) == 2 else 0
    write_timetable(group, offset=offset)


if __name__ == "__main__":
    main()
