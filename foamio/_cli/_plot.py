from __future__ import annotations

import argparse
import logging
from pathlib import Path

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import pandas as pd

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
        help="plots data (y-axis) on log scale - for"
        ' "residuals.dat" sets automatically',
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

    titles = __get_titles(args.loc)
    args.title = titles[0] if args.title is None else args.title
    args.subtitle = titles[1] if args.subtitle is None else args.subtitle


def __get_titles(loc: Path) -> tuple[str, str]:
    """Get OpenFOAM-case name and post-processing function name if the .dat
    file is located in postProcessing/ folder.

    Args:
        loc (Path): .dat-file path

    Returns:
        tuple[str, str]: title, subtitle
    """

    if not "postProcessing" in str(loc.parts):
        return "", ""

    folders = list(loc.parts)
    ind = folders.index("postProcessing")
    return (folders[ind - 1], folders[ind + 1])


def plot(args: argparse.Namespace) -> None:
    __validate(args)

    def __plot(ax, args) -> pd.DataFrame:
        df = read(args.loc, usecols=args.usecols, usenth=args.usenth)
        df.plot(
            ax=ax,
            title=args.subtitle,
            logy=args.logscale,
            grid=True,
        )
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
            fig=fig,
            func=animate,
            save_count=1,
            interval=1e3 * args.refresh,
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
