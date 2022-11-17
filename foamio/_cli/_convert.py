from __future__ import annotations

import argparse
import concurrent.futures
import xml.etree.cElementTree as et
from pathlib import Path

import pyvista

SUPPORTED_SUFFIXES = dict(
    reader={'.vtk'},
    writer={'.pvd'},
)


def add_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        'loc',
        metavar='DIR',
        type=Path,
        help='directory with time-step folders to be read from',
    )
    parser.add_argument(
        'ofile',
        metavar='PVD',
        type=Path,
        help='pvd file to generate',
    )
    parser.add_argument(
        '--pattern',
        '-p',
        type=str,
        default='*.vtk',
        help="glob pattern to match vtk files (e.g.: '*_cutPlane.vtk')",
    )


def __validate(args: argparse.Namespace) -> None:
    args.loc = args.loc.resolve()
    args.ofile = args.ofile.resolve()


def __convert_to_vtu(loc: Path, pattern: str = '*.vtk') -> None:
    """Convert all .vtk to .vtu files in directory recursively.

    Args:
        loc (Path): Directory storing .vtk-files.
        pattern (str, optional): Glob pattern to match .vtk-files.
        Defaults to '*.vtk'.
    """

    with concurrent.futures.ProcessPoolExecutor() as e:
        for vtk_file in loc.rglob(pattern):
            # Convertion could be done with meshio directly but it does not
            # support reading VTK PolyData yet.
            e.submit(
                pyvista.save_meshio,
                vtk_file.with_suffix('.vtu'),
                pyvista.read(vtk_file),
            )


def __generate_pvd(loc: Path,
                   output_file: Path,
                   pattern: str = '*.vtu') -> None:
    """Create ParaView .pvd-file from directory with time-step folders.

    Args:
        loc (Path): Directory storing time-step folders with .vtu-files.
        output_file (Path): .pvd-file to generate.
        pattern (str, optional): Glob pattern to match .vtk-files.
        Defaults to '*.vtk'.
    """

    root = et.Element('VTKFile',
                      type='Collection',
                      byte_order='LittleEndian',
                      compressor='vtkZLibDataCompressor')

    # Iterate over .vtu-files
    cellection = et.SubElement(root, 'Collection')
    for vtu_file in sorted(loc.rglob(pattern)):
        et.SubElement(
            cellection,
            'DataSet',
            timestep=vtu_file.parent.name,
            group='',
            part='0',
            file=str(vtu_file.relative_to(output_file.parent)),
        )

    tree = et.ElementTree(root)
    tree.write(output_file)


def convert(args: argparse.Namespace) -> None:
    __validate(args)
    # Convert '.vtk' suffix to '.vtu' in pattern
    # https://stackoverflow.com/questions/2556108/rreplace-how-to-replace-the-last-occurrence-of-an-expression-in-a-string
    pattern = '.vtu'.join(args.pattern.rsplit('.vtk', 1))

    __convert_to_vtu(args.loc, pattern=args.pattern)
    __generate_pvd(args.loc, args.ofile, pattern=pattern)
