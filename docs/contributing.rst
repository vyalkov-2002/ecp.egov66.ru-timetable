.. SPDX-FileCopyrightText: 2026 Matvey Vyalkov
.. SPDX-License-Identifier: CC0-1.0

Внести вклад
============

Любой вклад приветствуется, будь то код, тесты, документация, добрый совет или
донат :)


Работа с кодом
--------------

Клонируйте репозиторий:

.. prompt:: bash

   git clone https://altlinux.space/acme-corp/ecp.egov66.ru-timetable

Внесите свои изменения и запустите тесты с линтерами:

.. prompt:: bash

   tox run

Какого-то жесткого стиля кода нет, просто старайтесь придерживаться стандарта
`PEP 8`_ и не игнорируйте обнаруженные линтером проблемы.

.. _PEP 8: https://peps.python.org/pep-0008/

Сделайте коммит. Чем подробнее сообщение коммита, тем лучше. Атомарные коммиты
предпочтительны. Если необходимо, используйте `git rebase`_, чтобы переписать
историю коммитов.

.. _git rebase: https://git-rebase.io/

Наконец, создайте запрос на слияние в Forgejo. Кстати, Forgejo поддерживает
`AGit-Workflow`_ без создания форка.

.. _`AGit-Workflow`: https://forgejo.org/docs/latest/user/agit-support/

Если вы не хотите регистрироваться на ALT Linux Space, отправьте патчи по почте
с помощью `git send-email`_:

.. prompt:: bash

   git send-email --to=vyalkov.2002@mail.ru origin/master

.. _git send-email: https://git-send-email.io/
