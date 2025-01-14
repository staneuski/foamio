from __future__ import annotations

import contextlib
import os
import itertools
import logging
import re
import subprocess
from pathlib import Path

REGEX_GPFILE = r"^_.*|^Ggrid.txt$|^.*\.(conn(|_s)|log|pty|sch|surfrigid|tmp(|.*))$"


def _execute(
    file: Path,
    sargs: list[str],
    *args,
    **kwargs,
) -> subprocess.CompletedProcess[int]:
    """Execute a GridPro (utilities) command.

    Args:
        file (Path): path to the GridPro file
        sargs (list[str]): list of command line arguments

    Returns:
        subprocess.CompletedProcess[int]: CompletedProcess object
    """

    logging.debug(f"calling `subprocess.run({sargs})`")
    return subprocess.run(sargs, cwd=file.parent, *args, **kwargs)


def clean(
    topo_dir: Path | str, geom_dir: Path | str = None, include: str = REGEX_GPFILE
) -> None:
    """Remove automatically generated GridPro files.

    Args:
        topo_dir (Path | str): topology directory to clean
        geom_dir (Path | str, optional): geometry directory to clean
        Defaults to None.
        include (str, optional): regular expression pattern to match the files
        to be removed. Defaults to REGEX_GPFILE.
    """

    topo_dir = Path(topo_dir).resolve()
    geom_dir = Path(geom_dir).resolve() if not geom_dir is None else topo_dir

    fnames = []
    for f in itertools.chain(topo_dir.glob("*"), geom_dir.glob("*")):
        if re.search(include, f.name):
            logging.debug(f"{f=}.unlink()")
            fnames.append(f.name)
            f.unlink()
    logging.info(f"{fnames=} are removed")
