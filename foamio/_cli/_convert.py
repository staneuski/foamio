from __future__ import annotations

import argparse
from pathlib import Path

import vtk

SUPPORTED_SUFFIXES = dict(
    reader={'.vtk'},
    writer={'.vtp'},
)


def add_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        'infile',
        metavar='DIR',
        type=Path,
        help='mesh file to be read from',
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


def __validate(args: argparse.Namespace) -> None:
    args.infile = args.infile.resolve()
    args.outfile = (args.infile.with_suffix('.vtp')
                    if args.outfile is None else args.outfile.resolve())


def convert(args: argparse.Namespace) -> None:
    __validate(args)

    reader = vtk.vtkPolyDataReader()
    reader.SetFileName(args.infile)

    writer = vtk.vtkXMLPolyDataWriter()
    writer.SetFileName(args.outfile)
    writer.SetInputConnection(reader.GetOutputPort())
    writer.Update()

    if not args.keep:
        args.infile.unlink()
