.. SPDX-FileCopyrightText: 2026 Matvey Vyalkov
.. SPDX-License-Identifier: CC0-1.0

Быстрый старт
=============

В этом разделе говорится о том, как установить библиотеку и быстро получить
первый результат.


Установка
---------

Чтобы установить последний опубликованный релиз, выполните:

.. prompt:: bash

   pip install ecp.egov66.ru-timetable

Чтобы установить из Git-репозитория, выполните:

.. prompt:: bash

   pip install git+https://altlinux.space/acme-corp/ecp.egov66.ru-timetable


Конфигурация
------------

Прежде чем начать, необходимо указать несколько обязательных параметров: это
адрес сайта личного кабинета (например, ``https://t00.ecp.egov66.ru``) и
cookie-файлы для авторизации:

* ``edinyi_lk_session`` — это временный ключ сеанса личного кабинета, который
  обновляется раз в сутки (библиотека делает это за вас).
* ``remember_web_<...>`` — это постоянный ключ сеанса, который не меняется.

.. note::
   Не знаете, как вытащить cookie-файлы из браузера? Вот инструкции для
   `Chrome`_ и `Firefox`_.

.. _Chrome: https://developer.chrome.com/docs/devtools/application/cookies
.. _Firefox: https://firefox-source-docs.mozilla.org/devtools-user/storage_inspector/index.html

Создайте файл :file:`settings.json` следующего содержания, подставив в него
свои значения:

.. code-block:: json

   {
     "instance": "https://<...>.ecp.egov66.ru",
     "cookies": [
       "edinyi_lk_session": "<...>",
       "remember_web_<...>": "<...>"
     ]
   }

.. note::
   Список всех настроек, которые поддерживает библиотека, вы можете найти в
   документации тип :class:`Settings
   <egov66_timetable.types.settings.Settings>`.


CLI-интерфейс
-------------

Вместе с библиотекой идет утилита. Воспользуемся ей, чтобы получить расписание
для группы 101 на следующую неделю и вывести его в HTML-файл:

.. prompt:: bash

   ecp-egov66-timetable 101 1

* *Первый аргумент* — это номер группы, каким он указан в личном кабинете.
* *Второй аргумент (необязательный)* — это смещение относительно текущей недели.
  Параметр принимает только целочисленные значения.

После успешного завершения утилита перезапишет файл :file:`settings.json` с
новыми значениями cookie.
