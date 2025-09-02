import argparse
import linecache
import shutil
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class Interval:
    lhs: float = 0
    rhs: float = np.inf

    lhs_less = np.less_equal
    rhs_less = np.less

    def __post_init__(self):
        self.lhs = (
            0 if not isinstance(self.lhs, float) and self.lhs == "" else float(self.lhs)
        )
        self.rhs = (
            np.inf
            if not isinstance(self.rhs, float) and self.rhs == ""
            else float(self.rhs)
        )

    def is_in(self, value: float) -> bool:
        return self.lhs_less(self.lhs, value) and self.rhs_less(value, self.rhs)


def _count_columns(filepath: Path | str, sep: str, line_no: int = 1) -> int:
    """Count columns in a data-file by counting separators in a line."""

    line = linecache.getline(str(Path(filepath)), line_no)
    return line.count(sep) + line.count("\n")


def remove(tree: Path) -> None:
    if tree.is_file():
        tree.unlink()
        return

    shutil.rmtree(tree)


def require_range(n_min, n_max):
    class RequiredLength(argparse.Action):
        def __call__(self, parser, args, values, option_string=None):
            if not n_min <= len(values) <= n_max:
                raise argparse.ArgumentTypeError(
                    f"argument '{self.dest}' requires "
                    f"between {n_min} and {n_max} arguments"
                )
            setattr(args, self.dest, values)

    return RequiredLength
