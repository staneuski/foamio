import argparse
from sys import version_info

from foamio.__about__ import __version__
from foamio._cli import _clean, _convert, _describe, _generate, _plot
import logging
from foamio._common import LOGGING_FORMAT


def main(argv=None) -> argparse.Namespace:
    parent_parser = argparse.ArgumentParser(
        description='OpenFOAM input/output tools and routines.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=f'foamio v{__version__}'
        f' [Python {version_info.major}.{version_info.minor}.{version_info.micro}]'
        '\nCopyright (c) 2021-2023 Stanislau Stasheuski',
    )

    parent_parser.add_argument(
        '-v',
        '--verbose',
        help='output information',
        action='store_const',
        dest='loglevel',
        const=logging.INFO,
    )
    parent_parser.add_argument(
        '-d',
        '--debug',
        help='print debug statements',
        action='store_const',
        dest='loglevel',
        const=logging.DEBUG,
        default=logging.WARNING,
    )

    subparsers = parent_parser.add_subparsers(title='subcommands',
                                              dest='command',
                                              required=True)

    help_tail = 'OpenFOAM/ParaView files'

    clean = dict(aliases=['rm'], help=f'Clean {help_tail}')
    parser = subparsers.add_parser('clean', **clean)
    _clean.add_args(parser)
    parser.set_defaults(func=_clean.clean)

    convert = dict(aliases=['c'], help=f'Convert {help_tail}')
    parser = subparsers.add_parser('convert', **convert)
    _convert.add_args(parser)
    parser.set_defaults(func=_convert.convert)

    generate = dict(aliases=['g'], help=f'Generate {help_tail}')
    parser = subparsers.add_parser('generate', **generate)
    _generate.add_args(parser)
    parser.set_defaults(func=_generate.generate)

    describe = dict(aliases=['d'], help=f'Describe {help_tail}')
    parser = subparsers.add_parser('describe', **describe)
    _describe.add_args(parser)
    parser.set_defaults(func=_describe.describe)

    plot = dict(aliases=['p'], help=f'Plot {help_tail}')
    parser = subparsers.add_parser('plot', **plot)
    _plot.add_args(parser)
    parser.set_defaults(func=_plot.plot)

    args = parent_parser.parse_args(argv)
    logging.basicConfig(level=args.loglevel, format=LOGGING_FORMAT)

    return args.func(args)
