from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.animation as animation
import matplotlib.pyplot as plt
from foamio.dat import read


def add_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        'loc',
        metavar='FILE_OR_DIR',
        type=Path,
        help='.dat-file path or directory with .dat-files.',
    )
    parser.add_argument(
        '--usecols',
        '-uc',
        type=int,
        nargs='+',
        help='column indices (using header in .dat-file)',
    )

    parser.add_argument(
        '--usecols',
        '-uc',
        type=int,
        nargs='+',
        help='column indices to plot (index starting from 1)',
    )
    parser.add_argument(
        '--usenth',
        '-un',
        type=int,
        default=None,
        help='read every n-th row in .dat-file',
    )


def __validate(args: argparse.Namespace) -> None:
    args.loc = args.loc.resolve()

    titles = __get_titles(args.loc)
    args.title = titles[0] if args.title is None else args.title
    args.subtitle = titles[1] if args.subtitle is None else args.subtitle

    args.logscale = args.logscale or 'residuals' in str(args.loc)



def describe(args: argparse.Namespace) -> None:
    __validate(args)

    print(read(args.loc, usecols=args.usecols, use_nth=args.usenth).describe())
