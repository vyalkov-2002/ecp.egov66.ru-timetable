# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2025 Matvey Vyalkov
# No warranty

from datetime import date

from egov66_timetable.types import Week

monday = date.fromisocalendar(2000, 2, 1)


def test_week_id():
    week = Week(monday)
    Week.from_week_id(week.week_id) == week


def test_week_add():
    week = Week(monday) + 1
    assert week.monday == date.fromisocalendar(2000, 3, 1)
    assert week.sunday == date.fromisocalendar(2000, 3, 7)


def test_week_sub():
    week = Week(monday) - 1
    assert week.monday == date.fromisocalendar(2000, 1, 1)
    assert week.sunday == date.fromisocalendar(2000, 1, 7)
