from __future__ import annotations

import argparse
import concurrent.futures
import logging
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from foamio._common import NUMBER_PATTERN
from foamio._helpers import remove, require_range


@dataclass
class Interval:
    lhs: float = 0
    rhs: float = np.inf

    _lhs_less = np.less_equal
    _rhs_less = np.less

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
        return self._lhs_less(self.lhs, value) and self._rhs_less(value, self.rhs)


def add_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "indir",
        metavar="DIR",
        type=Path,
        help="directory with time-step folders to be clean",
    )
    parser.add_argument(
        "--interval",
        "-i",
        type=str,
        help="half-interval of time-step folders (e.g. '1e-5:0.01' or '1e-5:')",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
    )
    parser.add_argument(
        "--exclude-first",
        action="store_true",
        help="""exclude the first time-step folder from the interval
                (the 0/ time-step folder is included by default - use this flag not to
                delete initial conditions)""",
    )
    parser.add_argument(
        "--include-last",
        action="store_true",
        help="include the last time-step folder in the interval",
    )
    parser.add_argument(
        "--keep",
        type=float,
        nargs="+",
        default=None,
        action=require_range(3, 3),
        help="""keep time-step folders based on START STOP INTERVAL range
                (args to numpy.arange)""",
    )


def __validate(args: argparse.Namespace) -> None:
    args.indir = args.indir.resolve()
    args.interval = (
        Interval(*args.interval.split(":")) if not args.interval is None else Interval()
    )

    if args.exclude_first:
        args.interval._lhs_less = np.less
    if args.include_last:
        args.interval._rhs_less = np.less_equal
    args.keep = np.arange(*args.keep) if not args.keep is None else np.array([])
    # logging.debug(f"excluding list: {sorted(set(args.keep))}")


def clean(args: argparse.Namespace) -> None:
    __validate(args)

    logging.debug(f"searching time-steps in {args.indir}…")
    timesteps: list[Path] = [
        d
        for d in args.indir.rglob("*")
        if d.is_dir()
        and re.match(NUMBER_PATTERN, d.name)
        and args.interval.is_in(time := float(d.name))
        and not np.any(np.isclose(time, args.keep))
    ]

    if args.dry_run:
        unique_times = set([timesteps.name for timesteps in timesteps])
        unique_info = (
            f", {len(unique_times)} of them are unique"
            if len(unique_times) != len(timesteps)
            else ""
        )
        logging.info(
            f"{len(timesteps)} time-steps are to deletion"
            f"{unique_info}:\n{sorted(unique_times)}"
        )
        return

    with concurrent.futures.ProcessPoolExecutor() as e:
        logging.info(f"recursive deletion of {len(timesteps)} time-step directories…")

        future_to_dir = {e.submit(remove, timestep): timestep for timestep in timesteps}
        for future in concurrent.futures.as_completed(future_to_dir):
            timestep = future_to_dir[future]
            try:
                future.result()
            except Exception as exception:
                logging.warning(f"deletion of {timestep} raised an {exception=}")
            logging.debug(f"{timestep} deleted")

        logging.info(f"found timesteps have been deleted in {args.indir}")
