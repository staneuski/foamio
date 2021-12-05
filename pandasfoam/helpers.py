import linecache
from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd


def count_columns(filepath: Union[Path, str], sep: str, line_no: int = 1) -> int:
    """Count columns in a data-file by counting separators in a line."""

    line = linecache.getline(str(Path(filepath)), line_no)
    return line.count(sep) + line.count('\n')


def load_dat(filepath: Union[Path, str],
             usecols: list[int] = None) -> pd.DataFrame:
    """Load OpenFOAM post-processing .dat file as pandas DataFrame."""

    def get_header_size(filepath: Union[Path, str]) -> int:
        """Get header size."""

        header = 0
        with open(filepath) as f:
            for index, line in enumerate(f):
                if not line.startswith('#'):
                    return index - 1

    def unnest(dat: pd.DataFrame) -> pd.DataFrame:
        """Unnest non-scalar field values to components."""

        nested_columns: list = []
        for key, column_dtype in zip(dat, dat.dtypes):
            if column_dtype == np.dtype('object'):
                dat[key] = dat[key].apply(lambda cell: np.array(
                    cell.replace('(', '').replace(')', '').split(),
                    dtype=float))

                pos, field = (dat.columns.to_list().index(key) + 1,
                              np.array(dat[key].to_list()))
                for component_no in range(field.shape[-1]):
                    dat.insert(pos + component_no,
                               f'{key}.{component_no}',
                               field[:, component_no])

                nested_columns.append(key)

        return dat.drop(nested_columns, axis='columns')

    # Read .dat-file as pandas' DataFrame
    dat = pd.read_csv(filepath,
                      sep='\t',
                      header=get_header_size(filepath),
                      index_col=0,
                      usecols=usecols if usecols is None else ([0] + usecols))

    # Drop '#' and trails spaces from column names
    dat.index.name = dat.index.name.replace('#', '').strip()
    dat.columns = dat.columns.str.strip()

    return unnest(dat)


def load_xy(filepath: Union[Path, str],
            usecols: list[int] = None) -> pd.DataFrame:
    """Load OpenFOAM post-processing .xy file as pandas DataFrame."""

    # Get field names by slitting the filename
    fields = Path(filepath).stem.split('_')

    # Check if field is vector-field by comparing fields and columns sizes
    columns_count = count_columns(filepath, sep='\t')
    if len(fields) != columns_count:
        # Add coordinates to field names
        columns = [fields[0]]
        for column in fields[1:]:
            columns += [f'{column}.{component_no}' for component_no in range(3)]
    else:
        columns = fields

    return pd.read_csv(filepath,
                       sep='\t',
                       index_col=0,
                       usecols=usecols if usecols is None else ([0] + usecols),
                       names=(columns if len(columns) == columns_count
                              else range(columns_count)))
