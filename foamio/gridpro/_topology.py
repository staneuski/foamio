from __future__ import annotations

from pathlib import Path
from typing import Iterable

import gp_utilities as gp
from foamio.gridpro._helpers import _execute as execute


def _execute(topology: gp.Topology, sargs: list[str], cwd: Path = None) -> None:
    """Execute topology command.

    Args:
        topology (gp.Topology): topology object
        sargs (list[str]): commands list
        cwd (Path, optional): current working directory. Defaults to None.
    """

    topology.execute(" ".join(map(str, sargs)))


def get_corners(topology: gp.Topology, corner_group: gp.CornerGroup | int) -> list[int]:
    """Corner indices in the given corner group.

    Args:
        topology (gp.Topology): topology object
        corner_group (gp.CornerGroup | int): corner group or corner group ID
    """

    if not isinstance(corner_group, gp.CornerGroup):
        corner_group = topology.corner_group(corner_group)
    return [ci.get_id() for ci in corner_group.get_all()]


def get_surfaces(topology: gp.Topology) -> dict[int]:
    """Surface indices in the topology.

    Args:
        topology (gp.Topology): topology object

    Returns:
        dict[int]: dictionary of surface indices
    """

    return {
        topology.surface(i).get_label(): topology.surface(i).get_id()
        for i in range(topology.num_surfaces())
    }


def _translate(
    topology: gp.Topology,
    translation: Iterable[float, 3],
    corner_group: int = None,
    surface_group: int = None,
    surfaces: Iterable[int] = None,
) -> gp.Topology:
    """Translate the topology by the given displacement vector.

    Args:
        topology (gp.Topology): topology object
        translation (Iterable[float, 3]): displacement vector
        surfaces (Iterable[int], optional): surface indices. Defaults to None.
        surface_group (int | Iterable[int], optional): surface group index.
        Defaults to None.
        corner_group (int, optional): corner group index. Defaults to None.
    """

    sargs = ["transform_topo"]
    sargs += ["-g", corner_group] if corner_group is not None else []
    sargs += ["-sg", surface_group] if surface_group is not None else []
    sargs += ["-s", ", ".join(map(str, surfaces))] if surfaces is not None else []
    sargs += ["-t1"] + [str(coord) for coord in translation[:3]]

    _execute(topology, sargs)


def align(
    topology: gp.Topology | Path | str,
    grd_file: Path | str,
    corner_grp: gp.CornerGroup = None,
) -> None:
    """Align the topology with the given grid.

    Args:
        topology (gp.Topology | Path | str): topology object or path to the
        .fra-topology file
        grd_file (Path | str): path to the input grid file
        topology (gp.Topology): topology object
        corner_grp (gp.CornerGroup, optional): corner group to align, use all
        if None. Defaults to None.
    """

    grd_file = Path(grd_file).resolve()

    if not isinstance(topology, gp.Topology):
        fra_file = Path(topology).resolve()
        # yapf: disable
        sargs = ['gp_utilities', 'grid_to_til',
                 '-fn', fra_file.name,
                 '-ofn', fra_file.name,
                 '-gfn', str(grd_file),
                 '-g', str(0 if corner_grp is None else corner_grp.get_id())]
        # yapf: enable
        execute(fra_file, sargs)
        return

    corner_grp = topology.new_corner_grp() if corner_grp is None else corner_grp
    corner_grp.add_all()
    # yapf: disable
    sargs = ['grid_to_til',
             '-g', str(corner_grp.get_id()),
             '-gfn', str(grd_file)]
    # yapf: enable
    _execute(topology, sargs)


def split(
    topology: gp.Topology, surface_group: gp.SurfaceGroup | int, outfile: Path | str
) -> None:
    """Split the topology by the given surface group.

    Args:
        topology (gp.Topology): topology object
        surface_group (gp.SurfaceGroup | int): surface group or surface group ID
        outfile (Path | str): split file prefix. E.g. `dir/split` will generate
        `dir/split.0.fra`, `dir/split.1.fra`, etc.
    """

    index = (
        surface_group.get_id()
        if isinstance(surface_group, gp.SurfaceGroup)
        else surface_group
    )
    outfile = Path(outfile).resolve()

    sargs = ["split_topology", "-sg", index, "-p", outfile.name]
    _execute(topology, sargs)
