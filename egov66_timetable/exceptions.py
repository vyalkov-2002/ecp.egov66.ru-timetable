# SPDX-License-Identifier: EUPL-1.2
# SPDX-FileCopyrightText: 2025 Matvey Vyalkov
# No warranty

"""
Ошибки и исключения.
"""


class SessionExpired(Exception):
    """
    Эта ошибка означает, что сеанс завершен и нужно получить новый cookie-файл
    edinyi_lk_session.
    """


class CSRFTokenNotFound(Exception):
    """
    Эта ошибка означает, что на странице не удалось найти CSRF-токен.
    """


class InitialDataNotFound(Exception):
    """
    Эта ошибка означает, что на странице не удалось найти начальные данные.
    """
