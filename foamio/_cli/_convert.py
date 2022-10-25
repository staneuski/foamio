from __future__ import annotations

import argparse
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
    # parser.add_argument(
    #     '--input-format',
    #     '--ifmt',
    #     '-i',
    #     type=str,
    #     default='vtk',
    #     choices=[s.replace('.', '') for s in SUPPORTED_SUFFIXES['reader']],
    #     help='output file format',
    # )
    # parser.add_argument(
    #     '--output-format',
    #     '--ofmt',
    #     '-o',
    #     type=str,
    #     default='pvd',
    #     choices=[s.replace('.', '') for s in SUPPORTED_SUFFIXES['writer']],
    #     help='output file format',
    # )

def __validate(args: argparse.Namespace) -> None:
    args.loc = args.loc.resolve()


def __convert_to_vtu(loc: Path) -> None:
    """Convert all .vtk to .vtu files in directory recursively.

    Args:
        loc (Path): Directory storing .vtk-files.
    """

    for vtk_file in loc.rglob('*.vtk'):
        # Convertion could be done with meshio directly but it does not
        # support reading VTK PolyData.
        pyvista.save_meshio(vtk_file.with_suffix('.vtu'),
                            pyvista.read(vtk_file))


def __generate_pvd(loc: Path) -> Path:
    """Create ParaView .pvd-file from directory with time-step folders.

    Args:
        loc (Path): Directory storing time-step folders with .vtu-files.

    Returns:
        Path: generated XML-based ParaView .pvd-file
    """

    root = et.Element('VTKFile',
                      type='Collection',
                      byte_order='LittleEndian',
                      compressor='vtkZLibDataCompressor')

    # Iterate over .vtu-files
    cellection = et.SubElement(root, 'Collection')
    for vtu_file in sorted(loc.rglob('*.vtu')):
        et.SubElement(
            cellection,
            'DataSet',
            timestep=vtu_file.parent.name,
            group='',
            part='0',
            file=str(vtu_file.relative_to(loc.parent)),
        )

    tree = et.ElementTree(root)
    tree.write(pvd_file := loc.with_suffix('.pvd'))
    return pvd_file


def convert(args: argparse.Namespace) -> None:
    __validate(args)

    __convert_to_vtu(args.loc)
    __generate_pvd(args.loc)
