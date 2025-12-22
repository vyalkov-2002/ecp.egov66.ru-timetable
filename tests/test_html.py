# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2025 Matvey Vyalkov
# No warranty

from uuid import uuid4

from pytest_cases import parametrize_with_cases

from egov66_timetable.callbacks.html import (
    collapse_timetable,
    collapse_teacher_timetable,
)
from egov66_timetable.types import (
    Lesson,
    Timetable,
)
from egov66_timetable.utils import get_type_adapter


@parametrize_with_cases("day_lessons,day_expected", prefix="case_student_")
def test_collapse_timetable(day_lessons: dict[int, tuple[str, str]],
                            day_expected: list[tuple[str, str, int]]):
    day = {
        lesson_num: (str(uuid4()), day_lessons[lesson_num])
        for lesson_num in day_lessons
    }
    timetable = get_type_adapter(Timetable[Lesson]).validate_python(
        [day.copy() for _ in range(5)]
    )
    expected = [day_expected.copy() for _ in range(5)]

    assert collapse_timetable(timetable) == expected


def test_collapse_timetable_empty():
    timetable: Timetable[Lesson] = [{} for _ in range(5)]

    day_expected = [("", "", 1)] * 3
    expected = [day_expected.copy() for _ in range(5)]

    assert collapse_timetable(timetable) == expected


@parametrize_with_cases("day_lessons,day_expected", prefix="case_teacher_")
def test_collapse_teacher_timetable(day_lessons: dict[int, list[tuple[str, str]]],
                                    day_expected: list[list[tuple[str, str, int]]]):
    day = {
        lesson_num: [
            (str(uuid4()), event)
            for event in day_lessons[lesson_num]
        ]
        for lesson_num in day_lessons
    }
    timetable = get_type_adapter(Timetable[list[Lesson]]).validate_python(
        [day.copy() for _ in range(5)]
    )
    expected = [day_expected.copy() for _ in range(5)]

    assert collapse_teacher_timetable(timetable) == expected


def test_collapse_teacher_timetable_empty():
    timetable: Timetable[list[Lesson]] = [{} for _ in range(5)]

    day_expected = [[("", "")]] * 3
    expected = [day_expected.copy() for _ in range(5)]

    assert collapse_teacher_timetable(timetable) == expected
