# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2025 Matvey Vyalkov
# No warranty

import json
import locale
import sys
from datetime import timedelta
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from egov66_timetable.client import Client
from egov66_timetable.types import Settings
from egov66_timetable.utils import get_current_week

# Выводить дни недели в русской локали
locale.setlocale(locale.LC_TIME, "ru_RU.utf8")


def write_timetable(group: str, *, settings: Settings, offset: int = 0) -> None:
    """
    Получает и сохраняет расписание на неделю в HTML-файл.

    :param group: номер группы
    :param settings: настройки
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


def read_settings() -> Settings:
    """
    Читает настройки из файла settings.json.

    :returns: настройки
    """

    file = Path("settings.json")
    if not file.is_file():
        print("Файл settings.json не найден", file=sys.stderr)
        sys.exit(1)

    return json.loads(file.read_text())


def write_settings(settings: Settings) -> None:
    """
    Записывает настройки в файл settings.json.

    :param settings: настройки
    """

    with open("settings.json", "w") as file:
        json.dump(settings, file, indent=2)


def main() -> None:
    args = sys.argv[1:]
    if not 1 <= len(args) <= 2:
        print("usage: ecp-egov66-timetable group [offset]", file=sys.stderr)
        sys.exit(1)

    group = args[0]
    offset = int(args[1]) if len(args) == 2 else 0

    settings = read_settings()
    write_timetable(group, offset=offset, settings=settings)


if __name__ == "__main__":
    main()
