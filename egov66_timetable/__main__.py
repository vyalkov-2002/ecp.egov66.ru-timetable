# SPDX-License-Identifier: WTFPL
# SPDX-FileCopyrightText: 2025 Matvey Vyalkov
# No warranty

import sys

from egov66_timetable import write_timetable
from egov66_timetable.utils import (
    read_settings,
    write_settings,
)


def main() -> None:
    args = sys.argv[1:]
    if not 1 <= len(args) <= 2:
        print("usage: ecp-egov66-timetable group [offset]", file=sys.stderr)
        sys.exit(1)

    group = args[0]
    offset = int(args[1]) if len(args) == 2 else 0

    settings = read_settings()
    write_timetable(group, offset=offset, settings=settings)
    write_settings(settings)


if __name__ == "__main__":
    main()
