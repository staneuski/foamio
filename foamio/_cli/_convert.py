from __future__ import annotations

import argparse
import concurrent.futures
import logging
from pathlib import Path

import vtk

from foamio._common import LOGGING_FORMAT

SUPPORTED_SUFFIXES = dict(
    reader={'.vtk'},
    writer={'.vtp'},
)


def add_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        'inloc',
        type=Path,
        help='mesh file or directory to be read from',
    )
    parser.add_argument(
        '-o',
        '--outfile',
        type=Path,
        default=None,
        help='mesh file to be written to',
    )
    parser.add_argument(
        '-k',
        '--keep',
        action='store_true',
        help='keep input file',
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='verbose',
    )


def __validate(args: argparse.Namespace) -> None:
    args.inloc = args.inloc.resolve()
    args.outfile = (args.inloc.with_suffix('.vtp')
                    if args.outfile is None else args.outfile.resolve())


def __convert(infile: Path, outfile: Path, keep: bool = False) -> None:

    logging.debug(f'reading {infile}')
    reader = vtk.vtkPolyDataReader()
    reader.SetFileName(infile)

    logging.debug(f'writing {outfile}')
    writer = vtk.vtkXMLPolyDataWriter()
    writer.SetFileName(outfile)
    writer.SetInputConnection(reader.GetOutputPort())
    writer.Update()

    if not keep:
        logging.debug(f'deleting {infile}')
        infile.unlink()


def convert(args: argparse.Namespace) -> None:
    __validate(args)

    if args.inloc.is_file():
        logging.debug(f'direct convertion')
        __convert(infile := args.inloc, args.outfile, args.keep)
        logging.info(f'{infile} converted')
        return

    logging.debug(f'recursive convertion')
    with concurrent.futures.ProcessPoolExecutor() as e:
        future_to_infile = {
            e.submit(
                __convert,
                infile,
                infile.with_suffix('.vtp'),
                args.keep,
            ): infile
            for infile in args.inloc.rglob('*.vtk')
        }

        for future in concurrent.futures.as_completed(future_to_infile):
            infile = future_to_infile[future]
            try:
                future.result()
            except Exception as exception:
                logging.warning(f'conversion of {infile} raised an {exception=}')
            else:
                logging.info(f'{infile} converted')