import argparse
import logging
from sys import version_info

from foamio.__about__ import __version__
from foamio._cli import _clean, _describe, _plot, _tabulate
from foamio._common import LOGGING_FORMAT


def main(argv=None) -> argparse.Namespace:
    parent_parser = argparse.ArgumentParser(
        description="OpenFOAM input/output tools and routines.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=f"foamio v{__version__}"
        f" [Python {version_info.major}.{version_info.minor}.{version_info.micro}]"
        "\nCopyright (c) 2021-2025 Stanislau Stasheuski",
    )

    parent_parser.add_argument(
        "-v",
        "--verbose",
        help="output information",
        action="store_const",
        dest="loglevel",
        const=logging.INFO,
    )
    parent_parser.add_argument(
        "-d",
        "--debug",
        help="print debug statements",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
        default=logging.WARNING,
    )

    subparsers = parent_parser.add_subparsers(
        title="subcommands", dest="command", required=True
    )

    help_case = "OpenFOAM case (including postProcessing/ directory)"
    help_dat = "OpenFOAM functionObject (or directory with .dat-files)"

    clean = dict(aliases=["rm"], help=f"Clean {help_case}")
    parser = subparsers.add_parser("clean", **clean)
    _clean.add_args(parser)
    parser.set_defaults(func=_clean.clean)

    describe = dict(aliases=["d"], help=f"Describe {help_dat}")
    parser = subparsers.add_parser("describe", **describe)
    _describe.add_args(parser)
    parser.set_defaults(func=_describe.describe)

    plot = dict(aliases=["p"], help=f"Plot {help_dat}")
    parser = subparsers.add_parser("plot", **plot)
    _plot.add_args(parser)
    parser.set_defaults(func=_plot.plot)

    tabulate = dict(aliases=["t"], help=f"Create tabulated entry with CoolProp")
    parser = subparsers.add_parser("tabulate", **tabulate)
    _tabulate.add_args(parser)
    parser.set_defaults(func=_tabulate.tabulate)

    args = parent_parser.parse_args(argv)
    logging.basicConfig(level=args.loglevel, format=LOGGING_FORMAT)

    return args.func(args)
