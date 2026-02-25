# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2025 Matvey Vyalkov
# No warranty

"""
Запись расписания в базу данных SQLite.
"""

import logging
import sqlite3
from importlib.resources import files

from egov66_timetable import (
    TeacherTimetableCallback,
    TimetableCallback,
)
from egov66_timetable.types import Lesson, Teacher, Timetable, Week
from egov66_timetable.utils import (
    flatten,
    get_type_adapter,
)

logger = logging.getLogger(__name__)


def create_db(conn: sqlite3.Connection) -> sqlite3.Cursor:
    """
    Создает базу данных и индексы.

    :param conn: база данных SQLite
    :returns: курсор SQLite
    """

    sql_script: str = (
        files("egov66_timetable.callbacks.sqlite")
        .joinpath("schema.sql")
        .read_text()
    )

    with conn:
        return conn.executescript(sql_script)


def load_timetable(cur: sqlite3.Cursor | sqlite3.Connection, *,
                   group: str, week: Week | str) -> Timetable[Lesson]:
    """
    Загружает расписание из базы данных.

    :param cur: курсор или база данных SQLite
    :param group: номер группы
    :param week: неделя
    :returns: расписание на неделю для группы
    """

    week_id = week.week_id if isinstance(week, Week) else week

    cur = cur.execute(
        """
        SELECT
          id, classroom, name, day_num, lesson_num
        FROM
          lesson
        WHERE
          group_id = ? AND week_id = ? AND obsolete_since IS NULL
        """,
        [group, week_id]
    )

    result: Timetable[Lesson] = [{} for _ in range(7)]
    for lesson_id, classroom, name, day_num, lesson_num in cur:
        result[day_num][lesson_num] = (lesson_id, (classroom, name))

    # Если на выходных ничего нет, удаляем лишние дни.
    for _ in range(2):
        if len(result[-1]) > 0:
            break
        del result[-1]

    return get_type_adapter(Timetable[Lesson]).validate_python(result)


def sqlite_callback(conn: sqlite3.Connection) -> TimetableCallback:
    """
    Записывает расписание в базу данных.

    :param conn: база данных SQLite
    :returns: коллбэк-функция для расписания группы
    """

    def callback(timetable: Timetable[Lesson], group: str, week: Week) -> None:
        total_deleted: int = 0
        total_added: int = 0

        for day_num, day in enumerate(timetable):
            # 1. Сначала проверим, нет ли уже в БД расписания на этот день.
            cur = conn.execute(
                """
                SELECT
                  id
                FROM
                  lesson
                WHERE
                  group_id = ? AND week_id = ? AND day_num = ?
                """,
                [group, week.week_id, day_num]
            )
            old_lesson_ids: set[str] = {item[0] for item in cur}

            # 2. Получим UUID всех пар на день.
            new_lesson_ids = {lesson[0]: lesson_num
                              for lesson_num, lesson in day.items()}

            # 3. Найдем пары, которые были удалены.
            deleted_lesson_ids: set[str] = old_lesson_ids - new_lesson_ids.keys()
            if (num_deleted := len(deleted_lesson_ids)) > 0:
                total_deleted += num_deleted
                conn.executemany(
                    """
                    UPDATE
                      lesson
                    SET
                      obsolete_since = CURRENT_TIMESTAMP
                    WHERE
                      id = ? AND group_id = ?
                    """,
                    [(lesson_id, group) for lesson_id in deleted_lesson_ids]
                )

            # 4. Найдем пары, которые были добавлены.
            added_lesson_ids: dict[str, int]
            added_lesson_ids = {lesson_id: lesson_num
                                for lesson_id, lesson_num in new_lesson_ids.items()
                                if lesson_id not in old_lesson_ids}

            if (num_added := len(added_lesson_ids)) > 0:
                total_added += num_added
                data = (
                    [*flatten(day[lesson_num]), group, week.week_id,
                     day_num, lesson_num]
                    for lesson_num in added_lesson_ids.values()
                )

                sql: str = (
                    """
                    INSERT INTO
                      lesson(id, classroom, name, group_id, week_id, day_num, lesson_num)
                    VALUES
                      (?, ?, ?, ?, ?, ?, ?)
                    """
                )

                if not __debug__:
                    conn.executemany(sql, data)
                else:
                    for lesson in data:
                        logger.debug("Добавляю новую запись в таблицу lesson: %s", lesson)
                        conn.execute(sql, lesson)

        if total_added > 0:
            logger.info("Новых записей в БД: %d", total_added)
        if total_deleted > 0:
            logger.info("Устаревших записей в БД: %d", total_deleted)
        if total_added + total_deleted == 0:
            logger.info("Расписание в БД уже актуально")

        # Если все получилось, коммитим изменения.
        conn.commit()

    return callback


def sqlite_teacher_callback(conn: sqlite3.Connection) -> TeacherTimetableCallback:
    """
    Добавляет информацию о преподавателе в расписание в базе данных.

    :param conn: база данных SQLite
    :returns: коллбэк-функция для расписания преподавателя
    """

    def callback(timetable: Timetable[list[Lesson]], teacher: Teacher, week: Week) -> None:
        params = ((teacher.id, lesson[0], lesson[1][0])
                  for day in timetable
                  for time_slot in day.values()
                  for lesson in time_slot)

        sql: str = (
            """
            UPDATE
              lesson
            SET
              teacher_id = ?
            WHERE
              id = ? AND group_id = ?
            """
        )

        if not __debug__:
            logger.info("Добавляю информацию о преподавателе в расписание")
            with conn:
                conn.executemany(sql, list(params))
        else:
            for data in params:
                logger.debug("Добавляю информацию о преподавателе к "
                             "занятию (%s, %s)", *data[:-2])
                with conn:
                    conn.execute(sql, data)

    return callback
