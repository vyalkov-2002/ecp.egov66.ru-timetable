# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2025 Matvey Vyalkov
# No warranty


def case_student_with_repeats():
    day_lessons = {
        0: ("100", "А"),
        1: ("100", "А"),
        2: ("200", "Б"),
        3: ("100", "А"),
        4: ("100", "А"),
    }
    day_expected = [
        ("100", "А", 2),
        ("200", "Б", 1),
        ("100", "А", 2),
    ]

    return day_lessons, day_expected


def case_student_with_space_in_the_middle():
    day_lessons = {
        0: ("100", "А"),
        2: ("200", "Б"),
        3: ("300", "В"),
    }
    day_expected = [
        ("100", "А", 1),
        ("нет", "", 1),
        ("200", "Б", 1),
        ("300", "В", 1),
    ]

    return day_lessons, day_expected


def case_student_with_space_in_the_beginning():
    day_lessons = {
        1: ("100", "А"),
        2: ("200", "Б"),
        3: ("300", "В"),
    }
    day_expected = [
        ("нет", "", 1),
        ("100", "А", 1),
        ("200", "Б", 1),
        ("300", "В", 1),
    ]

    return day_lessons, day_expected


def case_teacher_with_overlaps():
    day_lessons = {
        0: [("111-12", "А")],
        1: [
            ("112-12", "А"),
            ("311-10", "Б"),
        ],
        2: [("111-12", "А")],
        3: [("111-12", "А")],
    }
    day_expected = [
        [("111-12", "А")],
        [
            ("112-12", "А"),
            ("311-10", "Б"),
        ],
        [("111-12", "А")],
        [("111-12", "А")],
    ]

    return day_lessons, day_expected


def case_teacher_with_space_in_the_middle():
    day_lessons = {
        0: [("111-12", "А")],
        2: [("211-11", "А")],
        3: [("311-10", "А")],
    }
    day_expected = [
        [("111-12", "А")],
        [("нет", "")],
        [("211-11", "А")],
        [("311-10", "А")],
    ]

    return day_lessons, day_expected


def case_teacher_with_space_in_the_beginning():
    day_lessons = {
        1: [("111-12", "А")],
        2: [("211-11", "А")],
        3: [("311-10", "А")],
    }
    day_expected = [
        [("нет", "")],
        [("111-12", "А")],
        [("211-11", "А")],
        [("311-10", "А")],
    ]

    return day_lessons, day_expected
