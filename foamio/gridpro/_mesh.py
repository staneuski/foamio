from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Iterable

import gp_utilities as gp
from foamio.gridpro._helpers import _execute as execute


def _schedule(
    fra_file: Path, grd_file: Path = None, n_steps: int = 10, n_sweeps: int = 1_000
) -> Path:
    """Generate schedule file.

    Args:
        fra_file (Path): path to the .fra-topology file
        grd_file (Path, optional): path to the output grid file.
        Defaults to None.
        n_steps (int, optional): number of steps for mesh generatio per sweep.
        Defaults to 10.
        n_sweeps (int, optional): number of sweeps per step. Defaults to 1000.

    Returns:
        path to the .grd-grid file
    """

    fra_file = Path(fra_file).resolve()
    grd_file = fra_file.with_suffix(".grd") if grd_file is None else grd_file
    grd_file.parent.mkdir(parents=True, exist_ok=True)

    sch_file = grd_file.with_suffix(".sch")
    gp.Topology().write_schedule_file(
        str(sch_file),
        n_steps,
        n_sweeps,
        str(grd_file.relative_to(fra_file.parent)),
        str(grd_file.with_suffix(".dump.tmp").relative_to(fra_file.parent)),
    )

    return grd_file


def _mesh(fra_file: Path) -> subprocess.CompletedProcess[int]:
    """Call Ggrid.

    Args:
        fra_file (Path): path to the .fra-topology file
    """

    return execute(fra_file, ["Ggrid", fra_file.name])


def mesh(
    fra_file: Path | str,
    region: Path | str = None,
    n_steps: int = 10,
    n_sweeps: int = 1_000,
) -> Path:
    """Generate a mesh using the given topology.

    Args:
        fra_file (Path | str): path to the .fra-topology file
        region (Path | str, optional): path to the OpenFOAM-region directory.
        Defaults to None.
        n_steps (int, optional): number of steps for mesh generatio per sweep.
        Defaults to 10.
        n_sweeps (int, optional): number of sweeps per step. Defaults to 1000.
        convert (bool, optional): convert .grd-file to polyMesh and remove it.
        Defaults to False.

    Returns:
        path to the generated .grd-grid file
    """

    fra_file = Path(fra_file).resolve()
    grd_file = None
    if not region is None:
        region = Path(region).resolve()
        region.mkdir(parents=True, exist_ok=True)
        grd_file = region / fra_file.with_suffix(".grd").name

    grd_file = _schedule(fra_file, grd_file, n_steps, n_sweeps)
    _mesh(fra_file)
    return grd_file


def extrude(
    infile: Path | str,
    surface: int,
    spacing: float,
    aspect: float = 1.0,
    distance: float = None,
    cell_count: int = None,
    outfile: Path | str = None,
) -> None:
    """Extrude surfaces by the given IDs to the given distance.

    Args:
        infile (Path | str): input GridPro .grd-grid file
        surface (int): index of the surface to extrude
        spacing (float): first cell size/spacing
        distance (float): total extrusion distance
        aspect (float): aspect ratio. Defaults to 1.
        outfile (Path | str, optional): output GridPro .grd-grid file.
        Defaults to None.

    Raises:
        ValueError: if nor `distance` or `cell_count` is provided
    """

    infile = Path(infile).resolve()
    outfile = infile if outfile is None else Path(outfile).resolve()

    # yapf: disable
    sargs = ['gp_utilities', 'extrude_block_faces_using_surfaces',
             '-ifn', infile.name,
             '-sid', str(surface + 1), # extrude_block_faces is 1-based
             '-s', str(spacing),
             '-gr', str(aspect)]
    # yapf: enable
    if distance is None and not cell_count is None:
        sargs += ["-n", str(cell_count)]
    elif not distance is None and cell_count is None:
        sargs += ["-l", str(distance)]
    else:
        raise ValueError("either `distance` or `cell_count` must be provided")

    execute(infile, sargs + ["-outfn", str(outfile)])


def set_cell_size(
    grd_file: Path | str, surfaces: Iterable[int], cell_size: float
) -> None:
    """Set first cell size at the given surfaces.

    Args:
        grd_file (Path | str): input GridPro .grd-grid file
        surfaces (Iterable[int]): list of surface indices
        cell_size (float): first cell size
    """

    grd_file = Path(grd_file).resolve()
    # yapf: disable
    sargs = ['gp_utilities', 'first_cell_spacing',
             '-ifn', grd_file.name,
             '-s', ' '.join(map(str, surfaces)),
             '-cs', str(cell_size)]
    # yapf: enable
    execute(grd_file, sargs)


def scale(infile: Path | str, factor: int, outfile: Path | str = None) -> None:
    """Scale the grid by the given factor.

    Args:
        infile (Path | str): input GridPro .grd-grid file
        factor (int): scaling factor
        outfile (Path | str, optional): output GridPro .grd-grid file.
        Defaults to None.
    """

    infile = Path(infile).resolve()
    outfile = infile if outfile is None else Path(outfile).resolve()

    # yapf: disable
    sargs = ['gp_utilities', 'transform_grid',
             '-ifn', infile.name,
             '-t1', '0', '0', '0',
             '-sc', str(factor), str(factor), str(factor),
             '-t2', '0', '0', '0',
             '-outfn', str(outfile)]
    # yapf: enable
    execute(infile, sargs)


def convert(
    infile: Path | str,
    outdir: Path | str = None,
    *,
    keep: bool = False,
    drop_zones: bool = False,
) -> None:
    """Convert GridPro grid to OpenFOAM polyMesh

    Args:
        infile (Path | str): GridPro .grd-grid file
        outdir (Path | str): OpenFOAM polyMesh directory to save
        keep (bool, optional): keep .grd-grid file after conversion
        drop_zones (bool, optional): Whether to remove cellzones file from
        outdir

    Raises:
        RuntimeError: `gp_utilities change_format` failed
    """

    # yapf: disable
    infile = Path(infile).resolve()
    outdir = infile.parent / 'polyMesh' if outdir is None else Path(outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    # GridPro recognises format from the extension, filename is arbitrary.
    sargs = ['gp_utilities', 'change_format', '-iif',
             '-ifn', infile.name,
             '-outfn', '/tmp/polyMesh.foam',
             '-dn', str(outdir)]
    # yapf: enable
    execute(infile, sargs)
    if not (outdir / "boundary").exists() or not (outdir / "points").exists():
        raise RuntimeError(f"failed to convert {infile.name} to {outdir.name}")

    if drop_zones:
        (outdir / "cellzones").unlink()
    else:
        (outdir / "cellzones").rename(outdir / "cellZones")

    if (outdir / "points").exists() and not keep:
        infile.unlink()
        logging.debug(f"{infile} is removed")
