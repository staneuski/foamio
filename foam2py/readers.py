import linecache
import re
from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd
import pyvista as pv
from tqdm import tqdm

REGEX_DIGIT = r'[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?'

def count_columns(filepath: Union[Path, str],
                  sep: str,
                  line_no: int = 1) -> int:
    """Count columns in a data-file by counting separators in a line."""

    line = linecache.getline(str(Path(filepath)), line_no)
    return line.count(sep) + line.count('\n')


def read_dat(filepath: Union[Path, str],
             *,
             usecols: list = None,
             use_nth: int = None) -> pd.DataFrame:
    """Read OpenFOAM post-processing .dat file as pandas DataFrame.

    Args:
        filepath (Union[Path, str]): Path to .dat-file of directory
        with .dat-files.
        usecols (list[int], optional): Columns to read (starting with 1).
        Defaults to None.
        use_nth (int, optional): Read every n-th row. Defaults to None.

    Raises:
        ValueError: _description_

    Returns:
        pd.DataFrame: Converted to DataFrame .dat-file.
    """

    def get_header_size(filepath: Union[Path, str], comment: str = '#') -> int:
        """Get header size."""

        with open(filepath) as f:
            for index, line in enumerate(f):
                if not line.startswith(comment):
                    return index - 1

    def unnest_columns(dat: pd.DataFrame) -> pd.DataFrame:
        """Unnest non-scalar field values to components."""

        nested_columns: list = []
        for key, column_dtype in zip(dat, dat.dtypes):
            if (column_dtype == np.dtype('object')
                    and re.match(rf'.*?{REGEX_DIGIT}', dat[key].iloc[-1])):

                fn = lambda cell: np.array(cell.replace('(', '').replace(
                    ')', '').split(),
                                           dtype=float)
                dat[key] = dat[key].apply(fn)

                pos, field = (dat.columns.to_list().index(key) + 1,
                              np.array(dat[key].to_list()))
                for component in range(field.shape[-1]):
                    dat.insert(pos + component, f'{key}.{component}',
                               field[:, component])

                nested_columns.append(key)

        return dat.drop(nested_columns, axis='columns')

    def load(filepath: Path) -> pd.DataFrame:

        header_pos = get_header_size(filepath)

        # Read .dat-file as pandas' DataFrame
        dat = pd.read_csv(
            filepath,
            sep='\t',
            header=header_pos,
            index_col=0,
            usecols=(usecols if usecols is None else ([0] + usecols)),
            skiprows=(lambda n: n > header_pos and n % use_nth
                      if not use_nth is None and use_nth >= 2 else None),
        )

        # Drop '#' and trails spaces from column names
        dat.index.name = dat.index.name.replace('#', '').strip()
        dat.columns = dat.columns.str.strip()

        return unnest_columns(dat)

    filepath = Path(filepath)

    # Merge all .dat-files in the direcotry into one dataframe
    if filepath.is_dir():
        filepaths = list(filepath.rglob('*.dat'))
        if len({fp.name for fp in filepaths}) != 1:
            raise ValueError(f'{filepath} is not valid')

        return pd.concat([load(dat_file) for dat_file in sorted(filepaths)])

    return load(filepath)


def read_xy(filepath: Union[Path, str],
            *,
            usecols: list = None,
            use_nth: int = None) -> pd.DataFrame:
    """Load OpenFOAM post-processing .xy file as pandas DataFrame.

    Args:
        filepath (Union[Path, str]): Path to .xy-file.
        usecols (list[int], optional): Columns to read (starting with 1).
        Defaults to None.
        use_nth (int, optional): Read every n-th row. Defaults to None.

    Returns:
        pd.DataFrame: Converted to DataFrame .dat-file.
    """

    def field_components(field_name: str, components_count: int) -> list:
        if components_count <= 1:
            return [field_name]
        elif components_count == 3:
            components = 'xyz'
        elif components_count == 6:
            components = ['xx', 'xy', 'xz', 'yy', 'yz', 'zz']
        else:
            components = range(components_count)

        return [f'{field_name}.{component}' for component in components]

    filepath = Path(filepath)

    # Get field names by splitting the filename
    field_names = filepath.stem.split('_')

    columns_count = count_columns(filepath, sep='\t')

    # Get position of the first column with field value
    pos = 0
    if not (columns_count - 1) % len(field_names[1:]):
        pos = 1
    elif columns_count > 3 and not (columns_count - 3) % len(field_names[3:]):
        pos = 3

    # Constuct field names by appending components
    components_count = (columns_count - pos) / len(field_names[pos:])
    names = field_components(field_names[0], pos)
    for field_name in field_names[pos:]:
        names += field_components(field_name, components_count)

    return pd.read_csv(
        filepath,
        sep='\t',
        index_col=0,
        usecols=usecols if usecols is None else ([0] + usecols),
        names=names,
        skiprows=(lambda n: n % use_nth
                  if not use_nth is None and use_nth >= 2 else None),
    )


def read_vtkfields(vtkdir: Path, pattern: str = '_cutPlane.vtk') -> pv.DataSet:
    """Read folder (time-folder) with .vtk-files into a DataSet.

    Args:
        vtkdir (Path): Path to folder (time-folder)
        pattern (str, optional): Pattern to match .vtk-files. Defaults to '_cutPlane.vtk'.

    Returns:
        pv.DataSet: DataSet with all .vtk-fields in folder (time-folder).
    """ 

    # Match all .vtk-files using pattern
    files = sorted(vtkdir.glob(f'*{pattern}'))

    # Load and append to fields to DataArrays
    ds = pv.read(files[0])
    for f in files[1:]:
        fieldname = f.name.replace(pattern, '')
        if fieldname in (data := pv.read(f)).array_names:
            ds[fieldname] = data[fieldname]
    return ds


def read_vtktimes(vtktimes_dir: Path) -> pv.MultiBlock:
    """Read all time folders with .vtk-files into a MultiBlock.

    Args:
        cutplane_dir (Path): Path to cutplane directory.

    Returns:
        pv.MultiBlock: Times with combined .vtk-data into one DataSet.
    """

    time_folders = sorted(vtktimes_dir.glob(f'[0-1]*'))

    block = pv.MultiBlock()
    for time_folder in (pbar := tqdm(time_folders)):
        pbar.set_description(f'Reading {(time := time_folder.name)}')
        block[time] = read_vtkfields(time_folder)
    return block
