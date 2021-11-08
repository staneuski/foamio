import linecache
import os

import pandas as pd


def count_columns(filepath: str, sep: str, line_no: int = 1) -> int:
    """Count columns in a data-file by counting separators in a line."""

    line = linecache.getline(filepath, line_no)
    return line.count(sep) + line.count('\n')


def load_dat(filepath: str) -> pd.DataFrame:
    """Load OpenFOAM post-processing .dat file as pandas DataFrame."""

    # Get header size
    header = 0
    with open(filepath) as f:
        for index, line in enumerate(f):
            if not line.startswith('#'):
                header = index - 1
                break

    # Read .dat-file as pandas' DataFrame
    dat = pd.read_csv(filepath, sep='\t', header=header, index_col=0)

    # Drop '#' and trails spaces from column names
    dat.index.name = dat.index.name.replace('#', '').strip()
    dat.columns = dat.columns.str.strip()

    return dat


def load_xy(filepath: str) -> pd.DataFrame:
    """Load OpenFOAM post-processing .xy file as pandas DataFrame."""

    # Get field names by slitting the filename
    fields = os.path.splitext(os.path.basename(filepath))[0].split('_')

    # Check if field is vector-field by comparing fields and columns sizes
    columns_count = count_columns(filepath, sep='\t')
    if len(fields) != columns_count:
        # Add coordinates to field names
        columns = [fields[0]]
        for column in fields[1:]:
            columns += [f'{column}.{coord}' for coord in 'xyz']
    else:
        columns = fields

    return pd.read_csv(filepath,
                       sep='\t',
                       names=columns if len(columns) == columns_count
                       else range(columns_count),
                       index_col=0)
