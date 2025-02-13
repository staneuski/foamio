from __future__ import annotations

import argparse
import logging
from pathlib import Path

from foamio.dat import read


def add_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "loc",
        type=Path,
        help=".dat-file path or directory with .dat-files",
    )
    parser.add_argument(
        "--background",
        "-b",
        action="store_true",
        help="open in background mode, i.e. save as .csv-file alongside",
    )

    parser.add_argument(
        "--usecols",
        "-uc",
        type=int,
        nargs="+",
        help="column indices to plot (index starting from 1)",
    )
    parser.add_argument(
        "--usenth",
        "-un",
        type=int,
        default=None,
        help="read every n-th row in .dat-file",
    )


def __validate(args: argparse.Namespace) -> None:
    args.loc = args.loc.resolve()


def describe(args: argparse.Namespace) -> None:
    __validate(args)

    logging.info(f"reading {args.loc}")
    stat = read(args.loc, usecols=args.usecols, use_nth=args.usenth).describe()

    if not args.background:
        print(stat)
        return

    # Save to path with .csv suffix either for folder name
    # (e.g. to  functionObject folder name) or just replace .dat suffix with .csv
    fname = (
        args.loc.with_suffix(args.loc.suffix + ".csv")
        if args.loc.is_dir()
        else args.loc.with_suffix(".csv")
    )
    stat.to_csv(fname)
    logging.info(f"saved to {fname}")
