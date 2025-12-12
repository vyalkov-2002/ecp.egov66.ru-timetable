-- SPDX-FileCopyrightText: 2025 Matvey Vyalkov
--
-- SPDX-License-Identifier: EUPL-1.2

PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS lesson(
    -- UUID пары
    id TEXT PRIMARY KEY NOT NULL,

    -- Номер аудитории
    classroom TEXT,

    -- Название предмета
    name TEXT,

    -- Группа, у которой пара стоит в расписании
    group_id TEXT NOT NULL,

    -- Номер года и номер недели
    week_id TEXT NOT NULL,

    -- Номер дня недели (0 - понедельник, 6 - воскресенье)
    day_num INTEGER NOT NULL,

    -- Номер пары (начиная с нуля)
    lesson_num INTEGER NOT NULL,

    -- Если TRUE, то пара была удалена из расписания
    is_deleted INTEGER NOT NULL DEFAULT FALSE,

    -- Дата добавления или обновления
    last_updated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Дата последней проверки
    last_checked TEXT NOT NULL DEFAULT '1970-01-01 00:00:00'
);

CREATE INDEX IF NOT EXISTS idx_lessons_group
ON lesson (group_id, week_id, day_num);
