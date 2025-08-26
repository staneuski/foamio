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
        help="column indices to describe",
    )
    parser.add_argument(
        "--usenth",
        "-un",
        type=int,
        default=None,
        help="read every n-th row in .dat-file",
    )

    parser.add_argument(
        "--filter",
        "-f",
        type=str,
        default=None,
        help="filter columns by regex pattern after reading",
    )


def __validate(args: argparse.Namespace) -> None:
    args.loc = args.loc.resolve()

    if args.usecols is not None:
        args.usecols = [int(c) + 1 for c in args.usecols]


def describe(args: argparse.Namespace) -> None:
    __validate(args)

    logging.info("reading %s", args.loc)
    df = read(args.loc, usecols=args.usecols, usenth=args.usenth)
    if args.filter is not None:
        df = df.filter(
            regex=args.filter,
            axis="columns",
        )
    stat = df.describe()
    stat.loc["last"] = df.iloc[-1]

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
    logging.info("saved to %s", fname)
