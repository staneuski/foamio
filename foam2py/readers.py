import concurrent.futures
import linecache
import logging
import re
from pathlib import Path
from typing import Callable, Iterable, Union

import numpy as np
import pandas as pd
import pyvista as pv

REGEX_DIGIT = r'[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?'


def _count_columns(filepath: Union[Path, str],
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
        ValueError: Raised when .dat-file path is invalid.

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

        df = pd.concat([load(dat_file) for dat_file in sorted(filepaths)])
        return df[~df.index.duplicated(keep='last')]

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

    columns_count = _count_columns(filepath, sep='\t')

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


def read_vtkfields(
    timefolder: Path,
    fieldnames: list = None,
    selector: Callable = lambda pattern: f'^({pattern})_cutPlane.vtk'
) -> pv.DataSet:
    """Read .vtk-fields in folder (time-folder) into a DataSet.

    Args:
        timefolder (Path): Path to folder (time-folder).
        fieldnames (list, optional): Fields to read. Defaults to None.
        selector (_type_, optional): Function returning regex pattern to match
        field filename. Defaults to
        `lambda pattern: f'^({pattern})_cutPlane.vtk'`.

    Returns:
        pv.DataSet: DataSet with selected .vtk-fields found in folder.
    """

    # Match .vtk-files using provided selector
    engine = re.compile(
        selector("|".join(fieldnames) if not fieldnames is None else '.*'))

    nthreads = len(fieldnames) if not fieldnames is None else 1
    with concurrent.futures.ThreadPoolExecutor(max_workers=nthreads) as e:
        future_to_fieldname = {
            e.submit(pv.read, f): match.group(1)
            for f in timefolder.glob('*.vtk')
            if (match := engine.search(f.name))
        }
        logging.info(
            f'{len(future_to_fieldname)} fields found @ {timefolder.name}')

        ds = None
        for future in concurrent.futures.as_completed(future_to_fieldname):
            fieldname = future_to_fieldname[future]
            logging.debug(f'{fieldname=} loaded @ {timefolder.name}')
            if ds is None:
                ds = future.result()
            else:
                ds[fieldname] = future.result()[fieldname]
        return ds


def read_vtksequence(folders: Iterable,
                     nproc: int = None,
                     *args,
                     **kwargs) -> Union[pv.MultiBlock, dict]:
    """Read all folders (time-folders) with .vtk-files into a MultiBlock.

    Args:
        folders (Iterable[Path]): folders (time-folders) with .vtk-files.
        nproc (int, optional): The maximum number of processes that can be
        used. If None or not given then as many worker processes will be
        created as the machine has processors.
        *args, **kwargs: `read_vtkfields` arguments.

    Returns:
        Union[pv.MultiBlock, dict]: Ordered folder name (time-folder) to
        dataset with fields.
    """

    with concurrent.futures.ProcessPoolExecutor(max_workers=nproc) as e:
        future_to_time = {
            e.submit(read_vtkfields, folder, *args, **kwargs): folder.name
            for folder in folders
        }

        time_to_ds = {
            future_to_time[future]: future.result()
            for future in concurrent.futures.as_completed(future_to_time)
        }
        block = pv.MultiBlock()
        for time, ds in sorted(time_to_ds.items(),
                               key=lambda time: float(time[0])):
            block[time] = ds
        return block
