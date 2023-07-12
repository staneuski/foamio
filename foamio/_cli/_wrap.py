from __future__ import annotations

import argparse
import concurrent.futures
import itertools
import logging
import re
import tarfile
from collections.abc import Iterable
from pathlib import Path

from foamio._helpers import remove

LOGFILES = r"(^(log|err|out)\..*|.*\.(log|err|out))"


def add_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        'inloc',
        metavar='FOAM_CASE',
        type=Path,
        help='OpenFOAM case directory',
    )
    parser.add_argument(
        '-k',
        '--keep',
        action='store_true',
        help='keep input files',
    )
    parser.add_argument(
        '--no-mesh',
        action='store_true',
        help='do not wrap polyMesh directories',
    )
    parser.add_argument(
        '--no-times',
        action='store_true',
        help='do not wrap times &/or processor directories',
    )
    parser.add_argument(
        '--no-logs',
        action='store_true',
        help='do not wrap log-files',
    )
    parser.add_argument(
        '--no-fnobj',
        action='store_true',
        help='do not wrap function objects',
    )


def __validate(args: argparse.Namespace) -> None:
    args.inloc = args.inloc.resolve()


def __wrap(infiles: Iterable, outfile: Path, keep: bool = False) -> Path:
    with tarfile.open(outfile, 'w') as tar:
        for infile in infiles:
            tar.add(infile, arcname=infile.name)
            if not keep:
                remove(infile)
        return outfile


def wrap(args: argparse.Namespace) -> None:
    __validate(args)

    with concurrent.futures.ProcessPoolExecutor() as e:

        future_to_outfile = {}

        if not args.no_mesh:
            logging.info(f'wrapping mesh…')
            outfile = Path(args.inloc, 'mesh.tar')
            future_to_outfile[e.submit(
                __wrap,
                list(Path(args.inloc, 'constant').rglob('polyMesh')),
                outfile,
                args.keep,
            )] = outfile

        if not args.no_times:
            logging.info(f'wrapping time-steps…')
            outfile = Path(args.inloc, 'times.tar')
            future_to_outfile[e.submit(
                __wrap,
                [
                    # `time` (reconstructed) or `processor` (decomposed)
                    timedir for timedir in itertools.chain(
                        args.inloc.glob('[0-9]*/'),
                        args.inloc.glob('processor*/'))
                    if timedir.suffix != '.orig' and timedir.name != '0'
                ],
                outfile,
                args.keep,
            )] = outfile

        if not args.no_logs:
            logging.info(f'wrapping logs…')
            outfile = Path(args.inloc, 'logs.tar')
            future_to_outfile[e.submit(
                __wrap,
                [
                    log for log in args.inloc.glob('*')
                    if re.match(LOGFILES, log.name) and log.is_file()
                ],
                outfile,
                args.keep,
            )] = outfile

        if not args.no_fnobj:
            logging.info(f'wrapping function objects…')
            future_to_outfile.update({
                e.submit(
                    __wrap,
                    [fn_obj],
                    fn_obj.with_suffix(fn_obj.suffix + '.tar'),
                    args.keep,
                ):
                fn_obj
                for fn_obj in args.inloc.glob('postProcessing/*/')
            })

        if not future_to_outfile:
            logging.warning(f'nothing has been wrapped in {args.inloc}: '
                            'either case is clean or arguments are too tight')
            return

        for future in concurrent.futures.as_completed(future_to_outfile):
            outfile = future_to_outfile[future]
            try:
                future.result()
            except Exception as exception:
                logging.warning(
                    f'wrapping to {outfile} raised an {exception=}')
            logging.debug(f'{outfile} is wrapped')

    logging.info(f'case {args.inloc} has been wrapped')
