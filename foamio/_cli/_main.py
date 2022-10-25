import argparse
from sys import version_info

from foamio.__about__ import __version__
from foamio._cli import _convert, _describe, _plot


def main(argv=None) -> argparse.Namespace:
    parent_parser = argparse.ArgumentParser(
        description='OpenFOAM input/output tools and routines.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=f'foamio v{__version__}'
        f' [Python {version_info.major}.{version_info.minor}.{version_info.micro}]'
        '\nCopyright (c) 2021-2022 Stanislau Stasheuski',
    )

    subparsers = parent_parser.add_subparsers(title='subcommands',
                                              dest='command',
                                              required=True)

    help_tail = 'OpenFOAM/ParaView files'

    convert = dict(aliases=['c'], help=f'Convert {help_tail}')
    parser = subparsers.add_parser('convert', **convert)
    _convert.add_args(parser)
    parser.set_defaults(func=_convert.convert)

    describe = dict(aliases=['d'], help=f'Describe {help_tail}')
    parser = subparsers.add_parser('describe', **describe)
    _describe.add_args(parser)
    parser.set_defaults(func=_describe.describe)

    plot = dict(aliases=['p'], help=f'Plot {help_tail}')
    parser = subparsers.add_parser('plot', **plot)
    _plot.add_args(parser)
    parser.set_defaults(func=_plot.plot)

    args = parent_parser.parse_args(argv)

    return args.func(args)
