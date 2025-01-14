from __future__ import annotations

import argparse
import json
import logging
import xml.etree.cElementTree as et
from pathlib import Path

SUPPORTED_SUFFIXES = dict(
    reader={".vtk", ".vtp", ".vtu"},
    writer={".pvd", ".series"},
)


def add_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "indir",
        metavar="DIR",
        type=Path,
        help="directory with time-step folders to be read from",
    )
    parser.add_argument(
        "--outfile",
        metavar="SERIES",
        type=Path,
        default=None,
        help="file to generate (DIR.vtk.series if not set)",
    )
    parser.add_argument(
        "--pattern",
        "-p",
        type=str,
        default="*.vtk",
        help="glob pattern to match VTK-files (e.g.: '*_cutPlane.vtk')",
    )


def __validate(args: argparse.Namespace) -> None:

    def validate(io: str, suffix: str) -> None:
        if not suffix.endswith(tuple(SUPPORTED_SUFFIXES[io])):
            logging.fatal(f"{suffix=} is not supported by {io} - exiting…")
            raise SystemExit(1)

    args.indir = args.indir.resolve()
    args.outfile = (
        args.indir.with_suffix(args.indir.suffix + ".vtk.series")
        if args.outfile is None
        else args.outfile.resolve()
    )

    validate("reader", args.pattern)
    validate("writer", args.outfile.suffix)


def __pvd(indir: Path, outfile: Path, pattern: str = "*.vtp") -> None:
    """Create ParaView .pvd-file from directory with time-step folders.

    Args:
        indir (Path): Directory storing time-step folders with .vtu-files.
        outfile (Path): .pvd-file to generate.
        pattern (str, optional): Glob pattern to match VTK-files. Defaults to '*.vtp'.
    """

    found_files = sorted(indir.rglob(pattern))
    if not found_files:
        logging.fatal(f"no files matched the {pattern=} in {indir} - skipping…")
        return

    logging.info(f"{len(found_files)} files matched the {pattern=} in {indir}")

    root = et.Element(
        "VTKFile",
        type="Collection",
        byte_order="LittleEndian",
        compressor="vtkZLibDataCompressor",
    )

    # Iterate over found files
    cellection = et.SubElement(root, "Collection")
    for f in found_files:
        logging.debug(f"{f} found")
        et.SubElement(
            cellection,
            "DataSet",
            timestep=f.parent.name,
            group="",
            part="0",
            file=str(f.relative_to(outfile.parent)),
        )

    tree = et.ElementTree(root)
    tree.write(outfile)
    logging.info(f"{outfile} generated")


def __series(indir: Path, outfile: Path, pattern: str = "*.vtk") -> None:
    """Create ParaView .vtk.series-file from directory with time-step folders.

    Args:
        indir (Path): Directory storing time-step folders with .vtu-files.
        outfile (Path): .vtk.series-file to generate.
        pattern (str, optional): Glob pattern to match VTK-files. Defaults to '*.vtk'.
    """

    found_files = sorted(indir.rglob(pattern))
    if not found_files:
        logging.fatal(f"no files matched the {pattern=} in {indir} - skipping…")
        return

    logging.info(f"{len(found_files)} files matched the {pattern=} in {indir}")

    root = {
        "files": [
            {"file": str(f.relative_to(outfile.parent)), "time": f.parent.name}
            for f in found_files
        ],
        "file-series-version": "1.0",
    }
    with open(outfile, "w") as f:
        json.dump(root, f)


def serialise(args: argparse.Namespace) -> None:
    __validate(args)

    outsuffix = args.outfile.suffix
    if outsuffix.endswith(".pvd"):
        __pvd(args.indir, args.outfile, pattern=args.pattern)
        return
    elif outsuffix.endswith(".series"):
        __series(args.indir, args.outfile, pattern=args.pattern)
        return

    logging.fatal(f"unsupported pattern {outsuffix=} - exiting…")
    raise SystemExit(1)
