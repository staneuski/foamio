import argparse
import json
import logging
import re
import xml.etree.ElementTree as et
from pathlib import Path

SUPPORTED_SUFFIXES = dict(writer={".pvd", ".series"})


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
        default=r".*/(?P<time>.*)/(?P<file>.*.vtk)",
        help="regex pattern to match VTK-files. Must include 'time' and 'file' groups, e.g. "
        "'.*/(?P<time>.*)/(?P<file>.*.vtk)' or '.*/(?P<file>f0_(?P<time>.*).vtk)'",
    )


def __validate(args: argparse.Namespace) -> None:

    def validate(io: str, suffix: str) -> None:
        if not suffix.endswith(tuple(SUPPORTED_SUFFIXES[io])):
            logging.fatal("%r is not supported by %s - exiting…", suffix, io)
            raise SystemExit(1)

    args.indir = args.indir.resolve()
    args.outfile = (
        args.indir.with_suffix(args.indir.suffix + ".vtk.series")
        if args.outfile is None
        else args.outfile.resolve()
    )

    validate("writer", args.outfile.suffix)


def __pvd(time_to_file: Path, outfile: Path) -> None:
    """Write .pvd-file from time-to-file mapping.

    Args:
        time_to_file (dict[float, str]): Mapping of time to file paths.
        outfile (Path): Output .series-file path.
    """

    root = et.Element(
        "VTKFile",
        type="Collection",
        byte_order="LittleEndian",
        compressor="vtkZLibDataCompressor",
    )
    collection = et.SubElement(root, "Collection")
    for time, f in time_to_file.items():
        et.SubElement(
            collection, "DataSet", timestep=str(time), file=f, group="", part="0"
        )
    tree = et.ElementTree(root)
    tree.write(outfile)
    logging.info("%s generated", outfile)


def __series(time_to_file: dict[float, str], outfile: Path) -> None:
    """Write .series-file from time-to-file mapping.

    Args:
        time_to_file (dict[float, str]): Mapping of time to file paths.
        outfile (Path): Output .series-file path.
    """

    root = {
        "files": [{"name": f, "time": time} for time, f in time_to_file.items()],
        "file-series-version": "1.0",
    }
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(root, f, separators=(",", ":"))
        logging.info("%s generated", outfile)


def serialise(args: argparse.Namespace) -> None:
    __validate(args)

    pattern = re.compile(args.pattern)
    time_to_file = {
        float(match.group("time")): str(f.relative_to(args.outfile.parent))
        for f in args.indir.rglob("*")
        if (match := pattern.fullmatch(str(f)))
    }
    if not time_to_file:
        logging.fatal(
            "no files matched the pattern=%r in %s - skipping…",
            args.pattern,
            args.indir,
        )
        raise SystemExit(1)

    logging.info(
        "%d files matched the pattern=%r in %s",
        len(time_to_file),
        args.pattern,
        args.indir,
    )

    outsuffix = args.outfile.suffix
    if outsuffix.endswith(".pvd"):
        __pvd(time_to_file, args.outfile)
        return
    elif outsuffix.endswith(".series"):
        __series(time_to_file, args.outfile)
        return

    logging.fatal("unsupported pattern outsuffix=%r - exiting…", outsuffix)
    raise SystemExit(1)
