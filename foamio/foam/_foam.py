import subprocess
from pathlib import Path

from foamio.foam import Caller


def _convert(value: str) -> str | list:
    """Convert OpenFOAM dictionary's string value number if possible.
    Convertion of lists is not implemented.

    Args:
        value (str): OpenFOAM dictionary value

    Returns:
        str | list: converted value
    """

    value = value.rstrip()  # drop end line charecters
    if value.isdigit():
        return int(value)
    try:
        return float(value)
    except ValueError:
        return value


def read(root: Path | str, fname: Path | str, *, encoding: str = "utf-8") -> dict:
    """Read OpenFOAM dictionary file as Python dictionary using
    `foamDictionary`.

    Args:
        root (Path | str): FOAM_CASE path
        fname (Path | str): Path to OpenFOAM dictionary
        encoding (str, optional): encoding. Defaults to 'utf-8'.

    Returns:
        dict: OpenFOAM dictionary converted to Python `dict`
    """

    root = Path(root).resolve()
    fname = Path(fname).resolve().relative_to(root)

    def _read(entry: str) -> str | dict | list:
        """Read key's value.

        Args:
            entry (str): OpenFOAM dictionary key/entry name.

        Returns:
            str | dict: entry value.
        """

        foam_dict = Caller(
            encoding=encoding,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        ).Dictionary
        kwargs = dict(case=root, entry=entry)
        try:
            return {
                key: _read(f"{entry}/{key}")
                for key in foam_dict(fname, keywords=True, **kwargs).stdout.splitlines()
            }
        except subprocess.CalledProcessError:
            return _convert(foam_dict(fname, value=True, **kwargs).stdout)

    return {
        entry: _read(entry)
        for entry in Caller(
            encoding=encoding,
            stdout=subprocess.PIPE,
        )
        .Dictionary(fname, case=root, keywords=True)
        .stdout.splitlines()
    }
