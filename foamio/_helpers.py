from __future__ import annotations

import argparse
import linecache
import shutil
from pathlib import Path


def _count_columns(filepath: Path | str, sep: str, line_no: int = 1) -> int:
    """Count columns in a data-file by counting separators in a line."""

    line = linecache.getline(str(Path(filepath)), line_no)
    return line.count(sep) + line.count("\n")


def remove(tree: Path) -> None:
    if tree.is_file():
        tree.unlink()
        return

    shutil.rmtree(tree)


def require_range(nmin, nmax):
    class RequiredLength(argparse.Action):
        def __call__(self, parser, args, values, option_string=None):
            if not nmin <= len(values) <= nmax:
                raise argparse.ArgumentTypeError(
                    f'argument "{self.dest}" requires '
                    f"between {nmin} and {nmax} arguments"
                )
            setattr(args, self.dest, values)

    return RequiredLength
