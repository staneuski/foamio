from pathlib import Path
from typing import Iterable

import pyvista as pv

from .readers import read_vtksequence

def is_notebook() -> bool:
    """Check if current file is IPython notebook."""

    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True  # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False


def read_vtktimes(fo: Path,
                  timerange: Iterable = None,
                  nproc: int = None,
                  *args,
                  **kwargs) -> pv.MultiBlock:
    """Combine time-folders with .vtk-files into a MultiBlock in selected
    timerange.

    Args:
        fo (Iterable[Path]): functionObject directory with time-folders.
        timerange (Iterable[Union[int, float]]): timerange
        nproc (int, optional): The maximum number of processes that can be
        used. If None or not given then as many worker processes will be
        created as the machine has processors.
        *args, **kwargs: `read_vtkfields` arguments.

    Returns:
        pv.MultiBlock: Ordered folder name (time-folder) to dataset with fields.
    """

    if timerange is None:
        timepaths = fo.glob('[0-9]*')
    else:
        timepaths = [
            timefolder for timefolder in fo.glob('[0-9]*')
            if timerange[0] <= float(timefolder.name) < timerange[-1]
        ]

    return read_vtksequence(timepaths, nproc, *args, **kwargs)