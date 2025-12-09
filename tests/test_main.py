# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2025 Matvey Vyalkov
# No warranty

from uuid import uuid4

from egov66_timetable import collapse_timetable
from egov66_timetable.types import Timetable


def test_collapse_timetable():
    day = {
        0: (str(uuid4()), ("100", "А")),
        1: (str(uuid4()), ("100", "А")),
        2: (str(uuid4()), ("200", "Б")),
        3: (str(uuid4()), ("100", "А")),
        4: (str(uuid4()), ("100", "А")),
    }
    timetable: Timetable = [day.copy() for _ in range(7)]

    day_collapsed = [
        ("100", "А", 2),
        ("200", "Б", 1),
        ("100", "А", 2),
    ]
    expected = [day_collapsed.copy() for _ in range(7)]

    assert collapse_timetable(timetable) == expected


def test_collapse_timetable_with_space_in_the_middle():
    day = {
        0: (str(uuid4()), ("100", "А")),
        2: (str(uuid4()), ("200", "Б")),
        3: (str(uuid4()), ("300", "В")),
    }
    timetable: Timetable = [day.copy() for _ in range(7)]

    day_collapsed = [
        ("100", "А", 1),
        ("нет", "", 1),
        ("200", "Б", 1),
        ("300", "В", 1),
    ]
    expected = [day_collapsed.copy() for _ in range(7)]

    assert collapse_timetable(timetable) == expected


def test_collapse_timetable_with_space_in_the_beginning():
    day = {
        1: (str(uuid4()), ("100", "А")),
        2: (str(uuid4()), ("200", "Б")),
        3: (str(uuid4()), ("300", "В")),
    }
    timetable: Timetable = [day.copy() for _ in range(7)]

    day_collapsed = [
        ("нет", "", 1),
        ("100", "А", 1),
        ("200", "Б", 1),
        ("300", "В", 1),
    ]
    expected = [day_collapsed.copy() for _ in range(7)]

    assert collapse_timetable(timetable) == expected


def test_collapse_timetable_empty():
    timetable: Timetable = [{} for _ in range(7)]

    day_collapsed = [("", "", 1)] * 3
    expected = [day_collapsed.copy() for _ in range(7)]

    assert collapse_timetable(timetable) == expected
