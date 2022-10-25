from __future__ import annotations

import linecache
from pathlib import Path


def _count_columns(filepath: Path | str, sep: str, line_no: int = 1) -> int:
    """Count columns in a data-file by counting separators in a line."""

    line = linecache.getline(str(Path(filepath)), line_no)
    return line.count(sep) + line.count('\n')


def read():
    pass
