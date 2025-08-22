from __future__ import annotations

import gzip
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def __get_header_size(filepath: Path | str, comment: str = "#") -> int:
    """Get header size."""

    with open(filepath, encoding="utf-8") as f:
        for index, line in enumerate(f):
            if not line.startswith(comment):
                return index - 1
    return 0


def __unnest_columns(dat: pd.DataFrame) -> pd.DataFrame:
    """Unnest non-scalar field values to components."""

    colnames: list[str] = list(dat)
    unnested: list[pd.DataFrame] = [dat]
    for i, name in enumerate(dat.columns):
        if not (
            dat[name].dtype == "object"
            and (col := dat[name].astype(str))
            .str.contains(r"^\(|\)$", regex=True)
            .any()
        ):
            continue

        col = col.replace(r"^\(|\)$", "", regex=True).apply(lambda s: s.split())
        unnested_names = [f"{name}.{i}" for i in range(col.map(len).max())]
        colnames[i : i + len(unnested_names)] = unnested_names

        unnested.append(
            pd.DataFrame(col.to_list(), index=col.index, columns=unnested_names)
        )
    return pd.concat(unnested, axis=1).drop(columns=set(dat) - set(colnames))


def read(
    filepath: Path | str, *, usecols: list | None = None, usenth: int | None = None
) -> pd.DataFrame:
    """Read OpenFOAM post-processing .dat file as pandas DataFrame

    Args:
        filepath (Path | str): path to .dat-file of directory
        with .dat-files.
        usecols (list[int], optional): columns to read (starting with 1).
        Defaults to None.
        usenth (int, optional): read every n-th row. Defaults to None.

    Raises:
        ValueError: raised when .dat-file path is invalid.

    Returns:
        pd.DataFrame: converted to DataFrame .dat-file.
    """

    def _read(filepath: Path) -> pd.DataFrame:

        header_pos = __get_header_size(filepath)

        # Read .dat-file as pandas' DataFrame
        dat = pd.read_csv(
            filepath,
            sep="\t",
            header=header_pos,
            index_col=0,
            usecols=(usecols if usecols is None else ([0] + usecols)),
            skiprows=(
                lambda n: (
                    n > header_pos and n % usenth
                    if not usenth is None and usenth >= 2
                    else None
                )
            ),  # type: ignore
        )

        # Drop '#' and trails spaces from column names
        dat.index.name = dat.index.name.replace("#", "").strip()
        dat.columns = dat.columns.str.strip()

        return (
            __unnest_columns(dat)
            .replace("N/A", pd.NA)
            .apply(func=lambda col: pd.to_numeric(col, errors="coerce"))
        )

    filepath = Path(filepath)

    # Merge all .dat-files in the direcotry into one dataframe
    if filepath.is_dir():
        filepaths = list(filepath.rglob("*.dat"))
        df = pd.concat([_read(dat_file) for dat_file in sorted(filepaths)])
        return df[~df.index.duplicated(keep="last")]

    return _read(filepath)


def write(
    fname: Path | str,
    dat: np.ndarray,
    *,
    compression: bool = False,
    header: str = None,
    dims: bool = False,
    footer: str = None,
) -> None:
    """Write n-dimensional array to .dat-file.

    Args:
        fname (Path | str): path to .dat-file.
        dat (np.ndarray): data to be saved to a .dat-file.
        dims (bool, optional): prepend dimensions. Defaults to False.
        compression (bool, optional): gzip file. Defaults to False.
    """

    np.set_printoptions(threshold=sys.maxsize)

    sdat = " ".join(str(d) for d in dat.shape) if dims else ""
    sdat += " "
    sdat += (
        np.array2string(dat, max_line_width=None, floatmode="maxprec")
        .replace("\n", "")
        .replace("[", "(")
        .replace("]", ")")
    )
    sdat = (
        (header if not header is None else "")
        + re.sub(r"\s+", " ", sdat).strip()
        + (footer if not footer is None else "")
    )
    if compression:
        with gzip.open(fname, "wt") as f:
            f.write(sdat)
    else:
        with open(fname, "w", encoding="utf-8") as f:
            f.write(sdat)
