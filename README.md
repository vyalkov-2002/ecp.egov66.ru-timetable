<!--
SPDX-FileCopyrightText: 2025-2026 Matvey Vyalkov

SPDX-License-Identifier: CC0-1.0
-->

# Расписание колледжей и техникумов Свердловской области

![Build Status](https://altlinux.space/acme-corp/ecp.egov66.ru-timetable/badges/workflows/test.yml/badge.svg)

## Что это?

Это Python-библиотека для получения расписания студента и преподавателя из личного кабинета [ГИС СО "ЕЦП"](https://lk.ecp.egov66.ru/),
написанная путём нехитрого реверс-инжиниринга :)

На этой библиотеке основана связка [egov66-timetable-chatbot][a1] + [iat-timetable][a2] + [iat-tablo][a3],
с помощью которой расписание [Ирбитского аграрно-технологического техникума][b1] можно посмотреть [на сайте][b2], [в мессенджерах][b3] и на листе бумаги.

[a1]: https://altlinux.space/acme-corp/egov66-timetable-chatbot
[a2]: https://altlinux.space/acme-corp/iat-timetable
[a3]: https://altlinux.space/acme-corp/iat-tablo
[b1]: https://иат.ирбитский-район.рф
[b2]: https://acme-corp.altlinux.team
[b3]: https://t.me/timetable66_bot

## Быстрый старт

1. Зайдите в личный кабинет и вытащите куки `edinyi_lk_session` и `remember_web_<...>`.
2. Создайте файл settings.json следующего содержания (подставьте свои значения):

   ```json
   {
     "instance": "https://<...>.ecp.egov66.ru",
     "cookies": [
       "edinyi_lk_session": "<...>",
       "remember_web_<...>": "<...>"
     ]
   }
   ```
3. Можно запускать!

   ```
   $ uv run ecp-egov66-timetable 101 1
   ```
Программа получит расписание для группы 101 на следующую неделю и запишет его в статический файл HTML.

## См. также

Похожий как две капли воды сайт с расписанием, оказывается, есть у образовательного центра "Сириус" в Сочи.
Для него мне удалось найти несколько аналогичных проектов:

* [pyrinium](https://github.com/PerovXP/pyrinium)
* [sirinium](https://github.com/PerovXP/sirinium)
* [new-schedule](https://github.com/nnqnn/new-schedule)

## Лицензия

Эта библиотека распространяется под лицензией EUPL 1.2,
условия которой аналогичны GNU AGPL v3.
По сравнению с AGPL текст этой лицензии более короткий и понятный,
поэтому вы можете без особого труда прочитать его полностью.
Вы можете свободно использовать, изменять и распространять эту библиотеку при условии,
что модифицированный исходный код будет доступен пользователям под такой же лицензией.
