import logging
from pathlib import Path

from foamio.gridpro._helpers import _execute as execute


def create_zones(
    infile: Path | str, labels: str, outfile: Path | str = None, init_index: int = 3
) -> dict[str]:
    """Create cell zones from block labels

    Args:
        infile (Path | str): GridPro .grd-grid input file
        labels (str): corresponding zone names
        outfile (Path | str, optional): output GridPro .grd-grid file
        init_index (int, optional): initial index for zone numbering (by default
        1 generates ws.Fluid, 2 - ws.Solid, 3 - ws.User3, 4 - ws.User4, etc.).
        Defaults to 3.

    Returns:
        dict[str]: label to GridPro zone name (i.e. ws.User3, ws.User4, etc.)
    """

    infile = Path(infile).resolve()
    outfile = infile if outfile is None else Path(outfile).resolve()

    # yapf: disable
    sargs = ['gp_utilities', 'block_labels_to_3d_properties',
             '-ifn', infile.name]
    # yapf: enable

    label_to_zone = {}
    for i, label in enumerate(labels):
        ind = init_index + i
        if ind == 1:
            label_to_zone[label] = f"ws.Fluid"
        elif ind == 2:
            label_to_zone[label] = f"ws.Solid"
        else:
            label_to_zone[label] = f"ws.User{ind}"
        sargs += ["-ln", label, "-p", str(ind)]
    sargs += ["-outfn", str(outfile)]
    execute(infile, sargs)

    return label_to_zone
