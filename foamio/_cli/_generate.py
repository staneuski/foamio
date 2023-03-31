from __future__ import annotations

import argparse
import logging
import xml.etree.cElementTree as et
from pathlib import Path

SUPPORTED_SUFFIXES = dict(
    reader={'.vtk'},
    writer={'.pvd'},
)


def add_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        'indir',
        metavar='DIR',
        type=Path,
        help='directory with time-step folders to be read from',
    )
    parser.add_argument(
        '--outfile',
        metavar='PVD',
        type=Path,
        default=None,
        help='.pvd-file to generate (search directory name if not set)',
    )
    parser.add_argument(
        '--pattern',
        '-p',
        type=str,
        default='*.vtp',
        help="glob pattern to match VTK-files (e.g.: '*_cutPlane.vtu')",
    )


def __validate(args: argparse.Namespace) -> None:
    args.indir = args.indir.resolve()
    args.outfile = (args.indir.with_suffix(args.indir.suffix + '.pvd')
                    if args.outfile is None else args.outfile.resolve())


def __pvd(indir: Path, outfile: Path, pattern: str = '*.vtp') -> None:
    """Create ParaView .pvd-file from directory with time-step folders.

    Args:
        indir (Path): Directory storing time-step folders with .vtu-files.
        outfile (Path): .pvd-file to generate.
        pattern (str, optional): Glob pattern to match VTK-files.
        Defaults to '*.vtp'.
    """

    found_files = sorted(indir.rglob(pattern))
    logging.info(f'{len(found_files)} files matched the {pattern=} in {indir}')

    root = et.Element('VTKFile',
                      type='Collection',
                      byte_order='LittleEndian',
                      compressor='vtkZLibDataCompressor')

    # Iterate over found files
    cellection = et.SubElement(root, 'Collection')
    for found_file in found_files:
        logging.debug(f'{found_file} found')
        et.SubElement(
            cellection,
            'DataSet',
            timestep=found_file.parent.name,
            group='',
            part='0',
            file=str(found_file.relative_to(outfile.parent)),
        )

    tree = et.ElementTree(root)
    tree.write(outfile)
    logging.info(f'{outfile} generated')


def generate(args: argparse.Namespace) -> None:
    __validate(args)
    __pvd(args.indir, args.outfile, pattern=args.pattern)
