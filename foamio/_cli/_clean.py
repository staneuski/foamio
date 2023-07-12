from __future__ import annotations

import argparse
import concurrent.futures
import logging
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from foamio._common import REGEX_DIGIT
from foamio._helpers import remove

@dataclass
class Interval:
    lhs: float = 0
    rhs: float = np.inf

    _lhs_less = np.less_equal
    _rhs_less = np.less

    def __post_init__(self):
        self.lhs = (0 if not isinstance(self.lhs, float) and self.lhs == ''
                    else float(self.lhs))
        self.rhs = (np.inf if not isinstance(self.rhs, float)
                    and self.rhs == '' else float(self.rhs))

    def is_in(self, value: float) -> bool:
        return self._lhs_less(self.lhs, value) and self._rhs_less(
            value, self.rhs)


def add_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        'indir',
        metavar='DIR',
        type=Path,
        help='directory with time-step folders to be clean',
    )
    parser.add_argument(
        '--interval',
        '-i',
        type=str,
        help='half-interval of time-step folders (e.g. "1e-5:0.01" or "1e-5:")',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
    )
    parser.add_argument(
        '--exclude-first',
        action='store_true',
        help='''exclude the first time-step folder from the interval
                (the 0/ time-step folder is included by default - use this flag
                not to delete initial conditions)''',
    )
    parser.add_argument(
        '--include-last',
        action='store_true',
        help='include the last time-step folder in the interval',
    )


def __validate(args: argparse.Namespace) -> None:
    args.indir = args.indir.resolve()
    args.interval = (Interval(*args.interval.split(':'))
                     if not args.interval is None else Interval())

    if args.exclude_first:
        args.interval._lhs_less = np.less
    if args.include_last:
        args.interval._rhs_less = np.less_equal


def clean(args: argparse.Namespace) -> None:
    __validate(args)

    timesteps = [
        d for d in args.indir.rglob('*')
        if d.is_dir() and re.match(REGEX_DIGIT, d.name)
    ]

    if args.dry_run:
        timesteps = sorted(
            set([
                time for timestep in timesteps
                if args.interval.is_in(time := float(timestep.name))
            ]))
        logging.info(
            f'{len(timesteps)} timesteps are to deletion ({timesteps=})')
        return

    with concurrent.futures.ProcessPoolExecutor() as e:
        logging.info(
            f'recursive deletion of {len(timesteps)} timestep directories…')

        future_to_dir = {
            e.submit(remove, timestep): timestep
            for timestep in timesteps
            if args.interval.is_in(float(timestep.name))
        }

        for future in concurrent.futures.as_completed(future_to_dir):
            timestep = future_to_dir[future]
            try:
                future.result()
            except Exception as exception:
                logging.warning(
                    f'deletion of {timestep} raised an {exception=}')
            logging.debug(f'{timestep} deleted')

        logging.info(f'found timesteps have been deleted in {args.indir}')
