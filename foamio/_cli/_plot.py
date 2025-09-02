import argparse
import logging
from pathlib import Path

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from foamio._helpers import Interval
from foamio.dat import read


def add_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "loc",
        metavar="FILE_OR_DIR",
        type=Path,
        help=".dat-file path or directory with .dat-files.",
    )
    parser.add_argument(
        "--title",
        "-t",
        type=str,
        help="graph title - OpenFOAM case name by default",
    )
    parser.add_argument(
        "--subtitle",
        "-st",
        type=str,
        help="graph subtitle - .dat file name without extension by default",
    )
    parser.add_argument(
        "--logscale",
        "-l",
        action="store_true",
        help="plots data (y-axis) on log scale",
    )
    parser.add_argument(
        "--refresh",
        "-r",
        type=int,
        default=10,
        help="refreshes display every <time> sec",
    )
    parser.add_argument(
        "--background",
        "-b",
        action="store_true",
        help="open in background mode, i.e. save .svg-plot alongside",
    )

    parser.add_argument(
        "--usecols",
        "-uc",
        type=int,
        nargs="+",
        help="column indices to plot (1-based indexing)",
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
    parser.add_argument(
        "--index",
        type=str,
        help="x-interval (e.g. '1e-5:0.01' or '1e-5:')",
    )
    parser.add_argument(
        "--range",
        type=str,
        help="y-interval (e.g. '1e-5:0.01' or '1e-5:')",
    )


def __validate(args: argparse.Namespace) -> None:
    args.loc = args.loc.resolve()

    titles = __get_titles(args.loc)
    args.title = titles[0] if args.title is None else args.title
    args.subtitle = titles[1] if args.subtitle is None else args.subtitle

    if args.index is not None:
        args.index = Interval(*args.index.split(":"))
        args.index.rhs_less = np.less_equal

    if args.range is not None:
        args.range = Interval(*args.range.split(":"))
        args.range.rhs_less = np.less_equal


def __get_titles(loc: Path) -> tuple[str, str]:
    """Get OpenFOAM-case name and post-processing function name if the .dat
    file is located in postProcessing/ folder.

    Args:
        loc (Path): .dat-file path

    Returns:
        tuple[str, str]: title, subtitle
    """

    folders = list(loc.parts)
    if "postProcessing" not in folders:
        return "", ""

    ind = folders.index("postProcessing")
    return (folders[ind - 1], folders[ind + 1])


def plot(args: argparse.Namespace) -> None:
    __validate(args)

    def __plot(ax, args) -> pd.DataFrame:
        df = read(args.loc, usecols=args.usecols, usenth=args.usenth)
        if args.filter is not None:
            df = df.filter(regex=args.filter, axis="columns")
        if args.index is not None:
            df = df[df.index.map(args.index.is_in)]
        if args.range is not None:
            df = df[df.map(args.range.is_in).all(axis="columns")]
        df.plot(ax=ax, title=args.subtitle, logy=args.logscale, grid=True)
        return df

    def animate(frame: int = 0) -> None:
        ax.clear()
        logging.debug("animate frame=%d", frame)
        __plot(ax, args)

    fig = plt.figure(figsize=(10, 6))
    fig.suptitle(args.title, fontweight="bold", fontsize=16)

    logging.info(
        'animating "%s" figure with "%s" plot from %s every %ss',
        args.title,
        args.subtitle,
        args.loc,
        args.refresh,
    )
    ax = fig.add_subplot()
    df = __plot(ax, args)

    if args.refresh and not args.background:
        ani = animation.FuncAnimation(
            fig=fig, func=animate, save_count=1, interval=1e3 * args.refresh
        )
        logging.debug("animation started: %s", hasattr(ani, "_draw_was_started"))

    # plt.tight_layout()
    if args.background:
        # Append the column names to the file name, if --usecols is set
        tail = "." + "-".join(c for c in df.columns) if args.usecols else ""

        # Use the directory name with a .png-suffix, if the input is a directory.
        # Otherwise, replace the .dat-suffix with .png
        plt.savefig(
            fname := (
                args.loc.with_suffix(f"{args.loc.suffix}{tail}.png")
                if args.loc.is_dir()
                else args.loc.with_suffix(f"{tail}.png")
            )
        )
        logging.info("saved plot to %s", fname)
        return

    plt.show(block=True)
